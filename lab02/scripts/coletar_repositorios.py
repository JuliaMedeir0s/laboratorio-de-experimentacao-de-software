#!/usr/bin/env python3
"""
Script para coletar os 1000 repositórios Java mais populares do GitHub.

Uso:
    python coletar_repositorios.py --count 1000 --output data/repos.csv
"""

import os
import csv
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv
from github import Github

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def coletar_repositorios(count: int, output_file: str) -> None:
    """
    Coleta os repositórios Java mais populares do GitHub.
    
    Args:
        count: Número de repositórios a coletar
        output_file: Caminho do arquivo de saída CSV
    """
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        logger.error("GITHUB_TOKEN não encontrado em .env")
        return
    
    try:
        g = Github(token)
        logger.info(f"Autenticado no GitHub com sucesso")
        
        # Query para os repositórios Java mais populares
        # Ordenados por número de estrelas (descrescente)
        query = 'language:java sort:stars-desc'
        
        logger.info(f"Coletando {count} repositórios Java...")
        repos = g.search_repositories(query=query, per_page=100)
        
        # Preparar dados
        data = []
        for i, repo in enumerate(repos[:count]):
            if i % 10 == 0:
                logger.info(f"Progresso: {i}/{count} repositórios coletados")
            
            try:
                repo_info = {
                    'rank': i + 1,
                    'name': repo.full_name,
                    'owner': repo.owner.login,
                    'url': repo.html_url,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'watchers': repo.watchers_count,
                    'open_issues': repo.open_issues_count,
                    'created_at': repo.created_at.isoformat() if repo.created_at else '',
                    'updated_at': repo.updated_at.isoformat() if repo.updated_at else '',
                    'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else '',
                    'description': repo.description or '',
                    'language': repo.language or 'Java',
                    'topics': ','.join(repo.get_topics()) if repo.get_topics() else '',
                }
                data.append(repo_info)
            except Exception as e:
                logger.warning(f"Erro ao coletar repositório {i}: {e}")
                continue
        
        logger.info(f"Total de repositórios coletados: {len(data)}")
        
        # Salvar em CSV
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys() if data else [])
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Repositórios salvos em: {output_file}")
        
    except Exception as e:
        logger.error(f"Erro ao coletar repositórios: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Coleta repositórios Java do GitHub'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1000,
        help='Número de repositórios a coletar (padrão: 1000)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/repos.csv',
        help='Caminho do arquivo de saída CSV'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Iniciando coleta de repositórios Java")
    logger.info("=" * 60)
    
    coletar_repositorios(args.count, args.output)
    
    logger.info("=" * 60)
    logger.info("Coleta finalizada!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

