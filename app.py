from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave-padrao')

# Corrige o prefixo do DATABASE_URL se necessário
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'connect_args': {'sslmode': 'require'}
}

db = SQLAlchemy(app)

class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    data = db.Column(db.String(10), nullable=False)
    categoria = db.Column(db.String(50))

    def __repr__(self):
        return f'<Transacao {self.descricao}>'

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Coleta dados do formulário
        descricao = request.form.get('descricao', '').strip()
        valor = float(request.form.get('valor', 0))
        tipo = request.form.get('tipo', 'despesa')
        data = request.form.get('data') or datetime.now().strftime('%Y-%m-%d')
        categoria = request.form.get('categoria', 'Outros')
        
        # Validação básica
        if not descricao or valor <= 0:
            return redirect(url_for('index'))
        
        # Cria nova transação
        nova_transacao = Transacao(
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            data=data,
            categoria=categoria
        )
        
        # Salva no banco de dados
        db.session.add(nova_transacao)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    # Carrega todas as transações ordenadas por data (mais recente primeiro)
    transacoes = Transacao.query.order_by(Transacao.data.desc()).all()
    
    # Calcula saldo total
    saldo = sum(t.valor if t.tipo == 'receita' else -t.valor for t in transacoes)
    
    # Agrupa por mês para o resumo
    resumo_meses = defaultdict(lambda: {'receitas': 0, 'despesas': 0, 'saldo': 0})
    for t in transacoes:
        mes_ano = t.data[:7]  # Formato YYYY-MM
        if t.tipo == 'receita':
            resumo_meses[mes_ano]['receitas'] += t.valor
        else:
            resumo_meses[mes_ano]['despesas'] += t.valor
        resumo_meses[mes_ano]['saldo'] = resumo_meses[mes_ano]['receitas'] - resumo_meses[mes_ano]['despesas']
    
    # Ordena os meses cronologicamente
    meses_ordenados = sorted(resumo_meses.items(), reverse=True)
    
    return render_template('index.html', 
                        transacoes=transacoes, 
                        saldo=saldo,
                        resumo_meses=dict(meses_ordenados))

@app.route('/extrato_mensal', methods=['GET', 'POST'])
def extrato_mensal():
    if request.method == 'POST':
        mes_ano = request.form.get('mes_ano')
        
        # Filtra transações pelo mês selecionado
        transacoes_filtradas = Transacao.query.filter(
            Transacao.data.startswith(mes_ano)
        ).order_by(Transacao.data.desc()).all()
        
        # Calcula totais
        receitas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'receita')
        despesas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'despesa')
        saldo = receitas - despesas
        
        return render_template('extrato_mensal.html', 
                            transacoes=transacoes_filtradas,
                            mes_ano=mes_ano,
                            receitas=receitas,
                            despesas=despesas,
                            saldo=saldo)
    
    # Lista de meses disponíveis para seleção
    meses = [t.data[:7] for t in Transacao.query.distinct(Transacao.data[:7]).all()]
    return render_template('extrato_mensal.html', meses=meses)

@app.route('/extrato_categoria', methods=['GET', 'POST'])
def extrato_categoria():
    if request.method == 'POST':
        categoria = request.form.get('categoria', '').strip()
        
        # Filtra transações pela categoria selecionada
        transacoes_filtradas = Transacao.query.filter(
            Transacao.categoria.ilike(f'%{categoria}%')
        ).order_by(Transacao.data.desc()).all()
        
        # Calcula totais
        receitas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'receita')
        despesas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'despesa')
        saldo = receitas - despesas
        
        return render_template('extrato_categoria.html', 
                            transacoes=transacoes_filtradas,
                            categoria=categoria,
                            receitas=receitas,
                            despesas=despesas,
                            saldo=saldo)
    
    # Lista de categorias disponíveis para seleção
    categorias = [t[0] for t in db.session.query(Transacao.categoria).distinct().all() if t[0]]
    return render_template('extrato_categoria.html', categorias=categorias)

@app.route('/excluir/<int:transacao_id>', methods=['POST'])
def excluir_transacao(transacao_id):
    # Busca a transação ou retorna 404 se não existir
    transacao = Transacao.query.get_or_404(transacao_id)
    
    # Remove do banco de dados
    db.session.delete(transacao)
    db.session.commit()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)