#!/usr/bin/env python3
import argparse, ast, base64, logging, os, re
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

DEFAULT_WSDL="https://institutopresbiteriano146532.rm.cloudtotvs.com.br:8051/wsReport/MEX?wsdl"
LOG=logging.getLogger("totvs_wsreport")
NS="http://www.totvs.com.br/RM/"

def client(wsdl,user,pwd,verify,timeout):
 s=Session(); s.auth=HTTPBasicAuth(user,pwd); s.verify=verify
 s.mount("https://",HTTPAdapter(max_retries=Retry(total=3,backoff_factor=.7,status_forcelist=(429,502,503,504),allowed_methods=frozenset({"GET","POST"}))))
 return Client(wsdl=wsdl,transport=Transport(session=s,timeout=timeout,operation_timeout=timeout),settings=Settings(strict=False,xml_huge_tree=False,forbid_dtd=True,forbid_entities=True,forbid_external=True))

def bind_report(c):
 for sn,s in c.wsdl.services.items():
  for pn,p in s.ports.items():
   if "GetReportInfo" in p.binding._operations:
    LOG.info("Service selecionado: %s",sn); LOG.info("Port selecionado: %s",pn); return c.bind(sn,pn)
 raise RuntimeError("Port do wsReport nao localizado")

def report_info(s,coligada,rid): return s.GetReportInfo(codColigada=coligada,idReport=rid)

def split_info(value):
 # zeep normalmente devolve lista/array; preserva XML exatamente como recebido.
 if isinstance(value,(list,tuple)) and len(value)>=2: return str(value[0]),str(value[1])
 if hasattr(value,'string'):
  a=list(value.string)
  if len(a)>=2:return str(a[0]),str(a[1])
 text=str(value)
 try:
  a=ast.literal_eval(text)
  if isinstance(a,(list,tuple)) and len(a)>=2:return str(a[0]),str(a[1])
 except Exception: pass
 raise RuntimeError("Formato inesperado no retorno de GetReportInfo")

def set_params(xml_text, values):
 # O XML serializado pelo RM contem um namespace .NET que nao e URI valida
 # segundo o libxml2/lxml. Nao reserializamos o documento: alteramos somente
 # os textos de <ParamName>...<Value>, preservando o restante byte a byte.
 text = str(xml_text)
 found = set()
 for name, value in values.items():
  pattern = re.compile(
   r'(<(?:\w+:)?ParamName>\s*' + re.escape(name) +
   r'\s*</(?:\w+:)?ParamName>.*?<(?:\w+:)?Value(?:\s[^>]*)?>)(.*?)(</(?:\w+:)?Value>)',
   re.IGNORECASE | re.DOTALL
  )
  replacement = lambda m, v=str(value): m.group(1) + v + m.group(3)
  text, count = pattern.subn(replacement, text, count=1)
  if count:
   found.add(name)
 missing = set(values) - found
 if missing:
  raise RuntimeError("Parametros nao encontrados no XML: " + ", ".join(sorted(missing)))
 return text

def parse_result(v):
 if isinstance(v,bytes): return v.decode()
 return str(v).strip().strip('{}')

def main():
 ap=argparse.ArgumentParser(description="Gera o relatorio RM 2122")
 ap.add_argument('--wsdl',default=os.getenv('TOTVS_WSDL',DEFAULT_WSDL)); ap.add_argument('--cod-coligada',type=int,default=int(os.getenv('TOTVS_CODCOLIGADA','1')))
 ap.add_argument('--report-id',type=int,default=2122); ap.add_argument('--ra'); ap.add_argument('--id-habilitacao-filial'); ap.add_argument('--id-perlet')
 ap.add_argument('--contexto',default=os.getenv('TOTVS_CONTEXT','')); ap.add_argument('--output',type=Path,default=Path('relatorio_2122.pdf')); ap.add_argument('--info-only',action='store_true'); ap.add_argument('--timeout',type=int,default=90); ap.add_argument('--insecure',action='store_true')
 a=ap.parse_args(); logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
 user=os.getenv('TOTVS_USERNAME') or input('Usuario tecnico TOTVS: ').strip(); pwd=os.getenv('TOTVS_PASSWORD') or getpass('Senha TOTVS: ')
 c=client(a.wsdl,user,pwd,not a.insecure,a.timeout); s=bind_report(c)
 LOG.info("Consultando metadados do relatorio %d",a.report_id); raw=report_info(s,a.cod_coligada,a.report_id); filters,params=split_info(raw)
 Path('report_2122_filters.xml').write_text(filters,encoding='utf-8'); Path('report_2122_parameters.xml').write_text(params,encoding='utf-8')
 if a.info_only: LOG.info("Metadados separados e salvos."); return 0
 ra=a.ra or input('RA: ').strip(); hab=a.id_habilitacao_filial or input('IDHABILITACAOFILIAL: ').strip(); per=a.id_perlet or input('IDPERLET: ').strip()
 if not all([ra,hab,per]): raise ValueError('RA, IDHABILITACAOFILIAL e IDPERLET sao obrigatorios.')
 # Nome padrao obrigatorio do arquivo final:
 # Declaracao_Matricula_<CODCOLIGADA>_<RA>_<IDHABILITACAOFILIAL>_<IDPERLET>.pdf
 safe_parts=[str(a.cod_coligada), ra, hab, per]
 if any(any(ch in part for ch in '<>:"/\\|?*') for part in safe_parts):
  raise ValueError('Os identificadores contem caracteres invalidos para nome de arquivo no Windows.')
 a.output=Path(f"Declaracao_Matricula_{a.cod_coligada}_{ra}_{hab}_{per}.pdf")
 params=set_params(params,{'CODCOLIGADA':a.cod_coligada,'RA':ra,'IDHABILITACAOFILIAL':hab,'IDPERLET':per})
 LOG.info("Gerando relatorio %d",a.report_id)
 LOG.info("Arquivo de saida: %s",a.output.name)
 guid=parse_result(s.GenerateReport(codColigada=a.cod_coligada,id=a.report_id,filters=filters,parameters=params,fileName=a.output.name,contexto=a.contexto)); UUID(guid); LOG.info("GUID: %s",guid)
 LOG.info("GenerateReport concluido. GUID salvo em report_2122_guid.txt")
 Path('report_2122_guid.txt').write_text(guid,encoding='utf-8')

 # Contrato confirmado no WSDL do ambiente:
 # GetGeneratedReportSize(guid) informa o tamanho da string Base64.
 # GetFileChunk(guid, offset, length) devolve essa string em xsd:string.
 b64_size = int(s.GetGeneratedReportSize(guid=guid))
 if b64_size <= 0:
  raise RuntimeError(f"Tamanho Base64 invalido retornado pelo RM: {b64_size}")
 if b64_size > 140 * 1024 * 1024:
  raise RuntimeError(f"Conteudo Base64 excede o limite de seguranca: {b64_size} caracteres")
 LOG.info("Tamanho Base64 informado pelo RM: %d caracteres", b64_size)

 # IMPORTANTE: neste wsReport o arquivo temporario pode ser removido apos
 # GetFileChunk. Por isso recuperamos toda a string Base64 em uma unica chamada.
 b64_text = s.GetFileChunk(guid=guid, offset=0, length=b64_size)
 if b64_text is None:
  raise RuntimeError("GetFileChunk retornou conteudo vazio")
 if isinstance(b64_text, bytes):
  b64_text = b64_text.decode('ascii')
 b64_text = ''.join(str(b64_text).split())
 LOG.info("Base64 recebido: %d caracteres", len(b64_text))

 # Algumas implementacoes podem omitir padding final; completa-o de forma segura.
 padding = (-len(b64_text)) % 4
 if padding:
  b64_text += '=' * padding
 try:
  pdf_data = base64.b64decode(b64_text, validate=True)
 except Exception as exc:
  raise RuntimeError(f"Conteudo retornado por GetFileChunk nao e Base64 valido: {exc}") from exc

 if not pdf_data:
  raise RuntimeError("PDF decodificado esta vazio")
 if not pdf_data.startswith(b'%PDF-'):
  raise RuntimeError("Arquivo decodificado nao possui assinatura PDF valida (%PDF-)")
 a.output.write_bytes(pdf_data)
 LOG.info("PDF decodificado: %d bytes", len(pdf_data))
 LOG.info("PDF gerado e validado: %s", a.output.resolve())
 return 0

if __name__=='__main__':
 try: raise SystemExit(main())
 except (Fault,ValueError,RuntimeError,OSError,TypeError) as e: LOG.error("Falha: %s",e); raise SystemExit(1)
