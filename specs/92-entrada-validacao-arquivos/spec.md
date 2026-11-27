
# Spec: Entrada e validação de arquivos multimodais

| Campo | Valor |
|---|---|
| Issue | #92 |
| Status | Aprovada |
| Contexto delimitado | Recebimento de pergunta textual acompanhada de imagem ou PDF de nota fiscal |
| Agente | Recibaldo |

## Problema

A API precisa receber documentos enviados pela pessoa usuária, validar os arquivos e encaminhá-los ao mecanismo de processamento adequado, associando a pergunta textual ao documento.

Atualmente, é necessário estabelecer um contrato de entrada e saída que permita receber diferentes formatos de documentos de maneira segura e padronizada, sem manter a requisição HTTP aberta durante todo o processamento da nota fiscal.

## Comportamento esperado

1. Receber uma pergunta textual e um arquivo em uma única requisição.
2. Aceitar imagens e documentos PDF.
3. Validar extensão, MIME type, tamanho e integridade do arquivo.
4. Verificar se o conteúdo real corresponde ao formato declarado, sem confiar exclusivamente na extensão ou no MIME type informado pelo cliente.
5. Rejeitar arquivos vazios, corrompidos ou em formatos não suportados.
6. Identificar o tipo de arquivo e encaminhar a tarefa ao fluxo de processamento correspondente.
7. Associar a pergunta textual ao documento recebido durante todo o processamento.
8. Após a validação, encaminhar o processamento para execução assíncrona.
9. Retornar imediatamente um identificador do documento e a situação inicial do processamento.
10. Permitir que a pessoa usuária consulte posteriormente a situação do processamento e o resultado da extração.
11. Retornar uma resposta estruturada que diferencie o recebimento, a validação, o encaminhamento, o processamento e a conclusão da extração.
12. Informar adequadamente os erros ocorridos, sem expor detalhes internos da aplicação.
13. Manter o estado e o resultado disponíveis durante o prazo de retenção definido.
14. Remover o arquivo original temporário após o processamento, independentemente de sucesso ou falha.

## Termos do domínio

- **NotaFiscal:** documento fiscal que contém informações da compra.
- **ItemExtraido:** informação de produto, quantidade e valor identificada em um documento, acompanhada de seu nível de confiança.
- **Revisao:** confirmação ou correção das informações extraídas pela pessoa usuária.
- **Recibaldo:** agente responsável pela leitura de documentos.

## Regras de negócio

- Somente imagens e documentos PDF são aceitos nesta entrega.
- A pergunta textual deve estar associada ao arquivo enviado durante todo o processamento.
- Arquivos vazios, inválidos ou corrompidos não devem ser encaminhados para processamento.
- A validação deve considerar extensão, MIME type, tamanho e integridade do conteúdo.
- O MIME type informado pelo cliente não deve ser considerado prova suficiente do formato do arquivo.
- O limite máximo é de **10 MiB por arquivo**, equivalentes a **10.485.760 bytes** (`10 * 1024 * 1024`).
- O limite deverá ser configurável para permitir ajustes futuros conforme os resultados dos testes.
- Arquivos com tamanho superior a 10.485.760 bytes devem ser rejeitados.
- Arquivos com tamanho igual ou inferior a 10.485.760 bytes podem ser aceitos, desde que atendam às demais validações.
- A validação deverá considerar o tamanho real recebido, sem confiar exclusivamente em metadados informados pelo cliente.
- Dados pessoais presentes na nota fiscal, como CPF, devem respeitar as regras de privacidade estabelecidas no modelo de domínio.
- Informações extraídas com confiança inferior a 0,85 devem seguir a regra de revisão prevista no modelo de domínio antes de serem utilizadas em cálculos ou recomendações.
- A API não deve informar que a extração foi concluída quando apenas recebeu, validou ou encaminhou o arquivo.
- A aceitação da tarefa pela API não significa que o processamento foi concluído.
- Falhas durante o processamento devem ser identificadas e disponibilizadas na consulta de status, sem exposição de detalhes internos.
- A API somente deverá retornar HTTP 202 quando a tarefa tiver sido aceita pelo mecanismo de enfileiramento.
- A indisponibilidade do mecanismo de enfileiramento deverá impedir a confirmação de aceitação da tarefa.
- A identificação do fluxo de processamento deverá permitir o encaminhamento posterior ao extrator de imagem ou PDF correspondente.
- O estado e o resultado temporários do processamento deverão permanecer disponíveis por 24 horas após a conclusão ou falha.
- Enquanto o processamento estiver ativo, o estado não deverá expirar.
- O arquivo original temporário deverá ser removido após o encerramento do processamento, inclusive em caso de falha.
- A retenção temporária da #92 não deverá remover nem alterar registros persistentes do histórico financeiro do sistema.

## Entradas e saídas

### Endpoint de envio

- **Método:** `POST`
- **Rota:** `/api/v1/documentos`
- **Content-Type:** `multipart/form-data`

#### Entrada

A requisição deverá conter os seguintes campos:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `pergunta` | Texto | Sim | Pergunta associada ao documento enviado |
| `arquivo` | Arquivo | Sim | Imagem ou documento PDF da nota fiscal |

#### Validações de entrada

A API deverá verificar:

- Presença da pergunta textual e do arquivo.
- Pergunta não vazia.
- Extensão permitida.
- MIME type permitido.
- Correspondência entre o formato declarado e o conteúdo real.
- Tamanho máximo de 10.485.760 bytes.
- Integridade e possibilidade de leitura do documento.

A lista exata de extensões e MIME types aceitos deverá ser definida na implementação, mantendo a restrição de aceitar somente imagens e PDFs.

#### Saída de sucesso

Após validar o arquivo e aceitar a tarefa para processamento, a API deverá retornar HTTP `202 Accepted`, utilizando uma estrutura `ResultadoDoDocumento`.

| Campo | Tipo | Descrição |
|---|---|---|
| `documento_id` | Identificador | Identificador técnico do documento |
| `tipo` | Texto | `imagem` ou `pdf` |
| `etapa` | Texto | Etapa atual do processamento |
| `resposta` | Texto ou nulo | Resposta associada à pergunta |
| `itens` | Lista ou nulo | Itens identificados no documento |

Na resposta inicial, os campos `resposta` e `itens` deverão permanecer nulos, pois a extração ainda não terá sido concluída.

A etapa inicial retornada deverá representar que o documento foi encaminhado para processamento, e não que sua extração foi concluída.

### Endpoint de consulta

- **Método:** `GET`
- **Rota:** `/api/v1/documentos/{documento_id}`

O endpoint deverá permitir consultar a situação atual do processamento de um documento previamente recebido.

A resposta deverá utilizar a estrutura `ResultadoDoDocumento`, apresentando a etapa atual e, quando disponíveis, a resposta associada à pergunta e os itens extraídos.

#### Etapas do processamento

Os valores possíveis para `etapa` são:

- `recebido`: arquivo recebido pela API.
- `validado`: arquivo aprovado nas validações.
- `encaminhado`: documento encaminhado para processamento assíncrono.
- `processando`: tarefa em execução pelo worker responsável.
- `extraido`: extração efetivamente concluída.
- `falhou`: processamento interrompido por uma falha.

#### Comportamento da consulta por etapa

| Etapa | HTTP | Resposta e itens |
|---|---:|---|
| `recebido` | 200 | Nulos |
| `validado` | 200 | Nulos |
| `encaminhado` | 200 | Nulos |
| `processando` | 200 | Nulos |
| `extraido` | 200 | Disponíveis quando produzidos |
| `falhou` | 200 | Sem resultado válido; mensagem genérica de falha |

Um identificador inexistente ou cujo estado tenha expirado deverá retornar HTTP `404`.

Cada item extraído deverá conter:

| Campo | Tipo | Descrição |
|---|---|---|
| `descricao` | Texto | Descrição do produto identificado |
| `quantidade` | Numérico | Quantidade identificada |
| `unidade` | Texto | Unidade de medida |
| `valor_total` | Inteiro | Valor monetário em centavos |
| `confianca` | Numérico | Nível de confiança entre 0 e 1 |
| `revisar` | Booleano | Indica se o item exige revisão |

O campo `revisar` deverá ser derivado do nível de confiança: verdadeiro quando `confianca` for inferior a 0,85, conforme a regra de negócio do domínio.

Os campos `resposta` e `itens` deverão permanecer nulos enquanto a extração não estiver concluída.

O recebimento, a validação e o encaminhamento não devem ser confundidos com a conclusão da extração.

### Saída de erro

As respostas de erro deverão seguir o formato **Problem Details**, conforme a RFC 9457, sem expor detalhes internos da aplicação.

#### Erros no envio do documento

| Situação | Código HTTP |
|---|---:|
| Pergunta ou arquivo ausente ou inválido | 400 |
| Arquivo acima do limite de 10.485.760 bytes | 413 |
| Formato não suportado | 415 |
| Conteúdo inválido, vazio, corrompido ou incompatível com o formato declarado | 422 |
| Indisponibilidade do mecanismo de enfileiramento | 503 |
| Falha interna inesperada | 500 |

#### Erros na consulta do documento

| Situação | Código HTTP |
|---|---:|
| Documento não encontrado ou estado expirado | 404 |
| Falha interna inesperada | 500 |

Falhas ocorridas durante o processamento assíncrono deverão ser identificadas pela etapa `falhou` na consulta do documento.

## Processamento assíncrono

O processamento deverá ocorrer em segundo plano, sem manter a requisição HTTP aberta até a conclusão da extração.

O fluxo proposto é:

1. O frontend envia a pergunta e o arquivo para a API.
2. A API realiza as validações iniciais.
3. A API gera um identificador técnico para o documento.
4. O arquivo validado é armazenado temporariamente em diretório compartilhado entre API e worker.
5. O estado inicial do processamento é registrado.
6. A tarefa é encaminhada para a fila RQ, utilizando Redis.
7. A API confirma a aceitação da tarefa e retorna HTTP `202 Accepted`, com o identificador e a etapa inicial.
8. Um worker executa o processamento do documento.
9. O worker identifica o tipo de documento e encaminha a tarefa ao fluxo de extração correspondente.
10. O estado do processamento é atualizado no Redis durante a execução.
11. Ao concluir, o worker disponibiliza o resultado ou registra a falha.
12. O arquivo original temporário é removido após o encerramento do processamento.
13. O estado e o resultado permanecem disponíveis para consulta durante 24 horas após a conclusão ou falha.
14. Após o prazo de retenção, o estado e o resultado temporários expiram.
15. O frontend consulta o endpoint de status até que o processamento seja concluído ou apresente falha.

Se a fila estiver indisponível ou não aceitar a tarefa, a API deverá retornar HTTP `503`, não confirmar o encaminhamento e remover o arquivo temporário recebido.

A implementação do OCR e da extração específica de PDFs será tratada nas respectivas entregas (#93 e #94). Nesta issue, o foco é estabelecer o recebimento, a validação e o encaminhamento adequado.

### Infraestrutura e persistência temporária

A implementação utilizará a infraestrutura Redis e RQ já prevista na arquitetura do EconoMIA.

#### Redis

O Redis será responsável por armazenar temporariamente:

- Identificador do documento.
- Tipo do documento.
- Pergunta associada ao documento.
- Etapa atual do processamento.
- Resultado da extração, quando disponível.
- Mensagem genérica de falha, quando aplicável.

O registro de estado e resultado deverá utilizar o identificador técnico do documento como referência.

A política de expiração será:

- Durante o processamento: o estado deverá permanecer disponível, sem expiração prematura.
- Após conclusão: estado e resultado com TTL de 86.400 segundos.
- Após falha: estado e informação da falha com TTL de 86.400 segundos.
- Após expiração: a consulta deverá retornar HTTP `404`.

A expiração deverá ser aplicada a partir do encerramento do processamento, e não do recebimento inicial do arquivo.

#### RQ

O RQ será responsável por gerenciar a fila e a execução das tarefas assíncronas.

A retenção dos resultados e das falhas das tarefas deverá ser configurada explicitamente:

- `result_ttl=86400`: retenção do resultado da tarefa concluída por 24 horas.
- `failure_ttl=86400`: retenção da tarefa com falha por 24 horas.

A retenção do RQ não substitui o registro de estado e resultado no Redis. O endpoint de consulta deverá utilizar o estado temporário do documento como fonte de informação para responder à pessoa usuária.

#### Arquivos temporários

Os arquivos recebidos deverão ser armazenados em diretório temporário compartilhado entre API e worker.

O armazenamento deverá:

- Permitir que o worker acesse o arquivo recebido pela API.
- Evitar persistência definitiva do documento original.
- Remover o arquivo após sucesso ou falha do processamento.
- Remover o arquivo caso a tarefa não possa ser aceita pela fila.
- Não manter arquivos temporários após a finalização da tarefa.

A limpeza deverá ser considerada também em situações de exceção durante o processamento.

#### Separação de responsabilidades

A retenção de 24 horas aplica-se exclusivamente ao estado e ao resultado temporários da execução da #92.

Ela não altera a persistência de dados financeiros, histórico de compras ou demais registros permanentes do domínio.

## Fora do escopo

- Consulta de QR Code ou chave de acesso em serviços externos.
- Consulta externa de NFC-e.
- Implementação completa do OCR nesta issue.
- Implementação completa da extração de conteúdo de PDF nesta issue.
- Interface frontend de envio de arquivos.
- Histórico de compras.
- Persistência definitiva dos documentos recebidos.
- Implementação de mecanismos adicionais de revisão manual dos itens extraídos.

## Critérios de aceitação

- [ ] Existe endpoint para receber pergunta textual e arquivo.
- [ ] O contrato de entrada e saída está documentado.
- [ ] Existe endpoint para consultar a situação do processamento.
- [ ] Imagens e documentos PDF são aceitos.
- [ ] Extensão, MIME type, tamanho e integridade são validados.
- [ ] O conteúdo real do arquivo é verificado.
- [ ] Arquivos vazios, corrompidos e formatos não suportados são rejeitados.
- [ ] Arquivos com tamanho igual ou inferior a 10.485.760 bytes são aceitos quando atendem às demais validações.
- [ ] Arquivos acima de 10.485.760 bytes são rejeitados com HTTP 413.
- [ ] A pergunta textual é associada ao arquivo recebido.
- [ ] O tipo de arquivo determina o encaminhamento ao fluxo de processamento adequado.
- [ ] A API utiliza Redis e RQ para o processamento assíncrono.
- [ ] A API retorna HTTP 202 quando o processamento é aceito para execução assíncrona.
- [ ] A API não retorna HTTP 202 quando o mecanismo de enfileiramento está indisponível.
- [ ] O identificador do documento permite consultar o processamento posteriormente.
- [ ] O recebimento, a validação, o encaminhamento, o processamento e a conclusão da extração são identificados separadamente.
- [ ] Falhas durante o processamento são identificadas e disponibilizadas na consulta de status.
- [ ] Os erros possuem respostas estruturadas em Problem Details e códigos HTTP adequados.
- [ ] O estado e o resultado permanecem disponíveis durante 24 horas após conclusão ou falha.
- [ ] O estado não expira enquanto a tarefa estiver em execução.
- [ ] O RQ utiliza retenção de 24 horas para resultados e falhas.
- [ ] O arquivo original temporário é removido após sucesso ou falha.
- [ ] O arquivo temporário é removido quando a fila não aceita a tarefa.
- [ ] A consulta de um documento expirado retorna HTTP 404.
- [ ] A retenção temporária não altera os registros financeiros persistentes.
- [ ] Existe teste para conteúdo incompatível com o formato declarado.
- [ ] Existe teste para indisponibilidade do mecanismo de enfileiramento.
- [ ] Existem testes automatizados para os cenários de sucesso e falha.
- [ ] As regras de privacidade do modelo de domínio são respeitadas.

## Dependências

- Modelo de domínio do projeto.
- Disponibilidade e definição dos contratos de comunicação com os extratores de imagem e PDF.
- Alinhamento com a arquitetura atual da API.
- Disponibilidade da infraestrutura Redis e RQ.
- Diretório temporário compartilhado entre API e worker.

## Riscos e limitações

- Imagens com baixa resolução, iluminação inadequada ou desfoque podem prejudicar a extração.
- PDFs digitalizados podem exigir OCR.
- O MIME type informado pelo cliente pode não corresponder ao conteúdo real do arquivo.
- Arquivos muito grandes podem comprometer o desempenho e o consumo de memória.
- A indisponibilidade dos extratores pode impedir o processamento após a validação.
- A indisponibilidade da fila pode impedir o agendamento de novas tarefas.
- Falhas nos workers podem interromper o processamento.
- A indisponibilidade do Redis pode impedir a consulta e atualização do estado temporário.
- A limpeza dos arquivos temporários deve ocorrer mesmo diante de exceções.
- O limite de 10 MiB poderá ser ajustado futuramente caso os testes demonstrem necessidade.
- A qualidade das informações extraídas depende das características e da legibilidade do documento.
