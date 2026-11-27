
# language: pt

Funcionalidade: Entrada e validação de arquivos multimodais
  Como pessoa usuária do EconoMIA
  Quero enviar uma pergunta acompanhada de uma imagem ou PDF
  Para obter informações extraídas do meu documento

  Cenário: Receber uma imagem válida
    Dado que a pessoa usuária possui uma pergunta textual
    E possui uma imagem válida de uma nota fiscal
    Quando enviar a pergunta e a imagem para a API
    Então a API deve aceitar o arquivo
    E associar a pergunta ao documento
    E identificar o documento como imagem
    E encaminhar a tarefa para o fluxo de processamento de imagens
    E retornar o código HTTP 202

  Cenário: Receber um PDF válido
    Dado que a pessoa usuária possui uma pergunta textual
    E possui um PDF válido de uma nota fiscal
    Quando enviar a pergunta e o PDF para a API
    Então a API deve aceitar o arquivo
    E associar a pergunta ao documento
    E identificar o documento como PDF
    E encaminhar a tarefa para o fluxo de processamento de PDFs
    E retornar o código HTTP 202

  Cenário: Rejeitar formato não suportado
    Dado que a pessoa usuária possui um arquivo em formato não suportado
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 415
    E informar que o formato não é aceito

  Cenário: Rejeitar arquivo vazio
    Dado que a pessoa usuária possui um arquivo vazio
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 422
    E informar que o arquivo está vazio

  Cenário: Rejeitar arquivo corrompido
    Dado que a pessoa usuária possui um arquivo corrompido
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 422
    E informar que não foi possível validar o documento

  Cenário: Rejeitar arquivo com MIME type incompatível com o conteúdo
    Dado que a pessoa usuária possui um arquivo cujo conteúdo real não corresponde ao MIME type declarado
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 422
    E informar que o conteúdo do documento é inválido

  Cenário: Rejeitar pergunta textual vazia
    Dado que a pessoa usuária não informou uma pergunta
    Quando enviar um arquivo para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 400
    E informar que a pergunta é obrigatória

  Cenário: Rejeitar arquivo acima do limite de 10 MiB
    Dado que a pessoa usuária possui um arquivo com tamanho superior a 10.485.760 bytes
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 413
    E informar que o tamanho máximo permitido foi excedido

  Cenário: Rejeitar requisição sem arquivo
    Dado que a pessoa usuária informou uma pergunta textual
    Mas não anexou um arquivo
    Quando enviar a requisição para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 400
    E informar que o arquivo é obrigatório

  Cenário: Não informar extração concluída antes do processamento
    Dado que a API recebeu e validou um arquivo
    Quando encaminhar o documento para processamento assíncrono
    Então a API deve informar que o documento foi encaminhado
    E retornar o código HTTP 202
    E não deve informar que a extração foi concluída
    E os campos de resposta e itens devem permanecer nulos

  Cenário: Rejeitar envio quando a fila estiver indisponível
    Dado que a pessoa usuária possui uma pergunta textual
    E possui um arquivo válido
    E o mecanismo de enfileiramento está indisponível
    Quando enviar a pergunta e o arquivo para a API
    Então a API deve informar que não foi possível aceitar a tarefa
    E retornar o código HTTP 503
    E não deve informar que o documento foi encaminhado
    E deve remover o arquivo temporário recebido

  Cenário: Consultar documento ainda em processamento
    Dado que existe um documento encaminhado para processamento
    E seu estado atual é processando
    Quando consultar o documento pelo seu identificador
    Então a API deve retornar o código HTTP 200
    E informar a etapa processando
    E manter os campos de resposta e itens nulos

  Cenário: Consultar documento com processamento concluído
    Dado que existe um documento cujo processamento foi concluído
    Quando consultar o documento pelo seu identificador
    Então a API deve retornar o código HTTP 200
    E informar a etapa extraido
    E disponibilizar a resposta e os itens extraídos

  Cenário: Consultar documento com falha no processamento
    Dado que existe um documento cujo processamento falhou
    Quando consultar o documento pelo seu identificador
    Então a API deve retornar o código HTTP 200
    E informar a etapa falhou
    E apresentar uma mensagem genérica de falha
    E não expor detalhes internos da aplicação

  Cenário: Consultar documento inexistente
    Dado que não existe documento com o identificador informado
    Quando consultar o documento pelo seu identificador
    Então a API deve retornar o código HTTP 404
    E informar que o documento não foi encontrado

  Cenário: Remover arquivo temporário após o processamento
    Dado que existe um documento armazenado temporariamente
    Quando o processamento do documento for concluído ou falhar
    Então o arquivo original temporário deve ser removido
    E o estado e o resultado do processamento devem continuar disponíveis durante o prazo de retenção

  Cenário: Expirar estado e resultado após 24 horas
    Dado que existe um documento cujo processamento foi concluído ou falhou
    E já transcorreram 24 horas desde a finalização do processamento
    Quando consultar o documento pelo seu identificador
    Então a API deve retornar o código HTTP 404
    E informar que o documento não foi encontrado
