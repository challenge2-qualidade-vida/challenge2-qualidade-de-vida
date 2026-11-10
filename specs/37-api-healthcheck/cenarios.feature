# language: pt

Funcionalidade: Healthcheck da API
  Como pessoa desenvolvedora ou serviço consumidor
  Quero verificar se a API está funcionando
  Para identificar se a aplicação está disponível

  Cenário: API responde ao healthcheck
    Dado que a aplicação FastAPI está inicializada
    Quando uma requisição GET for enviada para /health
    Então a resposta deverá possuir status HTTP 200
    E o corpo deverá conter o JSON {"status": "ok"}
