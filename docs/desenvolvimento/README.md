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
| 3 | Comparação entre mercados | "1 mercado" vs. "2 mercados", com custo de deslocamento | SciPy | ✅ Feito | [03](03-comparacao-mercados.md) |
| 4 | API (backend) | Endpoints que o site chama | FastAPI + Uvicorn | ✅ Feito | [04](04-api.md) |
| 5 | Site (frontend) | Tela: formulário de orçamento → cesta → comparação | HTML, CSS e JavaScript puros | ✅ Feito | [05](05-site.md) |
| 6 | Base de conhecimento + RAG | Busca no Guia Alimentar e na TACO para fundamentar respostas | scikit-learn (TF-IDF, local) | ✅ Feito | [06](06-rag.md) |
| 7 | LLM com ferramentas | Chat em linguagem natural que chama o otimizador | Ollama local (padrão), Groq ou Gemini (planos gratuitos) | ✅ Feito | [07](07-llm-ferramentas.md) |
| 8 | Experimento LLM × LLM + RAG | Comparação com gabarito: correção, fundamentação, latência, custo | Script Python + pytest | ✅ Feito | [08](08-experimento-llm-rag.md) |
| 9 | Agentes | Orquestrador, Cifrão (preços), Miau-ricio (nutrição), Mia (verificação) | Mesmo LLM do tópico 7; Orquestrador e Mia por regras | ✅ Feito | [09](09-agentes.md) |
| 10 | Leitura da NFC-e (multimodal) | Recibaldo: lê o QR code do cupom e cadastra os preços | OpenCV + BeautifulSoup + consulta pública da SEFAZ-DF | ✅ Feito (falta validar com cupom real) | [10](10-nfce-multimodal.md) |
| 11 | Métricas e testes finais | Economia, aderência ao orçamento, adequação nutricional, precisão de preço | Script Python + pytest | ✅ Feito (falta trabalho de campo: gôndola e usuários) | [11](11-metricas.md) |
| 12 | Publicação | Site no ar para a banca testar | Docker + Render ou Hugging Face Spaces (planos gratuitos) | ✅ Preparado (publicar exige a conta do grupo) | [12](12-publicacao.md) |
| 13 | Localização e proteínas | Mercados perto do usuário, custo de deslocamento, ranking das proteínas (carne, frango, ovos...), supermercados do OpenStreetMap | Geolocalização do navegador + OpenStreetMap (Overpass) | ✅ Feito | [13](13-localizacao-proteinas.md) |

A ordem segue o roadmap das semanas: tópicos 1–5 formam o núcleo do app (semanas 1–2), 6–8 cobrem RAG e o experimento (semanas 2–3), 9 os agentes (semana 4), 10 a multimodalidade (semana 5) e 11–12 a integração, os testes e a entrega (semanas 6–7).

## Como rodar

```bash
git checkout develop_gui
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest                                               # 142 testes, ~8 s
ollama pull qwen2.5:7b                               # opcional: LLM local e gratuito
uvicorn economia.api:app --app-dir src --reload
```

Depois acesse <http://localhost:8000> (site) ou <http://localhost:8000/docs> (documentação da API). Sem Ollama, o app funciona no modo sem LLM.

## O site, em 6 abas de funcionalidade

| Onde | O que faz | Tópicos |
|------|-----------|---------|
| **Montar cesta** | Orçamento + pessoas + período + restrições → cesta mais barata que cumpre as metas, 1 × 2 mercados, explicação, metas, lista com preço/kg e fonte → **Sugerir cardápio** | 2, 3, 5, 9 |
| **Perto de mim** | Localização (ou região) → mercados com preços no raio, distância, custo de ida e volta, **onde a proteína está mais barata**, supermercados do OpenStreetMap → montar a cesta só com os mercados próximos | 13 |
| **Conversar** | Chat em linguagem natural; o Orquestrador escolhe o agente, e a Mia confere a resposta | 6, 7, 9 |
| **Preços** | Tabela produto × mercado com preço por kg, data e fonte; menor preço destacado | 1, 4, 5 |
| **Enviar cupom** | Foto do cupom → QR code → nota da SEFAZ-DF → conferir → preços entram na base | 10 |
| `/docs` | Documentação interativa da API (Swagger) | 4 |

## O que falta (depende do grupo)

1. **Coleta real de preços** em 3–4 mercados de Brasília, **com a latitude e a longitude de cada um** → substituir os preços de exemplo ([01](01-dados.md#como-adicionar-a-coleta-real-de-preços), [13](13-localizacao-proteinas.md#limitações)).
2. **Conferir** os resumos do Guia Alimentar e os valores da TACO com os originais ([06](06-rag.md)).
3. **Testar a NFC-e com um cupom real do DF** e ajustar o leitor, se o layout for diferente ([10](10-nfce-multimodal.md#️-limitação-importante-o-layout-real-da-sefaz-df)).
4. **Verificação na gôndola** e **teste com usuários** (métricas 6 e 8, [11](11-metricas.md#o-que-falta-trabalho-de-campo-do-grupo)).
5. **Publicar** no Render ou no Hugging Face ([12](12-publicacao.md)).

## Estrutura do código

```
data/
  alimentos/alimentos.json   nutrição por 100 g (TACO)        → tópico 1
  base-conhecimento/*.md     Guia Alimentar, critérios, receitas → tópico 6
  experimento/perguntas.json perguntas e gabarito             → tópico 8
  experimento/cesta_referencia.json cesta estilo DIEESE        → tópico 11
  precos/precos.json         mercados, produtos e preços      → tópico 1
  precos/contribuicoes.json  preços enviados via NFC-e (fora do git) → tópico 10
src/economia/
  dados.py                   carrega e valida as bases        → tópico 1
  metas.py                   metas nutricionais e restrições  → tópico 2
  otimizador.py              monta a cesta mais barata        → tópico 2
  planejador.py              1 mercado × 2 mercados           → tópico 3
  explicacao.py              explica o plano em frases        → tópico 3
  api.py                     API FastAPI + serve o site       → tópico 4
  rag.py                     busca na base de conhecimento    → tópico 6
  llm.py                     cliente de LLM gratuito          → tópico 7
  precos.py                  consulta de preços e promoções   → tópico 7
  assistente.py              chat: LLM + ferramentas + RAG    → tópico 7
  avaliacao.py               critérios do experimento         → tópico 8
  agentes.py                 Orquestrador, Cifrão, Miau-ricio, Mia → tópico 9
  nfce.py                    Recibaldo: QR code da NFC-e      → tópico 10
  metricas.py                métricas do projeto              → tópico 11
  geo.py                     localização e ranking de proteínas → tópico 13
experimentos/
  llm_x_rag.py               experimento LLM × LLM + RAG      → tópico 8
  metricas.py                gera docs/semana-7/metricas.md   → tópico 11
src/web/
  index.html, estilo.css, app.js   o site                     → tópico 5
tests/
  test_dados.py              testes de integridade das bases  → tópico 1
  test_otimizador.py         testes do otimizador             → tópico 2
  test_planejador.py         testes da comparação             → tópico 3
  test_api.py                testes da API                    → tópico 4
  test_rag.py                testes da busca                  → tópico 6
  test_assistente.py         testes do chat (LLM falso)       → tópico 7
  conftest.py                testes sem LLM de verdade        → tópico 7
  test_avaliacao.py          testes dos critérios             → tópico 8
  test_agentes.py            testes dos agentes               → tópico 9
  test_nfce.py               testes da NFC-e                  → tópico 10
  test_geo.py                testes de localização            → tópico 13
  fixtures/nfce_exemplo.html nota fictícia para os testes     → tópico 10
requirements.txt             dependências (todas gratuitas)
Dockerfile, render.yaml      publicação gratuita              → tópico 12
pytest.ini                   configuração dos testes
```
