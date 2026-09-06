# Laboratório 32 — Rotação de confiança do serviço

1. Gere dois bearers aleatórios sem imprimi-los ou adicioná-los ao Git.
2. Grave somente os hashes SHA-256 em um trust file fora do repositório.
3. Configure janelas UTC sobrepostas por alguns minutos e defina
   `SPECVORA_STATE_SERVICE_TOKEN_FILE`.
4. Confirme que ambos funcionam durante a sobreposição.
5. Encerre a janela antiga, mantenha a nova e confirme a rejeição da credencial anterior.
6. Teste uma versão desconhecida e um timestamp sem timezone; ambos devem falhar genericamente.
7. Remova o bearer antigo do cliente somente após confirmar que todos usam o novo.

O laboratório não deve registrar os bearers em histórico, evidência ou console. O arquivo contém
somente digests, mas ainda precisa de controle de integridade e distribuição operacional.
