### Autora: Karine Victoria Rosa da Paixão

## Introdução

Este projeto analisa um pipeline CI/CD real de uma API de tarefas em Flask. O objetivo é registrar execuções reais do GitHub Actions, coletar métricas do workflow, gerar gráficos e interpretar o comportamento do pipeline sob diferentes condições de teste, falha e execução.

## Entregáveis

Para facilitar a avaliação e navegação pelo repositorio, esta seção concentra os links principais do projeto e do experimento:

- Repositório GitHub: [karinevicr/metricas-pipeline](https://github.com/karinevicr/metricas-pipeline)
- Workflow do GitHub Actions: [.github/workflows/ci-pipeline.yml](.github/workflows/ci-pipeline.yml)
- Script de coleta das métricas: [scripts/coleta_metricas.py](scripts/coleta_metricas.py)
- Base de dados gerada em CSV: [dados/metricas.csv](dados/metricas.csv)
- Gráficos produzidos:
	- [Tempo total do pipeline](graficos/grafico1_tempo_total.png)
	- [Tempo médio por job](graficos/grafico2_tempo_por_job.png)
	- [Taxa de sucesso vs falha](graficos/grafico3_taxa_sucesso.png)
	- [Quantidade de testes vs duração](graficos/grafico4_testes_vs_duracao.png)
- Relatório técnico em Markdown: [relatorio-tecnico.md](relatorio-tecnico.md)
- Como reproduzir o experimento: veja a seção [Como reproduzir](#como-reproduzir-o-experimento)


## Visão geral do pipeline

O workflow principal está em [.github/workflows/ci-pipeline.yml](.github/workflows/ci-pipeline.yml) e possui dois jobs independentes: `tests` e `lint`.

Como não existe dependência declarada entre eles com `needs`, os dois jobs são disparados em paralelo pelo GitHub Actions. Dentro de cada job, os steps executam em sequência.

O fluxo atual é composto por:

- checkout do código em cada job
- setup do Python 3.12 com cache de `pip`
- instalação das dependências em cada job
- execução do `pytest` no job `tests`
- upload do artefato `test-results` no job `tests`
- execução do `flake8` no job `lint`

O script de coleta usa a API do GitHub para ler as execuções do workflow, buscar os jobs, ler os steps de cada job, obter o artefato de testes quando ele existe e salvar tudo em [dados/metricas.csv](dados/metricas.csv).

## Resumo dos dados coletados

O conjunto atual de dados contém 12 execuções do workflow e 204 linhas no CSV.

Isso acontece porque a coleta está no nível de step: cada execução gera várias linhas, uma para cada step de cada job. Como o workflow possui dois jobs e vários steps por job, o arquivo cresce rapidamente mesmo com poucas execuções.

### Indicadores consolidados por execução

- Total de execuções analisadas: 12
- Execuções com sucesso: 9
- Execuções com falha: 3
- Duração média por execução: 33,33 s
- Mediana da duração por execução: 30,5 s
- Menor duração observada: 9 s
- Maior duração observada: 61 s

### Distribuição das falhas

- `test_failure`: 2 ocorrências
- `setup_failure`: 1 ocorrência

### Tabela das 12 execuções mais recentes

| Run ID | Commit | Mensagem | Status | Duração estimada | Artefato |
| --- | --- | --- | --- | --- | --- |
| 27095948645 | 19427f0 | exp: pipeline com testes passando | success | 31 s | 410 bytes |
| 27095909785 | db2f504 | exp: teste que consome muita memoria | success | 32 s | 427 bytes |
| 27095595987 | e206ca3 | exp: pipeline sem testes | failure | 23 s | 0 bytes |
| 27095465456 | a555129 | exp: roda testes em sequencia | success | 55 s | 412 bytes |
| 27095372028 | a65917c | exp: altera ordem de jobs | success | 27 s | 411 bytes |
| 27095241514 | 05f2b19 | exp: teste lento (30 segundos) | success | 61 s | 413 bytes |
| 27095230828 | 7dd2851 | exp: teste lento (15 segundos) | success | 40 s | 412 bytes |
| 27095220609 | 41efb57 | exp: teste lento (5 segundos) | success | 34 s | 411 bytes |
| 27095126439 | b083c6b | exp: requirements quebrado (lib fake) | failure | 9 s | 0 bytes |
| 27095052830 | a2de59c | exp: + 150 testes | success | 30 s | 874 bytes |
| 27095034559 | 595eca1 | exp: + 50 testes | success | 30 s | 581 bytes |
| 27094915826 | b8468c3 | exp: teste falhando | failure | 28 s | 0 bytes |

## Análise dos resultados atuais

### 1. Etapa que mais pesa no tempo total

O maior custo continua concentrado na execução dos testes. Isso aparece com clareza nos experimentos com teste lento, principalmente no run `27095241514`, que atingiu 61 s por causa da espera artificial de 30 segundos. Já as falhas interrompem o fluxo antes do fim natural, então tendem a encurtar o tempo total.

### 2. Impacto do cache

O workflow já usa cache de `pip` em todas as execuções do experimento atual. Isso melhora a instalação de dependências, mas não permite comparar diretamente um cenário com cache contra outro sem cache, porque não há grupo controle na amostra atual.

### 3. Impacto do paralelismo

Os jobs `tests` e `lint` estão separados e são executados em paralelo no GitHub Actions. Na prática, isso ajuda a reduzir o tempo total percebido quando um job não depende do outro. Ainda assim, o ganho exato precisa ser interpretado com cuidado, porque ambos compartilham uma parte importante da preparação do ambiente, e a amostra continua pequena.

### 4. Tipo de falha mais frequente

As falhas mais frequentes foram de teste. Isso indica que a maior parte dos problemas detectados pelo pipeline está ligada ao comportamento da aplicação e dos testes automatizados, e não à configuração básica do workflow.

### 5. Feedback para o desenvolvimento

Para desenvolvimento local e validação contínua, um pipeline com média próxima de 33 s ainda fornece feedback razoavelmente rápido. O ponto de atenção são os cenários artificiais, que ampliam a duração e tornam a iteração menos confortável quando o teste fica propositalmente mais pesado.

## Limitações do experimento

- A amostra continua pequena, com 12 execuções.
- O CSV é granular por step, então não representa uma linha por execução.
- Não há um experimento controlado com e sem cache no mesmo conjunto de entradas.
- O paralelismo ainda precisa ser comparado com mais runs após a alteração do workflow.
- Algumas métricas de testes dependem do artefato `test-results`, então podem variar conforme o sucesso do job e a disponibilidade do artefato.

## Como reproduzir o experimento

1. Clone o repositório e instale as dependências:

```bash
git clone https://github.com/karinevicr/metricas-pipeline.git
```

```bash
pip install -r requirements.txt
```

2. Execute a API e valide os testes localmente, se desejar conferir o comportamento da aplicação:

```bash
python src/app.py
python -m pytest -q
```

3. Configure [scripts/.env](scripts/.env) com `GITHUB_TOKEN` e `REPO_NAME` para permitir a coleta de dados do GitHub Actions.

4. Rode o coletor para gerar ou atualizar [dados/metricas.csv](dados/metricas.csv):

```bash
python scripts/coleta_metricas.py
```

5. Gere os gráficos a partir do CSV:

```bash
python scripts/gerar_graficos.py
```

6. Abra o relatório técnico em [relatorio-tecnico.md](relatorio-tecnico.md) e os gráficos da pasta [graficos/](graficos) para revisar os resultados.

## Arquivos principais

- [API Flask](src/app.py)
- [Coleta de métricas](scripts/coleta_metricas.py)
- [Geração de gráficos](scripts/gerar_graficos.py)
- [Dados coletados](dados/metricas.csv)
- [Teste da aplicação](tests/test_terefas.py)