# language: pt
Funcionalidade: Envio de imagens e PDFs no frontend
  Como pessoa que fez compras no mercado
  Quero enviar a foto ou o PDF da nota fiscal com uma pergunta
  Para entender o que comprei sem digitar os itens

  Cenário: Enviar uma imagem com pergunta
    Dado uma imagem "nota.jpg" de 2 MB
    E a pergunta "Quanto gastei com hortifrúti?"
    Quando eu envio o documento
    Então a API recebe a pergunta e o arquivo no mesmo envio
    E vejo a resposta do assistente
    E vejo os itens extraídos com os valores em reais

  Cenário: Enviar um PDF com pergunta
    Dado um PDF "nota.pdf" de 1 MB
    E a pergunta "Qual foi o item mais caro?"
    Quando eu envio o documento
    Então vejo a resposta do assistente

  Cenário: Item com confiança baixa aparece para conferir
    Dado uma resposta com um item marcado para revisão
    Quando a tela mostra os itens extraídos
    Então o item aparece destacado com "conferir"

  Cenário: Estado do processamento
    Dado uma resposta na etapa "encaminhado"
    Quando a tela mostra o resultado
    Então vejo que o documento foi encaminhado para leitura
    E a tela não diz que a extração foi concluída

  Esquema do Cenário: Erros conferidos antes do envio
    Dado <situacao>
    Quando eu envio o documento
    Então aparece o aviso "<aviso>"
    E a API não é chamada

    Exemplos:
      | situacao                             | aviso                                   |
      | a pergunta vazia                     | Escreva uma pergunta sobre o documento. |
      | nenhum arquivo escolhido             | Escolha uma imagem ou um PDF.           |
      | um arquivo "planilha.xlsx"           | Envie uma imagem (JPEG, PNG ou WebP) ou um PDF. |
      | um arquivo vazio                     | O arquivo está vazio.                   |
      | uma imagem de 11 MB                  | O arquivo pode ter até 10 MB.           |

  Cenário: Erro da API
    Dado que a API responde 415 com a mensagem "Formato não suportado"
    Quando eu envio o documento
    Então aparece a mensagem "Formato não suportado"

  Cenário: Tela desligada por padrão
    Dado o site sem a flag "documentos"
    Quando eu abro o site
    Então a aba Documento não aparece
