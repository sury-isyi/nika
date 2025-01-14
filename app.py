from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
import bcrypt  # Biblioteca para criptografia segura de senhas
from PIL import Image
import io
import base64

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 

app.secret_key = 'zorogostoso'

def conectar():
    """
    Função para estabelecer a conexão com o banco de dados MySQL.
    Retorna um objeto de conexão.
    """
    conexao = mysql.connector.connect(
        host="localhost",       
        user="root",            
        password="zorogostoso", 
        database="nika"         
    )
    return conexao  # Retorna a conexão para ser usada nas consultas

@app.route('/')
def index():
    """
    Rota principal do aplicativo.
    Redireciona o usuário para a página de cadastro (página inicial).
    """
    return redirect(('inicial'))  

@app.route('/cadastro', methods=["GET", "POST"])
def cadastrar():
    """
    Rota para cadastro de novos usuários.
    - Método GET: Exibe o formulário de cadastro.
    - Método POST: Processa os dados enviados pelo formulário.
    """
    if request.method == "POST": 
        nome = request.form.get("nome")       
        email = request.form.get("email")     
        password = request.form.get("password")
        if nome and email and password: 
            try:
                
                with conectar() as conexao:  
                    cursor = conexao.cursor()  
                    cursor.execute("""
                        INSERT INTO user (nome, gmail, senha)
                        VALUES (%s, %s, %s)
                    """, (nome, email, password)) 
                    conexao.commit()  

                
                session["email_user"] = email
                print("Cadastro realizado com sucesso!")  
                return redirect(url_for("logar"))  

            except Error as e:  # Captura erros relacionados ao banco de dados
                print(f"Erro ao cadastrar usuário: {e}")  # Mostra o erro no console
                return render_template("cadastro.html", error="Erro ao cadastrar, tente novamente.")

        # Se algum campo estiver vazio, retorna ao formulário com uma mensagem de erro
        return render_template("cadastro.html", error="Preencha todos os campos.")

   
    return render_template("cadastro.html")

@app.route('/login', methods=["GET", "POST"])
def logar():
    """
    Rota para login de usuários.
    - Método GET: Exibe o formulário de login.
    - Método POST: Processa as credenciais enviadas.
    """
    if request.method == "POST":
        email = request.form.get("email")       
        password = request.form.get("password") 
        
        if email and password: 
            try:
                
                with conectar() as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("SELECT * FROM user WHERE gmail = %s", (email,))
                    conta = cursor.fetchone() 

                if conta:  
                    
                    if password == conta[3]: 
                        session["email_user"] = email  
                        print("Login bem-sucedido!")
                        return redirect(url_for("inicial"))  
                    else:
                        return render_template("login.html", error="Senha incorreta.")  
                else:
                    return render_template("login.html", error="Usuário não encontrado.") 
            
            except Error as e:
                print(f"Erro ao tentar logar: {e}")  
                return render_template("login.html", error="Erro ao tentar acessar o banco de dados.")

        return render_template("login.html", error="Preencha todos os campos.")  

    return render_template("login.html")  

@app.route('/inicial', methods=["GET", "POST"])
def inicial():
    posts = []

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            
            cursor.execute(""" 
                           SELECT 
                           p.id, p.data, p.imagem, p.descricao, 
                           u.nome
                           FROM post AS p
                           INNER JOIN user AS u
                           ON p.user_id = u.id
                           ORDER BY p.data DESC

                           """)

            posts_bd = cursor.fetchall()

        if posts_bd:
            for post_bd in posts_bd:
                imagem_blob = post_bd[2]
                imagem_base64 = base64.b64encode(imagem_blob).decode("utf-8")
                img = f"data:image/jpg;base64,{imagem_base64}"

                with conectar() as conexao:
                    cursor = conexao.cursor()
                    cursor.execute(" SELECT text FROM comentario WHERE post_id = %s", (post_bd[0], ))
                    comentarios = cursor.fetchall()
                print(comentarios)
                comentarios = list(comentarios)


                post = list(post_bd)
                post.pop(2)  
                post.append(comentarios)
                post.append(img) 

                posts.append(post)

    except Error as e:
        print(f"Algo deu errado ao buscar os posts cadastrados: {e}")

    if request.method == "POST":
        comentario = request.form.get("mensagem")
        post_id = request.form.get("post_id")  

        if comentario and post_id:
            with conectar() as conexao:
                cursor = conexao.cursor()
                cursor.execute("INSERT INTO comentario(text, post_id) VALUES(%s, %s)", (comentario, post_id))
                conexao.commit()

        return redirect(url_for('inicial'))  

    return render_template("inicial.html", posts=posts, conta=session.get("email_user"))

@app.route("/perfil", methods=["GET"])
def perfil():
    
    if not session.get("email_user"):
        return redirect(url_for("logar"))

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT id, nome, gmail FROM user WHERE gmail = %s", (session.get('email_user'),))
            dados = cursor.fetchone() 

        if dados:  
            id, nome, email = dados  # Desempacota a tupla
        else:
            return redirect(url_for("logar")) 

    except Error as e:
        print(f"Ocorreu um erro ao acessar os dados da conta: {e}")
        return render_template("perfil.html", error="Erro ao carregar os dados do perfil.")

   
    return render_template("perfil.html", id=id, nome=nome, email=email)

@app.route("/logout", methods=["GET"])
def logout():

    session.pop("user_id", None)
    session.pop("email_id", None)

    return redirect(url_for("login"))
    return render_template("perfil")

@app.route('/post/<int:post_id>', methods=["GET", "POST"])
def post(post_id):
    """
    Exibe um post específico com seus comentários.
    - Método GET: Carrega o post e os comentários associados.
    - Método POST: Permite que o usuário adicione um comentário.
    """
    with conectar() as conexao:  
        cursor = conexao.cursor()
        
        
        cursor.execute("SELECT * FROM post WHERE id = %s", (post_id,))
        post = cursor.fetchone()  

      
        cursor.execute("""
            SELECT comentarios.comentario, user.nome 
            FROM comentarios 
            INNER JOIN user ON comentarios.user_id = user.id 
            WHERE comentarios.post_id = %s
        """, (post_id,))
        comentarios = cursor.fetchall()  

    if request.method == "POST":  
        comentario = request.form.get("comentario") 
        user_id = 1  

        if comentario:  
            try:
               
                with conectar() as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("""
                        INSERT INTO comentarios (post_id, user_id, comentario)
                        VALUES (%s, %s, %s)
                    """, (post_id, user_id, comentario))
                    conexao.commit()  
                return redirect(url_for("post", post_id=post_id))  
            except Error as e:
                return render_template("post.html", post=post, comentarios=comentarios, error="Erro ao enviar comentário.")

    return render_template("post.html", post=post, comentarios=comentarios)  

@app.route('/edperfil', methods=["GET", "POST"])
def editar_perfil():
   
    if "email_user" not in session:
        return redirect(url_for("index"))

    email_atual = session.get("email_user")

    if request.method == "POST":
        novo_nome = request.form.get("nome")
        nova_senha = request.form.get("password")

        
        if not novo_nome and not nova_senha:
            return render_template("edperfil.html", error="Preencha ao menos um campo.")
        if nova_senha:
            hashed_password = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt())
        try:  
            with conectar() as conexao:
                cursor = conexao.cursor()
                cursor.execute("UPDATE user SET nome = %s, senha = %s WHERE gmail = %s", (novo_nome, hashed_password.decode('utf-8'), session.get("email_user")))
                print("atualizacao feita")
                conexao.commit()  

            return redirect(url_for("inicial"))  

        except Error as e:
            print(f"Erro ao atualizar perfil: {e}")
            return render_template("edperfil.html", error="Erro ao atualizar perfil. Por favor, tente novamente.")

    
    return render_template("edperfil.html")

@app.route("/excluir-post/<int:post_id>", methods=["GET", "POST"])  
def excluir_post(post_id):
    if "email_user" not in session:
        return redirect(url_for("logar"))

    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id FROM user WHERE gmail = %s", (session.get("email_user"),))
        user_id = cursor.fetchall()[0]

        cursor.execute("SELECT user_id FROM post WHERE id = %s", (post_id,))
        user_post = cursor.fetchall()[0]

    if user_id != user_post:
        print("Usuário não pode excluir um projeto que não é seu")
        return redirect(url_for("perfil"))

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM comentario WHERE post_id = %s", (post_id,))
            cursor.execute("DELETE FROM post WHERE id = %s", (post_id,))
            conexao.commit()
        
        return redirect(url_for("inicial"))
    
    except Error as e:
        print(f"Ocorreu um erro ao excluir o post: {e}")
       
        return redirect(url_for('inicial'))

@app.route('/criar', methods=['GET', 'POST'])
def criar():
    if "email_user" not in session:
        return redirect(url_for("logar"))

    if request.method == 'POST':
        descricao = request.form.get('descricao') 
        imagem = request.files.get('img') 

        if not descricao and not imagem:
            return render_template("criar.html", error="Preencha ao menos a descrição ou envie uma imagem.")

        img_blob = None
        if imagem:
            try:
              
                img = Image.open(imagem)
                
               
                img.thumbnail((800, 800))  

             
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                img_blob = img_byte_arr.getvalue()

            except Exception as e:
                print(f"Erro ao processar imagem: {e}")
                return render_template("criar.html", error="Erro ao processar a imagem.")

        try:
            with conectar() as conexao:
                cursor = conexao.cursor()

                # Busca o ID do usuário
                cursor.execute("SELECT id FROM user WHERE gmail = %s", (session.get("email_user"),))
                user_id = cursor.fetchone()
                if user_id:
                    user_id = user_id[0]
                else:
                    return render_template("criar.html", error="Usuário não encontrado.")

                # Insere o post
                cursor.execute("""
                    INSERT INTO post(data, imagem, descricao, user_id) 
                    VALUES (CURRENT_DATE(), %s, %s, %s)
                """, (img_blob, descricao, user_id))
                conexao.commit()
            print("Conexão e inserção bem-sucedidas.")
            return redirect(url_for("inicial"))  
        except Error as e:
            print(f"Erro ao criar postagem: {e}")
            return render_template("criar.html", error="Erro ao criar postagem, tente novamente.")

    return render_template("criar.html")


@app.route('/materias')
def materiais():
     return render_template("materias.html", conta=session.get("email_user"))  

@app.route('/tecnicas')
def tecnicas():
     
     return render_template("tecnicas.html", conta=session.get("email_user"))



if __name__ == "__main__":
    app.run(debug=True)
