# Laboratório 20 — Fixtures controladas para 429 e 503

## Objetivo

Transformar os dois cenários promovidos do Petstore em testes geráveis sem fingir falhas
de produção. O alvo local responde de modo determinístico a um cabeçalho reservado.

## Procedimento

1. Atualize o projeto com o pacote do módulo 20 e reinstale `.[dev]`.
2. Em um PowerShell, inicie somente o alvo de treinamento:

```powershell
cd D:\Specvora
.\.venv\Scripts\Activate.ps1
python -m uvicorn specvora.fixture_app:app --host 127.0.0.1 --port 8080
```

3. Em outro PowerShell, crie `bindings-module20.json` em UTF-8 sem BOM:

```powershell
$json = '{"bindings":[{"scenario_id":"PROM-AI-001","case_id":"getPet-valid"},{"scenario_id":"PROM-AI-002","case_id":"getPet-valid"}]}'
[IO.File]::WriteAllText('D:\Specvora\bindings-module20.json', $json, (New-Object Text.UTF8Encoding($false)))
```

4. Execute `generate-promoted` usando os mesmos cinco artefatos da `review-001`, o novo
arquivo de vínculos e uma pasta nova `plan-002`. Inspecione o gate e os casos; não execute
o arquivo Pytest diretamente.

5. Para executar, prepare uma autorização nova com o hash exato de `plan-002` e use o
runner assinado do módulo 18 contra `http://127.0.0.1:8080`. A chave privada permanece offline.

## Evidência esperada

O plano fica READY_FOR_HUMAN_APPROVAL e contém dois casos com baseline `getPet-valid`.
Somente cada cenário negativo recebe seu valor de `X-Specvora-Fixture`. O alvo retorna
429 e 503 de modo controlado. Alterar o cabeçalho, os artefatos ou reutilizar a assinatura
deve impedir uma execução autorizada.

Explique na apresentação por que documentar o status, preparar a condição e autorizar a
execução são decisões separadas.
