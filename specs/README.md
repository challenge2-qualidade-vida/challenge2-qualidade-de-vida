# Specs

Cada funcionalidade tem uma pasta `specs/<numero-da-issue>-<nome>/` com dois arquivos:

| Arquivo | Conteúdo |
| --- | --- |
| `spec.md` | O que a funcionalidade faz, para quem, regras de negócio e o que fica fora do escopo |
| `cenarios.feature` | Critérios de aceitação em Gherkin, em português. Executados pelo pytest-bdd |

Para começar uma spec, copiar a pasta [_modelo](_modelo/) e renomear com o número da issue.

A [spec do RAG de receitas](15-rag-receitas/) serve de exemplo.

O fluxo completo está em [docs/processo/fluxo-de-trabalho.md](../docs/processo/fluxo-de-trabalho.md). Os termos usados nas specs vêm do [modelo de domínio](../docs/arquitetura/modelo-de-dominio.md).

## Gherkin em português

Os arquivos `.feature` começam com `# language: pt` e usam as palavras-chave em português:

| Palavra-chave | Uso |
| --- | --- |
| `Funcionalidade` | Nome da funcionalidade |
| `Contexto` | Passos comuns a todos os cenários |
| `Cenário` | Um exemplo de comportamento |
| `Esquema do Cenário` + `Exemplos` | Mesmo cenário com vários dados |
| `Dado` | Situação inicial |
| `Quando` | Ação |
| `Então` | Resultado esperado |
| `E`, `Mas` | Continuação do passo anterior |

O suporte do pytest-bdd a `# language: pt` deve ser confirmado na versão adotada (#36). Se não houver suporte, os cenários usam as palavras-chave em inglês (`Feature`, `Scenario`, `Given`, `When`, `Then`), mantendo o texto dos passos em português.
