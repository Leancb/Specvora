# Laboratório 23 — Bloqueio de replay entre execuções

## Objetivo

Demonstrar que uma aprovação assinada pode iniciar no máximo uma execução governada, mesmo em
runners hospedados diferentes.

## Preparação

1. Proteja o padrão de tags `specvora-approvals/*` contra atualização e exclusão.
2. Mantenha o environment `specvora-governed` com revisão humana obrigatória.
3. Prepare e publique uma autorização nova conforme o laboratório 22.

## Exercício

Execute `Governed fixture execution` e confirme o sucesso. Localize a tag técnica cujo nome
contém o `approval_id` da evidência. Sem preparar outra autorização, dispare o workflow novamente.
O segundo job deve falhar antes do Pytest com a mensagem de que o ledger rejeitou o claim.

Prepare então um envelope novo. O novo `approval_id` cria outra tag e permite uma nova execução.
Remova o segredo efêmero após o exercício; não remova as tags de consumo.

## Evidência para apresentação

- primeira execução: claim remoto criado e testes executados;
- replay: claim rejeitado e nenhum subprocesso de teste iniciado;
- novo consentimento humano: novo UUID, novo claim e nova execução;
- chave privada: permanece fora do repositório e do GitHub Actions.

Explique que a tag é um registro de consumo, não uma aprovação, e que administradores capazes de
apagá-la continuam dentro do modelo de confiança operacional.
