from .common_imports import *

REQUEST_TIMESTAMPS = []

def get_user_date_range():
    try:
        max_date=datetime.now()
        print("Wybierz zakres dat dla danych o rtoacjach")
        start_str = input(f"Data początkowa RRRR-MM-DD: ").strip()
        end_str = input(f"Data końcowa RRRR-MM-DD: ").strip()

        start_date = pd.to_datetime(start_str, format="%Y-%m-%d", errors="raise")
        end_date = pd.to_datetime(end_str, format="%Y-%m-%d", errors="raise")

        if end_date < start_date:
            raise ValueError("Data końcowa nie może być wcześniejsza niż początkowa.")
        if end_date > max_date:
            raise ValueError("Data końcowa wychodzi poza dostępny zakres.")

        return start_date, end_date

    except Exception as e:
        print(f"\n{e}")
        print("Upewnij się, że wprowadzasz daty w formacie: RRRR-MM-DD (np. 2025-10-05)")
        raise SystemExit(1)


def Avg_cost(product_ids: list, baselinker_api_url: str, bl_token: str, inventory_id: int, pace: int ) -> dict:
    """Pobiera sredni koszt productu o danym id"""
    product_ids = list(set(product_ids))
    chunk_size = 500
    result = {}

    for i in range(0, len(product_ids), chunk_size):
        chunk = product_ids[i:i+chunk_size]
        method_params = {   "inventory_id": inventory_id, "products": chunk }
        data = bl_request("getInventoryProductsData", method_params, baselinker_api_url, bl_token, pace )
        REQUEST_TIMESTAMPS.append(time.time())

        for pid, pdata in data["products"].items():
            result[pid] = float(pdata.get("average_cost", 0))

    return result


def get_rotacje(baselinker_api_url: str, bl_token: str, inventory_id: int,
                 save_csv: bool = True, csv_dir: Path = Path(__file__).parent, pace: int = 70 ) -> pd.DataFrame:
    """Pobiera wszystkie zamówienia z BaseLinker od `days` dni wstecz i zwraca listę słowników gotowych do CSV"""
    
    date_from, date_to = get_user_date_range()
    print("Rozpoczynam pobieranie danych o rotacjach\n")
    date_from = int(date_from.timestamp())
    date_to = int(date_to.timestamp())

    global MAX_REQUESTS, MIN_INTERVAL
    MAX_REQUESTS = pace
    MIN_INTERVAL = 60 / pace

    # DIRECTORY
    output_file = csv_dir / f"rotacje_from_{datetime.fromtimestamp(date_from).strftime('%Y-%m-%d')}.csv"

    all_orders = []
    date_confirmed_from = date_from
    while True:

        # wyliczamy zapytania/min
        now = time.time()
        REQUEST_TIMESTAMPS[:] = [t for t in REQUEST_TIMESTAMPS if now - t < WINDOW]  # czyścimy stare
        rpm = len(REQUEST_TIMESTAMPS)  # requests per minute
        print(f"\rZapytania: {rpm}/min", end="", flush=True)

        method_params = { "date_confirmed_from": date_confirmed_from, "get_unconfirmed_orders": False }
        # wysłanie POST
        data = bl_request( "getOrders", method_params, baselinker_api_url, bl_token, pace )
        REQUEST_TIMESTAMPS.append(time.time())
        orders_in_range = [o for o in data["orders"] if o["date_confirmed"] <= date_to]
        all_orders.extend(orders_in_range)
        
        # sprawdzenie czy <100 zamowien tzn. koniec pobierania 
        if len(data["orders"]) < 100:
            break

        # dodajemy seknde do daty ostatniego pobranego zamówienia aby nie pobrac go ponownie
        date_confirmed_from = data['orders'][-1]["date_confirmed"] + 1
        if date_confirmed_from > date_to:
            break

    products_ids_avg = []
    for order in all_orders:
        for p in order.get("products", []):
            products_ids_avg.append(p["product_id"])
    try:
        avg_costs = Avg_cost( products_ids_avg, baselinker_api_url, bl_token, inventory_id, pace )
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
        print(f"\nZakończono pobieranie. Plik {output_file}")
        
    return df_rotacje


if __name__ == "__main__":
    BASELINKER_API_URL = "https://api.baselinker.com/connector.php"
    BL_TOKEN = "5004221-5013195-GBT19RBZAAJG4AKIFRAG9547IT7X7QV6L4K47L40RC5TDX64NZ852KP2VYL4E65B"
    INVENTORY_ID = 35072

    try:
        get_rotacje(BASELINKER_API_URL, BL_TOKEN, INVENTORY_ID, save_csv=True, csv_dir=Path(__file__).parent, pace=70 )
    except Exception as e:
        print("ERROR:", e)