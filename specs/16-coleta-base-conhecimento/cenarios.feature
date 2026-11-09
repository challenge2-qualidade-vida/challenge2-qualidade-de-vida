# language: pt
Funcionalidade: Coleta de documentos da base de conhecimento
  Cenário: Fonte catalogada com metadados e licença
    Dado que um documento foi selecionado para a base
    Quando a fonte é registrada em FONTES.md
    Então o registro contém título, instituição, ano, link e motivo da confiabilidade
    E contém a situação de licença ou permissão de uso

  Cenário: Documento sem licença esclarecida não é redistribuído
    Dado que a licença do documento não está esclarecida
    Quando a equipe prepara a base
    Então o documento fica pendente de validação
    E não é copiado para a base distribuída no repositório
