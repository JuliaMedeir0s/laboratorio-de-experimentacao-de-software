# Lab05S02 — Relatório Final (Execução + Análise)

## Introdução

Este relatório apresenta um experimento controlado comparando REST e GraphQL quanto a (RQ1) latência e (RQ2) tamanho da resposta. Foram considerados três tratamentos: REST com payload completo (REST_FULL), GraphQL solicitando os mesmos campos (GQL_FULL) e GraphQL solicitando subconjunto (GQL_SMALL).

## Metodologia

**Ambiente (resumo):**

- OS: linux 6.17.0-29-generic (x64)
- CPUs: 12
- Node: v18.19.1
- Trials por tratamento: 200 (warm-up: 20)
- userId consultado: 42

**Coleta:** para cada requisição, foi medido (i) tempo total de resposta em ms e (ii) tamanho do corpo da resposta em bytes. A ordem das requisições foi randomizada para reduzir viés temporal.


**Como reproduzir:** ver o passo-a-passo em `README.md` (rodar o benchmark e depois os scripts de análise).

## Revisão Inicial dos Dados

- Total de medições: 600

- Mediões OK (status 2xx/ok=1): 600

## Estatística Descritiva (resumo)

As tabelas descritivas de latência e tamanho (média/mediana/desvio/min/max por tratamento) estão consolidadas no dashboard: [dashboard.md](dashboard.md).

## Resultados por Pergunta de Pesquisa

### RQ1 — GraphQL é mais rápido que REST?

Comparação primária: `REST_FULL` vs `GQL_FULL` (mesmo volume de dados). Testes reportados: Mann–Whitney (não-paramétrico) e t-test de Welch (paramétrico).

- Mann–Whitney U: U=359, p=1.01e-64
- Welch t-test: t=-26.695, p=3.86e-76
- Cliff's delta (REST vs GQL): -0.982

- Mediana (REST_FULL): 4.593 ms | Mediana (GQL_FULL): 9.669 ms
- Conclusão (RQ1): neste cenário, **GraphQL não foi mais rápido**; REST teve menor latência.


### RQ2 — GraphQL tem tamanho menor que REST?

Comparação primária: `REST_FULL` vs `GQL_SMALL` (REST com payload fixo vs GraphQL selecionando subconjunto de campos).

- Mann–Whitney U: U=40000, p=9.18e-89
- Welch t-test: N/A (variância ~0 ou dados degenerados)
- Cliff's delta (REST vs GQL): 1.000

- Mediana (REST_FULL): 18933 bytes | Mediana (GQL_SMALL): 571 bytes
- Redução mediana: 97.0%
- Conclusão (RQ2): neste cenário, **GraphQL teve resposta menor** (seleção de campos reduziu payload).


## Gráficos

- Latência: ![](../figures/latency_boxplot.png)

- Tamanho: ![](../figures/size_boxplot.png)


## Discussão

Os resultados devem ser interpretados considerando que o cenário é local e usa dataset sintético. Diferenças observadas podem refletir custos de parsing/execução do GraphQL, serialização JSON e estrutura do payload.
