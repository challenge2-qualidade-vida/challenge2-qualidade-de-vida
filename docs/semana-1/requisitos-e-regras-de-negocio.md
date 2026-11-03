# Requisitos, regras de negócio e pontos em aberto do Relatório 1

> Documento da Semana 1. Fonte analisada: **Relatório Técnico-Estratégico do EconoMIA**, de 29/10/2026 (arquivo `Relatório 1 (29-10).pdf`, 14 páginas). Ele foi cruzado com a [análise de viabilidade v2](analise-viabilidade-e-justificativa-v2.md) para apontar contradições.
>
> As citações são literais e trazem a página do PDF (ex.: *p. 10*). A única mudança foi trocar as fórmulas em LaTeX que a exportação quebrou (ex.: `$R\$/kg$`) pelo texto que elas representam (R$/kg). Essas trocas estão marcadas com *[fórmula reescrita]*.

---

## 0. Como ler

O documento tem três camadas:

1. **O que está explícito** (seções 1 a 3): requisitos e regras que o relatório declara.
2. **O que está implícito** (seção 4): funcionalidades e dados que o relatório pressupõe, mas não declara como requisito.
3. **O que precisa de decisão** (seções 5 e 6): uma ficha por problema, com o trecho, o problema e a pergunta a responder. O campo **Decisão** fica em branco para a equipe preencher.

Tipos de achado usados nas fichas:

| Tipo | Significado |
| --- | --- |
| **Contradição** | Dois trechos dizem coisas incompatíveis |
| **Ausência** | O texto depende de algo que não está definido em nenhum lugar |
| **Ambiguidade** | O trecho admite mais de uma leitura |
| **Métrica não mensurável** | A meta existe, mas falta linha de base, método ou prazo viável |
| **Risco LGPD** | Tratamento de dado pessoal ou sensível sem regra clara |
| **Escopo** | O compromisso parece grande demais para 7 semanas e 5 pessoas |
| **Fonte frágil** | Referência incompleta, sem link ou com dado duvidoso |

---

## 1. Requisitos funcionais explícitos

O relatório numera **quatro** RFs, todos na p. 10.

| ID | Requisito | Trecho (p. 10) |
| --- | --- | --- |
| **RF-01** | Ingestão visual de cupons fiscais e encartes | "um módulo de ingestão visual (RF-01) capaz de extrair automaticamente nomes de produtos, quantidades, valores e descontos a partir de imagens de cupons fiscais (NFC-e/SAT) e encartes promocionais por meio de visão computacional e OCR." |
| **RF-02** | Normalização de preços por unidade de medida | "o motor de dados realiza a normalização de preços (RF-02), calculando de forma padronizada o custo real por unidade de medida (R$/kg, R$/L ou valor unitário) para viabilizar comparações objetivas entre marcas e embalagens de tamanhos variados." *[fórmula reescrita]* |
| **RF-03** | Receitas a partir do estoque doméstico, via RAG | "a solução integra recomendações baseadas no armazenamento doméstico (RF-03), utilizando a arquitetura RAG para sugerir receitas culinárias estruturadas a partir dos insumos já disponíveis na despensa do usuário." |
| **RF-04** | Ajuste automático ao orçamento | "o sistema oferece um mecanismo de ajuste orçamentário automático (RF-04), reorganizando a lista de compras e priorizando itens essenciais sempre que a estimativa total ultrapassar o limite financeiro estipulado pela família." |

## 2. Requisitos não funcionais explícitos

| ID | Requisito | Trecho |
| --- | --- | --- |
| **RNF-01** | Explicabilidade e verificabilidade: cálculos 100% determinísticos | "o sistema adota como pilar a explicabilidade e a verificabilidade (RNF-01), na qual 100% das operações aritméticas e comparações financeiras são executadas por algoritmos determinísticos verificáveis, impedindo qualquer alucinação numérica decorrente de modelos generativos de linguagem." (p. 10) |
| **RNF-02** | Desempenho: até 2,5 s | "o tempo de resposta para requisições conversacionais e buscas por similaridade no repositório vetorial (RAG) não deve exceder o teto de 2,5 segundos no percentil T90." (p. 10) |
| **RNF-03** | Privacidade e LGPD: anonimização | "todos os dados de identificação pessoal e chaves de acesso presentes nos cupons fiscais são submetidos a uma camada de anonimização estrita antes da persistência no banco de dados." (p. 10) |
| **RNF-04** | Acessibilidade: WCAG 2.1 AA e voz | "a camada de apresentação assegura altos padrões de acessibilidade (RNF-04), seguindo rigorosamente as diretrizes da WCAG 2.1 no nível AA para disponibilizar navegação simplificada, compatibilidade com leitores de tela e suporte nativo a interações por comandos de voz." (p. 10–11) |

## 3. Regras de negócio explícitas

O relatório não numera regras de negócio. As regras abaixo foram extraídas do texto e receberam números aqui.

| ID | Regra | Trecho |
| --- | --- | --- |
| **RN-01** | Todo item tem um de três níveis de prioridade | "Classificação dos itens em três níveis de prioridade: Essenciais (proteínas básicas, grãos,itens de higiene primária), Secundários (hortifrúti variado, laticínios complementares) e Superfluos/Opcionais (sobremesas, bebidas)." (p. 4–5) |
| **RN-02** | O ajuste é acionado quando o custo total passa do orçamento | "Caso o custo total supere o orçamento informado (C_total > O_disponível), o sistema sugere dinamicamente:" (p. 5) *[fórmula reescrita]* |
| **RN-03** | Três ações de ajuste, nesta ordem | "1. Redução de volumes dos itens de menor prioridade. 2. Substituição por marcas equivalentes registradas com menor valor. 3. Remoção temporária de itens opcionais." (p. 5) |
| **RN-04** | Custo por unidade = preço ÷ massa ou volume líquido | "Custo Real por Unidade = Preço do Pacote / Massa ou Volume Líquido" (p. 5) *[fórmula reescrita]* |
| **RN-05** | O deslocamento entra no custo final da compra | "O custo logístico incorpora o valor estimado do deslocamento (distância vs. consumo do veículo ou tarifa de transporte) no custo final da compra, indicando se a troca de estabelecimento compensa a variação do valor dos produtos." (p. 5) |
| **RN-06** | O LLM não faz contas | "A IA generativa não executa cálculos matemáticos diretamente; a inteligência generativa é reservada para interpretação de texto, estruturação de intenções,sumarização e interação conversacional. Operações aritméticas e comparações financeiras são delegadas a motores determinísticos verificáveis." (p. 6) |
| **RN-07** | Toda sugestão mostra seus critérios (XAI) | "Cada sugestão é acompanhada pelos critérios técnicos e matemáticos que a fundamentaram" (p. 3) |
| **RN-08** | O sistema não decide pelo usuário nem garante o menor preço | "O sistema não toma decisões automáticas e nem garante o menor custo financeiro absoluto sob qualquer premissa, uma vez que preferências pessoais (marcas de preferência, restrições alérgicas,proximidade do estabelecimento) possuem pesos subjetivos que pertencem ao usuário." (p. 4) |
| **RN-09** | Receitas priorizam o que já está em casa | "Dadas as opções de ingredientes na residência, o algoritmo prioriza receitas que não exijam a compra de novos insumos." (p. 6) e "Sugere pratos que priorizam os insumos com data de vencimento próxima" (p. 4) |
| **RN-10** | Leitura com baixa confiança exige validação do usuário | "o sistema adota um mecanismo de checagem com validação do usuário para leituras com índice de confiança inferior a 85%." (p. 11) |
| **RN-11** | Todo preço mostra data e fonte | "a plataforma aplica uma rotulagem transparente indicando a data e a fonte da última atualização do preço." (p. 11) |
| **RN-12** | Dados pessoais são anonimizados antes de salvar | Mesmo trecho do RNF-03 (p. 10) |
| **RN-13** | A base de conhecimento do RAG tem quatro fontes | "Tabela Nutricional e Guia Alimentar para a População Brasileira; Acervo de receitas estruturadas [...]; Manuais de conservação e armazenamento de perecíveis; Regras de equivalência de unidades de medida" (p. 7) |

---

## 4. Requisitos implícitos (candidatos a RF/RNF)

### 4.1 Funcionalidades citadas sem número nem critério de aceite

| Funcionalidade | Trecho | O que falta |
| --- | --- | --- |
| Comparação de preços entre lojas | "adiciona-se comparação de preços multidirecional, onde a comparação não se limita ao preço nominal" (p. 5) | Virar RF. Hoje só o RF-02 (normalização) está numerado; a comparação em si não está |
| Rotulagem de confiabilidade dos dados | "Rotulagem de Confiabilidade dos Dados" (p. 5) | Só o título. Ver ficha A22 |
| Detecção de anomalias de preço | "Detecção de Anomalias de Preço" (p. 5) | Só o título. Ver ficha A22 |
| Garantias de transparência | "Garantias de Transparência" (p. 5) | Só o título. Ver ficha A22 |
| Lista de compras dinâmica | "Oferta de Lista de Compras Inteligente e Dinâmica" (p. 5) | O que a torna "inteligente"? De onde vêm os itens? |
| Gestão gastronômica e motor de receitas | "Gestão Gastronômica e Aproveitamento Integral" e "Motor de Receitas Conectado" (p. 5) | Parece igual ao RF-03. Fundir ou separar? |
| Assistente conversacional multimodal (texto e voz) | "Interface em linguagem natural capaz de interagir por texto e voz, interpretando comandos complexos, mantendo o contexto da sessão" (p. 6) | Não é RF. A voz só aparece no RNF-04. Ver ficha A14 |
| NLU e roteamento de tarefas | "extrair entidades (produtos, valores, restrições) da mensagem do usuário [...] o encaminhamento de tarefas identifica a necessidade da solicitação e acionamento de ferramentas certas" (p. 6) | Requisito de arquitetura sem critério de aceite |
| Salvaguardas contra alucinação | "Consideram-se também as salvaguardas e limitações, como checagens de alucinação e bloqueios da LLM." (p. 6) | Quais checagens? O que é bloqueado? |
| Mapeamento de ambiguidades na leitura | "mapeamento de ambiguidades e aplicação de limites de confiança (Confidence Thresholds)" (p. 6) | O limite aparece como 85% na p. 11 (RN-10), mas o "mapeamento" não está definido |

### 4.2 Dados e cadastros que o texto pressupõe, sem requisito

| Pressuposto | Onde aparece | Requisito que falta |
| --- | --- | --- |
| **Perfil do usuário** (orçamento, preferências, restrições alérgicas, marcas, local) | "coleta e consolida dados de orçamento, preferências alimentares, restrições e preços" (p. 3); "restrições alérgicas,proximidade do estabelecimento" (p. 4) | RF de cadastro e perfil. Há implicações de LGPD (ficha A13) |
| **Meio de transporte e localização** do usuário | RN-05: "distância vs. consumo do veículo ou tarifa de transporte" (p. 5) | Um campo obrigatório no perfil (o v2, seção 1.9, já recomenda) |
| **Estoque doméstico** (despensa, com validade) | RF-03 e "insumos com data de vencimento próxima" (p. 4) | RF de registro e atualização do estoque (ficha A09) |
| **Histórico de preços** | "considerando a durabilidade estimada e o histórico de uso" (p. 4); "oscilações abruptas de valores nas gôndolas em relação ao histórico" (p. 11) | RF de persistência e consulta do histórico |
| **Cadastro de lojas** (endereço e localização) | "custo de transporte até a loja rival" (p. 4) | RF ou base de dados de estabelecimentos |
| **Catálogo e normalização de produtos** ("ARROZ T1 5KG" = "Arroz Tipo 1, 5 kg") | RF-02 e "marcas equivalentes registradas" (p. 5) | RF de catálogo e equivalência (o v2, seção 4, estima cerca de 60 itens) |
| **Histórico de consumo** do usuário | "histórico de uso" (p. 4); "validade atende ao consumo semanal" (p. 4) | De onde vem o consumo semanal? (ficha A06) |

---

## 5. Ambiguidades, contradições e ausências

### A01 · Contradição: ajuste "automático" × "não toma decisões automáticas"

> "Ajuste Automático ao Teto Financeiro" (p. 5)
> "um mecanismo de ajuste orçamentário automático (RF-04), reorganizando a lista de compras" (p. 10)
> "A EconoMIA preserva a autonomia do usuário. O sistema não toma decisões automáticas" (p. 4)

- **Problema:** o RF-04 diz que o sistema *reorganiza* a lista sozinho, e a RN-08 diz que ele nunca decide sozinho. A p. 5 usa "sugere dinamicamente", o que favorece a leitura de sugestão.
- **Pergunta:** o RF-04 **propõe** uma lista ajustada para o usuário aceitar, ou **altera** a lista? Se propõe, renomear para "sugestão de ajuste ao orçamento".
- **Decisão:** ___

### A02 · Ambiguidade: quem define a prioridade de cada item

> "Essenciais (proteínas básicas, grãos,itens de higiene primária), Secundários (hortifrúti variado, laticínios complementares) e Superfluos/Opcionais (sobremesas, bebidas)." (p. 4–5)

- **Problema:**
  1. Não diz se a classificação é fixa (tabela do sistema), feita pelo LLM ou escolhida pelo usuário.
  2. "Itens de higiene" saem do escopo de *alimentos* que o resto do relatório descreve.
  3. "Bebidas" como supérfluo inclui leite, café e água? "Hortifrúti" como secundário contradiz o Guia Alimentar, que trata in natura como base da alimentação.
- **Pergunta:** a tabela de prioridade é fixa e editável pelo usuário? Produtos de higiene entram no MVP? Como classificar leite, café e frutas?
- **Decisão:** ___

### A03 · Ausência: como os três ajustes são aplicados

> "1. Redução de volumes dos itens de menor prioridade. 2. Substituição por marcas equivalentes registradas com menor valor. 3. Remoção temporária de itens opcionais." (p. 5)

- **Problema:**
  1. Não diz se os passos são sequenciais (só passa ao 2 se o 1 não bastar) ou combinados.
  2. Não diz quanto reduzir, nem se há um volume mínimo.
  3. "Marcas equivalentes **registradas**": registradas onde, e por quem? Qual critério de equivalência (mesmo tipo, mesmo peso, mesma categoria NOVA)?
  4. A ordem é estranha: reduzir volume vem antes de trocar de marca, embora trocar de marca preserve mais a quantidade de comida.
  5. Se nem os três passos bastarem, o que acontece?
- **Pergunta:** qual é o algoritmo exato (ordem, limites, critério de parada)? Onde fica a tabela de equivalência de marcas?
- **Decisão:** ___

### A04 · Ambiguidade: a fórmula do "custo real" não é o custo real

> "Custo Real por Unidade = Preço do Pacote / Massa ou Volume Líquido" (p. 5) *[fórmula reescrita]*

- **Problema:**
  1. O nome diz "real", mas o custo logístico (RN-05) e o desperdício provável não entram. A fórmula é só o **preço unitário**, que a Lei 13.175/2015 já obriga o mercado a mostrar (v2, seção 1.4).
  2. Não cobre produtos vendidos por unidade (ovos, pães), peso drenado (enlatados), multipacks e promoções do tipo "leve 3, pague 2".
  3. Não fixa a unidade de saída (R$/kg ou R$/100 g) nem a conversão a partir de g e ml.
- **Pergunta:** renomear para "preço por unidade de medida" e criar um "custo efetivo" separado, com deslocamento? Como tratar os casos de 2?
- **Decisão:** ___

### A05 · Ausência: a fórmula do custo logístico

> "O custo logístico incorpora o valor estimado do deslocamento (distância vs. consumo do veículo ou tarifa de transporte) no custo final da compra" (p. 5)
> "assegurar que a pesquisa de menores preços não resulte em um custo logístico de deslocamento ou tempo que elimine a economia do usuário" (p. 11)

- **Problema:**
  1. Não há fórmula.
  2. Faltam os dados: o perfil não tem meio de transporte, consumo do veículo, preço do combustível, tarifa de ônibus nem endereço.
  3. A p. 11 cita o **tempo**, mas a p. 5 só conta dinheiro.
  4. Quem vai a pé não tem custo em reais, mas tem um limite de peso e distância.
- **Pergunta:** qual fórmula usar (ex.: `2 × distância × custo/km` para carro, `2 × tarifa` para ônibus)? O tempo entra? Meio de transporte e região viram campos obrigatórios?
- **Decisão:** ___

### A06 · Ausência: dados que a tabela de exemplos usa e nenhum RF coleta

> "Compara o valor equivalente por unidade de medida (R$/kg), considerando a durabilidade estimada e o histórico de uso." (p. 4) *[fórmula reescrita]*
> "Analisa se a embalagem é menor, se o limite de validade atende ao consumo semanal e se o custo de transporte até a loja rival vale a pena." (p. 4)

- **Problema:**
  1. "Durabilidade estimada", "histórico de uso", "consumo semanal" e "limite de validade" não têm origem.
  2. A NFC-e **não traz a data de validade**.
  3. "Se a embalagem é menor" exige o histórico do tamanho da embalagem para detectar reduflação, e nenhum requisito guarda isso.
- **Pergunta:** essas análises ficam no MVP? Se sim, de onde vem cada dado: o usuário informa, há uma tabela média de durabilidade por categoria, ou o RAG busca em manuais de conservação?
- **Decisão:** ___

### A07 · Ausência: critério de "cesta balanceada"

> "Apresenta uma cesta balanceada por categoria nutricional, indicando a margem de sobra financeira e opções de ajuste." (p. 4)

- **Problema:** não define "balanceada". Pode ser pelos grupos do Guia Alimentar, pela classificação NOVA (o v2, seção 4, propõe NOVA) ou por macronutrientes (tabela TACO). Também conflita com a RN-01, que classifica por prioridade, não por nutrição.
- **Pergunta:** qual critério nutricional vale? Qual prevalece em conflito: prioridade (RN-01) ou nutrição?
- **Decisão:** ___

### A08 · Contradição com o v2: OCR de imagem × QR code da NFC-e, e o "SAT"

> "a partir de imagens de cupons fiscais (NFC-e/SAT) e encartes promocionais por meio de visão computacional e OCR." (p. 10)

- **Problema:**
  1. O v2 (seções 3.2 e 3.3) recomenda ler o **QR code** da NFC-e, que aponta para a consulta pública da Sefaz-DF e é muito mais confiável que OCR. O relatório só fala em OCR.
  2. O **SAT (CF-e-SAT)** é usado em São Paulo. No DF o varejo emite NFC-e. Incluir o SAT amplia o escopo sem necessidade.
  3. Encartes são outro problema (layout livre, sem padrão) e talvez mereçam um RF próprio.
- **Pergunta:** o RF-01 passa a ser "QR code da NFC-e primeiro, OCR como alternativa"? Tirar o SAT? Separar encartes num RF próprio?
- **Decisão:** ___

### A09 · Ausência: o estoque doméstico que o RF-03 consome

> "sugerir receitas culinárias estruturadas a partir dos insumos já disponíveis na despensa do usuário." (p. 10)
> "somado ao compromisso do usuário em manter uma rotina mínima de atualização do seu estoque doméstico." (p. 11)

- **Problema:** o RF-03 depende de um estoque que nenhum RF registra. A manutenção depende de um "compromisso do usuário", que é exatamente a fricção que o próprio relatório aponta como risco: "excesso de dados manuais" (p. 11). Também não diz se o estoque baixa sozinho quando uma receita é feita.
- **Pergunta:** criar um RF de estoque (entrada pela NFC-e, baixa manual ou por receita)? Ou o RF-03 recebe os ingredientes digitados na hora ("tenho ovo, arroz e tomate")?
- **Decisão:** ___

### A10 · Ambiguidade: como verificar os "100% determinísticos"

> "100% das operações aritméticas e comparações financeiras são executadas por algoritmos determinísticos verificáveis, impedindo qualquer alucinação numérica" (p. 10)

- **Problema:** o motor pode calcular certo e, ainda assim, o LLM errar ao **escrever** o número na resposta (arredondar, trocar ou inventar). O RNF não diz como testar.
- **Pergunta:** adotar a regra "todo número exibido vem de um campo do motor, nunca do texto livre do LLM", com um teste automático que compara os números da resposta com a saída do motor?
- **Decisão:** ___

### A11 · Ambiguidade: o que entra nos 2,5 segundos

> "o tempo de resposta para requisições conversacionais e buscas por similaridade no repositório vetorial (RAG) não deve exceder o teto de 2,5 segundos no percentil T90." (p. 10)

- **Problema:**
  1. "T90" não é um termo usual. O provável é **P90** (90º percentil).
  2. Não diz se conta só a busca vetorial ou a resposta completa com o LLM. A resposta de um LLM por API costuma passar de 2,5 s.
  3. Não diz se a leitura de nota (RF-01) entra.
  4. Não define o ambiente nem a carga da medição.
- **Pergunta:** separar em metas próprias? Exemplo: busca RAG P90 ≤ 500 ms; primeiro token do chat P90 ≤ 2,5 s; leitura de nota P90 ≤ 15 s.
- **Decisão:** ___

### A12 · Risco LGPD / Ambiguidade: o que anonimizar na nota fiscal

> "todos os dados de identificação pessoal e chaves de acesso presentes nos cupons fiscais são submetidos a uma camada de anonimização estrita antes da persistência" (p. 10)

- **Problema:**
  1. A **chave de acesso** da NFC-e identifica a *nota*, não a pessoa. Anonimizá-la impede consultar a nota na Sefaz e detectar envio duplicado.
  2. O dado pessoal da nota é o **CPF** (opcional), que o v2 manda descartar.
  3. Não diz se a **imagem original** fica guardada (o v2, seção 3.5, recomenda não guardar).
  4. Não diz o que acontece com o histórico de compras de cada usuário, que também é dado pessoal.
- **Pergunta:** a regra passa a ser "descartar CPF e nome; guardar a chave de acesso (ou o hash dela) para deduplicar; não guardar a imagem"?
- **Decisão:** ___

### A13 · Risco LGPD: restrições alérgicas são dado sensível

> "preferências pessoais (marcas de preferência, restrições alérgicas,proximidade do estabelecimento) possuem pesos subjetivos que pertencem ao usuário." (p. 4)

- **Problema:** alergias e restrições alimentares são **dado referente à saúde**, ou seja, **dado pessoal sensível** (LGPD, art. 5º, II), com regras mais rígidas de consentimento (art. 11). O relatório só trata dos dados dos cupons. A localização do usuário, usada no custo logístico, também é dado pessoal e não é citada.
- **Pergunta:** o MVP guarda restrições alimentares? Se sim, com consentimento específico e opção de apagar. Se não, o usuário informa a cada pedido.
- **Decisão:** ___

### A14 · Escopo: "suporte nativo a comandos de voz"

> "seguindo rigorosamente as diretrizes da WCAG 2.1 no nível AA para disponibilizar navegação simplificada, compatibilidade com leitores de tela e suporte nativo a interações por comandos de voz." (p. 10–11)
> "Interface em linguagem natural capaz de interagir por texto e voz" (p. 6)

- **Problema:** a WCAG 2.1 AA **não exige** comando de voz. Voz é uma funcionalidade à parte (fala→texto, texto→fala), que hoje está escondida dentro de um RNF de acessibilidade. A persona "Aposentados Conscientes" (p. 10) depende dela.
- **Pergunta:** a voz vira um RF próprio, com prioridade definida (MVP ou trabalho futuro)? O RNF-04 fica só com a WCAG 2.1 AA?
- **Decisão:** ___

### A15 · Ausência: de onde vêm os preços no início (partida a frio) e o recorte geográfico

> "O desenvolvimento do EconoMIA parte da premissa central de que haverá um fluxo contínuo de dados de preços regionais, alimentado pela contribuição colaborativa dos usuários via envio de cupons fiscais e pela captura pública de encartes promocionais" (p. 11)
> "comparar atacadões da região" (p. 9)

- **Problema:** em 7 semanas não haverá usuários suficientes para um fluxo colaborativo. Sem preços, as comparações não funcionam. O relatório não define **região**: "da região" não diz qual. O v2 (seções 0 e 3.1) propõe o **Gama** como piloto, com coleta própria em 4 a 6 mercados.
- **Pergunta:** a premissa vira "base inicial coletada pela equipe no Gama + NFC-e da equipe e de voluntários; colaboração aberta como trabalho futuro"? O recorte do Gama entra no relatório?
- **Decisão:** ___

### A16 · Ambiguidade: de onde vem o "índice de confiança" de 85%

> "o sistema adota um mecanismo de checagem com validação do usuário para leituras com índice de confiança inferior a 85%." (p. 11)

- **Problema:** um OCR tradicional (ex.: Tesseract) devolve uma confiança por palavra. Um LLM multimodal **não devolve uma confiança calibrada**. O relatório não diz qual tecnologia usa, nem se a confiança é por campo, por item ou por nota. O número 85% não tem justificativa.
- **Pergunta:** qual será o sinal de confiança (por item; soma dos itens bate com o total da nota; preço dentro da faixa histórica)? Ou mostrar a revisão sempre, para todos os itens?
- **Decisão:** ___

### A17 · Métrica não mensurável: metas sem linha de base nem método

> "busca-se alcançar uma taxa média de economia nas compras mensais (ΔE) igual ou superior a 15%, acompanhada por uma taxa de acurácia na leitura OCR de no mínimo 92% para itens e preços. [...] uma redução de pelo menos 20% no desperdício doméstico de perecíveis [...] um Net Promoter Score (NPS) superior a 65 pontos e por uma taxa de retenção ativa de usuários em 30 dias superior a 45%." (p. 11) *[fórmula reescrita]*

- **Problema:**

| Meta | Problema |
| --- | --- |
| Economia ≥ 15% | Economia em relação a quê (cesta DIEESE, compra anterior, maior preço da base)? "Compras mensais" exige pelo menos 1 mês de uso real |
| OCR ≥ 92% | Métrica indefinida (acurácia por campo, F1 por item?). O benchmark citado no v2 (ReceiptBench 2026) mostra F1 ≈ 0,71–0,74 nos melhores modelos. A meta é otimista para OCR e fácil para QR code |
| Desperdício −20% | Não há linha de base de desperdício do usuário nem método de medição |
| NPS > 65 | É preciso um número mínimo de respondentes; com poucos usuários, o número não tem significado |
| Retenção em 30 dias > 45% | O projeto inteiro dura 7 semanas e os testes com usuários ficam na semana 7 (v2, seção 4), então não há 30 dias de uso |

Falta também a métrica que o próprio desafio pede: **LLM puro × LLM + RAG** (semana 3), citada na p. 8, mas sem meta.

- **Pergunta:** separar em **métricas de MVP** (medidas em laboratório, com gabarito: acurácia da leitura de nota, acerto do RAG no gabarito de cerca de 50 perguntas, erro numérico = 0, latência) e **métricas de produto** (economia, desperdício, NPS, retenção), estas declaradas como trabalho futuro?
- **Decisão:** ___

### A18 · Contradição: duas perguntas norteadoras diferentes

> "Como utilizar a Inteligência Artificial para ajudar as pessoas a compreender melhor as opções de compra, tomar decisões mais conscientes e aproveitar melhor seus recursos financeiros e alimentares?" (p. 3, seção 1.1)
> "Como um assistente baseado em Inteligência Artificial pode integrar orçamento, histórico de preços, necessidades domésticas e planejamento de refeições para apoiar famílias na comparação de alternativas de compra, na avaliação real de promoções e na redução do desperdício de alimentos?" (p. 14)

- **Problema:** são duas perguntas de nível diferente. A da p. 3 é genérica, próxima da Big Idea. A da p. 14 é mais específica e testável. O README e as [definições do projeto](definicoes-do-projeto.md) ainda dizem "a definir".
- **Pergunta:** qual é a **Essential Question** oficial? Sugestão: a da p. 14, com recorte (ex.: "... famílias do Gama ...").
- **Decisão:** ___

### A19 · Contradição com o v2: personas definitivas × hipóteses

> "As Personas que direcionam o design de experiência incluem: Gestores Familiares: 30-40 anos [...] Jovens Profissionais: 19-26 anos [...] Aposentados Conscientes: 50-68 anos" (p. 9–10)

- **Problema:** o relatório apresenta as personas como prontas. O v2 (seção 5) as trata como **proto-personas a validar** com questionário, e as faixas divergem: no v2, "Mãe que faz o mês" tem 30 a 45 anos e o aposentado tem 60 anos ou mais. O v2 também tem uma quarta hipótese ("Casal de carro do atacarejo"). "Aposentados" a partir de 50 anos é uma faixa incomum. Nenhuma persona do relatório tem **meio de transporte** nem **renda**, que o v2 aponta como variáveis-chave.
- **Pergunta:** o relatório passa a chamar essas personas de hipóteses até o questionário? Qual conjunto (relatório ou v2) vale?
- **Decisão:** ___

### A20 · Ambiguidade: stakeholders internos que a equipe não tem

> "Stakeholders Internos: Equipes multidisciplinares de Engenharia de Software, Ciência de Dados/IA, UX/UI Design, Product Managers e Especialistas em DevOps e Segurança." (p. 9)

- **Problema:** a equipe tem 5 integrantes divididos em 5 frentes (p. 7–9 e Considerações Finais). "Product Managers" e "Especialistas em Segurança" não existem como papel. Faltam stakeholders reais do contexto acadêmico: **mentores e avaliadores da Residência**, Instituto Eldorado e UnB. Faltam também, entre os externos, **Sefaz-DF** (dona da consulta da NFC-e) e fontes de dados como **DIEESE e IBGE**.
- **Pergunta:** reescrever a lista de stakeholders com os papéis reais (quem é quem na equipe) e os externos que de fato afetam o projeto?
- **Decisão:** ___

### A21 · Ausência: fontes concretas da base do RAG

> "Tabela Nutricional e Guia Alimentar para a População Brasileira; Acervo de receitas estruturadas com tempos de preparo, substituições e rendimento; Manuais de conservação e armazenamento de perecíveis" (p. 7)

- **Problema:** "Tabela Nutricional" não diz qual (TACO/Unicamp? TBCA/USP?). O "acervo de receitas" não tem fonte nem **licença**: copiar receitas de sites pode ter restrição de direitos autorais. Os "manuais de conservação" também não são nomeados. O relatório cita "similaridade de cosseno", mas não escolhe o modelo de embeddings nem o banco vetorial (o v2, seção 3.4, deixa isso "em decisão").
- **Pergunta:** quais documentos exatos entram na base (com link e licença)? Registrar em [`data/base-conhecimento/FONTES.md`](https://github.com/dida0982/challenge2-qualidade-de-vida/blob/main/data/base-conhecimento/FONTES.md)?
- **Decisão:** ___

### A22 · Ausência: funcionalidades que são só um título

> "Rotulagem de Confiabilidade dos Dados · Detecção de Anomalias de Preço · Garantias de Transparência" (p. 5)

- **Problema:** aparecem só em lista, sem descrição. Interpretações possíveis:
  - **Confiabilidade:** selo por idade e origem do preço (relaciona-se à RN-11).
  - **Anomalias:** preço fora de uma faixa do histórico, que pode ser erro de leitura ou promoção real.
  - **Transparência:** o mesmo que RN-07 (XAI).
- **Pergunta:** confirmar essas leituras? Definir o critério de anomalia (ex.: mais de 2 desvios-padrão do histórico do item na região)? "Transparência" pode ser fundida com a RN-07?
- **Decisão:** ___

### A23 · Risco jurídico: "captura pública de encartes"

> "pela captura pública de encartes promocionais" (p. 11)
> "redes varejistas e supermercados locais (fontes de ofertas/encartes)" (p. 9)

- **Problema:** não diz se a captura é por foto do usuário, download manual ou raspagem automática de sites (scraping). A raspagem pode violar os termos de uso dos sites dos mercados.
- **Pergunta:** no MVP, encarte = foto ou PDF enviado pelo usuário ou pela equipe, sem scraping automático?
- **Decisão:** ___

### A24 · Ausência: regra para substituições e preferências culturais

> "Investiga-se também qual é a fronteira ideal da autonomia da Inteligência Artificial ao sugerir substituições de produtos sem desrespeitar as tradições e preferências culturais da família" (p. 12)

- **Problema:** aparece como pergunta de pesquisa, mas afeta diretamente a RN-03 (passo 2: troca de marca) e o RF-04. Sem regra, o sistema pode sugerir trocar um item que o usuário marcou como preferido.
- **Pergunta:** criar a regra "item marcado como **fixo** pelo usuário nunca é trocado nem reduzido"? Isso exige um campo "fixo" na lista ou no perfil.
- **Decisão:** ___

### A25 · Escopo: arquitetura × prazo, sem núcleo mínimo

> "Projetar e implementar APIs RESTful/gRPC, modelar bancos de dados relacionais e vetoriais e estruturar pipelines de ingestão" (p. 8)
> "conteinerização com Docker, pipelines de integração e entrega contínua (CI/CD), estratégias de deployment, monitoramento de métricas e gestão centralizada de logs" (p. 8–9)

- **Problema:** o relatório descreve uma arquitetura de produto completo (REST **e** gRPC, dois bancos, CI/CD, logs centralizados), além de cerca de 10 funcionalidades e voz, sem dizer **o que é obrigatório** no MVP. O v2 (seção 4) classifica "escopo grande demais" como risco Alto e propõe o núcleo **orçamento + comparação + leitura de NFC-e**.
- **Pergunta:** adotar o núcleo do v2 e marcar cada RF como **MVP** ou **futuro**? Fica REST **ou** gRPC (não os dois)?
- **Decisão:** ___

---

## 6. Fontes e problemas de redação

| # | Trecho | Problema | Ação sugerida |
| --- | --- | --- | --- |
| F1 | "Em outubro de 2026, por exemplo, a alimentação em casa subiu 1,01%, enquanto o grupo Alimentação e Bebidas avançou 0,88%." (p. 13) | O relatório é de 29/10. O IPCA de outubro só sai em novembro, então o dado deve ser do **IPCA-15** de outubro. Também não há link | Confirmar se é IPCA-15 e pôr o link do IBGE |
| F2 | "Em 15 de setembro de 2026, o relatório de mostra variações expressivas" (p. 13) | Frase truncada ("o relatório **de** mostra"). Não diz qual relatório | Corrigir e citar a fonte |
| F3 | "IBGE/IPCA-15 biblioteca.ibge.gov+1", "one.oecd", "embrapa", "Embrapa/FGV gov+1" (p. 13) | Links sem título, data nem autor. O sufixo "+1" parece ter vindo de cópia de uma ferramenta de busca | Trocar por referências completas (o v2 já tem a Embrapa/FGV como [21] e [22]) |
| F4 | "Em estimativa da ONU, cerca de 17% dos alimentos adquiridos em 2019 — cerca de 931 milhões de toneladas — foram descartados [...] Os dados reforçam a dimensão do problema no país" (p. 14) | Dado global (UNEP Food Waste Index 2021) usado para falar "do país", e sem link | Citar a fonte. Para o Brasil, usar o dado do PNUMA de 94 kg per capita (v2, [23]) |
| F5 | "mecanismos de compra tudo sobre promoções no varejo, conclui- se que mecanismos promocionais múltiplos podem levar consumidores a decisões de compra subótimas" (p. 14) | Frase sem sentido ("compra tudo sobre"), e o estudo da OCDE não é identificado | Reescrever e citar o estudo da OCDE pelo título |
| F6 | "Beattie, Alan. False Economy [...] (2009)" (p. 2 e 14) | O livro trata de história econômica, não de "falsa economia" no consumo doméstico. O uso do conceito na p. 2 é uma interpretação livre | Manter como inspiração ou trocar por fonte sobre reduflação e preço unitário (v2, seção 1.4) |
| F7 | "(R$/kg ou R$/L)", "(ΔE)", "(C_total > O_disponível)" (p. 3, 4, 5, 10, 11) | LaTeX quebrado na exportação: aparece como `$R\$/kg$` e `$\Delta E$` | Usar texto simples ou o editor de equações do Docs/Word |
| F8 | "4. Como alocar o orçamento:;" (p. 2) | Pontuação duplicada | Corrigir |
| F9 | "Superfluos" (p. 5); "grãos,itens", "intenções,sumarização", "alérgicas,proximidade", "estratégico,a", "problema,objetivos", "riscos,métricas", "logs.Apoia" (p. 5–9) | Acento faltando e espaços faltando após vírgula ou ponto | Revisão ortográfica |
| F10 | Título da seção 1: "O Problema e o Contexto de Mercado e A Complexidade das Decisões de Compras Domésticas" (p. 2) | Dois títulos colados num só | Separar em 1 e 1.1 (e renumerar a pergunta norteadora) |

---

## 7. Resumo das decisões pendentes

**Prioridade Alta** = bloqueia a Semana 2 (base de conhecimento, dados e primeiro RAG) ou o desenho dos dados.

| # | Tipo | Tema | Prioridade |
| --- | --- | --- | --- |
| A01 | Contradição | RF-04: sugerir ou alterar a lista | Média |
| A02 | Ambiguidade | Quem classifica a prioridade dos itens; higiene no escopo | Média |
| A03 | Ausência | Algoritmo dos 3 ajustes ao orçamento | Média |
| A04 | Ambiguidade | "Custo real" × preço unitário; casos especiais | **Alta** |
| A05 | Ausência | Fórmula do custo logístico; transporte no perfil | **Alta** |
| A06 | Ausência | Validade, durabilidade e consumo: origem dos dados | Média |
| A07 | Ausência | Critério de cesta balanceada | Média |
| A08 | Contradição | QR code × OCR; tirar o SAT | **Alta** |
| A09 | Ausência | RF de estoque doméstico | **Alta** |
| A10 | Ambiguidade | Teste dos "100% determinísticos" | Média |
| A11 | Ambiguidade | O que entra nos 2,5 s | Baixa |
| A12 | Risco LGPD | Chave de acesso, CPF e imagem | **Alta** |
| A13 | Risco LGPD | Restrição alérgica = dado sensível | **Alta** |
| A14 | Escopo | Voz: RF próprio, MVP ou futuro | Média |
| A15 | Ausência | Partida a frio dos preços; recorte no Gama | **Alta** |
| A16 | Ambiguidade | Origem do índice de confiança de 85% | Média |
| A17 | Métrica não mensurável | Metas de MVP × metas de produto | **Alta** |
| A18 | Contradição | Qual é a Essential Question | **Alta** |
| A19 | Contradição | Personas: definitivas ou hipóteses | Média |
| A20 | Ambiguidade | Stakeholders reais | Baixa |
| A21 | Ausência | Documentos e licenças da base do RAG | **Alta** |
| A22 | Ausência | Confiabilidade, anomalia e transparência | Baixa |
| A23 | Risco jurídico | Scraping de encartes | Baixa |
| A24 | Ausência | Itens "fixos" que não podem ser trocados | Média |
| A25 | Escopo | Núcleo do MVP e stack mínima | **Alta** |
| F1–F10 | Fonte frágil / redação | Correções no texto do relatório | Baixa |
