# Spec: Research Agent — Recuperação de Evidências

| Campo | Valor |
| --- | --- |
| Issue | #75 |
| Status | Implementada |
| Contexto delimitado | Pesquisa de evidências (`pesquisa_evidencias`) |
| Agente | Research Agent |

## Problema

O processo de verificação de informações precisa localizar evidências científicas e documentais relacionadas a uma pergunta ou alegação, preservando a origem e a localização dos trechos recuperados.

## Comportamento esperado

O Research Agent recebe uma pergunta, realiza uma busca semântica na base de conhecimento e retorna os trechos mais relevantes, acompanhados de seus scores de similaridade e informações de proveniência.

A recuperação deve permitir que os agentes responsáveis pelas etapas posteriores utilizem as evidências sem depender de uma nova extração dos documentos originais.

## Termos do domínio

- Documento de evidência.
- Trecho de evidência.
- Evidência recuperada.
- Fonte de evidência.
- Pesquisa semântica.

## Regras de negócio

- A pergunta não pode ser vazia.
- O limite de evidências deve ser positivo.
- A API aceita limite entre 1 e 20, com padrão 5.
- Os resultados devem preservar a identificação do documento e a proveniência da fonte.
- O score representa similaridade semântica, não probabilidade de veracidade.
- Só voltam evidências com score igual ou acima do limiar de similaridade do modelo de embeddings configurado (`limiar_similaridade`, o mesmo da RN11: 0,845 para o E5). Se nenhuma passar, a lista vem vazia e `total_evidencias` é zero. O limite é aplicado antes do limiar, então a API pode devolver menos evidências que o pedido.
- A recuperação não classifica a alegação como verdadeira ou falsa.

## Entradas e saídas

**Endpoint:** `POST /api/v1/verificar`, na mesma aplicação das outras rotas (`economia.api.app`).

Entrada (`RequisicaoVerificacao`):

- `pergunta`: string obrigatória.
- `limite`: inteiro opcional, padrão 5, mínimo 1 e máximo 20.

Saída (`RespostaVerificacao`):

- `pergunta`: pergunta utilizada.
- `total_evidencias`: quantidade de resultados.
- `evidencias`: lista de evidências recuperadas.

Cada evidência contém:

- Trecho: identificador, texto, páginas inicial e final e seção.
- Documento: identificador, arquivo e hash SHA-256.
- Fonte: título, instituição, ano e URL.
- Score: similaridade de cosseno, limitada a [-1, 1] (o Qdrant pode devolver um pouco acima de 1 por arredondamento).

Erros (Problem Details, RFC 9457, `application/problem+json`):

- 422: pergunta vazia ou limite fora de 1 a 20, com `detail` explicando o campo.
- 500: falha interna (Qdrant ou modelo de embeddings), sem expor detalhes no `detail`.

## Fora do escopo

- Classificação de veracidade.
- Identificação de alegações recicladas ou parcialmente verdadeiras.
- Análise de contradições.
- Validação de conclusões.
- Redação da resposta final.

Essas responsabilidades pertencem aos demais agentes do fluxo.

## Critérios de aceitação

Os cenários de recuperação, proveniência, validação de entrada e ausência de resultados estão descritos em `cenarios.feature`.

## Dependências

- Issue #72: arquitetura multiagente e entrega do Second Challenge.
- Issue #75: implementação do Research Agent.
- Modelo `intfloat/multilingual-e5-base`.
- Qdrant e coleção exclusiva de evidências (`evidencias_verificacao_<modelo>`).
- Base de conhecimento de evidências indexadas.

A integração dos modelos internos com o estado compartilhado do LangGraph depende do alinhamento dos contratos entre os agentes.

## Riscos e limitações

- A busca semântica pode retornar trechos apenas parcialmente relacionados à pergunta.
- O score não representa confiança ou veracidade.
- A ausência de resultados não comprova que uma alegação seja falsa.
- A qualidade da recuperação depende da cobertura e qualidade documental da base indexada.
- Os contratos HTTP atuais ainda não equivalem necessariamente aos contratos internos de comunicação do LangGraph.
