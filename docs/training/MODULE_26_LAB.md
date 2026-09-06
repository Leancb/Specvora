# Laboratório 26 — Credencial referenciada em tempo de execução

## Preparação

Em um PowerShell dedicado, execute:

```powershell
cd D:\Specvora
.\scripts\setup-runtime-credential.ps1 -Alias staging-api -ApproveSetup
```

Informe uma credencial de treinamento com pelo menos 16 caracteres. Não use produção. Prepare o
JSON do runner com `"credential_ref":{"alias":"staging-api"}` ou passe
`--credential-alias staging-api` pela CLI. Gere e assine uma nova ação após escolher o alias.

## Verificações

1. Procure o valor nos arquivos do workspace e confirme que ele não foi persistido.
2. Execute contra um alvo não produtivo autorizado e confirme o cabeçalho recebido.
3. Faça o alvo repetir o valor na resposta de diagnóstico e confirme `[REDACTED]` na saída.
4. Troque o alias depois da assinatura e confirme a rejeição por divergência de hash.
5. Abra outro PowerShell e confirme que a referência não está disponível nele.

## Discussão

Explique por que o hash assina o alias, mas não o segredo; por que rotação é diferente de troca de
identidade lógica; e por que código gerado revisado continua sendo parte da base confiável durante
a execução. Redação exata não substitui credenciais curtas, escopo mínimo ou prevenção de saída.
