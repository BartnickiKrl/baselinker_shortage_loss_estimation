from pathlib import Path
import time
import pandas as pd
from get_all_modules import *


LAST_CALL_TIME = 0

def check_rate_limit():
    '''
    Sprawdza czy inna funkcja nie działała w tej samej minucie,
    aby uniknąć nawarstwianania się requestów różnych funkcji 
    co nie może być kontrolowane wewnątrz.
    '''
    global LAST_CALL_TIME

    now = time.time()
    elapsed = now - LAST_CALL_TIME

    if elapsed < 60:
        wait = int(60 - elapsed + 5)
        time.sleep(wait)

    LAST_CALL_TIME = time.time()


def main():

    # ==============================================================
    BASELINKER_API_URL = "https://api.baselinker.com/connector.php"
    BL_TOKEN = input("Token Baselinker: ")
    INVENTORY_ID = input("Inventory ID: ")
    # ==============================================================

    print("\nKtóre pliki chcesz pobrać:")
    print("1 - Produkty")
    print("2 - Stany")
    print("3 - Rotacje")
    choice = input("Twój wybór (np. 13 / 123): ").strip()

    try:
        pace = int(input("Podaj maksymalne tempo zapytań na minute (<100): "))
        if not isinstance(pace, int) or pace >= 100:
            raise Exception("\nPodane tempo wynosi ponad 100 co będzie skutkować banem")
    except Exception as e:
        print("ERROR: ", e)

    csv_dir = Path("downloaded_csv_files")
    csv_dir.mkdir(parents=True, exist_ok=True)
    products_csv = csv_dir / "products_list.csv"
    df_products = pd.read_csv(products_csv, sep=";") if products_csv.exists() else None


    if "1" in choice:
        check_rate_limit()
        print("\nRozpoczynam pobieranie listy produktow")
        try:
            df_products = get_produkty(BASELINKER_API_URL, BL_TOKEN, INVENTORY_ID,
                                       save_csv=True, csv_dir=csv_dir, pace=pace)
        except Exception as e:
            print("ERROR: Błąd przy pobieraniu produktów:", e)

    if "2" in choice:
        if df_products is None and input(
            f"Nie znaleziono istniejącego pliku ({products_csv}). Pobrac go? [T/N]: "
        ).strip().lower() == "t":

            check_rate_limit()
            print("\nRozpoczynam pobieranie listy produktow")
            try:
                df_products = get_produkty(BASELINKER_API_URL, BL_TOKEN, INVENTORY_ID,
                                           save_csv=True, csv_dir=csv_dir, pace=pace)
            except Exception as e:
                print("ERROR: Błąd przy pobieraniu produktów:", e)
                df_products = None

        if df_products is not None:
            check_rate_limit()
            print("\nRozpoczynam pobieranie danych o stanach - to moze chwile potrwac\n")
            try:
                get_stany(df_products, get_date_from_last_6_months(),
                          BASELINKER_API_URL, BL_TOKEN, save_csv=True, csv_dir=csv_dir, pace=pace)
            except Exception as e:
                print("ERROR: Błąd przy pobieraniu stanów:", e)

    if "3" in choice:

        days_input = input("\nPodaj liczbę dni wstecz do pobrania rotacji: ").strip()
        if not days_input.isdigit():
            print("ERROR: Niepoprawna liczba dni.")
            return -13
        days = int(days_input)

        check_rate_limit()
        print("Rozpoczynam pobieranie danych o rotacjach\n")
        try:
            get_rotacje(BASELINKER_API_URL, BL_TOKEN, INVENTORY_ID,
                        days=days, save_csv=True, csv_dir=csv_dir, pace=pace)
        except Exception as e:
            print("ERROR: Błąd przy pobieraniu rotacji:", e)


if __name__ == "__main__":
    main()
