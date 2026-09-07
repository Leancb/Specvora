# Laboratório 37 — Fronteira de confiança OIDC

1. Gere uma chave RSA de laboratório e um JWKS contendo apenas a chave pública.
2. Configure issuer HTTPS, audience e caminho do JWKS fora do Git.
3. Assine um ID token `RS256` com nonce, timestamps e usuário local existente.
4. Valide o token e confirme que os papéis vêm do cadastro local.
5. Altere separadamente assinatura, issuer, audience, nonce, `kid`, `exp` e `iat`.
6. Confirme a mesma rejeição genérica em todos os casos.
7. Inclua `roles:["operator"]` no token para um usuário local reviewer e confirme ausência de
   elevação.

Não conecte este laboratório a um provedor real. O próximo fluxo deve usar Authorization Code +
PKCE e estado/nonce de uso único mantidos no servidor; token colado pelo usuário não é login OIDC.
