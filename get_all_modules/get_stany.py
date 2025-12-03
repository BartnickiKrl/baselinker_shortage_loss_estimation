from .common_imports import *

# zapis timestamp
REQUEST_TIMESTAMPS = []

def get_date_from_last_6_months() -> int:
    now = datetime.now()
    date_from = now - timedelta(days=180)
    return int(date_from.timestamp())


def make_row( date: datetime, id, sku, ean, prev_stock_str, new_stock_str) -> list[dict]:
    
    try:
        prev_stock = float(prev_stock_str)
        new_stock = float(new_stock_str)
    except (TypeError, ValueError):
        print(prev_stock_str, new_stock_str)
        return []

    if (prev_stock > 0 and new_stock > 0 ) or (prev_stock <= 0 and new_stock <= 0):
        return []

    row1={}
    if prev_stock <= 0 and new_stock > 0 and date:
        row1 =  { "data": date, "id": id, "sku": sku, "ean": ean,
            "stan_przed": "zakończona", "stan_po": "rozkręcanie" }
        
        prev_stock = "rozkręcanie"
        new_stock = "aktywna"
        date += timedelta(hours=24)
    else:
        prev_stock = "aktywna"
        new_stock = "zakończona"
    
    if date:
        row2 =  { "data": date, "id": id, "sku": sku, "ean": ean,
            "stan_przed": prev_stock, "stan_po": new_stock }
    
    if row1:
        return [row2, row1]
    elif row2:
        return [row2]
    return []


def get_stany(products_ids: pd.DataFrame, date_from_ts: int, baselinker_api_url: str, bl_token: str,
               save_csv: bool = True, csv_dir: Path = Path(__file__).parent, pace: int = 70 ) -> pd.DataFrame: 

    timer = time.time()

    if products_ids.empty:
        print("Brak produktów do przetworzenia")
        return pd.DataFrame()

    # DIRECTORY
    output_file = csv_dir / f"stany_from_{datetime.fromtimestamp(date_from_ts).strftime('%Y-%m-%d')}.csv"

    rpm = 0
    stany_rows = []
    for product_number in range(len(products_ids)):

        product_id = products_ids.iloc[product_number, 0]
        page = 1
        product_stats=[]
        first_log = 1
        while True:

            # wyliczamy zapytania/min
            now = time.time()
            REQUEST_TIMESTAMPS[:] = [t for t in REQUEST_TIMESTAMPS if now - t < WINDOW]  # czyścimy stare
            rpm = len(REQUEST_TIMESTAMPS)  # requests per minute
            procent = ((product_number+1)/len(products_ids))*100 
            elapsed = time.time() - timer
            remaining = (100 * elapsed / procent) - elapsed if procent > 0 else 0
            print(f"\rUkonczono: {procent:.0f}% | Zapytania/min: {rpm} | Pozostało ok. {remaining:.0f}s", end="", flush=True)


            method_params = {
                "product_id": int(product_id),
                "date_from": int(date_from_ts),
                "sort": "ASC",  # rosnąco po czasie
                "page": int(page),
                "type": 1 }
            
            data = bl_request("getInventoryProductLogs", method_params, baselinker_api_url, bl_token, pace)
            REQUEST_TIMESTAMPS.append(time.time())
            product_stats.extend(data["logs"])
            
            # sprawdzenie czy <100 logow tzn. koniec pobierania 
            if len(data["logs"]) < 100:
                break

            # przerzucamy strone
            page += 1
    

        for logi in product_stats:
            log_date_ts = logi.get("time")
            if not log_date_ts:
                continue  # pomiń logi bez daty

            entries = logi.get("entries", [])
    
            if isinstance(entries, dict):
                entries = [entries]
            
            for entry in entries:
                if entry.get("type") == 1:
                    row = make_row( datetime.fromtimestamp(int(logi["time"])), 
                                    product_id, 
                                    products_ids.iloc[product_number, 2], 
                                    products_ids.iloc[product_number, 1],
                                    entry.get("from"), 
                                    entry.get("to") )
                    if row == []:
                        continue
                    if first_log and row:
                        row = row[0]
                        row["stan_przed"] = ""
                        first_log = 0
                        row = [row]

                    stany_rows.extend(row)

    df_stany = pd.DataFrame(stany_rows)
    print(df_stany.head())
    if not df_stany.empty:
        df_stany = df_stany.sort_values(by=df_stany.columns[0])

    if save_csv and not df_stany.empty:
        df_stany.to_csv(output_file, sep=";", index=False, encoding="utf-8")
        print(f"Zakończono pobieranie. Plik {output_file}")

    return df_stany


if __name__ == "__main__":
    BASELINKER_API_URL = "https://api.baselinker.com/connector.php"
    BL_TOKEN = "5004221-5013195-GBT19RBZAAJG4AKIFRAG9547IT7X7QV6L4K47L40RC5TDX64NZ852KP2VYL4E65B"

    df_produkty = pd.read_csv(Path(__file__).parent/"products_list.csv", sep=";")
    try:
        get_stany( df_produkty, get_date_from_last_6_months(), BASELINKER_API_URL, BL_TOKEN, save_csv=True, csv_dir=Path(__file__).parent, pace=70 )
    except Exception as e:
        print("ERROR:", e)