import argparse
from pathlib import Path
import os

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--figdir", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    csv_path = Path(args.csv)
    figdir = Path(args.figdir)
    out_md = Path(args.out_md)
    figdir.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")
    df["size_bytes"] = pd.to_numeric(df["size_bytes"], errors="coerce")
    df["ok"] = pd.to_numeric(df["ok"], errors="coerce").fillna(0).astype(int)
    df_ok = df[df["ok"] == 1].copy()

    # Tables
    table_latency = (
        df_ok.groupby("treatment")["latency_ms"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .reset_index()
        .rename(columns={"count": "n"})
    )

    table_size = (
        df_ok.groupby("treatment")["size_bytes"]
        .agg(["count", "mean", "median", "std", "min", "max"])
        .reset_index()
        .rename(columns={"count": "n"})
    )

    # Figures
    sns.set_theme(style="whitegrid")

    latency_png = figdir / "dashboard_latency.png"
    plt.figure(figsize=(10, 5))
    sns.violinplot(data=df_ok, x="treatment", y="latency_ms", inner="quartile", cut=0)
    plt.title("Dashboard — Latência por tratamento")
    plt.tight_layout()
    plt.savefig(latency_png, dpi=200)
    plt.close()

    size_png = figdir / "dashboard_size.png"
    plt.figure(figsize=(10, 5))
    sns.violinplot(data=df_ok, x="treatment", y="size_bytes", inner="quartile", cut=0)
    plt.title("Dashboard — Tamanho (bytes) por tratamento")
    plt.tight_layout()
    plt.savefig(size_png, dpi=200)
    plt.close()

    # Markdown dashboard
    latency_rel = Path(os.path.relpath(latency_png, start=out_md.parent)).as_posix()
    size_rel = Path(os.path.relpath(size_png, start=out_md.parent)).as_posix()

    lines = []
    lines.append("# Lab05S03 — Dashboard (Visualização de Resultados)\n")
    lines.append("Este dashboard resume as diferenças entre REST e GraphQL nas métricas de **latência** (RQ1) e **tamanho da resposta** (RQ2).\n")

    lines.append("## Tabela — Latência (ms)\n")
    lines.append(table_latency.to_markdown(index=False, floatfmt=".3f"))
    lines.append("\n## Tabela — Tamanho (bytes)\n")
    lines.append(table_size.to_markdown(index=False, floatfmt=".0f"))

    lines.append("\n## Gráfico — Latência\n")
    lines.append(f"![]({latency_rel})\n")

    lines.append("## Gráfico — Tamanho\n")
    lines.append(f"![]({size_rel})\n")

    out_md.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
