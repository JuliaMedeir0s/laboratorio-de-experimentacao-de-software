# Lab 02 — Qualidade de sistemas Java

Este diretório contém os scripts e artefatos do Laboratório 02.

## Pré-requisitos

- Python 3.10+
- Git
- Java (para executar o CK)
- Maven (para compilar o CK na primeira execução)

## Instalação

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

## Configurar token do GitHub

Crie o arquivo `lab02/.env` com o seu token:

```
GITHUB_TOKEN=seu_token_aqui
```

---

## Sprint 1 (Lab02S01)

### 1. Gerar a lista dos 1000 repositórios

```bash
.venv/Scripts/python scripts/coletar_repositorios.py --count 1000 --output data/repos.csv
```

Saída: `data/repos.csv`

### 2. Coletar métricas CK de 1 repositório (entrega da sprint)

```bash
.venv/Scripts/python scripts/clonar_e_analisar.py --repo Snailclimb/JavaGuide --output data/raw/ --skip-ck-download
```

Saída: `data/raw/Snailclimb_JavaGuide_class.csv` (e demais CSVs do CK)

---

## Sprint 2 (Lab02S02)

### 3. Coletar métricas CK dos 1000 repositórios

> Atenção: esse passo pode levar várias horas e ocupar bastante espaço em disco.

```bash
.venv/Scripts/python scripts/clonar_e_analisar.py --csv data/repos.csv --output data/raw/ --skip-ck-download
```

Saída: um `_class.csv` por repositório em `data/raw/`

### 4. Consolidar métricas (CK + GitHub)

```bash
.venv/Scripts/python scripts/analisar_dados.py
```

Saída: `data/processed/merged_metrics.csv`

### 5. Gerar gráficos de correlação e teste de Spearman

```bash
.venv/Scripts/python scripts/visualizar_resultados.py
```

Saída: gráficos em `results/` e tabela `results/correlacoes_spearman.csv`

---

## Estrutura de diretórios

```
lab02/
├── data/
│   ├── repos.csv              # lista dos 1000 repositórios
│   ├── raw/                   # CSVs brutos gerados pelo CK
│   └── processed/             # métricas consolidadas
├── results/                   # gráficos e tabela de correlações
├── repos/                     # clones temporários dos repositórios
├── ck/                        # ferramenta CK (compilada com Maven)
└── scripts/
    ├── coletar_repositorios.py
    ├── clonar_e_analisar.py
    ├── analisar_dados.py
    └── visualizar_resultados.py
```
