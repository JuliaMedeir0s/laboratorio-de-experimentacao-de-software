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
from pathlib import Path
from dotenv import load_dotenv
from github import Github

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
LAB02_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(dotenv_path=LAB02_ROOT / '.env')


def _resolve_under_lab02(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (LAB02_ROOT / p)


def coletar_repositorios(count: int, output_file: str) -> None:
    """
    Coleta os repositórios Java mais populares do GitHub.
    
    Args:
        count: Número de repositórios a coletar
        output_file: Caminho do arquivo de saída CSV
    """
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        logger.error("GITHUB_TOKEN não encontrado em .env/.env.example")
        logger.error("Defina GITHUB_TOKEN no arquivo lab02/.env (ou variável de ambiente) e tente novamente")
        raise SystemExit(1)
    
    try:
        g = Github(token)
        logger.info(f"Autenticado no GitHub com sucesso")
        
        # Query para os repositórios Java mais populares
        # Ordenados por número de estrelas (descrescente)
        query = 'language:Java'
        
        logger.info(f"Coletando {count} repositórios Java...")
        repos = g.search_repositories(query=query, sort='stars', order='desc')
        
        # Preparar dados
        data = []
        for i, repo in enumerate(repos):
            if i >= count:
                break
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
                    'topics': ','.join(repo.get_topics()) or '',
                }
                data.append(repo_info)
            except Exception as e:
                logger.warning(f"Erro ao coletar repositório {i}: {e}")
                continue
        
        logger.info(f"Total de repositórios coletados: {len(data)}")
        
        if not data:
            logger.error("Nenhum repositório foi coletado; nada a salvar")
            raise SystemExit(2)

        # Salvar em CSV
        output_path = _resolve_under_lab02(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Repositórios salvos em: {output_path}")
        
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

