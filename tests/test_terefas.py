from pathlib import Path
import sys
import time

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
import src.app as app_module
from src.app import app

@pytest.fixture(autouse=True)
def limpar_estado():
    app_module.tarefas = []
    app_module.id_counter = 1

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_listar_vazio(client):
    resp = client.get('/tarefas')
    assert resp.status_code == 200
    assert resp.json == []

def test_criar_tarefa(client):
    resp = client.post('/tarefas', json={'titulo': 'Estudar'})
    assert resp.status_code == 201
    assert resp.json['titulo'] == 'Estudar'

def test_deletar_tarefa(client):
    client.post('/tarefas', json={'titulo': 'Teste'})
    resp = client.delete('/tarefas/1')
    assert resp.status_code == 204

def test_atualizar_tarefa(client):
    client.post('/tarefas', json={'titulo': 'Original'})
    resp = client.put('/tarefas/1', json={'concluida': True})
    assert resp.json['concluida'] == True

# Teste que falha (para variação)
def test_busca_inexistente(client):
    resp = client.get('/tarefas/999')
    assert resp.status_code == 404  # Esse vai falhar se não implementado

# Teste lento (para variação)
def test_endpoint_lento(client):
    time.sleep(3)
    resp = client.get('/slow')
    assert resp.status_code == 200

def test_memoria_simples(client):
    dados_gigantes = ['X' * 1024 * 1024] * 200  # 200 strings de 1MB cada
    app_module.tarefas = [{'id': i, 'dados': dados_gigantes[i]} for i in range(200)]
    resp = client.get('/tarefas')
    assert resp.status_code == 200