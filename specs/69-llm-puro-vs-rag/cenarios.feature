# language: pt
Funcionalidade: Comparação do LLM puro com o LLM com RAG
  Como pessoa que desenvolve o Miau-ricio
  Quero avaliar as mesmas perguntas com e sem a base de conhecimento, com as chamadas registradas
  Para saber quanto o RAG melhora as respostas e qual LLM usar

  Cenário: Resposta do modo puro não tem fontes
    Dado um LLM que responde "Guarde a alface seca num pote fechado."
    Quando eu pergunto no modo puro "como conservo alface?"
    Então a resposta traz o texto do LLM
    E a resposta não tem trechos nem fontes
    E nenhuma busca é feita na base de conhecimento

  Cenário: No modo puro, o LLM pode dizer que não sabe
    Dado um LLM que responde "NAO_SEI"
    Quando eu pergunto no modo puro "quanto tempo dura o fermento biológico depois de aberto?"
    Então a resposta informa que não encontrou a informação

  Cenário: Resposta igual à referência tem as métricas de texto no máximo
    Dado uma pergunta com a resposta de referência "Guarde a alface seca num pote fechado."
    E um LLM que responde "Guarde a alface seca num pote fechado."
    Quando eu avalio a pergunta no modo puro
    Então o ROUGE-1 F1 da pergunta é 1,0
    E o ROUGE-L F1 da pergunta é 1,0

  Cenário: Pergunta sem resposta de referência não tem métricas de texto
    Dado uma pergunta sem resposta de referência
    Quando eu avalio a pergunta no modo puro
    Então a pergunta não tem ROUGE-1, ROUGE-L nem cosseno

  Cenário: Hit@k marca se o trecho do gabarito foi recuperado
    Dado que a base de conhecimento contém um trecho sobre conservação de folhas
    E uma pergunta cujo gabarito é esse trecho
    Quando eu avalio a pergunta no modo RAG
    Então o Hit@k da pergunta é 1

  Cenário: Modo puro não tem Hit@k
    Dado uma pergunta com gabarito
    Quando eu avalio a pergunta no modo puro
    Então a pergunta não tem Hit@k

  Cenário: Cada chamada ao LLM é registrada com modelo, prompt, tokens e latência
    Dado um registro de chamadas ligado ao LLM
    Quando eu pergunto no modo puro "como conservo alface?"
    Então o registro recebe uma chamada com o nome do modelo
    E a chamada traz o prompt, a resposta, os tokens de entrada e de saída e os segundos

  Cenário: Sem as chaves do Langfuse, nada é enviado
    Dado que as chaves do Langfuse não estão configuradas
    Quando eu avalio uma pergunta
    Então a avaliação termina normalmente
    E nenhum registro é enviado

  Cenário: Falha no registro não interrompe a avaliação
    Dado um registro de chamadas que falha ao enviar
    Quando eu avalio uma pergunta
    Então a avaliação termina normalmente
    E a resposta é a mesma de uma avaliação sem registro
