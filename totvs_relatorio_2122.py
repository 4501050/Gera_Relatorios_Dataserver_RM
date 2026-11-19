#!/usr/bin/env python3
import argparse, ast, base64, logging, os, re
from getpass import getpass
from pathlib import Path
from uuid import UUID
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from zeep import Client, Settings
from zeep.exceptions import Fault
from zeep.transports import Transport

DEFAULT_WSDL = "https://institutopresbiteriano146532.rm.cloudtotvs.com.br:8051/wsReport/MEX?wsdl"
DEFAULT_REPORT_ID = 2122
OUTPUT_DIR = Path("Gerados")
PARAM_DIR = Path("Parametros")
LOG = logging.getLogger("totvs_wsreport")

def client(wsdl,user,pwd,verify,timeout):
    s=Session(); s.auth=HTTPBasicAuth(user,pwd); s.verify=verify
    s.mount("https://",HTTPAdapter(max_retries=Retry(total=3,backoff_factor=.7,status_forcelist=(429,502,503,504),allowed_methods=frozenset({"GET","POST"}))))
    return Client(wsdl=wsdl,transport=Transport(session=s,timeout=timeout,operation_timeout=timeout),settings=Settings(strict=False,xml_huge_tree=False,forbid_dtd=True,forbid_entities=True,forbid_external=True))

def bind_report(c):
    for sn,svc in c.wsdl.services.items():
        for pn,port in svc.ports.items():
            if "GetReportInfo" in port.binding._operations:
                LOG.info("Service selecionado: %s",sn); LOG.info("Port selecionado: %s",pn); return c.bind(sn,pn)
    raise RuntimeError("Port do wsReport nao localizado.")

def split_info(value):
    if isinstance(value,(list,tuple)) and len(value)>=2: return str(value[0]),str(value[1])
    if hasattr(value,"string"):
        a=list(value.string)
        if len(a)>=2:return str(a[0]),str(a[1])
    try:
        a=ast.literal_eval(str(value))
        if isinstance(a,(list,tuple)) and len(a)>=2:return str(a[0]),str(a[1])
    except Exception: pass
    raise RuntimeError("Formato inesperado no retorno de GetReportInfo.")

def parameter_names(x):
    return re.findall(r'<(?:\w+:)?ParamName>\s*([^<]+?)\s*</(?:\w+:)?ParamName>',str(x),flags=re.I)

def set_params(xml,values):
    text=str(xml); found=set()
    for name,value in values.items():
        pat=re.compile(r'(<(?:\w+:)?ParamName>\s*'+re.escape(name)+r'\s*</(?:\w+:)?ParamName>.*?<(?:\w+:)?Value(?:\s[^>]*)?>)(.*?)(</(?:\w+:)?Value>)',re.I|re.S)
        text,n=pat.subn(lambda m,v=str(value):m.group(1)+v+m.group(3),text,count=1)
        if n: found.add(name)
    missing=set(values)-found
    if missing: raise RuntimeError("Parametros nao encontrados: "+", ".join(sorted(missing)))
    return text

def main():
    ap=argparse.ArgumentParser(description="Gera Declaracao de Matricula TOTVS RM - relatorio 2122")
    ap.add_argument("--wsdl",default=os.getenv("TOTVS_WSDL",DEFAULT_WSDL)); ap.add_argument("--cod-coligada",type=int,default=int(os.getenv("TOTVS_CODCOLIGADA","1")))
    ap.add_argument("--ra"); ap.add_argument("--id-habilitacao-filial"); ap.add_argument("--id-perlet"); ap.add_argument("--contexto",default=os.getenv("TOTVS_CONTEXT","")); ap.add_argument("--info-only",action="store_true"); ap.add_argument("--timeout",type=int,default=90); ap.add_argument("--insecure",action="store_true")
    a=ap.parse_args(); logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    if not OUTPUT_DIR.is_dir(): raise RuntimeError("A pasta Gerados nao existe.")
    if not PARAM_DIR.is_dir(): raise RuntimeError("A pasta Parametros nao existe.")
    user=os.getenv("TOTVS_USERNAME") or input("Usuario tecnico TOTVS: ").strip(); pwd=os.getenv("TOTVS_PASSWORD") or getpass("Senha TOTVS: ")
    c=client(a.wsdl,user,pwd,not a.insecure,a.timeout); s=bind_report(c)
    LOG.info("Consultando metadados do relatorio %d",DEFAULT_REPORT_ID)
    filters,params=split_info(s.GetReportInfo(codColigada=a.cod_coligada,idReport=DEFAULT_REPORT_ID))
    (PARAM_DIR/f"report_{DEFAULT_REPORT_ID}_filters.xml").write_text(filters,encoding="utf-8"); (PARAM_DIR/f"report_{DEFAULT_REPORT_ID}_parameters.xml").write_text(params,encoding="utf-8")
    names=parameter_names(params); LOG.info("Parametros encontrados no relatorio %d: %s",DEFAULT_REPORT_ID,", ".join(names) if names else "nenhum")
    if a.info_only:return 0
    # No 2122 atual, P_CODCOLIGADA pode nao existir; codColigada ja e enviado separadamente ao wsReport.
    required={"P_RA","P_IDHABILITACAOFILIAL","P_IDPERLET"}; missing=required-set(names)
    if missing: raise RuntimeError("Parametros obrigatorios ausentes no relatorio 2122: "+", ".join(sorted(missing)))
    ra=a.ra or input("RA: ").strip(); hab=a.id_habilitacao_filial or input("IDHABILITACAOFILIAL: ").strip(); per=a.id_perlet or input("IDPERLET: ").strip()
    values={"P_RA":ra,"P_IDHABILITACAOFILIAL":hab,"P_IDPERLET":per}
    if "P_CODCOLIGADA" in names: values["P_CODCOLIGADA"]=a.cod_coligada
    params=set_params(params,values)
    output=OUTPUT_DIR/f"Declaracao_Matricula_{a.cod_coligada}_{ra}_{hab}_{per}.pdf"
    LOG.info("Gerando relatorio %d",DEFAULT_REPORT_ID)
    guid=str(s.GenerateReport(codColigada=a.cod_coligada,id=DEFAULT_REPORT_ID,filters=filters,parameters=params,fileName=output.name,contexto=a.contexto)).strip().strip("{}")
    UUID(guid); (PARAM_DIR/f"report_{DEFAULT_REPORT_ID}_guid.txt").write_text(guid,encoding="utf-8"); LOG.info("GUID: %s",guid)
    size=int(s.GetGeneratedReportSize(guid=guid)); b64=s.GetFileChunk(guid=guid,offset=0,length=size)
    if isinstance(b64,bytes):b64=b64.decode("ascii")
    b64="".join(str(b64).split()); b64 += "="*((-len(b64))%4); pdf=base64.b64decode(b64,validate=True)
    if not pdf.startswith(b"%PDF-"):raise RuntimeError("Arquivo retornado nao possui assinatura PDF valida.")
    output.write_bytes(pdf); LOG.info("PDF gerado e validado: %s",output.resolve()); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except (Fault,ValueError,RuntimeError,OSError,TypeError) as e: LOG.error("Falha: %s",e); raise SystemExit(1)
