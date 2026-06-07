# metricas-pipeline

Projeto de analise de pipeline CI para a API de tarefas em Flask. O objetivo e registrar execucoes reais do GitHub Actions, coletar metricas do workflow, gerar graficos e responder perguntas sobre desempenho, falhas e feedback para desenvolvimento.

## Como executar o projeto

Instale as dependencias do projeto e rode os comandos abaixo na raiz do repositório.

```bash
pip install -r requirements.txt
python src/app.py
```

Em outra janela de terminal, para validar a aplicacao com testes:

```bash
python -m pytest -q
```

Para coletar as metricas do GitHub Actions, configure `scripts/.env` com `GITHUB_TOKEN` e `REPO_NAME` e execute:

```bash
python scripts/coleta_metricas.py
```

Para gerar os graficos a partir do CSV coletado:

```bash
python scripts/gerar_graficos.py
```

## O que o pipeline faz

O workflow principal esta em [.github/workflows/ci-pipeline.yml](.github/workflows/ci-pipeline.yml) e executa dois jobs independentes, `lint` e `tests`, para permitir comparar execucao separada das verificacoes:

- checkout do codigo em cada job
- setup do Python 3.12 com cache de `pip`
- instalacao das dependencias em cada job
- lint com `flake8` no job `lint`
- execucao dos testes com `pytest` no job `tests`
- upload do artefato `test-results` no job `tests`

O script de coleta usa a API do GitHub para ler as execucoes do workflow, buscar os jobs, ler os steps de cada job, ler o artefato de testes quando existe e salvar tudo em [dados/metricas.csv](dados/metricas.csv).

## Resumo dos dados coletados

O experimento atual registrou 12 execucoes do workflow.

- 7 execucoes com sucesso
- 5 execucoes com falha
- media do tempo total do pipeline: 32,4 s
- mediana do tempo total do pipeline: 32 s
- maior duracao observada: 60 s
- menor duracao observada: 13 s

## Evidencias reais das execucoes

As tabelas abaixo apontam para os runs reais do GitHub Actions e para os commits usados no experimento.

| Run ID | Commit | Status | Duracao | Run | Commit |
| --- | --- | --- | --- | --- | --- |
| 27048990842 | 83d469d | failure | 25 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048990842) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/83d469d) |
| 27048852685 | 73a99e5 | success | 32 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048852685) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/73a99e5) |
| 27048793074 | 777111b | success | 32 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048793074) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/777111b) |
| 27048669674 | 901d400 | failure | 26 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048669674) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/901d400) |
| 27048597435 | 7ebd17a | success | 40 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048597435) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/7ebd17a) |
| 27048558487 | 32663bc | success | 60 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048558487) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/32663bc) |
| 27048522053 | 1ef3d29 | failure | 13 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048522053) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/1ef3d29) |
| 27048447079 | 3322e2d | success | 36 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048447079) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/3322e2d) |
| 27047859538 | 692623f | failure | 27 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27047859538) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/692623f) |
| 27047816410 | eb05e60 | success | 36 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27047816410) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/eb05e60) |
| 27047637253 | 39a2b4e | success | 34 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27047637253) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/39a2b4e) |
| 27047252735 | 8a57bb4 | failure | 28 s | [abrir run](https://github.com/karinevicr/metricas-pipeline/actions/runs/27047252735) | [abrir commit](https://github.com/karinevicr/metricas-pipeline/commit/8a57bb4) |

## Graficos gerados

Os graficos sao gerados em [graficos/](graficos) e podem ser abertos diretamente pelo README.

- [Tempo total do pipeline](graficos/grafico1_tempo_total.png)
- [Tempo medio por job](graficos/grafico2_tempo_por_job.png)
- [Taxa de sucesso vs falha](graficos/grafico3_taxa_sucesso.png)
- [Quantidade de testes vs duracao](graficos/grafico4_testes_vs_duracao.png)

## Respostas para o relatorio

### 1. Qual etapa mais contribuiu para o tempo total do pipeline?

O dado coletado agora mede o tempo total do workflow, do job e de cada step. Mesmo assim, o comportamento mais custoso continuou aparecendo na etapa de testes, principalmente no run [27048558487](https://github.com/karinevicr/metricas-pipeline/actions/runs/27048558487), que ficou em 60 s por causa do teste com espera artificial. Nos casos de falha, o pipeline terminou mais cedo, entao lint, setup ou testes interrompidos pesaram menos no total.

### 2. Houve diferenca significativa entre execucoes com e sem cache?

Nao foi possivel isolar isso com rigor. O workflow atual usa cache de `pip` em todas as execucoes, entao o CSV nao traz um grupo controle sem cache. Com os dados disponiveis, nao da para afirmar uma diferenca significativa entre com e sem cache.

### 3. O paralelismo reduziu o tempo total? Em que condicoes?

Ainda nao ha evidencia suficiente para afirmar ganho real de paralelismo, porque os novos jobs ainda repetem a mesma base de preparacao e os dados historicos foram coletados antes da separacao. Para comparar de forma real, seria preciso repetir os runs apos a mudanca e comparar o tempo total com o mesmo conjunto de entradas.

### 4. Quais falhas foram mais frequentes?

As falhas mais frequentes foram `lint_failure` e `test_failure`, com 2 ocorrencias cada. `setup_failure` apareceu 1 vez. Isso mostra que o pipeline sofre mais com problemas de codigo e com problemas de validacao do que com a configuracao basica do ambiente.

### 5. O pipeline fornece feedback rapido o suficiente para o desenvolvedor?

Em media, sim: o pipeline ficou em 32,4 s, com mediana de 32 s. Para um ciclo de desenvolvimento local isso e um feedback bom. O ponto de atencao e que alguns cenarios artificiais elevaram a duracao para 60 s, o que ja comeca a ficar menos confortavel para iteracao frequente.

### 6. Que melhorias poderiam ser feitas no pipeline?

As melhores melhorias agora seriam comparar os dois jobs em runs novos, reduzir a preparacao duplicada entre eles, registrar melhor a quantidade real de testes executados, testar um cenario real de cache contra um cenario sem cache e considerar paralelismo adicional quando fizer sentido.

### 7. Quais limitacoes existem nos dados coletados?

As principais limitacoes sao o tamanho pequeno da amostra, a ausencia de um grupo controle sem cache, a falta de um experimento de paralelismo apos a separacao dos jobs e a inconsistencia do campo de quantidade de testes em parte das execucoes.

### 8. Como essa analise poderia apoiar decisoes de engenharia?

Ela ajuda a decidir onde investir para reduzir tempo de feedback: cache, paralelismo, separacao de jobs, melhoria dos testes e do lint. Tambem apoia a definicao de metas de CI, como teto de duracao por workflow e criterios de alerta quando o tempo medio subir.

## Hipotese inicial versus resultado observado

Hipotese inicial: aumentar a quantidade de testes, o tamanho do trabalho e as verificacoes deveria alongar o pipeline de forma mais ou menos proporcional.

Resultado observado: o tempo nao cresceu de forma linear. O run mais lento foi o de espera artificial em teste, e varios runs com falha terminaram mais cedo do que execucoes bem-sucedidas. Isso indica que o comportamento do pipeline e mais sensivel a interrupcoes, esperas artificiais e tipo de falha do que apenas ao volume bruto de testes.

## Resultados inesperados

1. As execucoes com falha foram, em media, mais rapidas que as execucoes com sucesso. Isso acontece porque o workflow para mais cedo quando encontra erro, entao o tempo total cai.
2. O experimento com 150 testes nao foi o mais lento. O maior tempo veio do caso com espera artificial de 30 s, o que mostra que a natureza do teste pesa mais do que o numero isolado de testes.

## Limitacoes do experimento

- O workflow agora tem dois jobs, mas eles ainda compartilham a maior parte da preparacao, entao o ganho de paralelismo ainda precisa ser medido em novos runs.
- O CSV agora captura duracao total do workflow, do job e de cada step.
- O campo de contagem de testes nao ficou confiavel em todas as execucoes.
- Nao houve um experimento controlado com e sem cache no mesmo conjunto de entradas.
- A amostra tem apenas 12 execucoes, o que e suficiente para observacao inicial, mas nao para conclusoes estatisticamente fortes.

## Arquivos principais

- [API Flask](src/app.py)
- [Coleta de metricas](scripts/coleta_metricas.py)
- [Geracao de graficos](scripts/gerar_graficos.py)
- [Dados coletados](dados/metricas.csv)
- [Teste da aplicacao](tests/test_vazio.py)