from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Inicializa o aplicativo Flask
app = Flask(__name__)

# Configura o banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ganhos_e_despesas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o SQLAlchemy
db = SQLAlchemy(app)

# Modelo de Transação
class Transacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(150), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)

# Rota para a página principal que lista as transações
@app.route('/')
def index():
    transacoes = Transacao.query.all()  # Busca todas as transações no banco
    return render_template('index.html', transacoes=transacoes)

# Rota para adicionar uma nova transação
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        tipo = request.form['tipo']
        
        nova_transacao = Transacao(descricao=descricao, valor=valor, tipo=tipo)
        db.session.add(nova_transacao)  # Adiciona a nova transação
        db.session.commit()  # Salva as alterações no banco
        
        return redirect(url_for('index'))  # Redireciona de volta para a página principal

    return render_template('adicionar.html')

# Rota para editar uma transação existente
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    transacao = Transacao.query.get_or_404(id)
    
    if request.method == 'POST':
        transacao.descricao = request.form['descricao']
        transacao.valor = float(request.form['valor'])
        transacao.tipo = request.form['tipo']
        
        db.session.commit()  # Salva as alterações no banco
        return redirect(url_for('index'))  # Redireciona para a página principal

    return render_template('editar.html', transacao=transacao)

# Rota para excluir uma transação
@app.route('/deletar/<int:id>', methods=['GET'])
def deletar(id):
    transacao = Transacao.query.get_or_404(id)
    db.session.delete(transacao)  # Exclui a transação do banco
    db.session.commit()  # Salva as alterações no banco
    return redirect(url_for('index'))  # Redireciona para a página principal

# Criar o banco de dados e tabelas, se ainda não existirem
with app.app_context():
    db.create_all()

# Executa o servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
