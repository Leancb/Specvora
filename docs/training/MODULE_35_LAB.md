# Laboratório 35 — Eventos de segurança do portal

1. Configure autenticação obrigatória com o backend SQLite transacional.
2. Faça um login inválido, um login válido e consuma um código de recuperação.
3. Consulte `security_events` e confirme a ordem dos eventos.
4. Verifique que `subject` é um SHA-256 e não contém o nome do usuário.
5. Confirme que senha, TOTP, recovery code e bearer não aparecem em nenhuma coluna.
6. Envie um tipo de evento não enumerado ao serviço central e confirme `422`.
7. Torne o backend indisponível em laboratório e confirme que a operação não prossegue em silêncio.

Compare esta trilha mínima com uma integração SIEM: transporte protegido, retenção, correlação,
alertas, identidade da workload e acesso de investigação continuam responsabilidades operacionais.
