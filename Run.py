import requests
from datetime import datetime
import pytz
from colorama import init, Fore, Style
import webbrowser
import os
import zipfile
import shutil
import sys

try:
    import msvcrt  # Windows
except ImportError:
    import sys, tty, termios  # Unix

# Initialize colorama
init()

def get_single_key():
    """Waits for a single key press and returns it."""
    try:
        return msvcrt.getch().decode('utf-8').lower()
    except ImportError:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_commit_info(box_content, box_width, new_commit):
    print(Fore.MAGENTA + Style.BRIGHT + "+" + "-"*box_width + "+" + Style.RESET_ALL)
    if new_commit:
        new_indicator = "*NEW*"
        print(Fore.MAGENTA + Style.BRIGHT + "|" + " " * ((box_width - len(new_indicator)) // 2) + Fore.YELLOW + Style.BRIGHT + new_indicator + Fore.MAGENTA + " " * ((box_width - len(new_indicator)) // 2) + "|" + Style.RESET_ALL)
        print(Fore.MAGENTA + Style.BRIGHT + "+" + "-"*box_width + "+" + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + "| " + Fore.CYAN + box_content[0].ljust(box_width - 2) + Fore.MAGENTA + " |" + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + "+" + "-"*box_width + "+" + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + "| " + Fore.CYAN + box_content[1].ljust(box_width - 2) + Fore.MAGENTA + " |" + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + "| " + Fore.CYAN + box_content[2].ljust(box_width - 2) + Fore.MAGENTA + " |" + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + "| " + Fore.CYAN + box_content[3].ljust(box_width - 2) + Fore.MAGENTA + " |" + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + "+" + "-"*box_width + "+" + Style.RESET_ALL)
    options = "X = Xbox | P = PS3 | O = Open Commit"
    print(Fore.MAGENTA + Style.BRIGHT + "| " + Fore.CYAN + options.center(box_width - 2) + Fore.MAGENTA + " |" + Style.RESET_ALL)
    print(Fore.MAGENTA + Style.BRIGHT + "+" + "-"*box_width + "+" + Style.RESET_ALL)

def download_with_progress(url, destination):
    response = requests.get(url, stream=True)
    total_length = response.headers.get('content-length')

    if total_length is None:  # no content length header
        with open(destination, 'wb') as f:
            f.write(response.content)
    else:
        total_length = int(total_length)
        downloaded = 0
        last_done = -1
        bar_length = 50  # Adjusted bar width
        with open(destination, 'wb') as f:
            for data in response.iter_content(chunk_size=4096):
                downloaded += len(data)
                f.write(data)
                done = int(bar_length * downloaded / total_length)
                if done != last_done:
                    clear_screen()
                    print(Fore.MAGENTA + "+" + "-"*52 + "+" + Style.RESET_ALL)
                    print(Fore.MAGENTA + "|" + " " + Fore.CYAN + "Downloading...".center(50) + Fore.MAGENTA + " " + "|" + Style.RESET_ALL)
                    print(Fore.MAGENTA + "|" + Fore.CYAN + "[" + "#" * done + " " * (bar_length-done) + "]" + Fore.MAGENTA + "|" + Style.RESET_ALL)
                    print(Fore.MAGENTA + "+" + "-"*52 + "+" + Style.RESET_ALL)
                    sys.stdout.flush()
                    last_done = done

def extract_zip(source, destination):
    with zipfile.ZipFile(source, 'r') as zip_ref:
        zip_ref.extractall(destination)

def get_latest_commit_info(repo, branch):
    url = f"https://api.github.com/repos/{repo}/commits/{branch}"
    response = requests.get(url)
    
    if response.status_code == 200:
        commit_data = response.json()
        latest_commit_sha = commit_data['sha']
        author_login = commit_data['author']['login']
        commit = commit_data['commit']
        message = commit['message']
        date_str = commit['author']['date']
        commit_url = commit_data['html_url']
        
        # Check if the latest commit is new
        seen_commit_file = "seen_commit.txt"
        if os.path.exists(seen_commit_file):
            with open(seen_commit_file, "r") as file:
                seen_commit_sha = file.read().strip()
        else:
            seen_commit_sha = ""
        
        new_commit = (latest_commit_sha != seen_commit_sha)
        
        # Store the latest commit SHA
        with open(seen_commit_file, "w") as file:
            file.write(latest_commit_sha)
        
        # Parse the date string and convert to desired timezone
        date_utc = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        local_tz = pytz.timezone('US/Mountain')
        date_local = date_utc.replace(tzinfo=pytz.utc).astimezone(local_tz)
        formatted_date = date_local.strftime("%A, at %I:%M %p %Z")
        
        # Determine the width of the box
        box_content = [
            f"Latest commit to {branch} branch:",
            f"Author : {author_login}",
            f"Date   : {formatted_date}",
            f"Message: {message}",
            "X = Xbox | P = PS3 | O = Open Commit"
        ]
        box_width = max(len(line) for line in box_content) + 4
        
        display_commit_info(box_content, box_width, new_commit)
        
        while True:
            print(Fore.CYAN + "Enter Selection: " + Style.RESET_ALL, end='', flush=True)
            choice = get_single_key()
            print(Fore.MAGENTA + choice.upper() + Style.RESET_ALL)
            if choice == 'x':
                print(Fore.CYAN + "Would you like to download the latest Xbox Nightly? (Y/N): " + Style.RESET_ALL, end='', flush=True)
                sub_choice = get_single_key()
                print(Fore.MAGENTA + sub_choice.upper() + Style.RESET_ALL)
                if sub_choice == 'n':
                    clear_screen()
                    display_commit_info(box_content, box_width, new_commit)
                elif sub_choice == 'y':
                    clear_screen()
                    download_url = "https://nightly.link/hmxmilohax/rock-band-3-deluxe/workflows/build/develop/RB3DX-Xbox.zip"
                    download_path = "RB3DX-Xbox.zip"
                    download_with_progress(download_url, download_path)
                    if os.path.exists("Xbox"):
                        shutil.rmtree("Xbox")
                    os.makedirs("Xbox")
                    extract_zip(download_path, "Xbox")
                    os.remove(download_path)
                    clear_screen()
                    display_commit_info(box_content, box_width, new_commit)
                    print(Fore.CYAN + "Would you like to open the Xbox directory? (Y/N): " + Style.RESET_ALL, end='', flush=True)
                    open_choice = get_single_key()
                    print(Fore.MAGENTA + open_choice.upper() + Style.RESET_ALL)
                    if open_choice == 'y':
                        os.startfile("Xbox" if os.name == 'nt' else 'open "Xbox"')
                    sys.exit()
            elif choice == 'p':
                print(Fore.CYAN + "Would you like to download the latest PS3 Nightly? (Y/N): " + Style.RESET_ALL, end='', flush=True)
                sub_choice = get_single_key()
                print(Fore.MAGENTA + sub_choice.upper() + Style.RESET_ALL)
                if sub_choice == 'n':
                    clear_screen()
                    display_commit_info(box_content, box_width, new_commit)
                elif sub_choice == 'y':
                    clear_screen()
                    download_url = "https://nightly.link/hmxmilohax/rock-band-3-deluxe/workflows/build/develop/RB3DX-PS3.zip"
                    download_path = "RB3DX-PS3.zip"
                    download_with_progress(download_url, download_path)
                    if os.path.exists("PS3"):
                        shutil.rmtree("PS3")
                    os.makedirs("PS3")
                    extract_zip(download_path, "PS3")
                    os.remove(download_path)
                    clear_screen()
                    display_commit_info(box_content, box_width, new_commit)
                    print(Fore.CYAN + "Would you like to open the PS3 directory? (Y/N): " + Style.RESET_ALL, end='', flush=True)
                    open_choice = get_single_key()
                    print(Fore.MAGENTA + open_choice.upper() + Style.RESET_ALL)
                    if open_choice == 'y':
                        os.startfile("PS3" if os.name == 'nt' else 'open "PS3"')
                    sys.exit()
            elif choice == 'o':
                webbrowser.open(commit_url)
                clear_screen()
                display_commit_info(box_content, box_width, new_commit)
    else:
        print(Fore.RED + f"Failed to retrieve data: {response.status_code}" + Style.RESET_ALL)

if __name__ == "__main__":
    REPO = "hmxmilohax/rock-band-3-deluxe"
    BRANCH = "develop"
    get_latest_commit_info(REPO, BRANCH)
