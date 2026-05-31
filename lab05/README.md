# Lab05 — GraphQL vs REST (Experimento Controlado)

Este diretório contém um cenário **reprodutível** para comparar **REST vs GraphQL** em duas métricas:

- **RQ1**: tempo de resposta (latência)
- **RQ2**: tamanho da resposta (bytes)

A implementação cria uma **API local** que expõe o mesmo conjunto de dados via **REST** e via **GraphQL**, e um script que executa medições e salva um **CSV**. Em seguida, scripts em Python geram o **relatório final** e um **dashboard** (tabelas + gráficos) usando **Pandas + Matplotlib/Seaborn**.

## Estrutura

- `sprint1_desenho_experimento.md` — desenho do experimento + decisões
- `api/` — servidor local REST + GraphQL
- `bench/run_experiment.js` — executa o experimento e grava `data/results.csv`
- `analysis/` — scripts de análise, relatório e dashboard
- `data/` — resultados (`results.csv`) e metadados (`run_info.json`)
- `figures/` — gráficos gerados

## Como rodar (do zero)

### 1) Subir dependências da API

```bash
cd api
npm install
```

### 2) Executar o experimento (gera CSV + run_info)

Na raiz do `lab05`:

```bash
node bench/run_experiment.js --trials 200 --warmup 20 --out data/results.csv
```

Arquivos gerados:
- `data/results.csv`
- `data/run_info.json`

### 3) Instalar dependências de análise (Python)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r analysis/requirements.txt
```

### 4) Gerar relatório final (Sprint 2)

```bash
python3 analysis/analyze_and_report.py --csv data/results.csv --run-info data/run_info.json --figdir figures --out-md analysis/relatorio_final.md
```

### 5) Gerar dashboard (Sprint 3)

```bash
python3 analysis/make_dashboard.py --csv data/results.csv --figdir figures --out-md analysis/dashboard.md
```

## Observações

- O experimento é **local** (mesma máquina), reduzindo ruído de rede externa.
- As consultas GraphQL usadas incluem um cenário **"full"** (mesma quantidade de dados do REST) e um cenário **"small"** (menos campos), para avaliar RQ1 e RQ2.
