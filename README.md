# Lotofácil Web App

Aplicação Flask que consulta resultados da Lotofácil utilizando a API oficial da Caixa, armazena os dados localmente em um banco SQLite e exibe as informações em uma página web.

## Requisitos

- Python 3.11+
- `pip` para instalar as dependências

Opcionalmente é possível utilizar Docker e Docker Compose para executar a aplicação em contêiner.

## Instalação e Execução Local

1. Clone este repositório.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute a aplicação:
   ```bash
   python app.py
   ```
4. Abra `http://localhost:5001` em seu navegador.

O banco de dados `dados_db/lotofacil_resultados.db` será criado automaticamente.

## Execução com Docker

1. Construa a imagem e inicie o contêiner:
   ```bash
   docker compose up --build
   ```
2. Acesse `http://localhost:5000` no navegador.

O compose mapeia a porta 5000 do host para a porta 8000 do contêiner onde o Gunicorn roda a aplicação.

## Estrutura do Projeto

- **app.py** – Aplicação Flask responsável pelas rotas e integração com a API/SQLite.
- **templates/** – Contém o template Jinja2 `index.html` usado na exibição.
- **Dockerfile** – Define a imagem Docker configurando o locale em português e executando via Gunicorn.
- **docker-compose.yml** – Serviço que sobe a aplicação mapeando a porta 5000 do host para o contêiner.
- **requirements.txt** – Lista as bibliotecas necessárias.
- **meu_deploy.sh** – Script opcional que auxilia no fluxo de commit e publicação de imagem Docker.

## Dicas

- Os concursos consultados ficam salvos em `dados_db/lotofacil_resultados.db` e são reutilizados se a API estiver indisponível.
- Para realizar deploy em servidores ou VPS, use o `Dockerfile`/`docker-compose.yml` ou adapte o script `meu_deploy.sh` conforme sua infraestrutura.

---

Com essas instruções você já pode executar a aplicação e explorar o código.
