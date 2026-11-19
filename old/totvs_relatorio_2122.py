#!/usr/bin/env python3
import argparse, base64, json, logging, os
from getpass import getpass
from pathlib import Path
from uuid import UUID
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zeep import Client, Settings
from zeep.exceptions import Fault
from zeep.transports import Transport

DEFAULT_WSDL = "https://institutopresbiteriano146532.rm.cloudtotvs.com.br:8051/wsReport/MEX?wsdl"
DEFAULT_REPORT_ID = 2122
DEFAULT_CHUNK_SIZE = 2 * 1024 * 1024
MAX_REPORT_SIZE = 100 * 1024 * 1024
LOG = logging.getLogger("totvs_wsreport")

def local_name(tag): return tag.rsplit("}",1)[-1]
def result_text(value):
    if value is None: raise RuntimeError("O servico retornou resultado vazio.")
    if isinstance(value, bytes): return value.decode("utf-8")
    if isinstance(value, (str,int,float)): return str(value)
    if isinstance(value, dict):
        for k,v in value.items():
            if str(k).lower().endswith("result"): return result_text(v)
    for name in dir(value):
        if name.lower().endswith("result"): return result_text(getattr(value,name))
    return str(value)

def build_client(wsdl, username, password, verify_tls, timeout):
    s=Session(); s.auth=HTTPBasicAuth(username,password); s.verify=verify_tls
    retries=Retry(total=3,connect=3,read=2,backoff_factor=.8,status_forcelist=(429,502,503,504),allowed_methods=frozenset({"GET","POST"}))
    s.mount("https://",HTTPAdapter(max_retries=retries))
    return Client(wsdl=wsdl, transport=Transport(session=s,timeout=timeout,operation_timeout=timeout), settings=Settings(strict=False,xml_huge_tree=False,forbid_dtd=True,forbid_entities=True,forbid_external=True))

def operation_names(client):
    names=[]
    for svc in client.wsdl.services.values():
        for port in svc.ports.values(): names.extend(port.binding._operations.keys())
    return sorted(set(names))

def call_variants(service, operation, variants):
    method=getattr(service,operation); errors=[]
    for args,kwargs in variants:
        try: return method(*args,**kwargs)
        except TypeError as exc: errors.append(str(exc))
    raise TypeError(f"Nao foi possivel adequar os argumentos de {operation}. " + " | ".join(errors[-3:]))

def get_report_info(service, report_id, context):
    return result_text(call_variants(service,"GetReportInfo",[((),{"reportId":report_id,"context":context}),((),{"ReportId":report_id,"Context":context}),((report_id,context),{}),((report_id,),{})]))

def apply_parameters(info_xml, parameters):
    if not parameters: return info_xml
    root=etree.fromstring(info_xml.encode(),parser=etree.XMLParser(resolve_entities=False,no_network=True))
    found=set()
    for node in root.iter():
        children={local_name(c.tag).lower():c for c in node if isinstance(c.tag,str)}
        nn=next((children[n] for n in ("name","nome","parametername","paramname") if n in children),None)
        if nn is None or (nn.text or "").strip() not in parameters: continue
        key=(nn.text or "").strip(); vn=next((children[n] for n in ("value","valor","parametervalue") if n in children),None)
        if vn is None: raise ValueError(f"Parametro {key} sem elemento de valor reconhecido.")
        vn.text=str(parameters[key]); found.add(key)
    missing=sorted(set(parameters)-found)
    if missing: raise ValueError("Parametros nao localizados: "+", ".join(missing))
    return etree.tostring(root,encoding="unicode")

def generate_report(service, report_id, xml_params, filename, context):
    v=call_variants(service,"GenerateReport",[((),{"reportId":report_id,"parameters":xml_params,"filename":filename,"context":context}),((),{"ReportId":report_id,"Parameters":xml_params,"FileName":filename,"Context":context}),((report_id,xml_params,filename,context),{}),((report_id,xml_params,filename),{})])
    guid=result_text(v).strip().strip("{}"); UUID(guid); return guid

def get_size(service,guid):
    v=call_variants(service,"GetGeneratedReportSize",[((),{"guid":guid}),((),{"reportId":guid}),((),{"Guid":guid}),((guid,),{})]); size=int(result_text(v).strip())
    if size<=0 or size>MAX_REPORT_SIZE: raise RuntimeError(f"Tamanho recusado: {size} bytes.")
    return size

def get_chunk(service,guid,offset,length):
    v=call_variants(service,"GetFileChunk",[((),{"guid":guid,"offset":offset,"length":length}),((),{"reportId":guid,"offset":offset,"length":length}),((),{"Guid":guid,"Offset":offset,"Length":length}),((guid,offset,length),{}),((guid,length),{})])
    return base64.b64decode("".join(result_text(v).split()),validate=True)

def save_report(service,guid,size,output,chunk_size):
    written=0
    with output.open("wb") as f:
        while written<size:
            chunk=get_chunk(service,guid,written,min(chunk_size,size-written))
            if not chunk: raise RuntimeError(f"Chunk vazio no offset {written}.")
            f.write(chunk); written+=len(chunk); LOG.info("Download: %d/%d bytes",written,size)
    data=output.read_bytes()
    if len(data)!=size: raise RuntimeError(f"Tamanho final divergente: esperado {size}, obtido {len(data)}.")
    if not data.startswith(b"%PDF-"): raise RuntimeError("Arquivo retornado nao possui assinatura PDF valida.")

def parse_args():
    p=argparse.ArgumentParser(description="Gera o relatorio 2122 no TOTVS RM via WsReport.")
    p.add_argument("--wsdl",default=os.getenv("TOTVS_WSDL",DEFAULT_WSDL)); p.add_argument("--report-id",type=int,default=DEFAULT_REPORT_ID)
    p.add_argument("--context",default=os.getenv("TOTVS_CONTEXT","")); p.add_argument("--params",type=Path); p.add_argument("--parameters-xml",type=Path)
    p.add_argument("--save-info",type=Path,default=Path("report_2122_info.xml")); p.add_argument("--info-only",action="store_true")
    p.add_argument("--output",type=Path,default=Path("relatorio_2122.pdf")); p.add_argument("--chunk-size",type=int,default=DEFAULT_CHUNK_SIZE)
    p.add_argument("--timeout",type=int,default=90); p.add_argument("--insecure",action="store_true"); p.add_argument("--list-operations",action="store_true"); p.add_argument("--verbose",action="store_true")
    return p.parse_args()

def main():
    args=parse_args(); logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    username=os.getenv("TOTVS_USERNAME") or input("Usuario tecnico TOTVS: ").strip(); password=os.getenv("TOTVS_PASSWORD") or getpass("Senha TOTVS: ")
    if not username or not password: raise ValueError("Usuario e senha sao obrigatorios.")
    client=build_client(args.wsdl,username,password,not args.insecure,args.timeout)
    operations=operation_names(client)
    if args.list_operations: print("\n".join(operations)); return 0
    required={"GetReportInfo","GenerateReport","GetGeneratedReportSize","GetFileChunk"}; missing=required-set(operations)
    if missing: raise RuntimeError("Operacoes ausentes no WSDL: "+", ".join(sorted(missing)))
    service=None
    for service_name,wsdl_service in client.wsdl.services.items():
        for port_name,port in wsdl_service.ports.items():
            ops=set(port.binding._operations.keys())
            if args.verbose: LOG.debug("Analisando Service=%s Port=%s Operacoes=%s",service_name,port_name,", ".join(sorted(ops)))
            if "GetReportInfo" in ops:
                service=client.bind(service_name,port_name); LOG.info("Service selecionado: %s",service_name); LOG.info("Port selecionado: %s",port_name); LOG.info("Binding selecionado: %s",port.binding.name); break
        if service is not None: break
    if service is None: raise RuntimeError("Nenhum Service/Port contendo GetReportInfo foi localizado no WSDL.")
    LOG.info("Consultando metadados do relatorio %d",args.report_id); info_xml=get_report_info(service,args.report_id,args.context)
    args.save_info.write_text(info_xml,encoding="utf-8"); LOG.info("Metadados salvos em %s",args.save_info)
    if args.info_only: return 0
    parameters_xml=args.parameters_xml.read_text(encoding="utf-8") if args.parameters_xml else apply_parameters(info_xml,json.loads(args.params.read_text(encoding="utf-8")) if args.params else {})
    LOG.info("Gerando relatorio"); guid=generate_report(service,args.report_id,parameters_xml,args.output.name,args.context); LOG.info("GUID recebido: %s...",guid[:8])
    size=get_size(service,guid); LOG.info("Tamanho: %d bytes",size); save_report(service,guid,size,args.output,args.chunk_size); LOG.info("PDF validado e salvo em %s",args.output); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (Fault,ValueError,RuntimeError,OSError,TypeError) as exc:
        LOG.error("Falha: %s",exc); raise SystemExit(1)
