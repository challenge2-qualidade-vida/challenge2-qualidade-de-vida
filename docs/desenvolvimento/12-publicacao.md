# Tópico 12 — Publicação

**Status:** ✅ preparado em 29/10/2026. **A publicação em si precisa ser feita por alguém do grupo**, porque exige criar uma conta e colocar o site no ar publicamente.

## O que foi feito

| Arquivo | Para quê |
|---------|----------|
| [Dockerfile](../../Dockerfile) | Imagem do app: Python 3.14, dependências, `src/` e `data/`. Roda com um usuário sem privilégios |
| [.dockerignore](../../.dockerignore) | Deixa de fora `.venv`, `.env`, testes, docs e as contribuições de NFC-e |
| [render.yaml](../../render.yaml) | Configuração pronta para o **Render** (plano gratuito) |

### O que foi testado

- `pip install -r requirements.txt` num **ambiente limpo**: instalou tudo, e os **127 testes passaram** nele.
- O **comando de produção** (`uvicorn ... --host 0.0.0.0 --port $PORT`, com `LLM_PROVEDOR=nenhum`) subiu, e responderam `/api/saude`, o site e o chat.
- ⚠️ A **imagem Docker não foi construída** nesta máquina: o Docker está instalado, mas o serviço não estava rodando. Na primeira publicação, acompanhe o log de build da hospedagem.

## O LLM na nuvem

O **Ollama roda no computador**, e as hospedagens gratuitas não têm memória nem CPU para um modelo de 7B. Na nuvem, as opções gratuitas são:

| Opção | Como | Observação |
|-------|------|------------|
| **Groq** (recomendado) | Criar a chave grátis em console.groq.com → `LLM_PROVEDOR=groq`, `LLM_API_KEY=...` | Rápido (poucos segundos); plano gratuito com limite de requisições por minuto e por dia |
| Gemini | Chave grátis em aistudio.google.com → `LLM_PROVEDOR=gemini`, `LLM_API_KEY=...` | Plano gratuito com limites; os dados podem ser usados pelo Google no plano gratuito, então leia os termos |
| Sem LLM | `LLM_PROVEDOR=nenhum` (padrão da imagem) | Cesta, preços, promoção, cupom e RAG funcionam; o chat responde por regras |

Se o limite gratuito estourar, o app **cai sozinho no modo sem LLM** (tópico 7): o site não para.

> 🔒 **A chave nunca vai para o GitHub.** Ela é colada como "secret" ou "environment variable" no painel da hospedagem. O `.env` já está no `.gitignore`.

Depois de publicar com Groq ou Gemini, vale rodar o experimento de novo com o mesmo provedor (`LLM_PROVEDOR=groq .venv/bin/python experimentos/llm_x_rag.py`), porque o modelo é outro.

## Passo a passo: Render (gratuito)

1. Enviar a branch para o GitHub: `git push -u origin develop_gui`.
2. Criar a conta em render.com (pode entrar com o GitHub).
3. **New → Blueprint** → escolher o repositório `challenge2-qualidade-de-vida`. O Render lê o `render.yaml`.
4. Quando pedir `LLM_API_KEY`, colar a chave do Groq (ou deixar vazio e mudar `LLM_PROVEDOR` para `nenhum`).
5. Aguardar o build. O endereço fica como `https://economia-xxxx.onrender.com`.
6. Conferir `https://.../api/saude` → `{"status":"ok"}`.

**Limitações do plano gratuito do Render:** o serviço **dorme** depois de cerca de 15 min sem acesso, e o primeiro acesso seguinte demora uns 30–60 s. **Abra o site alguns minutos antes da apresentação.**

## Alternativa: Hugging Face Spaces (gratuito)

1. Criar a conta em huggingface.co → **New Space** → SDK **Docker** → Blank.
2. Enviar para o Space os arquivos `Dockerfile`, `requirements.txt`, `src/` e `data/`.
3. No README do Space, o cabeçalho precisa ter `sdk: docker` e `app_port: 8000`.
4. Em **Settings → Variables and secrets**, criar `LLM_PROVEDOR` e o secret `LLM_API_KEY`.

## Cuidados antes de deixar público

| Ponto | Situação | O que fazer |
|-------|----------|-------------|
| Preços de exemplo | O site mostra o aviso no topo | Trocar pela coleta real (tópico 1, "Como adicionar a coleta real") |
| Contribuições de NFC-e | Ficam em `contribuicoes.json`, no disco do servidor | No plano gratuito o disco **é apagado** a cada novo deploy ou reinício. Para guardar de verdade, usar um banco gratuito (ex.: SQLite num volume, ou o plano gratuito de um Postgres) |
| Abuso do chat | Qualquer pessoa pode mandar muitas mensagens e gastar o limite gratuito do LLM | Para a apresentação, basta. Se ficar aberto ao público, adicionar um limite de requisições por IP |
| Gravação sem login | Qualquer pessoa pode confirmar preços de NFC-e | Os dados vêm da nota oficial, mas o preço é editável na tela. Para produção, marcar contribuições editadas ou exigir login |
| Privacidade | Nenhum dado pessoal é salvo; o orçamento só passa pela requisição | Manter assim; com o Gemini gratuito, avisar que as mensagens vão para o Google |

## Como rodar localmente (resumo final)

```bash
git clone https://github.com/dida0982/challenge2-qualidade-de-vida.git
cd challenge2-qualidade-de-vida
git checkout develop_gui
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                                                   # 127 testes
ollama pull qwen2.5:7b                                   # opcional: LLM local e gratuito
uvicorn economia.api:app --app-dir src --reload          # http://localhost:8000
```
