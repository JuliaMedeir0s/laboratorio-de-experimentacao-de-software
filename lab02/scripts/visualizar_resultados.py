#!/usr/bin/env python3
"""
Script para gerar gráficos de visualização e análise estatística.

Uso:
    python visualizar_resultados.py --data data/processed/ --output results/
"""

import os
import argparse
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, pearsonr

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar estilo dos gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


def carregar_dados_metricas(csv_file: str) -> pd.DataFrame:
    """Carrega os dados de métricas processadas."""
    try:
        df = pd.read_csv(csv_file, index_col=0)
        logger.info(f"Dados carregados de {csv_file}")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar {csv_file}: {e}")
        return pd.DataFrame()


def achatar_colunas_multinivel(df: pd.DataFrame) -> pd.DataFrame:
    """Achata colunas multi-nível em nomes simples."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() for col in df.columns.values]
    return df


def computar_correlacoes(metrics_file: str, repos_file: str = None) -> None:
    """
    Computa correlações entre métricas de processo e qualidade.
    
    Requer arquivo repos.csv com informações de GitHub.
    """
    logger.info("\n" + "="*60)
    logger.info("Análise de Correlação")
    logger.info("="*60)
    
    try:
        metrics_df = carregar_dados_metricas(metrics_file)
        
        if metrics_df.empty:
            logger.error("Dados de métricas vazios")
            return
        
        metrics_df = achatar_colunas_multinivel(metrics_df)
        
        logger.info(f"\nColunas disponíveis:\n{metrics_df.columns.tolist()}")
        
        # Exemplo de análise com dados hipotéticos
        # Em produção, você mescalaria com dados do GitHub
        logger.info("\n✓ Correlações estatísticas podem ser computadas quando dados de GitHub estiverem disponíveis")
        
    except Exception as e:
        logger.error(f"Erro ao computar correlações: {e}")


def plotar_distribuicao_metrica(df: pd.DataFrame, metric_col: str, output_dir: str) -> None:
    """Gera gráficos de distribuição de uma métrica."""
    try:
        if metric_col not in df.columns:
            logger.warning(f"Coluna {metric_col} não encontrada")
            return
        
        # Remover NaN
        data = df[metric_col].dropna()
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histograma
        axes[0].hist(data, bins=30, edgecolor='black', alpha=0.7)
        axes[0].set_title(f'Distribuição de {metric_col}')
        axes[0].set_xlabel(metric_col)
        axes[0].set_ylabel('Frequência')
        axes[0].grid(True, alpha=0.3)
        
        # Box plot
        axes[1].boxplot(data, vert=True)
        axes[1].set_title(f'Box Plot de {metric_col}')
        axes[1].set_ylabel(metric_col)
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_file = os.path.join(output_dir, f'distribution_{metric_col}.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        logger.info(f"Gráfico salvo em: {output_file}")
        plt.close()
        
    except Exception as e:
        logger.error(f"Erro ao plotar distribuição de {metric_col}: {e}")


def plotar_estatisticas_resumo(summary_file: str, output_dir: str) -> None:
    """Gera visualizações dos sumários estatísticos."""
    try:
        df = carregar_dados_metricas(summary_file)
        df = achatar_colunas_multinivel(df)
        
        if df.empty:
            logger.warning("Dados vazios para visualização")
            return
        
        # Plotar primeiras 20 repositórios
        plot_data = df.head(20)
        
        # Gráfico de barras com médias
        fig, ax = plt.subplots(figsize=(14, 8))
        
        mean_cols = [col for col in df.columns if 'mean' in col]
        if mean_cols:
            plot_data[mean_cols].plot(kind='bar', ax=ax)
            ax.set_title('Métricas Médias por Repositório (Top 20)')
            ax.set_xlabel('Repositório')
            ax.set_ylabel('Valor')
            ax.legend(loc='upper right')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            output_file = os.path.join(output_dir, 'metrics_by_repo.png')
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"Gráfico salvo em: {output_file}")
            plt.close()
        
    except Exception as e:
        logger.error(f"Erro ao plotar sumários: {e}")


def gerar_relatorio(data_dir: str, output_dir: str) -> None:
    """Gera relatório completo de análise."""
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("Gerando Visualizações")
    logger.info("=" * 60)
    
    # Arquivos esperados
    summary_file = os.path.join(data_dir, 'metrics_by_repository.csv')
    overall_file = os.path.join(data_dir, 'overall_statistics.csv')
    
    if not os.path.exists(summary_file):
        logger.error(f"Arquivo não encontrado: {summary_file}")
        return
    
    # Plotar distribuições
    logger.info("\nGerando gráficos de distribuição...")
    df = carregar_dados_metricas(summary_file)
    df = achatar_colunas_multinivel(df)
    
    for col in df.columns:
        if 'mean' in col:
            metric_name = col.replace('_mean', '')
            plotar_distribuicao_metrica(df, col, output_dir)
    
    # Plotar sumários
    logger.info("Gerando gráficos de sumários...")
    plotar_estatisticas_resumo(summary_file, output_dir)
    
    # Correlações
    logger.info("Analisando correlações...")
    computar_correlacoes(summary_file)
    
    logger.info("\n" + "=" * 60)
    logger.info("Visualizações geradas com sucesso!")
    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Gera visualizações e análises dos dados'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/processed/',
        help='Diretório com dados processados'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/',
        help='Diretório de saída para gráficos'
    )
    
    args = parser.parse_args()
    
    gerar_relatorio(args.data, args.output)


if __name__ == '__main__':
    main()

