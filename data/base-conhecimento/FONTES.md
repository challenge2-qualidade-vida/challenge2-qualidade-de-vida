# Fontes da base de conhecimento

Toda fonte usada no RAG deve ser listada aqui (restrição do desafio: "Utilizar evidências confiáveis").

| Arquivo | Título | Autor / instituição | Ano | Link | Por que é confiável |
|---------|--------|---------------------|-----|------|---------------------|
| guia-alimentar-principios.md | Guia Alimentar para a População Brasileira, 2ª ed. (caps. 1, 2 e 6, resumo do grupo) | Ministério da Saúde | 2014 | <https://bvsms.saude.gov.br/bvs/publicacoes/guia_alimentar_populacao_brasileira_2ed.pdf> | Documento oficial do governo federal sobre alimentação saudável |
| guia-alimentar-grupos.md | Guia Alimentar para a População Brasileira, 2ª ed. (caps. 3 e 4, resumo do grupo) | Ministério da Saúde | 2014 | mesmo link | Idem |
| compras-e-economia.md | Critérios de compra da EconoMIA + Guia Alimentar, cap. 5 | Grupo + Ministério da Saúde | 2026 / 2014 | — | Critérios matemáticos (preço por kg) e resumo do Guia |
| aproveitamento-e-receitas.md | Aproveitamento de alimentos e receitas simples | Grupo | 2026 | — | Conteúdo do grupo, sem fonte externa; o app sinaliza isso. Receitas: **revisão do grupo pendente** |
| (gerado de data/alimentos/alimentos.json) | Tabela Brasileira de Composição de Alimentos (TACO), 4ª ed. | NEPA/Unicamp | 2011 | <https://nepa.unicamp.br/publicacoes/tabela-taco-pdf/> | Tabela oficial de composição de alimentos brasileiros |
| — (usado em metas.py) | Instrução Normativa nº 75/2020 (valores diários de referência) | ANVISA | 2020 | <https://www.in.gov.br/en/web/dou/-/instrucao-normativa-in-n-75-de-8-de-outubro-de-2020-282071143> | Norma oficial de rotulagem nutricional |
| — (usado em metas.py) | Recomendação de 400 g/dia de frutas e hortaliças | OMS | — | <https://www.who.int/news-room/fact-sheets/detail/healthy-diet> | Organização Mundial da Saúde |

## Dados usados na avaliação e na justificativa do problema

| Dado | Autor / instituição | Data | Link | Uso |
|------|---------------------|------|------|-----|
| Metodologia da cesta básica (Decreto-Lei nº 399/1938) | DIEESE | — | <https://www.dieese.org.br/metodologia/metodologiaCestaBasica.pdf> | Quantidades da cesta de referência, Região 1 |
| Custo da cesta em Brasília: R$ 773,78 | Conab/DIEESE | setembro/2026 | <https://www.dieese.org.br/analisecestabasica/2026/202609cestabasica.pdf> | Referência real e evidência do problema |
| Segurança Alimentar 2024 (PNAD Contínua) | IBGE | 2025 | <https://biblioteca.ibge.gov.br/visualizacao/livros/liv102212_informativo.pdf> | Evidência do problema |
| Pesquisa de preços em 6 supermercados | Procon Anápolis | março/2026 | <https://www.anapolis.go.gov.br/wp-content/uploads/2026/03/plan-e-rel-cesta-basica-26..pdf> | Variação entre mercados e teste de sensibilidade. Não são preços do DF |

## Imagens

- Fotos dos alimentos: Wikimedia Commons, licenças CC0, domínio público, CC BY e CC BY-SA. Autor e licença de cada uma em [docs/marca/creditos-fotos-alimentos.md](../../docs/marca/creditos-fotos-alimentos.md).
- Logo e personagens: criados pelo grupo (docs/marca/).
