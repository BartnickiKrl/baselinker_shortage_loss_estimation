import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

project_dir = Path("downloaded_csv_files")
if not project_dir.exists():
    project_dir = Path("test_csv_files")  # katalog z testowymi plikami
    print("NIE ZNALEZIONO FOLDERU \"downloaded_csv_files\": ANALIZA NA TESTOWYCH PLIKACH")

rotacje_path = next(project_dir.glob("rotacje_*.csv"), None)
stany_path = next(project_dir.glob("stany_*.csv"), None)
product_path = next(project_dir.glob("product_list.csv"), None)

#============================================================================================================
# Zgranie danych z rotacje.csv i stany.csv i product_list do DataFrame
#============================================================================================================
try:
    if not rotacje_path.exists():
        raise FileNotFoundError(f"ERROR: Nie znaleziono pliku z rotacjami o nazwie zwierajacej rotacje.csv: {rotacje_path.resolve()}")
    if not stany_path.exists():
        raise FileNotFoundError(f"ERROR: Nie znaleziono pliku ze stanami o nazwie zwierajacej stany.csv: {stany_path.resolve()}")
    if not product_path.exists():
        raise FileNotFoundError(f"ERROR: Nie znaleziono pliku ze stanami o nazwie product_list.csv: {stany_path.resolve()}")
    
    df_product = pd.read_csv(product_path, sep=";")
    df_rotacje = pd.read_csv(rotacje_path, sep=";")
    df_stany   = pd.read_csv(stany_path, sep=";")


except FileNotFoundError as e:
    print(f"[BŁĄD] {e}")
    raise SystemExit(1)

# KONWERSJA KOLUMN NA DATETIME
df_rotacje["date"] = pd.to_datetime(df_rotacje["date"], format="%Y-%m-%d", errors="coerce", utc=True)
df_stany["data"] = pd.to_datetime(df_stany["data"], utc=True)

# WYZNACZENIE DOSTĘPNYCH ZAKRESÓW
min_date_rotacje = df_rotacje["date"].min().normalize().tz_convert("UTC")
max_date_rotacje = df_rotacje["date"].max().normalize().tz_convert("UTC")

min_date_stany = df_stany["data"].min().normalize().tz_convert("UTC")
max_date_stany = df_stany["data"].max().normalize().tz_convert("UTC")

# FUNKCJA DO POBRANIA DAT OD UŻYTKOWNIKA
def get_user_date_range(entity_name, min_date, max_date):
    print(f"\nDostępny zakres dla {entity_name}: od {min_date.strftime('%Y-%m-%d')} do {max_date.strftime('%Y-%m-%d')}")
    try:
        start_str = input(f"Data początkowa {entity_name}: ").strip()
        end_str = input(f"Data końcowa {entity_name}: ").strip()

        start_date = pd.to_datetime(start_str, format="%Y-%m-%d", errors="raise").tz_localize("UTC")
        end_date = pd.to_datetime(end_str, format="%Y-%m-%d", errors="raise").tz_localize("UTC")

        if end_date < start_date:
            raise ValueError("Data końcowa nie może być wcześniejsza niż początkowa.")
        if start_date < min_date:
            raise ValueError("Data początkowa wychodzi poza dostępny zakres.")
        if end_date > max_date:
            raise ValueError("Data końcowa wychodzi poza dostępny zakres.")

        return start_date, end_date

    except Exception as e:
        print(f"\n{e}")
        print("Upewnij się, że wprowadzasz daty w formacie: RRRR-MM-DD (np. 2025-10-05)")
        raise SystemExit(1)

# POBRANIE DAT DLA ROTACJI I STANÓW
start_rotacje, end_rotacje = get_user_date_range("rotacji", min_date_rotacje, max_date_rotacje)
start_stany, end_stany = get_user_date_range("stanów", min_date_stany, max_date_stany)

dates_rotacje = pd.date_range(start=start_rotacje, end=end_rotacje)

# WYBRANIE INTERESUJĄCEGO PRZEDZIAŁU CZASOWEGO
mask_rotacje = (df_rotacje["date"] >= start_rotacje) & (df_rotacje["date"] <= end_rotacje)
mask_stany = (df_stany["data"] >= start_stany) & (df_stany["data"] <= end_stany)
#============================================================================================================
# NORMALIZACJA I FILTROWANIE WSPÓLNYCH ID
#============================================================================================================

# Zamieniamy product_id na variant_id tam, gdzie variant_id **nie jest NaN**
df_rotacje["product_id"] = df_rotacje.apply(
    lambda row: row["variant_id"] if pd.notna(row["variant_id"]) and str(row["variant_id"]) != "0.0" else row["product_id"],
    axis=1
)

# porownanie ID jako str i usunięcie .0
df_product["id"] = df_product["id"].astype(str).str.replace(".0", "", regex=False)
df_rotacje["product_id"] = df_rotacje["product_id"].astype(str).str.replace(".0", "", regex=False)
df_stany["id"] = df_stany["id"].astype(str).str.replace(".0", "", regex=False)

ids_prod     = set(df_product["id"])
ids_rotacje  = set(df_rotacje["product_id"])
ids_stany    = set(df_stany["id"])

# ID obecne wszędzie
common_ids = ids_prod & ids_rotacje & ids_stany
#pliki z wycietymi ID
df_product_cut = df_product[~df_product["id"].isin(common_ids)]
df_rotacje_cut = df_rotacje[~df_rotacje["product_id"].isin(common_ids)]
if len(df_product_cut):
    df_product_cut.to_csv("products_cut.csv", index=False)
    print(f"\nProdukty bez danych o rotacji: {len(df_product_cut)} na {len(df_product)+len(df_product_cut)} produktow. Lista w pliku products_cut.csv")
if len(df_rotacje_cut):
    df_rotacje_cut.to_csv("rotacje_cut.csv", index=False)
    print(f"Dla: {len(df_rotacje_cut)} produktow znaleziono rotacje jednak nie ma dla nich danych o stanach. Lista w pliku rotacje_cut.csv")

# filtrujemy wszystko do wspolnych ID
df_product = df_product[df_product["id"].isin(common_ids)]
df_rotacje = df_rotacje[df_rotacje["product_id"].isin(common_ids)]
df_stany   = df_stany[df_stany["id"].isin(common_ids)]

#============================================================================================================
#                  BADANIE ŁĄCZNYCH ROTACJI|PRZYCHODÓW|KOSZTÓW
#============================================================================================================
print("\nRozpoczynam analize rotacji")
slownik_godziny = {}

days = ["d1", "d2", "d3", "d4", "d5", "d6", "d7"]
hours = [f"h{i}" for i in range(24)]

dates_by_weekday = {i: dates_rotacje[dates_rotacje.weekday == i].date for i in range(7)}

slownik_godziny = {}
for d in days:
    weekday_index = int(d[1]) - 1
    day_dates = dates_by_weekday[weekday_index]  # tylko raz
    for h in hours:
        slownik_godziny[f"{d}_{h}"] = [len(day_dates), list(day_dates)]
# mamy słownik w formacie: {"d1_h15": [4, ["10.11.2025","03.11.2025"]]}


df_grouped = df_rotacje.groupby(["product_id", "date", "hour"]).agg(
    suma_przychodu=pd.NamedAgg(column="unit_price_brutto", aggfunc=lambda x: (x * df_rotacje.loc[x.index, "rotation_qty"]).sum()),
    suma_kosztu=pd.NamedAgg(column="purchase_cost", aggfunc=lambda x: (x * df_rotacje.loc[x.index, "rotation_qty"]).sum()),
    suma_rotacji=pd.NamedAgg(column="rotation_qty", aggfunc="sum")
).reset_index()

# Tworzymy słownik do szybkiego wyszukiwania wyników
grouped_dict = {
    (row.product_id, row.date.date(), row.hour): (row.suma_przychodu, row.suma_kosztu, row.suma_rotacji)
    for row in df_grouped.itertuples() }

produkty = df_product["id"].unique()

df_wyniki = pd.DataFrame({"product_id": df_product["id"], "ean": df_product["ean"], "sku": df_product["sku"], "name": df_product["name"]})
wyniki_dict = {produkt: {} for produkt in produkty}
suma_dict = {produkt: {} for produkt in produkty} 

count = 0
for kolumna, (ile_wystapien, lista_dat) in slownik_godziny.items():
    #print(f"Analiza: {kolumna} ({ile_wystapien} wystapien, daty={lista_dat})")
    count += 1
    print(f"\rUkonczono: {(count/168)*100:.0f}%", end="", flush=True)

    if ile_wystapien == 0:
        continue 

    for produkt in produkty:
        suma_przychodu = 0.0
        suma_kosztu = 0.0
        suma_rotacji = 0.0
        
 
        hour_index = int(kolumna.split("_h")[1])
        
        for data_dt in lista_dat:
            key = (produkt, data_dt, hour_index)
            if key in grouped_dict:
                p, k, r = grouped_dict[key]
                suma_przychodu += p
                suma_kosztu += k
                suma_rotacji += r

        wyniki_dict[produkt][kolumna] = [round(suma_rotacji/ile_wystapien, 2), round(suma_przychodu/ile_wystapien, 2), round(suma_kosztu/ile_wystapien, 2)]

        day_key = f"d{int(kolumna[1])}_suma"
        if day_key not in suma_dict[produkt]:
            suma_dict[produkt][day_key] = [0.0, 0.0, 0.0]  # [rotacje, przychod, koszt]

        suma_dict[produkt][day_key][0] += suma_rotacji
        suma_dict[produkt][day_key][1] += suma_przychodu
        suma_dict[produkt][day_key][2] += suma_kosztu


#Wynikowy DataFrame dodajemy produkty i d1_h1
for kolumna in slownik_godziny.keys():
    df_wyniki[kolumna] = [wyniki_dict[produkt].get(kolumna, [0, 0, 0]) for produkt in produkty]
#dodajemy sumy dla każdego dnia
for kol in suma_dict[produkt].keys():
    df_wyniki[kol] = [suma_dict[p][kol] for p in produkty]

cols_sumy = [col for col in df_wyniki.columns if col.endswith("_suma")]
df_wyniki["suma_dla_okresu"] = df_wyniki[cols_sumy].apply(
    lambda row: [round(sum([x[i] for x in row if isinstance(x, (list, tuple)) and len(x) == 3]), 2)
                 for i in range(3)],
    axis=1
)

print("\nZakonczono analize rotacji")
#============================================================================================================
#        BADANIE DŁUGOŚCI TRAWANIA STANÓW + SYMULACJA UTRACONEGO ZAROBKU (optymalizacja)
#============================================================================================================
print("\nRozpoczynam analize stanow, to moze chwile potrwac")

all_hours_cache = pd.date_range(start=start_stany, end=end_stany, freq="h", tz="UTC")
hour_str_cache = {h: f"d{h.weekday()+1}_h{h.hour}" for h in all_hours_cache}

mask_stany = (df_stany["data"] >= start_stany) & (df_stany["data"] <= end_stany)
df_puste = df_stany[df_stany["stan_przed"].isna() | (df_stany["stan_przed"] == "")]
df_masked = df_stany[mask_stany & df_stany["stan_przed"].notna() & (df_stany["stan_przed"] != "") & df_stany["stan_po"].notna() & (df_stany["stan_po"] != "")]
df_final = pd.concat([df_puste, df_masked]).sort_values(["id", "data"])

godziny_dict = {}
lost_total_dict = {}

count = 0
for produkt, dane_produktu in df_final.groupby("id"):
    count += 1
    print(f"\rUkonczono: {(count/len(df_final.groupby('id')))*100:.0f}%", end="", flush=True)

    dane_produktu = dane_produktu.sort_values("data")
    lista_godziny = []
    lost_total = np.zeros(3)

    lista = [[row["data"], row["stan_po"]] for _, row in dane_produktu.iterrows()]
    for i in range(len(lista)):
        curr_date = lista[i][0]
        stan = lista[i][1]

        prev_date = start_stany if i == 0 else lista[i - 1][0]
        next_date = end_stany if i == len(lista) - 1 else lista[i + 1][0]

        diff_h = (next_date - curr_date).total_seconds() / 3600

        # wyciągamy godziny z precomputed cache
        all_hours = [h for h in all_hours_cache if curr_date <= h < next_date]
        godziny_dni = [hour_str_cache[h] for h in all_hours]

        stan_lower = str(stan).lower()
        utrata_ratio = 1.0 if "zakończona" in stan_lower else 0.5 if "rozkręcanie" in stan_lower else 0.0

        lost_values = np.zeros(3)
        df_prod = df_wyniki[df_wyniki["product_id"] == produkt]
        if df_prod.empty:
            continue
        for gh in godziny_dni:
            if gh in df_prod.columns:
                val = df_prod[gh].values[0]
                if isinstance(val, (list, tuple)) and len(val) == 3:
                    lost_values += np.array(val) * utrata_ratio

        lost_total += lost_values
        lista_godziny.append([round(diff_h, 2), stan])

    godziny_dict[str(produkt)] = lista_godziny
    lost_total_dict[str(produkt)] = [round(float(v), 2) for v in lost_total]

df_wyniki["czasy_stanow"] = df_wyniki["product_id"].apply(lambda pid: godziny_dict.get(str(pid), []))
df_wyniki["suma_strat"] = df_wyniki["product_id"].apply(lambda pid: lost_total_dict.get(str(pid), []))

print("\nZakonczono analize stanow")
#============================================================================================================
#                                       ZAOKRAGLANIE WYNIKOW
#============================================================================================================
def fix_floats(val):
    if isinstance(val, list) and len(val) == 3:
        return [float(f"{x:.2f}") for x in val if isinstance(x, (int, float))]
    elif isinstance(val, (int, float)):
        return float(f"{val:.2f}")
    else:
        return val
for col in df_wyniki.columns:
    df_wyniki[col] = df_wyniki[col].apply(fix_floats)
#============================================================================================================
#                           TWORZENIE UPROSZCZONEGO PLIKU ZE STATYSTYKAMI
#============================================================================================================
print("\nPrzygotowywanie pliku z uproszczonymi statystykami")

df_stats = pd.DataFrame({"product_id": df_product["id"], "ean": df_product["ean"], "sku": df_product["sku"], "name": df_product["name"]})

# srednie czasy i ilosci zakonczen
actives_dict = {}
ends_dict = {}
avg_active_time_dict = {}
avg_unactive_time_dict = {}

for pid, values in godziny_dict.items():
    count_unactive = 0
    sum_unactive = 0
    count_active = 0
    sum_active = 0

    for i in range(len(values)):
        if values[i][1] == "zakończona": 
            count_unactive += 1
            sum_unactive += float(values[i][0])
        elif values[i][1] == "aktywna": 
            count_active += 1
            sum_active += float(values[i][0])

    actives_dict[pid] = count_active
    ends_dict[pid] = count_unactive
    avg_active_time_dict[pid] = sum_active/count_active if count_active else 0
    avg_unactive_time_dict[pid] = sum_unactive/count_unactive if count_unactive else 0

df_stats["ilosc_zakonczen"] = df_stats["product_id"].apply(lambda pid: ends_dict.get(str(pid), 0))
df_stats["ilosc_aktywowan"] = df_stats["product_id"].apply(lambda pid: actives_dict.get(str(pid), 0))
df_stats["srednio_zakonczony"] = df_stats["product_id"].apply(lambda pid: avg_unactive_time_dict.get(str(pid), 0))
df_stats["srednio_aktywny"] = df_stats["product_id"].apply(lambda pid: avg_active_time_dict.get(str(pid), 0))

# zyski bez listy rozdzielone
df_stats["suma_rotacji"] = df_wyniki[cols_sumy].apply(
    lambda row: float(round(sum([x[0] for x in row if isinstance(x, (list, tuple)) and len(x) == 3]), 2)), axis=1)
df_stats["suma_przychodow"] = df_wyniki[cols_sumy].apply(
    lambda row: float(round(sum([x[1] for x in row if isinstance(x, (list, tuple)) and len(x) == 3]), 2)), axis=1)
df_stats["suma_kosztow"] = df_wyniki[cols_sumy].apply(
    lambda row: float(round(sum([x[2] for x in row if isinstance(x, (list, tuple)) and len(x) == 3]), 2)), axis=1)

# straty bez listy rozdzielone
lost_rotation = {}
lost_revenue = {}
lost_cost = {}

for pid, values in lost_total_dict.items():
    lost_rotation[pid] = values[0] if len(values) > 0 else 0
    lost_revenue[pid] = values[1] if len(values) > 1 else 0
    lost_cost[pid] = values[2] if len(values) > 2 else 0

df_stats["stracone_rotacje"] = df_stats["product_id"].apply(lambda pid: lost_rotation.get(str(pid), 0))
df_stats["stracony_przychod"] = df_stats["product_id"].apply(lambda pid: lost_revenue.get(str(pid), 0))
df_stats["stracony_koszt"] = df_stats["product_id"].apply(lambda pid: lost_cost.get(str(pid), 0))

#============================================================================================================
#                                   DODAWANIE WIERSZA Z SUMAMI
#============================================================================================================

#====================================== PLIK UPROSZCZONY ====================================================
num_cols = df_stats.select_dtypes(include=['number']).columns
suma_row1 = {}
for col in num_cols:
    df_stats[col] = df_stats[col].round(2)
    suma_row1[col] = round(sum(x for x in df_stats[col] if isinstance(x, (int, float)) and (pd.notna(x))), 2)


suma_row1["product_id"] = "SUMA"
suma_row1["ean"] = "DLA"
suma_row1["sku"] = "WSZYSTKICH"
suma_row1["name"] = "KOLUMN"

suma_row1_df = pd.DataFrame([suma_row1])
suma_row1_df = suma_row1_df.reindex(columns=df_stats.columns)
df_stats = pd.concat([suma_row1_df, df_stats], ignore_index=True)

#====================================== PLIK GŁÓWNY ========================================================
list_cols = [col for col in df_wyniki.columns if df_wyniki[col].apply(lambda x: isinstance(x, list)).any()]

suma_row = {}
for col in list_cols:
    # Bierzemy tylko te elementy, które są listami 3-elementowymi (rotacja, przychód, koszt)
    lists = [x for x in df_wyniki[col] if isinstance(x, (list, tuple)) and len(x) == 3]
    if lists:
        suma_row[col] = [round(sum(x[i] for x in lists if isinstance(x[i], (int, float))), 2) for i in range(3)]
    else:
        suma_row[col] = ""

suma_row["product_id"] = "SUMA"
suma_row["ean"] = "DLA"
suma_row["sku"] = "WSZYSTKICH"
suma_row["name"] = "KOLUMN"

suma_row_df = pd.DataFrame([suma_row])
suma_row_df = suma_row_df.reindex(columns=df_wyniki.columns)
df_wyniki = pd.concat([suma_row_df, df_wyniki], ignore_index=True)

#============================================================================================================
#                           ZAPISANIE PLIKU WYNIKOWEGO
#============================================================================================================
now_str = datetime.now().strftime("%H%M%S")
start_stany_str = start_stany.strftime("%Y-%m-%d")
start_rotacje_str = start_rotacje.strftime("%Y-%m-%d")

#====================================== PLIK GŁÓWNY ========================================================
output_analysis_file = project_dir / f"analysis_for_stany_{start_stany_str}_rotacje_{start_rotacje_str}_at_{now_str}.csv"
df_wyniki.to_csv(output_analysis_file, sep=";", index=False, encoding="utf-8")
print(f"\nZapisano wynik: analysis_for_stany_{start_stany_str}_rotacje_{start_rotacje_str}_at_{now_str}.csv")

#====================================== PLIK UPROSZCZONY ====================================================
output_stats_file = project_dir / f"stats_{now_str}.csv"
df_stats.to_csv(output_stats_file, sep=";", index=False, encoding="utf-8")
print(f"Zapisano uproszczony wynik: stats_stany_{start_stany_str}_rotacje_{start_rotacje_str}.csv")