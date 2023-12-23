import pandas as pd 
from flask import Flask, jsonify, request, render_template

# Criar uma instância do Flask
app = Flask(__name__)

# Função para carregar os dados
def get_dados():

    # Carregar os dados
    df = pd.read_csv('ranking_quantbrasil.csv')

    # Retornar os dados
    return df

# Função para calcular o peso
def calcular_peso(df, coluna, peso):

    df_copy = df.copy()
    df_copy = df_copy[['ativo', coluna]]
    df_copy[coluna] = df_copy[coluna] * peso
    df_copy = df_copy.sort_values(by=[coluna], ascending=True)
    df_copy[f'{coluna}_rank'] = df_copy.reset_index().index + 1
    df_copy = df_copy.set_index('ativo')

    return df_copy

# Função para calcular o peso total
def peso_multiplicador(df, momentum, low_risk, magic_formula):

    # Calcular o peso para momentum
    df_1 = calcular_peso(df, 'momentum', momentum)
    # Calcular o peso para low_risk
    df_2 = calcular_peso(df, 'low_risk', low_risk)
    # Calcular o peso para magic_formula
    df_3 = calcular_peso(df, 'magic_formula', magic_formula)

    # Concatenar os dataframes
    df_final = pd.concat([df_1, df_2, df_3], axis=1)

    # Calcular o peso total
    df_final['pontos_total'] = df_final['momentum'] + df_final['low_risk'] + df_final['magic_formula']
    df_final = df_final.sort_values(by=['pontos_total'], ascending=False)
    df_final['rank_total'] = df_final.reset_index().index + 1
    df_final.reset_index(inplace=True)
    df_final = df_final[['rank_total', 'ativo', 'momentum_rank', 'low_risk_rank', 'magic_formula_rank']]

    # Renomear as colunas
    df_final.rename(columns={'rank_total': 'Posição',
                             'ativo': 'Ativo', 
                             'momentum_rank': 'Momentum',
                             'low_risk_rank': 'Low Risk', 
                             'magic_formula_rank': 'Magic Formula'}, inplace = True)

    # Retornar o dataframe
    return df_final

# Função para ordenar a tabela
def ordenar_tabela(df, ordem):

    # Aplicando a ordenação
    if ordem == 1:
        df = df.sort_values(by='Momentum')
    elif ordem == 2:
        df = df.sort_values(by='Low Risk')
    elif ordem == 3:
        df = df.sort_values(by='Magic Formula')
    else:  # 'melhor_posicao' ou qualquer outro valor
        df = df.sort_values(by='Posição')
    
    # Retornar o dataframe
    return df

# Função para alterar o design do html da tabela
def html(df):

    # Converte o DataFrame para HTML
    table_html = df.to_html(classes='table', header=True, index=False)

    # VAriavel com a quantidades de colunas na tabela
    colunas = len(df.columns)

    # Configurações do html da tabela
    # TABLE
    table_antigo = '<table border="1" class="dataframe table">'
    tabela_novo = '<table class="table align-middle">'
    # Trocar o table_antigo pelo table_novo
    table_html = table_html.replace(table_antigo, tabela_novo)

    # THEAD
    thead_antigo = '<thead>'
    thead_novo = '<thead>'
    # Trocar o thead_antigo pelo thead_novo
    table_html = table_html.replace(thead_antigo, thead_novo)

    # TBODY
    tbody_antigo = '<tbody>'
    tbody_novo = '<tbody class="table-group-divider">'
    # Trocar o tbody_antigo pelo tbody_novo
    table_html = table_html.replace(tbody_antigo, tbody_novo)

    # TH
    th_antigo = '<th>'
    th_novo_col = '<th scope="col" class="text-center">'
    th_novo_row = '<th scope="row" class="text-center">'
    # Contar quantas vezes o th_antigo aparece no html
    th_count = table_html.count(th_antigo)
    # Trocar o th_antigo pelo th_novo_col para a quantidade de colunas
    for i in range(th_count):
        if i < colunas - 1:
            table_html = table_html.replace(th_antigo, th_novo_col)
        else:
            table_html = table_html.replace(th_antigo, th_novo_row)

    # TD
    td_antigo = '<td>'
    td_novo = '<td class="text-center">'
    # Trocar o td_antigo pelo td_novo
    table_html = table_html.replace(td_antigo, td_novo)

    # Retornar o html da tabela
    return table_html

# Lê o arquivo CSV e cria um DataFrame
df = get_dados()

@app.route('/') # Rota para a página inicial
def home():
    
    # Definindo valores padrão
    momentum = 2
    low_risk = 1
    magic_formula = 1
    filtro_ativo = ''
    ordem = 0

    # Se for uma requisição POST, processa os dados do formulário
    if request.method == 'POST':
        momentum = int(request.form.get('peso_momentum', 2))
        low_risk = int(request.form.get('peso_low_risk', 1))
        magic_formula = int(request.form.get('peso_magic_formula', 1))
        filtro_ativo = request.form.get('filtro_ativo', '')
        ordem = int(request.form.get('ordenacao', 0))

    # Aplicar os pesos
    df_ranking = peso_multiplicador(df, momentum, low_risk, magic_formula)

    # Filtrar por ativo, se necessário
    if filtro_ativo:
        df_ranking = df_ranking[df_ranking['Ativo'].str.contains(filtro_ativo.upper())]

    # Aplicar ordenação
    df_ranking = ordenar_tabela(df_ranking, ordem)

    # Gera o HTML da tabela atualizada
    table_html = html(df_ranking)

    # Renderiza o template index.html com a tabela atualizada e o as variaveis do HTML
    return render_template('index.html', table=table_html,
                                        momentum=momentum, 
                                        low_risk=low_risk, 
                                        magic_formula=magic_formula, 
                                        filtro_ativo=filtro_ativo,
                                        ordenacao=ordem)


# Rota para atualizar a tabela via AJAX
@app.route('/update_table', methods=['POST'])
def update_table():
    # Extraia os valores do formulário enviado via AJAX
    data = request.get_json()
    momentum = int(data.get('momentum', 2))
    low_risk = int(data.get('low_risk', 1))
    magic_formula = int(data.get('magic_formula', 1))
    filtro_ativo = data.get('filtro_ativo', '')
    ordem = int(data.get('ordenacao', 0))

    # Aplicar os pesos
    df_ranking = peso_multiplicador(df, momentum, low_risk, magic_formula)

    # Filtrar por ativo, se necessário
    if filtro_ativo:
        df_ranking = df_ranking[df_ranking['Ativo'].str.contains(filtro_ativo.upper())]

    # Aplicar ordenação
    df_ranking = ordenar_tabela(df_ranking, ordem)

    # Gera o HTML da tabela atualizada
    table_html = html(df_ranking)

    # Retorna o HTML da tabela atualizada
    return jsonify({'html_table': table_html})

# Condição para executar o servidor
if __name__ == '__main__':
    app.run(debug=True)

