import requests
import csv
import os
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ENV_FILE = BASE_DIR / '.env'

# Carregar token do arquivo .env ao lado do script
load_dotenv(dotenv_path=ENV_FILE)

TOKEN = os.getenv('GITHUB_TOKEN')
REPO = os.getenv('REPO_NAME')

if not TOKEN or not REPO:
    raise RuntimeError(
        f'Variáveis ausentes em {ENV_FILE}: GITHUB_TOKEN e REPO_NAME precisam '
        'estar definidos.'
    )

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def get_last_12_workflow_runs():
    """Busca as últimas 12 execuções do workflow (mais recentes primeiro)"""
    url = f'https://api.github.com/repos/{REPO}/actions/runs'
    params = {'per_page': 30}  # Busca 30 para ter certeza
    
    response = requests.get(url, headers=headers, params=params)
    all_runs = response.json().get('workflow_runs', [])
    
    # Pegar as 12 mais recentes
    last_12_runs = all_runs[:12]
    
    print(f"📊 Total de runs: {len(all_runs)}")
    print(f"📊 Usando apenas as 12 mais recentes (runs #{last_12_runs[-1]['id']} a #{last_12_runs[0]['id']})")
    
    return last_12_runs

def get_jobs_for_run(run_id):
    """Busca os jobs de uma execução específica"""
    url = f'https://api.github.com/repos/{REPO}/actions/runs/{run_id}/jobs'
    response = requests.get(url, headers=headers)
    return response.json().get('jobs', [])

def get_artifacts_for_run(run_id):
    """Busca artefatos da execução (para métrica opcional)"""
    url = f'https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts'
    response = requests.get(url, headers=headers)
    return response.json().get('artifacts', [])

def extrair_metricas_do_junit_xml(xml_bytes):
    """Extrai quantidade de testes e falhas a partir de um JUnit XML."""
    try:
        root = ET.fromstring(xml_bytes)

        if root.tag == 'testsuites':
            tests = int(root.attrib.get('tests', 0))
            failures = int(root.attrib.get('failures', 0))
            return tests, failures

        if root.tag == 'testsuite':
            tests = int(root.attrib.get('tests', 0))
            failures = int(root.attrib.get('failures', 0))
            return tests, failures

        total_tests = 0
        total_failures = 0
        for node in root.iter():
            if node.tag == 'testsuite':
                total_tests += int(node.attrib.get('tests', 0))
                total_failures += int(node.attrib.get('failures', 0))

        return total_tests, total_failures
    except Exception as e:
        print(f"    ⚠️ Erro ao parsear XML: {e}")
        return None, None

def get_test_metrics_for_run(run_id):
    """Busca o artefato de teste e extrai métricas do arquivo XML."""
    artifacts = get_artifacts_for_run(run_id)

    for artifact in artifacts:
        if artifact.get('name') != 'test-results':
            continue

        try:
            response = requests.get(artifact['archive_download_url'], headers=headers)
            response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.endswith('.xml'):
                        with zip_file.open(file_name) as xml_file:
                            return extrair_metricas_do_junit_xml(xml_file.read())
        except Exception as e:
            print(f"    ⚠️ Erro ao baixar artefato do run {run_id}: {e}")
            return None, None

    return None, None

def extrair_metricas_teste(workflow_run):
    """Extrai informações de teste do workflow"""
    test_count, test_failures = None, None

    # Tenta buscar do artefato gerado pelo pytest
    test_count, test_failures = get_test_metrics_for_run(workflow_run['id'])
    
    # Se conseguiu, retorna os valores reais
    if test_count is not None:
        return test_count, test_failures
    
    # Fallback: tentar extrair da mensagem de commit
    commit_msg = workflow_run.get('head_commit', {}).get('message', '').lower()
    
    if 'teste falhando' in commit_msg or 'falha' in commit_msg:
        test_failures = 1
    elif 'requirements quebrado' in commit_msg:
        test_failures = 1
    
    # Se ainda não tem, usa status da execução
    if test_failures is None:
        if workflow_run.get('conclusion') == 'success':
            test_failures = 0
        elif workflow_run.get('conclusion') == 'failure':
            test_failures = 1
    
    return test_count, test_failures

def coletar_metricas():
    """Função principal: coleta todas as métricas das últimas 12 execuções"""
    runs = get_last_12_workflow_runs()
    dados = []
    
    print(f"\n📊 Coletando métricas de {len(runs)} execuções...\n")
    
    for i, run in enumerate(runs, 1):
        run_id = run['id']
        commit_sha = run['head_sha'][:7]
        commit_message = run['head_commit']['message'] if run.get('head_commit') else ''
        status = run['conclusion'] if run['conclusion'] else run['status']
        timestamp = run['created_at']
        workflow_duration = run.get('updated_at')
        
        print(f"  [{i}] Run #{run_id}: {commit_sha[:7]} - {commit_message[:50]}")
        
        # Buscar jobs
        jobs = get_jobs_for_run(run_id)
        
        for job in jobs:
            job_name = job['name']
            job_duration = job['completed_at']
            
            # Métricas de teste
            test_count, test_failures = extrair_metricas_teste(run)
            
            # Métricas opcionais
            artifacts = get_artifacts_for_run(run_id)
            artifact_size = sum(a['size_in_bytes'] for a in artifacts) if artifacts else 0
            
            # Tipo de falha
            failure_type = None
            if status == 'failure':
                if 'lint' in commit_message.lower():
                    failure_type = 'lint_failure'
                elif 'requirements' in commit_message.lower():
                    failure_type = 'setup_failure'
                else:
                    failure_type = 'test_failure'

            steps = job.get('steps', [])
            if not steps:
                dados.append({
                    'run_id': run_id,
                    'commit_sha': commit_sha,
                    'commit_message': commit_message,
                    'status': status,
                    'workflow_duration': workflow_duration,
                    'job_name': job_name,
                    'job_duration': job_duration,
                    'step_name': None,
                    'step_status': None,
                    'step_started_at': None,
                    'step_completed_at': None,
                    'step_duration_seconds': None,
                    'test_count': test_count,
                    'test_failures': test_failures,
                    'timestamp': timestamp,
                    'artifact_size': artifact_size,
                    'failure_type': failure_type
                })
            else:
                for step in steps:
                    step_started_at = step.get('started_at')
                    step_completed_at = step.get('completed_at')
                    step_duration_seconds = None

                    if step_started_at and step_completed_at:
                        inicio = datetime.fromisoformat(step_started_at.replace('Z', '+00:00'))
                        fim = datetime.fromisoformat(step_completed_at.replace('Z', '+00:00'))
                        step_duration_seconds = (fim - inicio).total_seconds()

                    dados.append({
                        'run_id': run_id,
                        'commit_sha': commit_sha,
                        'commit_message': commit_message,
                        'status': status,
                        'workflow_duration': workflow_duration,
                        'job_name': job_name,
                        'job_duration': job_duration,
                        'step_name': step.get('name'),
                        'step_status': step.get('status'),
                        'step_started_at': step_started_at,
                        'step_completed_at': step_completed_at,
                        'step_duration_seconds': step_duration_seconds,
                        'test_count': test_count,
                        'test_failures': test_failures,
                        'timestamp': timestamp,
                        'artifact_size': artifact_size,
                        'failure_type': failure_type
                    })

            print(f"      ✅ Job: {job_name} | Status: {status} | Testes: {test_count or 'N/A'} | Falhas: {test_failures or 'N/A'}")
    
    return dados

def salvar_csv(dados, arquivo='../dados/metricas.csv'):
    """Salva os dados em CSV"""
    caminho_arquivo = ROOT_DIR / 'dados' / 'metricas.csv'
    caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
    
    with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['run_id', 'commit_sha', 'commit_message', 'status', 
                      'workflow_duration', 'job_name', 'job_duration', 
                      'step_name', 'step_status', 'step_started_at',
                      'step_completed_at', 'step_duration_seconds',
                      'test_count', 'test_failures', 'timestamp', 
                      'artifact_size', 'failure_type']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dados)
    
    print(f"\n📁 Dados salvos em {caminho_arquivo}")
    print(f"📊 Total de {len(dados)} linhas no CSV")

def gerar_csv_com_apenas_experimentos():
    """Versão alternativa: filtra apenas experimentos (#11 em diante)"""
    url = f'https://api.github.com/repos/{REPO}/actions/runs'
    params = {'per_page': 30}
    
    response = requests.get(url, headers=headers, params=params)
    all_runs = response.json().get('workflow_runs', [])
    
    # Filtrar experimentos (run_id >= 11, que é quando começaram os experimentos)
    # Baseado nos seus dados, run #11 é o primeiro experimento
    experimentos = [run for run in all_runs if run['run_number'] >= 11]
    
    print(f"📊 Total: {len(all_runs)} runs | Experimentos: {len(experimentos)} runs")
    
    return experimentos

if __name__ == "__main__":
    print("🚀 Iniciando coleta de métricas (últimas 12 execuções)...")
    print("=" * 50)
    
    dados = coletar_metricas()
    salvar_csv(dados)
    
    print("\n" + "=" * 50)
    print("✅ Coleta finalizada!")