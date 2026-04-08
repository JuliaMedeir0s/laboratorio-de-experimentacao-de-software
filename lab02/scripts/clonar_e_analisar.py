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
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import shutil
import stat

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
                if dst.exists():
                    try:
                        dst.unlink()
                    except Exception:
                        pass
                try:
                    shutil.move(str(file), str(dst))
                except Exception:
                    os.replace(str(file), str(dst))
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


def _safe_delete_dir(target_dir: Path, allowed_root: Path) -> bool:
    """Remove um diretório recursivamente, garantindo que ele esteja dentro de allowed_root."""
    try:
        target_resolved = target_dir.resolve()
        allowed_resolved = allowed_root.resolve()

        try:
            target_resolved.relative_to(allowed_resolved)
        except ValueError:
            logger.error(
                f"Recusando deletar fora de {allowed_resolved}: {target_resolved}"
            )
            return False

        if not target_resolved.exists():
            return True

        def _on_rmtree_error(func, path, exc_info):
            exc = exc_info[1]
            if isinstance(exc, PermissionError):
                try:
                    os.chmod(path, stat.S_IWRITE)
                except Exception:
                    pass
                func(path)
                return
            raise exc

        try:
            shutil.rmtree(target_resolved, onerror=_on_rmtree_error)
            return True
        except Exception as e:
            if os.name == 'nt':
                try:
                    cmd = f'rmdir /s /q "{target_resolved}"'
                    result = subprocess.run(
                        ['cmd', '/c', cmd],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0 and not target_resolved.exists():
                        return True
                except Exception:
                    pass

            logger.warning(
                f"Falha ao deletar {target_dir}: {e} (possível arquivo em uso/lock; tente executar novamente ou fechar processos que estejam usando o repo)"
            )
            return False
    except Exception as e:
        logger.warning(f"Falha ao deletar {target_dir}: {e}")
        return False


def processar_repositorio(repo_name: str, output_dir: str, keep_repos: bool = False) -> bool:
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

    if not keep_repos:
        repo_dir = Path(repo_path)
        output_dir_p = _resolve_under_lab02(output_dir)

        # Só deletar se houver evidência de saída gerada.
        generated = list(output_dir_p.glob(f"{repo_dir.name}_*.csv"))
        if not generated:
            logger.warning(
                f"Nenhum CSV encontrado em {output_dir_p} para {repo_dir.name}; mantendo clone para troubleshooting"
            )
        else:
            clone_root = _resolve_under_lab02(clone_dir)
            if _safe_delete_dir(repo_dir, clone_root):
                logger.info(f"Repositório removido após análise: {repo_dir}")
            else:
                logger.warning(f"Não foi possível remover o repositório: {repo_dir}")
    
    logger.info(f"✓ {repo_name} processado com sucesso\n")
    return True


def processar_csv(
    csv_file: str,
    output_dir: str,
    limit: int = None,
    keep_repos: bool = False,
    workers: int = 2,
) -> None:
    """Processa repositórios a partir de um CSV."""
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            repos = list(reader)
        
        total = min(limit, len(repos)) if limit else len(repos)
        logger.info(f"Processando {total} repositórios a partir de {csv_file}")
        
        workers = max(1, int(workers or 1))
        logger.info(f"Executando processamento com {workers} worker(s)")

        items = repos[:total]
        success_count = 0
        completed = 0

        def _repo_name_from_row(row: dict, row_index: int) -> str:
            if 'name' not in row:
                raise KeyError(f"'name' não encontrado no CSV (linha {row_index + 1})")
            return row['name']

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for i, row in enumerate(items):
                try:
                    repo_name = _repo_name_from_row(row, i)
                except KeyError as e:
                    logger.error(str(e))
                    continue
                futures[executor.submit(
                    processar_repositorio,
                    repo_name,
                    output_dir,
                    keep_repos,
                )] = repo_name

            for fut in as_completed(futures):
                repo_name = futures[fut]
                completed += 1
                try:
                    ok = bool(fut.result())
                    if ok:
                        success_count += 1
                    else:
                        logger.warning(f"Falha ao processar {repo_name}")
                except Exception as e:
                    logger.error(f"Erro ao processar {repo_name}: {e}")

                if completed % 5 == 0 or completed == len(futures):
                    logger.info(f"Progresso: {completed}/{len(futures)} concluídos")
        
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
    parser.add_argument(
        '--keep-repos',
        action='store_true',
        help='Mantém os repositórios clonados em lab02/repos (padrão: deleta após análise bem-sucedida)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=2,
        help='Número de workers para processar CSV em paralelo (padrão: 2)'
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
        processar_repositorio(args.repo, args.output, keep_repos=args.keep_repos)
    else:
        processar_csv(args.csv, args.output, args.limit, keep_repos=args.keep_repos, workers=args.workers)
    
    logger.info("=" * 60)
    logger.info("Processamento finalizado!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

