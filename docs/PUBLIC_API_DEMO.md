# Demonstração com uma API pública

O alvo é [JSONPlaceholder](https://jsonplaceholder.typicode.com/), um serviço externo gratuito
para prototipação e testes. Os dados são fictícios; a conexão e as respostas HTTP são reais.
Não é uma API de um cliente nem uma prova de desempenho em produção.

## Gerar os testes pelo Specvora

Na raiz do repositório, com o ambiente virtual ativado:

```powershell
specvora analyze examples\jsonplaceholder_project.json
```

Abra `workspaces/jsonplaceholder-demo/generated/test_generated_api.py`, `quality-plan.json`
e `quality-gate.json`. Serão gerados três testes positivos GET para:

- `https://jsonplaceholder.typicode.com/posts`;
- `https://jsonplaceholder.typicode.com/posts/1`;
- `https://jsonplaceholder.typicode.com/posts/1/comments`.

O arquivo OpenAPI é um recorte escrito pelo Specvora a partir do
[guia oficial](https://jsonplaceholder.typicode.com/guide/), não uma especificação oficial.
Usa caminhos de exemplo concretos porque o gerador básico não substitui parâmetros de caminho.
Esses testes gerados validam status HTTP; não alegam validar regras de negócio ou schemas de resposta.
Sua execução pelo runner continua exigindo a aprovação assinada normal.

## Verificar respostas externas agora

O diagnóstico complementar faz somente três GET sequenciais, sem credenciais, redirects ou
retentativas. Confere identidade e campos do post e o vínculo dos comentários.
É um script escrito manualmente para este exemplo, não código gerado pelo Specvora e não
produz autorização ou recomendação de release.

```powershell
$session = [guid]::NewGuid().ToString("N")
python examples\jsonplaceholder\check_live.py --output "workspaces\jsonplaceholder-demo\diagnostics\$session.json"
```

O relatório registra destino, horário, caminhos, status HTTP e resultado das verificações.
`passed: true` confirma apenas os critérios listados naquele instante.
Falhas de rede ou indisponibilidade do serviço público também podem reprovar a execução.
O diagnóstico usa as autoridades certificadoras do sistema via `ssl.create_default_context()`.
O gerador básico usa a configuração TLS padrão do HTTPX; neste ambiente ela apresentou
`CERTIFICATE_VERIFY_FAILED`. A execução assinada da suíte gerada não foi realizada nesta etapa.
O diagnóstico não é executado automaticamente nos testes internos nem no CI.

O próximo passo para um piloto é fornecer o contrato de uma API autorizada do cliente e adicionar
critérios de negócio acordados com ele.
