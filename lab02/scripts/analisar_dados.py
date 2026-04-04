#!/usr/bin/env python3
"""
Script para analisar e sumarizar os dados coletados pelo CK,
mesclando com as métricas coletadas do GitHub.

Uso:
    python analisar_dados.py
"""

import os
import re
import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
REPOS_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'repos.csv')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')


def extrair_nome_repo(filename, repos_conhecidos):
    # remove o sufixo "_class.csv" pra ficar só com a parte do nome do repo
    stem = re.sub(r'_class\.csv$', '', filename)

    # o script de clonagem salva como "Owner_RepoName" ou "Owner--RepoName"
    candidatos = [
        stem.replace('--', '/'),
        re.sub(r'_', '/', stem, count=1),
    ]

    for c in candidatos:
        if c in repos_conhecidos:
            return c

    # fallback case-insensitive
    stem_norm = stem.lower().replace('--', '/').replace('_', '/')
    for nome in repos_conhecidos:
        if nome.lower() == stem_norm:
            return nome

    return None


def carregar_ck(repos_lookup):
    frames = []

    for arquivo in sorted(os.listdir(RAW_DIR)):
        if not arquivo.endswith('_class.csv'):
            continue

        repo = extrair_nome_repo(arquivo, repos_lookup)
        if repo is None:
            print(f"[aviso] Não consegui mapear '{arquivo}' a nenhum repositório, pulando.")
            continue

        caminho = os.path.join(RAW_DIR, arquivo)
        df = pd.read_csv(caminho)
        df['repo_name'] = repo
        frames.append(df)
        print(f"  carregado: {arquivo} → {repo} ({len(df)} classes)")

    if not frames:
        print("[erro] Nenhum arquivo _class.csv encontrado.")
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def resumo_por_repo(ck_df):
    # métricas de qualidade que precisamos (CBO, DIT, LCOM)
    metricas = [c for c in ['cbo', 'dit', 'lcom'] if c in ck_df.columns]

    agg = {m: ['median', 'mean', 'std'] for m in metricas}

    # LOC total do repositório = soma das linhas de código de todas as classes
    if 'loc' in ck_df.columns:
        agg['loc'] = ['sum']

    resumo = ck_df.groupby('repo_name').agg(agg)
    # achata colunas multi-nível: "cbo_median", "dit_mean", etc.
    resumo.columns = ['_'.join(col) for col in resumo.columns]
    resumo = resumo.rename(columns={'loc_sum': 'loc_total'})
    resumo = resumo.reset_index().round(3)
    return resumo


def mesclar_com_github(resumo_ck, repos_df):
    # pega só as colunas de processo que vamos usar nas análises
    colunas = ['name', 'stars', 'forks', 'releases_count', 'age_years', 'rank']
    colunas = [c for c in colunas if c in repos_df.columns]

    merged = resumo_ck.merge(
        repos_df[colunas],
        left_on='repo_name',
        right_on='name',
        how='left'
    )
    merged = merged.drop(columns=['name'], errors='ignore')
    return merged


def main():
    print("Carregando lista de repositórios...")
    repos_df = pd.read_csv(REPOS_CSV)
    repos_lookup = set(repos_df['name'])

    print(f"Carregando dados CK de {RAW_DIR}...")
    ck_df = carregar_ck(repos_lookup)
    if ck_df.empty:
        return

    print("Calculando resumo por repositório...")
    resumo = resumo_por_repo(ck_df)

    print("Mesclando com métricas do GitHub...")
    final = mesclar_com_github(resumo, repos_df)

    os.makedirs(OUT_DIR, exist_ok=True)

    saida = os.path.join(OUT_DIR, 'merged_metrics.csv')
    final.to_csv(saida, index=False)
    print(f"\nSalvo em: {saida}")
    print(final.to_string(index=False))

    stats = final.select_dtypes(include='number').describe().round(3)
    stats.to_csv(os.path.join(OUT_DIR, 'overall_statistics.csv'))
    print("\nEstatísticas descritivas salvas em overall_statistics.csv")


if __name__ == '__main__':
    main()
