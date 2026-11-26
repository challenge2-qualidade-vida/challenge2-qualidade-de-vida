# language: pt
Funcionalidade: Interface da demo da verificação de alegações
  Como pessoa que recebeu uma afirmação sobre alimentação
  Quero ver o veredito e o caminho que os agentes fizeram
  Para entender a resposta e confiar em de onde ela veio

  Cenário: Veredito aprovado direto
    Dado a alegação "Alimentos ultraprocessados devem ser evitados"
    E o perfil "consumidor_geral"
    Quando eu peço a verificação
    Então vejo a classificação "reciclada"
    E vejo a fonte "Guia Alimentar para a População Brasileira"
    E o caminho dos agentes é Research, Analysis, Validation e Communication

  Cenário: Retorno do Validation aparece no caminho
    Dado a alegação "O feijão tem fibra e por isso cura o diabetes"
    E o perfil "consumidor_geral"
    Quando eu peço a verificação
    Então o caminho dos agentes mostra a validação reprovada com retorno ao Research
    E depois do retorno há um novo Research, Analysis e Validation

  Cenário: Perfil rápido
    Dado a alegação "Alimentos ultraprocessados devem ser evitados"
    E o perfil "consumidor_rapido"
    Quando eu peço a verificação
    Então a mensagem tem no máximo 2 frases

  Cenário: Verificação não conclusiva
    Dado um veredito com "aprovado_pela_validacao" falso
    Quando a tela mostra o veredito
    Então aparece o aviso de que a verificação não foi conclusiva

  Cenário: Alegação vazia
    Dado a alegação ""
    Quando eu peço a verificação
    Então aparece o pedido para escrever a alegação
    E a API não é chamada

  Cenário: Tela desligada por padrão
    Dado o site sem a flag "verificacao"
    Quando eu abro o site
    Então a aba Verificar não aparece
