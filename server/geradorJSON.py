import requests
import json
from datetime import date, timedelta
from dotenv import load_dotenv
import os

def logar():
    load_dotenv()
    url = 'https://api.tisaude.com/api/login'

    dado = {
        'login' : os.getenv('login'),
        'senha' : os.getenv('senha')
    }

    response = requests.post(url, json=dado)
    token = response.json()["access_token"]
    headers_auth = {
        'Authorization': f'Bearer {token}'
    }
    return headers_auth

def get_data():
    amanha = date.today() + timedelta(days=1)
    resultado = amanha.strftime("%d-%m-%Y")
    return resultado

def relatorio_pcte(headers_auth):
    dict_fim = {}
    data = get_data()
    url_pcte = f'https://api.tisaude.com/api/reports/patients?relatorio=Anal%C3%ADtico&idade=anos&status=TODOS&estadocivil=TODOS&sexo=TODOS&genero=TODOS&wp=0&retornoJson=true&inicioAgendamento={data}&fimAgendamento={data}'

    response_pcte = requests.get(url_pcte, headers=headers_auth)
    for i in response_pcte.json()["data"]:
        dict_fim[str(i['id'])] = {'id' : i['id'], 'nome' : i['nome'], 'data_n' : i['nascimento'], 'lembretes' : str(i['lembretes']).split(', '), 'qtd_lem' : len(str(i['lembretes']).split(', '))}
    print("Dicionario criado sem data exame")
    return dict_fim

def gerar_json():
    data = get_data()
    url_get_relatorio_agendamento = f'https://api.tisaude.com/api/reports/agenda?inicio={data}&fim={data}&relatorio=Anal%C3%ADtico&retornoJson=true'

    headers_auth = logar()
    response_rel_age = requests.get(url_get_relatorio_agendamento, headers=headers_auth)

    dict_fim = relatorio_pcte(headers_auth)
    
    list_pop = []

    for dados in response_rel_age.json()["data"]:
        for dadosDict in dict_fim:
            if (dados['idPcte'] == int(dadosDict) and dados['deletado'] == 0):
                dict_fim[str(dados['idPcte'])]['data'] = dados['data'] + ' ' + dados['hora']
        if (dados['deletado'] == 1):
            list_pop.append(str(dados['idPcte']))

    for i in list_pop:
        del dict_fim[i]

    print("Dicionario criado com data exame")

    with open(f'{data}.json', 'w', encoding='utf-8') as f:
        json.dump(
            dict_fim, 
            f, 
            indent=4,           
            ensure_ascii=False, 
        )
        print("Arquivo json criado")

gerar_json()