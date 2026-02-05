document.addEventListener('DOMContentLoaded', () => {

  let carrinho = [];

  function moeda(valor) {
    return valor.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    });
  }

  function initDB() {
    if (!localStorage.getItem('db')) {
      localStorage.setItem('db', JSON.stringify({
        usuarios: [
          { login: 'admin', senha: 'java1814' },
          { login: 'operador', senha: 'operador123' }
        ],
        produtos: [
          { id: 1, desc: 'Heineken', preco: 8 },
          { id: 2, desc: 'Budweiser', preco: 5 },
          { id: 3, desc: 'Amstel', preco: 5 },
          { id: 4, desc: 'Itaipava', preco: 4 },
          { id: 5, desc: 'Schin', preco: 3.5 },
          { id: 6, desc: 'Coca-Cola Lata', preco: 5 },
          { id: 7, desc: 'Água Mineral', preco: 2 },
          { id: 8, desc: 'Halls', preco: 3 },
          { id: 9, desc: 'Batata Frita', preco: 7 }
        ]
      }));
    }
  }

  function carregarProdutos() {
    const db = JSON.parse(localStorage.getItem('db'));
    const lista = document.getElementById('produtos');
    lista.innerHTML = '';

    db.produtos.forEach(prod => {
      const div = document.createElement('div');
      div.className = 'product-item';
      div.innerHTML = `${prod.desc} - ${moeda(prod.preco)}`;
      div.onclick = () => adicionarCarrinho(prod);
      lista.appendChild(div);
    });
  }

  function adicionarCarrinho(prod) {
    carrinho.push(prod);
    renderCarrinho();
  }

  function renderCarrinho() {
    const div = document.getElementById('carrinho');
    const totalEl = document.getElementById('total');
    let total = 0;

    div.innerHTML = '';

    carrinho.forEach(p => {
      total += p.preco;
      div.innerHTML += `
        <div class="cart-item">
          <span>${p.desc}</span>
          <span>${moeda(p.preco)}</span>
        </div>`;
    });

    totalEl.textContent = moeda(total);
  }

  // LOGIN
  document.getElementById('btn-login').onclick = () => {
    const usuario = document.getElementById('login-user').value;
    const senha = document.getElementById('login-pass').value;
    const db = JSON.parse(localStorage.getItem('db'));

    const ok = db.usuarios.find(
      u => u.login === usuario && u.senha === senha
    );

    if (ok) {
      document.getElementById('login-screen').style.display = 'none';
      document.getElementById('app').style.display = 'block';
      carregarProdutos();
    } else {
      alert('Usuário ou senha inválidos');
    }
  };

  document.getElementById('btn-logout').onclick = () => location.reload();

  document.getElementById('btn-cancelar').onclick = () => {
    carrinho = [];
    renderCarrinho();
  };

  document.getElementById('btn-finalizar').onclick = () => {
    if (!carrinho.length) {
      alert('Carrinho vazio');
      return;
    }
    alert('Venda finalizada com sucesso!');
    carrinho = [];
    renderCarrinho();
  };

  initDB();
});

