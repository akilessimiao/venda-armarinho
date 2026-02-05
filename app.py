from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vendas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===== MODELOS =====
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    perfil = db.Column(db.String(20), nullable=False)  # 'admin' ou 'operador'
    ativo = db.Column(db.Boolean, default=True)

    def set_senha(self, senha):
        self.senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verificar_senha(self, senha):
        return bcrypt.checkpw(senha.encode('utf-8'), self.senha_hash.encode('utf-8'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'login': self.login,
            'perfil': self.perfil
        }

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True)
    descricao = db.Column(db.String(200), nullable=False)
    preco_custo = db.Column(db.Float)
    preco_venda = db.Column(db.Float, nullable=False)
    estoque = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descricao': self.descricao,
            'preco_venda': self.preco_venda,
            'estoque': self.estoque
        }

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # 'cpf' ou 'cnpj'
    documento = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    endereco = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'tipo': self.tipo,
            'documento': self.documento,
            'telefone': self.telefone,
            'email': self.email,
            'endereco': self.endereco
        }

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    total = db.Column(db.Float, nullable=False)
    tipo_cupom = db.Column(db.String(20), default='nao_fiscal')
    cancelada = db.Column(db.Boolean, default=False)
    senha_admin_cancelamento = db.Column(db.String(200))

class MovimentacaoCaixa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'sangria' ou 'suprimento'
    valor = db.Column(db.Float, nullable=False)
    especificacao = db.Column(db.String(200))
    senha_admin = db.Column(db.String(200), nullable=False)

# ===== ROTAS =====
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        login = data.get('login')
        senha = data.get('senha')
        
        usuario = Usuario.query.filter_by(login=login, ativo=True).first()
        
        if usuario and usuario.verificar_senha(senha):
            session['user_id'] = usuario.id
            session['perfil'] = usuario.perfil
            session['nome'] = usuario.nome
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': '/vendas' if usuario.perfil == 'operador' else '/admin'})
            return redirect('/vendas' if usuario.perfil == 'operador' else '/admin')
        
        if request.is_json:
            return jsonify({'success': False, 'error': 'Usuário ou senha inválidos'}), 401
        flash('Usuário ou senha inválidos!', 'error')
        return redirect('/login')
    
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Sistema de Vendas</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }
            body { background: linear-gradient(135deg, #1a2a6c, #2c3e50); height: 100vh; display: flex; align-items: center; justify-content: center; }
            .container { background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); padding: 40px; width: 100%; max-width: 400px; text-align: center; }
            h1 { color: #2c3e50; margin-bottom: 30px; font-size: 28px; }
            .input-group { margin-bottom: 20px; text-align: left; }
            label { display: block; margin-bottom: 8px; color: #7f8c8d; font-weight: 500; }
            input { width: 100%; padding: 14px; border: 2px solid #ecf0f1; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }
            input:focus { border-color: #3498db; outline: none; }
            button { background: #3498db; color: white; border: none; padding: 14px; width: 100%; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; transition: background 0.3s; }
            button:hover { background: #2980b9; }
            .error { color: #e74c3c; background: #fadbd8; padding: 12px; border-radius: 8px; margin-bottom: 20px; display: none; }
            .footer { margin-top: 30px; color: #7f8c8d; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔐 Sistema de Vendas</h1>
            <div id="error" class="error"></div>
            
            <form id="login-form">
                <div class="input-group">
                    <label for="login">Usuário</label>
                    <input type="text" id="login" name="login" required autofocus>
                </div>
                
                <div class="input-group">
                    <label for="senha">Senha</label>
                    <input type="password" id="senha" name="senha" required>
                </div>
                
                <button type="submit">Entrar</button>
            </form>
            
            <div class="footer">
                <p>Admin: admin / java1814</p>
                <p>Operador: operador / operador123</p>
            </div>
        </div>

        <script>
            document.getElementById('login-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const login = document.getElementById('login').value;
                const senha = document.getElementById('senha').value;
                const errorDiv = document.getElementById('error');
                
                try {
                    const response = await fetch('/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ login, senha })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        window.location.href = result.redirect;
                    } else {
                        errorDiv.textContent = result.error || 'Usuário ou senha inválidos!';
                        errorDiv.style.display = 'block';
                    }
                } catch (err) {
                    errorDiv.textContent = 'Erro de conexão com o servidor';
                    errorDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/vendas')
def tela_vendas():
    if 'user_id' not in session or session.get('perfil') != 'operador':
        return redirect('/login')
    
    produtos = Produto.query.filter_by(ativo=True).all()
    return render_template('vendas.html', 
                         produtos=[p.to_dict() for p in produtos],
                         operador=session['nome'])

@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('perfil') != 'admin':
        return redirect('/login')
    
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin - Sistema de Vendas</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }
            body { background: #f5f7fa; color: #333; }
            .header { background: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
            .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .card { background: white; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); padding: 25px; text-align: center; transition: transform 0.3s; cursor: pointer; }
            .card:hover { transform: translateY(-5px); }
            .card-icon { font-size: 40px; margin-bottom: 15px; }
            .card-title { font-size: 20px; font-weight: bold; margin-bottom: 10px; }
            .card-desc { color: #7f8c8d; font-size: 14px; }
            .btn { padding: 10px 20px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s; background: #3498db; color: white; }
            .btn:hover { background: #2980b9; }
            .btn-block { display: block; width: 100%; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">👑 Admin - Armarinho</div>
            <div class="user-info">
                <div class="name">Administrador</div>
            </div>
        </div>

        <div class="container">
            <div class="dashboard">
                <div class="card" onclick="alert('Funcionalidade em desenvolvimento: Cadastro de Produtos')">
                    <div class="card-icon">📦</div>
                    <div class="card-title">Produtos</div>
                    <div class="card-desc">Cadastrar, editar e excluir</div>
                    <button class="btn btn-block">Gerenciar</button>
                </div>
                <div class="card" onclick="alert('Funcionalidade em desenvolvimento: Cadastro de Clientes CPF/CNPJ')">
                    <div class="card-icon">👥</div>
                    <div class="card-title">Clientes</div>
                    <div class="card-desc">CPF e CNPJ</div>
                    <button class="btn btn-block">Gerenciar</button>
                </div>
                <div class="card" onclick="alert('Funcionalidade em desenvolvimento: APIs de Pagamento')">
                    <div class="card-icon">💳</div>
                    <div class="card-title">APIs de Pagamento</div>
                    <div class="card-desc">Contas digitais e PIX</div>
                    <button class="btn btn-block">Configurar</button>
                </div>
                <div class="card" onclick="window.location.href='/logout'">
                    <div class="card-icon">🚪</div>
                    <div class="card-title">Sair</div>
                    <div class="card-desc">Encerrar sessão</div>
                    <button class="btn btn-block" style="background:#e74c3c">Sair</button>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/api/produtos/buscar')
def buscar_produto():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    termo = request.args.get('q', '').strip()
    if not termo:
        return jsonify([])
    
    produtos = Produto.query.filter(
        Produto.ativo == True,
        (Produto.codigo.ilike(f'%{termo}%')) | (Produto.descricao.ilike(f'%{termo}%'))
    ).limit(10).all()
    
    return jsonify([p.to_dict() for p in produtos])

@app.route('/api/vendas', methods=['POST'])
def registrar_venda():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    dados = request.get_json()
    venda = Venda(
        usuario_id=session['user_id'],
        cliente_id=dados.get('cliente_id'),
        total=dados['total'],
        tipo_cupom=dados.get('tipo_cupom', 'nao_fiscal')
    )
    
    db.session.add(venda)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'venda_id': venda.id,
        'data': venda.data.strftime('%d/%m/%Y %H:%M:%S'),
        'total': venda.total
    })

@app.route('/api/caixa/sangria', methods=['POST'])
def sangria():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    dados = request.get_json()
    senha_admin = dados.get('senha_admin', '')
    
    # Verificar senha de administrador (java1814)
    admin = Usuario.query.filter_by(perfil='admin', ativo=True).first()
    if not admin or not admin.verificar_senha(senha_admin):
        return jsonify({'error': 'Senha de administrador inválida'}), 403
    
    movimentacao = MovimentacaoCaixa(
        usuario_id=session['user_id'],
        tipo='sangria',
        valor=float(dados['valor']),
        especificacao=dados.get('especificacao', ''),
        senha_admin=senha_admin
    )
    
    db.session.add(movimentacao)
    db.session.commit()
    
    return jsonify({'success': True, 'id': movimentacao.id})

# ===== ROTAS DE CLIENTES =====
@app.route('/api/clientes', methods=['GET', 'POST'])
def clientes_api():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    if request.method == 'POST':
        dados = request.get_json()
        
        # Validar documento
        documento = dados.get('documento', '').replace('.', '').replace('-', '').replace('/', '').strip()
        tipo = dados.get('tipo', 'cpf')
        
        if tipo == 'cpf' and len(documento) != 11:
            return jsonify({'error': 'CPF inválido! Deve ter 11 dígitos.'}), 400
        
        if tipo == 'cnpj' and len(documento) != 14:
            return jsonify({'error': 'CNPJ inválido! Deve ter 14 dígitos.'}), 400
        
        # Verificar se já existe
        if Cliente.query.filter_by(documento=documento).first():
            return jsonify({'error': 'Cliente com este documento já cadastrado!'}), 400
        
        cliente = Cliente(
            nome=dados['nome'].strip(),
            tipo=tipo,
            documento=documento,
            telefone=dados.get('telefone', '').strip(),
            email=dados.get('email', '').strip(),
            endereco=dados.get('endereco', '').strip()
        )
        
        db.session.add(cliente)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': cliente.id,
            'message': 'Cliente cadastrado com sucesso!'
        })
    
    # GET - Listar clientes
    busca = request.args.get('busca', '').strip()
    if busca:
        clientes = Cliente.query.filter(
            (Cliente.nome.ilike(f'%{busca}%')) | 
            (Cliente.documento.ilike(f'%{busca}%'))
        ).limit(20).all()
    else:
        clientes = Cliente.query.order_by(Cliente.nome).limit(50).all()
    
    return jsonify([c.to_dict() for c in clientes])

@app.route('/api/clientes/<int:id>', methods=['PUT', 'DELETE'])
def cliente_individual(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'PUT':
        dados = request.get_json()
        
        cliente.nome = dados.get('nome', cliente.nome).strip()
        cliente.telefone = dados.get('telefone', cliente.telefone).strip()
        cliente.email = dados.get('email', cliente.email).strip()
        cliente.endereco = dados.get('endereco', cliente.endereco).strip()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cliente atualizado com sucesso!'
        })
    
    # DELETE
    db.session.delete(cliente)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Cliente excluído com sucesso!'
    })

@app.route('/api/clientes/<int:id>')
def buscar_cliente(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    
    cliente = Cliente.query.get_or_404(id)
    return jsonify(cliente.to_dict())

# ===== ROTA PARA TELA DE CLIENTES =====
@app.route('/clientes')
def tela_clientes():
    if 'user_id' not in session:
        return redirect('/login')
    
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Clientes - Sistema de Vendas</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; font-family: Arial, sans-serif; }
            body { background: #f5f7fa; color: #333; }
            .header { background: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
            .search-box { margin-bottom: 20px; }
            .search-box input { width: 100%; padding: 14px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
            .search-box input:focus { border-color: #3498db; outline: none; }
            .btn { padding: 12px 25px; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
            .btn-primary { background: #3498db; color: white; }
            .btn-primary:hover { background: #2980b9; }
            .btn-success { background: #2ecc71; color: white; }
            .btn-success:hover { background: #27ae60; }
            .btn-danger { background: #e74c3c; color: white; }
            .btn-danger:hover { background: #c0392b; }
            .btn-warning { background: #f39c12; color: white; }
            .btn-warning:hover { background: #e67e22; }
            table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-top: 20px; }
            th, td { padding: 15px; text-align: left; border-bottom: 1px solid #eee; }
            th { background: #f8f9fa; font-weight: 600; color: #2c3e50; }
            tr:hover { background: #f8f9fa; }
            .actions { display: flex; gap: 8px; }
            .btn-sm { padding: 6px 12px; font-size: 14px; }
            .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; }
            .modal-content { background: white; padding: 30px; border-radius: 15px; width: 90%; max-width: 600px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
            .modal h3 { margin-bottom: 20px; color: #2c3e50; text-align: center; }
            .form-group { margin-bottom: 15px; text-align: left; }
            .form-group label { display: block; margin-bottom: 8px; color: #7f8c8d; font-weight: 500; }
            .form-group input, .form-group select { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
            .form-group input:focus, .form-group select:focus { border-color: #3498db; outline: none; }
            .modal-buttons { display: flex; gap: 15px; margin-top: 20px; }
            .badge { padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; }
            .badge-cpf { background: #3498db; color: white; }
            .badge-cnpj { background: #2ecc71; color: white; }
            .empty { padding: 40px; text-align: center; color: #999; }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <div class="logo">👥 Cadastro de Clientes</div>
            </div>
            <button class="btn btn-danger" onclick="window.location.href='/logout'" style="padding:8px 15px; font-size:14px;">Sair</button>
        </div>

        <div class="container">
            <div class="search-box">
                <input type="text" id="busca-cliente" placeholder="Buscar por nome ou documento...">
            </div>
            
            <button class="btn btn-success" id="btn-novo-cliente" style="margin-bottom: 20px;">
                ➕ Novo Cliente
            </button>
            
            <div id="lista-clientes">
                <table>
                    <thead>
                        <tr>
                            <th>Nome</th>
                            <th>Documento</th>
                            <th>Tipo</th>
                            <th>Telefone</th>
                            <th>Email</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-clientes">
                        <tr>
                            <td colspan="6" class="empty">Carregando clientes...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Modal Novo/Editar Cliente -->
        <div class="modal" id="modal-cliente">
            <div class="modal-content">
                <h3 id="modal-title">➕ Novo Cliente</h3>
                <input type="hidden" id="cliente-id">
                
                <div class="form-group">
                    <label for="cliente-nome">Nome *</label>
                    <input type="text" id="cliente-nome" required>
                </div>
                
                <div class="form-group">
                    <label for="cliente-tipo">Tipo de Documento *</label>
                    <select id="cliente-tipo" onchange="atualizarMascaraDocumento()">
                        <option value="cpf">CPF (Pessoa Física)</option>
                        <option value="cnpj">CNPJ (Pessoa Jurídica)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="cliente-documento">Documento *</label>
                    <input type="text" id="cliente-documento" required maxlength="18">
                </div>
                
                <div class="form-group">
                    <label for="cliente-telefone">Telefone</label>
                    <input type="text" id="cliente-telefone" placeholder="(00) 00000-0000">
                </div>
                
                <div class="form-group">
                    <label for="cliente-email">Email</label>
                    <input type="email" id="cliente-email" placeholder="exemplo@email.com">
                </div>
                
                <div class="form-group">
                    <label for="cliente-endereco">Endereço</label>
                    <input type="text" id="cliente-endereco" placeholder="Rua, número, bairro, cidade">
                </div>
                
                <div class="modal-buttons">
                    <button class="btn btn-success" id="btn-salvar-cliente" style="flex:1">💾 Salvar Cliente</button>
                    <button class="btn" id="btn-cancelar-cliente" style="flex:1; background:#95a5a6; color:white">Cancelar</button>
                </div>
            </div>
        </div>

        <script>
            let clientes = [];
            let clienteEditando = null;

            // Formatação de documentos
            function atualizarMascaraDocumento() {
                const tipo = document.getElementById('cliente-tipo').value;
                const docInput = document.getElementById('cliente-documento');
                docInput.value = '';
                docInput.maxLength = tipo === 'cpf' ? 14 : 18;
            }

            function formatarCPF(valor) {
                valor = valor.replace(/\D/g, '');
                if (valor.length <= 11) {
                    return valor.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
                }
                return valor;
            }

            function formatarCNPJ(valor) {
                valor = valor.replace(/\D/g, '');
                if (valor.length <= 14) {
                    return valor.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
                }
                return valor;
            }

            document.getElementById('cliente-documento').addEventListener('input', function(e) {
                const tipo = document.getElementById('cliente-tipo').value;
                let valor = e.target.value.replace(/\D/g, '');
                
                if (tipo === 'cpf') {
                    if (valor.length > 11) valor = valor.substring(0, 11);
                    e.target.value = formatarCPF(valor);
                } else {
                    if (valor.length > 14) valor = valor.substring(0, 14);
                    e.target.value = formatarCNPJ(valor);
                }
            });

            document.getElementById('cliente-telefone').addEventListener('input', function(e) {
                let valor = e.target.value.replace(/\D/g, '');
                if (valor.length > 11) valor = valor.substring(0, 11);
                if (valor.length > 2) {
                    valor = `(${valor.substring(0, 2)}) ${valor.substring(2)}`;
                    if (valor.length > 10) {
                        valor = `${valor.substring(0, 10)}-${valor.substring(10)}`;
                    }
                }
                e.target.value = valor;
            });

            // Buscar clientes
            async function buscarClientes(termo = '') {
                try {
                    const response = await fetch(`/api/clientes?busca=${encodeURIComponent(termo)}`);
                    clientes = await response.json();
                    renderizarClientes();
                } catch (err) {
                    console.error('Erro ao buscar clientes:', err);
                    document.getElementById('tabela-clientes').innerHTML = '<tr><td colspan="6" class="empty">Erro ao carregar clientes</td></tr>';
                }
            }

            function renderizarClientes() {
                const tbody = document.getElementById('tabela-clientes');
                
                if (clientes.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="empty">Nenhum cliente encontrado</td></tr>';
                    return;
                }
                
                let html = '';
                clientes.forEach(c => {
                    const docFormatado = c.tipo === 'cpf' ? 
                        c.documento.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4') :
                        c.documento.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
                    
                    html += `
                        <tr>
                            <td><strong>${c.nome}</strong></td>
                            <td>${docFormatado}</td>
                            <td><span class="badge badge-${c.tipo}">${c.tipo.toUpperCase()}</span></td>
                            <td>${c.telefone || '-'}</td>
                            <td>${c.email || '-'}</td>
                            <td class="actions">
                                <button class="btn btn-sm btn-primary" onclick="editarCliente(${c.id})">✏️ Editar</button>
                                <button class="btn btn-sm btn-danger" onclick="excluirCliente(${c.id})">🗑️ Excluir</button>
                            </td>
                        </tr>
                    `;
                });
                
                tbody.innerHTML = html;
            }

            // Novo cliente
            document.getElementById('btn-novo-cliente').addEventListener('click', () => {
                clienteEditando = null;
                document.getElementById('modal-title').textContent = '➕ Novo Cliente';
                document.getElementById('cliente-id').value = '';
                document.getElementById('cliente-nome').value = '';
                document.getElementById('cliente-tipo').value = 'cpf';
                document.getElementById('cliente-documento').value = '';
                document.getElementById('cliente-telefone').value = '';
                document.getElementById('cliente-email').value = '';
                document.getElementById('cliente-endereco').value = '';
                document.getElementById('modal-cliente').style.display = 'flex';
                document.getElementById('cliente-nome').focus();
            });

            // Editar cliente
            window.editarCliente = async function(id) {
                try {
                    const response = await fetch(`/api/clientes/${id}`);
                    const cliente = await response.json();
                    
                    clienteEditando = id;
                    document.getElementById('modal-title').textContent = '✏️ Editar Cliente';
                    document.getElementById('cliente-id').value = cliente.id;
                    document.getElementById('cliente-nome').value = cliente.nome;
                    document.getElementById('cliente-tipo').value = cliente.tipo;
                    document.getElementById('cliente-documento').value = cliente.tipo === 'cpf' ? 
                        cliente.documento.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4') :
                        cliente.documento.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
                    document.getElementById('cliente-telefone').value = cliente.telefone || '';
                    document.getElementById('cliente-email').value = cliente.email || '';
                    document.getElementById('cliente-endereco').value = cliente.endereco || '';
                    
                    document.getElementById('modal-cliente').style.display = 'flex';
                    document.getElementById('cliente-nome').focus();
                } catch (err) {
                    alert('Erro ao carregar cliente');
                }
            };

            // Excluir cliente
            window.excluirCliente = function(id) {
                if (!confirm('⚠️ Deseja realmente excluir este cliente? Esta ação não pode ser desfeita.')) {
                    return;
                }
                
                fetch(`/api/clientes/${id}`, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('✅ Cliente excluído com sucesso!');
                            buscarClientes();
                        } else {
                            alert('❌ Erro ao excluir cliente');
                        }
                    })
                    .catch(err => {
                        alert('❌ Erro de conexão');
                    });
            };

            // Salvar cliente
            document.getElementById('btn-salvar-cliente').addEventListener('click', async () => {
                const nome = document.getElementById('cliente-nome').value.trim();
                const tipo = document.getElementById('cliente-tipo').value;
                const documento = document.getElementById('cliente-documento').value;
                const telefone = document.getElementById('cliente-telefone').value;
                const email = document.getElementById('cliente-email').value;
                const endereco = document.getElementById('cliente-endereco').value;
                
                if (!nome) {
                    alert('⚠️ O nome é obrigatório!');
                    return;
                }
                
                if (!documento || documento.replace(/\D/g, '').length < (tipo === 'cpf' ? 11 : 14)) {
                    alert(`⚠️ O ${tipo.toUpperCase()} é obrigatório e deve estar completo!`);
                    return;
                }
                
                const dados = {
                    nome,
                    tipo,
                    documento: documento.replace(/\D/g, ''),
                    telefone: telefone.replace(/\D/g, ''),
                    email,
                    endereco
                };
                
                try {
                    const url = clienteEditando ? `/api/clientes/${clienteEditando}` : '/api/clientes';
                    const method = clienteEditando ? 'PUT' : 'POST';
                    
                    const response = await fetch(url, {
                        method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(dados)
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(result.message || 'Cliente salvo com sucesso!');
                        document.getElementById('modal-cliente').style.display = 'none';
                        buscarClientes();
                    } else {
                        alert('❌ ' + result.error);
                    }
                } catch (err) {
                    alert('❌ Erro de conexão com o servidor');
                }
            });

            // Cancelar modal
            document.getElementById('btn-cancelar-cliente').addEventListener('click', () => {
                document.getElementById('modal-cliente').style.display = 'none';
            });

            // Busca em tempo real
            document.getElementById('busca-cliente').addEventListener('input', (e) => {
                const termo = e.target.value;
                if (termo.length >= 2 || termo.length === 0) {
                    buscarClientes(termo);
                }
            });

            // Fechar modal ao clicar fora
            window.addEventListener('click', (e) => {
                const modal = document.getElementById('modal-cliente');
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });

            // Inicializar
            buscarClientes();
        </script>
    </body>
    </html>
    '''

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/vendas' if session['perfil'] == 'operador' else '/clientes')
    return redirect('/login')

# ===== INICIALIZAÇÃO =====
def criar_usuarios_padrao():
    with app.app_context():
        db.create_all()
        if Usuario.query.count() == 0:
            # Admin com senha java1814
            admin = Usuario(nome='Administrador', login='admin', perfil='admin')
            admin.set_senha('java1814')
            db.session.add(admin)
            
            # Operador padrão
            operador = Usuario(nome='Operador', login='operador', perfil='operador')
            operador.set_senha('operador123')
            db.session.add(operador)
            
            # Produtos de exemplo
            produtos_exemplo = [
                Produto(codigo='001', descricao='Botão de Madeira', preco_venda=5.0, estoque=120),
                Produto(codigo='002', descricao='Linha de Algodão', preco_venda=8.5, estoque=85),
                Produto(codigo='003', descricao='Agulha de Costura', preco_venda=3.2, estoque=200),
                Produto(codigo='004', descricao='Fita Métrica', preco_venda=12.0, estoque=50),
                Produto(codigo='005', descricao='Tesoura Profissional', preco_venda=25.0, estoque=30)
            ]
            for p in produtos_exemplo:
                db.session.add(p)
            
            # Clientes de exemplo
            clientes_exemplo = [
                Cliente(nome='Maria Silva', tipo='cpf', documento='12345678901', telefone='84999999999', email='maria@email.com'),
                Cliente(nome='João Santos', tipo='cpf', documento='98765432109', telefone='84888888888', email='joao@email.com'),
                Cliente(nome='Confecção LTDA', tipo='cnpj', documento='12345678000190', telefone='8433333333', email='contato@confeccao.com.br')
            ]
            for c in clientes_exemplo:
                db.session.add(c)
            
            db.session.commit()
            print("✓ Banco de dados inicializado com sucesso!")
            print("   Admin: admin / java1814")
            print("   Operador: operador / operador123")

if __name__ == '__main__':
    criar_usuarios_padrao()
    print("\n🚀 Sistema iniciado com sucesso!")
    print("   Acesse em: http://localhost:5000")
    print("   Credenciais:")
    print("     • Admin: admin / java1814")
    print("     • Operador: operador / operador123\n")
    app.run(debug=True, host='0.0.0.0', port=5000)