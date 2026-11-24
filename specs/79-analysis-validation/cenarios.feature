# language: pt
Funcionalidade: Análise e validação de alegações
  Como sistema de verificação do EconoMIA
  Quero classificar cada alegação a partir das evidências e conferir a análise antes do veredito
  Para que nenhuma explicação sem fundamento chegue à pessoa

  Contexto:
    Dado o limiar mínimo de confiança de 0,845

  Cenário: Alegação reciclada com citação válida é aprovada direto
    Dado a alegação "Ultraprocessados devem ser evitados"
    E duas evidências recuperadas, a primeira com score 0,90
    E o LLM classifica como "reciclada" citando a evidência 1
    E o LLM não aponta contradição
    Quando o Analysis Agent analisa e o Validation Agent valida
    Então a análise cita o trecho da evidência 1
    E a confiança é 0,90
    E a validação é aprovada sem retorno

  Cenário: Citação inexistente reprova e volta para o Analysis
    Dado duas evidências recuperadas
    E o LLM classifica como "parcial" citando a evidência 7
    Quando o Analysis Agent analisa e o Validation Agent valida
    Então a análise registra a citação 7 como inválida
    E a validação é reprovada com retorno para o "analysis"

  Cenário: Evidência fraca reprova e volta para o Research
    Dado duas evidências recuperadas, a maior com score 0,80
    E o LLM classifica como "reciclada" citando a evidência 1
    Quando o Analysis Agent analisa e o Validation Agent valida
    Então a confiança é 0,80
    E a validação é reprovada com retorno para o "research"

  Cenário: Alegação nova com evidência forte reprova e volta para o Analysis
    Dado duas evidências recuperadas, a primeira com score 0,92
    E o LLM classifica como "nova" sem citar evidências
    Quando o Analysis Agent analisa e o Validation Agent valida
    Então a validação é reprovada com retorno para o "analysis"

  Cenário: Alegação nova sem evidência relevante é aprovada
    Dado duas evidências recuperadas, a maior com score 0,78
    E o LLM classifica como "nova" sem citar evidências
    E o LLM não aponta contradição
    Quando o Analysis Agent analisa e o Validation Agent valida
    Então a validação é aprovada sem retorno

  Cenário: Contradição apontada pelo LLM reprova e volta para o Analysis
    Dado duas evidências recuperadas, a primeira com score 0,90
    E o LLM classifica como "reciclada" citando a evidência 1
    E o LLM aponta que a justificativa contradiz a evidência
    Quando o Analysis Agent analisa e o Validation Agent valida
    Então a validação é reprovada com retorno para o "analysis"

  Cenário: Saída inválida do LLM não vira análise
    Dado duas evidências recuperadas
    E o LLM devolve um texto que não é JSON
    Quando o Analysis Agent analisa e o Validation Agent valida
    Então não há análise
    E a validação é reprovada com retorno para o "analysis"

  Cenário: Retorno ao Analysis na avaliação corrige a classificação
    Dado um caso de avaliação com a classificação esperada "reciclada"
    E na primeira análise o LLM cita uma evidência inexistente
    E na segunda análise o LLM classifica como "reciclada" citando a evidência 1
    Quando a avaliação roda o caso
    Então o caso acerta a classificação com 1 retorno para o "analysis"

  Cenário: A avaliação para no limite de retornos
    Dado um caso de avaliação em que toda análise cita uma evidência inexistente
    Quando a avaliação roda o caso
    Então o caso termina reprovado depois de 2 retornos
