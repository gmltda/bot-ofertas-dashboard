# Bot Ofertas Dashboard

Bot minerador de ofertas com integração a Trello e painel web em Flask.

## Instalação

1. Instale as dependências:

```
pip install -r requirements.txt
```

2. Instale os navegadores do Playwright:

```
python -m playwright install
```

3. Inicie o painel web:

```
python dashboard/app.py
```

## Modos de Mineração

- `manual`: roda uma única palavra-chave informada.
- `txt`: lê as palavras do arquivo `data/keywords.txt` e processa uma a uma.

## Como adicionar keywords

Edite o arquivo `data/keywords.txt` e adicione uma palavra por linha. O minerador ignora keywords repetidas nas últimas 24 horas.

## Como rodar e parar

- Rodar manualmente via terminal:

```
python minerador.py --mode manual --keyword "sua keyword"
```

- Rodar via arquivo TXT:

```
python minerador.py --mode txt
```

- Rodar pelo painel:
  - Acesse `http://127.0.0.1:5000/`
  - Escolha o modo e informe a keyword (quando manual)
  - Clique em `🚀 Iniciar` para começar
  - Clique em `🛑 Parar` para interromper o processo atual

## Trello

Configure suas credenciais do Trello via variáveis de ambiente (`TRELLO_KEY`, `TRELLO_TOKEN`, `TRELLO_LIST_ID`) ou diretamente no topo de `minerador.py`. Cards são criados automaticamente para anúncios qualificados e anexos são adicionados quando disponíveis.