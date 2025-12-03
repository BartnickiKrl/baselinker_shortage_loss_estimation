import requests
import json
import time
from datetime import datetime, timedelta
try:
    from .GetExceptions import Bl_token_ban
except ImportError as e:
    print(f"ERROR: Blad importu modulu GetExceptions, sprawdz czy plik jest w odpowiednim miejscu {e}")

# Zarządzanie czasem – proponowane 70 zapytań/min
MAX_REQUESTS = 70
WINDOW = 60
LAST_REQUEST = 0
MIN_INTERVAL = 60 / MAX_REQUESTS    # np 0.857 sekundy

def bl_request(method, method_params, api_url, token, pace, max_ban_retries=2):
    """
    Zapytanie do BaseLinkera
    - opóźnienie 0.86s - 70/min
    - obsługa blokady tokenu
    """
    global LAST_REQUEST, MAX_REQUESTS, MIN_INTERVAL
    MAX_REQUESTS = pace
    MIN_INTERVAL = 60 / pace

    now = time.time()
    elapsed = now - LAST_REQUEST
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    LAST_REQUEST = time.time()

    ban_attempt = 0

    while ban_attempt < max_ban_retries:
        try:
            headers = {"X-BLToken": token}
            api_params = {"method": method, "parameters": json.dumps(method_params)}

            response = requests.post(api_url, data=api_params, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data["status"] != "SUCCESS":
                raise Bl_token_ban(data)  # korzystamy z istniejącej klasy
            
            return data

        except Bl_token_ban as ban:
            if ban.wait_till == -1:
                print(f"\nERROR: niepowodzenie ze strony API: {ban.why}")
                raise RuntimeError
            else:
                # czas do końca blokady + 30s bufora
                delay = (ban.wait_till - datetime.now() + timedelta(seconds=30)).total_seconds()
                if delay > 0:
                    print(f"\nToken zablokowany na {delay:.0f} sekund. Czekam i ponawiam próbę.")
                    start_time = time.time()
                    while True:
                        remaining = delay - (time.time() - start_time)
                        if remaining <= 0:
                            break
                        print(f"\rDo końca bana pozostało: {int(remaining)}s", end="", flush=True)
                        time.sleep(10)
                print("\nToken odblokowany. Ponawiam próbę.")
                ban_attempt += 1

    # jeśli ban nie ustąpił po max_ban_retries
    print("\nERROR: przeczekanie bana nie przyniosło rezultatów, spróbuj ponownie później")
    raise RuntimeError