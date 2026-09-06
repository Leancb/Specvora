# Laboratório 33 — Limite transacional de login

1. Configure autenticação obrigatória e o backend SQLite em arquivos temporários.
2. Envie cinco senhas inválidas para o mesmo usuário.
3. Confirme que a credencial correta também é recusada dentro da mesma janela.
4. Avance o relógio controlado por cinco minutos e autentique corretamente.
5. Confirme que o sucesso limpou o contador e permite uma nova autenticação.
6. Repita pelo serviço central e observe `201` nas reivindicações e `429` no excesso.
7. Verifique que a tabela contém somente o hash do sujeito, instante e contador.

Use somente identidades de laboratório. Discuta como um gateway complementa esse controle com
limites por origem, telemetria, alertas e proteção distribuída contra negação de serviço.
