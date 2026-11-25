# language: pt
Funcionalidade: Communication Agent
  Como pessoa que quer saber se uma afirmação sobre alimentação tem base
  Quero receber o veredito em linguagem simples e no tamanho que escolhi
  Para entender a resposta e saber de onde ela veio

  Cenário: Perfil geral com a validação aprovada
    Dado duas evidências recuperadas, com scores 0,87 e 0,80
    E uma análise "parcial" que cita as duas evidências
    E uma validação aprovada
    E o LLM escreve a mensagem "Em parte. O Guia Alimentar fala de ovos, mas não de colesterol."
    Quando o Communication Agent monta o veredito para o perfil "consumidor_geral"
    Então o veredito tem a classificação "parcial"
    E o veredito foi aprovado pela validação
    E o veredito tem 1 fonte, o "Guia Alimentar para a População Brasileira"
    E a mensagem é "Em parte. O Guia Alimentar fala de ovos, mas não de colesterol."

  Cenário: Perfil rápido corta a mensagem em duas frases
    Dado duas evidências recuperadas, com scores 0,87 e 0,80
    E uma análise "reciclada" que cita as duas evidências
    E uma validação aprovada
    E o LLM escreve a mensagem "Sim. O Guia recomenda evitar. Isso vale para todas as idades."
    Quando o Communication Agent monta o veredito para o perfil "consumidor_rapido"
    Então a mensagem é "Sim. O Guia recomenda evitar."

  Cenário: As fontes vêm das evidências citadas, não do LLM
    Dado duas evidências recuperadas, com scores 0,87 e 0,80
    E uma análise "parcial" que cita as duas evidências
    E uma validação aprovada
    E o LLM escreve a mensagem "Segundo a OMS e o Guia Alimentar, em parte."
    Quando o Communication Agent monta o veredito para o perfil "consumidor_geral"
    Então o veredito tem 1 fonte, o "Guia Alimentar para a População Brasileira"

  Cenário: Verificação não conclusiva no limite de retornos
    Dado duas evidências recuperadas, com scores 0,87 e 0,80
    E uma análise "reciclada" que cita as duas evidências
    E uma validação reprovada com o motivo "A confiança está abaixo do limiar."
    Quando o Communication Agent monta o veredito para o perfil "consumidor_geral"
    Então o veredito não foi aprovado pela validação
    E a mensagem diz que a verificação não foi conclusiva
    E o LLM não é chamado

  Cenário: Alegação nova sem evidência
    Dado nenhuma evidência recuperada
    E uma análise "nova" sem citações
    E uma validação aprovada
    Quando o Communication Agent monta o veredito para o perfil "consumidor_geral"
    Então o veredito não tem fontes
    E o veredito tem a classificação "nova"
    E a mensagem diz que a base não tem evidência sobre a alegação
    E o LLM não é chamado

  Cenário: Saída inválida do LLM usa a justificativa da análise
    Dado duas evidências recuperadas, com scores 0,87 e 0,80
    E uma análise "parcial" com a justificativa "O Guia Alimentar trata do consumo de ovos [1]."
    E uma validação aprovada
    E o LLM devolve um texto que não é JSON
    Quando o Communication Agent monta o veredito para o perfil "consumidor_geral"
    Então a mensagem é "O Guia Alimentar trata do consumo de ovos."
    E o veredito tem a classificação "parcial"
