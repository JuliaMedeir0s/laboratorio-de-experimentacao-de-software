# Relatório de Saída - Dashboard BI
## Análise de Dependências Vulneráveis em Projetos Node.js

Este diretório contém todos os arquivos de saída gerados para o Dashboard BI do Laboratório 04.

## 📋 Arquivos Disponíveis

### 1. **dashboard.pdf** (Auxiliar)
   - Relatório em PDF com 10 páginas
   - Contém todas as visualizações e análises
   - Pronto para impressão
   - **Observação:** o enunciado do lab pede dashboard em Power BI/Tableau/Looker Studio; este PDF é um artefato de apoio.

### 2. **dashboard.html** (Interativo)
   - Versão interativa do dashboard
   - Pode ser aberta em qualquer navegador
   - Todas as gráficos estão embutidos (base64)
   - Suporta impressão via navegador (Ctrl+P → Imprimir como PDF)

### 3. **RELATORIO_DASHBOARD.md** (Markdown)
   - Relatório completo em formato Markdown
   - Inclui todas as análises, tabelas e conclusões
   - Pronto para ser integrado ao artigo de TIS 6
   - Pode ser convertido para diferentes formatos
   - Gerado a partir de `dataset/ANALISE_RQ.md` (sem hard-code)

### 4. **Gráficos Individuais**
   - Todos os gráficos estão em `/dataset/graficos/`
   - Podem ser usados individualmente no artigo

## 📊 Estrutura do Dashboard

O dashboard está organizado em 5 seções principais:

### Seção 1: Caracterização do Dataset
- Visão geral do dataset (ver `dataset_overview`)
- Distribuição de ferramentas de automação (Dependabot, Renovate, Snyk)
- Estatísticas de dependências e versões

### Seção 2: RQ1 - Frequência de Vulnerabilidades
- Taxa de repositórios vulneráveis (ver métricas calculadas)
- Distribuição de CVEs por repositório
- Análise comparativa por grupo de automação

### Seção 3: RQ2 - Níveis de Severidade
- Distribuição de severidade (MEDIUM, HIGH, LOW, CRITICAL, UNKNOWN)
- Heatmap de severidade por grupo
- Análise de risco operacional

### Seção 4: RQ3 - Impacto da Automação
- Comparação de ferramentas (Dependabot vs Sem bot vs Renovate)
- Redução relativa de risco (ver tabela de comparação direta)
- Scatter plots de tendências

### Seção 5: Recomendações
- Ações curto prazo (auditar, adotar automação)
- Ações médio prazo (automatizar updates)
- Ações longo prazo (monitorar tendências)

## 🎯 Como Usar os Arquivos

### Para a Entrega Final
1. **Montar o dashboard em uma ferramenta de BI** (Power BI/Tableau/Looker Studio)
   - Gere os CSVs em `lab04/bi/tables/` e siga o guia em `lab04/bi/README.md`
2. **Exportar o dashboard em PDF** a partir da ferramenta de BI
3. **Atualizar artigo TIS 6**: 
   - Inclua a Seção 3 (Metodologia) com gráficos de caracterização
   - Inclua a Seção 4 (Resultados) com gráficos das RQs
   - Use o Markdown como referência

### Para Apresentação em Aula
- Use `dashboard.html` em um navegador
- Ou imprima o PDF para apresentação física

### Para Análise Detalhada
- Abra `RELATORIO_DASHBOARD.md` para ver todas as métricas
- Verifique os gráficos individuais em `/dataset/graficos/`

## 📈 Insights Principais

### RQ1: Frequência
- Ver valores atualizados no relatório Markdown e em `lab04/bi/tables/`

### RQ2: Severidade
- Ver distribuição atualizada no relatório Markdown e em `lab04/bi/tables/`

### RQ3: Impacto da Automação
- Ver tabelas de comparação em `lab04/bi/tables/`

## 🔧 Scripts Utilizados

### `create_dashboard.py`
- Gera dashboard HTML com todos os gráficos embutidos
- Usa base64 para incorporar imagens

### `create_pdf_reports.py`
- Gera PDF a partir das páginas
- Combina texto e gráficos em um documento estruturado

### `create_pdf_pages.py`
- Gera páginas individuais em PNG (se matplotlib estiver disponível)

## 📝 Notas Técnicas

- **Formato HTML**: Usa CSS Grid e Flexbox para responsividade
- **Formato PDF**: 10 páginas, suporta impressão em alta qualidade
- **Gráficos**: PNG de alta resolução (150 DPI)
- **Dados**: Baseado em análise completa em `/dataset/ANALISE_RQ.md`

## 📞 Metodologia de Coleta

- **Ferramenta de Análise**: OSV (Open Source Vulnerability) API
- **Validação**: NVD (National Vulnerability Database)
- **Severidade**: CVSS base score normalizado
- **Período**: ver `dataset/ANALISE_RQ.md`
- **Amostra**: ver `dataset/ANALISE_RQ.md`

## ✅ Checklist de Entrega

- [x] Dashboard PDF completo
- [x] Dashboard HTML interativo
- [x] Relatório em Markdown
- [x] Gráficos individuais
- [x] Análise de RQ1, RQ2, RQ3
- [x] Recomendações
- [x] Conclusões

## 📂 Estrutura de Diretórios

```
lab04/
├── README.md (especificação original)
├── dataset/
│   ├── ANALISE_RQ.md (análise detalhada)
│   ├── graficos/ (todos os gráficos)
│   ├── scan_por_repo/ (dados brutos)
│   └── *.json (dados processados)
├── outputs/ (ESTA PASTA)
│   ├── dashboard.pdf ⭐
│   ├── dashboard.html
│   ├── RELATORIO_DASHBOARD.md
│   └── README.md (este arquivo)
├── create_dashboard.py
├── create_pdf_reports.py
└── create_pdf_pages.py
```

---

**Data de Geração:** $(date +%d/%m/%Y)  
**Status:** ✅ Completo e pronto para entrega
