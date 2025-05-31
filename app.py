from flask import Flask, render_template, request, redirect, url_for
import requests
import locale # <<-- NOVA IMPORTAÇÃO

# Tenta configurar o locale para Português do Brasil para formatação de moeda
# Isso garante que teremos R$ e os separadores corretos (ponto para milhar, vírgula para decimal)
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252') # Alternativa para Windows
    except locale.Error:
        print("AVISO: Locale 'pt_BR.UTF-8' ou 'Portuguese_Brazil.1252' não encontrado. A formatação de moeda pode usar o padrão do sistema.")

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
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        dados = response.json()
        
        if dados and 'listaRateioPremio' in dados:
            for item_rateio in dados['listaRateioPremio']:
                item_rateio['numeroDeGanhadores'] = int(item_rateio.get('numeroDeGanhadores', 0))
                valor_premio_float = float(item_rateio.get('valorPremio', 0.0))
                # <<-- NOVA FORMATAÇÃO DE MOEDA AQUI -->>
                # Cria uma nova chave com o valor formatado
                item_rateio['valorPremioFormatado'] = locale.currency(valor_premio_float, grouping=True, symbol=True)
                # Mantemos o valor original como float, caso precisemos para outros cálculos
                item_rateio['valorPremio'] = valor_premio_float 
        return dados
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados da API: {e}")
        return None
    except ValueError as e: 
        print(f"Erro ao processar dados do rateio: {e}")
        return dados 
    except Exception as e: # Captura outros erros inesperados na formatação
        print(f"Erro inesperado na formatação de dados: {e}")
        # Se 'dados' foi definido antes do erro, retorna, senão None
        return dados if 'dados' in locals() else None


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
        if dados_concurso is None:
            dados_concurso = {} 

    return render_template('index.html', concurso=dados_concurso, mensagem_erro=mensagem_erro)