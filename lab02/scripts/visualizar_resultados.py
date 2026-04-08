#!/usr/bin/env python3
"""
Gera visualizações para as 4 questões de pesquisa:
  1. Heatmap de correlações de Spearman (visão geral)
  2. Box plots por quartil — CBO e LCOM (distribuição por faixa de processo)
  3. Barras empilhadas de proporção DIT (DIT=1 / DIT=2 / DIT≥3 por quartil)
  4. Gráfico de barras dos coeficientes ρ com destaque de significância
  5. Tabela CSV com todos os resultados

Uso:
    python visualizar_resultados.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.stats import spearmanr

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'merged_metrics.csv')
OUT_DIR   = os.path.join(os.path.dirname(__file__), '..', 'results')

QUESTOES = [
    ('RQ01\nPopularidade\n(estrelas)',  'stars',          'Estrelas'),
    ('RQ02\nMaturidade\n(idade)',        'age_years',      'Idade (anos)'),
    ('RQ03\nAtividade\n(releases)',      'releases_count', 'Nº de releases'),
    ('RQ04\nTamanho\n(LOC)',             'loc_total',      'LOC total'),
]

QUALIDADE = [
    ('CBO',  'cbo_median'),
    ('LCOM', 'lcom_median'),
]

QUALIDADE_COMPLETA = [
    ('CBO',  'cbo_median'),
    ('DIT',  'dit_median'),
    ('LCOM', 'lcom_median'),
]

QUARTIL_LABELS = ['Q1\n(menor)', 'Q2', 'Q3', 'Q4\n(maior)']
CORES_QUARTIL  = ['#4C9BE8', '#5DBB8A', '#F5A623', '#E05C5C']


# ── helpers ──────────────────────────────────────────────────────────────────

def calcular_correlacoes(df):
    linhas = []
    for rq_label, rq_col, _ in QUESTOES:
        if rq_col not in df.columns:
            continue
        for q_label, q_col in QUALIDADE_COMPLETA:
            if q_col not in df.columns:
                continue
            validos = df[[rq_col, q_col]].dropna()
            if len(validos) >= 3:
                rho, pval = spearmanr(validos[rq_col], validos[q_col])
                linhas.append({
                    'rq_label':  rq_label,
                    'rq_col':    rq_col,
                    'q_label':   q_label,
                    'q_col':     q_col,
                    'rho':       round(rho,  3),
                    'pval':      round(pval, 4),
                    'sig':       pval < 0.05,
                    'N':         len(validos),
                })
    return pd.DataFrame(linhas)


# ── Gráfico 1: heatmap ────────────────────────────────────────────────────────

def plot_heatmap(corr_df):
    rq_labels = [r[0] for r in QUESTOES]
    q_labels  = [q[0] for q in QUALIDADE_COMPLETA]

    matriz_rho = pd.DataFrame(index=rq_labels, columns=q_labels, dtype=float)
    matriz_sig = pd.DataFrame(index=rq_labels, columns=q_labels, dtype=bool)

    for _, row in corr_df.iterrows():
        matriz_rho.loc[row['rq_label'], row['q_label']] = row['rho']
        matriz_sig.loc[row['rq_label'], row['q_label']] = row['sig']

    fig, ax = plt.subplots(figsize=(7, 5))
    vmax = max(abs(matriz_rho.values.astype(float)).max(), 0.05)

    im = ax.imshow(matriz_rho.values.astype(float), cmap='RdYlGn',
                   vmin=-vmax, vmax=vmax, aspect='auto')

    ax.set_xticks(range(len(q_labels)))
    ax.set_yticks(range(len(rq_labels)))
    ax.set_xticklabels(q_labels, fontsize=11, fontweight='bold')
    ax.set_yticklabels(rq_labels, fontsize=9)

    for i in range(len(rq_labels)):
        for j in range(len(q_labels)):
            rho = float(matriz_rho.iloc[i, j])
            sig = bool(matriz_sig.iloc[i, j])
            cor_texto = 'white' if abs(rho) > vmax * 0.6 else 'black'
            marcador  = '★' if sig else ''
            ax.text(j, i, f'ρ = {rho:.3f}\n{marcador}',
                    ha='center', va='center', fontsize=10,
                    color=cor_texto, fontweight='bold' if sig else 'normal')

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label('Spearman ρ', fontsize=9)

    ax.set_title('Correlações de Spearman — Processo × Qualidade\n'
                 '(★ = significativo, p < 0,05)', fontsize=12, fontweight='bold', pad=14)

    plt.tight_layout()
    caminho = os.path.join(OUT_DIR, 'heatmap_correlacoes.png')
    plt.savefig(caminho, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Gráfico salvo: heatmap_correlacoes.png')


# ── Gráfico 2: box plots por quartil ─────────────────────────────────────────

def plot_boxplots_quartil(df):
    n_rq = len(QUESTOES)
    n_q  = len(QUALIDADE)

    # limite superior por métrica = percentil 95 global (evita que outliers esmaguem as caixas)
    ylims = {}
    for q_label, q_col in QUALIDADE:
        if q_col in df.columns:
            ylims[q_col] = (0, df[q_col].quantile(0.95) * 1.15)

    fig, axes = plt.subplots(n_rq, n_q, figsize=(14, 4 * n_rq))
    fig.suptitle('Distribuição das Métricas de Qualidade por Quartil da Métrica de Processo\n'
                 '(eixo Y limitado ao percentil 95 — outliers extremos omitidos para legibilidade)',
                 fontsize=11, fontweight='bold', y=1.01)

    for i, (rq_label, rq_col, rq_xlabel) in enumerate(QUESTOES):
        if rq_col not in df.columns:
            continue

        try:
            df['_quartil'] = pd.qcut(df[rq_col], q=4, labels=False, duplicates='drop')
        except ValueError:
            continue

        for j, (q_label, q_col) in enumerate(QUALIDADE):
            ax = axes[i][j]

            if q_col not in df.columns:
                ax.set_visible(False)
                continue

            grupos = [
                df.loc[df['_quartil'] == k, q_col].dropna().values
                for k in range(4)
            ]

            bp = ax.boxplot(
                grupos,
                patch_artist=True,
                medianprops=dict(color='black', linewidth=2),
                whiskerprops=dict(linewidth=1.2),
                capprops=dict(linewidth=1.2),
                flierprops=dict(marker='o', markersize=2, alpha=0.3,
                                markerfacecolor='gray', markeredgecolor='none'),
                showfliers=True,
            )

            for patch, cor in zip(bp['boxes'], CORES_QUARTIL):
                patch.set_facecolor(cor)
                patch.set_alpha(0.75)

            # limita o eixo Y ao p95 para que as caixas sejam visíveis
            if q_col in ylims:
                ax.set_ylim(ylims[q_col])

            tamanhos = [len(g) for g in grupos]
            ax.set_xticks(range(1, 5))
            ax.set_xticklabels(
                [f'{lb}\n(n={n})' for lb, n in zip(QUARTIL_LABELS, tamanhos)],
                fontsize=7.5,
            )

            validos = df[[rq_col, q_col]].dropna()
            rho, pval = spearmanr(validos[rq_col], validos[q_col])
            sig_str = ' ★' if pval < 0.05 else ''
            ax.set_title(f'ρ={rho:.3f}, p={pval:.3f}{sig_str}', fontsize=9)
            ax.set_xlabel(rq_xlabel, fontsize=8)
            # métrica de qualidade só na primeira linha; RQ label só na coluna 0
            if i == 0:
                ax.set_title(f'{q_label}\nρ={rho:.3f}, p={pval:.3f}{sig_str}', fontsize=9)
            if j == 0:
                ax.set_ylabel(rq_label.replace('\n', ' '), fontsize=8)
            ax.tick_params(labelsize=7)
            ax.grid(axis='y', linestyle='--', alpha=0.3)

    df.drop(columns=['_quartil'], inplace=True, errors='ignore')
    plt.tight_layout()
    caminho = os.path.join(OUT_DIR, 'boxplots_por_quartil.png')
    plt.savefig(caminho, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Gráfico salvo: boxplots_por_quartil.png')


# ── Gráfico 3: DIT — barras empilhadas de proporção por quartil ──────────────

def plot_dit_proporcao(df):
    """
    DIT tem 91 % dos repos com mediana = 1,0 — boxplot e violin ficam vazios.
    Mostramos a proporção de repos com DIT=1 / DIT=2 / DIT≥3 por quartil
    de cada métrica de processo. Isso revela se projetos maiores/mais ativos
    tendem a ter herança mais profunda.
    """
    def categorizar_dit(val):
        if val <= 1:
            return 'DIT = 1'
        elif val <= 2:
            return 'DIT = 2'
        else:
            return 'DIT ≥ 3'

    COR_DIT = {'DIT = 1': '#4C9BE8', 'DIT = 2': '#F5A623', 'DIT ≥ 3': '#E05C5C'}
    categorias = ['DIT = 1', 'DIT = 2', 'DIT ≥ 3']

    fig, axes = plt.subplots(1, len(QUESTOES), figsize=(16, 4), sharey=True)
    fig.suptitle('Distribuição de DIT por Quartil da Métrica de Processo\n'
                 '(proporção de repositórios por categoria de profundidade de herança)',
                 fontsize=11, fontweight='bold')

    df['_dit_cat'] = df['dit_median'].apply(categorizar_dit)

    for ax, (rq_label, rq_col, rq_xlabel) in zip(axes, QUESTOES):
        if rq_col not in df.columns:
            ax.set_visible(False)
            continue

        try:
            df['_quartil'] = pd.qcut(df[rq_col], q=4, labels=False, duplicates='drop')
        except ValueError:
            continue

        # proporção de cada categoria DIT por quartil
        tabela = (df.groupby(['_quartil', '_dit_cat'])
                    .size()
                    .unstack(fill_value=0))
        # garante todas as categorias e todos os quartis (0-3)
        for cat in categorias:
            if cat not in tabela.columns:
                tabela[cat] = 0
        tabela = tabela.reindex(range(4), fill_value=0)[categorias]
        tabela_pct = tabela.div(tabela.sum(axis=1).replace(0, 1), axis=0) * 100

        bottom = np.zeros(4)
        tamanhos = tabela.sum(axis=1).values

        for cat in categorias:
            vals = tabela_pct[cat].values
            ax.bar(range(4), vals, bottom=bottom,
                   color=COR_DIT[cat], label=cat, edgecolor='white', linewidth=0.5)
            # rótulo percentual só se a fatia for visível (>= 3 %)
            for xi, (v, b) in enumerate(zip(vals, bottom)):
                if v >= 3:
                    ax.text(xi, b + v / 2, f'{v:.0f}%',
                            ha='center', va='center', fontsize=7.5,
                            color='white', fontweight='bold')
            bottom += vals

        rho, pval = spearmanr(df[rq_col].dropna(),
                               df.loc[df[rq_col].notna(), 'dit_median'])
        sig_str = ' ★' if pval < 0.05 else ''
        rq_titulo = rq_label.replace('\n', ' ')
        ax.set_title(f'{rq_titulo}\nρ={rho:.3f}, p={pval:.3f}{sig_str}', fontsize=9)
        ax.set_xticks(range(4))
        ax.set_xticklabels(
            [f'{lb}\n(n={n})' for lb, n in zip(QUARTIL_LABELS, tamanhos)],
            fontsize=7.5,
        )
        ax.set_xlabel(rq_xlabel, fontsize=8)
        ax.set_ylim(0, 105)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        if ax == axes[0]:
            ax.set_ylabel('% de repositórios', fontsize=9)

    df.drop(columns=['_quartil', '_dit_cat'], inplace=True, errors='ignore')

    # legenda única
    handles = [mpatches.Patch(facecolor=COR_DIT[c], label=c) for c in categorias]
    fig.legend(handles=handles, loc='lower center', ncol=3,
               fontsize=9, frameon=True, bbox_to_anchor=(0.5, -0.08))

    plt.tight_layout()
    caminho = os.path.join(OUT_DIR, 'dit_proporcao_quartil.png')
    plt.savefig(caminho, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Gráfico salvo: dit_proporcao_quartil.png')


# ── Gráfico 4: barras dos coeficientes ρ ─────────────────────────────────────

def plot_barras_rho(corr_df):
    fig, axes = plt.subplots(1, len(QUALIDADE_COMPLETA), figsize=(13, 5), sharey=True)
    fig.suptitle('Coeficientes de Correlação de Spearman (ρ) por Questão de Pesquisa\n'
                 '(barras hachuradas = não significativo, p ≥ 0,05)',
                 fontsize=12, fontweight='bold')

    COR_SIM = '#2E86AB'
    COR_NAO = '#AECDE0'

    rq_labels_curtos = ['RQ01\n(estrelas)', 'RQ02\n(idade)', 'RQ03\n(releases)', 'RQ04\n(LOC)']

    for ax, (q_label, q_col) in zip(axes, QUALIDADE_COMPLETA):
        sub = corr_df[corr_df['q_label'] == q_label].reset_index(drop=True)

        cores    = [COR_SIM if s else COR_NAO for s in sub['sig']]
        hatches  = ['' if s else '///'        for s in sub['sig']]
        barras   = ax.bar(range(len(sub)), sub['rho'], color=cores,
                          edgecolor='black', linewidth=0.8)

        for bar, hatch, rho, sig in zip(barras, hatches, sub['rho'], sub['sig']):
            bar.set_hatch(hatch)
            offset = 0.005 if rho >= 0 else -0.012
            ax.text(bar.get_x() + bar.get_width() / 2,
                    rho + offset,
                    f'{rho:.3f}',
                    ha='center', va='bottom' if rho >= 0 else 'top',
                    fontsize=8.5, fontweight='bold' if sig else 'normal')

        ax.axhline(0, color='black', linewidth=0.8)
        ax.set_xticks(range(len(sub)))
        ax.set_xticklabels(rq_labels_curtos[:len(sub)], fontsize=8)
        ax.set_title(q_label, fontsize=11, fontweight='bold')
        ax.set_ylim(
            min(sub['rho'].min() - 0.05, -0.05),
            max(sub['rho'].max() + 0.07,  0.07),
        )
        ax.set_ylabel('ρ de Spearman' if ax == axes[0] else '')
        ax.tick_params(labelsize=8)
        ax.grid(axis='y', linestyle='--', alpha=0.4)

    # legenda global
    patch_sim = mpatches.Patch(facecolor=COR_SIM, edgecolor='black', label='Significativo (p < 0,05)')
    patch_nao = mpatches.Patch(facecolor=COR_NAO, edgecolor='black', hatch='///', label='Não significativo')
    fig.legend(handles=[patch_sim, patch_nao], loc='lower center',
               ncol=2, fontsize=9, frameon=True, bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout()
    caminho = os.path.join(OUT_DIR, 'barras_rho.png')
    plt.savefig(caminho, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Gráfico salvo: barras_rho.png')


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DATA_FILE):
        print(f'[erro] Arquivo não encontrado: {DATA_FILE}')
        print('Execute primeiro: python analisar_dados.py')
        return

    df = pd.read_csv(DATA_FILE)
    print(f'Dados carregados: {len(df)} repositórios')

    os.makedirs(OUT_DIR, exist_ok=True)

    corr_df = calcular_correlacoes(df)

    print('\n[1/4] Gerando heatmap de correlações...')
    plot_heatmap(corr_df)

    print('[2/4] Gerando box plots por quartil (CBO e LCOM)...')
    plot_boxplots_quartil(df)

    print('[3/4] Gerando gráfico de proporção DIT por quartil...')
    plot_dit_proporcao(df)

    print('[4/4] Gerando gráfico de barras dos coeficientes ρ...')
    plot_barras_rho(corr_df)

    # tabela CSV
    tabela = corr_df[['rq_label', 'q_label', 'rho', 'pval', 'sig', 'N']].copy()
    tabela.columns = ['Questão', 'Métrica de qualidade', 'ρ (rho)', 'p-value',
                      'Significativo (p<0.05)', 'N']
    tabela['Significativo (p<0.05)'] = tabela['Significativo (p<0.05)'].map({True: 'sim', False: 'não'})
    tabela['Questão'] = tabela['Questão'].str.replace('\n', ' ')
    saida_csv = os.path.join(OUT_DIR, 'correlacoes_spearman.csv')
    tabela.to_csv(saida_csv, index=False)
    print(f'\nTabela salva em: {saida_csv}')
    print(tabela.to_string(index=False))
    print(f'\nPronto! Gráficos salvos em: {OUT_DIR}')


if __name__ == '__main__':
    main()
