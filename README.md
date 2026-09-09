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

MVP local de treinamento, com 44 módulos documentados. Consulte o [changelog](CHANGELOG.md)
e o [checklist de release](docs/RELEASE_CHECKLIST.md) para acompanhar a preparação da versão 0.1.0.
A operação em produção ainda depende dos itens descritos no [roadmap](docs/ROADMAP.md).

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

Para um alvo externo, consulte a [demonstração com JSONPlaceholder](docs/PUBLIC_API_DEMO.md).
Ela inclui um contrato de leitura, geração de três testes e um diagnóstico das respostas reais.

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
   Transforma requisitos e um contrato OpenAPI em cenários, plano de qualidade e testes inspecionáveis.

2. [Resultados, auditoria e confiança de release](docs/modules/02_RELEASE_CONFIDENCE.md)  
   Calcula uma recomendação de release a partir dos resultados e registra uma trilha de auditoria encadeada.

3. [Geração determinística de dados de schema](docs/modules/03_SCHEMA_DATA_GENERATION.md)  
   Produz dados de requisição a partir das restrições declaradas no JSON Schema.

4. [Referências e composição segura de schemas](docs/modules/04_SAFE_SCHEMA_REFERENCES.md)  
   Resolve referências internas e composições de schema dentro do subconjunto suportado.

5. [Ingestão controlada de evidências Pytest](docs/modules/05_PYTEST_EVIDENCE_INGESTION.md)  
   Normaliza relatórios Pytest em evidências com hash e indicadores de resultado.

6. [Executor Pytest local controlado](docs/modules/06_CONTROLLED_LOCAL_RUNNER.md)  
   Executa arquivos Pytest aprovados com comando fixo, limite de tempo e diretórios confinados.

7. [Casos completos para variantes de união](docs/modules/07_SCHEMA_UNION_VARIANTS.md)  
   Gera casos para as alternativas declaradas em oneOf e anyOf.

8. [Validação de casos e diagnóstico de uniões](docs/modules/08_SCHEMA_CASE_VALIDATION.md)  
   Verifica os casos gerados contra o schema e identifica ambiguidades nas uniões.

9. [Gate determinístico da geração](docs/modules/09_GENERATION_QUALITY_GATE.md)  
   Bloqueia a geração inadequada e indica quando os artefatos estão prontos para revisão humana.


#### Web, IA e revisão humana — módulos 10–18

10. [Geração determinística de jornadas Playwright](docs/modules/10_PLAYWRIGHT_JOURNEY_GENERATION.md)  
   Converte jornadas web declaradas em testes Playwright e artefatos de planejamento.

11. [Execução Playwright controlada](docs/modules/11_CONTROLLED_PLAYWRIGHT_EXECUTION.md)  
   Executa jornadas aprovadas com controles de destino, tempo e acesso pelo navegador.

12. [Evidências Playwright e confiança de release](docs/modules/12_PLAYWRIGHT_EVIDENCE.md)  
   Incorpora resultados Playwright à evidência normalizada e à avaliação de release.

13. [Propostas de cenários por IA governada](docs/modules/13_GOVERNED_AI_PROPOSALS.md)  
   Recebe propostas estruturadas de IA, registra proveniência e aplica validações determinísticas.

14. [Revisão humana e promoção de propostas](docs/modules/14_HUMAN_PROPOSAL_PROMOTION.md)  
   Registra decisões humanas e promove os cenários aceitos para um catálogo imutável.

15. [Isolamento de saída de rede](docs/modules/15_NETWORK_EGRESS_ISOLATION.md)  
   Produz políticas de saída de rede para execução isolada com bloqueio por padrão.

16. [Portal multiprojeto de revisão humana](docs/modules/16_MULTIPROJECT_REVIEW_PORTAL.md)  
   Organiza projetos e propostas em uma fila persistente de revisão humana.

17. [Aprovações assinadas e decisão combinada](docs/modules/17_SIGNED_APPROVALS_COMBINED_RELEASE.md)  
   Verifica aprovações Ed25519 de uso único e combina avaliações de API e web.

18. [Autorização assinada no portal e executores](docs/modules/18_SIGNED_AUTHORIZATION_INTEGRATION.md)  
   Exige a autorização assinada nas decisões do portal e nos executores controlados.


#### Testes promovidos e CI governada — módulos 19–26

19. [Geração de testes a partir de cenários promovidos](docs/modules/19_PROMOTED_TEST_GENERATION.md)  
   Vincula cenários promovidos a casos determinísticos para gerar testes rastreáveis.

20. [Fixtures controladas de resiliência](docs/modules/20_CONTROLLED_RESILIENCE_FIXTURES.md)  
   Permite demonstrar respostas 429 e 503 documentadas em um alvo controlado.

21. [Geração promovida pelo portal](docs/modules/21_PORTAL_PROMOTED_GENERATION.md)  
   Permite selecionar casos e gerar planos imutáveis pela interface do portal.

22. [Execução governada de fixtures no CI](docs/modules/22_GOVERNED_CI_FIXTURES.md)  
   Executa fixtures no GitHub Actions com aprovação assinada e coleta de evidências.

23. [Ledger durável e atômico de aprovações](docs/modules/23_DURABLE_APPROVAL_LEDGER.md)  
   Consome aprovações atomicamente em referências Git para impedir reutilização entre runners.

24. [Sessões autenticadas e papéis do portal](docs/modules/24_AUTHENTICATED_PORTAL_ROLES.md)  
   Adiciona login, sessões assinadas, proteção CSRF e permissões por papel.

25. [Adaptadores controlados de autenticação e dependência](docs/modules/25_CONTROLLED_AUTH_DEPENDENCY_ADAPTERS.md)  
   Modela falhas de autenticação e dependência por adaptadores explícitos de treinamento.

26. [Broker de credenciais em runtime](docs/modules/26_RUNTIME_CREDENTIAL_BROKER.md)  
   Resolve credenciais por alias em tempo de execução e filtra o valor nas saídas capturadas.


#### Identidade e estado transacional — módulos 27–36

27. [Autenticação multifator TOTP](docs/modules/27_PORTAL_TOTP_MFA.md)  
   Adiciona TOTP por usuário e rejeita a reutilização de códigos segundo o estado configurado.

28. [Estado transacional das sessões](docs/modules/28_TRANSACTIONAL_PORTAL_SESSION_STATE.md)  
   Persiste sessões revogáveis e consome contadores MFA atomicamente em SQLite.

29. [Contrato do backend de estado](docs/modules/29_PORTAL_STATE_BACKEND_CONTRACT.md)  
   Separa a autenticação da implementação de persistência por um contrato de backend.

30. [Adaptador HTTP centralizado de estado](docs/modules/30_CENTRALIZED_HTTP_STATE_ADAPTER.md)  
   Acessa o contrato de estado por HTTPS com autenticação e validação de respostas.

31. [Serviço central de estado do portal](docs/modules/31_CENTRAL_PORTAL_STATE_SERVICE.md)  
   Disponibiliza o serviço de estado para sessões e MFA com persistência SQLite.

32. [Rotação da confiança do serviço de estado](docs/modules/32_ROTATING_STATE_SERVICE_TRUST.md)  
   Valida credenciais de serviço por hashes e janelas de validade com rotação sobreposta.

33. [Limitação transacional de tentativas de login](docs/modules/33_TRANSACTIONAL_LOGIN_THROTTLING.md)  
   Limita tentativas de login transacionalmente e mantém mensagens de falha genéricas.

34. [Recuperação MFA de uso único](docs/modules/34_ONE_USE_MFA_RECOVERY.md)  
   Gera e consome códigos de recuperação MFA uma única vez, persistindo apenas digests.

35. [Eventos estruturados de segurança](docs/modules/35_PORTAL_SECURITY_EVENTS.md)  
   Registra tipos de evento, hash do usuário e horário sem metadados livres.

36. [Exportação segura de eventos para SIEM](docs/modules/36_SAFE_SIEM_EXPORT.md)  
   Envia eventos a um coletor HTTPS autorizado e avança o checkpoint após confirmação.


#### Federação OIDC e operação monitorada — módulos 37–44

37. [Validação estrita de identidade OIDC](docs/modules/37_STRICT_OIDC_IDENTITY_VALIDATION.md)  
   Valida assinatura RS256, issuer, audience, nonce e validade dos tokens de identidade.

38. [Authorization Code + PKCE de uso único](docs/modules/38_ONE_USE_OIDC_PKCE_FLOW.md)  
   Implementa Authorization Code com PKCE e transações de login consumidas uma única vez.

39. [Login federado no portal](docs/modules/39_FEDERATED_PORTAL_LOGIN.md)  
   Conecta o login federado às sessões revogáveis e aos papéis locais do portal.

40. [Descoberta OIDC fixada e rotação JWKS](docs/modules/40_PINNED_OIDC_DISCOVERY_ROTATION.md)  
   Valida descoberta sob issuer fixado e controla a substituição do conjunto de chaves JWKS.

41. [Mudanças de confiança OIDC aprovadas independentemente](docs/modules/41_APPROVED_OIDC_TRUST_CHANGES.md)  
   Exige aprovação independente para mudanças de confiança e registra os hashes na auditoria.

42. [Monitoramento determinístico da confiança OIDC](docs/modules/42_OIDC_TRUST_MONITORING.md)  
   Detecta mudanças nas chaves e inconsistências na auditoria sem alterar a confiança.

43. [Entrega autenticada e idempotente de alertas](docs/modules/43_AUTHENTICATED_OIDC_ALERT_DELIVERY.md)  
   Entrega alertas autenticados com identificador estável e retentativas limitadas.

44. [Ciclos monitorados com lease transacional](docs/modules/44_LEASED_OIDC_MONITOR_CYCLES.md)  
   Coordena ciclos de monitoramento com lease SQLite, histórico e agendamento local explícito.


Os exercícios correspondentes estão em [`docs/training`](docs/training) e a ordem didática está
no [guia de treinamento](docs/TRAINING_GUIDE.md). O estado e os limites de cada etapa aparecem no
[roadmap](docs/ROADMAP.md).

### Documentos gerais

- [Produto](docs/PRODUCT.md): proposta comercial e público-alvo;
- [Arquitetura](docs/ARCHITECTURE.md): componentes e fluxo;
- [Segurança](docs/SECURITY.md): modelo de ameaças e controles;
- [Roadmap](docs/ROADMAP.md): caminho do MVP à operação;
- [Apresentação](docs/PRESENTATION.md): roteiro de apresentação profissional;
- [CI/CD](docs/CI_CD.md): integração na esteira;
- [Changelog](CHANGELOG.md): histórico de versões;
- [Checklist da release](docs/RELEASE_CHECKLIST.md): validações para publicar a versão.

