import time
import numpy as np
import winsound
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.constants import ACTIVES
# Connexion à IQ Option
email = "email@example.com"
password = "password"

api = IQ_Option(email, password)
check, reason = api.connect()

if check:
    print("Connexion réussie!")
else:
    print(f"Échec de la connexion: {reason}")
    exit(1)

# Configurations
asset = "EURUSD"
candle_timeframe = 60  # 1 minute
trade_duration = 1  # 1 minute
amount = 1.5

rsi_period = 14
rsi_overbought = 70
rsi_oversold = 30

# Détection des niveaux de support et de résistance
def get_support_resistance(candles):
    closes = [candle['close'] for candle in candles]
    high = max(closes)
    low = min(closes)
    return low, high

def calculate_rsi(closes, period):
    deltas = np.diff(closes)
    seed = deltas[:period + 1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down
    rsi = np.zeros_like(closes)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(closes)):
        delta = deltas[i - 1]

        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

# Fonction pour détecter le range avec RSI
def detect_range_with_rsi(candles, rsi_period, rsi_overbought, rsi_oversold):
    closes = np.array([candle['close'] for candle in candles])
    rsi_values = calculate_rsi(closes, rsi_period)
    current_rsi = rsi_values[-1]

    if current_rsi >= rsi_overbought:
        return 'overbought'  # Prix dans une zone de surachat
    elif current_rsi <= rsi_oversold:
        return 'oversold'  # Prix dans une zone de survente
    else:
        return None  # Pas de signal RSI clair

def trigger_alert(file):
    winsound.PlaySound(file, winsound.SND_FILENAME)

def now():
    return time.strftime('%H:%M:%S', time.gmtime())

def load_goals(api):
    profits_from_iq = api.get_all_profit()
    assets_from_iq = api.get_all_open_time()
    inst = {i: profits_from_iq[i]['turbo'] for i in assets_from_iq['turbo'] if assets_from_iq['turbo'][i]['open']}
    return inst

#============================================== main ==========================================================
assets = load_goals(api)
print('Démarrage du bot de trading...')
print('Attente pour synchronisation...', 60 - time.localtime().tm_sec - 1, ' seconds.')
DUREE_ATTENTE_SECONDES = 60

SMA_WINDOW = 20 
trade = False
profit = 0
total_loss = 0
total_win = 0
trade = False
nbre = 0
alert = 1
par=''
debut = 0
prix = 1.5
amount = 1.5
prix = amount
alert = True
sorted_keys = sorted(assets.keys())
while True:
    while int(time.localtime().tm_sec % 60) < 1:
        for asset in sorted_keys:
            if asset in ACTIVES:
                print(f"{now()} Currency: {asset}")
                candles = api.get_candles(asset, candle_timeframe, 200, time.time())
                
                support, resistance = get_support_resistance(candles)
                latest_close = candles[-1]['close']
                signal = detect_range_with_rsi(candles, rsi_period, rsi_overbought, rsi_oversold)
                print('signal: ',signal)

                if signal == 'oversold' and latest_close <= support and par != asset:
                    print(f"{now()} Niveau de support atteint pour {asset}. Trade call.")
                    status, id = api.buy(amount, asset, 'call', trade_duration)
                    par = asset
                    if alert == 1:
                        trigger_alert("alerte.wav")
                    trade = True
                    if status:
                        print(f"{now()} Trade call ouvert")
                    else:
                        print(f"{now()} Erreur lors du placement du trade call")
                    break
                elif signal == 'overbought' and latest_close >= resistance and par != asset:
                    print(f"{now()} Niveau de résistance atteint pour {asset}. Trade put.")
                    status, id = api.buy(amount, asset, 'put', trade_duration)
                    par = asset
                    if alert == 1:
                        trigger_alert("alerte.wav")
                    trade = True
                    if status:
                        print(f"{now()} Trade put ouvert")
                    else:
                        print(f"{now()} Erreur lors du placement du trade put")
                    break
                else:
                    print("Aucun signal détecté. Pas de trade.")
                    trade = False

        if trade:
            print('Attendez 1 Minute svp...')
            succes, idd = api.check_win_v4(id)
            if idd < 0:
                print('>> Loose     : ', str('%.2f' % idd) + ' $')
                profit += idd
                total_loss += 1
                #if debut>=1:
                amount = amount * 2.3
                debut +=1
                trade = False
                if alert == 1:
                    trigger_alert("loose.wav")
            elif idd > 0:
                print('>> Win       : ', str('%.2f' % idd) + ' $')
                profit += idd
                total_win += 1
                #amount = amount +idd
                amount = prix
                nbre +=1
                trade = False
                debut = 0
                if alert == 1:
                    trigger_alert("win.wav")
            else:
                print('>> Equals       : ', str('%.2f' % idd) + ' $')
                trade = False

        print('\n')
        if profit > 0:
            print('Getting profits actuel: ', str('%.2f' % profit) + ' $', '\n')
        elif profit < 0:
            print('Getting profits actuel: ', str('%.2f' % profit) + ' $', '\n')
        else:
            print('Getting profits actuel: ', str('%.2f' % profit) + ' $', '\n')

        print("# Total Win : ", total_win, "x")
        print("# Total Loss : ", total_loss, "x")

        print()
        timeToSleep = 60 - time.localtime().tm_sec - 1
        print(f'Attente pour prochaines bougies {timeToSleep} secondes.\n')
        time.sleep(timeToSleep)
