from .common_imports import *

REQUEST_TIMESTAMPS = []

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
    REQUEST_TIMESTAMPS = []
    while True:
        
        # wyliczamy zapytania/min
        now = time.time()
        REQUEST_TIMESTAMPS[:] = [t for t in REQUEST_TIMESTAMPS if now - t < WINDOW]  # czyścimy stare
        rpm = len(REQUEST_TIMESTAMPS)  # requests per minute
        print(f"\rZapytania: {rpm}/min", end="", flush=True)

        try:
            parameters = {
                    "inventory_id": int(inventory_id),
                    "page": page,
                    "include_variants": True}

            data = bl_request("getInventoryProductsList", parameters, baselinker_api_url, bl_token, pace)
            REQUEST_TIMESTAMPS.append(time.time())
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

            data = bl_request("getInventoryProductsData", parameters, baselinker_api_url, bl_token, pace)
            REQUEST_TIMESTAMPS.append(time.time())

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
        print(f"\nZakończono pobieranie. Plik {output_path.name}")

    return df_produkty


if __name__ == "__main__":
    pass
