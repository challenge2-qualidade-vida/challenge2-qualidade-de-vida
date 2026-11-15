# language: pt

Funcionalidade: Containerização da API e do banco de dados
  Como pessoa desenvolvedora
  Quero iniciar a API e o PostgreSQL pelo Docker Compose
  Para executar o backend em um ambiente padronizado

  Cenário: Construção da imagem da API
    Dado que o projeto possui um Dockerfile configurado
    Quando a imagem da API for construída
    Então a construção deverá terminar sem erros

  Cenário: Inicialização da API e do PostgreSQL
    Dado que o Docker Compose está configurado
    Quando a pessoa desenvolvedora executar docker compose up
    Então a API deverá ser iniciada
    E o PostgreSQL deverá estar disponível
    E o PostgreSQL deverá estar acessível pela rede interna do Docker

  Cenário: Persistência dos dados do PostgreSQL
    Dado que o PostgreSQL está em execução
    Quando o contêiner do banco for recriado
    Então os dados armazenados no volume persistente deverão ser preservados

  Cenário: Preservação do Qdrant
    Dado que o Docker Compose possui o serviço Qdrant
    Quando a configuração for ampliada para incluir a API e o PostgreSQL
    Então o Qdrant deverá continuar disponível
    E seu volume de dados deverá ser preservado
