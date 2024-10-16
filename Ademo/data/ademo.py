import requests
import json
import os
import time
from fake_useragent import UserAgent
import re
import uuid
from colorama import init, Fore, Style
import fade
import keyboard  # Pour écouter les touches du clavier

init(autoreset=True)  # Initialiser Colorama

def search_player_in_dump(dump_dir, search_term):
    # Vérifie si le répertoire dump existe
    if not os.path.exists(dump_dir):
        print(Fore.RED + f"[ERROR] Le répertoire {dump_dir} n'existe pas." + Style.RESET_ALL)
        print()
        input(Fore.MAGENTA + "Appuyez sur Entrée pour continuer...")
        return

    files_found = False
    results_count = 0  # Compteur pour le nombre de résultats trouvés

    try:
        for filename in os.listdir(dump_dir):
            if filename.endswith('.txt'):
                files_found = True
                filepath = os.path.join(dump_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                        for line in lines:
                            if search_term in line:
                                results_count += 1
                                print(Fore.GREEN + f"[FOUND] " + Style.RESET_ALL + f"Match trouvé dans {filename}: {line.strip()}")
                except IOError as io_error:
                    print(Fore.RED + f"[ERROR] Impossible de lire le fichier {filename}: {io_error}" + Style.RESET_ALL)

        if not files_found:
            print(Fore.RED + f"[ERROR] Aucun fichier .txt trouvé dans le répertoire {dump_dir}." + Style.RESET_ALL)
        elif results_count == 0:
            print(Fore.RED + f"[INFO] Aucun résultat trouvé pour {search_term} dans les fichiers du dump." + Style.RESET_ALL)
        else:
            print(Fore.CYAN + f"[INFO] Nombre total de résultats trouvés pour '{search_term}': {results_count}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[ERROR] Une erreur est survenue : {e}" + Style.RESET_ALL)
    
    input(Fore.MAGENTA + "Appuyez sur Entrée pour continuer...")


def clean_filename(hostname):
    return re.sub(r'^([0-9])', '', re.sub(r'[/:"*?<>|]', '', hostname)).replace('^0','').replace('^1','').replace('^2','').replace('^3','').replace('^4','').replace('^5','').replace('^6','').replace('^7','').replace('^8','').replace('^9','')

def check_if_player_exists(filename, player_data, added_players):
    if not os.path.exists(filename):
        return False

    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    for i, line in enumerate(lines):
        try:
            existing_player = json.loads(line)
        except json.JSONDecodeError:
            continue

        if existing_player.get('fivem') == player_data.get('fivem'):
            fields_to_check = ['steam', 'name', 'live', 'xbl', 'license', 'license2', 'name', 'ip']
            fields_match = True

            for field in fields_to_check:
                existing_field_value = existing_player.get(field)
                new_field_value = player_data.get(field)

                if (existing_field_value is not None or new_field_value is not None) and existing_field_value != new_field_value:
                    fields_match = False
                    break

            if fields_match:
                return True

    if player_data['identifiers'] in added_players:
        return True

    return False

def search_player_by_discord_id(players, discord_id):
    for player in players:
        for identifier in player['identifiers']:
            if f'discord:{discord_id}' in identifier:
                return player
    return None

def get_server_info(server_id, proxy, added_players, discord_id=None):
    url = f'https://servers-frontend.fivem.net/api/servers/single/{server_id}'
    user_agent = UserAgent()
    headers = {
        'User-Agent': user_agent.random,
        'method': 'GET'
    }

    try:
        response = requests.get(url, headers=headers, proxies=proxy)

        if response.status_code == 200:
            server_data = response.json()
            hostname = clean_filename(str(uuid.uuid4()))

            try:
                hostname = clean_filename(server_data['Data']['hostname'])[:100]
            except Exception as err:
                print(err)

            try:
                if len(server_data['Data']['vars']['sv_projectName']) >= 10:
                    hostname = clean_filename(server_data['Data']['vars']['sv_projectName'])[:100]
            except:
                pass

            if not os.path.exists('dump'):
                os.makedirs('dump')

            filename = f'dump/{hostname}.txt'
            players_added_count = 0

            if discord_id:
                player = search_player_by_discord_id(server_data['Data']['players'], discord_id)
                if player:
                    print(Fore.GREEN + f'[INFO]' + Style.RESET_ALL + f" Joueur avec Discord ID {discord_id} trouvé : {player['name']}")
                else:
                    print(Fore.RED + f'[INFO]' + Style.RESET_ALL + f" Aucun joueur trouvé avec Discord ID {discord_id}")
            else:
                for player in server_data['Data']['players']:
                    player_data = json.dumps(player, ensure_ascii=False)
                    player_identifiers = player['identifiers']

                    if not check_if_player_exists(filename, player, added_players):
                        with open(filename, 'a', encoding='utf-8') as file:
                            file.write(player_data)
                            file.write('\n')

                        print(Fore.GREEN + f'[NEW]' + Style.RESET_ALL + f' {player["name"]} a été ajouté !')
                        added_players.append(player_identifiers)
                        players_added_count += 1

            print(Fore.CYAN + f'[INFO]' + Style.RESET_ALL + f' Nombre de joueurs ajoutés dans {filename}: {players_added_count}')
            print(Fore.CYAN + '[INFO]' + Style.RESET_ALL + f' Nombre total de joueurs ajoutés : {len(added_players)}\n')

        else:
            print(Fore.RED + f'\n[ERROR]' + Style.RESET_ALL + f" Message d'erreur ({server_id}: {response.status_code})\n")

    except Exception as e:
        print(f'Erreur: {str(e)}')

def process_servers(server_ids, proxies, added_players, discord_id=None):
    for server_id, proxy in zip(server_ids, proxies):
        # Vérifiez si la touche "V" a été pressée pour interrompre la boucle
        if keyboard.is_pressed('v'):
            print(Fore.MAGENTA + "\n[INFO] Interrompu par l'utilisateur. Retour au menu principal..." + Style.RESET_ALL)
            break

        get_server_info(server_id, proxy, added_players, discord_id)
        time.sleep(0.5)

def print_slow(text, delay=0.01):
    for line in text.splitlines():
        for char in line:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()  # Passer à la ligne suivante
    print()  # Sauter une ligne après avoir fini

def display_banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner = '''
                                                       
  /$$$$$$        /$$                                  
 /$$__  $$      | $$                                  
| $$  \ $$  /$$$$$$$  /$$$$$$  /$$$$$$/$$$$   /$$$$$$ 
| $$$$$$$$ /$$__  $$ /$$__  $$| $$_  $$_  $$ /$$__  $$
| $$__  $$| $$  | $$| $$$$$$$$| $$ \ $$ \ $$| $$  \ $$
| $$  | $$| $$  | $$| $$_____/| $$ | $$ | $$| $$  | $$
| $$  | $$|  $$$$$$$|  $$$$$$$| $$ | $$ | $$|  $$$$$$/
|__/  |__/ \_______/ \_______/|__/ |__/ |__/ \______/ 

'''
    faded_text = fade.purplepink(banner)
    print(faded_text)

username = os.getlogin()

def main():
    with open('serveur.txt', 'r') as server_file:
        french_server_ids = [line.strip() for line in server_file.readlines()]

    with open('proxy.txt', 'r') as proxy_file:
        proxy_list = [{'http': f'socks5://{proxy.strip()}'} for proxy in proxy_file]

    added_players = []

    while True:
        display_banner()
        print_slow(f"                                                    Welcome! {username}\n")
        print(Fore.MAGENTA + "\nChoose an option :" + Style.RESET_ALL)
        print()
        print(Fore.MAGENTA + "        (1) - FiveM Dumper (To Stop Restart).  /  (3) - Put in id , liscence to search in the db")
        print()
        print(Fore.MAGENTA + "        (2) - Scrap FiveM Server But With A discord ID  /  (4) - Type exit to quit the aplication")       
        print()
        choice = input(Fore.MAGENTA + "Your choice : " + Style.RESET_ALL).lower()

        if choice == "1":
            while True:
                display_banner()
                print()
                print(Fore.CYAN + 'The Dumper Start In 2s' + Style.RESET_ALL)
                print()
                time.sleep(2)
                process_servers(french_server_ids, proxy_list, added_players)

                print(Fore.MAGENTA + "\n[TIME]" + Style.RESET_ALL + " Dump ENd, pls wait (5sec) For The Next ...\n")
                time.sleep(5)

                if keyboard.is_pressed('V'):
                    print(Fore.MAGENTA + "\Return To The Menue..." + Style.RESET_ALL)
                    time.sleep(1)  # Petite pause pour éviter que l'appui sur 'V' soit détecté trop rapidement dans le menu principal
                    break
        
        elif choice == "2":
            discord_id = input(Fore.MAGENTA + "Enter The Discord ID : " + Style.RESET_ALL)
            process_servers(french_server_ids, proxy_list, added_players, discord_id)

        elif choice == "3":
            print()
            search_term = input(Fore.MAGENTA + "Put The id , xbl to search : " + Style.RESET_ALL)
            search_player_in_dump('dump', search_term)

        elif choice == "exit":
            break

        else:
            print(Fore.RED + "Invalid choice pls " + Style.RESET_ALL)

if __name__ == "__main__":
    main()
