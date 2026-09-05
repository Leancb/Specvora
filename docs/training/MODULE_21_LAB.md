# Laboratório 21 — Gerar um plano pelo portal

1. Atualize e reinstale o projeto, então reinicie o portal local.
2. Abra `/portal`. Na revisão concluída, selecione **Generate test plan**.
3. Informe um identificador novo, como `plan-portal-001`.
4. Para cada cenário 429/503, escolha `getPet-valid`. A fixture controlada deve partir
   de uma requisição válida para isolar a condição simulada.
5. Confirme a geração e verifique `READY_FOR_HUMAN_APPROVAL`.
6. Repita com o mesmo ID e demonstre que o portal recusa sobrescrever o plano.

Não inicie o alvo nem execute Pytest durante esta demonstração. Abra o diretório gerado e
mostre `quality-gate.json`, `promotion-plan.json`, `traceability.json`, `request-cases.json`
e o teste pertencente ao cliente. Depois explique que execução requer uma nova assinatura
vinculada exatamente a esse novo diretório.

Critério de conclusão: selecionar vínculos sem editar JSON, preservar planos anteriores,
demonstrar confinamento e distinguir acesso ao portal de autoridade criptográfica.
