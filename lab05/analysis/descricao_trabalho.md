# Lab05 — O que foi feito e dicionário de dados do CSV

## Visão geral (o que foi feito)

Este lab foi implementado como um cenário **reprodutível** para comparar **REST vs GraphQL** em duas métricas:

- **RQ1 (tempo)**: latência de resposta.
- **RQ2 (tamanho)**: tamanho do payload (bytes) recebido.

A solução foi organizada em quatro partes principais:

1) **Desenho do experimento (Sprint 1)**
- Documento com hipóteses, variáveis, tratamentos, medições e ameaças à validade: `sprint1_desenho_experimento.md`.

2) **Cenário experimental (API local REST + GraphQL)**
- Servidor Node/Express que expõe os mesmos dados via **REST** e via **GraphQL**.
- Objetivo: manter **mesmo host, mesma máquina, mesmo dataset**, mudando apenas o “tipo de API/consulta”.
- Código:
  - Dataset sintético e determinístico: `api/src/data.js`.
  - Endpoint REST: `GET /rest/user/:id` (tratamento `REST_FULL`).
  - Endpoint GraphQL: `POST /graphql` (tratamentos `GQL_FULL` e `GQL_SMALL`).
  - Servidor: `api/src/server.js`.

3) **Execução do experimento e coleta**
- Script Node que:
  - sobe o servidor local automaticamente,
  - executa **warm-up** (descartado),
  - executa trials com **ordem randomizada**,
  - mede **latência (ms)** e **tamanho (bytes)**,
  - grava resultados em CSV.
- Código: `bench/run_experiment.js`.
- Saídas:
  - `data/results.csv` (todas as medições)
  - `data/run_info.json` (metadados do ambiente e parâmetros do run)

4) **Análise, Relatório e Dashboard**
- Análise estatística e geração do relatório final: `analysis/analyze_and_report.py` → `analysis/relatorio_final.md`.
- Dashboard com tabelas e gráficos (Pandas + Matplotlib/Seaborn): `analysis/make_dashboard.py` → `analysis/dashboard.md`.
- Figuras geradas em `figures/`.

## Dicionário de dados — data/results.csv

O arquivo `data/results.csv` contém **uma linha por requisição medida** (warm-up não entra no CSV).

### Cabeçalho

O cabeçalho atual é:

```
ts,trial,treatment,userId,latency_ms,size_bytes,ok,status,error
```

### Significado das colunas

| Coluna | Tipo | Unidade / domínio | Como é gerada | Interpretação |
|---|---:|---|---|---|
| `ts` | string | ISO-8601 UTC | `new Date().toISOString()` | Momento em que a linha foi registrada (não é o “início exato” do request; é o timestamp na gravação da linha). |
| `trial` | int | 1..N | do agendamento | Índice do trial lógico. Cada trial possui 1 execução por tratamento, mas a ordem é embaralhada. |
| `treatment` | string | `REST_FULL`, `GQL_FULL`, `GQL_SMALL` | do agendamento | Tratamento aplicado naquela medição (qual API/consulta foi chamada). |
| `userId` | int | id do usuário | argumento (`--userId`) | Identificador do usuário consultado em todas as chamadas. |
| `latency_ms` | float | milissegundos | `process.hrtime.bigint()` | Latência total do request: inclui rede local + parsing + execução + serialização + transferência + leitura do body. |
| `size_bytes` | int | bytes | tamanho do body | Tamanho do corpo da resposta (payload) em bytes, medido após ler `res.arrayBuffer()`. |
| `ok` | int | 0 ou 1 | `res.ok` | 1 se resposta foi HTTP 2xx; 0 caso falha (rede/erro/HTTP não-2xx). |
| `status` | int | código HTTP (ex.: 200) | `res.status` | Código HTTP retornado. Em erro de rede/exceção, pode ser 0. |
| `error` | string | texto livre | exception message | Mensagem do erro (se houver). Vazio quando a medição teve sucesso. |

### Observações importantes

- Para análises de latência/tamanho, normalmente você deve filtrar **apenas `ok == 1`**, para não misturar falhas com medidas válidas.
- O tratamento **`GQL_FULL`** tenta retornar um payload comparável ao `REST_FULL` (mesmos campos), para responder RQ1 com “volume semelhante”.
- O tratamento **`GQL_SMALL`** retorna um subconjunto de campos (cenário típico onde GraphQL pode evitar overfetch), mais indicado para discutir RQ2.

### Exemplo de linha interpretada

Exemplo (valores ilustrativos):

```
2026-05-29T00:58:34.650Z,116,REST_FULL,42,4.327,18933,1,200,
```

Interpretação:
- `trial=116` (um dos trials lógicos), tratamento REST_FULL.
- Consultou `userId=42`.
- Latência medida: `4.327 ms`.
- Payload: `18933 bytes`.
- Sucesso: `ok=1`, HTTP `200`.

## Metadados do run — data/run_info.json

O arquivo `data/run_info.json` complementa o CSV com:
- parâmetros do run (`trials`, `warmup`, `userId`, `seed` de randomização),
- configuração do dataset (seed e tamanhos),
- informações do ambiente (OS, CPU count, Node version).
