# language: pt
Funcionalidade: Perguntas sobre receitas e alimentação
  Como pessoa que planeja as compras da casa
  Quero perguntar o que posso cozinhar e como aproveitar os alimentos
  Para usar melhor o que já tenho e desperdiçar menos

  Cenário: Resposta baseada na base de conhecimento cita a fonte
    Dado que a base de conhecimento contém a receita "Arroz de forno com sobras"
    Quando eu pergunto "o que posso fazer com o arroz que sobrou?"
    Então a resposta sugere a receita "Arroz de forno com sobras"
    E a resposta cita a fonte da receita

  Cenário: Receita prioriza ingredientes da despensa
    Dado que a minha despensa tem "arroz", "ovo" e "cenoura"
    E que a base de conhecimento contém receitas com esses ingredientes
    Quando eu pergunto "o que posso cozinhar hoje?"
    Então as receitas sugeridas usam ingredientes da minha despensa

  Cenário: Pergunta sem informação na base
    Dado que a base de conhecimento não contém informações sobre "sushi"
    Quando eu pergunto "como faço sushi?"
    Então a resposta informa que não encontrou essa informação na base
    E a resposta não sugere uma receita de sushi

  Cenário: Calorias vêm da tabela TACO
    Dado que a tabela TACO contém o alimento "Arroz, tipo 1, cozido"
    Quando eu pergunto "quantas calorias tem 100 g de arroz cozido?"
    Então o valor de calorias da resposta é o da tabela TACO
    E a resposta cita a tabela TACO como fonte

  Cenário: Pergunta sobre preço atual não é respondida pela base de receitas
    Quando eu pergunto "quanto está o arroz no mercado hoje?"
    Então a resposta informa que preços atuais não vêm da base de receitas
