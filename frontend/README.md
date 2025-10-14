# Frontend — Bot Ofertas Dashboard (GitHub Pages)

Este é o frontend estático do projeto Bot Ofertas, pensado para rodar no GitHub Pages. Ele exibe um painel simples (HTML/CSS/JS puro) e se comunica via `fetch` com o backend hospedado no Render.

## Estrutura

```
frontend/
├── index.html
├── static/
│   ├── css/style.css
│   └── js/dashboard.js
└── README.md
```

## Configuração do Backend

- Defina a URL do backend no arquivo `static/js/dashboard.js`:
  ```js
  const BACKEND_URL = "https://bot-ofertas-dashboard.onrender.com";
  ```
- No backend (Flask), habilite CORS para seu domínio do GitHub Pages em `backend/app.py`:
  ```python
  from flask_cors import CORS
  CORS(app, origins=["https://SEU_USUARIO.github.io"])
  ```
  Substitua `SEU_USUARIO` pelo seu usuário do GitHub ou o domínio customizado.

## Publicação no GitHub Pages

1. Crie um repositório (ou use um existente) e coloque os arquivos do diretório `frontend/` na raiz do repositório ou na pasta `docs/`.
2. Faça commit e push.
3. Vá em Settings → Pages e escolha:
   - Branch: `main` (ou a branch usada)
   - Folder: `/` (root) ou `docs/` (se usar essa pasta)
4. Salve e aguarde a publicação. A URL será `https://SEU_USUARIO.github.io/NOME_DO_REPO/`.

Observação: Como os caminhos no `index.html` são relativos (`static/...`), funcionarão corretamente tanto em root quanto em subpasta.

## Uso

- Abra a página publicada no GitHub Pages.
- Preencha a palavra-chave (quando estiver em modo `Manual`).
- Selecione o modo (`Manual` ou `TXT`).
- Clique em `🚀 Iniciar` para acionar o backend Render.
- Clique em `🛑 Parar` para encerrar o processo.
- A área de favoritos é carregada via `GET /favoritos`.

## Desenvolvimento Local

Você pode visualizar localmente sem build:

```bash
python -m http.server 8000 --directory frontend
```

Abra `http://localhost:8000/`. O painel tentará se comunicar com o backend remoto definido em `BACKEND_URL`.

## Dicas

- Se usar domínio customizado no GitHub Pages, atualize o `origins` do CORS no backend.
- Certifique-se de que o backend está respondendo as rotas `/status`, `/start`, `/stop` e `/favoritos` com `application/json`.
- No Render, rode o Flask na porta `10000` para compatibilidade.