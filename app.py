# Importa o Flask para criar nossa aplicação web.
# 'render_template' é usado para carregar e exibir nosso arquivo HTML.
from flask import Flask, render_template 
import requests # Para buscar os dados da API

# Cria a instância da nossa aplicação web.
app = Flask(__name__)

# URL da API da Caixa para os resultados da Lotofácil
URL_API_LOTOFACIL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/"

def buscar_ultimo_resultado_lotofacil():
    """
    Busca os dados do último concurso da Lotofácil na API da Caixa.
    Retorna um dicionário com os dados ou None em caso de erro.
    """
    try:
        # Faz a requisição para a API. O timeout evita que o site fique "preso".
        response = requests.get(URL_API_LOTOFACIL, timeout=10)
        # Se a resposta da API for um erro (ex: 404, 500), isso vai gerar uma exceção.
        response.raise_for_status() 
        # Retorna os dados convertidos do formato JSON para um dicionário Python.
        return response.json()
    except requests.exceptions.RequestException as e:
        # Se houver qualquer erro na requisição (conexão, etc), imprime o erro no terminal.
        print(f"Erro ao buscar dados da API: {e}")
        return None

# Define a rota principal do nosso site (a página inicial, ex: http://127.0.0.1:5000/)
@app.route('/')
def mostrar_resultado():
    """
    Esta função é executada quando alguém acessa a página inicial.
    """
    print("Recebida requisição para a página inicial. Buscando dados...")
    # 1. Chama a função para buscar os dados da loteria.
    dados_concurso = buscar_ultimo_resultado_lotofacil()
    
    # 2. Ordena as dezenas para exibição, se os dados foram recebidos.
    if dados_concurso and 'listaDezenas' in dados_concurso:
        # Ordena numericamente, convertendo strings para inteiros.
        dados_concurso['listaDezenas'] = sorted(dados_concurso['listaDezenas'], key=int)

    # 3. Renderiza o arquivo HTML, passando os dados do concurso para ele.
    # O HTML poderá acessar os dados através da variável 'concurso'.
    return render_template('index.html', concurso=dados_concurso)

# Este bloco permite executar a aplicação diretamente com 'python app.py'
# O debug=True faz com que o servidor reinicie automaticamente a cada alteração no código.
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')