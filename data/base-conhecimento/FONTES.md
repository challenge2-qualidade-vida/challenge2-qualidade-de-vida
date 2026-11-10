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

## Base ampliada para 20 fontes (#16)

Os 13 documentos abaixo vêm do catálogo montado pela Isabel na branch `chore/16-base-conhecimento`, com a licença conferida no próprio documento ou na página editorial. Foram escolhidos pelo impacto nas perguntas do Miau-ricio. A análise de cada documento do catálogo, incluindo os que ficaram de fora, está em [docs/semana-2/avaliacao-rag.md](../../docs/semana-2/avaliacao-rag.md). Os comandos para baixar estão na seção "Dados" do [plano da versão 1](../../specs/15-rag-receitas/plano-v1.md).

| Arquivo | Título | Autor / instituição | Ano | Link | Licença | Por que é confiável |
| --- | --- | --- | --- | --- | --- | --- |
| `orientacao/ms_guia_alimentar_criancas_menores_2_anos_2019.pdf` | Guia Alimentar para Crianças Brasileiras Menores de 2 Anos | Ministério da Saúde | 2019 | [PDF](http://189.28.128.100/dab/docs/portaldab/publicacoes/guia_da_crianca_2019.pdf) | CC BY-NC-SA 4.0 | Diretriz oficial do governo federal para a alimentação de crianças pequenas |
| `orientacao/ms_protocolo_guia_alimentar_adultos_fasciculo1_2021.pdf` | Protocolos de Uso do Guia Alimentar na Orientação Alimentar, Fascículo 1 (adultos) | Ministério da Saúde e USP | 2021 | [BVS MS](https://bvsms.saude.gov.br/bvs/publicacoes/protocolos_guia_alimentar_fasciculo1.pdf) | CC BY-NC-SA 4.0 | Material técnico oficial que traduz o Guia em orientações práticas |
| `orientacao/opas_laboratorio_inovacao_flv_2022.pdf` | Laboratório de Inovação: frutas, legumes e verduras | OPAS, Ministério da Saúde, INCA, FAO e WFP | 2022 | [INCA](https://ninho.inca.gov.br/jspui/bitstream/123456789/13758/1/9789275725146_por.pdf) | CC BY-NC-SA 3.0 IGO | Publicação interinstitucional com experiências de acesso, consumo e redução de perdas |
| `orientacao/bjft_percepcao_consumidor_riscos_rastreabilidade_2013.pdf` | Percepção do consumidor frente aos riscos associados aos alimentos, sua segurança e rastreabilidade | Brazilian Journal of Food Technology (ITAL) | 2013 | [SciELO](https://www.scielo.br/j/bjft/a/G6NXXPM79sRRX78HKm6xb8t/) | CC BY 4.0 | Artigo científico revisado por pares |
| `orientacao/raca_ultraprocessados_riscos_2022.pdf` | Alimentos ultraprocessados e seus riscos à cultura alimentar e à saúde | RACA, Fiocruz | 2022 | [RACA](https://raca.fiocruz.br/index.php/raca/article/view/145) | CC BY 4.0 | Ensaio em revista científica da Fiocruz (o catálogo dizia 2023; o PDF é de ago./dez. 2022) |
| `orientacao/raca_consumo_alimentar_pandemia_2024.pdf` | O que envolve o consumo alimentar e como a pandemia por Covid-19 pode ter influenciado | RACA, Fiocruz | 2024 | [RACA](https://raca.fiocruz.br/index.php/raca/article/view/182) | CC BY 4.0 | Ensaio em revista científica da Fiocruz |
| `orientacao/raca_comensalidade_pandemia_2024.pdf` | Impactos da pandemia de Covid-19 na alimentação e comensalidade | RACA, Fiocruz | 2024 | [RACA](https://raca.fiocruz.br/index.php/raca/article/view/192) | CC BY 4.0 | Artigo científico com entrevistas |
| `orientacao/raca_ambiente_escolar_praticas_alimentares_2023.pdf` | Ambiente escolar e práticas alimentares familiares e escolares | RACA, Fiocruz | 2023 | [RACA](https://raca.fiocruz.br/index.php/raca/article/view/154) | CC BY 4.0 | Artigo científico |
| `orientacao/ifc_food_safety_handbook_2020.pdf` | Food Safety Handbook (só o capítulo 3, p. 72 a 225) | International Finance Corporation (IFC), Grupo Banco Mundial | 2020 | [IFC](https://www.ifc.org/content/dam/ifc/doc/2020/food-safety-handbook-2020-edition-ifc-2023.pdf) | CC BY 3.0 IGO | Manual técnico internacional de segurança dos alimentos (APPCC, perigos, temperaturas) |
| `orientacao/bjft_diagnostico_higiene_servicos_alimentacao_2012.pdf` | Diagnóstico das condições higiênicas de serviços de alimentação de acordo com a NBR 15635:2008 | Brazilian Journal of Food Technology (ITAL) | 2012 | [SciELO](https://www.scielo.br/j/bjft/a/db7TDPqpcFvZdcWFH3YTwJG/) | CC BY 4.0 | Artigo científico revisado por pares |
| `orientacao/raca_praticas_higiene_servicos_alimentacao_2019.pdf` | Redefinindo para melhor refletir: práticas de higiene em serviços de alimentação | RACA, Fiocruz | 2019 | [RACA](https://raca.fiocruz.br/index.php/raca/article/view/5) | CC BY 4.0 | Artigo em revista científica da Fiocruz |
| `orientacao/taco_4_edicao_2011.pdf` | Tabela Brasileira de Composição de Alimentos (TACO), 4ª edição revisada e ampliada | NEPA, Unicamp | 2011 | [NEPA](https://nepa.unicamp.br/wp-content/uploads/sites/27/2023/10/taco_4_edicao_ampliada_e_revisada.pdf) | Reprodução total ou parcial permitida, desde que citada a fonte | Tabela de referência nacional, com análises de laboratório |
| `orientacao/cadsc_campanha_reducao_desperdicio_2022.pdf` | Efetividade de uma campanha para redução de desperdício em uma unidade de alimentação e nutrição | Cadernos Saúde Coletiva (UFRJ) | 2022 | [SciELO](https://www.scielo.br/j/cadsc/a/yGYP7nfb9NKybvFDqfxdsJS/) | CC BY 4.0 | Artigo científico revisado por pares |

## Na base, depois da curadoria

20 documentos-fonte, 6.151 trechos na coleção `base_conhecimento_e5` (indexação de 10/11/2026).

| Grupo | Trechos |
|---|---|
| Receitas do afrodite.json (completas, sem duplicatas) | 1.004 |
| Receitas do RecipeNLG | 3.000 |
| Guia Alimentar para Crianças Menores de 2 Anos | 453 |
| TACO | 430 |
| Food Safety Handbook (IFC, capítulo 3) | 411 |
| Guia Alimentar para a População Brasileira | 167 |
| Na cozinha com as frutas, legumes e verduras | 137 |
| Laboratório de Inovação FLV (OPAS) | 130 |
| Protocolo do Guia Alimentar para adultos | 67 |
| Os 8 artigos (5 da RACA, 2 do BJFT e 1 dos Cadernos Saúde Coletiva) | 314 |
| Folhetos e cartilha da Embrapa | 38 |
