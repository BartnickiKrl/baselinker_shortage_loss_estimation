import requests
import json
import pandas as pd
from pathlib import Path
import time

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


def get_produkty(baselinker_api_url: str, bl_token: str, inventory_id: int,
                 save_csv: bool = True, csv_dir: Path = Path(__file__).parent, pace: int = 70) -> pd.DataFrame:
    """
    Pobiera WSZYSTKIE produkty z BaseLinkera (łącznie z wariantami),
    pobiera meta (nazwy, SKU, EAN),
    filtruje bundlery i rodziców wariantów,
    zwraca DataFrame oraz zapisuje CSV.
    """

    global MAX_REQUESTS, MIN_INTERVAL
    MAX_REQUESTS = pace
    MIN_INTERVAL = 60 / pace

    # WYJŚCIE
    output_path = csv_dir / "products_list.csv"

    # =====================================================================
    # 1) Pobieranie produktów strona po stronie
    # =====================================================================
    all_products_basic = []
    page = 1

    while True:
        try:
            parameters = {
                    "inventory_id": int(inventory_id),
                    "page": page,
                    "include_variants": True}

            data = bl_request("getInventoryProductsList", parameters, baselinker_api_url, bl_token)

            products_page = data.get("products") or {}

        except Exception as e:
            print(f"[ERROR] Nie udało się pobrać strony {page}: {e}")
            break

        # brak dalszych stron
        if not products_page:
            break

        # dodaj wszystkie
        all_products_basic.extend(list(products_page.values()))

        page += 1

    # lista ID do pobrania meta
    product_ids = []
    for p in all_products_basic:
        try:
            product_ids.append(int(p["id"]))
        except Exception:
            pass

    # =====================================================================
    # 2) Pobieranie META (nazwa, SKU, EAN…) w paczkach po 200
    # =====================================================================
    meta = {}

    def chunk_list(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    for pack in chunk_list(product_ids, 200):
        try:
            parameters = {
                    "inventory_id": int(inventory_id),
                    "products": pack}

            data = bl_request("getInventoryProductsData", parameters, baselinker_api_url, bl_token)

            for k, v in (data.get("products") or {}).items():
                try:
                    pid = int(k)
                except Exception:
                    pid = v.get("id")
                if pid:
                    meta[pid] = v

        except Exception as e:
            print(f"[ERROR] Meta pack error: {pack} → {e}")

    # =====================================================================
    # 3) Filtracja — usuwamy bundlery i produkty rodziców wariantów
    # =====================================================================
    rows = []

    for p in all_products_basic:
        try:
            pid = int(p["id"])
        except Exception:
            continue

        m = meta.get(pid, {})

        # FILTR
        is_bundle = m.get("is_bundle", False)
        parent_id = m.get("parent_id") or 0
        variants = m.get("variants") or []

        if is_bundle:
            continue
        if parent_id == 0 and isinstance(variants, list) and len(variants) > 0:
            continue

        # produkt OK → dodajemy
        rows.append({
            "id": pid,
            "ean": p.get("ean") or "",
            "sku": p.get("sku") or "",
            "name": p.get("name") or ""
        })

    # =====================================================================
    # 4) DataFrame + CSV
    # =====================================================================
    df_produkty = pd.DataFrame(rows, columns=["id", "ean", "sku", "name"])

    if save_csv and len(rows) > 0:
        df_produkty.to_csv(output_path, sep=";", index=False, encoding="utf-8")
        print(f"Zakończono pobieranie. Plik {output_path}")

    return df_produkty


if __name__ == "__main__":
    BASELINKER_API_URL = "https://api.baselinker.com/connector.php"
    BL_TOKEN = "5004221-5013195-GBT19RBZAAJG4AKIFRAG9547IT7X7QV6L4K47L40RC5TDX64NZ852KP2VYL4E65B"
    INVENTORY_ID = 35072

    try:
        df_products = get_produkty(BASELINKER_API_URL, BL_TOKEN, INVENTORY_ID, save_csv = True, csv_dir = Path(__file__).parent)
    except Exception as e:
        print("[ERROR MAIN]", e)
