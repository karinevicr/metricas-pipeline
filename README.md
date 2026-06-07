# 📊 Análise de Métricas de Pipeline CI/CD

**Autora:** Karine Victoria Rosa da Paixão

## 📌 Sobre o Projeto

Este projeto tem como objetivo analisar o comportamento de um pipeline CI/CD real de uma API de tarefas desenvolvida em Flask. Através da coleta sistemática de métricas de execução do GitHub Actions, busca-se compreender padrões de desempenho, identificar gargalos e avaliar o impacto de diferentes cenários de teste no tempo total de execução do pipeline.

Foram realizadas 12 execuções controladas do workflow, variando parâmetros como:
- Quantidade de testes
- Tempo de execução dos testes (slow tests)
- Introdução de falhas intencionais (testes quebrados, dependências inválidas)
- Alterações na estrutura do workflow

Cada execução foi registrada e analisada através de um script de coleta que utiliza a API do GitHub para extrair métricas detalhadas por step, job e execução.

## 📁 Entregáveis

Para facilitar a navegação e avaliação, os principais artefatos do experimento estão organizados abaixo:

| Categoria | Arquivo / Link |
|-----------|----------------|
| 📦 Repositório | [karinevicr/metricas-pipeline](https://github.com/karinevicr/metricas-pipeline) |
| ⚙️ Workflow CI/CD | [.github/workflows/ci-pipeline.yml](.github/workflows/ci-pipeline.yml) |
| 📊 Script de coleta | [scripts/coleta_metricas.py](scripts/coleta_metricas.py) |
| 💾 Base de dados | [dados/metricas.csv](dados/metricas.csv) |
| 📈 Gráficos | • [Tempo total do pipeline](graficos/grafico1_tempo_total.png)<br>• [Tempo médio por job](graficos/grafico2_tempo_por_job.png)<br>• [Taxa de sucesso vs falha](graficos/grafico3_taxa_sucesso.png)<br>• [Quantidade de testes vs duração](graficos/grafico4_testes_vs_duracao.png) |
| 📄 Relatório técnico | [relatorio-tecnico.md](relatorio-tecnico.md) |
| 🔄 Como reproduzir | [Instruções abaixo](#como-reproduzir-o-experimento) |


## 🏗️ Visão Geral do Pipeline

O pipeline é definido no arquivo [.github/workflows/ci-pipeline.yml](.github/workflows/ci-pipeline.yml) e consiste em **dois jobs independentes** executados em paralelo:

### Estrutura do Workflow

| Job: tests | Job: lint |
|:-----------|:----------|
| 1. Checkout código | 1. Checkout código |
| 2. Setup Python 3.12 + cache | 2. Setup Python 3.12 + cache |
| 3. Instalar dependências | 3. Instalar dependências |
| 4. Executar pytest | 4. Executar flake8 |
| 5. Upload test-results | — |

### Características importantes

- **Execução paralela**: por não haver dependência declarada com `needs`, ambos os jobs rodam simultaneamente
- **Cache de dependências**: o pip é configurado com cache para acelerar instalações repetidas
- **Artefatos gerados**: resultados dos testes são salvos como artefato do GitHub Actions

### Coleta de métricas

O script `coleta_metricas.py` utiliza a API do GitHub para:
1. Listar todas as execuções do workflow
2. Para cada execução, buscar seus jobs e steps
3. Obter artefatos de teste quando disponíveis
4. Consolidar os dados em um arquivo CSV com granularidade por **step**


## 📈 Resumo dos Dados Coletados

### Visão geral da amostra

| Métrica | Valor |
|---------|-------|
| Total de execuções analisadas | 12 |
| Linhas no CSV (granularidade por step) | 204 |
| Execuções com sucesso ✅ | 9 (75%) |
| Execuções com falha ❌ | 3 (25%) |

### Estatísticas de tempo por execução

| Indicador | Valor |
|-----------|-------|
| Duração média | 38,4 s |
| Mediana da duração | 36 s |
| Menor duração observada | 13 s |
| Maior duração observada | 66 s |

### Tipos de falha identificados

| Tipo de falha | Ocorrências |
|---------------|-------------|
| `test_failure` (teste falhou) | 2 |
| `setup_failure` (ambiente quebrou) | 1 |

### 📋 Tabela completa das 12 execuções

| Run ID | Commit | Mensagem | Status | Duração | Artefato |
|--------|--------|----------|--------|---------|----------|
| 27095948645 | 19427f0 | exp: pipeline com testes passando | ✅ success | 35 s | 410 B |
| 27095909785 | db2f504 | exp: teste que consome muita memoria | ✅ success | 38 s | 427 B |
| 27095595987 | e206ca3 | exp: pipeline sem testes | ❌ failure | 28 s | 0 B |
| 27095465456 | a555129 | exp: roda testes em sequencia | ✅ success | 61 s | 412 B |
| 27095372028 | a65917c | exp: altera ordem de jobs | ✅ success | 31 s | 411 B |
| 27095241514 | 05f2b19 | exp: teste lento (30 segundos) | ✅ success | 66 s | 413 B |
| 27095230828 | 7dd2851 | exp: teste lento (15 segundos) | ✅ success | 44 s | 412 B |
| 27095220609 | 41efb57 | exp: teste lento (5 segundos) | ✅ success | 40 s | 411 B |
| 27095126439 | b083c6b | exp: requirements quebrado (lib fake) | ❌ failure | 13 s | 0 B |
| 27095052830 | a2de59c | exp: + 150 testes | ✅ success | 37 s | 874 B |
| 27095034559 | 595eca1 | exp: + 50 testes | ✅ success | 35 s | 581 B |
| 27094915826 | b8468c3 | exp: teste falhando | ❌ failure | 33 s | 0 B |

## 🔍 Análise dos Resultados

### 1. Gargalo principal: execução de testes

O maior impacto no tempo total do pipeline está concentrado na **execução dos testes**. Esta conclusão é evidenciada pelos experimentos com "teste lento":

- O run `27095241514` (30 segundos de espera artificial) atingiu **66 segundos** — o dobro da média
- Observa-se correlação praticamente linear entre tempo de teste e duração total

### 2. Efeito do cache de dependências

Todas as execuções analisadas utilizaram cache do pip, beneficiando a etapa de instalação de dependências. 

### 3. Impacto do paralelismo

Os jobs `tests` e `lint` são executados em paralelo, o que teoricamente reduz o tempo total percebido. Entretanto:

- Ambos compartilham etapas similares (checkout, setup Python, instalação de dependências)
- O ganho real do paralelismo depende do grau de independência entre os jobs
- Com a amostra atual, não é possível isolar o ganho exato

### 4. Padrões de falha

As falhas observadas se distribuíram da seguinte forma:
- **Falhas de teste (2 ocorrências)** — problemas no código ou nas asserções dos testes
- **Falha de setup (1 ocorrência)** — dependência inválida declarada no requirements.txt

> **Insight**: A maioria das falhas está relacionada ao comportamento da aplicação, não à infraestrutura do pipeline. Isso indica que o pipeline está bem configurado para detectar problemas reais de código.

### 5. Feedback para desenvolvimento

Com média de aproximadamente 38 segundos por execução, o pipeline oferece **feedback rápido** para o ciclo de desenvolvimento. 

**Ponto de atenção**: Experimentos com testes lentos propositais (30 segundos) elevaram o tempo para aproximadamente 66 segundos, patamar que começa a impactar a fluidez do desenvolvimento local e da integração contínua.

## ⚠️ Limitações do Experimento

Para uma interpretação correta dos resultados, é necessário reconhecer as seguintes limitações:

| Limitação | Impacto na análise |
|-----------|---------------------|
| Amostra pequena (12 execuções) | Baixa significância estatística para generalizações |
| CSV granular por step (não por execução) | Análises por execução exigem agregação pós-coleta |
| Ausência de grupo controle sem cache | Impossibilidade de quantificar o ganho do cache |
| Paralelismo não isolado experimentalmente | Ganho real do paralelismo não foi mensurado |
| Artefatos disponíveis apenas em runs bem-sucedidos | Métricas de testes podem apresentar viés de seleção |
| API do GitHub não retorna campo duration para repositórios públicos [fonte](https://docs.github.com/pt/actions/how-tos/monitor-workflows/view-job-execution-time) | As durações foram calculadas manualmente a partir dos timestamps dos jobs, introduzindo um pequeno overhead sistemático de aproximadamente 4 a 6 segundos por execução |

## Como Reproduzir o Experimento

### Pré-requisitos

- Python 3.12+
- Token de acesso pessoal do GitHub com permissão para leitura de Actions
- Repositório clonado ou forkado

### Passo a passo

```bash
# 1. Clonar o repositório
git clone https://github.com/karinevicr/metricas-pipeline.git

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. (Opcional) Executar a API localmente para validação
python src/app.py
python -m pytest -q

# 4. Configurar as credenciais do GitHub
Editar scripts/.env com:
GITHUB_TOKEN=seu_token_aqui
REPO_NAME=karinevicr/metricas-pipeline

# 5. Executar o coletor de métricas
python scripts/coleta_metricas.py

# 6. Gerar os gráficos
python scripts/gerar_graficos.py
```

## 📂 Arquivos do Projeto

| Arquivo | Descrição |
|---------|-----------|
| `src/app.py` | API Flask de tarefas (aplicação sob teste) |
| `scripts/coleta_metricas.py` | Coleta de métricas via API do GitHub |
| `scripts/gerar_graficos.py` | Geração dos gráficos a partir do CSV |
| `dados/metricas.csv` | Base de dados completa das execuções |
| `tests/test_tarefas.py` | Testes unitários da aplicação |
| `.github/workflows/ci-pipeline.yml` | Definição do pipeline CI/CD |
