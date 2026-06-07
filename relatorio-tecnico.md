# Relatório Técnico do Experimento CI/CD

## 1. Contexto

Este projeto documenta um experimento de observação de pipeline CI/CD em uma API de tarefas desenvolvida em Flask. O objetivo é analisar como o GitHub Actions se comporta em cenários reais de execução, falha, cache, separação de jobs e testes com durações diferentes.

O pipeline foi executado em diferentes commits para produzir um histórico de métricas. Essas métricas foram extraídas automaticamente e consolidadas em [dados/metricas.csv](dados/metricas.csv), que é a base usada para as análises e os gráficos do trabalho.

## 2. Estrutura do pipeline

O workflow principal está em [.github/workflows/ci-pipeline.yml](.github/workflows/ci-pipeline.yml) e possui dois jobs:

- `tests`, responsável por instalar dependências e executar `pytest`
- `lint`, responsável por instalar dependências e executar `flake8`

Como não há dependência explícita entre os jobs com `needs`, os dois são tratados pelo GitHub Actions como independentes e podem executar em paralelo. Dentro de cada job, os steps seguem em sequência.

O workflow usa cache de `pip`, o que reduz o custo de repetição da instalação de pacotes em execuções sucessivas.

## 3. Coleta de métricas

A coleta é feita pelo script [scripts/coleta_metricas.py](scripts/coleta_metricas.py), que consulta a API do GitHub para:

1. listar as execuções recentes do workflow
2. recuperar os jobs de cada execução
3. recuperar os steps de cada job
4. verificar a existência do artefato `test-results`
5. extrair métricas de teste quando o artefato está disponível
6. salvar os dados consolidados em CSV

O arquivo gerado possui granularidade de step. Isso significa que uma única execução aparece em várias linhas, uma para cada step de cada job. Essa decisão melhora a rastreabilidade, mas aumenta o número total de linhas do arquivo.

## 4. Base de dados atual

A base atual contém 12 execuções do workflow e 204 linhas no CSV.

### 4.1 Resumo agregado

- Execuções com sucesso: 9
- Execuções com falha: 3
- Duração média por execução: 38,4 s
- Mediana da duração por execução: 36 s
- Menor duração: 13 s
- Maior duração: 66 s

### 4.2 Falhas observadas

- `test_failure`: 2 ocorrências
- `setup_failure`: 1 ocorrência

### 4.3 Execuções registradas

| Run ID | Commit | Mensagem | Status | Duração estimada | Artefato |
| --- | --- | --- | --- | --- | --- |
| 27095948645 | 19427f0 | exp: pipeline com testes passando | success | 35 s | 410 bytes |
| 27095909785 | db2f504 | exp: teste que consome muita memoria | success | 38 s | 427 bytes |
| 27095595987 | e206ca3 | exp: pipeline sem testes | failure | 28 s | 0 bytes |
| 27095465456 | a555129 | exp: roda testes em sequencia | success | 61 s | 412 bytes |
| 27095372028 | a65917c | exp: altera ordem de jobs | success | 31 s | 411 bytes |
| 27095241514 | 05f2b19 | exp: teste lento (30 segundos) | success | 66 s | 413 bytes |
| 27095230828 | 7dd2851 | exp: teste lento (15 segundos) | success | 44 s | 412 bytes |
| 27095220609 | 41efb57 | exp: teste lento (5 segundos) | success | 40 s | 411 bytes |
| 27095126439 | b083c6b | exp: requirements quebrado (lib fake) | failure | 13 s | 0 bytes |
| 27095052830 | a2de59c | exp: + 150 testes | success | 37 s | 874 bytes |
| 27095034559 | 595eca1 | exp: + 50 testes | success | 35 s | 581 bytes |
| 27094915826 | b8468c3 | exp: teste falhando | failure | 33 s | 0 bytes |

## 5. Leitura dos resultados

### 5.1 Tempo total

O tempo médio por execução ficou em torno de 38,4 segundos. Isso sugere um feedback razoavelmente rápido para um fluxo de desenvolvimento local, especialmente considerando que o pipeline contém duas validações distintas: testes e lint.

O run mais lento foi o `27095241514`, com 66 s, motivado pelo teste com espera artificial de 30 segundos. Esse resultado mostra que a natureza do teste pesa mais do que o número bruto de casos.

### 5.2 Falhas e comportamento de encerramento

As falhas aparecem com menor duração porque o workflow interrompe parte do processamento assim que encontra erro. Isso explica por que alguns runs com falha ficaram abaixo da média das execuções bem-sucedidas.

### 5.3 Cache e preparação do ambiente

O cache de `pip` reduz o custo de reinstalação das dependências, mas o experimento atual não contém um grupo controle sem cache. Portanto, não há base suficiente para afirmar ganho quantitativo isolando apenas essa variável.

### 5.4 Paralelismo

Os jobs estão independentes e podem executar em paralelo. Isso é bom para reduzir o tempo total de feedback. Porém, como ambos os jobs repetem a instalação de dependências e a amostra ainda é pequena, o efeito líquido do paralelismo precisa ser reavaliado com mais execuções.

## 6. Gráficos gerados

<div align="center">
  <p> <b>Figura 1 </b> - Grafico 1</p>
<img src="graficos/grafico1_tempo_total.png" alt="grafico 1" />
  <p><b>Fonte:</b> Material elaborado pela autora.</p>
</div>

Execuções com falha (em vermelho) são visivelmente mais curtas que as bem-sucedidas, pois o pipeline interrompe o processamento ao encontrar um erro crítico - o caso mais extremo (b083c6b) durou apenas 13 segundos. O outlier de 66 segundos (05f2b19) evidencia o impacto de um teste com espera artificial de 30 segundos, mostrando que a natureza do teste pesa mais que sua quantidade. A maioria das execuções bem-sucedidas concentra-se na faixa de 30-40 segundos, indicando um custo fixo saudável para o pipeline.

<div align="center">
  <p> <b>Figura 2</b> - Grafico 2</p>
<img src="graficos/grafico2_tempo_por_job.png" alt="grafico 2" />
  <p><b>Fonte:</b> Material elaborado pela autora.</p>
</div>

O job de tests é o grande gargalo, com média de aproximadamente 35 segundos, enquanto o lint é mais leve (cerca de 29 segundos). Graças ao paralelismo entre os jobs (não há dependência explícita com needs), o tempo total do pipeline é dominado apenas pelo job mais lento (tests), e não pela soma de ambos - caso contrário, o pipeline levaria cerca de 60 segundos em vez dos 30-40 observados.

<div align="center">
  <p> <b>Figura 3</b> - Grafico 3</p>
<img src="graficos/grafico3_taxa_sucesso.png" alt="grafico 3" />
  <p><b>Fonte:</b> Material elaborado pela autora.</p>
</div>

O pipeline teve 75% de sucesso (9 em 12 execuções), o que é saudável para um ambiente de experimentação. As três falhas foram intencionais e permitiram observar diferentes modos de falha: setup quebrado (falha rápida em 13s), pipeline sem artefato de testes (falha intermediária em 28s) e teste falhando (falha após execução completa). Essa diversidade enriqueceu a análise do comportamento do CI/CD.

<div align="center">
  <p> <b>Figura 4</b> - Grafico 4</p>
<img src="graficos/grafico4_testes_vs_duracao.png" alt="grafico 4" />
  <p><b>Fonte:</b> Material elaborado pela autora.</p>
</div>

Surpreendentemente, não há correlação direta entre o número de testes e a duração do pipeline. O commit com +150 testes rodou em ~37s, enquanto o teste lento com sleep(30) demorou 66s mesmo com poucos testes. Isso demonstra que a composição e a natureza dos testes (operações de I/O, espera ativa, processamento pesado) impactam muito mais o tempo de resposta do que a simples quantidade de casos de teste.

Os gráficos se encontram na pasta [graficos/](graficos):

- [Tempo total do pipeline](graficos/grafico1_tempo_total.png)
- [Tempo médio por job](graficos/grafico2_tempo_por_job.png)
- [Taxa de sucesso vs falha](graficos/grafico3_taxa_sucesso.png)
- [Quantidade de testes vs duração](graficos/grafico4_testes_vs_duracao.png)

## 7. Limitações do experimento

- A base possui apenas 12 execuções.
- O CSV registra o nível de step, o que amplia o número de linhas.
- Não há experimento controlado com e sem cache no mesmo conjunto de entradas.
- O paralelismo ainda precisa ser medido com mais runs após a separação dos jobs.
- Algumas métricas dependem do artefato de testes e podem variar conforme o sucesso do job.

## 8. Como reproduzir

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Execute os testes locais:

```bash
python -m pytest -q
```

3. Configure [scripts/.env](scripts/.env) com `GITHUB_TOKEN` e `REPO_NAME`.

4. Execute o coletor para atualizar [dados/metricas.csv](dados/metricas.csv):

```bash
python scripts/coleta_metricas.py
```

5. Gere os gráficos:

```bash
python scripts/gerar_graficos.py
```

6. Abra o workflow em [.github/workflows/ci-pipeline.yml](.github/workflows/ci-pipeline.yml), o relatório em [relatorio-tecnico.md](relatorio-tecnico.md) e os gráficos da pasta [graficos/](graficos) para revisar o experimento completo.