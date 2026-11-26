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
    E encaminhar o documento ao extrator de imagens

  Cenário: Receber um PDF válido
    Dado que a pessoa usuária possui uma pergunta textual
    E possui um PDF válido de uma nota fiscal
    Quando enviar a pergunta e o PDF para a API
    Então a API deve aceitar o arquivo
    E associar a pergunta ao documento
    E encaminhar o documento ao extrator de PDF

  Cenário: Rejeitar formato não suportado
    Dado que a pessoa usuária possui um arquivo em formato não suportado
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E informar que o formato não é aceito

  Cenário: Rejeitar arquivo vazio
    Dado que a pessoa usuária possui um arquivo vazio
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E informar que o arquivo está vazio

  Cenário: Rejeitar arquivo corrompido
    Dado que a pessoa usuária possui um arquivo corrompido
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E informar que não foi possível validar o documento

  Cenário: Rejeitar pergunta textual vazia
    Dado que a pessoa usuária não informou uma pergunta
    Quando enviar um arquivo para a API
    Então a API deve rejeitar a requisição
    E informar que a pergunta é obrigatória

  Cenário: Rejeitar arquivo acima do limite de 10 MB
    Dado que a pessoa usuária possui um arquivo maior que 10 MB
    Quando enviar o arquivo para a API
    Então a API deve rejeitar a requisição
    E retornar o código HTTP 413
    E informar que o tamanho máximo permitido foi excedido

  Cenário: Rejeitar requisição sem arquivo
    Dado que a pessoa usuária informou uma pergunta textual
    Mas não anexou um arquivo
    Quando enviar a requisição para a API
    Então a API deve rejeitar a requisição
    E informar que o arquivo é obrigatório

  Cenário: Não informar extração concluída antes do processamento
    Dado que a API recebeu e validou um arquivo
    Quando encaminhar o documento ao extrator
    Então a API deve informar que o documento foi encaminhado
    E não deve informar que a extração foi concluída antes de receber o resultado
