# Specvora

**Autonomous Quality Engineering — from requirements to release confidence.**

**Autor e fundador:** Leandro do Couto Brum

Specvora transforma requisitos e contratos OpenAPI em uma estratégia de qualidade
rastreável, um projeto de testes automatizados e uma decisão objetiva para a esteira
de entrega. A IA propõe; políticas determinísticas validam; pessoas mantêm a autoridade.

## Valor para o cliente

- reduz o tempo entre requisito e primeira suíte automatizada;
- liga requisito, risco, cenário, teste e resultado em uma única trilha;
- gera testes legíveis e pertencentes ao cliente, sem aprisionamento tecnológico;
- começa por APIs e evolui para jornadas web com Playwright;
- bloqueia execução fora de hosts autorizados e exige aprovação humana;
- entrega evidência pronta para CI/CD e auditoria.

## MVP 0.1

Módulo 18: decisões no portal e execuções controladas exigem assinatura por padrão.
Antes de atualizar seu servidor, consulte `docs/training/MODULE_18_LAB.md` para configurar
chave pública/identidade/ledger ou selecionar explicitamente o modo de laboratório local.

O fluxo atual recebe requisitos em texto e uma especificação OpenAPI, identifica
operações, gera cenários positivos e negativos, cria testes Pytest/HTTPX e produz
uma matriz de rastreabilidade. O modo determinístico funciona sem custos de IA.
O modo assistido por OpenAI é opcional e nunca executa código proposto sem validação.
Jornadas web declarativas geram Playwright e podem usar um executor controlado após gate
determinístico e aprovação humana específica.
Relatórios Pytest e Playwright são normalizados em evidências com hash antes de alimentar
o mesmo cálculo explicável de release confidence e o log de auditoria.
O modo opcional de IA propõe cenários em formato estruturado, registra proveniência e
submete cada vínculo e status a políticas determinísticas antes da revisão humana.
Uma revisão humana completa pode promover apenas o cenário aceito para um catálogo
imutável e não executável, mantendo geração e autorização como fronteiras posteriores.
Políticas de saída aprovadas podem fixar o destino em IP e porta e ser aplicadas por um
contêiner Linux com `nftables`, bloqueando por padrão qualquer outra conexão de rede.
O portal local mantém múltiplos projetos e uma fila durável de revisão em SQLite, permitindo
que uma pessoa examine propostas e registre decisões imutáveis sem conceder autoridade à IA.

## Início rápido

```powershell
cd D:\Specvora
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn specvora.main:app --reload --port 8100
```

Acesse `http://localhost:8100/portal` para o portal ou `http://localhost:8100/docs`
para a API técnica.

## Demonstração por linha de comando

```powershell
specvora analyze examples\petstore_project.json
```

O resultado é criado em `workspaces/<project-id>/generated/` e inclui plano,
matriz, testes e workflow do GitHub Actions.

## Segurança

Specvora não deve apontar para produção sem autorização formal. A execução usa
allowlist de hosts, comandos fixos, timeout e diretórios confinados. Credenciais
ficam em arquivos ignorados pelo Git. Para execução hostil, use também o perfil isolado
descrito em `docs/modules/15_NETWORK_EGRESS_ISOLATION.md`. Consulte `docs/SECURITY.md`.

## Documentação

O módulo 19 adiciona `specvora generate-promoted`: geração de Pytest/HTTPX a partir
de cenários promovidos, com vínculos explícitos e gate determinístico. Não executa testes.
Consulte [o módulo](docs/modules/19_PROMOTED_TEST_GENERATION.md) e
[o laboratório](docs/training/MODULE_19_LAB.md).

O módulo 20 permite casos 429/503 somente quando o contrato documenta a resposta e declara
uma fixture controlada. Inclui um alvo local de treinamento, sem remover a autorização
assinada de execução. Consulte `docs/modules/20_CONTROLLED_RESILIENCE_FIXTURES.md`.

O módulo 21 permite selecionar casos e gerar planos imutáveis no portal local. A interface
não assina nem executa testes. Consulte `docs/modules/21_PORTAL_PROMOTED_GENERATION.md`.

O módulo 22 adiciona ações assináveis portáveis e execução manual de fixtures no GitHub
Actions sem disponibilizar a chave privada. Consulte `docs/modules/22_GOVERNED_CI_FIXTURES.md`.

O módulo 17 adiciona `specvora-governance` para aprovações Ed25519 e avaliação conjunta
de resultados API/web. O módulo 18 integra essa verificação ao portal e aos executores.
Consulte `docs/modules/17_SIGNED_APPROVALS_COMBINED_RELEASE.md` e o laboratório correspondente.

- `docs/PRODUCT.md`: proposta comercial e público-alvo;
- `docs/ARCHITECTURE.md`: componentes e fluxo;
- `docs/SECURITY.md`: modelo de ameaças e controles;
- `docs/ROADMAP.md`: caminho de MVP a SaaS;
- `docs/PRESENTATION.md`: roteiro de apresentação profissional;
- `docs/CI_CD.md`: integração na esteira.

