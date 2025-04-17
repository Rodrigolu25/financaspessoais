from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from collections import defaultdict
import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'chave-padrao')

# Caminho para o banco de dados SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'financas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Transação
class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'receita' ou 'despesa'
    data = db.Column(db.String(10), nullable=False)  # formato: 'YYYY-MM-DD'
    categoria = db.Column(db.String(50))

    def __repr__(self):
        return f'<Transacao {self.descricao}>'

# Garante que as tabelas sejam criadas
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        descricao = request.form.get('descricao', '').strip()
        valor = float(request.form.get('valor', 0))
        tipo = request.form.get('tipo', 'despesa')
        data = request.form.get('data') or datetime.now().strftime('%Y-%m-%d')
        categoria = request.form.get('categoria', 'Outros')
        
        if not descricao or valor <= 0:
            return redirect(url_for('index'))
        
        nova_transacao = Transacao(
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            data=data,
            categoria=categoria
        )
        
        db.session.add(nova_transacao)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    transacoes = Transacao.query.order_by(Transacao.data.desc()).all()
    saldo = sum(t.valor if t.tipo == 'receita' else -t.valor for t in transacoes)
    
    resumo_meses = defaultdict(lambda: {'receitas': 0, 'despesas': 0, 'saldo': 0})
    for t in transacoes:
        mes_ano = t.data[:7]
        if t.tipo == 'receita':
            resumo_meses[mes_ano]['receitas'] += t.valor
        else:
            resumo_meses[mes_ano]['despesas'] += t.valor
        resumo_meses[mes_ano]['saldo'] = resumo_meses[mes_ano]['receitas'] - resumo_meses[mes_ano]['despesas']
    
    meses_ordenados = sorted(resumo_meses.items(), reverse=True)
    
    return render_template('index.html', 
                           transacoes=transacoes, 
                           saldo=saldo,
                           resumo_meses=dict(meses_ordenados))

@app.route('/extrato_mensal', methods=['GET', 'POST'])
def extrato_mensal():
    if request.method == 'POST':
        mes_ano = request.form.get('mes_ano')
        
        transacoes_filtradas = Transacao.query.filter(
            Transacao.data.startswith(mes_ano)
        ).order_by(Transacao.data.desc()).all()
        
        receitas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'receita')
        despesas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'despesa')
        saldo = receitas - despesas
        
        return render_template('extrato_mensal.html', 
                               transacoes=transacoes_filtradas,
                               mes_ano=mes_ano,
                               receitas=receitas,
                               despesas=despesas,
                               saldo=saldo)
    
    datas = db.session.query(Transacao.data).distinct().all()
    meses = sorted({d[0][:7] for d in datas if d[0]}, reverse=True)
    
    return render_template('extrato_mensal.html', meses=meses)

@app.route('/extrato_categoria', methods=['GET', 'POST'])
def extrato_categoria():
    if request.method == 'POST':
        categoria = request.form.get('categoria', '').strip()
        
        transacoes_filtradas = Transacao.query.filter(
            Transacao.categoria.ilike(f'%{categoria}%')
        ).order_by(Transacao.data.desc()).all()
        
        receitas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'receita')
        despesas = sum(t.valor for t in transacoes_filtradas if t.tipo == 'despesa')
        saldo = receitas - despesas
        
        return render_template('extrato_categoria.html', 
                               transacoes=transacoes_filtradas,
                               categoria=categoria,
                               receitas=receitas,
                               despesas=despesas,
                               saldo=saldo)
    
    categorias = [t[0] for t in db.session.query(Transacao.categoria).distinct().all() if t[0]]
    return render_template('extrato_categoria.html', categorias=categorias)

@app.route('/extrato_descricao', methods=['GET', 'POST'])
def extrato_descricao():
    descricao = None
    transacoes = []
    receitas = despesas = saldo = 0.0

    if request.method == 'POST':
        descricao = request.form['descricao']
        transacoes = Transacao.query.filter(Transacao.descricao.ilike(f'%{descricao}%')).order_by(Transacao.data.desc()).all()
        for t in transacoes:
            if t.tipo == 'receita':
                receitas += t.valor
            elif t.tipo == 'despesa':
                despesas += t.valor
        saldo = receitas - despesas

    descricoes = [t.descricao for t in Transacao.query.with_entities(Transacao.descricao).distinct()]

    return render_template('extrato_descricao.html',
                           descricao=descricao,
                           transacoes=transacoes,
                           receitas=receitas,
                           despesas=despesas,
                           saldo=saldo,
                           descricoes=descricoes)

@app.route('/excluir/<int:transacao_id>', methods=['POST'])
def excluir_transacao(transacao_id):
    transacao = Transacao.query.get_or_404(transacao_id)
    db.session.delete(transacao)
    db.session.commit()
    return redirect(url_for('index'))

# Rodar a aplicação
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
