import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# Criando a aplicação Flask
app = Flask(__name__)

# Configurando a chave secreta para sessões (em produção, deve ser uma chave única e segura)
app.config['SECRET_KEY'] = os.urandom(24)

# Configuração do banco de dados usando a variável de ambiente DATABASE_URL
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# Configuração para não mostrar o aviso de modificações em tempo real no banco de dados
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializando o objeto de banco de dados
db = SQLAlchemy(app)

# Definindo o modelo de transações
class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(120), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'ganho' ou 'despesa'
    data = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Transacao {self.descricao} - {self.valor}>"

# Página principal
@app.route('/')
def index():
    transacoes = Transacao.query.all()  # Busca todas as transações no banco de dados
    return render_template('index.html', transacoes=transacoes)

# Página de adicionar transação
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        tipo = request.form['tipo']

        # Criar nova transação
        nova_transacao = Transacao(descricao=descricao, valor=valor, tipo=tipo)

        try:
            db.session.add(nova_transacao)
            db.session.commit()
            flash('Transação adicionada com sucesso!', 'success')
            return redirect(url_for('index'))
        except:
            db.session.rollback()  # Em caso de erro, reverte as alterações
            flash('Ocorreu um erro ao adicionar a transação.', 'error')
            return redirect(url_for('adicionar'))

    return render_template('adicionar.html')

# Página de editar transação
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    transacao = Transacao.query.get_or_404(id)

    if request.method == 'POST':
        transacao.descricao = request.form['descricao']
        transacao.valor = float(request.form['valor'])
        transacao.tipo = request.form['tipo']

        try:
            db.session.commit()
            flash('Transação atualizada com sucesso!', 'success')
            return redirect(url_for('index'))
        except:
            db.session.rollback()
            flash('Ocorreu um erro ao atualizar a transação.', 'error')
            return redirect(url_for('editar', id=id))

    return render_template('editar.html', transacao=transacao)

# Página de excluir transação
@app.route('/excluir/<int:id>', methods=['GET', 'POST'])
def excluir(id):
    transacao = Transacao.query.get_or_404(id)

    try:
        db.session.delete(transacao)
        db.session.commit()
        flash('Transação excluída com sucesso!', 'success')
        return redirect(url_for('index'))
    except:
        db.session.rollback()
        flash('Ocorreu um erro ao excluir a transação.', 'error')
        return redirect(url_for('index'))

# Rodar o app
if __name__ == '__main__':
    app.run(debug=True)
