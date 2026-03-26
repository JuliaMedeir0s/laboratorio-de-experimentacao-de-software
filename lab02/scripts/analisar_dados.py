#!/usr/bin/env python3
"""
Script para analisar e sumarizar os dados coletados pelo CK.

Uso:
    python analisar_dados.py --raw data/raw/ --processed data/processed/
"""

import os
import csv
import argparse
import logging
import pandas as pd
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def carregar_e_mesclar_dados_ck(raw_dir: str) -> pd.DataFrame:
    """
    Carrega todos os CSVs CK e mescla em um único dataframe.
    
    O CK gera vários arquivos:
    - class.csv: Métricas por classe
    - method.csv: Métricas por método
    - variable.csv: Métricas por variável
    """
    try:
        class_files = []
        
        for file in os.listdir(raw_dir):
            if file.endswith('_class.csv'):
                file_path = os.path.join(raw_dir, file)
                logger.info(f"Carregando {file}...")
                
                try:
                    df = pd.read_csv(file_path)
                    
                    # Extrair nome do repositório
                    repo_name = file.replace('_class.csv', '').replace('_', '/')
                    df['repository'] = repo_name
                    
                    class_files.append(df)
                except Exception as e:
                    logger.warning(f"Erro ao carregar {file}: {e}")
                    continue
        
        if not class_files:
            logger.error("Nenhum arquivo class.csv encontrado")
            return pd.DataFrame()
        
        # Mesclar todos os dados
        merged_df = pd.concat(class_files, ignore_index=True)
        logger.info(f"Total de classes analisadas: {len(merged_df)}")
        
        return merged_df
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados CK: {e}")
        return pd.DataFrame()


def computar_resumo_metricas(df: pd.DataFrame, output_file: str) -> None:
    """
    Computa estatísticas descritivas das métricas por repositório.
    
    Calcula: média, mediana, desvio padrão, mínimo, máximo
    """
    if df.empty:
        logger.error("DataFrame vazio!")
        return
    
    try:
        # Colunas de interesse do CK
        metric_columns = ['cbo', 'dit', 'lcom']
        
        # Filtrar apenas colunas que existem
        existing_metrics = [col.lower() for col in metric_columns 
                           if col.lower() in df.columns]
        
        if not existing_metrics:
            # Tentar com variações de nome
            logger.warning("Colunas esperadas não encontradas. Colunas disponíveis:")
            logger.warning(df.columns.tolist())
            logger.info("Usando todas as colunas numéricas para análise")
            existing_metrics = df.select_dtypes(include=['number']).columns.tolist()
        
        # Agrupar por repositório
        summary = df.groupby('repository')[existing_metrics].agg([
            'count', 'mean', 'median', 'std', 'min', 'max'
        ]).round(3)
        
        # Salvar resultado
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        summary.to_csv(output_file)
        
        logger.info(f"Resumo salvo em: {output_file}")
        logger.info(f"\nResumo das métricas por repositório:\n{summary}")
        
    except Exception as e:
        logger.error(f"Erro ao computar métricas: {e}")


def computar_estatisticas_gerais(df: pd.DataFrame, output_file: str) -> None:
    """Computa estatísticas gerais de todas as classes."""
    if df.empty:
        logger.error("DataFrame vazio!")
        return
    
    try:
        metric_columns = df.select_dtypes(include=['number']).columns
        
        stats = df[metric_columns].describe().round(3)
        stats.to_csv(output_file)
        
        logger.info(f"\nEstatísticas gerais salvas em: {output_file}")
        logger.info(f"\nEstatísticas gerais:\n{stats}")
        
    except Exception as e:
        logger.error(f"Erro ao computar estatísticas gerais: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Analisa e sumariza dados do CK'
    )
    parser.add_argument(
        '--raw',
        type=str,
        default='data/raw/',
        help='Diretório com CSVs brutos do CK'
    )
    parser.add_argument(
        '--processed',
        type=str,
        default='data/processed/',
        help='Diretório de saída para dados processados'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Iniciando análise de dados CK")
    logger.info("=" * 60)
    
    # Carregar dados
    logger.info(f"Carregando dados de {args.raw}...")
    df = carregar_e_mesclar_dados_ck(args.raw)
    
    if df.empty:
        logger.error("Nenhum dado para processar!")
        return
    
    # Computar sumários
    os.makedirs(args.processed, exist_ok=True)
    
    summary_file = os.path.join(args.processed, 'metrics_by_repository.csv')
    computar_resumo_metricas(df, summary_file)
    
    overall_file = os.path.join(args.processed, 'overall_statistics.csv')
    computar_estatisticas_gerais(df, overall_file)
    
    logger.info("=" * 60)
    logger.info("Análise finalizada!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

