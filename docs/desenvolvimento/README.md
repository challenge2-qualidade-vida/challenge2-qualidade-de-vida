# Desenvolvimento da EconoMIA

Esta pasta registra **o que foi feito, como foi feito e como rodar** cada parte do app. O projeto é construído **um tópico por vez**, na branch `develop_gui`, usando **só ferramentas gratuitas**.

- Documento de concepção do grupo: [Challenge 2 – grupo 3 (EconoMIA)](https://docs.google.com/document/d/1tAXZiDwsO28eBtUtyNtbrhFa5G9R9JpwtzgR2J1baEI/edit?tab=t.0#heading=h.uzzrdpjtezwc)
- Visão geral do produto: [README principal](../../README.md)
- Decisões técnicas e justificativas: [decisoes.md](../decisoes.md)

## Tópicos

| # | Tópico | O que entrega | Ferramentas (gratuitas) | Status | Doc |
|---|--------|---------------|-------------------------|--------|-----|
| 0 | Organização e ambiente | Branch, ambiente Python, estrutura de pastas, testes | Git, Python 3, venv, pytest | ✅ Feito | [00](00-organizacao-e-ambiente.md) |
| 1 | Base de dados | Alimentos com nutrição (TACO) e preços de 3 mercados de exemplo | JSON | ✅ Feito | [01](01-dados.md) |
| 2 | Otimizador da cesta | Monta a cesta mais barata que cumpre orçamento, nutrição, variedade e restrições | SciPy (`milp`) | ✅ Feito | [02](02-otimizador.md) |
| 3 | Comparação entre mercados | "1 mercado" vs. "2 mercados", com custo de deslocamento | SciPy | ⏳ Próximo | — |
| 4 | API (backend) | Endpoints que o site chama | FastAPI + Uvicorn | ⬜ | — |
| 5 | Site (frontend) | Tela: formulário de orçamento → cesta → comparação | HTML, CSS e JavaScript puros | ⬜ | — |
| 6 | Base de conhecimento + RAG | Busca no Guia Alimentar e na TACO para fundamentar respostas | sentence-transformers + ChromaDB (locais) | ⬜ | — |
| 7 | LLM com ferramentas | Chat em linguagem natural que chama o otimizador | Gemini API (plano gratuito), Groq (plano gratuito) ou Ollama (local) — escolher no tópico | ⬜ | — |
| 8 | Experimento LLM × LLM + RAG | Comparação com gabarito: correção, fundamentação, latência, custo | pytest + notebook Jupyter | ⬜ | — |
| 9 | Agentes | Orquestrador, Cifrão (preços), Miau-ricio (nutrição), Mia (verificação) | Mesmo LLM do tópico 7 | ⬜ | — |
| 10 | Leitura da NFC-e (multimodal) | Recibaldo: lê o QR code do cupom e cadastra os preços | OpenCV / pyzbar + portal público da NFC-e | ⬜ | — |
| 11 | Métricas e testes finais | Economia, aderência ao orçamento, adequação nutricional, precisão de preço | pytest + notebook | ⬜ | — |
| 12 | Publicação | Site no ar para a banca testar | Render (plano gratuito) ou Hugging Face Spaces | ⬜ | — |

A ordem segue o roadmap das semanas: tópicos 1–5 formam o núcleo do app (semanas 1–2), 6–8 cobrem RAG e o experimento (semanas 2–3), 9 os agentes (semana 4), 10 a multimodalidade (semana 5) e 11–12 a integração, os testes e a entrega (semanas 6–7).

## Como rodar (estado atual)

```bash
git checkout develop_gui
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Ainda não há site para abrir: ele chega nos tópicos 4 e 5.

## Estrutura do código

```
data/
  alimentos/alimentos.json   nutrição por 100 g (TACO)        → tópico 1
  precos/precos.json         mercados, produtos e preços      → tópico 1
src/economia/
  dados.py                   carrega e valida as bases        → tópico 1
  metas.py                   metas nutricionais e restrições  → tópico 2
  otimizador.py              monta a cesta mais barata        → tópico 2
tests/
  test_dados.py              testes de integridade das bases  → tópico 1
  test_otimizador.py         testes do otimizador             → tópico 2
requirements.txt             dependências (todas gratuitas)
pytest.ini                   configuração dos testes
```
