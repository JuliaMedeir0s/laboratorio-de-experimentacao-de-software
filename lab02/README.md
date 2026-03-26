# Lab 02 — Qualidade de sistemas Java

Este diretório contém os scripts e artefatos do Laboratório 02.

## Sprint 1 (Lab02S01)

Requisitos:

1. Lista dos **1.000** repositórios Java mais populares do GitHub.
2. Script de automação de **clone + coleta de métricas** (CK).
3. Um arquivo `.csv` com o resultado das medições de **1** repositório.

### Pré-requisitos

- Python (recomendado usar `venv`)
- Git
- Java (para executar o CK)
- Maven (para compilar o CK na primeira execução)

### Instalação (Python)

```bash
python -m pip install -r requirements.txt
```

### Configurar token do GitHub

Crie `lab02/.env` baseado em `lab02/.env.example` e preencha `GITHUB_TOKEN`.

### Gerar a lista dos 1000 repositórios (repos.csv)

Executar a partir do diretório `lab02/`:

```bash
python scripts/coletar_repositorios.py --count 1000 --output data/repos.csv
```

Saída esperada:

- `lab02/data/repos.csv`

### Gerar uma amostra de métricas CK (1 repositório)

```bash
python scripts/clonar_e_analisar.py --repo apache/commons-lang --output data/sample/
```

Saída esperada:

- `lab02/data/sample/*_class.csv` (e possivelmente outros CSVs do CK)

## Observação sobre paths

Os scripts resolvem caminhos relativos ao diretório `lab02/` (independente do diretório atual em que o comando é executado).

