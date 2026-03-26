#!/usr/bin/env python3
"""
Script para clonar repositórios e executar a análise CK.

Uso:
    python clonar_e_analisar.py --repo owner/name --output data/raw/
    python clonar_e_analisar.py --csv data/repos.csv --limit 1 --output data/raw/
"""

import os
import sys
import csv
import json
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def baixar_ck():
    """Baixa a ferramenta CK se não estiver presente."""
    ck_jar = 'ck/target/ck.jar'
    
    if os.path.exists(ck_jar):
        logger.info("CK já está instalado")
        return True
    
    logger.info("Baixando CK...")
    
    try:
        # Clone do repositório CK
        if not os.path.exists('ck'):
            subprocess.run(
                ['git', 'clone', 'https://github.com/mauricioaniche/ck.git'],
                check=True
            )
        
        # Build com Maven
        logger.info("Compilando CK (pode levar alguns minutos)...")
        result = subprocess.run(
            ['mvn', 'clean', 'package', '-DskipTests'],
            cwd='ck',
            check=True
        )
        
        logger.info("CK instalado com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao instalar CK: {e}")
        logger.error("Certifique-se de que Maven está instalado")
        return False
    except FileNotFoundError:
        logger.error("Git ou Maven não encontrado no PATH")
        return False


def clonar_repositorio(repo_name: str, clone_dir: str) -> bool:
    """Clona um repositório Git."""
    try:
        repo_path = os.path.join(clone_dir, repo_name.replace('/', '_'))
        
        if os.path.exists(repo_path):
            logger.info(f"Repositório já existe em {repo_path}")
            return True
        
        os.makedirs(clone_dir, exist_ok=True)
        
        logger.info(f"Clonando {repo_name}...")
        subprocess.run(
            ['git', 'clone', '--depth', '1', 
             f'https://github.com/{repo_name}.git', 
             repo_path],
            check=True,
            capture_output=True,
            timeout=300
        )
        logger.info(f"Repositório clonado com sucesso")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout ao clonar {repo_name}")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao clonar {repo_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao clonar {repo_name}: {e}")
        return False


def executar_analise_ck(repo_path: str, output_dir: str) -> bool:
    """Executa a análise CK em um repositório."""
    try:
        ck_jar = 'ck/target/ck.jar'
        
        if not os.path.exists(ck_jar):
            logger.error(f"CK não encontrado em {ck_jar}")
            return False
        
        logger.info(f"Executando CK em {repo_path}...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Executar CK
        result = subprocess.run(
            ['java', '-jar', ck_jar, repo_path, 'true', '0', 'false'],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            logger.warning(f"CK retornou código {result.returncode}")
            logger.warning(f"Saída de erro: {result.stderr}")
        
        logger.info(f"Análise CK concluída")
        
        # Mover arquivos CSV para output_dir
        results_dir = os.path.join(repo_path, 'report')
        if os.path.exists(results_dir):
            for file in os.listdir(results_dir):
                if file.endswith('.csv'):
                    src = os.path.join(results_dir, file)
                    repo_name = os.path.basename(repo_path)
                    dst = os.path.join(output_dir, f"{repo_name}_{file}")
                    shutil.copy2(src, dst)
                    logger.info(f"Movido {file} para {dst}")
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout ao executar CK")
        return False
    except Exception as e:
        logger.error(f"Erro ao executar CK: {e}")
        return False


def processar_repositorio(repo_name: str, output_dir: str) -> bool:
    """Processa um repositório individual."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Processando: {repo_name}")
    logger.info(f"{'='*60}")
    
    clone_dir = 'repos'
    
    if not clonar_repositorio(repo_name, clone_dir):
        return False
    
    repo_path = os.path.join(clone_dir, repo_name.replace('/', '_'))
    
    if not executar_analise_ck(repo_path, output_dir):
        return False
    
    logger.info(f"✓ {repo_name} processado com sucesso\n")
    return True


def processar_csv(csv_file: str, output_dir: str, limit: int = None) -> None:
    """Processa repositórios a partir de um CSV."""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            repos = list(reader)
        
        total = min(limit, len(repos)) if limit else len(repos)
        logger.info(f"Processando {total} repositórios a partir de {csv_file}")
        
        success_count = 0
        for i, repo in enumerate(repos[:total]):
            try:
                repo_name = repo['name']
                if processar_repositorio(repo_name, output_dir):
                    success_count += 1
                else:
                    logger.warning(f"Falha ao processar {repo_name}")
            except KeyError:
                logger.error(f"Erro: 'name' não encontrado no CSV (linha {i+1})")
                continue
            except Exception as e:
                logger.error(f"Erro ao processar linha {i+1}: {e}")
                continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Resumo: {success_count}/{total} repositórios processados com sucesso")
        logger.info(f"{'='*60}")
        
    except FileNotFoundError:
        logger.error(f"Arquivo CSV não encontrado: {csv_file}")
    except Exception as e:
        logger.error(f"Erro ao processar CSV: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Clona repositórios Java e executa análise CK'
    )
    parser.add_argument(
        '--repo',
        type=str,
        help='Repositório individual (formato: owner/name)'
    )
    parser.add_argument(
        '--csv',
        type=str,
        help='Arquivo CSV com lista de repositórios'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limita quantidade de repositórios a processar'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/raw/',
        help='Diretório de saída para CSV do CK'
    )
    parser.add_argument(
        '--skip-ck-download',
        action='store_true',
        help='Pula download do CK (assume que já está instalado)'
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if not args.repo and not args.csv:
        parser.error("É necessário fornecer --repo ou --csv")
    elif args.repo and args.csv:
        parser.error("Forneça apenas --repo ou --csv, não ambos")
    
    logger.info("=" * 60)
    logger.info("Iniciando clone e análise de repositórios")
    logger.info("=" * 60)
    
    # Downloads CK se necessário
    if not args.skip_ck_download:
        if not baixar_ck():
            logger.error("Falha ao baixar CK. Execute com --skip-ck-download se o CK já está instalado")
            sys.exit(1)
    
    # Processar repositórios
    if args.repo:
        processar_repositorio(args.repo, args.output)
    else:
        processar_csv(args.csv, args.output, args.limit)
    
    logger.info("=" * 60)
    logger.info("Processamento finalizado!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

