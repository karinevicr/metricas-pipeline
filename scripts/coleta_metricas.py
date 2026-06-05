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

def get_workflow_runs():
    """Busca todas as execuções do workflow"""
    url = f'https://api.github.com/repos/{REPO}/actions/runs'
    params = {'per_page': 30}  # Pega até 30 execuções
    
    response = requests.get(url, headers=headers, params=params)
    return response.json().get('workflow_runs', [])

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


def get_test_metrics_for_run(run_id):
    """Busca o artefato de teste e extrai métricas do arquivo XML."""
    artifacts = get_artifacts_for_run(run_id)

    for artifact in artifacts:
        if artifact.get('name') != 'test-results':
            continue

        response = requests.get(artifact['archive_download_url'], headers=headers)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            for file_name in zip_file.namelist():
                if file_name.endswith('.xml'):
                    with zip_file.open(file_name) as xml_file:
                        return extrair_metricas_do_junit_xml(xml_file.read())

    return None, None

def extrair_metricas_teste(workflow_run):
    """Extrai informações de teste do workflow"""
    test_count, test_failures = None, None

    # Tenta buscar do artefato gerado pelo pytest
    try:
        return get_test_metrics_for_run(workflow_run['id'])
    except Exception:
        pass

    # Fallback simples quando o artefato não estiver disponível
    if workflow_run.get('conclusion') == 'success':
        test_failures = 0
    elif workflow_run.get('conclusion') == 'failure':
        test_failures = 1
    
    return test_count, test_failures

def coletar_metricas():
    """Função principal: coleta todas as métricas"""
    runs = get_workflow_runs()
    dados = []
    
    print(f"📊 Coletando métricas de {len(runs)} execuções...")
    
    for run in runs:
        run_id = run['id']
        commit_sha = run['head_sha'][:7]  # 7 primeiros caracteres
        commit_message = run['head_commit']['message'] if run.get('head_commit') else ''
        status = run['conclusion'] if run['conclusion'] else run['status']
        workflow_duration = run['updated_at']  # ou calcular com created_at
        timestamp = run['created_at']
        
        # Buscar jobs
        jobs = get_jobs_for_run(run_id)
        
        for job in jobs:
            job_name = job['name']
            job_duration = job['completed_at']  # Simplificado
            
            # Métricas de teste (simplificado)
            test_count, test_failures = extrair_metricas_teste(run)
            
            # Métricas opcionais
            artifacts = get_artifacts_for_run(run_id)
            artifact_size = sum(a['size_in_bytes'] for a in artifacts) if artifacts else 0
            
            # Lead time (diferença entre commit e conclusão)
            lead_time = None  # Calcular com timestamps
            
            # Tipo de falha (opcional)
            failure_type = None
            if status == 'failure':
                if 'lint' in job_name.lower():
                    failure_type = 'lint_failure'
                else:
                    failure_type = 'test_failure'
            
            dados.append({
                'run_id': run_id,
                'commit_sha': commit_sha,
                'commit_message': commit_message,
                'status': status,
                'workflow_duration': workflow_duration,
                'job_name': job_name,
                'job_duration': job_duration,
                'test_count': test_count,
                'test_failures': test_failures,
                'timestamp': timestamp,
                'artifact_size': artifact_size,
                'failure_type': failure_type
            })
            
            print(f"  ✅ Run {run_id}: {status}")
    
    return dados

def salvar_csv(dados, arquivo='../dados/metricas.csv'):
    """Salva os dados em CSV"""
    caminho_arquivo = ROOT_DIR / 'dados' / 'metricas.csv'
    caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
    
    with open(caminho_arquivo, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['run_id', 'commit_sha', 'commit_message', 'status', 
                      'workflow_duration', 'job_name', 'job_duration', 
                      'test_count', 'test_failures', 'timestamp', 
                      'artifact_size', 'failure_type']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(dados)
    
    print(f"📁 Dados salvos em {caminho_arquivo}")

if __name__ == "__main__":
    print("🚀 Iniciando coleta de métricas...")
    dados = coletar_metricas()
    salvar_csv(dados)
    print("✅ Coleta finalizada!")