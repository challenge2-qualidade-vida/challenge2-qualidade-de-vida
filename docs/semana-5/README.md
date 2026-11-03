# Semana 5 — Multimodalidade

**Entregável:** agentes multimodais. ✅ Detalhes no [tópico 10](../desenvolvimento/10-nfce-multimodal.md).

O **Recibaldo** aceita a **foto do cupom fiscal**: lê o QR code com OpenCV, consulta a nota na SEFAZ-DF, relaciona os produtos à base, e a pessoa confere antes de salvar.

**Por que QR code e não OCR:** a nota oficial traz os dados corretos, sem erro de leitura. **Segurança e LGPD:** só acessa domínios `*.fazenda.df.gov.br`, e o CPF não é lido.

**Pendente:** testar com um cupom real do DF. Os testes usam uma nota fictícia, e o layout real pode exigir ajustes.
