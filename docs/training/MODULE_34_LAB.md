# Laboratório 34 — Recuperação MFA de uso único

1. Habilite TOTP para uma identidade de laboratório e configure estado SQLite transacional.
2. Execute `scripts/generate-portal-recovery.ps1 -ApproveGeneration`.
3. Confirme que o arquivo contém oito códigos e que o banco contém somente digests.
4. Entre com senha e um código de recuperação sem fornecer TOTP.
5. Repita o mesmo código e confirme a mensagem genérica de credencial inválida.
6. Gere um novo conjunto e confirme que todos os códigos restantes do conjunto anterior falham.
7. Verifique que sessões emitidas antes da recuperação foram revogadas pela versão da identidade.
8. Remova com segurança o arquivo de códigos após transferi-los para armazenamento aprovado.

Não use identidades ou cofres de produção. Compare esta recuperação local com um processo
corporativo que exija identidade federada, auditoria, alertas e aprovação operacional.
