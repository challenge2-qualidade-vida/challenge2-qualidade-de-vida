# language: pt

Funcionalidade: Estrutura inicial do backend
  Como pessoa desenvolvedora
  Quero uma estrutura modular e padronizada para o backend
  Para organizar a implementação e facilitar a evolução da aplicação

  Cenário: Estrutura modular do backend disponível
    Dado que o repositório possui a estrutura inicial do backend
    Quando a pessoa desenvolvedora acessar o diretório src/economia
    Então deverá encontrar os diretórios compartilhado, api e worker
    E deverá encontrar os seis contextos de negócio organizados em camadas

  Cenário: Gerenciamento de dependências configurado
    Dado que o projeto utiliza Poetry para gerenciar suas dependências
    Quando a pessoa desenvolvedora validar a configuração do projeto
    Então o comando poetry check deverá ser executado sem erros
    E as dependências deverão estar declaradas no pyproject.toml
    E o arquivo poetry.lock deverá estar presente

  Cenário: Estrutura inicial sem funcionalidades de negócio
    Dado que a issue contempla apenas a estrutura inicial do backend
    Quando a pessoa desenvolvedora acessar os módulos criados
    Então deverá encontrar a organização inicial dos diretórios
    E não deverá pressupor que funcionalidades de negócio já estejam implementadas
