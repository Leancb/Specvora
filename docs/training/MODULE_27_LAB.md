# Laboratório 27 — Enrollment e login com TOTP

## Habilitar MFA

Pare de usar sessões abertas para o usuário do laboratório e execute:

```powershell
cd D:\Specvora
.\scripts\enable-portal-mfa.ps1 -Username leandro -ApproveEnrollment
```

Abra `.specvora-auth\mfa-enrollment.json` localmente e importe `otpauth_uri` no aplicativo
autenticador. Esse arquivo contém o segredo. Não envie ao Git, chat, e-mail ou logs. Depois de
confirmar o primeiro login, remova especificamente esse arquivo:

```powershell
Remove-Item -LiteralPath D:\Specvora\.specvora-auth\mfa-enrollment.json
```

A remoção comum não garante eliminação física em todas as mídias ou backups; o diretório inteiro
de autenticação continua sensível porque o servidor precisa armazenar a semente TOTP.

## Verificar os controles

1. Tente entrar apenas com usuário e senha e confirme HTTP 401.
2. Entre com o código atual e confirme a nova sessão.
3. Saia e tente reutilizar o mesmo código; confirme HTTP 401.
4. Espere o próximo intervalo e confirme que um código novo funciona.
5. Confirme que as sessões anteriores ao enrollment foram revogadas.

Discuta por que TOTP não elimina phishing, por que três intervalos são uma tolerância deliberada e
por que o armazenamento local não serve para múltiplos servidores concorrentes.
