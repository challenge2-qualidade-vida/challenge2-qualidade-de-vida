# language: pt
Funcionalidade: Observabilidade das perguntas ao Miau-ricio no Langfuse
  Como pessoa que mantém o EconoMIA
  Quero ver no Langfuse cada pergunta real, por pessoa e por conversa, com a qualidade medida
  Para entender respostas ruins e ser avisada quando a qualidade ou a latência piorarem

  Cenário: Pergunta pela API vira um registro com a busca e a chamada ao LLM
    Dado que as chaves do Langfuse estão configuradas
    Quando a API recebe a pergunta "como conservo alface?"
    Então o Langfuse recebe um registro "miau-ricio.pergunta"
    E o registro tem uma busca com os trechos e os scores
    E o registro tem uma chamada ao LLM com o modelo, os tokens e a latência

  Cenário: Registro ligado à pessoa e à conversa
    Dado um identificador anônimo e um identificador de conversa válidos
    Quando a API recebe uma pergunta com os dois cabeçalhos
    Então o registro tem o identificador anônimo como pessoa
    E o registro tem o identificador da conversa como sessão

  Cenário: Identificador fora do formato é ignorado
    Quando a API recebe uma pergunta com o cabeçalho X-Identificador-Anonimo "maria@exemplo.com"
    Então o registro não tem pessoa
    E a resposta é a mesma de uma pergunta sem o cabeçalho

  Esquema do Cenário: Dados pessoais são mascarados antes do envio
    Quando a API recebe a pergunta "<pergunta>"
    Então a entrada registrada é "<registrada>"

    Exemplos:
      | pergunta                                          | registrada                                  |
      | meu e-mail é maria@exemplo.com, que receita faço? | meu e-mail é [EMAIL], que receita faço?     |
      | meu CPF é 123.456.789-09                          | meu CPF é [CPF]                             |
      | me liga no (61) 98765-4321                        | me liga no [TELEFONE]                       |

  Cenário: Falha no mascaramento não envia o conteúdo
    Dado uma função de mascaramento que falha
    Quando a API recebe a pergunta "sou maria@exemplo.com"
    Então a entrada registrada é "[MASCARAMENTO_FALHOU]"
    E a API responde normalmente

  Cenário: Scores do código entram no registro
    Dado que a base de conhecimento tem um trecho sobre conservação de folhas
    Quando a API recebe a pergunta "como conservo alface?"
    Então o registro tem o score "encontrou" igual a verdadeiro
    E o registro tem o score "fonte_citada" igual a verdadeiro
    E o registro tem o score "latencia_s"

  Cenário: Erro na resposta fica registrado
    Dado que o Ollama está fora do ar
    Quando a API recebe uma pergunta
    Então a API responde 503
    E o registro tem nível de erro
    E o registro tem o score "erro" igual a verdadeiro

  Cenário: Sem as chaves do Langfuse, a API responde e nada é enviado
    Dado que as chaves do Langfuse não estão configuradas
    Quando a API recebe uma pergunta
    Então a API responde normalmente
    E nenhum registro é enviado

  Cenário: Falha do Langfuse não muda a resposta
    Dado um cliente do Langfuse que falha ao enviar
    Quando a API recebe uma pergunta
    Então a resposta é a mesma de uma pergunta sem registro

  Cenário: Sincronizar os prompts publica cada arquivo com a versão
    Dado o arquivo de prompt "miau-ricio/resposta_com_fontes_v2.md"
    Quando eu sincronizo os prompts
    Então o Langfuse tem o prompt "miau-ricio/resposta_com_fontes" com o rótulo "v2"
    E o prompt em uso pela configuração tem o rótulo "production"

  Cenário: Sincronizar de novo sem mudança não cria versão
    Dado que os prompts já foram sincronizados
    Quando eu sincronizo os prompts de novo
    Então nenhuma versão nova é criada no Langfuse

  Cenário: Sem o Langfuse, o prompt vem do arquivo
    Dado que o Langfuse não responde
    Quando o Miau-ricio carrega o prompt de resposta
    Então o texto é o do arquivo local

  Cenário: Chamada ao LLM fica ligada à versão do prompt
    Dado que o prompt de resposta foi lido do Langfuse
    Quando a API recebe uma pergunta
    Então a chamada ao LLM registrada está ligada ao prompt "miau-ricio/resposta_com_fontes" e à versão usada
