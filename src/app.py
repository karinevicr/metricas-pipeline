from flask import Flask, jsonify, request

app = Flask(__name__)
tarefas = []
id_counter = 1


@app.route('/')
def home():
    return {"mensagem": "API de Tarefas funcionando!",
            "endpoints": ["/tarefas", "/slow"]}


@app.route('/tarefas', methods=['GET'])
def listar():
    return jsonify(tarefas)


@app.route('/tarefas/<int:id>', methods=['GET'])
def buscar(id):
    for tarefa in tarefas:
        if tarefa['id'] == id:
            return jsonify(tarefa)
    return {'erro': 'Tarefa nao encontrada'}, 404


@app.route('/tarefas', methods=['POST'])
def criar():
    global id_counter
    dados = request.json
    tarefa = {
        'id': id_counter,
        'titulo': dados.get('titulo', ''),
        'concluida': False
    }
    tarefas.append(tarefa)
    id_counter += 1
    return jsonify(tarefa), 201


@app.route('/tarefas/<int:id>', methods=['DELETE'])
def deletar(id):
    global tarefas
    tarefas = [t for t in tarefas if t['id'] != id]
    return '', 204


@app.route('/tarefas/<int:id>', methods=['PUT'])
def atualizar(id):
    for t in tarefas:
        if t['id'] == id:
            dados = request.json
            t['concluida'] = dados.get('concluida', t['concluida'])
            t['titulo'] = dados.get('titulo', t['titulo'])
            return jsonify(t)
    return {'erro': 'Tarefa nao encontrada'}, 404


# Para teste lento
@app.route('/slow')
def slow():
    import time
    time.sleep(2)
    return {'status': 'lento'}


if __name__ == '__main__':
    app.run(debug=True)
   
