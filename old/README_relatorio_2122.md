# Gerador do relatório 2122 - TOTVS RM WsReport

## Requisitos

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1. Defina as credenciais sem gravá-las no código

```powershell
$env:TOTVS_USERNAME = "usuario_tecnico"
$env:TOTVS_PASSWORD = "senha"
$env:TOTVS_CONTEXT = "CODCOLIGADA=1;CODSISTEMA=S;CODUSUARIO=usuario_tecnico"
```

## 2. Consulte o contrato do relatório 2122

```powershell
python totvs_relatorio_2122.py --info-only
```

O comando grava `report_2122_info.xml`. Verifique nesse XML os nomes exatos dos parâmetros.

## 3. Crie `parametros_2122.json`

Exemplo ilustrativo (substitua pelos nomes retornados por GetReportInfo):

```json
{
  "P_CODCOLIGADA": 1,
  "P_RA": "00000000"
}
```

## 4. Gere o PDF

```powershell
python totvs_relatorio_2122.py --params parametros_2122.json --output relatorio_2122.pdf
```

Se o XML retornado pelo RM tiver uma estrutura não reconhecida pelo preenchimento automático, edite uma cópia do XML de informações com os valores corretos e execute:

```powershell
python totvs_relatorio_2122.py --parameters-xml parametros_2122.xml --output relatorio_2122.pdf
```

## Diagnóstico

```powershell
python totvs_relatorio_2122.py --list-operations
python totvs_relatorio_2122.py --info-only --verbose
```

Use `--insecure` somente para diagnóstico transitório em homologação quando houver certificado interno. Não use em produção.
