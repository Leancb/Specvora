# Laboratório 36 — Exportação segura para SIEM

1. Produza eventos de laboratório no `session-state.db`.
2. Configure um coletor HTTPS controlado e confirme seu hostname na allowlist.
3. Execute `scripts/export-portal-security.ps1 -ApproveExport` e informe o token sem exibi-lo.
4. Confirme o lote canônico, a chave de idempotência e o avanço do checkpoint.
5. Execute novamente sem novos eventos e confirme que nenhuma requisição é enviada.
6. Simule `503`, `429` e depois `202`; observe somente duas esperas e um único avanço.
7. Simule falha permanente e confirme que o checkpoint permanece inalterado.
8. Verifique que o bearer e credenciais de portal não aparecem no payload ou na saída.

Não use um SIEM de produção neste laboratório. O receptor deve honrar a chave de idempotência;
sem isso, retentativas podem produzir eventos duplicados apesar do checkpoint local.
