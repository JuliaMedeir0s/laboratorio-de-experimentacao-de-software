# Lab05S01 — Desenho e Preparação do Experimento

## Objetivo
Avaliar quantitativamente benefícios (ou ausência deles) na adoção de **GraphQL** em comparação com **REST**.

Perguntas de Pesquisa:
- **RQ1**: Respostas GraphQL são mais rápidas que respostas REST?
- **RQ2**: Respostas GraphQL têm tamanho menor que respostas REST?

## A) Hipóteses Nula e Alternativa

### RQ1 — Tempo de resposta (latência)
- **H0₁ (nula)**: Não há diferença na latência entre REST e GraphQL quando retornam a **mesma quantidade de dados**.
- **H1₁ (alternativa)**: Há diferença na latência entre REST e GraphQL quando retornam a **mesma quantidade de dados**.

> Observação: como direção (“mais rápida”) pode ser controversa, a análise estatística usa teste bicaudal; a discussão responde “mais rápido” olhando médias/medianas e tamanho de efeito.

### RQ2 — Tamanho da resposta
- **H0₂ (nula)**: Não há diferença no tamanho (bytes) da resposta entre REST e GraphQL.
- **H1₂ (alternativa)**: Respostas GraphQL têm tamanho menor que REST em cenários onde REST devolve payload fixo e GraphQL pode selecionar subconjunto de campos.

## B) Variáveis Dependentes

- **Latência (ms)**: tempo total entre envio e recebimento do payload.
- **Tamanho (bytes)**: tamanho do corpo de resposta (payload) recebido.

## C) Variáveis Independentes

- **Tipo de API / tratamento**:
  - `REST_FULL`: endpoint REST retorna objeto completo.
  - `GQL_FULL`: GraphQL consulta os **mesmos campos** do REST (payload equivalente).
  - `GQL_SMALL`: GraphQL consulta **subconjunto** de campos (para avaliar redução de payload).

## D) Tratamentos

Tratamentos são implementados sobre o **mesmo servidor local** e o **mesmo conjunto de dados**:

- **REST_FULL**: `GET /rest/user/:id`
- **GQL_FULL**: `POST /graphql` com query “full” (mesmos campos)
- **GQL_SMALL**: `POST /graphql` com query “small” (menos campos)

## E) Objetos Experimentais

- Um servidor Node.js local (`api/src/server.js`) expondo REST + GraphQL.
- Um conjunto de dados **sintético e determinístico** (gerado por semente) com:
  - usuários
  - posts por usuário
  - comentários por post

O objeto consultado é sempre um usuário específico (`userId`) para reduzir variabilidade.

## F) Tipo de Projeto Experimental

- **Within-subject / medidas repetidas**: cada tratamento é executado várias vezes no mesmo ambiente.
- **Randomização**: a ordem das requisições é embaralhada por trial para reduzir efeitos de aquecimento, cache e variações temporais.
- **Warm-up**: execuções iniciais descartadas para estabilizar JIT/caches.

## G) Quantidade de Medições

Padrão do script (`bench/run_experiment.js`):
- **Warm-up**: 20 requisições por tratamento (não registradas)
- **Medições**: 200 requisições por tratamento (registradas)

Total esperado: 3 tratamentos × 200 = **600 medições**.

## H) Ameaças à Validade

### Validade Interna
- Cache do runtime (V8), pooling de conexões HTTP e variação de carga do SO podem afetar latências.
- Mitigação: warm-up + randomização de ordem + mesmo host/porta.

### Validade de Construção
- Latência medida inclui serialização JSON; isso faz parte do custo real para APIs HTTP, mas não isola “custo puro” do motor GraphQL.
- Payload “full” tenta igualar campos REST vs GraphQL, mas pode haver diferenças pequenas no formato.

### Validade Externa
- Dataset sintético e execução local podem não representar cargas reais, rede, autenticação, DB real, cache distribuído etc.

### Validade de Conclusão
- Distribuições podem ser não-normais; testes paramétricos podem ser inadequados.
- Mitigação: usar estatística descritiva robusta (mediana/IQR) + testes não paramétricos (Mann–Whitney) e tamanhos de efeito.

## Preparação do Experimento (Passo 2)

Implementações preparadas neste lab:
- Servidor REST + GraphQL: `api/src/server.js`
- Script de execução e coleta: `bench/run_experiment.js` (gera `data/results.csv`)
- Scripts de análise/relatório: `analysis/analyze_and_report.py`
- Dashboard: `analysis/make_dashboard.py`

