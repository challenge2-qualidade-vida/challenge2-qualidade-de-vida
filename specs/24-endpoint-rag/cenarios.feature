# language: pt
Funcionalidade: Perguntar ao Miau-ricio pela API
  Como pessoa que planeja as compras da casa
  Quero fazer uma pergunta sobre receitas e alimentação numa tela simples
  Para ver a resposta e conferir de onde ela veio

  Cenário: Pergunta respondida com as fontes
    Dado que a base contém a orientação "Conservação de folhas" da "Embrapa"
    Quando eu envio a pergunta "como conservar folhas?" para a API
    Então a API responde com sucesso
    E a resposta foi encontrada na base
    E a fonte 1 da resposta é "Conservação de folhas"

  Cenário: Pergunta sem informação na base
    Dado que a base contém a orientação "Conservação de folhas" da "Embrapa"
    Quando eu envio a pergunta "qual o melhor time de futebol?" para a API
    Então a API responde com sucesso
    E a resposta diz que não encontrou a informação
    E a resposta não tem fontes

  Cenário: Pergunta de preço recebe o aviso
    Dado que a base contém a orientação "Conservação de folhas" da "Embrapa"
    Quando eu envio a pergunta "quanto custa o arroz hoje?" para a API
    Então a API responde com sucesso
    E a resposta traz o aviso de preço

  Cenário: Pergunta vazia é recusada
    Quando eu envio a pergunta "   " para a API
    Então a API recusa a pergunta como inválida

  Cenário: Serviço do RAG fora do ar
    Dado que o banco vetorial está fora do ar
    Quando eu envio a pergunta "como conservar folhas?" para a API
    Então a API responde que o Miau-ricio está indisponível
