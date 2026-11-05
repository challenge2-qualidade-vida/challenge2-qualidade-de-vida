# Tópico 28 — Trazer a `main` para a `develop_gui`

**Status:** ✅ feito em 05/11/2026; a `main` não foi alterada

## Por quê

A `develop_gui` estava 113 commits à frente e 31 atrás da `main`. O grupo tinha definido na `main` a arquitetura (DDD, specs, BDD), as regras de branch e commit e o esqueleto do backend (PR #52), e nada disso estava na `develop_gui`. O merge traz essas decisões para cá **sem mexer na `main`**: ela só muda por PR aprovado.

## Como foi feito

1. **Backup local** antes de tudo: branch `backup/develop_gui-antes-merge`. Para desfazer: `git reset --hard backup/develop_gui-antes-merge`.
2. `git merge --no-ff origin/main` na `develop_gui` (merge commit, como pede o fluxo do grupo).
3. **5 conflitos de texto**, resolvidos juntando as duas versões, sem apagar o que o time escreveu:

| Arquivo | Como ficou |
|---|---|
| `.gitignore` | As duas listas (contribuições da NFC-e e o site Astro) |
| `CONTRIBUTING.md` | Exemplo de commit e regras do grupo; mantida a seção do endereço do repositório |
| `docs/decisoes.md` | Todas as linhas das duas tabelas (é um registro histórico) |
| `docs/semana-1/definicoes-do-projeto.md` | Seção 7 (fontes) daqui e seção 8 (equipe e papéis) do grupo |
| `README.md` | Problema, funcionalidades e resultados daqui; equipe com fotos e site do grupo; estrutura do repositório com as pastas dos dois |

4. **Conflito de código:** a `main` criou o pacote `src/economia/api/` (com `__init__.py` vazio), que esconde o módulo `src/economia/api.py` e impede o app de subir. O conteúdo do `api.py` foi movido para `src/economia/api/__init__.py`, com os imports relativos trocados de `.` para `..` e os caminhos de `web/` e `data/` ajustados um nível acima. O comando continua o mesmo: `uvicorn economia.api:app --app-dir src`. A pasta `precos/` da `main` não tem `__init__.py` e não esconde o `precos.py`.

## Resultado

- 228 testes passando (`pytest`), e o site em `localhost:8000` continuou respondendo.
- O que ainda diverge do grupo e precisa ser conversado: o código daqui está em módulos soltos (`otimizador.py`, `rag.py`...), não nos contextos `dominio/aplicacao/infraestrutura`; usa `requirements.txt` e Render, e o grupo decidiu Poetry e VM no Azure; e o escopo do MVP do grupo deixa a nutrição de fora, que aqui é central.
- Commits antigos desta branch têm `Co-Authored-By`, o que as regras do grupo proíbem. Os novos já saem sem.
