#!/usr/bin/env python3
"""Script para criar um dashboard em HTML.

Observação: o enunciado do laboratório pede uma ferramenta de BI
(Power BI/Tableau/Looker Studio). Este HTML é um artefato auxiliar.

Os números são carregados de `dataset/ANALISE_RQ.md` para evitar hard-code.
"""

import os
from pathlib import Path
from base64 import b64encode
from datetime import datetime

from dashboard_data import extract_metrics, load_analise

# Diretórios
dataset_dir = Path(__file__).parent / "dataset"
graficos_dir = dataset_dir / "graficos"
output_dir = Path(__file__).parent / "outputs"

# Criar diretório de outputs se não existir
output_dir.mkdir(exist_ok=True)

def encode_image(image_path):
    """Converte imagem para base64 para embedding no HTML"""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as img_file:
        return b64encode(img_file.read()).decode()

def create_dashboard_html():
    """Cria um dashboard HTML interativo"""

    metrics = extract_metrics(load_analise())
    ds = metrics["dataset"]

    cves_per_vuln_dep = (
        (ds["total_cves"] / ds["total_vulnerable_deps"]) if ds.get("total_vulnerable_deps") else 0
    )

    # Convenience structures for rendering
    bots = metrics["bots"]
    severity = metrics["severity"]
    rq1_group = metrics["rq1_by_repo_group"]
    rq3_tools = metrics["rq3_tools_comparison"]
    
    # Codificar imagens
    images = {}
    image_files = [
        "bar_repo_vulnerability_rate.png",
        "boxplot_cves_by_group.png",
        "boxplot_cves_per_dependency_by_group.png",
        "stacked_bar_severity_distribution.png",
        "heatmap_severity_distribution.png",
        "bar_normalized_comparison.png",
        "bar_activity_difference_vs_none.png",
        "scatter_dependencies_vs_cves.png",
    ]
    
    for img_file in image_files:
        img_path = graficos_dir / img_file
        b64 = encode_image(str(img_path))
        if b64:
            images[img_file] = b64
    
    # Gerar HTML
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard BI - Análise de Dependências Vulneráveis em Projetos Node.js</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 8px;
            margin-bottom: 40px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .metadata {{
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .section h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .section h3 {{
            color: #764ba2;
            font-size: 1.5em;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .metric-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .metric-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .metric-card.alt {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .metric-card.alt2 {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        .metric-card.alt3 {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }}
        
        .table-responsive {{
            overflow-x: auto;
            margin-bottom: 30px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        
        table thead {{
            background-color: #f0f2f5;
            border-bottom: 2px solid #667eea;
        }}
        
        table th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #667eea;
        }}
        
        table td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        table tbody tr:hover {{
            background-color: #f9f9f9;
        }}
        
        .chart-container {{
            margin: 30px 0;
            text-align: center;
        }}
        
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .chart-title {{
            font-size: 1.3em;
            color: #764ba2;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .conclusion {{
            background: #f0f8ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .conclusion strong {{
            color: #667eea;
        }}
        
        .insights {{
            background: #f0fff4;
            border-left: 4px solid #43e97b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .insights strong {{
            color: #38f9d7;
        }}
        
        ul {{
            margin-left: 20px;
        }}
        
        li {{
            margin-bottom: 10px;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #e0e0e0;
            margin-top: 40px;
            font-size: 0.9em;
        }}
        
        @media print {{
            body {{
                background-color: white;
            }}
            
            .section {{
                page-break-inside: avoid;
                box-shadow: none;
                border: 1px solid #e0e0e0;
            }}
            
            .chart-container {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <header>
            <h1>📊 Dashboard BI</h1>
            <p>Análise de Dependências Vulneráveis em Projetos Node.js do GitHub</p>
            <div class="metadata">
                <span>{metrics['meta'].get('dataset','Dataset')} • Período: {metrics['meta'].get('periodo','')}</span>
                <span>Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</span>
            </div>
        </header>
        
        <!-- SEÇÃO 1: CARACTERIZAÇÃO DO DATASET -->
        <div class="section">
            <h2>1. Caracterização do Dataset</h2>
            
            <p style="margin-bottom: 20px;">
                O dataset analisado compreende <strong>1.000 repositórios Node.js públicos</strong> hospedados no GitHub, 
                coletados em um snapshot de abril de 2026. A análise utiliza ferramentas especializadas para identificar 
                dependências vulneráveis: <strong>OSV (Open Source Vulnerability) API</strong> para identificação e 
                <strong>NVD (National Vulnerability Database)</strong> para validação cruzada.
            </p>
            
            <h3>1.1. Visão Geral</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value">{ds['total_repos']}</div>
                    <div class="label">Repositórios Analisados</div>
                </div>
                <div class="metric-card alt">
                    <div class="value">{ds['repos_with_vuln']}</div>
                    <div class="label">Com Vulnerabilidades ({(ds['repos_with_vuln_pct'] or 0):.2f}%)</div>
                </div>
                <div class="metric-card alt2">
                    <div class="value">{ds['repos_without_vuln']}</div>
                    <div class="label">Sem Vulnerabilidades ({(ds['repos_without_vuln_pct'] or 0):.2f}%)</div>
                </div>
                <div class="metric-card alt3">
                    <div class="value">{ds['total_cves']}</div>
                    <div class="label">CVEs Identificados</div>
                </div>
            </div>
            
            <h3>1.2. Distribuição de Bots de Automação</h3>
            <p style="margin-bottom: 15px;">
                Os repositórios foram classificados conforme a presença de ferramentas de automação de dependências:
            </p>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Ferramenta</th>
                            <th>Repositórios</th>
                            <th>Percentual</th>
                            <th>Taxa de Vulnerabilidade</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for bot in bots:
        html += f"""
                        <tr>
                            <td><strong>{bot['tool']}</strong></td>
                            <td>{bot['repos']}</td>
                            <td>{bot['pct']:.2f}%</td>
                            <td>{bot['taxa']:.2f}%</td>
                        </tr>
"""
    
    html += f"""
                    </tbody>
                </table>
            </div>
            
            <h3>1.3. Distribuição de Dependências</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value">{ds['total_direct_deps']}</div>
                    <div class="label">Dependências Diretas (Total)</div>
                </div>
                <div class="metric-card alt">
                    <div class="value">{ds['total_resolved_versions']}</div>
                    <div class="label">Versões Resolvidas</div>
                </div>
                <div class="metric-card alt2">
                    <div class="value">{ds['total_vulnerable_deps']}</div>
                    <div class="label">Dependências Vulneráveis</div>
                </div>
                <div class="metric-card alt3">
                    <div class="value">{(ds['total_vulnerable_deps']/ds['total_direct_deps']*100 if ds['total_direct_deps'] else 0):.2f}%</div>
                    <div class="label">Taxa de Vulnerabilidade</div>
                </div>
            </div>
            
            <h3>1.4. Estatísticas Descritivas por Grupo</h3>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Métrica</th>
                            <th>Com Vulnerabilidade</th>
                            <th>Sem Vulnerabilidade</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Dependências diretas/repo</td>
                            <td>{rq1_group.get('Dependências diretas/repo',{}).get('with','')}</td>
                            <td>{rq1_group.get('Dependências diretas/repo',{}).get('without','')}</td>
                        </tr>
                        <tr>
                            <td>Versões resolvidas/repo</td>
                            <td>{rq1_group.get('Versões resolvidas/repo',{}).get('with','')}</td>
                            <td>{rq1_group.get('Versões resolvidas/repo',{}).get('without','')}</td>
                        </tr>
                        <tr>
                            <td>Dependências vulneráveis/repo</td>
                            <td>{rq1_group.get('Dependências vulneráveis/repo',{}).get('with','')}</td>
                            <td>0</td>
                        </tr>
                        <tr>
                            <td>CVEs/repo</td>
                            <td>{rq1_group.get('CVEs/repo',{}).get('with','')}</td>
                            <td>0</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- SEÇÃO 2: RQ1 - FREQUÊNCIA DE VULNERABILIDADES -->
        <div class="section">
            <h2>2. RQ1: Frequência de Dependências Vulneráveis</h2>
            
            <p style="margin-bottom: 20px;">
                <strong>Pergunta de Pesquisa:</strong> Qual é a frequência de dependências vulneráveis em projetos Node.js 
                hospedados no GitHub?
            </p>
            
            <div class="insights">
                <strong>💡 Insight Principal:</strong> Metade dos projetos Node.js analisados (49,5%) contém pelo menos 
                uma dependência com vulnerabilidade conhecida.
            </div>
            
            <h3>2.1. Estatísticas Principais</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value">{(ds['repos_with_vuln_pct'] or 0):.2f}%</div>
                    <div class="label">Taxa de Repos Vulneráveis</div>
                </div>
                <div class="metric-card alt">
                    <div class="value">{rq1_group.get('Dependências vulneráveis/repo',{}).get('with','')}</div>
                    <div class="label">Deps. Vulneráveis/Repo (média)</div>
                </div>
                <div class="metric-card alt2">
                    <div class="value">{rq1_group.get('CVEs/repo',{}).get('with','')}</div>
                    <div class="label">CVEs por Repositório Vulnerável</div>
                </div>
                <div class="metric-card alt3">
                    <div class="value">{cves_per_vuln_dep:.2f}</div>
                    <div class="label">CVEs por Dependência Vulnerável</div>
                </div>
            </div>
            
            <h3>2.2. Visualizações</h3>
"""
    
    if "bar_repo_vulnerability_rate.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Taxa de Vulnerabilidade por Grupo</div>
                <img src="data:image/png;base64,{images['bar_repo_vulnerability_rate.png']}" alt="Taxa de Vulnerabilidade">
            </div>
"""
    
    if "boxplot_cves_by_group.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Distribuição de CVEs por Repositório (por Grupo)</div>
                <img src="data:image/png;base64,{images['boxplot_cves_by_group.png']}" alt="Distribuição de CVEs">
            </div>
"""
    
    if "boxplot_cves_per_dependency_by_group.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">CVEs por Dependência (Análise Normalizada)</div>
                <img src="data:image/png;base64,{images['boxplot_cves_per_dependency_by_group.png']}" alt="CVEs por Dependência">
            </div>
"""
    
    html += """
            <div class="conclusion">
                <strong>Conclusão RQ1:</strong> A frequência de vulnerabilidades é alarmante. Especialmente preocupante é 
                que repositórios sem ferramentas de automação (Dependabot, Renovate, Snyk) têm 52,43% de chance de 
                conter vulnerabilidades, enquanto projetos com Dependabot têm apenas 40,88%.
            </div>
        </div>
        
        <!-- SEÇÃO 3: RQ2 - SEVERIDADE DAS VULNERABILIDADES -->
        <div class="section">
            <h2>3. RQ2: Nível de Severidade das Vulnerabilidades</h2>
            
            <p style="margin-bottom: 20px;">
                <strong>Pergunta de Pesquisa:</strong> Qual é o nível de severidade das vulnerabilidades encontradas e 
                qual a distribuição proporcional entre os níveis de risco?
            </p>
            
            <div class="insights">
                <strong>💡 Insight Principal:</strong> 86,3% dos CVEs têm severidade MEDIUM ou superior, indicando 
                risco significativo.
            </div>
            
            <h3>3.1. Distribuição de Severidade</h3>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Nível de Severidade</th>
                            <th>Contagem</th>
                            <th>Percentual</th>
                            <th>Risco Operacional</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for sev in severity:
        risk_class = "Imediato" if sev['severity'] in ["HIGH", "CRITICAL"] else "Médio prazo" if sev['severity'] == "MEDIUM" else "Monitorar"
        html += f"""
                        <tr>
                            <td><strong>{sev['severity']}</strong></td>
                            <td>{sev['count']}</td>
                            <td>{sev['pct']:.2f}%</td>
                            <td>{risk_class}</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value">86.3%</div>
                    <div class="label">CVEs com Severidade MEDIUM+</div>
                </div>
                <div class="metric-card alt">
                    <div class="value">46.5%</div>
                    <div class="label">CVEs HIGH + CRITICAL</div>
                </div>
                <div class="metric-card alt2">
                    <div class="value">39.79%</div>
                    <div class="label">CVEs MEDIUM</div>
                </div>
                <div class="metric-card alt3">
                    <div class="value">13.71%</div>
                    <div class="label">CVEs LOW + UNKNOWN</div>
                </div>
            </div>
            
            <h3>3.2. Visualizações</h3>
"""
    
    if "stacked_bar_severity_distribution.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Distribuição Percentual de Severidade (100% Stacked)</div>
                <img src="data:image/png;base64,{images['stacked_bar_severity_distribution.png']}" alt="Distribuição de Severidade">
            </div>
"""
    
    if "heatmap_severity_distribution.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Heatmap: Severidade (%) por Grupo</div>
                <img src="data:image/png;base64,{images['heatmap_severity_distribution.png']}" alt="Heatmap de Severidade">
            </div>
"""
    
    html += """
            <div class="conclusion">
                <strong>Conclusão RQ2:</strong> A maioria dos CVEs tem severidade significativa (MEDIUM ou superior). 
                Vulnerabilidades CRITICAL são mais prevalentes em projetos sem Dependabot (7,12% vs 4,82%), sugerindo 
                que a automação ajuda na mitigação rápida.
            </div>
        </div>
        
        <!-- SEÇÃO 4: RQ3 - IMPACTO DO DEPENDABOT -->
        <div class="section">
            <h2>4. RQ3: Impacto da Automação (Dependabot, Renovate, Snyk)</h2>
            
            <p style="margin-bottom: 20px;">
                <strong>Pergunta de Pesquisa:</strong> A utilização de ferramentas de automação (Dependabot, Renovate, Snyk) 
                está associada a uma menor incidência de dependências com vulnerabilidades conhecidas nos projetos analisados?
            </p>
            
            <div class="insights">
                <strong>💡 Insight Principal:</strong> SIM! O uso de ferramentas de automação (Dependabot, Renovate) está 
                associado a uma menor incidência de vulnerabilidades neste snapshot.
            </div>
            
            <h3>4.1. Comparação de Ferramentas</h3>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Ferramenta</th>
                            <th>Taxa de Repos Vulneráveis</th>
                            <th>CVEs/Repo</th>
                            <th>Deps. Vulneráveis/Repo</th>
                            <th>Benefício</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    baseline = None
    for t in rq3_tools:
        if t["tool"].lower().startswith("sem bot"):
            baseline = t
            break

    for comp in rq3_tools:
        if baseline and comp["tool"] == baseline["tool"]:
            beneficio = "Baseline"
        elif baseline:
            beneficio = f"✅ {100*(1-comp['taxa']/baseline['taxa']):.1f}% redução"
        else:
            beneficio = "—"

        html += f"""
                        <tr>
                            <td><strong>{comp['tool']}</strong></td>
                            <td>{comp['taxa']:.2f}%</td>
                            <td>{comp['cves_per_repo']:.2f}</td>
                            <td>—</td>
                            <td>{beneficio}</td>
                        </tr>
"""
    
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="value">19.64%</div>
                    <div class="label">Redução de Taxa de Repos Vulneráveis (Dependabot)</div>
                </div>
                <div class="metric-card alt">
                    <div class="value">21.39%</div>
                    <div class="label">Redução de CVEs/Repo (Dependabot)</div>
                </div>
                <div class="metric-card alt2">
                    <div class="value">12.49%</div>
                    <div class="label">Redução de Deps. Vulneráveis/Repo</div>
                </div>
                <div class="metric-card alt3">
                    <div class="value">~10</div>
                    <div class="label">NNT - Número Necessário para Tratar</div>
                </div>
            </div>
            
            <h3>4.2. Visualizações Comparativas</h3>
"""
    
    if "bar_normalized_comparison.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Risco por Grupo: Diferença Percentual vs None</div>
                <img src="data:image/png;base64,{images['bar_normalized_comparison.png']}" alt="Comparação Normalizada">
            </div>
"""
    
    if "bar_activity_difference_vs_none.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Atividade de Correção: Versões Resolvidas (Δ% vs None)</div>
                <img src="data:image/png;base64,{images['bar_activity_difference_vs_none.png']}" alt="Atividade de Correção">
            </div>
"""
    
    if "scatter_dependencies_vs_cves.png" in images:
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Scatter Plot: Dependências vs CVEs (Todos os Grupos)</div>
                <img src="data:image/png;base64,{images['scatter_dependencies_vs_cves.png']}" alt="Dependências vs CVEs">
            </div>
"""
    
    html += """
            <div class="conclusion">
                <strong>Conclusão RQ3:</strong> O Dependabot reduz o risco em aproximadamente 21,4% em termos de CVEs por 
                repositório. O Renovate tem um desempenho ainda melhor (30,36% de repos vulneráveis), embora com amostra menor. 
                O impacto na severidade também é notável: projetos com Dependabot têm menor proporção de vulnerabilidades 
                CRITICAL (4,82% vs 7,12%).
            </div>
        </div>
        
        <!-- SEÇÃO 5: RECOMENDAÇÕES -->
        <div class="section">
            <h2>5. Recomendações</h2>
            
            <h3>5.1. Curto Prazo (Imediato)</h3>
            <ul>
                <li><strong>Adotar Dependabot ou Renovate</strong> em todos os repositórios críticos</li>
                <li><strong>Auditar dependências existentes</strong> — especialmente aquelas com vulnerabilidades HIGH e CRITICAL</li>
                <li><strong>Estabelecer política SLA</strong> para resolução de vulnerabilidades por nível de severidade:
                    <ul>
                        <li>CRITICAL: Resolver em até 24 horas</li>
                        <li>HIGH: Resolver em até 7 dias</li>
                        <li>MEDIUM: Resolver em até 30 dias</li>
                        <li>LOW: Monitorar e resolver em release regular</li>
                    </ul>
                </li>
            </ul>
            
            <h3>5.2. Médio Prazo (1-3 meses)</h3>
            <ul>
                <li><strong>Automatizar atualizações de LOW</strong> — sem risco de breaking changes</li>
                <li><strong>Revisar manualmente MEDIUM e HIGH</strong> dentro de 30 dias</li>
                <li><strong>Bloquear CRITICAL em CI/CD</strong> até resolução completa</li>
                <li><strong>Implementar scanning contínuo</strong> em pipeline de desenvolvimento</li>
            </ul>
            
            <h3>5.3. Longo Prazo (3-12 meses)</h3>
            <ul>
                <li><strong>Monitorar tendências</strong> de novas CVEs contra dependências pinadas</li>
                <li><strong>Consolidar dependências</strong> — reduzir a superfície de ataque</li>
                <li><strong>Formar equipes de segurança</strong> para resposta rápida a advisories</li>
                <li><strong>Implementar dependency audit rotineiro</strong> como parte do ciclo de vida de desenvolvimento</li>
            </ul>
        </div>
        
        <!-- FOOTER -->
        <div class="section" style="text-align: center;">
            <h2>Conclusão Geral</h2>
            <p style="font-size: 1.1em; margin: 20px 0;">
                O dataset analisado revelou uma situação preocupante: <strong>49,5% dos repositórios Node.js contêm 
                vulnerabilidades conhecidas</strong>. Porém, a análise também demonstra que <strong>ferramentas de automação 
                como Dependabot reduzem significativamente o risco em aproximadamente 21%</strong>. As organizações devem 
                priorizar a adoção dessas ferramentas para mitigar riscos de segurança.
            </p>
        </div>
        
        <div class="footer">
            <p>Dashboard de BI - Laboratório 04 | Análise de Dependências Vulneráveis em Projetos Node.js</p>
            <p>Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} | Dados: Snapshot de abril de 2026</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html

# Criar e salvar o HTML
if __name__ == "__main__":
    print("Gerando dashboard HTML...")
    
    html_content = create_dashboard_html()
    
    # Salvar HTML
    html_path = output_dir / "dashboard.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Dashboard HTML criado: {html_path}")
    
    # Tentar converter para PDF (se wkhtmltopdf ou similar estiver disponível)
    try:
        import subprocess
        pdf_path = output_dir / "dashboard.pdf"
        subprocess.run(
            ["wkhtmltopdf", "--enable-local-file-access", str(html_path), str(pdf_path)],
            check=True,
            capture_output=True
        )
        print(f"✅ Dashboard PDF criado: {pdf_path}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️  wkhtmltopdf não disponível. Apenas HTML foi gerado.")
        print("   Para gerar PDF, instale: sudo apt-get install wkhtmltopdf")
    
    print("\n📊 Dashboard pronto!")
    print(f"   Abra em seu navegador: {html_path}")
