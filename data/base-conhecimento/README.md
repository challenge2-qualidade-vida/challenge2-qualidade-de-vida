# Base de conhecimento

Diretório destinado aos documentos-fonte utilizados pelo EconoMIA
no mecanismo de Retrieval-Augmented Generation (RAG).

## Organização

- `FONTES.md`: catálogo de fontes, instituições, links e condições de uso.
- `fontes.json`: manifesto de metadados utilizado pelo pipeline de ingestão.
- `orientacao-alimentar/`: guias e documentos sobre alimentação e nutrição.
- `conservacao/`: documentos sobre conservação e segurança dos alimentos.
- `receitas/`: materiais de receitas e aproveitamento culinário.
- `composicao-nutricional/`: materiais de composição nutricional.
- `desperdicio/`: materiais sobre desperdício e aproveitamento de alimentos.
- `evidencias-licencas/`: registros das licenças e permissões verificadas.

As pastas de conteúdo são utilizadas conforme a incorporação dos
documentos à base.

## Critérios de inclusão

Antes de incorporar um documento:

1. Identificar a instituição ou autoria responsável.
2. Registrar título, ano, tipo de conteúdo e URL de origem.
3. Conferir a licença ou autorização de reprodução.
4. Verificar eventuais restrições para materiais de terceiros.
5. Registrar a evidência da licença.
6. Preencher o caminho relativo do arquivo no `fontes.json`.

URL pública não equivale a autorização de redistribuição.

Quando a licença não estiver clara, o documento deve permanecer
fora da ingestão até a conclusão da verificação.

## Formatos suportados

- PDF com camada de texto;
- TXT;
- Markdown.

PDFs digitalizados sem camada textual podem exigir OCR.
O OCR não faz parte da implementação inicial do pipeline.

## Manifesto e ingestão

O arquivo `fontes.json` relaciona cada documento aos seguintes metadados:

- `arquivo`;
- `titulo`;
- `instituicao`;
- `ano`;
- `tipo_conteudo`;
- `url`.

O caminho registrado em `arquivo` deve ser relativo a
`data/base-conhecimento/` e corresponder a um arquivo existente.

Somente documentos com metadados válidos são processados pelo pipeline.

## Saídas

Os textos extraídos e normalizados são gravados em:

- `data/processed/documentos.jsonl`;
- `data/processed/relatorio_ingestao.json`.

Os arquivos gerados são resultados intermediários e permanecem
fora do versionamento conforme as regras do `.gitignore`.