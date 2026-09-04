# Laboratório 19 — Da proposta aprovada ao teste rastreável

## Objetivo

Separar aprovação de uma ideia, geração de dados, qualidade do teste e autorização de execução.
Não precisa de chave OpenAI nem envia requisições para a API durante a geração.

## 1. Verificação local

No PowerShell, com o ambiente virtual ativo:

```powershell
cd D:\Specvora
python -m pytest tests/test_promoted_generation.py -q
specvora generate-promoted --help
```

Os testes criam um contrato e decisões temporários, geram um caso positivo e um negativo
e verificam as chamadas HTTP com uma substituição local, sem tráfego de rede.

## 2. Preparar um catálogo real

Localize o projeto, a proposta original, a decisão, o registro de revisão e o catálogo
produzidos pela revisão humana. Use os caminhos reais registrados no seu ambiente;
o arquivo de projeto não substitui a proposta. Não altere os arquivos aprovados.

Crie `bindings.json` dentro do workspace, inicialmente com `{"bindings":[]}`.
O comando abaixo é um modelo: substitua TODOS os caminhos ilustrativos antes de executar.

```powershell
specvora generate-promoted CAMINHO_DO_PROJETO.json `
  --proposal CAMINHO_DA_PROPOSTA.json `
  --decision CAMINHO_DA_DECISAO.json `
  --review CAMINHO_DO_REGISTRO.json `
  --catalog CAMINHO_DO_CATALOGO.json `
  --bindings bindings.json `
  --output-dir workspaces\petstore-demo\promoted-generated\plan-001 `
  --workspace-root D:\Specvora
```

Abra `promotion-plan.json` no diretório de saída. Com vínculos vazios, o bloqueio é
esperado. Compare o catálogo com `available_cases` e prepare os vínculos adequados.
Cada entrada tem `scenario_id` e `case_id`. Execute novamente com uma NOVA pasta de saída,
como `plan-002`; saídas anteriores não são sobrescritas.

## 3. Interpretar o resultado

READY_FOR_HUMAN_APPROVAL permite revisar os testes, não executá-los automaticamente.
Confira a matriz, os parâmetros e os status antes de preparar uma nova autorização
assinada de execução pelo fluxo do módulo 18. Não compartilhe a chave privada.

Se o catálogo aprovado contém 429 ou 503, o resultado correto neste módulo é BLOCKED:
faltam condições controladas de limite de requisições ou falha de dependência.
Não troque o status esperado nem desative a política para fazer o teste passar.

## Apresentação de dois minutos

Mostre a cadeia requisito → proposta → decisão humana → caso determinístico → teste.
Depois mostre um caso bloqueado. Explique que hashes detectam divergências, mas não
autenticam sozinhos o autor; a execução exige autorização assinada independente.

Critério de conclusão: demonstrar geração positiva/negativa, bloqueio sem fixture,
rastreabilidade e rejeição de adulteração, sem confundir geração com execução.
