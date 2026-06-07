import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
GRAFICOS_DIR = ROOT_DIR / 'graficos'
CSV_FILE = ROOT_DIR / 'dados' / 'metricas.csv'

GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV_FILE)

# Calcular duração REAL do workflow a partir dos jobs
workflow_durations = []
for run_id in df['run_id'].unique():
    df_run = df[df['run_id'] == run_id]
    min_start = pd.to_datetime(df_run['timestamp']).min()
    max_end = pd.to_datetime(df_run['job_duration']).max()
    duration = (max_end - min_start).total_seconds()
    workflow_durations.append({'run_id': run_id, 'workflow_seconds': duration})

df_durations = pd.DataFrame(workflow_durations)

# Juntar com os dados das execuções
df_execucao = df.drop_duplicates(subset=['run_id']).copy()
df_execucao = df_execucao.merge(df_durations, on='run_id')
df_execucao['timestamp'] = pd.to_datetime(df_execucao['timestamp'])

# Calcular duração dos jobs
df_jobs = df.drop_duplicates(subset=['run_id', 'job_name']).copy()
df_jobs['timestamp'] = pd.to_datetime(df_jobs['timestamp'])
df_jobs['job_duration'] = pd.to_datetime(df_jobs['job_duration'])
df_jobs['job_seconds'] = (df_jobs['job_duration'] - df_jobs['timestamp']).dt.total_seconds()

# Ordenar
df_execucao = df_execucao.sort_values('timestamp')
df_execucao = df_execucao.reset_index(drop=True)
df_execucao['execucao'] = df_execucao.index + 1

print(f"📊 Durações calculadas: min={df_execucao['workflow_seconds'].min():.0f}s, max={df_execucao['workflow_seconds'].max():.0f}s")

# Gráfico 1
plt.figure(figsize=(12, 6))
cores_status = ['#2E86DE' if s == 'success' else '#E74C3C' for s in df_execucao['status']]
bars = plt.bar(df_execucao['execucao'], df_execucao['workflow_seconds'], color=cores_status, width=0.7)
plt.bar_label(bars, fmt='%.0f', padding=3, fontsize=8)
plt.xticks(df_execucao['execucao'], [f"{i}\n{sha}" for i, sha in zip(df_execucao['execucao'], df_execucao['commit_sha'])])
plt.xlabel('Execução / SHA curto')
plt.ylabel('Duração (segundos)')
plt.title('Tempo total do pipeline por execução')
plt.grid(True, alpha=0.3)
plt.legend(handles=[
    plt.Rectangle((0, 0), 1, 1, color='#2E86DE', label='success'),
    plt.Rectangle((0, 0), 1, 1, color='#E74C3C', label='failure')
])
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico1_tempo_total.png')
plt.close()
print("  ✅ Gráfico 1: tempo_total.png")

# Gráfico 2
job_times = df_jobs.groupby('job_name')['job_seconds'].mean().sort_values()
plt.figure(figsize=(10, 6))
job_times.plot(kind='barh', color='skyblue')
plt.xlabel('Duração média (segundos)')
plt.ylabel('Job')
plt.title('Tempo médio por job')
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico2_tempo_por_job.png')
plt.close()
print("  ✅ Gráfico 2: tempo_por_job.png")

# Gráfico 3
status_counts = df_execucao['status'].value_counts()
plt.figure(figsize=(8, 8))
colors = ['#2E86DE' if s == 'success' else '#E74C3C' for s in status_counts.index]
plt.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=colors, startangle=90)
plt.title('Taxa de sucesso vs falha')
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico3_taxa_sucesso.png')
plt.close()
print("  ✅ Gráfico 3: taxa_sucesso.png")

# Gráfico 4
df_testes = df_execucao.dropna(subset=['test_count'])
plt.figure(figsize=(10, 6))
if len(df_testes) < 2:
    plt.text(0.5, 0.5, 'Sem dados suficientes', ha='center', va='center', fontsize=12)
else:
    plt.scatter(df_testes['test_count'], df_testes['workflow_seconds'], alpha=0.75, s=120, color='#2E86DE')
    for _, row in df_testes.iterrows():
        plt.annotate(row['commit_sha'], (row['test_count'], row['workflow_seconds']), xytext=(6, 6), textcoords='offset points', fontsize=8)
plt.xlabel('Quantidade de testes')
plt.ylabel('Duração do pipeline (segundos)')
plt.title('Relação: quantidade de testes × duração do pipeline')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico4_testes_vs_duracao.png')
plt.close()
print("  ✅ Gráfico 4: testes_vs_duracao.png")

print(f"\n🎉 Gráficos salvos em {GRAFICOS_DIR}")