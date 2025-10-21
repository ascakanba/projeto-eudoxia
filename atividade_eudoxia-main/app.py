from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui_prato_feito'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prato_feito.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuracao inicial
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Defina o caminho base (o diretório onde está app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Crie a aplicação Flask especificando o caminho da pasta templates
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))


#----------------------------------------------------
#  MODELS
#----------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Marmita(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50))
    tamanho = db.Column(db.String(20))
    imagem = db.Column(db.String(200))
    disponivel = db.Column(db.Boolean, default=True)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    total = db.Column(db.Float, nullable=False)
    endereco_entrega = db.Column(db.String(200), nullable=False)
    user = db.relationship('User', backref=db.backref('pedidos', lazy=True))

class ItemPedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    marmita_id = db.Column(db.Integer, db.ForeignKey('marmita.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    marmita = db.relationship('Marmita', backref=db.backref('itens_pedido', lazy=True))


#-------------------------------------------------
#LOGIN MANAGER
#-------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#--------------------------------------------------
# ROTAS
#--------------------------------------------------
@app.route('/')
def index():
    marmitas = Marmita.query.filter_by(disponivel=True).limit(6).all()
    return render_template('index.html', marmitas=marmitas)

#registrar
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe!', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

#logaut
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

#cardapio
@app.route('/cardapio')
def cardapio():
    categoria = request.args.get('categoria')
    if categoria:
        marmitas = Marmita.query.filter_by(categoria=categoria, disponivel=True).all()
    else:
        marmitas = Marmita.query.filter_by(disponivel=True).all()
    
    categorias = db.session.query(Marmita.categoria).distinct().all()
    return render_template('cardapio.html', marmitas=marmitas, categorias=categorias)

#adicionar ao carrinho
@app.route('/adicionar_carrinho/<int:marmita_id>')
@login_required
def adicionar_carrinho(marmita_id):
    marmita = Marmita.query.get_or_404(marmita_id)
    flash(f'{marmita.nome} adicionado ao carrinho!', 'success')
    return redirect(url_for('cardapio'))

#carrinho
@app.route('/carrinho')
@login_required
def carrinho():
    return render_template('carrinho.html')

#perfil
@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')

#pedidos
@app.route('/pedidos')
@login_required
def pedidos():
    user_pedidos = Pedido.query.filter_by(user_id=current_user.id).order_by(Pedido.data_pedido.desc()).all()
    return render_template('pedidos.html', pedidos=user_pedidos)

#insercao de dados para exemplo
def add_sample_data():
    if Marmita.query.count() == 0:
        marmitas = [
            Marmita(
                nome='Marmita Fitness Frango',
                descricao='Frango grelhado, arroz integral, brócolis e batata doce',
                preco=25.90,
                categoria='fitness',
                tamanho='media'
            ),
            Marmita(
                nome='Marmita Vegetariana',
                descricao='Quinoa, grão-de-bico, legumes assados e salada',
                preco=22.50,
                categoria='vegetariana',
                tamanho='media'
            ),
            Marmita(
                nome='Marmita Low Carb',
                descricao='Carne moída, abobrinha refogada, salada verde',
                preco=28.90,
                categoria='lowcarb',
                tamanho='media'
            ),
            Marmita(
                nome='Marmita Fitness Peixe',
                descricao='Filé de peixe grelhado, arroz integral, legumes no vapor',
                preco=27.90,
                categoria='fitness',
                tamanho='media'
            ),
            Marmita(
                nome='Marmita Vegana',
                descricao='Lentilha, abóbora assada, couve e quinoa',
                preco=24.90,
                categoria='vegana',
                tamanho='media'
            ),
            Marmita(
                nome='Marmita Kids',
                descricao='Arroz, feijão, carne moída e batata frita',
                preco=20.90,
                categoria='kids',
                tamanho='pequena'
            )
        ]
        
        for marmita in marmitas:
            db.session.add(marmita)
        
        db.session.commit()
        print("Dados de exemplo adicionados com sucesso")

#--------------------------------------------------
# CRIAR BANCO NA PRIMEIRA EXECUÇAO
#--------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        add_sample_data()
    
    app.run(debug=True)
