# Tópico 0 — Organização e ambiente

**Status:** ✅ concluído em 29/10/2026

## O que foi feito

1. **Branch `develop_gui`** criada a partir da `main`. Todo o desenvolvimento acontece nela, e a `main` só recebe o trabalho por Pull Request.
2. **README principal reescrito** com a proposta unificada: nome e narrativa da EconoMIA e o núcleo técnico do plano *Cesta Inteligente* (otimizador, metas nutricionais, fonte de preços).
3. **Ambiente Python isolado** (`.venv`) com as dependências fixadas em `requirements.txt`.
4. **Estrutura de código**: o pacote Python fica em `src/economia/`, os testes em `tests/` e a configuração do pytest em `pytest.ini` (`pythonpath = src`, para os testes importarem `economia` sem instalar o pacote).
5. **Esta pasta `docs/desenvolvimento/`**, com um arquivo por tópico.

## Como foi feito

```bash
git checkout -b develop_gui              # cria a branch e entra nela
python3 -m venv .venv                     # cria o ambiente virtual
.venv/bin/pip install fastapi "uvicorn[standard]" scipy pytest httpx
```

A pasta `.venv/` já estava no `.gitignore`, então o ambiente não sobe para o GitHub. Cada pessoa do grupo cria o seu.

## Ferramentas e por que são gratuitas

| Ferramenta | Para quê | Licença |
|------------|----------|---------|
| Python 3 | Linguagem do backend e da IA | PSF (livre) |
| venv | Isolar as dependências do projeto | Vem com o Python |
| pytest | Testes automatizados | MIT |
| SciPy / NumPy | Otimizador da cesta (tópico 2) | BSD |
| FastAPI / Uvicorn | API do site (tópico 4) | MIT / BSD |

Foram instaladas agora para o ambiente ficar pronto. Cada uma só passa a ser usada no tópico indicado.

## Como reproduzir na sua máquina

```bash
git clone https://github.com/dida0982/challenge2-qualidade-de-vida.git
cd challenge2-qualidade-de-vida
git checkout develop_gui
python3 -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                           # deve mostrar todos os testes passando
```
