# BSLE - BASELINKER SHORTAGE LOSS ESTIMATOR

Choose language / Wybierz język:
* [English](#english)
* [Polski](#polski)


## Polski
Installacja programu jest bardzo prosta – należy pobrać **folder `BSLE_files`** oraz plik wykonawczy **`BSLE.py`**.  
Następnie, po uruchomieniu `BSLE.py`, program w intuicyjny sposób przeprowadzi nas przez Baselinkera do ostatecznych wyników.

## Działanie programu:

Program korzysta z dwóch rozbudowanych modułów:

## get_all.py – menedżer pobierania danych


Plik `get_all.py` to menedżer pobierania za pomocą zapytań API informacji o produktach i zamówieniach zapisywanych przez Baselinkera.

- Użytkownik podaje:
  - token
  - inventory ID
- Użytkownik może wybrać pliki do pobrania  
  *(za pierwszym razem najlepiej wybrać opcję "123", czyli wszystkie pliki)*

### Dostępne pliki:

1. **product_list.csv** `[id;ean;sku;name]`  
   - lista wszystkich produktów

2. **stany.csv** `[data;id;sku;ean;stan_przed;stan_po]`  
   - lista wszystkich znalezionych zmian stanów magazynowych dla produktów z pliku `product_list` (zapewnionego przez użytkownika lub pobranego wcześniej w tym wywołaniu programu)  
   - pobierana stale dla ostatnich 6 miesięcy (limit API Baselinkera)  
   - możliwe stany:  
     - `"aktywna"` – oferta jest aktywna, produkt na stanie  
     - `"zakończona"` – oferta jest zakończona, produktu brak  
     - `"rozkręcanie"` – pierwsze 24h po dodaniu na stan produktów, gdy poprzedni stan był `"zakończona"`

3. **rotacje.csv** `[product_id;variant_id;rotation_qty;unit_price_brutto;purchase_cost;date;weekday;hour]`  
   - lista wszystkich zamówień produktów przez ostatnie dni (ilość dni wybrana przez użytkownika)

### Ustawienia zapytań:

- Użytkownik wybiera tempo zapytań na minutę  
- Przy ponad 100/min Baselinker banuje możliwość zapytań na koncie na kilka/kilkanaście minut  
- Zaleca się ustawienie limitu na 70, jeśli mamy inne zapytania działające w tle

### Dodatkowe funkcjonalności:

- moduł wyposażony w licznik zapytań na minutę  
- przy pobieraniu stanów estymowany czas pozostały do ukończenia ze względu na czasochłonność operacji  

---

## Data_Analysis.py – analiza danych

Plik `Data_Analysis.py` sam wyszuka potrzebne pliki oraz przeprowadzi analizę na ich podstawie.

- Użytkownik wybiera dostępny zakres dat, na których będzie opierała się analiza  
- Możliwość wybrania innej daty dla rotacji oraz stanów  
- Przy wybraniu większego zakresu dla rotacji wyniki analizy stają się dużo bardziej dokładne

### Wyniki analizy

#### 1. Szczegółowy raport  
`analysis_for_stany_"data początkowa dla stanów"_rotacje_"data początkowa dla stanów"_at_"czas wykonanania analizy w formacie HHMMSS".csv`  
- zawiera szczegółowe wyniki analizy w 182 kolumnach  

##### Dane rotacji tworzą kolumny:

- `d1h1` – średnia rotacja dla każdego produktu `[ilość rotacji, suma przychodu, suma kosztów]`  
  - średnia = suma / ilość pojawień się danego dnia i godziny w zakresie dat  
  - z podziałem na każdą godzinę każdego dnia tygodnia (np. `d1_h3` – dzień 1, godzina 3:00 – wszystkie poniedziałki o 3 rano w zakresie dat dla rotacji)
- `d1_suma` – suma wszystkich 24h w danym dniu (`d1_suma = d1_h0 + d1_h1 + … + d1_h23`)  
- `suma_dla_okresu` – suma wszystkich dni / łączne statystyki dla każdego produktu przez cały okres dat dla rotacji  

##### Dane stanów tworzą kolumny:

- `czasy_stanow` – nazwy stanów, w których znalazł się produkt w wybranym zakresie dat, razem z czasem trwania w liście (wszystkie godziny z listy sumują się do ilości godzin w przedziale datowym)  
- `suma_strat` – kolumna szukająca straconych przychodów bazując na paternie sprzedaży:  
  - dla całego czasu, w którym produkt nie był aktywny, szukamy średnich wyników sprzedaży/rotacji w tych godzinach i dniach  
  - wynik sumujemy, przy czym jeśli produkt był w trybie `"rozkręcanie"` bierzemy tylko 50% kwoty, dla `"zakończona"` 100%  

##### Drugi wiersz - zawiera sumę każdej liczbowej kolumny  

#### 2. Podsumowanie statystyczne  
`stats_stany_"data początkowa dla stanów"_rotacje_"data początkowa dla stanów".csv`  
- zawiera podsumowane wyniki analizy w 14 kolumnach w łatwiejszej do interpretacji formie  

##### Dla każdego produktu:

- `ilosc_zakonczen` – ilość oddzielnych stanów `"zakończona"`  
- `ilosc_aktywowan` – ilość oddzielnych stanów `"aktywna"`  
- `srednio_zakonczony` – średni czas, przez który oferta była w stanie `"zakończona"`  
- `srednio_aktywny` – średni czas, przez który oferta była w stanie `"aktywna"`  

##### Rozdzielone na 3 kolumny (kolumna `suma_dla_okresu` z pliku 1):

- `suma_rotacji`  
- `suma_przychodow`  
- `suma_kosztow`  

##### Rozdzielone na 3 kolumny (kolumna `suma_strat` z pliku 1):

- `stracone_rotacje`  
- `stracony_przychod`  
- `stracony_koszt`  

##### Drugi wiersz zawiera sumę każdej liczbowej kolumny  

---

### Dodatkowe pliki

1. `products_cut.csv` – zawiera produkty bez danych o rotacji, ponieważ nie można było użyć ich w analizie  
2. `rotacje_cut.csv` – zawiera listę produktów, dla których znaleziono rotacje, jednak nie ma dla nich danych o stanach  

________________________________________________________________________________________________________________________________


## English

Installation is straightforward – download the **`BSLE_files` folder** and the **`BSLE.py`** executable file.  
Once launched, `BSLE.py` intuitively guides the user through the Baselinker integration to the final results.

## How it works

The program utilizes two comprehensive modules:

### get_all.py – Data Download Manager

The `get_all.py` file manages data retrieval via API, collecting information on products and orders stored in Baselinker.

- **User input:**
  - API Token
  - Inventory ID
- Users can select specific files to download  
  *(it is recommended to select option "123" – all files – for the first run)*

#### Available files:

1. **product_list.csv** `[id;ean;sku;name]`  
   - A complete list of all products.

2. **stany.csv** `[date;id;sku;ean;stock_before;stock_after]`  
   - A log of all stock level changes for products from `product_list`.  
   - Data is retrieved for the last 6 months (Baselinker API limit).  
   - **Possible statuses:** - `"active"` – offer is live, product in stock.  
     - `"closed"` – offer ended, product out of stock.  
     - `"warm-up"` – the first 24h after restocking a product that was previously `"closed"`.

3. **rotacje.csv** `[product_id;variant_id;rotation_qty;unit_price_brutto;purchase_cost;date;weekday;hour]`  
   - A list of all product orders over a user-defined period (number of days).

#### Request Settings:

- User-defined request rate (requests per minute).  
- Rates exceeding 100/min may result in a temporary API ban on the Baselinker account.  
- A limit of 70 is recommended if other requests are running in the background.

#### Additional Features:

- Real-time request-per-minute counter.  
- Estimated time remaining for stock data downloads due to the time-consuming nature of the operation.

---

### Data_Analysis.py – Data Analysis Engine

`Data_Analysis.py` automatically locates the required files and performs an in-depth analysis.

- User-selectable date range for the analysis.  
- Option to set different date ranges for rotations and stock levels.  
- Larger date ranges for rotation data significantly increase the precision of the results.

### Analysis Results

#### 1. Detailed Report  
`analysis_for_stany_[start_date]_rotacje_[start_date]_at_[HHMMSS].csv`  
- Contains comprehensive analysis results across 182 columns.  

**Rotation columns:**
- `d1h1` – average rotation for each product `[rotation quantity, total revenue, total costs]`.  
  - Average = total / occurrences of a specific day and hour within the date range.  
  - Breakdown by every hour of every weekday (e.g., `d1_h3` – day 1, 3:00 AM).
- `d1_total` – sum of all 24 hours for a given day (`d1_total = d1_h0 + d1_h1 + … + d1_h23`).  
- `period_total` – overall statistics for each product throughout the entire rotation date range.  

**Stock columns:**
- `status_durations` – names of statuses assigned to a product within the selected range, including their duration (total hours equal the selected timeframe).  
- `total_loss` – identifies lost revenue based on sales patterns:  
  - For the entire duration a product was inactive, the system calculates average sales/rotation for those specific hours and days.  
  - Results are aggregated: 100% loss value for `"closed"` status, 50% for `"warm-up"` status.

*The second row contains the sum of every numeric column.*

#### 2. Statistical Summary  
`stats_stany_[start_date]_rotacje_[start_date].csv`  
- A summarized version of the results in 14 columns for easier interpretation.  

**Per product:**
- `closed_count` – number of separate `"closed"` status occurrences.  
- `activated_count` – number of separate `"active"` status occurrences.  
- `avg_closed_duration` – average time an offer remained in the `"closed"` state.  
- `avg_active_duration` – average time an offer remained in the `"active"` state.  

**Rotation Breakdown (from `period_total`):**
- `total_rotation`  
- `total_revenue`  
- `total_cost`  

**Loss Breakdown (from `total_loss`):**
- `lost_rotations`  
- `lost_revenue`  
- `lost_cost`  

*The second row contains the sum of every numeric column.*

---

### Supplementary Files

1. `products_cut.csv` – products excluded from the analysis due to lack of rotation data.  
2. `rotacje_cut.csv` – products with found rotations but missing stock level data.

## Copyright

Copyright (c) 2025 Karol Bartnicki
All rights reserved.
