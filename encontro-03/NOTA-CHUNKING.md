# Nota de chunking · Equipe: Aurora

Caso: (x) Aurora  ( ) domínio próprio: ____________

## 1. O que adotamos

Estratégia de chunking: chunk por estrutura, com `MarkdownHeaderTextSplitter` e `prefixar_titulo=True`, produzindo trechos na forma "Título > Seção". Isso mantém o contexto da política no início do trecho e reduz a mistura de regras de diferentes assuntos.  

Busca (vetor, BM25 ou híbrida): híbrida (vetor + BM25 com Reciprocal Rank Fusion), porque a busca por sentido ajuda com linguagem natural e a busca léxica ajuda com termos específicos e jargão interno.  

Tratamento de versões e de autoridade: mantém só a vigência mais recente por política e descarta páginas fora da autoridade "oficial". Isso evita que a resposta venha de uma política desatualizada ou de um material informal.

k (quantos trechos o agente recebe): 3 trechos por pergunta.  

## 2. Por quê

| configuração | normal | excecao | conflito | termo-exato | autoridade | total |
|---|---|---|---|---|---|---|
| base: tamanho 400 · vetor | 7/7 (0) | 2/2 (1) | 2/3 (3) | 3/3 (1) | 1/1 (0) | 15/16 (5) |
| estrutura · vetor | 6/7 (0) | 2/2 (0) | 2/3 (3) | 3/3 (0) | 1/1 (0) | 14/16 (3) |
| estrutura · bm25 | 5/7 (0) | 2/2 (0) | 1/3 (3) | 3/3 (0) | 1/1 (0) | 12/16 (3) |
| estrutura · hibrida | 6/7 (0) | 2/2 (0) | 1/3 (3) | 3/3 (0) | 1/1 (0) | 13/16 (3) |
| estrutura · hibrida + vigente | 6/7 (0) | 2/2 (0) | 3/3 (0) | 3/3 (0) | 1/1 (0) | 15/16 (0) |
| final: híbrida + vigente + oficial | 6/7 (0) | 2/2 (0) | 3/3 (0) | 3/3 (0) | 1/1 (0) | 15/16 (0) |

A configuração escolhida foi a final: híbrida + vigente + oficial, porque ela mantém o mesmo recall da linha de base (15/16) e elimina a contaminação, reduzindo de 5 trechos errados para 0. O ponto mais importante é o custo de erro: na linha de base, 5 casos contaminados podem levar o agente a responder com a regra errada ou a versão velha. Em comparação, a estratégia por estrutura melhora bastante a separação entre tópicos, mas ainda fica em 14/16; a busca BM25 sozinha piora o recall (12/16); a busca híbrida sem filtros ainda deixa conflitos sem resolver (13/16). Só quando adicionamos a filtragem por vigência (`so_vigente=True`) e autoridade (`so_oficial=True`) o cenário fica robusto: 15/16 com zero contaminação. A filtragem por vigência é o que faz a diferença principal na categoria de conflito, e a filtragem por autoridade mantém o mesmo desempenho sem perder acertos, funcionando como proteção contra documentação informal.

## 3. O que ela não resolve

Ainda há um caso que falha na melhor configuração: `N5` — “Roubaram meu notebook do trabalho. O que eu faço?” Espera-se: “anexe o boletim de ocorrência”. A resposta existe na base, em `ti-equipamentos` (“Em caso de roubo, anexe o boletim de ocorrência”), mas o buscador ainda não a recupera em top-3. A causa mais adequada é `chunking`/retrieval semântico: o trecho correto está na base, mas a busca traz trechos mais genéricos do documento ou de outra política antes da regra específica. Em outras palavras, não é um caso de corpus vazio nem de sem resposta; é um caso em que o texto relevante existe, mas a unidade de busca não preserva o detalhe decisivo com o nível de contexto suficiente.

Esse problema deve ser tratado na camada de ingestão/retrieval, com refinamento do chunking ou regras de pós-processamento, e também em uma etapa de validação do agente antes de responder. O “não sei” ou a regra de fallback não é o lugar certo para resolver isso; o problema é que a evidência correta não está sendo recuperada com confiança.

## 4. O que a ingestão precisa garantir

Para a estratégia funcionar, a ingestão precisa preencher corretamente os metadados que a busca usa:

- `id`: quem preenche — editor/owner da página ou da wiki; quando atualiza — ao publicar ou alterar a política; se estiver errado — o sistema mistura páginas de políticas diferentes ou seleciona a página errada.
- `titulo`: quem preenche — o autor da página ou o time de documentação; quando atualiza — no momento da publicação; se estiver errado — o prefixo do chunk perde contexto e a busca mistura assuntos parecidos.
- `espaco`: quem preenche — responsável do espaço/área (TI, RH etc.); quando atualiza — ao criar ou mover a página; se estiver errado — o filtro de contexto e a classificação documental ficam inconsistentes.
- `politica`: quem preenche — dono da regra ou time responsável pela política; quando atualiza — toda vez que a política muda ou ganha exceção; se estiver errado — a lógica de vigência pode funcionar sobre o conjunto errado e o agente responde com a regra equivocada.
- `vigencia`: quem preenche — responsável da política e aprovador da mudança; quando atualiza — na publicação de nova versão; se estiver errado — a política antiga pode continuar aparecendo e gerar resposta desatualizada.
- `autoridade`: quem preenche — comitê de governança ou responsável da área; quando atualiza — quando a página passa a ser oficial ou deixa de ser; se estiver errado — o filtro `so_oficial` pode incluir material não aprovado ou excluir a fonte correta.

Conclusão: a estratégia de ingestão precisa garantir que cada documento seja rastreável, versionado e atribuído à fonte correta; se qualquer um desses metadados estiver inconsistente, a resposta do agente pode parecer correta, mas estará baseada em conteúdo errado, antigo ou não oficial.
 