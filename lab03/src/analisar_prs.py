from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr


METRICS = [
    "files_changed",
    "lines_added",
    "lines_removed",
    "analysis_time_hours",
    "body_length",
    "participants_count",
    "comments_count",
]


@dataclass(frozen=True)
class Paths:
    root: Path
    input_csv: Path
    out_dir: Path

    @property
    def tables_dir(self) -> Path:
        return self.out_dir / "tabelas"

    @property
    def plots_dir(self) -> Path:
        return self.out_dir / "graficos"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_dirs(paths: Paths) -> None:
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.plots_dir.mkdir(parents=True, exist_ok=True)


def _load_dataset(input_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(input_csv)

    expected = {
        "repo",
        "pr_number",
        "title",
        "status",
        "created_at",
        "closed_at",
        "merged_at",
        "analysis_time_hours",
        "files_changed",
        "lines_added",
        "lines_removed",
        "body_length",
        "participants_count",
        "comments_count",
        "reviews_count",
    }
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"CSV está faltando colunas esperadas: {sorted(missing)}")

    df["status_bin"] = df["status"].map({"MERGED": 1, "CLOSED": 0})
    if df["status_bin"].isna().any():
        bad = sorted(df.loc[df["status_bin"].isna(), "status"].unique().tolist())
        raise ValueError(f"Status inesperado encontrado no CSV: {bad}")

    numeric_cols = METRICS + ["reviews_count", "status_bin"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _spearman_table(df: pd.DataFrame, *, y: str) -> pd.DataFrame:
    rows: list[dict] = []

    for x in METRICS:
        sub = df[[x, y]].dropna()
        if len(sub) < 3:
            rho, p = float("nan"), float("nan")
            n = len(sub)
        else:
            res = spearmanr(sub[x], sub[y])
            rho, p = float(res.statistic), float(res.pvalue)
            n = len(sub)

        rows.append(
            {
                "x": x,
                "y": y,
                "n": n,
                "spearman_rho": round(rho, 6) if pd.notna(rho) else rho,
                "p_value": round(p, 6) if pd.notna(p) else p,
            }
        )

    out = pd.DataFrame(rows)
    out = out.sort_values(by="spearman_rho", ascending=False, na_position="last").reset_index(drop=True)
    return out


def _medians_by_status(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("status", dropna=False)

    rows: list[dict] = []
    for status, g in grouped:
        row = {
            "status": status,
            "n": int(len(g)),
        }
        for col in METRICS + ["reviews_count"]:
            row[f"median_{col}"] = float(g[col].median())
        rows.append(row)

    out = pd.DataFrame(rows)
    out = out.sort_values(by="status", ascending=False).reset_index(drop=True)
    return out


def _summary_counts(df: pd.DataFrame) -> pd.DataFrame:
    counts = (
        df["status"]
        .value_counts(dropna=False)
        .rename_axis("status")
        .reset_index(name="count")
        .sort_values(by="status", ascending=False)
        .reset_index(drop=True)
    )
    counts.loc[:, "percent"] = (counts["count"] / len(df) * 100).round(2)
    return counts


def _quartiles_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resumo por quartis das métricas independentes.

    Para cada métrica em METRICS, divide a amostra em quartis (Q1..Q4) e
    calcula estatísticas de interesse para interpretação:
    - taxa de MERGE (média de status_bin)
    - mediana de reviews_count
    - mediana de analysis_time_hours
    - min/max da própria métrica no quartil (para dar noção da faixa)

    Observação: usa qcut com duplicates='drop' para lidar com muitas repetições.
    """

    rows: list[dict] = []

    for metric in METRICS:
        sub = df[[metric, "status_bin", "reviews_count", "analysis_time_hours"]].dropna().copy()
        if len(sub) < 10:
            continue

        try:
            sub["quartil"] = pd.qcut(
                sub[metric],
                q=4,
                labels=["Q1", "Q2", "Q3", "Q4"],
                duplicates="drop",
            )
        except ValueError:
            # Pode acontecer se a coluna tiver poucos valores distintos.
            continue

        grouped = sub.groupby("quartil", dropna=True)
        for quartil, g in grouped:
            rows.append(
                {
                    "metric": metric,
                    "quartil": str(quartil),
                    "n": int(len(g)),
                    "merge_rate": round(float(g["status_bin"].mean()), 6),
                    "median_reviews_count": float(g["reviews_count"].median()),
                    "median_analysis_time_hours": float(g["analysis_time_hours"].median()),
                    "metric_min": float(g[metric].min()),
                    "metric_max": float(g[metric].max()),
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    quartil_order = pd.CategoricalDtype(categories=["Q1", "Q2", "Q3", "Q4"], ordered=True)
    out["quartil"] = out["quartil"].astype(quartil_order)
    out = out.sort_values(by=["metric", "quartil"]).reset_index(drop=True)
    return out


def _write_df(df: pd.DataFrame, csv_path: Path, md_path: Path) -> None:
    df.to_csv(csv_path, index=False)

    # to_markdown requer tabulate (já está no requirements.txt)
    md_table = df.to_markdown(index=False)
    md_path.write_text(md_table + "\n", encoding="utf-8")


def _plots(df: pd.DataFrame, plots_dir: Path) -> None:
    # Importa libs de plot aqui para evitar custo/erro caso usuário só queira tabelas
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme()

    def _clip_p99(series: pd.Series) -> pd.Series:
        # Clipping para reduzir a influência de outliers no eixo (somente visual).
        # Usa quantil 0.99 para manter a maior parte da distribuição visível.
        q = series.quantile(0.99)
        return series.clip(upper=q)

    # Distribuição por status: boxen (melhor para muitos dados) + violin
    for metric in METRICS + ["reviews_count"]:
        clipped = df.copy()
        clipped[metric] = _clip_p99(clipped[metric])

        plt.figure(figsize=(7, 4))
        sns.boxenplot(data=clipped, x="status", y=metric, order=["CLOSED", "MERGED"])
        plt.title(f"{metric} por status (boxen, p99 clip)")
        plt.tight_layout()
        plt.savefig(plots_dir / f"boxen_{metric}_por_status_p99.png", dpi=200)
        plt.close()

        plt.figure(figsize=(7, 4))
        sns.violinplot(
            data=clipped,
            x="status",
            y=metric,
            order=["CLOSED", "MERGED"],
            cut=0,
            inner="quartile",
        )
        plt.title(f"{metric} por status (violin, p99 clip)")
        plt.tight_layout()
        plt.savefig(plots_dir / f"violin_{metric}_por_status_p99.png", dpi=200)
        plt.close()

    # Relação reviews_count vs métricas: 2D histogram/hexbin em escala log1p
    # (evita overplotting e separa melhor regiões densas)
    for metric in METRICS:
        sub = df[[metric, "reviews_count"]].dropna().copy()
        sub[metric] = _clip_p99(sub[metric])
        sub["reviews_count"] = _clip_p99(sub["reviews_count"])

        x = np.log1p(sub[metric].to_numpy())
        y = np.log1p(sub["reviews_count"].to_numpy())

        plt.figure(figsize=(7, 4))
        plt.hexbin(x, y, gridsize=45, bins="log", mincnt=1)
        plt.colorbar(label="log10(contagem)")
        plt.title(f"log1p(reviews_count) vs log1p({metric}) (hexbin, p99 clip)")
        plt.xlabel(f"log1p({metric})")
        plt.ylabel("log1p(reviews_count)")
        plt.tight_layout()
        plt.savefig(plots_dir / f"hexbin_log1p_reviews_vs_{metric}_p99.png", dpi=200)
        plt.close()

        plt.figure(figsize=(7, 4))
        sns.histplot(x=x, y=y, bins=50, cbar=True)
        plt.title(f"log1p(reviews_count) vs log1p({metric}) (hist2d, p99 clip)")
        plt.xlabel(f"log1p({metric})")
        plt.ylabel("log1p(reviews_count)")
        plt.tight_layout()
        plt.savefig(plots_dir / f"hist2d_log1p_reviews_vs_{metric}_p99.png", dpi=200)
        plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sprint 3 — análise estatística do dataset de PRs")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Caminho do CSV consolidado (padrão: data/processed/prs.csv)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Diretório de outputs (padrão: outputs/)",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Não gera gráficos (somente tabelas)",
    )
    args = parser.parse_args()

    root = _repo_root()
    input_csv = Path(args.input) if args.input else (root / "data" / "processed" / "prs.csv")
    out_dir = Path(args.out) if args.out else (root / "outputs")

    paths = Paths(root=root, input_csv=input_csv, out_dir=out_dir)
    _ensure_dirs(paths)

    df = _load_dataset(paths.input_csv)

    # Tabelas principais
    counts = _summary_counts(df)
    medians = _medians_by_status(df)
    spearman_status = _spearman_table(df, y="status_bin")
    spearman_reviews = _spearman_table(df, y="reviews_count")
    quartiles = _quartiles_summary(df)

    _write_df(counts, paths.tables_dir / "contagem_status.csv", paths.tables_dir / "contagem_status.md")
    _write_df(medians, paths.tables_dir / "medianas_por_status.csv", paths.tables_dir / "medianas_por_status.md")
    _write_df(
        spearman_status,
        paths.tables_dir / "spearman_status.csv",
        paths.tables_dir / "spearman_status.md",
    )
    _write_df(
        spearman_reviews,
        paths.tables_dir / "spearman_reviews.csv",
        paths.tables_dir / "spearman_reviews.md",
    )

    if not quartiles.empty:
        _write_df(
            quartiles,
            paths.tables_dir / "quartis_resumo.csv",
            paths.tables_dir / "quartis_resumo.md",
        )

    if not args.skip_plots:
        _plots(df, paths.plots_dir)

    merged = int((df["status"] == "MERGED").sum())
    closed = int((df["status"] == "CLOSED").sum())

    print("Análise concluída.")
    print(f"Dataset: {paths.input_csv}")
    print(f"Total PRs: {len(df)} | MERGED: {merged} | CLOSED: {closed}")
    print(f"Tabelas: {paths.tables_dir}")
    print(f"Gráficos: {paths.plots_dir}")


if __name__ == "__main__":
    main()
