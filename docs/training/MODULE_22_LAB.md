# Laboratório 22 — Execução governada no GitHub Actions

## Configuração única

No GitHub, crie o environment `specvora-governed` e configure **Required reviewers**. Não
adicione a chave privada. O workflow utiliza somente `contents: read`.

## Autorizar uma execução

Com o branch sincronizado e o ambiente virtual ativo:

```powershell
cd D:\Specvora
.\scripts\prepare-ci-approval.ps1 -ApproveSigning
.\scripts\publish-ci-approval.ps1 -ApproveUpload
```

O primeiro script assina localmente a ação portável por 30 minutos. O segundo envia ao
environment apenas a chave pública e o envelope assinado em base64, sem imprimir valores.
Cada preparação cria uma sessão nova em `.specvora-ci/sessions/`; portanto, uma tentativa
anterior não é sobrescrita nem reutilizada. A publicação recusa sessões incompletas ou
expiradas.

Em seguida, abra **Actions → Governed fixture execution → Run workflow**. Aprove o job no
environment protegido. Baixe o artifact `specvora-evidence-<run-id>` e confira relatório,
evidência, auditoria e ledger da execução.

Após o término, remova imediatamente o envelope:

```powershell
gh secret delete SPECVORA_CI_SIGNED_APPROVAL_B64 --repo Leancb/Specvora --env specvora-governed
```

Não reutilize a autorização e não faça upload dos arquivos de `.specvora-ci`. Se o plano,
URL, timeout, allowlist ou caminho lógico mudar, prepare uma nova assinatura.

## Demonstração de segurança

Mostre que o workflow não contém chave privada e não é acionado por pull requests. Altere
temporariamente uma cópia local do teste e demonstre que a ação assinável muda. Explique a
limitação do ledger efêmero: Required reviewers, expiração curta e remoção do segredo são
controles compensatórios, não equivalem a uma garantia global de uso único.
