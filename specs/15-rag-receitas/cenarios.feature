# language: pt
Funcionalidade: Receitas e perguntas sobre alimentação
  Como pessoa que planeja as compras da casa
  Quero saber o que cozinhar com o que tenho e como aproveitar os alimentos
  Para usar melhor o que já comprei e desperdiçar menos

  Cenário: Receita sugerida com os ingredientes informados cita a fonte
    Dado que a base de receitas contém a receita "Arroz de forno com sobras"
    E que essa receita usa "arroz", "ovo" e "cenoura"
    Quando eu pergunto "o que posso fazer com arroz, ovo e cenoura?"
    Então a resposta sugere a receita "Arroz de forno com sobras"
    E a resposta cita a fonte da receita com o link

  Cenário: Receitas completas aparecem antes das que têm ingredientes faltando
    Dado que a base de receitas contém a receita "Omelete de legumes", que usa "ovo" e "cenoura"
    E que a base de receitas contém a receita "Torta de legumes", que usa "ovo", "cenoura", "farinha" e "leite"
    Quando eu pergunto "o que posso fazer com ovo e cenoura?"
    Então a receita "Omelete de legumes" aparece antes da receita "Torta de legumes"
    E a resposta informa que faltam "farinha" e "leite" para a receita "Torta de legumes"

  Cenário: Receita com mais de 2 ingredientes faltando não é sugerida
    Dado que a base de receitas contém a receita "Bolo de cenoura", que usa "cenoura", "ovo", "farinha", "açúcar" e "fermento"
    Quando eu pergunto "o que posso fazer com cenoura e ovo?"
    Então a resposta não sugere a receita "Bolo de cenoura"

  Cenário: Pedido só com os itens informados
    Dado que a base de receitas contém a receita "Omelete simples", que usa "ovo"
    E que a base de receitas contém a receita "Omelete de queijo", que usa "ovo" e "queijo"
    Quando eu peço receitas só com "ovo"
    Então a resposta sugere a receita "Omelete simples"
    E a resposta não sugere a receita "Omelete de queijo"

  Cenário: Ingredientes disponíveis vêm das notas recentes quando a pessoa pede
    Dado que eu tenho uma nota fiscal recente revisada com "arroz" e "feijão"
    Quando eu peço sugestões de receita analisando as minhas notas recentes
    Então o sistema mostra "arroz" e "feijão" como ingredientes disponíveis
    E eu posso tirar ou acrescentar itens antes da sugestão

  Cenário: Notas fiscais não são usadas sem pedido
    Dado que eu tenho uma nota fiscal recente revisada com "frango"
    Quando eu pergunto "o que posso fazer com ovo?"
    Então os ingredientes disponíveis são só "ovo"

  Cenário: Receita que viola uma restrição do perfil fica de fora, com aviso
    Dado que o meu perfil tem a restrição "alergia a amendoim"
    E que a base de receitas contém a receita "Frango com amendoim", que usa "frango" e "amendoim"
    Quando eu pergunto "o que posso fazer com frango?"
    Então a resposta não sugere a receita "Frango com amendoim"
    E a resposta informa que 1 receita ficou de fora pela restrição "alergia a amendoim"

  Cenário: Pessoa pede para ver as receitas ocultadas pela restrição
    Dado que uma receita com "amendoim" ficou de fora pela restrição "alergia a amendoim"
    Quando eu peço para ver as receitas ocultadas
    Então a resposta mostra a receita
    E o ingrediente "amendoim" aparece destacado como restrito

  Cenário: Ingredientes que faltam vão para a lista de compras
    Dado que a resposta sugeriu a receita "Torta de legumes" com "farinha" e "leite" faltando
    Quando eu adiciono os ingredientes que faltam à lista de compras
    Então a minha lista de compras contém "farinha" e "leite"

  # RN26 a definir: sem fonte para a busca sob demanda (ver modelo de domínio).
  @pendente
  Cenário: Sem receitas na base, o sistema busca novas e avisa quando termina
    Dado que a base de receitas não contém receitas com "jiló"
    Quando eu pergunto "o que posso fazer com jiló?"
    Então a resposta informa que o sistema vai buscar novas receitas
    E uma busca de receitas com "jiló" é iniciada
    E eu recebo uma notificação quando a busca termina

  @pendente
  Cenário: Busca de receitas sem resultado
    Dado que uma busca de receitas com "jiló" terminou sem encontrar receitas
    Então eu recebo uma notificação explicando que não foram encontradas receitas
    E a notificação pede desculpas
    E a resposta não inventa uma receita

  Cenário: Pergunta sobre conservação é respondida com a fonte
    Dado que a base de conhecimento contém um trecho sobre conservação de folhas
    Quando eu pergunto "como conservo alface para durar mais?"
    Então a resposta se baseia nesse trecho
    E a resposta cita a fonte do trecho

  Cenário: Pergunta sem informação na base de conhecimento
    Dado que a base de conhecimento não contém informações sobre "fermento biológico"
    Quando eu pergunto "quanto tempo dura o fermento biológico depois de aberto?"
    Então a resposta informa que não encontrou essa informação na base

  Cenário: Pergunta sobre preço atual não é respondida pela base de conhecimento
    Quando eu pergunto "quanto está o arroz no mercado hoje?"
    Então a resposta informa que preços atuais não vêm da base de conhecimento
