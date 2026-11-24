# language: pt

Funcionalidade: Recuperação semântica de evidências científicas
  Como agente responsável pela pesquisa de evidências
  Quero recuperar trechos relevantes para uma pergunta
  Para fornecer fontes rastreáveis às etapas posteriores de verificação

  Cenário: Recuperar evidências relacionadas à pergunta
    Dado que a base de conhecimento possui documentos indexados
    E que a pergunta está preenchida
    Quando solicito a recuperação de evidências com limite 5
    Então o sistema deve retornar até 5 evidências relevantes
    E cada evidência deve apresentar um score de similaridade

  Cenário: Preservar a proveniência das evidências
    Dado que uma evidência foi recuperada
    Quando o sistema monta a resposta
    Então deve informar o texto do trecho recuperado
    E identificar o documento de origem
    E apresentar as informações bibliográficas disponíveis
    E preservar a localização do trecho no documento

  Cenário: Rejeitar pergunta vazia
    Dado que a pergunta está vazia ou contém somente espaços
    Quando envio uma solicitação para o endpoint "/verificar"
    Então a API deve retornar HTTP 422
    E informar que a pergunta não pode ser vazia

  Cenário: Rejeitar limite de evidências inválido
    Dado que solicito um limite menor que 1 ou maior que 20
    Quando envio uma solicitação para o endpoint "/verificar"
    Então a API deve retornar HTTP 422

  Cenário: Retornar resposta sem evidências
    Dado que a pergunta não possui evidências correspondentes na base indexada
    Quando solicito a recuperação de evidências
    Então o sistema deve retornar uma lista vazia
    E informar total_evidencias igual a zero
