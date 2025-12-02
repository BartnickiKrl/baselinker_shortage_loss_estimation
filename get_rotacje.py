import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import time
# json obsluga bledow try except

# Zarządzanie czasem – 70 zapytań/min
REQUEST_TIMESTAMPS = []
MAX_REQUESTS = 70
WINDOW = 60
LAST_REQUEST = 0
MIN_INTERVAL = 60 / MAX_REQUESTS    # 0.857 sekundy

def bl_request(method, method_params, api_url, token):
    """
    Zapytanie do BaseLinkera
    - opóźnienie 0.86s - 70/min
    - 3 retry (1s, 5s, 5s)
    """
    global LAST_REQUEST, REQUEST_TIMESTAMPS

    # bezpieczne stałe tempo 70/min
    now = time.time()
    elapsed = now - LAST_REQUEST
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)

    LAST_REQUEST = time.time()
    backoff_times = [1, 5, 5]

    for attempt in range(4):
        try:
            headers = {"X-BLToken": token}
            api_params = {"method": method, "parameters": json.dumps(method_params)}

            response = requests.post(api_url, data=api_params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data["status"] != "SUCCESS":
                raise RuntimeError(f"BL META ERROR: {data}")

            # zapisz timestamp
            REQUEST_TIMESTAMPS.append(time.time())
            return data

        except Exception as e:
            if attempt == 3:
                raise

            # (1s, 5s, 5s)
            time.sleep(backoff_times[attempt])

def get_date_from(days:int = 180) -> int:
    now = datetime.now()
    date_from = now - timedelta(days=days)
    return int(date_from.timestamp())


def Avg_cost(product_ids: list, baselinker_api_url: str, bl_token: str, inventory_id: int ) -> dict:
    """Pobiera sredni koszt productu o danym id"""
    product_ids = list(set(product_ids))
    chunk_size = 500
    result = {}

    for i in range(0, len(product_ids), chunk_size):
        chunk = product_ids[i:i+chunk_size]
        method_params = {   "inventory_id": inventory_id,
                        "products": chunk }
        data = bl_request("getInventoryProductsData", 
                              method_params,
                              baselinker_api_url, bl_token)

        for pid, pdata in data["products"].items():
            result[pid] = float(pdata.get("average_cost", 0))

    return result



def get_rotacje(baselinker_api_url: str, bl_token: str, inventory_id: int, days: int = 180,
                 save_csv: bool = True, csv_dir: Path = Path(__file__).parent, pace: int = 70 ) -> pd.DataFrame:
    """Pobiera wszystkie zamówienia z BaseLinker od `days` dni wstecz i zwraca listę słowników gotowych do CSV"""
    
    global MAX_REQUESTS, MIN_INTERVAL
    MAX_REQUESTS = pace
    MIN_INTERVAL = 60 / pace

    # DIRECTORY
    output_file = csv_dir / f"rotacje_{datetime.fromtimestamp(get_date_from(days)).strftime('%Y-%m-%d')}.csv"

    all_orders = []
    date_confirmed_from = get_date_from(days)

    while True:

        # wyliczamy zapytania/min
        now = time.time()
        REQUEST_TIMESTAMPS[:] = [t for t in REQUEST_TIMESTAMPS if now - t < WINDOW]  # czyścimy stare
        rpm = len(REQUEST_TIMESTAMPS)  # requests per minute
        print(f"\rZapytania: {rpm}/min", end="", flush=True)

        method_params = { "date_confirmed_from": date_confirmed_from, "get_unconfirmed_orders": False }
        # wysłanie POST
        data = bl_request( "getOrders", method_params, baselinker_api_url, bl_token )
        
        all_orders.extend(data['orders'])
        
        # sprawdzenie czy <100 zamowien tzn. koniec pobierania 
        if len(data["orders"]) < 100:
            break

        # dodajemy seknde do daty ostatniego pobranego zamówienia aby nie pobrac go ponownie
        date_confirmed_from = data['orders'][-1]["date_confirmed"] + 1

    products_ids_avg = []
    for order in all_orders:
        for p in order.get("products", []):
            products_ids_avg.append(p["product_id"])
    try:
        avg_costs = Avg_cost( products_ids_avg, baselinker_api_url, bl_token, inventory_id )
    except Exception as e:
            print("Błąd przy pobieraniu srednich cen dla produktow:", e)
    

    rotacje_rows = []
    for order in all_orders:
        if "products" not in order or not order["products"]:
            continue
        for product in order["products"]:
            row = {
                "product_id": product["product_id"],
                "variant_id": product["variant_id"],
                "rotation_qty": product["quantity"],
                "unit_price_brutto": product["price_brutto"],
                "purchase_cost":  avg_costs.get(product["product_id"], 0),
                "date": (datetime.fromtimestamp(order["date_confirmed"])).strftime('%Y-%m-%d'),  
                "weekday": (datetime.fromtimestamp(order["date_confirmed"])).weekday() + 1,
                "hour": (datetime.fromtimestamp(order["date_confirmed"])).strftime('%H')
            }
            rotacje_rows.append(row)

    df_rotacje = pd.DataFrame(rotacje_rows)
    df_rotacje = df_rotacje.sort_values(by=df_rotacje.columns[5])

    if save_csv and not df_rotacje.empty:
        df_rotacje.to_csv(output_file, sep=";", index=False, encoding="utf-8")
        print(f"Zakończono pobieranie. Plik {output_file}")
        
    return df_rotacje


if __name__ == "__main__":
    BASELINKER_API_URL = "https://api.baselinker.com/connector.php"
    BL_TOKEN = "5004221-5013195-GBT19RBZAAJG4AKIFRAG9547IT7X7QV6L4K47L40RC5TDX64NZ852KP2VYL4E65B"
    INVENTORY_ID = 35072

    try:
        get_rotacje(BASELINKER_API_URL, BL_TOKEN, INVENTORY_ID, days=180, save_csv=True, csv_dir=Path(__file__).parent )
    except Exception as e:
        print("ERROR:", e)