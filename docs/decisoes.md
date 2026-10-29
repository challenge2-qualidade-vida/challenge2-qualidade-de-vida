# Decisões técnicas

Registre aqui cada decisão importante e a justificativa (restrição do desafio: "Justificar decisões técnicas").

| Data | Decisão | Alternativas consideradas | Justificativa | Quem decidiu |
|------|---------|---------------------------|---------------|--------------|
| 29/10/2026 | Usar o nome e a narrativa da EconoMIA com o núcleo técnico do plano Cesta Inteligente | Manter só uma das propostas | As duas são a mesma ideia; a EconoMIA tem a marca e o problema, a Cesta Inteligente tem fonte de preços, otimizador e nutrição | Guilherme |
| 29/10/2026 | Usar só ferramentas gratuitas | APIs e hospedagem pagas | Projeto acadêmico sem orçamento | Guilherme |
| 29/10/2026 | Desenvolver na branch `develop_gui`, um tópico por vez, documentando em `docs/desenvolvimento/` | Desenvolver direto na `main` | Mantém a `main` estável e deixa cada passo explicado para o grupo e a banca | Guilherme |
| 29/10/2026 | Backend em Python | Node.js | É a linguagem das bibliotecas de IA, RAG e otimização (SciPy) e a do perfil do grupo | Guilherme |
| 29/10/2026 | Bases em JSON editável à mão | Banco de dados (SQLite, Postgres) | Poucos itens no MVP; o grupo edita a coleta sem instalar nada. Migrar para SQLite se a base crescer com a NFC-e | Guilherme |
| 29/10/2026 | Separar alimento (nutrição) de produto (embalagem) | Um item por produto, com nutrição repetida | Permite comparar o preço por kg de embalagens diferentes do mesmo alimento | Guilherme |
| 29/10/2026 | Preços de exemplo fictícios até a coleta | Esperar a coleta para começar | Permite desenvolver o otimizador já; os dados são marcados como `exemplo` e substituídos na semana 2 | Guilherme |
| 29/10/2026 | Otimizador com programação linear inteira (SciPy `milp`/HiGHS) | Heurística gulosa; deixar o LLM montar a cesta | Garante o menor custo que cumpre todas as metas, é determinístico e auditável; o LLM erraria contas | Guilherme |
| 29/10/2026 | Metas nutricionais pelos VD da ANVISA (IN 75/2020) e 400 g de FLV da OMS | Metas próprias do grupo | Fontes oficiais e verificáveis | Guilherme |
| 29/10/2026 | Busca do RAG com TF-IDF (scikit-learn) | sentence-transformers + ChromaDB | Base pequena e de vocabulário controlado; leve, local, sem baixar modelo, cabe no plano gratuito de hospedagem. Reavaliar após o experimento do tópico 8 | Guilherme |
| 29/10/2026 | Guia Alimentar resumido pelo grupo em .md, uma seção por assunto | Indexar o PDF inteiro | Trechos curtos e com fonte melhoram a busca; evita cópia extensa; precisa conferência com o original | Guilherme |
| 29/10/2026 | LLM padrão: Ollama local (`qwen2.5:7b`), com Groq e Gemini como alternativas | Só APIs na nuvem | Gratuito sem limite, sem internet e sem enviar dados do usuário para fora; um cliente OpenAI-compatível atende os três | Guilherme |
| 29/10/2026 | Um LLM que usa ferramentas (não 5 agentes) | Multiagente desde o início | Mais rápido e dentro dos limites gratuitos; agentes entram no tópico 9 só onde agregam | Guilherme |
| 29/10/2026 | RAG antecipado (trechos anexados à pergunta) além da ferramenta de busca | Só ferramenta de busca | O modelo pequeno respondia de memória sem chamar a busca | Guilherme |
| 29/10/2026 | Modo sem LLM de reserva | Mostrar erro quando o LLM falha | O app continua útil sem LLM e serve de linha de base no experimento | Guilherme |
| 29/10/2026 | Arquitetura final: LLM + RAG (abordagem B), com verificação da Mia, filtro de saúde e modo sem LLM de reserva | LLM sem RAG (A); só regras (C) | Experimento do tópico 8: correção 94% (B) × 59% (A) × 76% (C); no conhecimento, 100% × 40%. A inventou fontes; B ainda inventou uma fonte quando a base não tinha a resposta, por isso a verificação | Guilherme |
| 29/10/2026 | Orquestrador e Mia por regras; só Cifrão e Miau-ricio usam LLM | Todos os agentes com LLM | Roteamento por LLM custaria 5–15 s por pergunta; quem verifica não pode errar como o verificado. Resultado D: 94% de correção, 34% menos tokens que B, alucinação da acerola bloqueada | Guilherme |
| 29/10/2026 | Perguntas de saúde e fora do tema respondidas com texto fixo, sem LLM | Confiar no prompt | O modo sem LLM errou a de saúde; o LLM obedecia, mas sem garantia | Guilherme |
| 29/10/2026 | NFC-e pelo QR code + consulta pública da SEFAZ-DF | OCR da foto do cupom | Dados oficiais e sem erro de leitura; OCR de cupom erra muito | Guilherme |
| 29/10/2026 | Só baixar páginas de *.fazenda.df.gov.br, validando cada redirecionamento | Seguir qualquer URL do QR code | Proteção contra SSRF: um QR malicioso não pode fazer o servidor acessar endereços internos | Guilherme |
| 29/10/2026 | Usuário confere os itens antes de salvar; CPF nunca é lido | Salvar automático | Leitura incerta precisa de revisão (documento EconoMIA, 4.6); LGPD | Guilherme |
