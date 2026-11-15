# Pipeline de ingestão e preparação

## Fluxo
```mermaid
flowchart TD
 A[Documentos licenciados] --> B[Manifesto fontes.json]
 A --> C[Extratores PDF/TXT/Markdown]
 B --> D[Validação de metadados]
 C --> E[Normalização]
 D --> F[JSONL com origem]
 E --> F
 F --> G[Hash e relatório]
 G --> H[Chunking e embeddings]
```

## Execução
```bash
poetry install
poetry run python -m economia.leitura_documentos.infraestrutura.ingestao.pipeline
```

Saídas: `data/processed/documentos.jsonl` e `data/processed/relatorio_ingestao.json`.

PDFs digitalizados sem camada de texto são reportados; OCR não está incluído. DOCX e HTML também não são suportados nesta primeira versão.
