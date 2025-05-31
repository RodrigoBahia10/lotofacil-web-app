from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

URL_API_LOTOFACIL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/"

def buscar_resultado_lotofacil(numero_concurso=None):
    if numero_concurso:
        url = f"{URL_API_LOTOFACIL}/{numero_concurso}"
        print(f"Buscando dados do concurso específico: {url}")
    else:
        url = URL_API_LOTOFACIL
        print(f"Buscando dados do último concurso: {url}")

    try:
        response = requests.get(url, timeout=15) # Aumentei um pouco o timeout para garantir
        response.raise_for_status()
        dados = response.json()
        
        # Vamos processar a lista de rateio aqui para facilitar no template
        if dados and 'listaRateioPremio' in dados:
            # Ordenar por faixa pode ser útil, mas a API já costuma vir ordenada
            # Vamos garantir que os números de ganhadores e valores sejam formatados
            for item_rateio in dados['listaRateioPremio']:
                # Convertendo para inteiro para remover casas decimais desnecessárias em ganhadores
                item_rateio['numeroDeGanhadores'] = int(item_rateio.get('numeroDeGanhadores', 0))
                # Formatando o valor do prêmio para ter duas casas decimais
                item_rateio['valorPremio'] = float(item_rateio.get('valorPremio', 0.0))
        return dados
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        return None
    except ValueError as e: # Para erros de conversão int/float
        print(f"Erro ao processar dados do rateio: {e}")
        return dados # Retorna os dados parcialmente processados se o rateio falhar

@app.route('/')
def pagina_inicial():
    dados_concurso = buscar_resultado_lotofacil()
    if dados_concurso and 'listaDezenas' in dados_concurso:
        dados_concurso['listaDezenas'] = sorted(dados_concurso['listaDezenas'], key=int)
    return render_template('index.html', concurso=dados_concurso)

@app.route('/buscar', methods=['POST'])
def buscar():
    numero = request.form.get('numero_concurso')
    if numero:
        return redirect(url_for('pagina_concurso', numero_concurso=numero))
    return redirect(url_for('pagina_inicial'))

@app.route('/concurso/<int:numero_concurso>')
def pagina_concurso(numero_concurso):
    dados_concurso = buscar_resultado_lotofacil(numero_concurso)
    mensagem_erro = None
    if dados_concurso and 'listaDezenas' in dados_concurso:
        dados_concurso['listaDezenas'] = sorted(dados_concurso['listaDezenas'], key=int)
    else:
        mensagem_erro = f"O concurso {numero_concurso} não foi encontrado ou os dados são inválidos."
        # Se dados_concurso for None ou não tiver 'listaDezenas', ele será None para o template
        # e a mensagem de erro será exibida.
        if dados_concurso is None:
            dados_concurso = {} # Garante que 'concurso' não seja None no template se a API falhar totalmente

    return render_template('index.html', concurso=dados_concurso, mensagem_erro=mensagem_erro)

# Não precisamos mais do if __name__ == '__main__': pois o Gunicorn cuida disso.