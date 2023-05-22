# Importar Bibliotecas
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Criar app
app = Flask(__name__)
app.config['SECRET_KEY'] = '9f72e64cd6c97d5b1aa1b2d10dc1c690'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comunidade.db'

database = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Exigir o Login do Usuário para acessar certas páginas
login_manager.login_message_category = 'alert-info' # Mensagem de Alerta

# Criar os routes (colocar os caminhos do site)
from comunidadepython import routes