from iqoptionapi.stable_api import IQ_Option
import ast
import sys
import time
from datetime import datetime, timedelta

print('''
	    
	JARVIS EXECUTOR DE SINAIS

 ------------------------------------
''''\n\n')

def carregar_lista_de_sinais(_filename: str, _separador: str) -> (list, list):
    with open(_filename, 'r') as signal_list:
        sinais_carregados = list(line for line in (row.strip() for row in signal_list) if line)

        lista = []
        for sinal in sinais_carregados:
            array = sinal.split(_separador)
            lista.append({'MOEDA': array[0], 'HORA': array[1], 'DIRECAO': array[2]})

        _lista_de_horas = sorted(set([sub['HORA'] for sub in lista]))

        return sorted(lista, key=lambda k: k['HORA']), _lista_de_horas


def verificar_se_fez_a_conexao(_iq: IQ_Option, _account_type: str = 'PRACTICE') -> bool:
    check, reason = _iq.connect()
    error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""
    requests_limit_exceeded = """{"code":"requests_limit_exceeded","message":"The number of requests has been exceeded. Try again in 10 minutes.","ttl":600}"""
    if check:
        print("\nIniciando Bot")
        _iq.change_balance(_account_type)
        return True
    else:
        if reason == "[Errno -2] Name or service not known":
            print("No Network")
        elif reason == error_password:
            error_message = ast.literal_eval(error_password)
            print(error_message['message'])
        elif reason == requests_limit_exceeded:
            error_message = ast.literal_eval(requests_limit_exceeded)
            print(error_message['message'])

    print("Finishing application, check your data and try again.")
    return False


def format_currency_value(_currency_account: str, _value: float) -> str:
    return '$ {:,.2f}'.format(_value) if _currency_account == 'USD' else 'R$ {:,.2f}'.format(_value)


def get_color_candle(_candle: dict) -> str:
    return 'G' if _candle['open'] < _candle['close'] else 'R' if _candle['open'] > _candle['close'] else 'D'


# Aqui você faz as configurações do BOT
# #:===============================================================:#
valor_entrada_incial = float(input(' Indique um valor para entrar: '))
stop_loss = float(input(' Indique o valor de Stop Loss: '))
stop_win = float(input(' Indique o valor de Stop Gain: '))
quantidade_martigale = int(input(' Indique a quantia de martingales: '))
tipo_pariedade = 'DIGITAL' #str(input(' Indique Digital ou Binaria: ')).upper
lista_de_sinais, lista_de_horas = carregar_lista_de_sinais(r'lista_sinais.txt', ';')

# Aqui você faz as configurações da sua conta IQ Opetion
# #:===============================================================:#
login = 'mathyas.dejesus@gmail.com'
password = '54587478'
account_type = 'PRACTICE'

# Aqui começa a configuração da API, não alterar
# #:===============================================================:#
iq = IQ_Option(login, password)
if not verificar_se_fez_a_conexao(iq, account_type):
    sys.exit(0)

currency_account = iq.get_currency()
account_balance = iq.get_balance()

#print('#:===============================================================:#\n')
#print(f"This is your API version {IQ_Option.__version__}")
print('#:===============================================================:#\n')
print(f"Bem vindo: {login}")
print(f"{'Conta de Treinamento Banca' if account_type == 'PRACTICE' else 'Conta Real Banca'}: "
      f"{format_currency_value(currency_account, account_balance)}")
print('#:===============================================================:#\n')

# Variáveis de controle do BOT, não alterar
# #:===============================================================:#
lucro_atual = 0
valor_entrada_atual = valor_entrada_incial
quantidade_martigale_executado = -1
executar_martingale = False

print(f'Executor de lista de sinais sem thread')
print(f'Quantidade de sinais na lista: {len(lista_de_sinais)}')
print(f"Hoje: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f'Valor da Entrada: {format_currency_value(currency_account, valor_entrada_incial)}')
print(f'Stop loss: {format_currency_value(currency_account, stop_loss)}')
print(f'Stop Win: {format_currency_value(currency_account, stop_win)}')
print(f'Máximo de Martingales: {quantidade_martigale}')
print(f'Observação, sinais com o mesmo horario, apenas um será excutado')
print('#:===============================================================:#\n')


def verificar_stops(_stop_loss: float, _stop_win: float, _lucro_atual: float, _valor_entrada_atual: float,
                    _show_message: bool = True) -> bool:
    if _lucro_atual >= _stop_win:
        if _show_message:
            print(f'Stop Win atingido!')
        return True

    if _lucro_atual < 0:
        if abs(_lucro_atual) + _valor_entrada_atual >= _stop_loss:
            if _show_message:
                print(f'Stop Loss atingido, ou valor muito próximo!')
            return True

    return False


def aguardar_horario_entrada(_lista_de_sinais: list, _lista_de_horas: list, _signal_index: int):
    while True:
        hora_do_sinal = _lista_de_horas[_signal_index]
        current_time = (datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M") + timedelta(minutes=1)).time()
        signal_time = datetime.strptime(hora_do_sinal, "%H:%M").time()

        if signal_time < current_time:
            _signal_index += 1

        if signal_time == current_time:
            _sinais = list(filter(lambda d: d["HORA"] == hora_do_sinal, lista_de_sinais))
            _signal_index += 1
            return True, _sinais[0], _signal_index

        if signal_time > current_time:
            print(f'>>>>>>>>>>>>>>> Aguardando próximo sinal de entrada que será as {signal_time}', end='\r')
            sleep_time = (
                    (signal_time.hour - current_time.hour) * 120 + (signal_time.minute - current_time.minute) * 60)
            time.sleep(0.5)

        if _signal_index > len(_lista_de_sinais) - 1:
            break


def executar_entrada(_iq: IQ_Option, _pariedade: str, _tipo_pariedade: str, _direcao: str, _valor_entrada_atual: float,
                     _quantidade_martigale_executado: int) -> (str, float):
    status, order_id = _iq.buy_digital_spot(_pariedade, _valor_entrada_atual, _direcao.upper(), 5) \
        if _tipo_pariedade.upper() == 'DIGITAL' else _iq.buy(_valor_entrada_atual, _pariedade, _direcao.upper(), 5)

    if quantidade_martigale_executado == -1:
        print(f">>>>>>>>>>>>>>> Executando {'compra' if _direcao.upper() == 'CALL' else 'venda'} "
              f"{'em digital,' if _tipo_pariedade.upper() == 'DIGITAL' else 'em binaria,'} "
              f"moeda {_pariedade} no valor de {format_currency_value(currency_account, _valor_entrada_atual)}, em "
              f"{datetime.now().strftime('%d/%m/%Y as %H:%M:%S')}")
    else:
        print(f">>>>>>>>>>>>>>> Executando {'compra' if _direcao.upper() == 'CALL' else 'venda'} "
              f"{'em digital,' if _tipo_pariedade.upper() == 'DIGITAL' else 'em binaria,'} "
              f"moeda {_pariedade} no valor de {format_currency_value(currency_account, _valor_entrada_atual)}, "
              f"Martingale nível: {_quantidade_martigale_executado + 1}, "
              f"em {datetime.now().strftime('%H:%M:%S')}")

    if status:
        print(f">>>>>>>>>>>>>>> Aguardando resultado da operação")
        while True:
            status, valor_retornado = _iq.check_win_digital_v2(
                order_id) if _tipo_pariedade.upper() == 'DIGITAL' else _iq.check_win_v4(order_id)
            if status:
                if valor_retornado > 0:
                    return 'WIN', float(valor_retornado)
                else:
                    return 'LOSS', float(_valor_entrada_atual)

    return 'ERROR', float(0)


signal_index = 0
print('>>>>>>>>>>>>>>> Iniciando operações')
while not verificar_stops(stop_loss, stop_win, lucro_atual, valor_entrada_atual):
    estrada_valida, sinal_corrente, signal_index = aguardar_horario_entrada(lista_de_sinais, lista_de_horas,
                                                                            signal_index)
    if estrada_valida:

        while True:

            if quantidade_martigale > quantidade_martigale_executado:
                resultado, valor = executar_entrada(iq, sinal_corrente['MOEDA'], tipo_pariedade,
                                                    sinal_corrente['DIRECAO'], valor_entrada_atual,
                                                    quantidade_martigale_executado)

                if resultado == 'LOSS':
                    lucro_atual -= valor
                    print(f">>>>>>>>>>>>>>> Resultado da operação foi LOSS, lucro até o momento "
                          f"{format_currency_value(currency_account, lucro_atual)}")
                    quantidade_martigale_executado += 1
                    valor_entrada_atual = valor_entrada_atual * 2
                    if quantidade_martigale_executado == quantidade_martigale:
                        quantidade_martigale_executado = -1
                        valor_entrada_atual = valor_entrada_incial
                else:
                    lucro_atual += valor
                    print(f">>>>>>>>>>>>>>> Resultado da operação foi WIN, lucro até o momento "
                          f"{format_currency_value(currency_account, lucro_atual)}")
                    valor_entrada_atual = valor_entrada_incial
                    quantidade_martigale_executado = -1
                    break
            else:
                quantidade_martigale_executado = -1
                valor_entrada_atual = valor_entrada_incial
                break

            if verificar_stops(stop_loss, stop_win, lucro_atual, valor_entrada_atual, False):
                break
    else:
        print(">>>>>>>>>>>>>>> Pulando entrada atual, alto risco de LOSS")
        time.sleep(5)
