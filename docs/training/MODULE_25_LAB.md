# Laboratório 25 — Adaptadores controlados de autenticação e dependências

## Objetivo

Gerar cenários promovidos para falhas de autenticação e dependências sem usar credenciais reais,
sem chamar um provedor de identidade e sem introduzir atrasos instáveis.

## Exercício

1. Inspecione no OpenAPI uma operação protegida, suas respostas 200, 401, 403 e 503 e os
   adaptadores `x-specvora-auth-fixtures` e `x-specvora-dependency-fixtures`.
2. Associe cada cenário promovido a um caso determinístico válido e gere uma nova pasta de plano.
3. Confirme no teste gerado que os únicos controles são `X-Specvora-Auth-Fixture` e
   `X-Specvora-Dependency-Fixture` com valores permitidos.
4. Remova o adaptador de autenticação e confirme que a geração é bloqueada.
5. Declare dois adaptadores para o mesmo status e confirme o diagnóstico de ambiguidade.
6. Execute os testes somente no alvo local, depois de criar uma autorização assinada separada.

## Discussão

Explique por que `expired` não contém um token expirado real e por que `timeout` retorna 503 sem
dormir. Identifique os controles que continuam independentes: contrato OpenAPI, validação
determinística, revisão humana, assinatura offline, allowlist, confinamento e evidência.

Nunca configure esses cabeçalhos em produção e nunca coloque segredos em OpenAPI, bindings,
artefatos gerados, logs ou fixtures.
