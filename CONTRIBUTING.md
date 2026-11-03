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
   git commit -m "feat: adiciona carregamento dos documentos da base"
   git push -u origin semana-2/rag-inicial
   ```
4. Abra um **Pull Request** para a `main` e peça para alguém do grupo revisar.
5. Depois de aprovado, faça o merge.

## Nome das branches

`semana-N/descricao-curta` — por exemplo `semana-1/stakeholders`, `semana-4/agente-triagem`.

## Padrão dos commits

Toda mensagem começa com o tipo da mudança, seguido de uma descrição curta em português:

```
tipo: o que mudou
```

| Tipo | Quando usar | Exemplo |
|------|-------------|---------|
| `feat` | Funcionalidade nova | `feat: adiciona botão de trocar item na cesta` |
| `fix` | Correção de erro | `fix: impede alimento cru no cardápio` |
| `docs` | Só documentação | `docs: adiciona relatório final` |
| `test` | Só testes | `test: cobre cestas sem proteína animal` |
| `refactor` | Muda o código sem mudar o comportamento | `refactor: separa o cardápio dos agentes` |
| `perf` | Melhora o desempenho | `perf: reduz o tempo de resposta do cardápio` |
| `style` | Só visual ou formatação | `style: ajusta o contraste dos chips no modo escuro` |
| `ci` | Testes automáticos no GitHub | `ci: roda o pytest a cada envio` |
| `chore` | Manutenção, dependências e configuração | `chore: atualiza as dependências` |

Faça um commit por assunto: se a mudança traz uma correção e uma funcionalidade nova, separe em dois.

Para achar um tipo no histórico:

```bash
git log --oneline --grep="^fix:"
```

Os commits anteriores a 03/11/2026 não seguem este padrão.

## Regras do grupo

- Não subir chaves de API, senhas ou arquivos `.env` (já estão no `.gitignore`).
- Não subir dados pessoais reais (LGPD). Use dados públicos ou anonimizados.
- Toda fonte usada na base de conhecimento deve ser registrada em `data/base-conhecimento/FONTES.md`.
- Decisões técnicas importantes vão em `docs/decisoes.md`, com a justificativa.
