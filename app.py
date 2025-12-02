from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from flask_mail import Mail, Message
import os
import random
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename # NOVO: Para segurança de nome de arquivo

# Carrega variáveis do arquivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ---------------- NOVAS CONFIGURAÇÕES DE UPLOAD ---------------- #
# Define o caminho onde os avatares serão salvos dentro da pasta 'static'
UPLOAD_FOLDER = 'static/images/avatars' 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Verifica se a extensão é permitida
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# ------------------------------------------------------------------ #

# Configuração do Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")
mail = Mail(app)

# Variável para armazenar códigos temporários
codigos = {}

# Função para conectar ao banco de dados
def get_db_connection():
    conn = sqlite3.connect('navislog.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar banco e criar tabela de usuários (executar uma vez)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Adicionando a coluna avatar_url na tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            avatar_url TEXT
        )
    ''')
    # Inserir usuário admin inicial
    cursor.execute('INSERT OR IGNORE INTO usuarios (usuario, senha, avatar_url) VALUES (?, ?, ?)', ('admin', '123', 'default_avatar.png'))
    conn.commit()
    conn.close()

# Inicializa o banco de dados
init_db()


# ---------------- ESTRUTURAS DE DADOS ---------------- #

# CLASSE SIMULADA: Simula um objeto de usuário completo retornado de um banco de dados mais robusto
class MockUser:
    def __init__(self, username, avatar_url='default_avatar.png'): # NOVO: Adiciona avatar_url
        self.username = username
        
        # Dados Fictícios (usados no template perfil.html)
        self.nome = "Tiago" if username == 'admin' else username.split('@')[0].capitalize()
        self.nome_completo = "Tiago Figueira do Nascimento"
        self.email = os.getenv("EMAIL_USER")
        self.telefone = "(92) 99999-9999"
        self.cnpj_cpf = "56.216.638/0001-00"
        self.cargo = "Administrador Master" if username == 'admin' else "Gerente Geral"
        self.nivel_acesso = "Administrador"
        self.membro_desde = datetime(2024, 5, 1)
        self.ultimo_login = datetime.now()
        self.embarcacoes_cadastradas = 42
        self.operacoes_agendadas = 15
        self.relatorios_gerados = 6
        
        # NOVO: Usa o avatar_url real do banco de dados (ou a simulação abaixo)
        # Como o SQLite3 só tem dados limitados, vamos buscar o avatar_url dele.
        conn = get_db_connection()
        user_db = conn.execute('SELECT avatar_url FROM usuarios WHERE usuario = ?', (username,)).fetchone()
        conn.close()

        self.avatar_url = user_db['avatar_url'] if user_db and user_db['avatar_url'] else 'default_avatar.png'
    
    # Método auxiliar para formatar datas no template
    def strftime(self, format_string):
        if 'membro_desde' in format_string:
            return self.membro_desde.strftime('%d/%m/%Y')
        return self.ultimo_login.strftime('%H:%M - %d/%m/%Y')

def get_user_data(username):
    # Retorna o objeto completo simulado, buscando a URL do avatar do DB
    return MockUser(username)

# ---------------- ROTAS ---------------- #

@app.route('/')
def home():
    return render_template('initial.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE usuario = ? AND senha = ?', (usuario, senha))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['usuario'] = usuario
            return redirect(url_for('index'))
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos!')

    return render_template('login.html')

@app.route('/index')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', usuario=session['usuario'])

@app.route('/config')
def configuracoes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('config.html', usuario=session['usuario'])

@app.route('/perfil')
def profile():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    username = session['usuario']
    # Cria o objeto de dados completo (MockUser) com base no usuário logado
    user_data = get_user_data(username) 
    
    return render_template('perfil.html', user=user_data) 

# NOVA ROTA: Rota para lidar com o upload de arquivo do avatar
@app.route('/upload-avatar', methods=['POST'])
def upload_avatar():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    # O arquivo vem do formulário com o nome 'avatar_file'
    if 'avatar_file' not in request.files:
        flash('Nenhum arquivo de avatar enviado.', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['avatar_file']
    usuario = session['usuario']
    
    if file.filename == '':
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{usuario}_avatar.{ext}")
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        file.save(file_path)

        # 4. Atualiza o banco de dados com o novo caminho (apenas o nome do arquivo,
        #    pois o UPLOAD_FOLDER é 'static/images/avatars')
        conn = get_db_connection()
        cursor = conn.cursor()
        # Salva o caminho relativo a 'static/images/' (ou seja, 'avatars/nome_do_arquivo.ext')
        avatar_db_path = os.path.join('avatars', filename).replace('\\', '/') 
        
        cursor.execute('UPDATE usuarios SET avatar_url = ? WHERE usuario = ?', (avatar_db_path, usuario))
        conn.commit()
        conn.close()
        
        flash('Avatar atualizado com sucesso!', 'success')
        return redirect(url_for('profile'))
    else:
        flash('Tipo de arquivo não permitido. Use PNG, JPG, JPEG ou GIF.', 'danger')
        return redirect(url_for('profile'))


@app.route('/editar-perfil')
def editar_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    flash('Funcionalidade de edição de perfil em desenvolvimento!', 'warning')
    return redirect(url_for('profile'))

@app.route('/senha', methods=['GET', 'POST'])
def alterar_senha():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario = session['usuario']

    if request.method == 'POST':
        etapa = request.form.get('etapa')

        # Enviar código
        if etapa == 'enviar_codigo':
            codigo = str(random.randint(100000, 999999))
            codigos[usuario] = codigo

            msg = Message(
                subject='Código para Alterar Senha - NavisLog',
                sender=os.getenv("EMAIL_USER"),
                recipients=[os.getenv("EMAIL_USER")],
                body=f"Olá {usuario},\n\nSeu código para alterar a senha é: {codigo}\n\nNavisLog"
            )
            mail.send(msg)
            flash('Código enviado! Verifique seu email.', 'info')
            return render_template('senha_change.html', etapa='verificar')

        # Verificar código e alterar senha
        elif etapa == 'verificar':
            codigo_digitado = request.form.get('codigo')
            nova_senha = request.form.get('nova_senha')

            if codigos.get(usuario) == codigo_digitado:
                # Atualiza a senha no banco de dados
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE usuarios SET senha = ? WHERE usuario = ?', (nova_senha, usuario))
                conn.commit()
                conn.close()

                codigos.pop(usuario)
                flash('Senha alterada com sucesso! Faça login novamente.', 'success')
                session.pop('usuario', None)
                return redirect(url_for('login'))
            else:
                flash('Código inválido! Tente novamente ou reenvie.', 'danger')
                return render_template('senha_change.html', etapa='verificar')

    return render_template('senha_change.html', etapa='enviar')

@app.route('/op')
def operacoes():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('operacoes.html', usuario=session['usuario'])

@app.route('/cad')
def cad():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('cad_navios.html', usuario=session['usuario'])

@app.route('/suporte', methods=['GET'])
def ajuda():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('suporte.html', usuario=session['usuario'])

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

@app.route('/sobre')
def sobre():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('sobre.html', usuario=session['usuario'])

@app.route('/relatorio')
def info():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('relatorios.html', usuario=session['usuario'])

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('home'))

# ------------------- EXECUÇÃO -------------------
if __name__ == '__main__':
    app.run(debug=True)