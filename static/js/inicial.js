// Importando os módulos necessários
const express = require('express');  // Para criar o servidor HTTP
const mysql = require('mysql2');     // Para interagir com o MySQL
const jwt = require('jsonwebtoken'); // Para criar e verificar tokens JWT
const bcrypt = require('bcryptjs');  // Para criptografar a senha de forma segura

// Inicializa o servidor Express
const app = express();
const port = 3000; // Define a porta do servidor

// Conexão com o banco de dados MySQL
const db = mysql.createConnection({
    host: 'localhost',       // Endereço do banco de dados
    user: 'root',            // Usuário do MySQL
    password: 'ifprquedas',            // Senha do MySQL
    database: 'nika'    // Nome do banco de dados
});

// Tenta conectar ao banco de dados
db.connect((err) => {
    if (err) {
        console.log('Erro ao conectar ao banco de dados:', err);
        return;
    }
    console.log('Conectado ao banco de dados MySQL!');
});

// Middleware para parsear dados JSON nas requisições
app.use(express.json());

// Rota para fazer o login
app.post('/login', (req, res) => {
    const { email, senha } = req.body;  // Obtém os dados da requisição (email e senha)

    // Consulta no banco de dados para encontrar o usuário pelo email
    db.query('SELECT * FROM usuarios WHERE email = ?', [email], (err, results) => {
        if (err) {
            return res.status(500).json({ message: 'Erro ao acessar o banco de dados' });
        }
        
        // Verifica se encontrou o usuário
        if (results.length > 0) {
            const usuario = results[0];  // Assume que encontrou um usuário

            // Compara a senha fornecida com a senha armazenada (que está criptografada)
            bcrypt.compare(senha, usuario.senha, (err, isMatch) => {
                if (err || !isMatch) {
                    return res.status(400).json({ message: 'Credenciais inválidas' });
                }
                
                // Se a senha estiver correta, gera um token JWT
                const token = jwt.sign({ id: usuario.id, email: usuario.email }, 'secreto', { expiresIn: '1h' });
                res.json({ message: 'Login bem-sucedido', token });  // Retorna o token JWT para o frontend
            });
        } else {
            return res.status(400).json({ message: 'Usuário não encontrado' });
        }
    });
});

// Rota para cadastro de usuário
app.post('/cadastro', (req, res) => {
    const { nome, email, senha } = req.body;  // Obtém os dados de cadastro

    // Criptografa a senha antes de salvar no banco
    bcrypt.hash(senha, 10, (err, hash) => {
        if (err) {
            return res.status(500).json({ message: 'Erro ao criar senha' });
        }

        // Salva o novo usuário no banco de dados com a senha criptografada
        db.query('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', [nome, email, hash], (err, results) => {
            if (err) {
                return res.status(500).json({ message: 'Erro ao salvar no banco de dados' });
            }

            res.json({ message: 'Cadastro bem-sucedido!' });  // Retorna mensagem de sucesso
        });
    });
});

// Rota para verificar se o usuário está autenticado
app.get('/perfil', (req, res) => {
    const token = req.headers['authorization'];  // O token é enviado no cabeçalho da requisição
    
    if (!token) {
        return res.status(401).json({ message: 'Token não fornecido' });
    }
    
    // Verifica a validade do token
    jwt.verify(token, 'secreto', (err, decoded) => {
        if (err) {
            return res.status(401).json({ message: 'Token inválido' });
        }

        // Se o token for válido, retorna os dados do usuário
        res.json({ message: 'Usuário autenticado', user: decoded });
    });
});

// Inicializa o servidor
app.listen(port, () => {
    console.log(`Servidor rodando na porta ${port}`);
});
