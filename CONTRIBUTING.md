# Como contribuir

## Fluxo básico

1. Pegue uma tarefa nas **Issues** (ou crie uma) e coloque seu nome como responsável.
2. Crie uma branch a partir da `main`:
   ```bash
   git checkout main
   git pull
   git checkout -b semana-2/rag-inicial
   ```
3. Faça commits pequenos e com mensagens claras:
   ```bash
   git add .
   git commit -m "Adiciona carregamento dos documentos da base"
   git push -u origin semana-2/rag-inicial
   ```
4. Abra um **Pull Request** para a `main` e peça para alguém do grupo revisar.
5. Depois de aprovado, faça o merge.

## Nome das branches

`semana-N/descricao-curta` — por exemplo `semana-1/stakeholders`, `semana-4/agente-triagem`.

## Regras do grupo

- Não subir chaves de API, senhas ou arquivos `.env` (já estão no `.gitignore`).
- Não subir dados pessoais reais (LGPD). Use dados públicos ou anonimizados.
- Toda fonte usada na base de conhecimento deve ser registrada em `data/base-conhecimento/FONTES.md`.
- Decisões técnicas importantes vão em `docs/decisoes.md`, com a justificativa.
