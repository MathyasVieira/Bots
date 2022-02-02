from email.message import EmailMessage
from iqoptionapi.stable_api import IQ_Option
from colorama import init, Fore, Back, Style
from datetime import datetime
from talib import *
import sys
import threading
import os
import numpy
import json, requests
import time
import talib

#from talib import MA_Type, EMA, BBANDS
os.system('cls')

print('\n\n===============  Iniciando =================')
email = str(input('\nMe informe seu Login: '))
senha = str(input('Me informe sua Senha: '))
print('\n============================================')

Iq = IQ_Option(email, senha)
Iq.connect()


def perfil():  # Exibindo os dados do Perfil
    perfil = json.loads(json.dumps(Iq.get_profile_ansyc()))
    return perfil


#print(Fore.BLUE + ' Bot  RSI   operando apenas nas binaria \n  Atençao esse bot usa RSI periodo 7 '
                  #'ele entra na reversão')
#print('  Filtros de entrada  acima de 65:00 ele entra com PUT ou se estiver abaixo de 35:00 ele entra com CALL  ')
#print(
    #'  Atençao esse bot vai  dobrando a entrada apos o loss vc pode desativar na variável  dobrar_entrada ' + Fore.RESET)
while True:
    print('\n - Tipos de conta:')
    MODE = int(input('  1 - Treinamento'
                     '\n  2 - Real'
                     '\n  3 - Torneio'
                     '\n\nInforme o número da conta: '))
    if MODE == 1:
        MODE = 'PRACTICE'
        break
    elif MODE == 2:
        MODE = 'REAL'
        break
    elif MODE == 3:
        MODE = 'TOURNAMENT'
        break
    else:
        print('  Opção inválida - Digite uma opção de 1 à 3')
        continue

Iq.change_balance(MODE)
''' Config RSI'''
RSI_SOBRE_COMPRADO = 65.00
RSI_SOBRE_VENDA = 35.00
RSI_timeperiod = 7
dobrar_entrada = str(input('Dejesa dobra entrada: '))  # sim para dobrar entrada apos o loss   ou nao nao dobrar entrada

def payout(par, tipo, timeframe=1):
    if tipo == 'turbo':
        a = Iq.get_all_profit()
        return int(100 * a[par]['turbo'])

    elif tipo == 'digital':

        Iq.subscribe_strike_list(par, timeframe)
        while True:
            d = Iq.get_digital_current_profit(par, timeframe)
            if d != False:
                d = int(d)
                break
            time.sleep(1)
        Iq.unsubscribe_strike_list(par, timeframe)
        return d


def Ver_ativos_aberto_turbo_m1():
    print('\n\n Verificando ativos aberto na BINARIAS')
    par = Iq.get_all_open_time()
    for paridade in par['turbo']:
        if par['turbo'][paridade]['open']:
            print('[ TURBO ]: ' + paridade + ' | Payout: ' + str(payout(paridade, 'turbo')))
            time.sleep(1)

''' print('\n Verificando ativos aberto na DIGITAL')
    par = Iq.get_all_open_time()
    for paridade in par['digital']:
        if par['digital'][paridade]['open']:
            print('[ DIGITAL ]: ' + paridade + ' | payout: ' + str(payout(paridade, 'digital')))'''

x = perfil()
print('\n\n============================================')
print('Ola:', x['name'])
print("Seu Saldo inicial R$:", str(Iq.get_balance()))
print('============================================')

Ver_ativos_aberto_turbo_m1()
par = input('\n Indique uma paridade para operar: ').upper()
valor_entrada = float(input(' Indique um valor para entrar: ''\n'))
valor_entrada_b = float(valor_entrada)


def put():
    global valor_entrada
    dir = 'put'
    print('\nIniciando operação!')
    print(datetime.now().strftime(' %d.%m.%Y %H:%M:%S'), end='\r')
    print('\n Direção =', dir, '', '\n Ativo: ', par, ' Valor entrada: ', valor_entrada)
    status, id = Iq.buy(valor_entrada, par, dir, 5)
    if isinstance(id, int):
        while True:
            _, lucro = Iq.check_win_v3(id)
            if status:
                if lucro > 0:
                    if lucro == 0:
                        print('Deu impate Entrada sera o valor da entrada Base')
                        valor_entrada = valor_entrada_b
                    print(Fore.LIGHTGREEN_EX + ' Win ✅😎  : ' + Fore.RESET + str(round(lucro, 2)))
                    print(datetime.now().strftime('%d.%m.%Y %H:%M:%S'), end='\r')
                    valor_entrada = valor_entrada_b  # volta valor da entrada inicial apos o win
                    print('=+=+=+' * 20)
                    print('Aguardando Proximo sinal!!')
                    time.sleep(6)
                    break
                else:
                    print(Fore.RED + ' Loss ❌😖 !! : ' + Fore.RESET + str(round(lucro, 2)))
                    if dobrar_entrada == 'sim':
                        valor_entrada = valor_entrada * 2.3

                break


def call():
    global valor_entrada
    dir = 'call'
    print('\nIniciando operação!')
    print(datetime.now().strftime(' %d.%m.%Y %H:%M:%S'), end='\r')
    print('\n Direção =', dir, '', '\n Ativo: ', par, ' Valor entrada: ', valor_entrada)
    status, id = Iq.buy(valor_entrada, par, dir, 5)
    if isinstance(id, int):
        while True:
            _, lucro = Iq.check_win_v3(id)
            if status:
                if lucro > 0:
                    if lucro == 0:
                        print('Deu impate Entrada sera o valor da entrada Base')
                        valor_entrada = valor_entrada_b
                    print(Fore.LIGHTGREEN_EX + ' Win ✅😎  : ' + Fore.RESET + str(round(lucro, 2)))
                    print(datetime.now().strftime('%d.%m.%Y %H:%M:%S'), end='\r')
                    valor_entrada = valor_entrada_b  # volta valor da entrada inicial apos o win
                    print('=+=+=+' * 20)
                    print('Aguardando Proximo sinal!!')

                    break
                else:
                    print(Fore.RED + ' Loss ❌😖 !! : ' + Fore.RESET + str(round(lucro, 2)))
                    if dobrar_entrada == 'sim':
                        valor_entrada = valor_entrada * 2.3

                break


def rsi1():
    ############# rsi ##############################
    bars = Iq.get_candles(par, 60, 15, time.time())
    close = []
    for x in bars:
        close.append(x["close"])

    closed_array = numpy.array(close)
    rsi = talib.RSI(closed_array, timeperiod=RSI_timeperiod)
    if rsi[-1] > RSI_SOBRE_COMPRADO:
        print('  RSI ACIMA DE 65.00 ..')
        print('\r  RSI --> %s' % rsi[-1])
        put()
        print('==========================================================')
    elif rsi[-1] < RSI_SOBRE_VENDA:
        print('  RSI ABAIXO DE 35.00 ..')
        print('\r  RSI --> %s' % rsi[-1])
        call()
        print('==========================================================')

    else:
        sys.stdout.write('\r  RSI NEUTRO --> %s' % rsi[-1])


while True:
    # time.sleep(0.5)
    rsi1()
