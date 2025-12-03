# Estymowanie strat poniesionych przez braki dostępności produktów na podstawie danych z Baselinker


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

---

## Copyright

Copyright (c) 2025 Karol Bartnicki
All rights reserved.
