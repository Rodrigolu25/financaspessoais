from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSACOES_FILE = os.path.join(BASE_DIR, 'transacoes.json')

if not os.path.exists(TRANSACOES_FILE):
    with open(TRANSACOES_FILE, 'w') as f:
        json.dump([], f)

def carregar_transacoes():
    with open(TRANSACOES_FILE, 'r') as f:
        return json.load(f)

def salvar_transacoes(transacoes):
    with open(TRANSACOES_FILE, 'w') as f:
        json.dump(transacoes, f, indent=2)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        valor = float(request.form.get('valor'))
        tipo = request.form.get('tipo')
        data = request.form.get('data') or datetime.now().strftime('%Y-%m-%d')
        
        nova_transacao = {
            'id': datetime.now().timestamp(),
            'descricao': descricao,
            'valor': valor,
            'tipo': tipo,
            'data': data
        }
        
        transacoes = carregar_transacoes()
        transacoes.append(nova_transacao)
        salvar_transacoes(transacoes)
        return redirect(url_for('index'))
    
    transacoes = carregar_transacoes()
    saldo = sum(t['valor'] if t['tipo'] == 'receita' else -t['valor'] for t in transacoes)
    
    # Agrupar por mês para o resumo
    resumo_meses = defaultdict(lambda: {'receitas': 0, 'despesas': 0, 'saldo': 0})
    for t in transacoes:
        mes_ano = t['data'][:7]  # Formato YYYY-MM
        if t['tipo'] == 'receita':
            resumo_meses[mes_ano]['receitas'] += t['valor']
        else:
            resumo_meses[mes_ano]['despesas'] += t['valor']
        resumo_meses[mes_ano]['saldo'] = resumo_meses[mes_ano]['receitas'] - resumo_meses[mes_ano]['despesas']
    
    return render_template('index.html', 
                        transacoes=transacoes, 
                        saldo=saldo,
                        resumo_meses=dict(resumo_meses))

@app.route('/extrato_mensal', methods=['GET', 'POST'])
def extrato_mensal():
    transacoes = carregar_transacoes()
    
    if request.method == 'POST':
        mes_ano = request.form.get('mes_ano')
        
        transacoes_filtradas = [
            t for t in transacoes 
            if t['data'].startswith(mes_ano)
        ]
        
        receitas = sum(t['valor'] for t in transacoes_filtradas if t['tipo'] == 'receita')
        despesas = sum(t['valor'] for t in transacoes_filtradas if t['tipo'] == 'despesa')
        saldo = receitas - despesas
        
        return render_template('extrato_mensal.html', 
                            transacoes=transacoes_filtradas,
                            mes_ano=mes_ano,
                            receitas=receitas,
                            despesas=despesas,
                            saldo=saldo)
    
    return render_template('extrato_mensal.html')

@app.route('/excluir/<float:transacao_id>')
def excluir_transacao(transacao_id):
    transacoes = carregar_transacoes()
    transacoes = [t for t in transacoes if t['id'] != transacao_id]
    salvar_transacoes(transacoes)
    return redirect(url_for('index'))
# Adicione esta nova rota
@app.route('/extrato_descricao', methods=['GET', 'POST'])
def extrato_descricao():
    transacoes = carregar_transacoes()
    
    if request.method == 'POST':
        descricao = request.form.get('descricao').lower()
        
        transacoes_filtradas = [
            t for t in transacoes 
            if descricao in t['descricao'].lower()
        ]
        
        receitas = sum(t['valor'] for t in transacoes_filtradas if t['tipo'] == 'receita')
        despesas = sum(t['valor'] for t in transacoes_filtradas if t['tipo'] == 'despesa')
        saldo = receitas - despesas
        
        return render_template('extrato_descricao.html', 
                            transacoes=transacoes_filtradas,
                            descricao=descricao,
                            receitas=receitas,
                            despesas=despesas,
                            saldo=saldo)
    
    # Sugere descrições existentes para facilitar a busca
    descricoes = list(set(t['descricao'].lower() for t in transacoes))
    return render_template('extrato_descricao.html', descricoes=descricoes)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Use 10000 ou qualquer porta disponível
    app.run(host='0.0.0.0', port=port)