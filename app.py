from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import os

# Carrega variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)

# Define a chave secreta da aplicação
app.secret_key = os.getenv("SECRET_KEY")

# Página inicial
@app.route('/')
def home():
    return render_template('initial.html')  # ✅ Mostra a página initial.html primeiro

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        # Exemplo de autenticação simples
        if usuario == 'admin' and senha == '123':
            session['usuario'] = usuario  # cria a sessão
            return redirect(url_for('index'))
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos!')

    return render_template('login.html')

# Página principal (somente para logados)
@app.route('/index')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', usuario=session['usuario'])

# Página de configurações (somente para logados)
@app.route('/config')
def config():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('config.html', usuario=session['usuario'])

# Rota de logout
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
