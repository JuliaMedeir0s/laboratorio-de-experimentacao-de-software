# Lab05S03 — Dashboard (Visualização de Resultados)

Este dashboard resume as diferenças entre REST e GraphQL nas métricas de **latência** (RQ1) e **tamanho da resposta** (RQ2).

Para detalhes de metodologia, testes estatísticos e discussão, ver: [relatorio_final.md](relatorio_final.md).

## Tabela — Latência (ms)

| treatment   |   n |   media |   mediana |   std |   min |    max |
|:------------|----:|-------:|---------:|------:|------:|-------:|
| GQL_FULL    | 200 | 10.185 |    9.669 | 2.712 | 5.159 | 17.606 |
| GQL_SMALL   | 200 |  7.500 |    7.242 | 1.940 | 3.487 | 15.191 |
| REST_FULL   | 200 |  4.693 |    4.593 | 1.052 | 2.256 |  8.523 |

## Tabela — Tamanho (bytes)

| treatment   |   n |   media |   mediana |   std |   min |   max |
|:------------|----:|-------:|---------:|------:|------:|------:|
| GQL_FULL    | 200 |  18951 |    18951 |     0 | 18951 | 18951 |
| GQL_SMALL   | 200 |    571 |      571 |     0 |   571 |   571 |
| REST_FULL   | 200 |  18933 |    18933 |     0 | 18933 | 18933 |

## Gráfico — Latência

![](../figures/dashboard_latency.png)

## Gráfico — Tamanho

![](../figures/dashboard_size.png)
