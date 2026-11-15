# Spec: observabilidade completa no Langfuse

| Campo | Valor |
| --- | --- |
| Issue | #29 e #28 (épico #25), entregues junto com a #69 |
| Status | Rascunho |
| Contexto delimitado | Transversal (infraestrutura de LLMOps). Toca Conversa e Receitas e nutrição |
| Agente | Miau-ricio (único agente com LLM hoje) |

## Problema

A #69 registra no Langfuse só a avaliação offline: perguntas fictícias, rodadas pela linha de comando. As perguntas que chegam pela API (`POST /api/v1/receitas/perguntas`) não deixam rastro. Para entender uma resposta ruim, saber quanto cada pessoa usa, ver uma conversa inteira ou perceber que a latência subiu, é preciso reproduzir o caso à mão.

Os prompts estão versionados no repositório, mas o Langfuse não sabe qual versão gerou cada resposta: o vínculo é feito pelo nome do arquivo, num metadado. A qualidade das respostas reais não é medida, e nada avisa quando ela piora.

## Comportamento esperado

### 1. Tracing das perguntas da API

Cada pergunta recebida pela API vira um registro (trace) no Langfuse, com o nome `miau-ricio.pergunta`, contendo:

- a busca no Qdrant, como observação *retriever*, com os trechos e os scores;
- cada chamada ao LLM, como *generation*, com modelo, parâmetros, tokens, latência e o prompt vinculado;
- a resposta final, com `encontrou`, o número de fontes e o limiar;
- o ambiente (`environment`): `local`, `producao` ou `avaliacao`, lido da configuração.

Erros (Qdrant ou Ollama fora do ar) ficam no registro com nível `ERROR` e a mensagem, e a API continua respondendo 503 como hoje.

### 2. Sessões e pessoas

- O frontend gera e guarda no navegador um **identificador anônimo** da pessoa, criado uma vez, e um **identificador da conversa**, criado a cada nova conversa (por enquanto, a cada carregamento da página).
- Os dois vão nos cabeçalhos `X-Identificador-Anonimo` e `X-Conversa` de cada pergunta.
- A API repassa os dois ao Langfuse: o identificador anônimo como `user_id` e a conversa como `session_id`. Pedidos sem os cabeçalhos são registrados sem `user_id` e sem `session_id`.
- Quando existir login (JWT), o `user_id` passa a ser o id da conta. Esta spec não trata do login.

### 3. Mascaramento antes do envio (RN30)

O cliente do Langfuse recebe uma função de mascaramento (`mask`), aplicada a toda entrada, saída e metadado antes do envio. Ela troca por marcadores:

| Dado | Marcador |
| --- | --- |
| E-mail | `[EMAIL]` |
| CPF (com ou sem pontuação) | `[CPF]` |
| Telefone brasileiro (fixo ou celular, com ou sem DDD) | `[TELEFONE]` |
| Número de cartão (13 a 19 dígitos) | `[CARTAO]` |
| Chave de acesso de NFC-e (44 dígitos) | `[CHAVE_NFCE]` |

O mascaramento é uma função determinística, com testes. Se ela falhar, o conteúdo enviado é só o marcador `[MASCARAMENTO_FALHOU]`, e a pergunta segue normalmente.

### 4. Prompts no Langfuse (prompt management, #28)

- Os arquivos em `prompts/<agente>/<nome>_v<versao>.md` continuam sendo a fonte da verdade, como pede o AGENTS.md.
- O comando `sincronizar-prompts` publica cada arquivo no Langfuse como o prompt `<agente>/<nome>` (ex.: `miau-ricio/resposta_com_fontes`), com o texto do arquivo. A versão do arquivo vai no rótulo `v<versao>`. O prompt em uso pela configuração recebe também o rótulo `production`.
- Rodar o comando de novo sem mudança nos arquivos não cria versão nova.
- Em execução, o prompt é lido do Langfuse pelo rótulo da versão configurada (`v1`, `v2`), com o arquivo local como alternativa (`fallback`) quando não há chaves ou o Langfuse não responde. Assim a avaliação pode usar outra versão sem mexer no rótulo `production`, que marca o prompt em uso pela configuração padrão.
- Cada *generation* fica vinculada ao prompt e à versão usados, e o Langfuse mostra as métricas por versão do prompt.

### 5. Scores

Cada registro de pergunta recebe scores calculados pelo código (RN01):

| Score | Tipo | Valor |
| --- | --- | --- |
| `encontrou` | booleano | a base tinha a informação (RN11) |
| `fonte_citada` | booleano | a resposta cita pelo menos uma fonte (RN10) |
| `aviso_de_preco` | booleano | a pergunta de preço recebeu o aviso da RN04 |
| `latencia_s` | numérico | segundos até a resposta |
| `erro` | booleano | a pergunta terminou em 503 |

Os scores da avaliação offline da #69 (ROUGE, cosseno, Hit@k, comportamento, fonte esperada) continuam como estão.

### 6. Evaluators gerenciados (LLM como juiz)

- Dois evaluators gerenciados do Langfuse Cloud, criados pela API do Langfuse com um script versionado no repositório:
  - **fidelidade:** a resposta só afirma o que está nos trechos recuperados;
  - **relevância:** a resposta atende à pergunta.
- Os dois rodam sobre a observação raiz de cada pergunta (`miau-ricio.pergunta`), que leva a pergunta, a resposta e os trechos usados, porque os evaluators não leem as observações filhas. Valem para os ambientes `producao` e `local` (para a equipe ver o juiz funcionando), sem as perguntas que deram erro, com uma amostra configurável do tráfego real. A avaliação offline da #69 segue com os seus scores determinísticos.
- O modelo juiz é o Gemini, pela *LLM Connection* do projeto no Langfuse (provedor Google AI Studio), cadastrada por uma pessoa da equipe pela interface. A chave do Gemini não passa pelo repositório.
- A amostra do tráfego real avaliada pelo juiz é de 20% (`LANGFUSE_AMOSTRA_JUIZ=0.2`), por conta do custo de cada avaliação. A avaliação offline é avaliada inteira.
- O texto enviado ao juiz é o já mascarado (RN30).

### 7. Alertas

- Os alertas são configurados pela interface do Langfuse; não há API documentada para eles. O passo a passo fica em `docs/semana-3/observabilidade.md`.
- O destino dos alertas é o GitHub Actions: o alerta dispara um `workflow_dispatch` num workflow do repositório, que abre uma issue com o alerta.
- O plano Hobby permite 2 alertas:
  1. **latência:** p95 de `latencia_s` acima de 60 s em 1 hora (aviso acima de 30 s);
  2. **qualidade:** média do score de fidelidade abaixo de 0,7 em 1 dia (aviso abaixo de 0,8).
- Não há métrica nativa de erro: a taxa de `erro` fica no painel e pode substituir um dos dois alertas, se a equipe preferir.

### 8. Painel

Um painel (dashboard) no Langfuse com latência p50 e p95, tokens por modelo, perguntas por dia, taxa de `encontrou`, taxa de `erro` e médias de fidelidade e relevância. Os passos para montá-lo ficam no mesmo documento.

## Termos do domínio

- `Conversa` (já existe, contexto Conversa): o identificador da conversa é o `session_id`.
- **Identificador anônimo** (termo novo, contexto Conversa, `IdentificadorAnonimo`): código aleatório gerado no navegador, que reconhece a mesma pessoa entre conversas enquanto não existe login. Não contém nem deriva de dado pessoal.

Os termos do Langfuse (trace, observation, generation, score, evaluator, session) são do ferramental e não entram no modelo de domínio.

## Regras de negócio

- **RN01:** os scores do código são contas determinísticas. O juiz dá uma nota qualitativa e não calcula valores do produto.
- **RN30 (alterada):** as perguntas reais passam a ser registradas, sempre mascaradas antes do envio. A regra passa a dizer como o mascaramento é feito e o que acontece quando ele falha.
- **RN04, RN10, RN11:** sem mudança. Os scores só registram se elas foram cumpridas.

Específicas desta funcionalidade:

- Sem as chaves do Langfuse, a API e a avaliação funcionam igual e nada é enviado.
- Uma falha ao falar com o Langfuse não muda a resposta nem o status HTTP.
- O identificador anônimo é um UUID v4. A API rejeita (ignora) valores fora desse formato, para que não entre texto livre no `user_id`.

## Entradas e saídas

- **Entrada da API:** os cabeçalhos opcionais `X-Identificador-Anonimo` e `X-Conversa` (UUID v4).
- **Configuração:** `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` (já existem), `LANGFUSE_AMBIENTE` (`local`, `producao`, `avaliacao`) e `LANGFUSE_AMOSTRA_JUIZ` (0 a 1).
- **Comandos:** `sincronizar-prompts` e `criar-avaliadores`.
- **Workflow:** `.github/workflows/alerta-langfuse.yml`, disparado pelo alerta, que abre uma issue com o nome, a severidade e o valor.
- **Saída:** registros, scores, prompts e evaluators no projeto do Langfuse, mais o documento `docs/semana-3/observabilidade.md`.

## Fora do escopo

- Login, contas e a troca do identificador anônimo pelo id da conta.
- Outros agentes além do Miau-ricio (ainda não existem).
- Guardar os registros fora do Langfuse.
- Retenção e exclusão dos dados no Langfuse a pedido da pessoa (LGPD, art. 18): fica registrado como pendência.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature).

## Dependências

- Gancho de chamadas ao LLM e cliente do Langfuse da #69.
- Chaves do Langfuse no `.env` (já configuradas).
- Uma *LLM Connection* cadastrada no projeto do Langfuse, para os evaluators.
- Decisões a registrar em `docs/decisoes.md`: mascaramento no SDK, identificador anônimo do navegador, evaluators gerenciados, prompts sincronizados do repositório para o Langfuse, alertas escolhidos.

## Riscos e limitações

- O mascaramento por padrões não pega tudo: um nome próprio ou uma alergia escritos na pergunta passam. As restrições de saúde ainda não entram pela API do Miau-ricio, mas vão entrar com o perfil (RN27); antes disso, a regra precisa ser revista.
- O juiz roda no Gemini: além do Langfuse, o texto mascarado também vai para o Google, e cada avaliação tem custo.
- No plano Hobby há só 2 alertas e uma cota mensal de registros: a amostra do juiz e o volume de testes precisam caber nela.
- A partir de 16/11/2026, os evaluators por trace deixam de rodar no Langfuse Cloud. Por isso esta spec usa evaluators por observação.
