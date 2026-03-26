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
LAB02_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(dotenv_path=LAB02_ROOT / '.env')


def _resolve_under_lab02(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (LAB02_ROOT / p)


def _find_maven_cmd() -> str | None:
    maven_cmd = os.environ.get('MAVEN_CMD')
    if maven_cmd:
        p = Path(maven_cmd)
        if p.exists():
            return str(p)

    from shutil import which

    found = which('mvn')
    if found:
        return found

    candidates: list[Path] = []
    home = Path.home()
    for base in (home / '.maven', home / 'apache-maven'):
        if base.exists():
            candidates.extend(base.glob('**/bin/mvn.cmd'))
            candidates.extend(base.glob('**/bin/mvn'))

    if not candidates:
        return None

    candidates.sort(key=lambda p: str(p))
    return str(candidates[-1])


def baixar_ck():
    """Baixa a ferramenta CK se não estiver presente."""
    ck_target_dir = LAB02_ROOT / 'ck' / 'target'
    ck_jar = ck_target_dir / 'ck.jar'
    
    if ck_jar.exists():
        logger.info("CK já está instalado")
        return True
    
    logger.info("Baixando CK...")
    
    try:
        mvn_cmd = _find_maven_cmd()
        if not mvn_cmd:
            logger.error("Maven não encontrado no PATH e MAVEN_CMD não definido")
            logger.error("Instale Maven ou defina MAVEN_CMD apontando para mvn/mvn.cmd")
            return False

        # Clone do repositório CK
        if not (LAB02_ROOT / 'ck').exists():
            subprocess.run(
                ['git', 'clone', 'https://github.com/mauricioaniche/ck.git'],
                cwd=str(LAB02_ROOT),
                check=True
            )
        
        # Build com Maven
        logger.info("Compilando CK (pode levar alguns minutos)...")
        subprocess.run(
            [mvn_cmd, 'clean', 'package', '-DskipTests', '-Dmaven.javadoc.skip=true'],
            cwd=str(LAB02_ROOT / 'ck'),
            check=True
        )

        if not ck_jar.exists():
            if not ck_target_dir.exists():
                logger.error("Diretório target do CK não encontrado após build")
                return False

            candidates = sorted(ck_target_dir.glob('*-jar-with-dependencies.jar'))
            if not candidates:
                candidates = sorted(ck_target_dir.glob('ck-*.jar'))

            if not candidates:
                logger.error("Nenhum JAR do CK encontrado em ck/target após build")
                return False

            shutil.copy2(str(candidates[-1]), str(ck_jar))
            logger.info(f"JAR do CK normalizado em: {ck_jar}")
        
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
        clone_path = _resolve_under_lab02(clone_dir)
        repo_path = clone_path / repo_name.replace('/', '_')
        
        if repo_path.exists():
            logger.info(f"Repositório já existe em {repo_path}")
            return True
        
        clone_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Clonando {repo_name}...")
        subprocess.run(
            ['git', 'clone', '--depth', '1', 
             f'https://github.com/{repo_name}.git', 
             str(repo_path)],
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
        ck_jar = LAB02_ROOT / 'ck' / 'target' / 'ck.jar'
        
        if not ck_jar.exists():
            logger.error(f"CK não encontrado em {ck_jar}")
            return False
        
        repo_path_p = Path(repo_path)
        output_dir_p = _resolve_under_lab02(output_dir)

        logger.info(f"Executando CK em {repo_path_p}...")
        
        output_dir_p.mkdir(parents=True, exist_ok=True)

        # CK gera arquivos com nomes fixos (class.csv, method.csv, ...).
        # Para não sobrescrever quando processar múltiplos repositórios,
        # rodamos em um diretório temporário por repositório e renomeamos ao copiar.
        staging_dir = output_dir_p / f".ck_staging_{repo_path_p.name}"
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Executar CK
        result = subprocess.run(
            ['java', '-jar', str(ck_jar), str(repo_path_p), 'true', '0', 'false'],
            cwd=str(staging_dir),
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            logger.warning(f"CK retornou código {result.returncode}")
            logger.warning(f"Saída de erro: {result.stderr}")
        
        logger.info(f"Análise CK concluída")

        moved_any = False
        for file in staging_dir.iterdir():
            if file.is_file() and file.name.endswith('.csv'):
                dst = output_dir_p / f"{repo_path_p.name}_{file.name}"
                shutil.move(str(file), str(dst))
                logger.info(f"Movido {file.name} para {dst}")
                moved_any = True

        shutil.rmtree(staging_dir, ignore_errors=True)

        if not moved_any:
            logger.warning("Nenhum CSV foi gerado pelo CK (staging vazio)")
        
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
    
    repo_path = str(_resolve_under_lab02(clone_dir) / repo_name.replace('/', '_'))
    
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

