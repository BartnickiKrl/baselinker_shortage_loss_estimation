import time
try:
    from BSLE_files import *
except ImportError as e:
    print(f"ERROR: Blad importu modulu BSLE_files, sprawdz czy folder jest w odpowiednim miejscu {e}")

def main():
    print("\n===========================================")
    print(" BSLE - Baselinker Shortage Loss Estimatior ")
    print("===========================================")
    
    while True:
        print("\nWybierz co chcesz zrobic: ")
        print("1. Pobrac brakujace pliki i przejść do Analizy.")
        print("2. Mam wszystko. Analiza na obecnych plikach.")
        print("3. Exit.")

        choose = input("\nWybor: ").strip()

        if "1" in choose:
            print("\nMENEDŻER POBIERANIA")
            get_all()
            print("\nANALIZA DANYCH")
            data_analysis()

        elif "2" in choose:
            print("\nANALIZA DANYCH")
            data_analysis()

        elif "3" in choose:
            raise SystemExit(3)

        else:
            print("Bledny wybor. Sprobuj ponownie lub wybierz 3 aby zakonczyc")
            time.sleep(2)

if __name__ == "__main__":
    main()