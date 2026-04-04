#!/usr/bin/env python3
"""
Gera gráficos de correlação para as 4 questões de pesquisa e
calcula o teste de Spearman para cada par (métrica de processo x qualidade).

Uso:
    python visualizar_resultados.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.stats import spearmanr

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'merged_metrics.csv')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')

# Questões de pesquisa: (nome legível, coluna no CSV)
QUESTOES = [
    ('RQ01 - Popularidade (estrelas)', 'stars'),
    ('RQ02 - Maturidade (idade em anos)', 'age_years'),
    ('RQ03 - Atividade (releases)', 'releases_count'),
    ('RQ04 - Tamanho (LOC)', 'loc_total'),
]

# Métricas de qualidade que vêm do CK
QUALIDADE = [
    ('CBO (mediana)', 'cbo_median'),
    ('DIT (mediana)', 'dit_median'),
    ('LCOM (mediana)', 'lcom_median'),
]


def gerar_scatter(ax, x, y, xlabel, ylabel, title):
    """Plota um scatter e adiciona o resultado do Spearman no título."""
    # remove linhas com NaN
    validos = pd.DataFrame({'x': x, 'y': y}).dropna()

    if len(validos) < 3:
        ax.text(0.5, 0.5, 'Dados insuficientes', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlabel, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        return

    rho, pval = spearmanr(validos['x'], validos['y'])

    ax.scatter(validos['x'], validos['y'], alpha=0.6, edgecolors='k', linewidths=0.3, s=40)
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=8)

    # exibe rho e p-value no título
    significancia = '*' if pval < 0.05 else ''
    ax.set_title(f"{title}\nSpearman ρ={rho:.3f}, p={pval:.3f}{significancia}", fontsize=9)
    ax.tick_params(labelsize=7)


def main():
    if not os.path.exists(DATA_FILE):
        print(f"[erro] Arquivo não encontrado: {DATA_FILE}")
        print("Execute primeiro: python analisar_dados.py")
        return

    df = pd.read_csv(DATA_FILE)
    print(f"Dados carregados: {len(df)} repositórios")
    print("Colunas disponíveis:", df.columns.tolist())

    os.makedirs(OUT_DIR, exist_ok=True)

    # uma figura por questão de pesquisa, com 3 subplots (um por métrica de qualidade)
    for rq_label, rq_col in QUESTOES:
        if rq_col not in df.columns:
            print(f"[aviso] Coluna '{rq_col}' não encontrada, pulando {rq_label}")
            continue

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(rq_label, fontsize=13, fontweight='bold')

        for ax, (q_label, q_col) in zip(axes, QUALIDADE):
            if q_col not in df.columns:
                ax.set_visible(False)
                continue

            gerar_scatter(
                ax,
                x=df[rq_col],
                y=df[q_col],
                xlabel=rq_label.split(' - ')[1],
                ylabel=q_label,
                title=q_label,
            )

        plt.tight_layout()
        nome_arquivo = f"{rq_col}_vs_qualidade.png"
        plt.savefig(os.path.join(OUT_DIR, nome_arquivo), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Gráfico salvo: {nome_arquivo}")

    # tabela resumo de todas as correlações
    print("\n--- Resumo das Correlações (Spearman) ---")
    linhas = []
    for rq_label, rq_col in QUESTOES:
        if rq_col not in df.columns:
            continue
        for q_label, q_col in QUALIDADE:
            if q_col not in df.columns:
                continue
            validos = df[[rq_col, q_col]].dropna()
            if len(validos) >= 3:
                rho, pval = spearmanr(validos[rq_col], validos[q_col])
                sig = 'sim' if pval < 0.05 else 'não'
                linhas.append({
                    'Questão': rq_label,
                    'Métrica de qualidade': q_label,
                    'ρ (rho)': round(rho, 3),
                    'p-value': round(pval, 4),
                    'Significativo (p<0.05)': sig,
                    'N': len(validos),
                })

    if linhas:
        tabela = pd.DataFrame(linhas)
        print(tabela.to_string(index=False))
        tabela.to_csv(os.path.join(OUT_DIR, 'correlacoes_spearman.csv'), index=False)
        print(f"\nTabela salva em: results/correlacoes_spearman.csv")
    else:
        print("Dados insuficientes para calcular correlações.")

    print("\nPronto! Gráficos salvos em:", OUT_DIR)


if __name__ == '__main__':
    main()
