from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
import bcrypt  # Para criptografar e comparar a senha de forma segura

app = Flask(__name__)

def conectar():
    """Função que conecta ao banco de dados MySQL"""
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="ifprquedas",  # Altere essa senha se necessário
        database="nika"
    )
    return conexao

@app.route('/')
def index():
    """Página de login"""
    return render_template("login.html")

@app.route('/cadastro', methods=["GET", "POST"])
def cadastrar():
    """Rota de cadastro de novo usuário"""
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        password = request.form.get("password")

        if nome and email and password:
            try:
                # Criptografando a senha
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                # Inserindo o novo usuário no banco
                with conectar() as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("""
                        INSERT INTO user (nome, email, senha)
                        VALUES (%s, %s, %s)
                    """, (nome, email, hashed_password))
                    conexao.commit()
                print("Cadastro realizado com sucesso!")
                return redirect(url_for("index"))

            except Error as e:
                print(f"Erro ao cadastrar usuário: {e}")
                return render_template("cadastro.html", error="Erro ao cadastrar, tente novamente.")

        return render_template("cadastro.html", error="Preencha todos os campos.")

    return render_template("cadastro.html")

@app.route('/login', methods=["GET", "POST"])
def logar():
    """Rota de login"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if email and password:
            try:
                with conectar() as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
                    conta = cursor.fetchone()

                if conta:
                    # Verificando a senha criptografada
                    if bcrypt.checkpw(password.encode('utf-8'), conta[2].encode('utf-8')):  # conta[2] é a senha criptografada
                        print("Login bem-sucedido!")
                        return redirect(url_for("inicial"))
                    else:
                        print("Senha incorreta")
                        return render_template("login.html", error="Senha incorreta.")
                else:
                    print("Usuário não encontrado.")
                    return render_template("login.html", error="Usuário não encontrado.")
            
            except Error as e:
                print(f"Erro ao tentar logar: {e}")
                return render_template("login.html", error="Erro ao tentar acessar o banco de dados.")

        return render_template("login.html", error="Preencha todos os campos.")

    return render_template("login.html")


@app.route('/inicial')
def inicial():
    """Página principal do sistema após o login"""
    # Aqui você pode carregar as postagens e seus respectivos comentários
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM posts")  # Supondo que a tabela de posts se chama 'posts'
        posts = cursor.fetchall()
    
    return render_template("pagina_principal.html", posts=posts)

@app.route('/post/<int:post_id>', methods=["GET", "POST"])
def post(post_id):
    """Página de exibição de um post específico e seus comentários"""
    with conectar() as conexao:
        cursor = conexao.cursor()
        
        # Carregar post
        cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        
        # Carregar comentários do post
        cursor.execute("SELECT comentarios.comentario, user.nome FROM comentarios INNER JOIN user ON comentarios.user_id = user.id WHERE comentarios.post_id = %s", (post_id,))
        comentarios = cursor.fetchall()

    if request.method == "POST":
        comentario = request.form.get("comentario")
        user_id = 1  # Aqui você deve pegar o ID do usuário logado, por enquanto está fixo

        if comentario:
            try:
                # Inserir o comentário no banco
                with conectar() as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("""
                        INSERT INTO comentarios (post_id, user_id, comentario)
                        VALUES (%s, %s, %s)
                    """, (post_id, user_id, comentario))
                    conexao.commit()
                print("Comentário enviado com sucesso!")
                return redirect(url_for("post", post_id=post_id))
            except Error as e:
                print(f"Erro ao enviar comentário: {e}")
                return render_template("post.html", post=post, comentarios=comentarios, error="Erro ao enviar comentário.")

    return render_template("post.html", post=post, comentarios=comentarios)

@app.route('/teste_conexao')
def teste_conexao():
    """Teste de conexão com o banco de dados"""
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT 1")  # Consulta simples para testar a conexão
            result = cursor.fetchone()  # Retorna o resultado da consulta
            if result:
                return "Banco de dados conectado com sucesso!"
            else:
                return "Erro na conexão com o banco de dados"
    except Error as e:
        return f"Erro ao conectar ao banco de dados: {e}"

if __name__ == "__main__":
    app.run(debug=True)
