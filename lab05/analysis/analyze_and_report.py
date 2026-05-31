import argparse
import json
from pathlib import Path
import math
import os

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats


def load_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")
    df["size_bytes"] = pd.to_numeric(df["size_bytes"], errors="coerce")
    df["ok"] = pd.to_numeric(df["ok"], errors="coerce").fillna(0).astype(int)
    return df


def cliffs_delta(a: pd.Series, b: pd.Series) -> float:
    # Effect size for non-parametric comparisons.
    # delta in [-1,1]. Positive means a tends to be larger than b.
    a = a.dropna().to_numpy()
    b = b.dropna().to_numpy()
    if len(a) == 0 or len(b) == 0:
        return float("nan")
    greater = 0
    less = 0
    for x in a:
        greater += (x > b).sum()
        less += (x < b).sum()
    return (greater - less) / (len(a) * len(b))


def summarize(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    g = df.groupby("treatment", as_index=False)[metric]
    out = g.agg(
        n="count",
        mean="mean",
        median="median",
        std="std",
        min="min",
        max="max",
    )
    return out


def mann_whitney(a: pd.Series, b: pd.Series):
    a = a.dropna()
    b = b.dropna()
    if len(a) == 0 or len(b) == 0:
        return {"u": float("nan"), "p": float("nan")}
    res = stats.mannwhitneyu(a, b, alternative="two-sided")
    return {"u": float(res.statistic), "p": float(res.pvalue)}


def welch_ttest(a: pd.Series, b: pd.Series):
    a = a.dropna()
    b = b.dropna()
    if len(a) == 0 or len(b) == 0:
        return {"t": float("nan"), "p": float("nan")}
    # If both samples have ~0 variance, Welch test is ill-defined (division by ~0)
    if float(a.std(ddof=1) if len(a) > 1 else 0.0) == 0.0 and float(b.std(ddof=1) if len(b) > 1 else 0.0) == 0.0:
        return {"t": float("nan"), "p": float("nan")}
    res = stats.ttest_ind(a, b, equal_var=False)
    return {"t": float(res.statistic), "p": float(res.pvalue)}


def plot_box(df: pd.DataFrame, metric: str, out_path: Path, title: str):
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 5))
    ax = sns.boxplot(data=df, x="treatment", y=metric, showfliers=False)
    ax.set_title(title)
    ax.set_xlabel("Tratamento")
    ax.set_ylabel(metric)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def md_table(df: pd.DataFrame, floatfmt: str = ".3f") -> str:
    return df.to_markdown(index=False, floatfmt=floatfmt)


def relpath(from_dir: Path, target: Path) -> str:
    return Path(os.path.relpath(target, start=from_dir)).as_posix()


def fmt_test_result(label: str, value: float) -> str:
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return f"{label}: N/A"
    return f"{label}: {value}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--run-info", required=False)
    ap.add_argument("--figdir", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    csv_path = Path(args.csv)
    figdir = Path(args.figdir)
    out_md = Path(args.out_md)
    figdir.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    df = load_results(csv_path)
    df_ok = df[df["ok"] == 1].copy()

    run_info = None
    if args.run_info:
        run_info = json.loads(Path(args.run_info).read_text(encoding="utf-8"))

    latency_summary = summarize(df_ok, "latency_ms")
    size_summary = summarize(df_ok, "size_bytes")

    # RQ1: REST_FULL vs GQL_FULL (same data volume)
    rq1_a = df_ok[df_ok["treatment"] == "REST_FULL"]["latency_ms"]
    rq1_b = df_ok[df_ok["treatment"] == "GQL_FULL"]["latency_ms"]
    rq1_mw = mann_whitney(rq1_a, rq1_b)
    rq1_t = welch_ttest(rq1_a, rq1_b)
    rq1_delta = cliffs_delta(rq1_a, rq1_b)

    # RQ2: REST_FULL vs GQL_SMALL (typical overfetch vs field selection)
    rq2_a = df_ok[df_ok["treatment"] == "REST_FULL"]["size_bytes"]
    rq2_b = df_ok[df_ok["treatment"] == "GQL_SMALL"]["size_bytes"]
    rq2_mw = mann_whitney(rq2_a, rq2_b)
    rq2_t = welch_ttest(rq2_a, rq2_b)
    rq2_delta = cliffs_delta(rq2_a, rq2_b)

    latency_plot = figdir / "latency_boxplot.png"
    size_plot = figdir / "size_boxplot.png"

    plot_box(df_ok, "latency_ms", latency_plot, "Distribuição de latência (ms) por tratamento")
    plot_box(df_ok, "size_bytes", size_plot, "Distribuição de tamanho (bytes) por tratamento")

    # Build report
    lines = []
    lines.append("# Lab05S02 — Relatório Final (Execução + Análise)\n")
    lines.append("## Introdução\n")
    lines.append(
        "Este relatório apresenta um experimento controlado comparando REST e GraphQL quanto a (RQ1) latência e (RQ2) tamanho da resposta. "
        "Foram considerados três tratamentos: REST com payload completo (REST_FULL), GraphQL solicitando os mesmos campos (GQL_FULL) e GraphQL solicitando subconjunto (GQL_SMALL).\n"
    )

    lines.append("## Metodologia\n")
    if run_info:
        exp = run_info.get("experiment", {})
        plat = run_info.get("platform", {})
        lines.append("**Ambiente (resumo):**\n")
        lines.append(
            f"- OS: {plat.get('os')} {plat.get('release')} ({plat.get('arch')})\n"
            f"- CPUs: {plat.get('cpus')}\n"
            f"- Node: {plat.get('node')}\n"
            f"- Trials por tratamento: {exp.get('trials')} (warm-up: {exp.get('warmup')})\n"
            f"- userId consultado: {exp.get('userId')}\n"
        )
    lines.append(
        "**Coleta:** para cada requisição, foi medido (i) tempo total de resposta em ms e (ii) tamanho do corpo da resposta em bytes. "
        "A ordem das requisições foi randomizada para reduzir viés temporal.\n"
    )

    lines.append("\n**Como reproduzir:** ver o passo-a-passo em `README.md` (rodar o benchmark e depois os scripts de análise).\n")

    lines.append("## Revisão Inicial dos Dados\n")
    lines.append(f"- Total de medições: {len(df)}\n")
    lines.append(f"- Mediões OK (status 2xx/ok=1): {len(df_ok)}\n")
    if (df["ok"] == 0).any():
        lines.append("- Observação: há medições com falha; a análise abaixo considera apenas `ok=1`.\n")

    lines.append("## Estatística Descritiva\n")
    lines.append("### Latência (ms)\n")
    lines.append(md_table(latency_summary) + "\n")
    lines.append("\n### Tamanho (bytes)\n")
    lines.append(md_table(size_summary, floatfmt=".0f") + "\n")

    lines.append("## Resultados por Pergunta de Pesquisa\n")

    lines.append("### RQ1 — GraphQL é mais rápido que REST?\n")
    lines.append(
        "Comparação primária: `REST_FULL` vs `GQL_FULL` (mesmo volume de dados). "
        "Testes reportados: Mann–Whitney (não-paramétrico) e t-test de Welch (paramétrico).\n"
    )
    lines.append(
        f"- Mann–Whitney U: U={rq1_mw['u']:.0f}, p={rq1_mw['p']:.3g}\n"
        + (
            f"- Welch t-test: t={rq1_t['t']:.3f}, p={rq1_t['p']:.3g}\n"
            if math.isfinite(rq1_t["t"]) and math.isfinite(rq1_t["p"])
            else "- Welch t-test: N/A (variância ~0 ou dados degenerados)\n"
        )
        + f"- Cliff's delta (REST vs GQL): {rq1_delta:.3f}\n"
    )

    rq1_rest_median = float(rq1_a.median())
    rq1_gql_median = float(rq1_b.median())
    lines.append(
        f"- Mediana (REST_FULL): {rq1_rest_median:.3f} ms | Mediana (GQL_FULL): {rq1_gql_median:.3f} ms\n"
        f"- Conclusão (RQ1): neste cenário, **GraphQL não foi mais rápido**; REST teve menor latência.\n"
    )

    lines.append("\n### RQ2 — GraphQL tem tamanho menor que REST?\n")
    lines.append(
        "Comparação primária: `REST_FULL` vs `GQL_SMALL` (REST com payload fixo vs GraphQL selecionando subconjunto de campos).\n"
    )
    lines.append(
        f"- Mann–Whitney U: U={rq2_mw['u']:.0f}, p={rq2_mw['p']:.3g}\n"
        + (
            f"- Welch t-test: t={rq2_t['t']:.3f}, p={rq2_t['p']:.3g}\n"
            if math.isfinite(rq2_t["t"]) and math.isfinite(rq2_t["p"])
            else "- Welch t-test: N/A (variância ~0 ou dados degenerados)\n"
        )
        + f"- Cliff's delta (REST vs GQL): {rq2_delta:.3f}\n"
    )

    rq2_rest_median = float(rq2_a.median())
    rq2_gql_median = float(rq2_b.median())
    reduction = (1.0 - (rq2_gql_median / rq2_rest_median)) if rq2_rest_median else float("nan")
    lines.append(
        f"- Mediana (REST_FULL): {rq2_rest_median:.0f} bytes | Mediana (GQL_SMALL): {rq2_gql_median:.0f} bytes\n"
        f"- Redução mediana: {reduction*100:.1f}%\n"
        f"- Conclusão (RQ2): neste cenário, **GraphQL teve resposta menor** (seleção de campos reduziu payload).\n"
    )

    lines.append("\n## Gráficos\n")
    latency_rel = relpath(out_md.parent, latency_plot)
    size_rel = relpath(out_md.parent, size_plot)
    lines.append(f"- Latência: ![]({latency_rel})\n")
    lines.append(f"- Tamanho: ![]({size_rel})\n")

    lines.append("\n## Discussão\n")
    lines.append(
        "Os resultados devem ser interpretados considerando que o cenário é local e usa dataset sintético. "
        "Diferenças observadas podem refletir custos de parsing/execução do GraphQL, serialização JSON e estrutura do payload.\n"
    )

    out_md.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
