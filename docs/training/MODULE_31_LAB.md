# Laboratório 31 — Serviço central de estado

1. Defina `SPECVORA_STATE_SERVICE_DB` para um arquivo temporário fora do Git.
2. Injete um token aleatório de pelo menos 32 caracteres em `SPECVORA_STATE_SERVICE_TOKEN`.
3. Inicie `specvora.state_service:app` somente em loopback para o laboratório.
4. Confirme que `/health` responde sem autenticação e que `/v1/sessions` rejeita token ausente.
5. Registre uma sessão, consulte-a no instante autorizado e revogue-a.
6. Envie duas reivindicações simultâneas do mesmo contador MFA e confirme apenas um sucesso.
7. Conecte o portal com o adaptador HTTP do Módulo 30 e repita login e logout.

Não exponha este laboratório à rede. SQLite, bearer estático e HTTP local demonstram o contrato e
a atomicidade em um host; não substituem TLS, identidade de workload, rate limiting, isolamento
por tenant nem um datastore operado para produção.
