import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
GRAFICOS_DIR = ROOT_DIR / 'graficos'
CSV_FILE = ROOT_DIR / 'dados' / 'metricas.csv'

# Criar pasta para os gráficos
GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)

# Carregar os dados do CSV
df = pd.read_csv(CSV_FILE)

# Converter timestamps para datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['workflow_duration'] = pd.to_datetime(df['workflow_duration'])
df['job_duration'] = pd.to_datetime(df['job_duration'])

# Durações em segundos
df['workflow_seconds'] = (df['workflow_duration'] - df['timestamp']).dt.total_seconds()
df['job_seconds'] = (df['job_duration'] - df['timestamp']).dt.total_seconds()

# Ordenar por data
df = df.sort_values('timestamp')
df = df.reset_index(drop=True)
df['execucao'] = df.index + 1

print(f"📊 Gerando gráficos com {len(df)} execuções...")

# ============================================
# GRÁFICO 1: Tempo total do pipeline por execução
# ============================================
plt.figure(figsize=(12, 6))
cores_status = ['#2E86DE' if s == 'success' else '#E74C3C' for s in df['status']]
plt.bar(df['execucao'], df['workflow_seconds'], color=cores_status, width=0.7)
plt.xticks(df['execucao'], [f"{i}\n{sha}" for i, sha in zip(df['execucao'], df['commit_sha'])], rotation=0)
plt.xlabel('Execução / SHA curto')
plt.ylabel('Duração (segundos)')
plt.title('Tempo total do pipeline por execução')
plt.grid(True, alpha=0.3)
plt.legend(handles=[
	plt.Rectangle((0, 0), 1, 1, color='#2E86DE', label='success'),
	plt.Rectangle((0, 0), 1, 1, color='#E74C3C', label='failure')
], title='Status')
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico1_tempo_total.png')
plt.close()
print("  ✅ Gráfico 1: tempo_total.png")

# ============================================
# GRÁFICO 2: Tempo por job
# ============================================
# Agrupar por job_name e calcular média
job_times = df.groupby('job_name')['job_seconds'].mean().sort_values()

plt.figure(figsize=(10, 6))
job_times.plot(kind='barh', color='skyblue')
plt.xlabel('Duração média (segundos)')
plt.ylabel('Job')
plt.title('Tempo médio por job')
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico2_tempo_por_job.png')
plt.close()
print("  ✅ Gráfico 2: tempo_por_job.png")

# ============================================
# GRÁFICO 3: Taxa de sucesso e falha
# ============================================
status_counts = df['status'].value_counts()

plt.figure(figsize=(8, 8))
colors = ['green' if s == 'success' else 'red' for s in status_counts.index]
plt.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', colors=colors, startangle=90)
plt.title('Taxa de sucesso vs falha')
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico3_taxa_sucesso.png')
plt.close()
print("  ✅ Gráfico 3: taxa_sucesso.png")

# ============================================
# GRÁFICO 4: Relação qtd testes × duração
# ============================================
# Filtrar apenas execuções com dados de teste
df_testes = df.dropna(subset=['test_count'])

plt.figure(figsize=(10, 6))
if len(df_testes) < 2:
	plt.text(
		0.5,
		0.5,
		'Sem dados suficientes para correlacionar quantidade de testes e duração',
		ha='center',
		va='center',
		fontsize=12,
	)
	plt.xlim(0, 1)
	plt.ylim(0, 1)
else:
	plt.scatter(df_testes['test_count'], df_testes['workflow_seconds'], alpha=0.75, s=120, color='#2E86DE')
	for _, row in df_testes.iterrows():
		plt.annotate(row['commit_sha'], (row['test_count'], row['workflow_seconds']), textcoords='offset points', xytext=(6, 6), fontsize=8)
plt.xlabel('Quantidade de testes')
plt.ylabel('Duração do pipeline (segundos)')
plt.title('Relação: quantidade de testes × duração do pipeline')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(GRAFICOS_DIR / 'grafico4_testes_vs_duracao.png')
plt.close()
print("  ✅ Gráfico 4: testes_vs_duracao.png")

print("\n🎉 Todos os gráficos foram gerados na pasta 'graficos/'!")
print(f"📁 Local: {GRAFICOS_DIR}")