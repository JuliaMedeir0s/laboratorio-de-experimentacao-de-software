import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timezone


def repo_root() -> Path:
    # Assume .../lab01/src/analise.py
    return Path(__file__).resolve().parents[2]


def main():
    root = repo_root()

    # Ajuste se o seu CSV estiver em outro lugar
    in_csv = root / "lab01" / "data" / "processed" / "top_1000.csv"

    out_tables = root / "lab01" / "outputs" / "tabelas"
    out_graphs = root / "lab01" / "outputs" / "graficos"
    out_tables.mkdir(parents=True, exist_ok=True)
    out_graphs.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_csv)

    # Datas
    created = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    pushed = pd.to_datetime(df["pushed_at"], utc=True, errors="coerce")
    now = datetime.now(timezone.utc)

    # Métricas derivadas
    df["repo_age_days"] = (now - created).dt.days
    df["repo_age_years"] = df["repo_age_days"] / 365.25
    df["days_since_push"] = (now - pushed).dt.days

    total = df["issues_total"].fillna(0)
    closed = df["issues_closed_total"].fillna(0)
    df["issues_closed_ratio"] = (closed / total.where(total != 0, pd.NA)).fillna(0).clip(0, 1)

    df["primary_language"] = df["primary_language"].fillna("Unknown").replace({"": "Unknown"})

    # =========================
    # TABELAS (para o relatório)
    # =========================

    tabela_mediana = pd.DataFrame([{
        "idade_mediana_dias": float(df["repo_age_days"].median()),
        "idade_mediana_anos": float(df["repo_age_years"].median()),
        "prs_merged_mediana": float(df["prs_merged_total"].median()),
        "releases_mediana": float(df["releases_total"].median()),
        "dias_desde_push_mediana": float(df["days_since_push"].median()),
        "ratio_issues_fechadas_mediana": float(df["issues_closed_ratio"].median()),
    }])
    tabela_mediana.to_csv(out_tables / "tabela_mediana_rqs.csv", index=False)

    lang_counts = df["primary_language"].value_counts()
    tabela_lang = pd.DataFrame({
        "linguagem": lang_counts.index,
        "count": lang_counts.values,
        "percentual": (lang_counts.values / len(df)) * 100,
    })
    tabela_lang.head(20).to_csv(out_tables / "tabela_linguagens_top20.csv", index=False)

    metrics_cols = ["repo_age_days", "prs_merged_total", "releases_total", "days_since_push", "issues_closed_ratio"]
    desc = df[metrics_cols].describe(percentiles=[0.25, 0.5, 0.75]).T
    desc = desc.rename(columns={"50%": "median", "25%": "p25", "75%": "p75"})
    desc.to_csv(out_tables / "tabela_stats_descritivas.csv")

    # =========
    # GRÁFICOS
    # =========

    # 1) Barras: Top 10 linguagens
    plt.figure()
    lang_counts.head(10).sort_values().plot(kind="barh")
    plt.title("Top 10 linguagens (contagem nos 1000 repos)")
    plt.xlabel("Quantidade")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_barras_top10_linguagens.png", dpi=200)
    plt.close()

    # 2) Histograma: idade (dias)
    plt.figure()
    df["repo_age_days"].dropna().plot(kind="hist", bins=30)
    plt.title("Distribuição da idade dos repositórios (dias)")
    plt.xlabel("Dias")
    plt.ylabel("Frequência")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_histograma_idade.png", dpi=200)
    plt.close()

    # 3) Histograma: dias desde push (zoom até 365)
    plt.figure()
    df["days_since_push"].dropna().clip(upper=365).plot(kind="hist", bins=30)
    plt.title("Dias desde o último push (até 365 dias)")
    plt.xlabel("Dias (cortado em 365)")
    plt.ylabel("Frequência")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_histograma_dias_desde_push_zoom365.png", dpi=200)
    plt.close()

    # 4) Histograma: dias desde push (escala log)
    plt.figure()
    # Para log no eixo x, não pode ter 0. Usa no mínimo 1 dia.
    ds = df["days_since_push"].dropna().clip(lower=1)
    ds.plot(kind="hist", bins=30)
    plt.xscale("log")
    plt.title("Dias desde o último push (escala log)")
    plt.xlabel("Dias (log)")
    plt.ylabel("Frequência")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_histograma_dias_desde_push_log.png", dpi=200)
    plt.close()

    # 5) Boxplot: PRs MERGED (sem outliers)
    plt.figure()
    plt.boxplot(df["prs_merged_total"].dropna(), showfliers=False)
    plt.title("PRs aceitas (MERGED) — sem outliers")
    plt.ylabel("Total de PRs MERGED")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_boxplot_prs_merged_sem_outliers.png", dpi=200)
    plt.close()

    # 6) Boxplot: PRs MERGED (escala log)
    plt.figure()
    plt.boxplot(df["prs_merged_total"].dropna())
    plt.yscale("log")
    plt.title("PRs aceitas (MERGED) — escala log")
    plt.ylabel("Total de PRs MERGED (log)")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_boxplot_prs_merged_log.png", dpi=200)
    plt.close()

    # 7) Scatter: Stars vs PRs MERGED (log-log + transparência)
    plt.figure()
    x = df["stars"].dropna().clip(lower=1)
    y = df["prs_merged_total"].dropna().clip(lower=1)
    # alinhar tamanhos (evita NaN em uma e valor em outra)
    tmp = pd.DataFrame({"stars": x, "prs": y}).dropna()
    plt.scatter(tmp["stars"], tmp["prs"], alpha=0.3, s=10)
    plt.xscale("log")
    plt.yscale("log")
    plt.title("Stars vs PRs MERGED (log-log)")
    plt.xlabel("Stars (log)")
    plt.ylabel("PRs MERGED (log)")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_dispersaostars_prs_loglog.png", dpi=200)
    plt.close()

    # 8) Pizza: Top 8 linguagens + Outras
    top = lang_counts.head(8)
    others = lang_counts.iloc[8:].sum()
    pie_series = pd.concat([top, pd.Series({"Outras": others})])
    plt.figure()
    pie_series.plot(kind="pie", autopct="%1.1f%%")
    plt.title("Percentual por linguagem (Top 8 + Outras)")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_pizza_linguagens_top8.png", dpi=200)
    plt.close()

    # 9) Heatmap de correlação (com colorbar)
    corr_cols = ["stars", "repo_age_days", "releases_total", "prs_merged_total",
                 "issues_total", "issues_closed_ratio", "days_since_push"]
    corr = df[corr_cols].corr(numeric_only=True)

    plt.figure()
    plt.imshow(corr.values)
    plt.colorbar()
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr.index)), corr.index)
    plt.title("Heatmap de correlação (métricas numéricas)")
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_heatmap_correlacao.png", dpi=200)
    plt.close()

    print("OK! Tabelas em:", out_tables)
    print("OK! Gráficos em:", out_graphs)
    
    # ===== Gráfico de linha: mediana por ano de criação =====
    df["created_year"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce").dt.year

    # escolha a métrica para a linha (troque aqui se quiser)
    metric_line = "prs_merged_total"  # ou "releases_total" ou "issues_closed_ratio"

    line = (
        df.dropna(subset=["created_year", metric_line])
        .groupby("created_year")[metric_line]
        .median()
        .sort_index()
    )

    plt.figure()
    line.plot(kind="line", marker="o")
    plt.title(f"Mediana de {metric_line} por ano de criação do repositório")
    plt.xlabel("Ano de criação")
    plt.ylabel(f"Mediana de {metric_line}")
    plt.tight_layout()
    plt.savefig(out_graphs / f"grafico_linha_mediana_{metric_line}_por_ano.png", dpi=200)
    plt.close()
    
    # ===== Histogramas sobrepostos: dias desde push por linguagem (Top 3) =====
    top_langs = df["primary_language"].value_counts().head(3).index.tolist()
    
    plt.figure()
    for lang in top_langs:
        subset = df.loc[df["primary_language"] == lang, "days_since_push"].dropna()
        # corta em 365 para o zoom ficar legível
        subset = subset.clip(upper=365)
        plt.hist(subset, bins=30, alpha=0.4, label=lang)
    
    plt.title("Dias desde o último push (até 365) — comparação Top 3 linguagens")
    plt.xlabel("Dias (cortado em 365)")
    plt.ylabel("Frequência")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_graphs / "grafico_sobreposto_hist_dias_desde_push_top3_langs.png", dpi=200)
    plt.close()


if __name__ == "__main__":
    main()
