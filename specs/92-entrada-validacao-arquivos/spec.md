# Spec: Entrada e validação de arquivos multimodais

| Campo | Valor |
|---|---|
| Issue | #92 |
| Status | Rascunho para revisão |
| Contexto delimitado | Recebimento de pergunta textual acompanhada de imagem ou PDF de nota fiscal |
| Agente | Recibaldo |

## Problema

A API precisa receber documentos enviados pela pessoa usuária, validar os arquivos e encaminhá-los ao mecanismo de extração adequado, associando a pergunta textual ao documento.

Atualmente, é necessário estabelecer um contrato de entrada e saída que permita receber diferentes formatos de documentos de maneira segura e padronizada.

## Comportamento esperado

1. Receber uma pergunta textual e um arquivo em uma única requisição.
2. Aceitar imagens e documentos PDF.
3. Validar extensão, MIME type, tamanho e integridade do arquivo.
4. Verificar se o conteúdo real corresponde ao formato declarado, sem confiar exclusivamente na extensão ou no MIME type informado pelo cliente.
5. Rejeitar arquivos vazios, corrompidos ou em formatos não suportados.
6. Identificar o tipo de arquivo e encaminhá-lo ao extrator correspondente.
7. Associar a pergunta textual ao documento recebido durante o processamento.
8. Retornar uma resposta estruturada que diferencie o recebimento, a validação, o encaminhamento e a conclusão da extração, quando disponível.
9. Informar adequadamente os erros ocorridos, sem expor detalhes internos da aplicação.

## Termos do domínio

- **NotaFiscal:** documento fiscal que contém informações da compra.
- **ItemExtraido:** informação de produto, quantidade e valor identificada em um documento, acompanhada de seu nível de confiança.
- **Revisao:** confirmação ou correção das informações extraídas pela pessoa usuária.
- **Recibaldo:** agente responsável pela leitura de documentos.

## Regras de negócio

- Somente imagens e documentos PDF são aceitos nesta entrega.
- A pergunta textual deve estar associada ao arquivo enviado.
- Arquivos vazios, inválidos ou corrompidos não devem ser encaminhados para extração.
- A validação deve considerar extensão, MIME type, tamanho e integridade do conteúdo.
- O MIME type informado pelo cliente não deve ser considerado prova suficiente do formato do arquivo.
- O limite máximo inicial é de **10 MB por arquivo**, configurável para permitir ajustes futuros conforme os resultados dos testes.
- Arquivos que ultrapassarem o limite configurado devem ser rejeitados.
- Dados pessoais presentes na nota fiscal, como CPF, devem respeitar as regras de privacidade estabelecidas no modelo de domínio.
- Informações extraídas com confiança inferior a 0,85 devem seguir a regra de revisão prevista no modelo de domínio antes de serem utilizadas em cálculos ou recomendações.
- A API não deve informar que a extração foi concluída quando apenas recebeu, validou ou encaminhou o arquivo.

## Entradas e saídas

### Entrada

Requisição HTTP utilizando `multipart/form-data`, contendo:

- `pergunta`: texto enviado pela pessoa usuária.
- `arquivo`: imagem ou documento PDF.

### Validações de entrada

A API deverá verificar:

- Presença da pergunta textual.
- Presença do arquivo.
- Extensão permitida.
- MIME type permitido.
- Correspondência entre o formato declarado e o conteúdo real.
- Tamanho máximo permitido de 10 MB.
- Integridade e possibilidade de leitura do documento.

### Saída de sucesso

A resposta deverá ser estruturada e informar, conforme a etapa alcançada:

- Identificação ou referência do documento, quando aplicável.
- Tipo do arquivo recebido.
- Situação da validação.
- Situação do encaminhamento ao extrator.
- Resultado da extração, quando disponível.
- Resposta associada à pergunta, quando disponível.

O recebimento e o encaminhamento do arquivo não devem ser confundidos com a conclusão da extração.

### Saída de erro

A API deverá retornar respostas estruturadas, com código HTTP adequado e mensagem que identifique o problema, sem expor detalhes internos da aplicação.

Mapeamento inicial sugerido:

| Situação | Código HTTP |
|---|---:|
| Pergunta ou arquivo ausente ou inválido | 400 |
| Formato não suportado | 415 |
| Arquivo acima do limite de 10 MB | 413 |
| Falha interna inesperada | 500 |

O mapeamento deverá ser validado durante a implementação e documentado no contrato da API.

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
- [ ] Imagens e documentos PDF são aceitos.
- [ ] Extensão, MIME type, tamanho e integridade são validados.
- [ ] O conteúdo real do arquivo é verificado.
- [ ] Arquivos vazios, corrompidos e formatos não suportados são rejeitados.
- [ ] Arquivos de até 10 MB são aceitos quando atendem às demais validações.
- [ ] Arquivos acima de 10 MB são rejeitados com HTTP 413.
- [ ] A pergunta textual é associada ao arquivo recebido.
- [ ] O tipo de arquivo determina o encaminhamento ao extrator adequado.
- [ ] O recebimento, o encaminhamento e a conclusão da extração são identificados separadamente.
- [ ] Os erros possuem respostas estruturadas e códigos HTTP adequados.
- [ ] Existem testes automatizados para os cenários de sucesso e falha.
- [ ] As regras de privacidade do modelo de domínio são respeitadas.

## Dependências

- Modelo de domínio do projeto.
- Disponibilidade e definição dos contratos de comunicação com os extratores de imagem e PDF.
- Alinhamento com a arquitetura atual da API.

## Riscos e limitações

- Imagens com baixa resolução, iluminação inadequada ou desfoque podem prejudicar a extração.
- PDFs digitalizados podem exigir OCR.
- O MIME type informado pelo cliente pode não corresponder ao conteúdo real do arquivo.
- Arquivos muito grandes podem comprometer o desempenho e o consumo de memória.
- A indisponibilidade dos extratores pode impedir o processamento após a validação.
- O limite inicial de 10 MB poderá ser aumentado caso os testes demonstrem necessidade.
- A qualidade das informações extraídas depende das características e da legibilidade do documento.
