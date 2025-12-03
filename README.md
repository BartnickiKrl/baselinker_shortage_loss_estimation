Projekt aktualnie działający tylko z BASELINKEREM



Plik get_all.py to menedżer pobierania za pomocą zapytań api inforamcji o produktach i zamówieniach zapisywanych przez Baselinkera
- Użytkownik podaje token oraz inventory ID
- Uzytkownik może wybrać pliki do pobrania (za pierwszym razem najlepiej wybrac opcje "123", czyli wszystkie pliki)
    1. product_list,csv   [id;ean;sku;name]
              - lista wszystkich produktów
       
    3. stany,csv    [data;id;sku;ean;stan_przed;stan_po]
              - lista wszystkich znalezionych zmian stanow magazynowych dla produktow z pliku product_list (zapewnionego przez uzytkownika lub pobranego etap wczesniej)
              - pobierana jest stale dla ostatnich 6 miesięcy (limit api Baselinkera)
              - stany:
                       "aktywna" - oferta jest aktywna, prdukt na stanie
                       "zakończona" - oferta jest zakończona, prduktu brak
                       "rozkręcanie" - pierwsze 24h po dodaniu na stan produktów gdy poprzedni stan był "zakończona"
       
    5. rotacje   [product_id;variant_id;rotation_qty;unit_price_brutto;purchase_cost;date;weekday;hour]
              - lista wszystkich zamówień produktów przez ostatnie (ilość dni wybrana przez użytkownika)

- Użytkownik wybiera tempo zapytań na minutę ( przy ponad 100/min baselinker banuje możliwość zapytań na koncie na kilka/kilkanaście minut ( zaleca sięusatwienie limitu na 70 jeżeli mamy jeszcze jakieś inne zapytania działające w tle )

- moduł jest wyposażony w licznik zapytań na minutę oraz przy pobieraniu stanów estymowany czas pozostały do ukończenia ze względu na czasochłonność akurat tej operacji



PLik Data_Analysis.py sam wyszuka potrzebne pliki oraz przeprowadzi analizę na ich podstawie
- Użytkownik wybiera dostępny zakres dat na których bedzie opierała się analiza
    . Jest możliwość wybrania innej daty dla rotacji oraz stanów. Przy wybraniu większego zakresu dla rotacji wyniki analizy stają się dużo bardziej dokładna
- Analiza zwraca dwa główne pliki:
    1. analysis_for_stany_"wybrana data poczatkowa dla stanow"_rotacje_"wybrana data poczatkowa dla stanow"_at_"czas wykonanania analizy w fomracie HHMMSS".csv
       :zawiera szczegółowe wyniki analizy w 182 kolumnach
       
       WYKORZYSTUJĄC DANE ROTACJI oraz wybrany zakres dat dla nich TWORZY KOLUMNY:
       - d1h1 - Zwiera dla każdego porduktu srednia rotacje [ilość rotacji, suma przychodu, suma koszów] (srednia to suma/ilosc pojawien sie danego dnia i gofziny w zakresie dat)
              - z podziałem na każdą godzine każdego dnia tygodnia ( d1_h3 - dzien 1, godzina 3:00 - wszystkie poniedziałki o 3 rano w zakresie dat dla rotacji )
       - d1_suma - dla każdego dnia suma wszystkich 24h ( d1_suma - suma kolumn d1_h0, d1_h1 ... d1_h23 )
       - suma_dla_okresu - suma wszystkich dni / łączne statystyi dla każdego produktu przez cały okres dat dla rotacji
         
       WYKORZYSTUJĄC DANE STANOW oraz wybrany zakres dat dla nich TWORZY KOLUMNY:
       - czasy_stanow - nazwy stanow w kotrych znalazl sie produkt w zakresie dat wybranych dla stanow razem z czasem trwania w liscie (wszystkie godiny z listy sumuja sie do ilosci godzin w przedziale datowym)
       - suma_strat - kolumna szukająca straconych przychodów bazując na paternie sprzedaży
           . dla całego czasu w którym produkt nie był aktywny szukamy srednich wynikow sprzedazy/rotacji w tych konkretnych godzinach i dniach
           . tak znalezione wynik sumujemy przy czym jeżeli produkt był wtedy w trybie "rozkręcanie" bieżemy tylko 50% kwoty, dla "zakończona" 100%

       DRUGI WIERSZ ZAWIERA SUMĘ KAŻDEJ LICZBOWEJ KOLUMNY

    3. stats_stany_"wybrana data poczatkowa dla stanow"_rotacje_"wybrana data poczatkowa dla stanow".csv
       :zawiera podsumowane wyniki analizy w 14 kolumnach w łatwiejszej do interpretacji fromie

       DLA KAŻDEGO PRODUKTU
       - ilosc_zakonczen - ilość oddzielnych stanów "zakończona" 
       - ilosc_aktywowan - ilość oddzielnych stanów "aktywna"
       - srednio_zakonczony - średni czas przez którym oferta była w stanie "zakończona"
       - srednio_aktywny - średni czas przez którym oferta była w stanie "aktywna"
       ROZDZIELONA NA 3 KOLUMNY - kolumna suma_dla_okresu z pliku 1.
       - suma_rotacji
       - suma_przychodow
       - suma_kosztow
       ROZDZIELONA NA 3 KOLUMNY - kolumna suma_strat z pliku 1.
       - stracone_rotacje
       - stracony_przychod
       - stracony_koszt
    
       DRUGI WIERSZ ZAWIERA SUMĘ KAŻDEJ LICZBOWEJ KOLUMNY

  - Zapisywane są również dodatkowe pliki:
    1. products_cut.csv - zawiera produkty bez danych o rotacji, ponieważ nie można było użyć ich w analizie
    2. rotacje_cut.csv - zawiera listę produktow, dla których znaleziono rotacje jednak nie ma dla nich danych o stanach



       



 
Copyright (c) 2025 Karol Bartnicki
All rights reserved.
