# Tópico 10 — Leitura da NFC-e (multimodalidade)

**Status:** ✅ concluído em 29/10/2026 (com nota fictícia; **falta validar com um cupom real do DF**)

## O que foi feito

O agente **Recibaldo**: a pessoa tira uma **foto do cupom fiscal**, o app lê o **QR code**, consulta a nota oficial na **SEFAZ-DF**, extrai produto, quantidade e preço e sugere a qual produto da base cada item corresponde. A pessoa **confere** e, ao confirmar, os preços entram na base com fonte `nfce` e passam a valer para todos.

É a parte **multimodal** do projeto (semana 5): a entrada é uma **imagem**.

| Arquivo | Conteúdo |
|---------|----------|
| [src/economia/nfce.py](../../src/economia/nfce.py) | QR code, validação da URL e da chave, leitura da página, associação com a base, gravação |
| [src/economia/dados.py](../../src/economia/dados.py) | `carregar()` agora junta os preços de `contribuicoes.json`, ficando com o mais recente |
| [src/economia/api.py](../../src/economia/api.py) | `POST /api/nfce/imagem`, `POST /api/nfce/url`, `POST /api/nfce/confirmar` |
| [src/web/](../../src/web/) | Aba **Enviar cupom** |
| [tests/test_nfce.py](../../tests/test_nfce.py) | 15 testes |
| [tests/fixtures/nfce_exemplo.html](../../tests/fixtures/nfce_exemplo.html) | Página de nota **fictícia** no layout padrão, usada nos testes |

## Por que o QR code, e não ler a foto (OCR)?

| | QR code + SEFAZ | OCR da foto do cupom |
|---|---|---|
| Precisão | dados **oficiais** da nota | erra com papel amassado, apagado ou fonte pequena |
| Dados | produto, quantidade, preço, data, CNPJ do mercado | o que der para ler |
| Custo | grátis (OpenCV) | grátis (Tesseract) ou API paga |
| Verificável | sim, pela chave de acesso | não |

Essa troca já estava na comparação das propostas: *"foto de cupom erra muito; é melhor ler pelo QR code, que já vem com os dados certos"*.

## Como funciona

```
foto do cupom (JPG/PNG, até 5 MB)
   │  1. OpenCV QRCodeDetector  (se falhar: amplia 2× e equaliza o contraste e tenta de novo)
   ▼
URL do QR code  ex.: https://www.fazenda.df.gov.br/nfce/qrcode?p=<chave 44 dígitos>|2|1|1|<hash>
   │  2. validar_url: só domínios *.fazenda.df.gov.br   ← proteção de segurança
   │  3. extrair_chave: 44 dígitos, modelo 65 (NFC-e), dígito verificador módulo 11
   ▼
página da nota na SEFAZ  (cada redirecionamento também é validado; página até 2 MB)
   │  4. extrair_nota: emitente, CNPJ, data e a tabela #tabResult (descrição, qtde., UN, vl. unit., total)
   ▼
itens
   │  5. associar: descobre o alimento pelas palavras ("FEIJAO CARIOCA 1KG" → feijão carioca)
   │     e a embalagem pelo tamanho ("5KG" → arroz-5kg). Vendido por KG → embalagem de 1 kg.
   ▼
tela de conferência: cada item marcado "certa" ou "revisar"; a pessoa ajusta e confirma
   │  6. salvar_contribuicao → data/precos/contribuicoes.json  (fonte "nfce", mercado = CNPJ do emitente)
   ▼
a base é recarregada e os preços novos já entram na cesta e na aba Preços
```

### Exemplo (nota fictícia dos testes)

| No cupom | Produto sugerido | Preço da embalagem | Leitura |
|----------|------------------|--------------------|---------|
| ARROZ TIPO 1 5KG | Arroz tipo 1 — 5 kg | R$ 24,90 | certa |
| FEIJAO CARIOCA 1KG (2 un.) | Feijão carioca — 1 kg | R$ 7,29 | certa |
| BANANA PRATA KG (1,235 kg) | Banana prata — 1 kg | R$ 5,49 | certa |
| SABAO EM PO 1KG | — | — | revisar (não é alimento da base) |
| ARROZ TIPO 1 2KG | — | — | revisar (a base não tem a embalagem de 2 kg) |

Quando a leitura é incerta, **o usuário decide**, como pede o documento da EconoMIA (seção 4.6).

## Segurança e privacidade

- **Proteção contra SSRF.** O servidor só baixa páginas de `fazenda.df.gov.br` e subdomínios. Um QR code malicioso apontando para `http://localhost`, `169.254.169.254` (metadados de nuvem), `file://` ou um domínio parecido (`fazenda.df.gov.br.golpe.com`) é **recusado**, e há testes para cada caso. Os redirecionamentos também passam pela validação.
- **Limites:** imagem até 5 MB, página até 2 MB, tempo máximo de 15 s, no máximo 3 redirecionamentos.
- **Dados pessoais (LGPD):** a página da nota pode ter o CPF e o nome do consumidor. O leitor **nunca lê** esses campos, e há um teste garantindo que o CPF da nota de exemplo não aparece no resultado. Só são salvos produto, preço, data e o mercado (CNPJ, que é dado de empresa).
- **O arquivo `contribuicoes.json` está no `.gitignore`**, então os preços enviados por usuários não vão para o GitHub. Nos testes, ele aponta para uma pasta temporária (`ECONOMIA_CONTRIBUICOES`).

## ⚠️ Limitação importante: o layout real da SEFAZ-DF

O leitor da página (`extrair_nota`) segue o **layout padrão da consulta pública da NFC-e**, usado por vários estados (tabela `#tabResult` com as classes `txtTit`, `Rqtd`, `RUN`, `RvlUnit` e `valor`). **Não tivemos um cupom real do DF para testar.**

Num teste manual com uma chave fictícia, o servidor acessou a SEFAZ-DF normalmente, mas, como era de se esperar, a página não trazia itens, e o app mostrou: *"Não encontrei itens na página da nota. O layout da SEFAZ pode ter mudado."*

**Próximo passo do grupo:** com um cupom real de um mercado do DF:

1. Rodar `curl "<link do QR code>" > tests/fixtures/nfce_real.html` (**apagar o CPF** do arquivo antes de salvar).
2. Abrir o HTML e conferir os nomes das classes.
3. Ajustar `extrair_nota` se for diferente e adicionar um teste com esse arquivo.

O restante do fluxo (QR code, validação, associação, conferência, gravação) não depende do layout e já está testado.

## Como usar

Pelo site: aba **Enviar cupom** → foto do cupom (no celular, abre a câmera) **ou** o link do QR code → **Ler cupom** → conferir → **Salvar preços conferidos**.

Pela API (<http://localhost:8000/docs>):

```bash
curl -F "arquivo=@cupom.jpg" localhost:8000/api/nfce/imagem
curl -X POST localhost:8000/api/nfce/url -H 'Content-Type: application/json' -d '{"url": "https://www.fazenda.df.gov.br/nfce/qrcode?p=..."}'
```

## Ferramentas (todas gratuitas)

| Ferramenta | Para quê |
|------------|----------|
| `opencv-python-headless` | Achar e decodificar o QR code na foto |
| `beautifulsoup4` | Ler o HTML da página da nota |
| `python-multipart` | Receber o upload da imagem no FastAPI |
| `qrcode` + `pillow` | Só nos testes: gerar imagens de QR code |

## Testes

```bash
pytest tests/test_nfce.py -v
```

Conferem: leitura do QR code de uma imagem gerada; erro claro para imagem sem QR code e para arquivo que não é imagem; aceita os domínios da SEFAZ-DF; **recusa** 5 endereços perigosos; extrai e valida a chave (dígito verificador errado → recusa); extrai emitente, CNPJ, data e itens; **não lê o CPF**; associa arroz 5 kg, feijão 1 kg e banana por kg, e deixa para revisar o sabão e o arroz de 2 kg; e a contribuição entra na base e é substituída por uma mais recente. Mais 4 testes na API: imagem inválida, domínio recusado, fluxo completo de ler e confirmar e produto desconhecido na confirmação.
