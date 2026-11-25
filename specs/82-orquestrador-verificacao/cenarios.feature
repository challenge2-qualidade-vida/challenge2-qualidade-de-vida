# language: pt
Funcionalidade: Orquestrador da verificação de alegações
  Como pessoa que quer saber se uma afirmação sobre alimentação tem base
  Quero enviar a alegação e receber o veredito com os passos de cada agente
  Para entender a resposta e ver como ela foi conferida

  Contexto:
    Dado um orquestrador com limite inicial de 5 trechos, teto de 10 trechos e no máximo 2 retornos

  Cenário: Análise aprovada direto
    Dado que a validação aprova a primeira análise
    Quando a alegação "Ovo aumenta o colesterol?" é verificada no perfil "consumidor_geral"
    Então os agentes rodam na ordem "research, analysis, validation, communication"
    E o veredito foi aprovado pela validação
    E a verificação teve 0 retornos

  Cenário: Retorno ao Research dobra o limite e recomeça a análise sem os motivos
    Dado que a validação devolve a primeira análise para o "research" com o motivo "A confiança está abaixo do limiar."
    E que a validação aprova a segunda análise
    Quando a alegação "Ovo aumenta o colesterol?" é verificada no perfil "consumidor_geral"
    Então o Research busca com os limites "5, 10"
    E a segunda análise não recebe motivos
    E a verificação teve 1 retorno

  Cenário: A busca não passa do teto
    Dado que a validação devolve as duas primeiras análises para o "research" com o motivo "A confiança está abaixo do limiar."
    E que a validação aprova a terceira análise
    Quando a alegação "Ovo aumenta o colesterol?" é verificada no perfil "consumidor_geral"
    Então o Research busca com os limites "5, 10, 10"

  Cenário: Retorno ao Analysis mantém as evidências e repassa os motivos
    Dado que a validação devolve a primeira análise para o "analysis" com o motivo "A citação 7 não está entre as 5 evidências recuperadas."
    E que a validação aprova a segunda análise
    Quando a alegação "Ovo aumenta o colesterol?" é verificada no perfil "consumidor_geral"
    Então o Research busca com os limites "5"
    E a segunda análise recebe o motivo "A citação 7 não está entre as 5 evidências recuperadas."

  Cenário: Limite de retornos leva a um veredito não conclusivo
    Dado que a validação devolve todas as análises para o "analysis" com o motivo "A justificativa contradiz a evidência citada."
    Quando a alegação "Ovo aumenta o colesterol?" é verificada no perfil "consumidor_geral"
    Então o Analysis roda 3 vezes
    E a verificação teve 2 retornos
    E o último agente é o "communication"
    E o veredito não foi aprovado pela validação

  Cenário: O perfil de leitura chega ao Communication
    Dado que a validação aprova a primeira análise
    Quando a alegação "Ovo aumenta o colesterol?" é verificada no perfil "consumidor_rapido"
    Então o Communication recebe o perfil "consumidor_rapido"

  Cenário: A rota devolve o veredito e o histórico
    Dado que a validação aprova a primeira análise
    Quando a API recebe POST /api/v1/verificacoes com a alegação "Ovo aumenta o colesterol?" e o perfil "consumidor_geral"
    Então a resposta tem o status 200
    E a resposta traz o veredito e 4 etapas no histórico

  Cenário: Alegação vazia é recusada
    Quando a API recebe POST /api/v1/verificacoes com a alegação "   " e o perfil "consumidor_geral"
    Então a resposta tem o status 422 em Problem Details

  Cenário: LLM indisponível
    Dado que o LLM não responde
    Quando a API recebe POST /api/v1/verificacoes com a alegação "Ovo aumenta o colesterol?" e o perfil "consumidor_geral"
    Então a resposta tem o status 503 em Problem Details
