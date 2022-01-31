from iqoptionapi.stable_api import IQ_Option
from colorama import init, Fore, Back, Style
import time, json, logging, configparser
from datetime import datetime, date, timedelta
import getpass
import sys

init(convert=True)

print(Style.BRIGHT + Fore.YELLOW + '''
	           R2 AUTOCOPY
 -----------------------------------------------
''' + Style.RESET_ALL)

logging.disable(level=(logging.DEBUG))

datet = '2022-02-10'

ExpirationDate = time.strftime("%Y-%m-%d")
if ExpirationDate >= datet:
    print(Fore.YELLOW + '\n   RENOVE A LICENÇA - TEMPO DE TESTE ACABOU!\n\n' + Fore.RESET)
    print(Fore.YELLOW + '\n   ENTRE EM CONTATO COM A R2 TRADERS\n\n' + Fore.RESET)
    time.sleep(10)
    sys.exit()
elif ExpirationDate == datet:
    print(Fore.YELLOW + '\n   LICENÇA EXPIRA HOJE!\n\n' + Fore.RESET)

error_password="""{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""

print(Style.BRIGHT + Fore.BLUE + '   Login: ' + Fore.RESET)
login = input('   ')
print('\n   Sua senha será ocultada!')
print(Style.BRIGHT + Fore.BLUE + '   Senha: ' + Fore.RESET)
senha = getpass.getpass('   ')

API=IQ_Option(login, senha)
cq, rs = API.connect()

if cq:
    print("\n   Conectado com Sucesso!\n\n")
    #if see this you can close network for test
    while True:
        if API.check_connect()==False:#detect the websocket is close
            print('\n   Tentando reconectar...\n\n')
            cq, rs = API.connect()
            if cq:
                print("\n   Reconectado com Sucesso!\n\n")
            else:
                if rs==error_password:
                    print(Fore.YELLOW + '\n   EMAIL OU SENHA INCORRETOS!\n\n' + Fore.RESET)
                    input("\n   Pressione ENTER para sair")
                    sys.exit()
                else:
                    print(Fore.YELLOW + '\n   SEM CONEXÃO!\n\n' + Fore.RESET)
                    input("\n   Pressione ENTER para sair")
                    sys.exit()
        break
else:
    if rs=="[Errno -2] Name or service not known":
        print(Fore.YELLOW + '\n   SEM CONEXÃO!\n\n' + Fore.RESET)
        input("\n   Pressione ENTER para sair")
        sys.exit()
    elif rs==error_password:
        print(Fore.YELLOW + '\n   EMAIL OU SENHA INCORRETOS!\n\n' + Fore.RESET)
        input("\n   Pressione ENTER para sair")
        sys.exit()

time.sleep(1)

API.change_balance('PRACTICE') # PRACTICE / REAL

user_id = API.get_profile_ansyc()['user_id']
print('\n   Usuário ID: ' + str(user_id))

profile = API.get_profile_ansyc()
for balance in profile["balances"]:
    if balance["type"] == 1:
        real_id = balance["id"]
    elif balance["type"] == 4:
        demo_id = balance["id"]

print(Style.BRIGHT + Fore.BLUE + '\n   Valor por Operação: ' + Fore.RESET)
valor_fixo = float(input('          '))

print(Style.BRIGHT + Fore.BLUE + '\n   Valor de Stop Gain: ' + Fore.RESET)
stop_gain = float(input('           '))

print(Style.BRIGHT + Fore.BLUE + '\n   Valor de Stop Loss: ' + Fore.RESET)
stop_loss = float(input('           '))

stop_loss = float(stop_loss * (-1))

if int(valor_fixo) < 2:
    valor_fixo = 2

tipo ='digital-option'
old = []
id_list = []
buyop_list = []
last_op = 0
lucro_total = 0
v = 0
b = 0

print("\n   Esperando Entradas...\n\n")

while True:

    ck, digital_data = API.get_positions(tipo)

    if ck == True:
        total_trades = list(digital_data.values())[0]

        if total_trades > 0:

            trades_data= list(digital_data.values())[-1]

            for trade in trades_data:

                position = trade['orders'][0]['position_id']
                buy_order = position = trade['orders'][0]['id']

                if not position in old:

                    par = str(trade['instrument_underlying'])
                    valor = trade['buy_amount']
                    direcao = str(trade['instrument_dir'])
                    timeframe = int(trade['instrument_period'] / 60)

                    if valor < 2:
                        valor = 2

                    API.change_balance('REAL') # PRACTICE / REAL

                    status, id = API.buy_digital_spot(par, valor_fixo, direcao, timeframe)
                    #status,id = API.buy(valor, par, direcao, timeframe)

                    print("   Dados de Entrada da Conta Demo")
                    print(Fore.BLUE + '   [ ! ]', par, ' / ', direcao, ' / %.2f' %(valor_fixo), '$ / ', int(timeframe),'M' + Fore.RESET)

                    if status:
                        print("   Copiado para Conta Real!\n")
                        id_list.append(id)
                    else:
                        print(Fore.YELLOW + '\n   NÃO FOI POSSÍVEL REALIZAR A OPERAÇÃO!\n' + Fore.RESET)

                    API.change_balance('PRACTICE') # PRACTICE / REAL

                    old.append(position)
        else:
            if id_list != []:
                API.change_balance('REAL') # PRACTICE / REAL
                for x in id_list:
                    all_data = API.get_digital_position(x)
                    order_data = all_data['msg']['position']
                    ativo = order_data['instrument_underlying']
                    investimento = float(order_data["buy_amount"])
                    retorno = float(order_data["close_effect_amount"])
                    lucro = (retorno - investimento)
                    lucro_total += lucro
                    b += 1
                    if lucro > 0:
                        print(Fore.GREEN + '   [ ! ]', ativo, ' / RESULTADO: WIN / LUCRO: %.2f' %(lucro), '$' + Fore.RESET)
                    else:
                        print(Fore.RED  + '   [ ! ]', ativo, ' / RESULTADO: LOSS / LUCRO: %.2f' %(lucro), '$' + Fore.RESET)
                if b > v:
                    if lucro_total > 0:
                        print(Fore.GREEN + '\n   LUCRO TOTAL: %.2f' %(lucro_total), '$' + Fore.RESET)
                        v = b
                        id_list.clear()
                        old.clear()
                    else:
                        print(Fore.RED  + '\n   LUCRO TOTAL: %.2f' %(lucro_total), '$' + Fore.RESET)
                        v = b
                        id_list.clear()
                        old.clear()
                    if lucro_total > stop_gain:
                        print(Fore.GREEN + '\n   ! PARABÉNS ! STOP GAIN ATINGIDO !: %.2f' %(lucro_total), '$' + Fore.RESET)
                        input("\n   Pressione ENTER para sair")
                        sys.exit()
                    elif lucro_total < stop_loss:
                        print(Fore.RED  + '\n   ! PARE DE OPERAR ! STOP LOSS ATINGIDO: %.2f' %(lucro_total), '$' + Fore.RESET)
                        input("\n   Pressione ENTER para sair")
                        sys.exit()
                API.change_balance('PRACTICE') # PRACTICE / REAL

    API.change_balance('PRACTICE') # PRACTICE / REAL
    if API.get_option_open_by_other_pc()!={}:

        id_op=list(API.get_option_open_by_other_pc().keys())[0]
        data_op = list(API.get_option_open_by_other_pc().values())[0]['msg']
        API.del_option_open_by_other_pc(id_op)

        exp_op = int(round((data_op['exp_time'] - data_op['created'])/60, 0))
        dir_op = str(data_op['dir'])
        par_op = str(data_op['active'])
        valor_op = data_op['profit_amount']
        balance_op = data_op['user_balance_id']

        if balance_op == demo_id:

            API.change_balance('REAL') # PRACTICE / REAL

            status_op, buyid_op = API.buy(valor_fixo, par_op, dir_op, exp_op)

            print("   Dados de Entrada da Conta Demo")
            print(Fore.BLUE + '   [ ! ]', par_op, ' / ', dir_op, ' / %.2f' %(valor_fixo), '$ / ', exp_op,'M' + Fore.RESET)

            if status_op:
                print("   Copiado para Conta Real!\n")
                buyop_list.append(buyid_op)
            else:
                print(Fore.YELLOW + '\n   NÃO FOI POSSÍVEL REALIZAR A OPERAÇÃO!\n' + Fore.RESET)


    else:
        new_op = list(API.get_optioninfo_v2(1).values())
        open_op = new_op[-2]['open_options']

        if buyop_list != [] and open_op == []:

            for buyop_rs in buyop_list:
                result_data = API.get_async_order(buyop_rs)["option-closed"]['msg']

                lucro = float(result_data['profit_amount'] - result_data['amount'])
                ativo = result_data['active']
                buyop_list.remove(buyop_rs)
                lucro_total += lucro

                if lucro > 0:
                    print(Fore.GREEN + '   [ ! ]', ativo, ' / RESULTADO: WIN / LUCRO: %.2f' %(lucro), '$' + Fore.RESET)
                else:
                    print(Fore.RED  + '   [ ! ]', ativo, ' / RESULTADO: LOSS / LUCRO: %.2f' %(lucro), '$' + Fore.RESET)

                if lucro_total > 0:
                    print(Fore.GREEN + '\n   LUCRO TOTAL: %.2f' %(lucro_total), '$' + Fore.RESET)
                else:
                    print(Fore.RED  + '\n   LUCRO TOTAL: %.2f' %(lucro_total), '$' + Fore.RESET)

                if lucro_total > stop_gain:
                    print(Fore.GREEN + '\n   ! PARABÉNS ! STOP GAIN ATINGIDO !: %.2f' %(lucro_total), '$' + Fore.RESET)
                    input("\n   Pressione ENTER para sair")
                    sys.exit()
                elif lucro_total < stop_loss:
                    print(Fore.RED  + '\n   ! PARE DE OPERAR ! STOP LOSS ATINGIDO: %.2f' %(lucro_total), '$' + Fore.RESET)
                    input("\n   Pressione ENTER para sair")
                    sys.exit()

    time.sleep(0.2)



