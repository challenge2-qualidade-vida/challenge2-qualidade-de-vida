# language: pt
Funcionalidade: Base de conhecimento com 20 fontes e avaliação do RAG
  Como equipe do EconoMIA
  Quero ampliar a base de conhecimento e medir o RAG antes e depois
  Para saber se os documentos novos melhoram as respostas do Miau-ricio

  Cenário: A base de conhecimento tem pelo menos 20 documentos-fonte
    Dado o catálogo de documentos da base de conhecimento
    Então o catálogo tem pelo menos 20 documentos-fonte
    E cada documento tem título, instituição, link e licença

  Cenário: A avaliação da recuperação separa o resultado por categoria
    Dado que a base contém só a receita "Bolo de cenoura"
    E um conjunto de avaliação com a pergunta "como fazer bolo de cenoura?" na categoria "receita" esperando essa receita
    E a pergunta "quantas calorias tem o arroz cozido?" na categoria "nutricao" esperando o documento "taco-2011"
    Quando eu avalio a recuperação
    Então o Recall@5 da categoria "receita" é 1
    E o Recall@5 da categoria "nutricao" é 0

  Cenário: A avaliação das respostas confere o comportamento esperado
    Dado que a base contém só a receita "Bolo de cenoura"
    E um conjunto de avaliação com a pergunta "como fazer bolo de cenoura?" na categoria "receita" esperando essa receita
    E a pergunta "como trocar o pneu do carro?" na categoria "sem_resposta" sem resposta na base
    E a pergunta "quanto custa o arroz hoje?" na categoria "preco" com aviso de preço
    Quando eu avalio as respostas
    Então a acurácia do comportamento é 1
    E a resposta da categoria "receita" cita a fonte esperada

  Cenário: A comparação entre duas execuções mostra a diferença
    Dado uma execução com Recall@5 de 0,50
    E uma execução seguinte com Recall@5 de 0,75
    Quando eu comparo as duas execuções
    Então a diferença do Recall@5 é +0,25

  Cenário: A resposta estruturada cita os trechos usados mesmo sem colchetes no texto
    Dado que a base contém só a receita "Bolo de cenoura"
    E que o LLM responde em JSON usando o trecho 1, sem colchetes no texto
    Quando eu pergunto "como fazer bolo de cenoura?" com a resposta estruturada
    Então a resposta é aceita
    E a fonte da resposta é a da receita "Bolo de cenoura"

  Cenário: A resposta sem citação ganha uma segunda tentativa
    Dado que a base contém só a receita "Bolo de cenoura"
    E que o LLM responde sem citar na primeira vez e citando na segunda
    Quando eu pergunto "como fazer bolo de cenoura?" com a segunda tentativa
    Então a resposta é aceita
    E o LLM foi chamado 2 vezes
