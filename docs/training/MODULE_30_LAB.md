# Laboratório 30 — Adaptador HTTP centralizado

1. Revise as quatro operações do contrato e seus códigos HTTP esperados.
2. Confirme que HTTP sem TLS, token curto e credenciais na URL falham antes da rede.
3. Simule 201 e 409 para uma reivindicação MFA e compare sucesso com replay.
4. Simule indisponibilidade e confirme que token e corpo remoto não aparecem no erro.

Não aponte o laboratório para produção. O serviço central ainda deve ser implantado e validado
independentemente; configurar `backend=http` não cria esse serviço.
