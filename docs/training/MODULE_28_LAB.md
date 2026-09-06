# Laboratório 28 — Sessões revogáveis e replay transacional

## Preparação

Execute novamente o setup em um PowerShell dedicado para aplicar
`SPECVORA_PORTAL_STATE_DB`, depois reinicie o portal:

```powershell
cd D:\Specvora
.\scripts\setup-portal-auth.ps1 -ApproveSetup
python -m uvicorn specvora.main:app --host 127.0.0.1 --port 8102
```

Se o usuário já existir, o script o preserva e apenas reaplica a configuração ao PowerShell.

## Exercício

1. Entre no portal e confirme que o banco registra uma sessão ativa.
2. Preserve uma cópia apenas para o laboratório, faça logout e confirme que a cópia é rejeitada.
3. Envie concorrentemente o mesmo contador TOTP e confirme uma única aceitação.
4. Reinicie o portal e confirme que a revogação permanece.
5. Remova temporariamente a configuração do banco e explique a diferença de segurança do fallback.

Não edite o banco manualmente. Não copie cookies, sementes ou bancos reais para material de
apresentação. Explique por que uma transação SQLite local prepara o contrato, mas não prova
consistência entre servidores ou segurança de um filesystem de rede.
