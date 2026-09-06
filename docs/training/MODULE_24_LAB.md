# Laboratório 24 — Login, papéis e revogação

## Criar o usuário local

No PowerShell do projeto, execute:

```powershell
cd D:\Specvora
.\scripts\setup-portal-auth.ps1 -ApproveSetup
python -m uvicorn specvora.main:app --host 127.0.0.1 --port 8102
```

O script solicita e confirma a senha sem colocá-la na linha de comando. Ele cria a chave de
sessão e o arquivo de hashes em `.specvora-auth/`, que é ignorado pelo Git, e aplica as variáveis
somente ao PowerShell atual. Abra `http://127.0.0.1:8102/portal` e faça login.

## Exercício de autorização

1. Entre com um usuário apenas `viewer` e confirme que a leitura funciona, mas alterações recebem
   HTTP 403.
2. Entre como `reviewer`, prepare uma decisão e tente usar outro nome no campo reviewer; a API
   deve rejeitar a divergência.
3. Entre como `operator` e registre um projeto, sem conceder autoridade para aprovar propostas.
4. Incremente `session_version` no usuário, recarregue a página e confirme a revogação.

Para HTTPS, defina `SPECVORA_PORTAL_COOKIE_SECURE=true`. Nunca versione `.specvora-auth/` e não
coloque a chave privada Ed25519 no portal; sessão, papel e assinatura são controles diferentes.
