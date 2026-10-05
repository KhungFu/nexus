# -*- coding: utf-8 -*-
import requests, os
from dotenv import load_dotenv

load_dotenv()

LIVE_URL = 'https://api-capital.backend-capital.com/api/v1'
DEMO_URL = 'https://demo-api-capital.backend-capital.com/api/v1'

def get_accounts(url, label):
    identifier = os.getenv('CAPITAL_IDENTIFIER')
    password   = os.getenv('CAPITAL_PASSWORD')
    api_key    = os.getenv('CAPITAL_API_KEY')

    if not all([identifier, password, api_key]):
        print("HATA: .env dosyasinda eksik bilgiler var!")
        print("Gereken: CAPITAL_IDENTIFIER, CAPITAL_PASSWORD, CAPITAL_API_KEY")
        return

    headers = {'X-CAP-API-KEY': api_key, 'Content-Type': 'application/json'}

    try:
        r = requests.post(f'{url}/session',
                          json={'identifier': identifier, 'password': password},
                          headers=headers, timeout=15)

        if r.status_code == 200:
            h = {
                'X-CAP-API-KEY':    api_key,
                'CST':              r.headers.get('CST'),
                'X-SECURITY-TOKEN': r.headers.get('X-SECURITY-TOKEN')
            }

            acc_res = requests.get(f'{url}/accounts', headers=h, timeout=15)
            if acc_res.status_code == 200:
                accounts = acc_res.json().get('accounts', [])

                print('\n' + '='*50)
                print(f'CAPITAL.COM HESAP LISTESI ({label})')
                print('='*50)

                for a in accounts:
                    name     = a.get('accountName', '?')
                    acc_id   = a.get('accountId', '?')
                    balance  = a.get('balance', {}).get('balance', '?')
                    currency = a.get('currency', 'EUR')
                    status   = 'AKTIF' if a.get('status') == 'ENABLED' else 'PASIF'

                    print(f"Isim   : {name}")
                    print(f"ID     : {acc_id}")
                    print(f"Bakiye : {balance} {currency}")
                    print(f"Durum  : {status}")
                    print('-'*50)

                print()
                print("NOT: Kullanmak istedigin hesap ID'sini kopyala.")
                print("     .env dosyasina ekle: CAPITAL_ACCOUNT_ID=<ID>")
                print("     Demo icin: IS_DEMO=true")
                print("     Canli icin: IS_DEMO=false")
            else:
                print(f"HATA: Hesap listesi alinamadi: {acc_res.text}")
        else:
            print(f"HATA: Giris basarisiz (HTTP {r.status_code}): {r.text}")

    except Exception as e:
        print(f"Baglanti hatasi: {e}")


if __name__ == '__main__':
    print("CAPITAL.COM HESAP BULUCU")
    print("Hem Demo hem Canli hesaplari listeleniyor...\n")

    get_accounts(DEMO_URL, "DEMO")
    get_accounts(LIVE_URL, "CANLI (LIVE)")
