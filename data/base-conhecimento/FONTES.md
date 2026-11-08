# Fontes da base de conhecimento

Toda fonte usada no RAG deve ser listada aqui (restrição do desafio: "Utilizar evidências confiáveis").

Os arquivos ficam em `data/raw/`, que o git ignora. Os comandos para baixar cada um estão na seção "Dados" do [plano da versão 1](../../specs/15-rag-receitas/plano-v1.md). As licenças foram conferidas em 08/11/2026, no próprio documento ou na página do repositório oficial.

> **Uso comercial:** todas as fontes abaixo têm restrição para uso comercial (NC) ou não declaram licença. Elas servem para a fase de treino e para o uso acadêmico. Um produto comercial vai precisar de fontes com licença compatível (ver [decisoes.md](../../docs/decisoes.md)).

## Orientação (alimentação saudável, conservação e aproveitamento)

| Arquivo | Título | Autor / instituição | Ano | Link | Licença | Por que é confiável |
| --- | --- | --- | --- | --- | --- | --- |
| `orientacao/guia_alimentar_populacao_brasileira_2ed.pdf` | Guia Alimentar para a População Brasileira, 2ª edição | Ministério da Saúde | 2014 | [BVS MS](https://bvsms.saude.gov.br/bvs/publicacoes/guia_alimentar_populacao_brasileira_2ed.pdf) | CC BY-NC-SA 4.0 ("é permitida a reprodução parcial ou total desta obra, desde que citada a fonte") | Diretriz alimentar oficial do governo federal, aprovada por consulta pública |
| `orientacao/na_cozinha_com_as_frutas_legumes_e_verduras.pdf` | Na cozinha com as frutas, legumes e verduras | Ministério da Saúde e Universidade Federal de Minas Gerais | 2016 | [Repositório UFMG](https://repositorio.ufmg.br/handle/1843/65672) | CC BY-NC-SA 4.0 (mesma nota de reprodução do Guia) | Publicação oficial do Ministério da Saúde, com ISBN 978-85-334-2356-5 |
| `orientacao/embrapa_hortalica_nao_e_so_salada_geladeira_2020.pdf` | Hortaliça não é só salada: Geladeira (2ª ed. rev.) | Milza Moreira Lana, Embrapa Hortaliças | 2020 | [Infoteca-e](https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1129028) | CC BY-NC-ND 4.0 (licença do repositório) | Folheto técnico de pesquisadora de pós-colheita da Embrapa |
| `orientacao/embrapa_hortalica_nao_e_so_salada_congelador_2020.pdf` | Hortaliça não é só salada: Congelador (2ª ed. rev.) | Milza Moreira Lana, Embrapa Hortaliças | 2020 | [Infoteca-e](https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1129067) | CC BY-NC-ND 4.0 (licença do repositório) | Folheto técnico de pesquisadora de pós-colheita da Embrapa |
| `orientacao/embrapa_recomendacoes_compras_armazenamento_consumo_2020.pdf` | Recomendações para compras, armazenamento e consumo de frutas e hortaliças | F. M. Camara, M. D. Ferreira e M. F. B. Durigan, Embrapa Instrumentação e Ceagesp | 2020 | [Infoteca-e](https://www.infoteca.cnptia.embrapa.br/infoteca/handle/doc/1122781) | CC BY-NC-ND 4.0 (licença do repositório) | Cartilha técnica da Embrapa com a Ceagesp, o maior entreposto de alimentos do país |

## Receitas

| Arquivo | Título | Autor / instituição | Ano | Link | Licença | Por que é confiável |
| --- | --- | --- | --- | --- | --- | --- |
| `receitas/afrodite.json` | afrodite.json | Adriano Ferreira (repositório no GitHub) | — | [GitHub](https://github.com/adrianosferreira/afrodite.json) | Não declarada. Os dados foram obtidos por web crawler, de site não informado | Única base pronta de receitas brasileiras em português. **Confiabilidade baixa:** origem desconhecida, sem link por receita |
| `receitas/recipenlg_0000.parquet` | RecipeNLG (amostra de 3.000 receitas, semente 42) | Poznań University of Technology | 2020 | [RecipeNLG](https://recipenlg.cs.put.poznan.pl/) · [cópia no Hugging Face](https://huggingface.co/datasets/SandhyaKilari/RecipeNLG_dataset) | Uso não comercial em pesquisa e ensino (termos do dataset original, a conferir) | Dataset acadêmico publicado na INLG 2020, com link para a página original de cada receita |

## Na base, depois da curadoria

| Grupo | Trechos |
|---|---|
| Receitas do afrodite.json (completas, sem duplicatas) | 1.004 |
| Receitas do RecipeNLG | 3.000 |
| Guia Alimentar | 167 |
| Outros textos de orientação | a contar na indexação |
