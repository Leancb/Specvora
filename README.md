# Specvora

**Autonomous Quality Engineering — from requirements to release confidence.**

**Autor e fundador:** Leandro Brum https://www.linkedin.com/in/leandro-brum-a5a8ab31/

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

Status: feature-complete training MVP. See `CHANGELOG.md` and
`docs/RELEASE_CHECKLIST.md` before creating tag `v0.1.0`. This status does not declare the local
state, runtime bearer or training portal suitable for production network exposure.

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

### Índice completo dos 44 módulos

#### Fundamentos determinísticos — módulos 01–09

1. [Análise determinística de OpenAPI](docs/modules/01_DETERMINISTIC_OPENAPI_ANALYSIS.md)
2. [Resultados, auditoria e confiança de release](docs/modules/02_RELEASE_CONFIDENCE.md)
3. [Geração determinística de dados de schema](docs/modules/03_SCHEMA_DATA_GENERATION.md)
4. [Referências e composição segura de schemas](docs/modules/04_SAFE_SCHEMA_REFERENCES.md)
5. [Ingestão controlada de evidências Pytest](docs/modules/05_PYTEST_EVIDENCE_INGESTION.md)
6. [Executor Pytest local controlado](docs/modules/06_CONTROLLED_LOCAL_RUNNER.md)
7. [Casos completos para variantes de união](docs/modules/07_SCHEMA_UNION_VARIANTS.md)
8. [Validação de casos e diagnóstico de uniões](docs/modules/08_SCHEMA_CASE_VALIDATION.md)
9. [Gate determinístico da geração](docs/modules/09_GENERATION_QUALITY_GATE.md)

#### Web, IA e revisão humana — módulos 10–18

10. [Geração determinística de jornadas Playwright](docs/modules/10_PLAYWRIGHT_JOURNEY_GENERATION.md)
11. [Execução Playwright controlada](docs/modules/11_CONTROLLED_PLAYWRIGHT_EXECUTION.md)
12. [Evidências Playwright e confiança de release](docs/modules/12_PLAYWRIGHT_EVIDENCE.md)
13. [Propostas de cenários por IA governada](docs/modules/13_GOVERNED_AI_PROPOSALS.md)
14. [Revisão humana e promoção de propostas](docs/modules/14_HUMAN_PROPOSAL_PROMOTION.md)
15. [Isolamento de saída de rede](docs/modules/15_NETWORK_EGRESS_ISOLATION.md)
16. [Portal multiprojeto de revisão humana](docs/modules/16_MULTIPROJECT_REVIEW_PORTAL.md)
17. [Aprovações assinadas e decisão combinada](docs/modules/17_SIGNED_APPROVALS_COMBINED_RELEASE.md)
18. [Autorização assinada no portal e executores](docs/modules/18_SIGNED_AUTHORIZATION_INTEGRATION.md)

#### Testes promovidos e CI governada — módulos 19–26

19. [Geração de testes a partir de cenários promovidos](docs/modules/19_PROMOTED_TEST_GENERATION.md)
20. [Fixtures controladas de resiliência](docs/modules/20_CONTROLLED_RESILIENCE_FIXTURES.md)
21. [Geração promovida pelo portal](docs/modules/21_PORTAL_PROMOTED_GENERATION.md)
22. [Execução governada de fixtures no CI](docs/modules/22_GOVERNED_CI_FIXTURES.md)
23. [Ledger durável e atômico de aprovações](docs/modules/23_DURABLE_APPROVAL_LEDGER.md)
24. [Sessões autenticadas e papéis do portal](docs/modules/24_AUTHENTICATED_PORTAL_ROLES.md)
25. [Adaptadores controlados de autenticação e dependência](docs/modules/25_CONTROLLED_AUTH_DEPENDENCY_ADAPTERS.md)
26. [Broker de credenciais em runtime](docs/modules/26_RUNTIME_CREDENTIAL_BROKER.md)

#### Identidade e estado transacional — módulos 27–36

27. [Autenticação multifator TOTP](docs/modules/27_PORTAL_TOTP_MFA.md)
28. [Estado transacional das sessões](docs/modules/28_TRANSACTIONAL_PORTAL_SESSION_STATE.md)
29. [Contrato do backend de estado](docs/modules/29_PORTAL_STATE_BACKEND_CONTRACT.md)
30. [Adaptador HTTP centralizado de estado](docs/modules/30_CENTRALIZED_HTTP_STATE_ADAPTER.md)
31. [Serviço central de estado do portal](docs/modules/31_CENTRAL_PORTAL_STATE_SERVICE.md)
32. [Rotação da confiança do serviço de estado](docs/modules/32_ROTATING_STATE_SERVICE_TRUST.md)
33. [Limitação transacional de tentativas de login](docs/modules/33_TRANSACTIONAL_LOGIN_THROTTLING.md)
34. [Recuperação MFA de uso único](docs/modules/34_ONE_USE_MFA_RECOVERY.md)
35. [Eventos estruturados de segurança](docs/modules/35_PORTAL_SECURITY_EVENTS.md)
36. [Exportação segura de eventos para SIEM](docs/modules/36_SAFE_SIEM_EXPORT.md)

#### Federação OIDC e operação monitorada — módulos 37–44

37. [Validação estrita de identidade OIDC](docs/modules/37_STRICT_OIDC_IDENTITY_VALIDATION.md)
38. [Authorization Code + PKCE de uso único](docs/modules/38_ONE_USE_OIDC_PKCE_FLOW.md)
39. [Login federado no portal](docs/modules/39_FEDERATED_PORTAL_LOGIN.md)
40. [Descoberta OIDC fixada e rotação JWKS](docs/modules/40_PINNED_OIDC_DISCOVERY_ROTATION.md)
41. [Mudanças de confiança OIDC aprovadas independentemente](docs/modules/41_APPROVED_OIDC_TRUST_CHANGES.md)
42. [Monitoramento determinístico da confiança OIDC](docs/modules/42_OIDC_TRUST_MONITORING.md)
43. [Entrega autenticada e idempotente de alertas](docs/modules/43_AUTHENTICATED_OIDC_ALERT_DELIVERY.md)
44. [Ciclos monitorados com lease transacional](docs/modules/44_LEASED_OIDC_MONITOR_CYCLES.md)

Os exercícios correspondentes estão em [`docs/training`](docs/training) e a ordem didática está
no [guia de treinamento](docs/TRAINING_GUIDE.md). O estado e os limites de cada etapa aparecem no
[roadmap](docs/ROADMAP.md).

### Evolução detalhada recente

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

O módulo 23 impede replay entre runners hospedados ao consumir cada aprovação em uma referência
Git criada atomicamente antes da execução. Consulte
`docs/modules/23_DURABLE_APPROVAL_LEDGER.md`.

O módulo 24 adiciona sessões assinadas, CSRF e papéis explícitos ao portal local sem substituir
a aprovação Ed25519 offline. Consulte `docs/modules/24_AUTHENTICATED_PORTAL_ROLES.md`.

O módulo 25 adiciona adaptadores controlados para cenários promovidos de autenticação e falhas
de dependência. Somente cabeçalhos dedicados e valores não secretos enumerados são aceitos;
operações autenticadas sem adaptador e declarações ambíguas são bloqueadas antes da geração.

O módulo 26 adiciona referências de credencial por alias à execução assinada. O valor bearer é
fornecido pelo operador apenas em tempo de execução, não aparece em planos ou evidências e é
removido da saída capturada. Consulte `docs/modules/26_RUNTIME_CREDENTIAL_BROKER.md`.

O módulo 27 adiciona enrollment TOTP por usuário, revogação das sessões anteriores e rejeição
local de códigos reutilizados. Consulte `docs/modules/27_PORTAL_TOTP_MFA.md`; federação externa,
recuperação, rate limiting e estado multinó continuam fora desta fronteira local.

O módulo 28 adiciona sessões revogáveis e consumo atômico de contadores TOTP em SQLite. É uma
fronteira transacional de host único, não um datastore distribuído. Consulte
`docs/modules/28_TRANSACTIONAL_PORTAL_SESSION_STATE.md`.

O módulo 29 separa autenticação e persistência por um contrato de backend fail-closed, mantendo
SQLite local e preparando um adaptador centralizado verificável.

O módulo 30 implementa o cliente HTTPS desse contrato, com autenticação de serviço em runtime,
timeout e validação estrita. O serviço central continua uma implantação independente.

O módulo 31 implementa o serviço central do contrato para integração controlada, preservando
sessões revogáveis e consumo atômico de MFA. O backend SQLite e o bearer estático continuam sendo
fronteiras de treinamento; produção exige datastore operado, TLS e identidade de workload.

O módulo 32 adiciona um trust file estrito com hashes e janelas UTC para rotação sobreposta das
credenciais do serviço. Bearers em texto claro permanecem fora do arquivo; identidade de workload
e leases auditáveis continuam como evolução de produção.

O módulo 33 adiciona limite transacional de tentativas de login por hash normalizado do usuário,
compartilhado entre SQLite e serviço central. Mensagens continuam genéricas e o sucesso completo
limpa a janela; controles de borda e telemetria de abuso continuam necessários em produção.

O módulo 34 adiciona códigos de recuperação MFA de uso único, gerados explicitamente pelo
operador e persistidos somente como digests. O consumo e a rotação usam estado transacional e
revogam sessões anteriores, sem ampliar a autoridade para execução ou release.

O módulo 35 registra eventos estruturados de login, bloqueio e recuperação no backend
transacional. A trilha contém somente tipos enumerados, hash do sujeito e horário; exportação para
SIEM, retenção e alertas permanecem controles de produção.

O módulo 36 exporta esses eventos incrementalmente para um coletor HTTPS autorizado, com lote
idempotente, retentativas limitadas e checkpoint atualizado somente após confirmação. O bearer
permanece em runtime; workload identity e operação do receptor continuam pendentes para produção.

O módulo 37 adiciona validação OIDC estrita de ID tokens `RS256`, vinculando issuer, audience,
nonce, tempo e JWKS confiável. Identidades externas só recebem papéis locais preexistentes.

O módulo 38 adiciona Authorization Code + PKCE `S256`, `state` persistido somente como digest e
troca de código confinada a endpoint HTTPS em allowlist. A identidade federada continua sem
autoridade para aprovar execução ou release.

O módulo 39 conecta esse fluxo às rotas do portal e à sessão local revogável. O provedor confirma
a identidade, mas usuários ativos, papéis e capacidades continuam definidos pelo Specvora.

O módulo 40 adiciona descoberta OIDC sob issuer fixado e rotação JWKS controlada. Hosts são
permitidos explicitamente, a troca exige sobreposição de chaves e o trust file só muda após
validação completa e gravação atômica.

O módulo 41 transforma essa rotação em mudança governada: uma pessoa aprova offline o artefato
exato, outra o aplica, a autorização é consumida uma vez e os hashes entram numa trilha encadeada.

O módulo 42 monitora essa confiança em modo somente leitura. Mudança sobreposta pede revisão;
descontinuidade, adulteração local ou auditoria inválida bloqueiam, sem rotação automática.

O módulo 43 entrega esses alertas a um receptor HTTPS autenticado e permitido, com payload fixo,
idempotência estável e retentativas limitadas. A notificação não recebe autoridade sobre o JWKS.

O módulo 44 executa monitoramento e entrega em um ciclo único com lease transacional e histórico
SQLite sem segredos. O agendamento local exige autorização explícita e nunca roda rotação de trust.

### Documentos gerais

- [Produto](docs/PRODUCT.md): proposta comercial e público-alvo;
- [Arquitetura](docs/ARCHITECTURE.md): componentes e fluxo;
- [Segurança](docs/SECURITY.md): modelo de ameaças e controles;
- [Roadmap](docs/ROADMAP.md): caminho do MVP à operação;
- [Apresentação](docs/PRESENTATION.md): roteiro de apresentação profissional;
- [CI/CD](docs/CI_CD.md): integração na esteira;
- [Changelog](CHANGELOG.md): histórico de versões;
- [Checklist da release](docs/RELEASE_CHECKLIST.md): validações para publicar a versão.

