print("DEBUG: Iniciando o script app.py...")
from flask import Flask, render_template, request, redirect, url_for
import requests
import locale 
import sqlite3 
import json 
import os 

try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252') 
    except locale.Error:
        print("AVISO: Locale 'pt_BR.UTF-8' ou 'Portuguese_Brazil.1252' não encontrado.")

app = Flask(__name__)

DB_DIR = os.path.join(os.path.dirname(__file__), 'dados_db')
os.makedirs(DB_DIR, exist_ok=True) 
DATABASE_FILE = os.path.join(DB_DIR, 'lotofacil_resultados.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    print(f"DEBUG: init_db - Verificando/Criando tabelas em: {DATABASE_FILE}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS concursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero INTEGER UNIQUE NOT NULL,
            data_apuracao TEXT,
            dezenas_sorteadas TEXT, 
            acumulou BOOLEAN,
            data_proximo_concurso TEXT,
            valor_estimado_proximo_concurso REAL 
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rateios_premio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            concurso_numero INTEGER NOT NULL,
            faixa INTEGER NOT NULL,
            descricao_faixa TEXT,
            numero_ganhadores INTEGER,
            valor_premio REAL,
            FOREIGN KEY (concurso_numero) REFERENCES concursos (numero)
        )
    ''')
    conn.commit()
    conn.close()
    print("DEBUG: init_db - Tabelas verificadas/criadas.")

with app.app_context():
    init_db()

URL_API_LOTOFACIL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/"

def salvar_resultado_no_db(dados_concurso):
    if not dados_concurso or 'numero' not in dados_concurso:
        print("DEBUG: salvar_resultado_no_db - Dados inválidos ou sem número.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    numero_concurso = dados_concurso.get('numero')
    print(f"DEBUG: salvar_resultado_no_db - Tentando salvar concurso {numero_concurso}.")

    try:
        cursor.execute("SELECT id FROM concursos WHERE numero = ?", (numero_concurso,))
        existente = cursor.fetchone()
        if existente:
            print(f"DEBUG: salvar_resultado_no_db - Concurso {numero_concurso} já existe. Não salvando novamente.")
            conn.close() # Fechar a conexão se não for fazer nada
            return

        print(f"DEBUG: salvar_resultado_no_db - Dados do concurso a serem salvos (da API): {dados_concurso}")
        cursor.execute('''
            INSERT INTO concursos 
            (numero, data_apuracao, dezenas_sorteadas, acumulou, data_proximo_concurso, valor_estimado_proximo_concurso)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            numero_concurso,
            dados_concurso.get('dataApuracao'), 
            json.dumps(dados_concurso.get('listaDezenas', [])), 
            dados_concurso.get('acumulado'), 
            dados_concurso.get('dataProximoConcurso'),
            dados_concurso.get('valorEstimadoProximoConcurso')
        ))
        print(f"DEBUG: salvar_resultado_no_db - Informações básicas do concurso {numero_concurso} inseridas.")

        if 'listaRateioPremio' in dados_concurso and dados_concurso['listaRateioPremio']:
            print(f"DEBUG: salvar_resultado_no_db - Salvando {len(dados_concurso['listaRateioPremio'])} itens de rateio para o concurso {numero_concurso}.")
            for item_rateio_api in dados_concurso['listaRateioPremio']:
                print(f"DEBUG: salvar_resultado_no_db - Item rateio da API: {item_rateio_api}")
                cursor.execute('''
                    INSERT INTO rateios_premio
                    (concurso_numero, faixa, descricao_faixa, numero_ganhadores, valor_premio)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    numero_concurso,
                    item_rateio_api.get('faixa'),
                    item_rateio_api.get('descricaoFaixa'), # Salva com a chave da API
                    int(item_rateio_api.get('numeroDeGanhadores', 0)), # Salva com a chave da API
                    float(item_rateio_api.get('valorPremio', 0.0)) # Salva com a chave da API
                ))
            print(f"DEBUG: salvar_resultado_no_db - Itens de rateio para concurso {numero_concurso} inseridos.")
        else:
            print(f"DEBUG: salvar_resultado_no_db - Sem listaRateioPremio para o concurso {numero_concurso} nos dados da API.")
        
        conn.commit()
        print(f"DEBUG: salvar_resultado_no_db - Concurso {numero_concurso} salvo com sucesso.")
    except sqlite3.Error as e:
        print(f"DEBUG: salvar_resultado_no_db - Erro SQLite ao salvar concurso {numero_concurso}: {e}")
        conn.rollback() 
    except Exception as e:
        print(f"DEBUG: salvar_resultado_no_db - Erro GERAL ao salvar concurso {numero_concurso}: {e}")
        conn.rollback()
    finally:
        conn.close()

def buscar_resultado_do_db(numero_concurso):
    print(f"DEBUG: buscar_resultado_do_db - Buscando concurso {numero_concurso}.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM concursos WHERE numero = ?", (numero_concurso,))
    concurso_row_db = cursor.fetchone() # Renomeado para clareza

    if concurso_row_db:
        # Mapear explicitamente os nomes das colunas do DB para as chaves esperadas (camelCase)
        dados_concurso_formatado = {
            'numero': concurso_row_db['numero'],
            'dataApuracao': concurso_row_db['data_apuracao'], 
            'acumulado': concurso_row_db['acumulou'], # A API retorna 'acumulado', o DB armazena 'acumulou'
            'dataProximoConcurso': concurso_row_db['data_proximo_concurso'],
            'valorEstimadoProximoConcurso': concurso_row_db['valor_estimado_proximo_concurso']
            # Adicione outros campos da tabela 'concursos' que você usa, se houver, e mapeie-os
        }
        print(f"DEBUG: buscar_resultado_do_db - Concurso {numero_concurso} encontrado (dados básicos mapeados): {dados_concurso_formatado}")
        
        dezenas_json = concurso_row_db['dezenas_sorteadas'] if concurso_row_db['dezenas_sorteadas'] else '[]'
        dados_concurso_formatado['listaDezenas'] = json.loads(dezenas_json)
        
        cursor.execute("SELECT * FROM rateios_premio WHERE concurso_numero = ?", (numero_concurso,))
        rateios_rows_db = cursor.fetchall() # Renomeado para clareza
        
        # Mapeia as chaves dos itens de rateio do DB para o formato da API (camelCase)
        lista_rateio_formatada = []
        for row_db in rateios_rows_db:
            item_formatado = {
                'faixa': row_db['faixa'],
                'descricaoFaixa': row_db['descricao_faixa'], # Mapeia snake_case para camelCase
                'numeroDeGanhadores': row_db['numero_ganhadores'], # Mapeia snake_case para camelCase
                'valorPremio': row_db['valor_premio'] # Mapeia snake_case para camelCase
            }
            lista_rateio_formatada.append(item_formatado)
            
        dados_concurso_formatado['listaRateioPremio'] = lista_rateio_formatada
        print(f"DEBUG: buscar_resultado_do_db - Rateios para concurso {numero_concurso} ({len(dados_concurso_formatado['listaRateioPremio'])} itens mapeados): {dados_concurso_formatado['listaRateioPremio']}")
        
        conn.close()
        return dados_concurso_formatado # Retorna o dicionário com chaves mapeadas
    
    conn.close()
    print(f"DEBUG: buscar_resultado_do_db - Concurso {numero_concurso} NÃO encontrado.")
    return None

def formatar_dados_para_exibicao(dados_concurso):
    # Esta função agora espera que dados_concurso já venha com chaves no formato da API (camelCase)
    if not dados_concurso:
        print("DEBUG: formatar_dados_para_exibicao - Sem dados para formatar.")
        return None
    
    if 'dataApuracao' not in dados_concurso: # Garante que a chave exista
        dados_concurso['dataApuracao'] = None 

    print(f"DEBUG: formatar_dados_para_exibicao - Formatando dados para concurso: {dados_concurso.get('numero')}, Data: {dados_concurso.get('dataApuracao')}")
    
    if 'listaDezenas' in dados_concurso and isinstance(dados_concurso['listaDezenas'], list):
        try:
            dados_concurso['listaDezenas'] = sorted([int(d) for d in dados_concurso['listaDezenas']])
        except (ValueError, TypeError):
            print(f"DEBUG: formatar_dados_para_exibicao - Erro ao converter/ordenar dezenas: {dados_concurso['listaDezenas']}. Ordenando como strings.")
            dados_concurso['listaDezenas'] = sorted(map(str, dados_concurso['listaDezenas']))


    if 'listaRateioPremio' in dados_concurso and isinstance(dados_concurso['listaRateioPremio'], list):
        for item_rateio in dados_concurso['listaRateioPremio']:
            # As chaves aqui já devem ser camelCase (numeroDeGanhadores, valorPremio, descricaoFaixa)
            item_rateio['numeroDeGanhadores'] = int(item_rateio.get('numeroDeGanhadores', 0))
            valor_premio_float = float(item_rateio.get('valorPremio', 0.0))
            try:
                item_rateio['valorPremioFormatado'] = locale.currency(valor_premio_float, grouping=True, symbol=True)
            except Exception as e:
                print(f"DEBUG: formatar_dados_para_exibicao - Erro ao formatar moeda para valor {valor_premio_float}: {e}. Usando formatação manual.")
                item_rateio['valorPremioFormatado'] = "R$ {:.2f}".format(valor_premio_float).replace('.', ',')
            # Não precisamos reatribuir item_rateio['valorPremio'] se ele já está correto.
    else:
        print(f"DEBUG: formatar_dados_para_exibicao - Sem listaRateioPremio ou não é lista para concurso {dados_concurso.get('numero')}")
        if 'listaRateioPremio' not in dados_concurso: # Garante que a chave exista
            dados_concurso['listaRateioPremio'] = []

    return dados_concurso

def buscar_resultado_lotofacil_com_db(numero_concurso=None):
    # A lógica principal desta função permanece a mesma,
    # pois agora buscar_resultado_do_db retorna dados no formato esperado (camelCase)
    dados_api = None
    if numero_concurso:
        dados_db = buscar_resultado_do_db(numero_concurso) # Retorna dados já mapeados para camelCase
        if dados_db:
            return formatar_dados_para_exibicao(dados_db) 
        
        print(f"DEBUG: buscar_resultado_lotofacil_com_db - Concurso {numero_concurso} não no DB. Buscando na API...")
        url = f"{URL_API_LOTOFACIL}/{numero_concurso}"
    else:
        print(f"DEBUG: buscar_resultado_lotofacil_com_db - Buscando último concurso na API...")
        url = URL_API_LOTOFACIL

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        dados_api = response.json() # Dados da API já vêm em camelCase
        print(f"DEBUG: buscar_resultado_lotofacil_com_db - Dados recebidos da API para {dados_api.get('numero') if dados_api else 'URL base'}: {json.dumps(dados_api, indent=2, ensure_ascii=False)}")
        
        if dados_api and dados_api.get('numero'):
            salvar_resultado_no_db(dados_api.copy()) # Salva os dados da API no DB

        return formatar_dados_para_exibicao(dados_api) # Formata os dados da API
        
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: buscar_resultado_lotofacil_com_db - Erro ao buscar dados da API ({url}): {e}")
        if numero_concurso:
            return None 
        print("DEBUG: buscar_resultado_lotofacil_com_db - API falhou para último concurso. Tentando pegar o mais recente do DB...")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT numero FROM concursos ORDER BY numero DESC LIMIT 1")
        ultimo_concurso_db_row = cursor.fetchone()
        conn.close()
        if ultimo_concurso_db_row:
            print(f"DEBUG: buscar_resultado_lotofacil_com_db - Último concurso encontrado no DB como fallback: {ultimo_concurso_db_row['numero']}")
            # buscar_resultado_do_db já retorna no formato camelCase
            return formatar_dados_para_exibicao(buscar_resultado_do_db(ultimo_concurso_db_row['numero']))
        return None
    except Exception as e:
        print(f"DEBUG: buscar_resultado_lotofacil_com_db - Erro inesperado: {e}")
        return None

@app.route('/')
def pagina_inicial():
    print("DEBUG: Rota '/' acessada.")
    dados_concurso = buscar_resultado_lotofacil_com_db()
    return render_template('index.html', concurso=dados_concurso)

@app.route('/buscar', methods=['POST'])
def buscar():
    numero = request.form.get('numero_concurso')
    print(f"DEBUG: Rota '/buscar' acessada com número: {numero}")
    if numero:
        return redirect(url_for('pagina_concurso', numero_concurso=numero))
    return redirect(url_for('pagina_inicial'))

@app.route('/concurso/<int:numero_concurso>')
def pagina_concurso(numero_concurso):
    print(f"DEBUG: Rota '/concurso/{numero_concurso}' acessada.")
    dados_concurso = buscar_resultado_lotofacil_com_db(numero_concurso)
    mensagem_erro = None
    
    if not dados_concurso or 'numero' not in dados_concurso: 
        mensagem_erro = f"O concurso {numero_concurso} não foi encontrado, não existe ou ocorreu um erro ao buscar os dados."
        dados_concurso = {} 

    return render_template('index.html', concurso=dados_concurso, mensagem_erro=mensagem_erro)

if __name__ == '__main__':
    print("DEBUG: Entrando no bloco if __name__ == '__main__'")
    app.run(debug=True, host='0.0.0.0', port=5001)
    print("DEBUG: Servidor Flask deveria estar rodando...")
