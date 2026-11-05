# language: pt
Funcionalidade: Frontend da EconoMIA em React com o visual atual
  Como pessoa que planeja as compras do mês
  Quero usar o mesmo site aprovado pelo grupo
  Para montar a cesta, conversar com a Mia e enviar cupons, agora integrado ao backend do grupo

  Esquema do Cenário: Tela idêntica ao site antigo
    Dado o site antigo e o site novo com os mesmos dados
    E todas as funcionalidades ligadas
    Quando eu abro a tela "<tela>" com <largura> px de largura
    Então a captura do site novo é igual à do site antigo, com diferença mínima

    Exemplos:
      | tela          | largura |
      | Início        | 390     |
      | Início        | 768     |
      | Início        | 1440    |
      | Cesta         | 390     |
      | Cesta         | 1440    |
      | Mia           | 1440    |
      | Cupom         | 1440    |
      | Perto de mim  | 1440    |
      | Configurações | 1440    |

  Cenário: Funcionalidades fora do MVP ficam desligadas por padrão
    Dado o site novo sem a variável de funcionalidades
    Quando eu abro o Início
    Então o atalho "Essa promoção vale?" não aparece
    E nenhuma rota fora do contrato é chamada

  Cenário: Erro da API em Problem Details
    Dado que a API responde com "application/problem+json" e o título "Orçamento inválido"
    Quando eu monto a cesta
    Então a tela mostra "Não foi possível montar a cesta: Orçamento inválido"

  Cenário: Sessão expirada é renovada sem a pessoa perceber
    Dado que o token de acesso venceu
    Quando o site chama a API e recebe 401
    Então ele pede um novo token em "/api/v1/auth/renovar" e repete a chamada

  Cenário: Resposta da Mia chega aos poucos
    Dado que a conversa responde por SSE
    Quando eu envio uma pergunta
    Então o texto da resposta aparece antes de o evento "fim" chegar
