# Laboratório 29 — Contrato substituível de estado

1. Execute o portal com backend `sqlite` e confirme login, logout e replay TOTP.
2. Defina `SPECVORA_PORTAL_STATE_BACKEND=redis` e confirme falha fechada.
3. Selecione `sqlite` sem `SPECVORA_PORTAL_STATE_DB` e confirme a rejeição.
4. Relacione cada método do protocolo à garantia transacional exigida de um backend centralizado.

Não configure um nome de backend como se ele comprovasse uma implementação. O próximo adaptador
deverá possuir testes reais de concorrência, indisponibilidade e recuperação.
