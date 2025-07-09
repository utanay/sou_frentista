from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import locale
locale.setlocale(locale.LC_TIME,'pt_BR.UTF-8')

app = Flask(__name__)
app.secret_key = 'chave-secreta-do-sistema'  # Necessário para usar flash

@app.template_filter('formatar_data')
def formatar_data(data_str):
    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d')
        return data_obj.strftime('%d/%m/%Y')
    except:
        return data_str
    
# Cria o banco e tabela se não existir
def init_db():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            usuario TEXT UNIQUE,
            senha TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()
def atualizar_tabela_fechamentos():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE fechamentos ADD COLUMN dinheiro_relatorio REAL")
    except sqlite3.OperationalError:
        pass  # já existe

    try:
        cursor.execute("ALTER TABLE fechamentos ADD COLUMN sangria REAL")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE fechamentos ADD COLUMN comentario TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()



@app.route('/')
def login():
    return render_template('login.html')

@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')

@app.route('/fechamento')
def fechamento():
    return render_template('fechamento.html')

@app.route('/painel')
def painel():
    return render_template('painel.html')

@app.route('/logar', methods=['POST'])
def logar():
    return redirect(url_for('painel'))

@app.route('/historico')
def historico():
    atualizar_tabela_fechamentos()

    conn = sqlite3.connect('usuarios.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT data, valor, dinheiro_relatorio, sangria, comentario FROM fechamentos ORDER BY data DESC")

    fechamentos = cursor.fetchall()

    mes_atual = datetime.now().strftime('%B/%Y')
   
    
    total_mes= 0

    for f in fechamentos:
        try:
            data_obj = datetime.strptime(f['data'], '%Y-%m-%d')
            if data_obj.month == datetime.now().month and data_obj.year == datetime.now().year:
                total_mes += float(f['valor'])
        except:
            pass

    conn.close()

    return render_template('historico.html', fechamentos=fechamentos, total_mes=total_mes, mes_atual=mes_atual)


@app.route('/registrar_fechamento',methods=['POST'])
def registrar_fechamento():
    atualizar_tabela_fechamentos()

    valor = request.form['valor']
    data = request.form['data']
    dinheiro_relatorio = float(request.form['dinheiro_relatorio'])
    sangria = float(request.form['sangria'])
    comentario = request.form.get('comentario','')

    diferenca = sangria - dinheiro_relatorio

    if diferenca > 0:
        resultado = f"Sobrou R${diferenca:.2f}"
    elif diferenca < 0:
        resultado = f"Faltou R${abs(diferenca):.2f}"
    else:
        resultado = "Fechamento exato"


    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()

    cursor.execute('''
         CREATE TABLE IF NOT EXISTS fechamentos ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            valor REAL,dinheiro_relatorio REAL,sangria REAL,comentario TEXT)''')

    cursor.execute (
        "INSERT INTO fechamentos (data, valor,dinheiro_relatorio,sangria,comentario) VALUES (?,?,?,?,?)"
        , (data, valor,dinheiro_relatorio,sangria,comentario))
    
    conn.commit()
    conn.close()

    flash (f"Fechamento registrado com sucesso!{resultado}")
    return redirect(url_for('fechamento'))

@app.route('/registrar', methods=['POST'])
def registrar():
    nome = request.form['nome']
    usuario = request.form['usuario']
    senha = request.form['senha']
    confirmar = request.form['confirmar_senha']

    if senha != confirmar:
        flash("As senhas não conferem!")
        return redirect(url_for('cadastro'))

    try:
        conn = sqlite3.connect('usuarios.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nome, usuario, senha) VALUES (?, ?, ?)", (nome, usuario, senha))
        conn.commit()
        conn.close()

        flash("Cadastro realizado com sucesso!")
        
        return redirect(url_for('login'))

    except sqlite3.IntegrityError:
        flash("Usuário já existe.")
        return redirect(url_for('cadastro'))

if __name__ == '__main__':
    app.run(debug=True)
