# Spec: envio de imagens e PDFs no frontend

| Campo | Valor |
| --- | --- |
| Issue | #95 (Refs #80) |
| Status | Em revisão |
| Contexto delimitado | Leitura de documentos |
| Agente | Recibaldo |

## Problema

A entrega da semana 5 pede um **assistente multimodal**, com pelo menos duas modalidades e uma demonstração do fluxo. A API vai receber uma pergunta junto com uma imagem ou um PDF de nota fiscal (#92, Isabel), mas falta onde a pessoa envia o arquivo, acompanha o processamento e lê a resposta.

## Comportamento esperado

Uma tela **Documento** no frontend da `develop_gui`, com o Recibaldo:

1. A pessoa escolhe uma **imagem** (JPEG, PNG ou WebP) ou um **PDF** e escreve uma **pergunta** sobre ele (ex.: "Quanto gastei com hortifrúti?").
2. Antes de enviar, a tela confere o que dá para conferir no aparelho e mostra o aviso sem chamar a API:
   - pergunta vazia;
   - nenhum arquivo;
   - formato que não é imagem nem PDF;
   - arquivo vazio;
   - arquivo maior que 10 MB.
3. Ao enviar, a tela mostra o **estado do processamento**: enviando, recebido, validado, encaminhado ao extrator ou extração concluída. A tela não diz que a extração terminou enquanto a API não devolver o resultado.
4. Com a extração concluída, a tela mostra:
   - a **resposta** do assistente à pergunta;
   - os **itens extraídos**, com descrição, quantidade e valor. Os itens marcados para revisão aparecem destacados com "conferir" (RN09).
5. Erros da API aparecem como Problem Details, com a mensagem da API: 400, 413, 415, 422 e 500.

A tela fica atrás da flag **`documentos`**, fora de `VITE_FUNCIONALIDADES=todas`, pelo mesmo motivo da tela Verificar: a comparação visual com o site antigo usa `todas`. Para a demo: `npm run dev:demo`.

A tela **Cupom** continua como está: ela lê o QR code da NFC-e para registrar preços, um fluxo diferente deste.

## Termos do domínio

Do [modelo de domínio](../../docs/arquitetura/modelo-de-dominio.md): nota fiscal (`NotaFiscal`), item extraído (`ItemExtraido`), revisão (`Revisao`) e Recibaldo. Na tela, "documento" é o arquivo enviado: imagem ou PDF de uma nota fiscal.

## Regras de negócio

- **RN01:** a tela não calcula nada. Valores (em centavos), confiança e a marcação de revisão vêm da API, e a tela só formata com `reais()`.
- **RN09:** item com confiança abaixo de 0,85 passa por revisão. Quem decide é a API, pelo campo `revisar`, e a tela só destaca.
- **RN15:** a tela não guarda o arquivo nem a resposta no aparelho. Nada vai para o `localStorage`.
- Limite de **10 MB** por arquivo, igual ao da #92. A checagem na tela só evita um envio que seria recusado; a API continua validando tudo.

## Entradas e saídas

Contrato **provisório** em `frontend/openapi/provisorio.yaml`. A #92 ainda não fixou a rota nem os nomes dos campos, então esta proposta precisa ser **alinhada com a Isabel**:

`POST /documentos`, `multipart/form-data`, com os campos `pergunta` (texto) e `arquivo` (imagem ou PDF), devolve `ResultadoDoDocumento`:

```json
{
  "documento_id": "doc-123",
  "tipo": "imagem",
  "etapa": "extraido",
  "resposta": "Você gastou R$ 32,47 com hortifrúti nesta nota.",
  "itens": [
    { "descricao": "BANANA PRATA KG", "quantidade": 1.2, "unidade": "KG", "valor_total": 659, "confianca": 0.78, "revisar": true }
  ]
}
```

- `tipo`: `imagem` ou `pdf`.
- `etapa`: `recebido`, `validado`, `encaminhado` ou `extraido`.
- `resposta` e `itens` vêm `null` até a etapa `extraido`.
- `valor_total` vem em centavos.

Com `VITE_DADOS_FALSOS=1`, os dados falsos devolvem uma nota fictícia já extraída, com um item para revisão, e simulam os erros 413 e 415.

## Fora do escopo

- A rota de verdade, a validação no servidor, o OCR e a leitura de PDF (#92, #93 e #94, Isabel).
- Salvar a revisão dos itens: isso continua na tela Cupom.
- Áudio e vídeo.
- Guardar o histórico de documentos enviados.

## Critérios de aceitação

Cenários em [cenarios.feature](cenarios.feature), cobertos pelos testes do Vitest em `frontend/src/testes/documentos.teste.ts`.

## Dependências

- **#92:** a rota, o formato da resposta e os códigos de erro. Até ela existir, a tela usa os dados falsos.
- **#93 e #94:** o conteúdo dos itens extraídos de imagens e de PDFs.

## Riscos e limitações

- O contrato é uma proposta. Se a #92 escolher outros nomes, muda o `provisorio.yaml` e a tela se ajusta.
- Se a API responder antes da extração terminar (etapa `encaminhado`), esta versão mostra a etapa e não consulta de novo. A consulta do resultado depois fica para quando a #92 definir como o resultado chega.
