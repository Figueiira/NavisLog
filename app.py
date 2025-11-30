from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
from flask import flash
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
def configuracoes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('config.html', usuario=session['usuario'])

@app.route('/op')
def operacoes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('operacoes.html', usuario=session['usuario'])

#ROTA DA PÁGINA DE CADASTRO DE NAVIOS!
@app.route('/cad')
def cad():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('cad_navios.html', usuario=session['usuario'])

#PÁGINA PARA O USUÁRIO ENTRAR EM CONTATO COM O SUPORTE DA NAVISLOG
@app.route('/suporte')
def ajuda():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('suporte.html', usuario=session['usuario'])

#PÁGINA PARA O USUÁRIO SABER MAIS SOBRE O SISTEMA ("SOBRE NÓS")
@app.route('/sobre')
def sobre():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('sobre.html', usuario=session['usuario'])

#PÁGINA DE ACESSO AOS RELATÓRIOS
@app.route('/relatorio')
def info():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('relatorios.html', usurio=session['usuario'])

#ROTA DE ENVIO DO FORMULÁRIO DO SUPORTE
@app.route('/suporte', methods=['GET'])
def suporte():
    return render_template('suporte.html')

@app.route('/enviar-suporte', methods=['POST'])
def enviar_suporte():
    nome = request.form.get("nome")
    email = request.form.get("email")
    telefone = request.form.get("telefone")
    assunto = request.form.get("assunto")
    tipo = request.form.get("tipo")
    prioridade = request.form.get("prioridade")
    descricao = request.form.get("descricao")
    arquivo = request.files.get("arquivo")

    print(nome, email, telefone, assunto, tipo, prioridade, descricao, arquivo)
    print("Solicitação enviada com sucesso! Aguarde a reposta da equipe de suporte.")

    return render_template("suporte_sucesso.html")




# Rota de logout
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
