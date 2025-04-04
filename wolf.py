#!/usr/bin/env python3
import os
import sys
import subprocess
import requests
import shutil
from time import sleep

# Configurações (ajustadas para Termux com SDCard)
HOME = os.path.expanduser("~")
PASTA_DOWNLOADS = "/sdcard/WolfVideos"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
ARQUIVO_COOKIES = "/sdcard/cookies.txt"
URL_ATUALIZACAO_COOKIES = "https://jottap-termux.github.io/cookies.txt"
ATUALIZAR_COOKIES_AUTO = True
TERMUX_PATH = "/data/data/com.termux/files/home/.local/bin"

# Formatos pré-definidos atualizados
FORMATOS_VIDEO = {
    '1': {'desc': '🎯 Best quality (4K if available)', 'code': 'best'},
    '2': {'desc': '🖥 1080p HD', 'code': '137+140'},
    '3': {'desc': '💻 720p HD', 'code': '22'},
    '4': {'desc': '📱 480p', 'code': '135+140'},
    '5': {'desc': '📼 360p', 'code': '18'}
}

FORMATOS_AUDIO = {
    '1': {'desc': '🎧 MP3 (High quality 320kbps)', 'code': 'mp3', 'params': '-x --audio-format mp3 --audio-quality 0'},
    '2': {'desc': '🎵 AAC (High quality)', 'code': 'aac', 'params': '-x --audio-format aac'},
    '3': {'desc': '🎼 FLAC (Lossless)', 'code': 'flac', 'params': '-x --audio-format flac'},
    '4': {'desc': '🎤 M4A (YouTube default)', 'code': 'm4a', 'params': '-x --audio-format m4a'},
    '5': {'desc': '🎶 OPUS (Efficient)', 'code': 'opus', 'params': '-x --audio-format opus'},
    '6': {'desc': '💿 MP3 with cover art', 'code': 'mp3', 'params': '-x --audio-format mp3 --audio-quality 0 --embed-thumbnail --add-metadata'}
}

def verificar_e_configurar_ambiente():
    """Verifica e configura todo o ambiente necessário"""
    print("\033[1;34m[•] Configurando ambiente...\033[0m")

    # Verifica se está no Termux
    is_termux = 'com.termux' in HOME

    # Configura PATH para Termux
    if is_termux:
        configurar_path_termux()

    # Cria pasta de downloads
    os.makedirs(PASTA_DOWNLOADS, exist_ok=True)
    print(f"\033[1;32m[✓] Pasta de downloads: {PASTA_DOWNLOADS}\033[0m")

    # Instala dependências
    if not instalar_dependencias_auto():
        sys.exit(1)

    # Configura cookies
    criar_cookies()

    # Atualiza cookies se necessário
    if ATUALIZAR_COOKIES_AUTO:
        atualizar_cookies()

def configurar_path_termux():
    """Configura o PATH para incluir binários do pip no Termux"""
    if TERMUX_PATH not in os.environ["PATH"]:
        with open(os.path.join(HOME, ".bashrc"), "a") as f:
            f.write(f'\nexport PATH="$PATH:{TERMUX_PATH}"\n')
        os.environ["PATH"] += f":{TERMUX_PATH}"
        print("\033[1;33m[•] PATH configurado para Termux\033[0m")

def instalar_dependencias_auto():
    """Instala automaticamente todas as dependências necessárias"""
    print("\033[1;34m[•] Instalando/Atualizando dependências...\033[0m")

    try:
        # Verifica se está no Termux
        is_termux = 'com.termux' in HOME

        if is_termux:
            # Tentativa de desbloquear o apt se estiver travado
            try:
                subprocess.run(["rm", "-f", "/data/data/com.termux/files/usr/var/lib/apt/lists/lock"], check=False)
                subprocess.run(["rm", "-f", "/data/data/com.termux/files/usr/var/cache/apt/archives/lock"], check=False)
            except:
                pass

            # Comandos para Termux com tratamento de erros
            def run_termux_command(cmd):
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return True
                except subprocess.CalledProcessError:
                    return False

            # Tentativa de atualizar pacotes
            if not run_termux_command(["pkg", "update", "-y"]):
                print("\033[1;33m[•] Tentando método alternativo de atualização...\033[0m")
                subprocess.run(["apt", "update", "-y"], check=True)

            # Instala pacotes essenciais
            packages = ["python", "ffmpeg", "libxml2", "libxslt", "binutils", "wget", "git"]
            for pkg in packages:
                if not run_termux_command(["pkg", "install", "-y", pkg]):
                    print(f"\033[1;33m[•] Tentando instalar {pkg} com apt...\033[0m")
                    subprocess.run(["apt", "install", "-y", pkg], check=True)

            # Instala pip se não existir
            if not shutil.which("pip"):
                subprocess.run(["pkg", "install", "-y", "python-pip"], check=True)

            # Instala yt-dlp e requests
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "yt-dlp", "requests"], check=True)

            # Garante que o yt-dlp está acessível
            if not shutil.which("yt-dlp"):
                print("\033[1;33m[•] Configurando yt-dlp...\033[0m")
                ytdlp_path = os.path.join(TERMUX_PATH, "yt-dlp")
                if not os.path.exists(TERMUX_PATH):
                    os.makedirs(TERMUX_PATH, exist_ok=True)
                subprocess.run(["ln", "-s", f"{HOME}/.local/bin/yt-dlp", ytdlp_path], check=True)
        else:
            # Comandos para Linux tradicional
            subprocess.run(["sudo", "apt", "update", "-y"], check=True)
            subprocess.run(["sudo", "apt", "upgrade", "-y"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "python3", "python3-pip", "ffmpeg", "wget"], check=True)
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "requests"], check=True)

        print("\033[1;32m[✓] Dependências instaladas/atualizadas!\033[0m")

        # Verifica instalação do yt-dlp
        if not verificar_yt_dlp():
            print("\033[1;31m[!] Falha crítica: yt-dlp não instalado corretamente\033[0m")
            return False

        return True
    except Exception as e:
        print(f"\033[1;31m[!] Erro durante instalação: {e}\033[0m")
        print("\033[1;33m[•] Você pode tentar instalar manualmente:")
        print("  1. pkg update && pkg upgrade")
        print("  2. pkg install -y python ffmpeg libxml2 libxslt binutils wget")
        print("  3. pip install --user yt-dlp requests")
        print("  4. ln -s ~/.local/bin/yt-dlp ~/.local/bin/yt-dlp\033[0m")
        return False

def verificar_yt_dlp():
    """Verifica se o yt-dlp está instalado e acessível"""
    try:
        # Verifica se o comando existe
        if not shutil.which("yt-dlp"):
            # Tenta encontrar o caminho manualmente no Termux
            termux_ytdlp = f"{TERMUX_PATH}/yt-dlp"
            if os.path.exists(termux_ytdlp):
                os.environ["PATH"] += f":{TERMUX_PATH}"
                return True
            return False

        # Verifica a versão
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"\033[1;32m[✓] yt-dlp versão {result.stdout.strip()} instalado\033[0m")
            return True
        return False
    except Exception:
        return False

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def mostrar_banner():
    print("""\033[1;36m
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣶⠶⢦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⠁⠀⠸⠛⢳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠃⠀⠀⠀⠀⣿⠹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠃⠀⠀⠀⠀⠀⣿⠀⢿⠀⣴⠟⠷⣆⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⠃⠀⠀⠀⠀⢀⣤⡟⠀⢸⣿⠃⠀⠀⠘⣷⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡾⠁⠀⠀⠀⠀⠀⣸⡿⠿⠟⢿⡏⠀⠀⠀⢀⣿⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣤⣾⠟⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⣼⡇⠀⠀⠀⣸⡏⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠛⡋⠉⣩⡇⠀⠀⠀⠀⠀⠀⠀⠀⠘⣷⣰⠟⠋⠁⠀⠀⢠⡟⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠏⢠⡞⣱⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠟⠀⠀⠀⠀⠀⣾⠃⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠃⢀⣿⢁⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠀⠀⠀⠀⣠⢰⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠁⠀⢸⣿⣿⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⢀⣶⣾⡇⢸⣧⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠀⠀⠀⢸⣿⣿⣾⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣏⣠⢰⢻⡟⢃⡿⡟⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣿⡇⠀⠀⠀⠀⠁⢿⠹⣿⣄⠀⠀⠀⢀⠀⠀⠀⠀⢺⠏⣿⣿⠼⠁⠈⠰⠃⣿⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⡟⠃⠀⠈⢻⣷⣄⠈⠁⣿⣿⡇⠀⠀⠈⣧⠀⠀⠀⠘⣠⠟⠁⠀⠀⠀⠀⠀⢻⡇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⣾⠟⠀⠀⣴⠀⠀⣿⡿⠀⠸⠋⢸⣿⣧⡐⣦⣸⡆⠀⠀⠈⠁⠀⠀⠀⠀⠀⠀⠀⠘⣿⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣠⡿⠃⠀⣀⣴⣿⡆⢀⣿⠃⠀⠀⠀⣸⠟⢹⣷⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣧⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣀⣤⣾⡏⠛⠻⠿⣿⣿⣿⠁⣼⠇⠀⠀⠀⠀⠁⠀⢸⣿⠙⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣇⠀⠀⠀⠀⠀
⠲⢾⣿⣿⣿⣿⣇⢀⣠⣴⣿⡿⢁⣼⣿⣀⠀⠀⠀⠀⠀⠀⠈⢿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣆⠀⠀⠀⠀
⠀⠀⠉⠙⠛⠻⣿⣷⣶⣿⣷⠾⣿⣵⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠙⠀⠀⠀⠀⠀⠀⠀⢤⡀⠀⠀⠀⠀⠀⠀⠀⡀⢿⡆⠀⠀⠀
⠀⠀⠀⠀⠀⣰⣿⡟⣴⠀⠀⠉⠉⠁⢿⡇⣴⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡆⠀⠀⠀⠀⣴⠀⣿⣿⣿⠀⠀⠀
⠀⠀⠀⠀⢠⣿⠿⣿⣿⢠⠇⠀⠀⠀⢸⣿⢿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⣀⠀⠀⢸⣿⡄⠀⠀⣼⣿⣇⢹⡟⢿⡇⠀⠀
⠀⠀⠀⠀⣿⠃⣠⣿⣿⣿⠀⠀⠀⠀⠀⢻⡈⢿⣆⠀⢳⡀⠀⢠⠀⠀⠀⠀⠀⢸⣿⣦⠀⣸⠿⣷⡀⠀⣿⣿⢿⣾⣿⠸⠇⠀⠀
⠀⠀⠀⠀⠋⣰⣿⣿⣿⣿⡀⢰⡀⠀⠀⠀⠀⠈⢻⣆⣼⣷⣄⠈⢷⡀⠀⠀⠀⢸⣿⢿⣶⠟⠀⠙⣷⣼⣿⣿⡄⠻⣿⣧⡀⠀⠀
⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣧⡿⠀⠀⠀⠀⠀⠀⠀⠙⢿⡄⠻⣷⣼⣿⣦⡀⠀⣼⠇⠸⠋⠀⠀⠀⠈⠻⣿⣿⣷⡀⠈⠻⣷⡀⠀
⠀⠀⠀⠀⠀⣿⣼⡿⢻⣿⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠀⠈⠻⣷⡙⣿⣶⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣷⢠⣀⠘⣷⡀
⠀⠀⠀⠀⠀⠀⣿⠇⣾⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠈⠛⢿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⠀⢻⣷⣾⡇
⠀⠀⠀⠀⠀⠀⣿⢠⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠓⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠀⢈⣿⡹⣷
⠀⠀⠀⠀⠀⠀⠈⠀⠻⠿⠿⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⡇⠉

██╗    ██╗ ██████╗ ██╗     ████████
██║    ██║██╔═══██╗██║     ██║
██║ █╗ ██║██║   ██║██║     ████████
██║███╗██║██║   ██║██║     ██
╚███╔███╔╝╚██████╔╝███████╗██╗
 ╚══╝╚══╝  ╚═════╝ ╚══════╝╚══════╝
 ██╗   ██╗██╗██████╗ ███████╗ ██████╗ ███████╗
 ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗██╔════╝
 ██║   ██║██║██║  ██║█████╗  ██║   ██║███████╗
 ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║╚════██║
  ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝███████║
   ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝
 \033[1;32m_______________________________________________
  • insta:jottap_62 • by jottap_62 • v6.0 • Wolf Edition• |
 ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
\033[1;33m• Recursos Premium:
  ✔ Download de vídeos 4K/1080p
  ✔ Conversão para MP3 com qualidade de estúdio
  ✔ Bypass de paywalls e restrições
  ✔ Sistema de cookies automático
  ✔ Player integrado com pré-visualização
  ✔ Suporte a múltiplas plataformas\033[0m""")

def criar_cookies():
    """Cria arquivo de cookies padrão se não existir"""
    try:
        if not os.path.exists(ARQUIVO_COOKIES):
            cookies_padrao = """# Netscape HTTP Cookie File
.xvideos.com    TRUE    /       FALSE   1735689600      ts      1
.xvideos.com    TRUE    /       FALSE   1735689600      platform      pc
.xvideos.com    TRUE    /       FALSE   1735689600      hash    5a8d9f8e7c6b5a4d3e2f1
"""
            with open(ARQUIVO_COOKIES, 'w') as f:
                f.write(cookies_padrao)
            print("\033[1;33m[•] Arquivo de cookies criado em:", ARQUIVO_COOKIES, "\033[0m")
    except PermissionError:
        print("\033[1;31m[!] Erro de permissão. Tentando criar cookies em local alternativo...\033[0m")
        # Usa um caminho alternativo dentro do Termux
        alt_cookies = os.path.join(HOME, ".cookies.txt")
        with open(alt_cookies, 'w') as f:
            f.write(cookies_padrao)
        print("\033[1;33m[•] Arquivo de cookies criado em:", alt_cookies, "\033[0m")
        return alt_cookies
    return ARQUIVO_COOKIES

def verificar_dependencias():
    """Verifica e instala dependências necessárias"""
    print("\033[1;34m[•] Verificando dependências...\033[0m")

    # Verifica yt-dlp
    try:
        subprocess.run(["yt-dlp", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("\033[1;32m[✓] yt-dlp já está instalado\033[0m")
    except:
        print("\033[1;33m[•] Instalando yt-dlp...\033[0m")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "yt-dlp"], check=True)

    # Verifica ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("\033[1;32m[✓] ffmpeg já está instalado\033[0m")
    except:
        print("\033[1;31m[!] ffmpeg não encontrado. É necessário para conversão MP3.\033[0m")
        if 'com.termux' in HOME:
            print("\033[1;33m[•] Execute: pkg install ffmpeg -y\033[0m")
        else:
            print("\033[1;33m[•] Execute: sudo apt install ffmpeg -y\033[0m")

    # Verifica cookies
    if not os.path.exists(ARQUIVO_COOKIES):
        criar_cookies()
    else:
        print("\033[1;32m[✓] Arquivo de cookies encontrado\033[0m")

def atualizar_ferramentas():
    """Atualiza o yt-dlp corretamente via pip"""
    print("\033[1;33m[•] Atualizando ferramentas...\033[0m")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "yt-dlp", "requests"], check=True)
        print("\033[1;32m[✓] Ferramentas atualizadas com sucesso!\033[0m")
    except Exception as e:
        print(f"\033[1;31m[!] Erro ao atualizar: {e}\033[0m")

def atualizar_cookies():
    """Atualiza cookies a partir da URL"""
    try:
        print("\033[1;34m[•] Baixando novos cookies...\033[0m")
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(URL_ATUALIZACAO_COOKIES, headers=headers, timeout=10)

        if response.status_code == 200:
            with open(ARQUIVO_COOKIES, 'w') as f:
                f.write(response.text)
            print("\033[1;32m[✓] Cookies atualizados com sucesso!\033[0m")
        else:
            print("\033[1;31m[!] Falha ao baixar cookies. Status code:", response.status_code, "\033[0m")
    except Exception as e:
        print(f"\033[1;31m[!] Erro ao atualizar cookies: {str(e)}\033[0m")

def mostrar_menu_video_qualidade():
    """Mostra menu de qualidade para vídeos"""
    print("""\033[1;36m
╔════════════════════════════════════════╗
║        📽  VIDEO QUALITY OPTIONS        ║
╠════════════════════════════════════════╣
║ 1. 🎯 Best quality (4K if available)   ║
║ 2. 🖥  1080p HD                         ║
║ 3. 💻  720p HD                         ║
║ 4. 📱  480p                            ║
║ 5. 📼  360p                            ║
║ 0. 🚪 Voltar                           ║
╚════════════════════════════════════════╝
\033[0m""")

def mostrar_menu_audio_formatos():
    """Mostra menu de formatos para áudio"""
    print("""\033[1;36m
╔════════════════════════════════════════╗
║        🎵 AUDIO FORMAT OPTIONS         ║
╠════════════════════════════════════════╣
║ 1. 🎧 MP3 (High quality 320kbps)       ║
║ 2. 🎵 AAC (High quality)               ║
║ 3. 🎼 FLAC (Lossless)                  ║
║ 4. 🎤 M4A (YouTube default)            ║
║ 5. 🎶 OPUS (Efficient)                 ║
║ 6. 💿 MP3 with cover art               ║
║ 0. 🚪 Voltar                           ║
╚════════════════════════════════════════╝
\033[0m""")

def listar_formatos(link):
    """Lista os formatos disponíveis para download"""
    print("\033[1;36m[•] Listando formatos disponíveis...\033[0m")
    try:
        subprocess.run(f'yt-dlp --cookies "{ARQUIVO_COOKIES}" -F "{link}"', shell=True)

        # Mostra menu de qualidade após listar formatos
        while True:
            mostrar_menu_video_qualidade()
            opcao = input("\n\033[1;36m🎬 Escolha uma opção [0-5]: \033[0m").strip()

            if opcao == "0":
                break
            elif opcao in FORMATOS_VIDEO:
                qualidade = FORMATOS_VIDEO[opcao]['code']
                if baixar_video(link, 'mp4', qualidade):
                    print(f"\033[1;32m[✓] Arquivo salvo em: {PASTA_DOWNLOADS}\033[0m")
                break
            else:
                print("\033[1;31m[!] Opção inválida. Tente novamente.\033[0m")

    except Exception as e:
        print(f"\033[1;31m[!] Erro ao listar formatos: {str(e)}\033[0m")

def baixar_multiplas_urls(tipo='video'):
    """Baixa múltiplas URLs de uma vez"""
    print("\033[1;36m[•] Modo múltiplas URLs (CTRL+D para finalizar)\033[0m")
    print("\033[1;33m[•] Cole as URLs uma por linha:\033[0m")

    urls = []
    try:
        while True:
            url = input().strip()
            if url.startswith(('http://', 'https://')):
                urls.append(url)
            elif url:
                print("\033[1;31m[!] URL inválida. Deve começar com http:// ou https://\033[0m")
    except EOFError:
        pass

    if not urls:
        print("\033[1;31m[!] Nenhuma URL válida fornecida\033[0m")
        return

    if tipo == 'video':
        mostrar_menu_video_qualidade()
        opcao = input("\n\033[1;36m🎬 Escolha a qualidade [1-5]: \033[0m").strip()
        if opcao in FORMATOS_VIDEO:
            qualidade = FORMATOS_VIDEO[opcao]['code']
        else:
            qualidade = 'best'
    else:
        mostrar_menu_audio_formatos()
        opcao = input("\n\033[1;36m🎵 Escolha o formato [1-6]: \033[0m").strip()
        if opcao in FORMATOS_AUDIO:
            formato = FORMATOS_AUDIO[opcao]
        else:
            formato = FORMATOS_AUDIO['1']

    for i, url in enumerate(urls, 1):
        print(f"\n\033[1;35m[•] Baixando URL {i}/{len(urls)}\033[0m")
        if tipo == 'video':
            baixar_video(url, 'mp4', qualidade)
        else:
            baixar_video(url, formato['code'], None, formato['params'])

def baixar_video(link, formato='mp4', qualidade=None, params_extra=None):
    """Executa o download com múltiplas estratégias e fallback automático"""
    tentativas = [
        f'yt-dlp --user-agent "{USER_AGENT}" --cookies "{ARQUIVO_COOKIES}" --no-check-certificate',
        f'yt-dlp --user-agent "{USER_AGENT}" --cookies "{ARQUIVO_COOKIES}" --force-generic-extractor',
        'yt-dlp --ignore-errors'
    ]

    output_template = f'"{PASTA_DOWNLOADS}/%(title)s.%(ext)s"'
    comando_base = None

    # Construir o comando baseado nos parâmetros
    if params_extra:
        comando_base = f'{params_extra} -o {output_template}'
    elif formato == 'mp3':
        comando_base = f'-x --audio-format mp3 --audio-quality 0 -o {output_template}'
    elif qualidade:
        # Verifica se o formato solicitado existe antes de tentar
        if qualidade in ['best', '22', '18', '137+140', '135+140']:
            comando_base = f'-f "{qualidade}+bestaudio" --merge-output-format {formato} -o {output_template}'
        else:
            comando_base = f'-f best -o {output_template}'
    else:
        comando_base = f'-f best -o {output_template}'

    for tentativa, cmd in enumerate(tentativas, 1):
        print(f"\n\033[1;35m[•] Tentativa {tentativa}/3\033[0m")
        comando = f'{cmd} {comando_base} "{link}"'

        try:
            print(f"\033[1;33m[•] Executando: {comando[:120]}...\033[0m")
            
            # Se falhar na primeira tentativa com formato específico, tentar com fallback
            if tentativa > 1 and qualidade and qualidade != 'best':
                print("\033[1;33m[•] Tentando fallback para melhor qualidade disponível...\033[0m")
                comando = f'{cmd} -f best -o {output_template} "{link}"'

            resultado = subprocess.run(comando, shell=True, check=True)
            if resultado.returncode == 0:
                print(f"\033[1;32m[✓] Download concluído com sucesso!\033[0m")
                return True

        except subprocess.CalledProcessError as e:
            # Se falhar por formato não disponível, tentar listar formatos
            if "Requested format is not available" in str(e):
                print("\033[1;33m[•] Formato solicitado não disponível. Listando formatos...\033[0m")
                subprocess.run(f'yt-dlp --list-formats "{link}"', shell=True)
                
                # Perguntar ao usuário qual formato usar
                novo_formato = input("\033[1;36m[?] Digite o código do formato desejado (ou Enter para melhor qualidade): \033[0m").strip()
                if novo_formato:
                    comando_base = f'-f "{novo_formato}+bestaudio" --merge-output-format {formato} -o {output_template}'
                    continue
                else:
                    comando_base = f'-f best -o {output_template}'
                    continue
            
            print(f"\033[1;31m[!] Erro na tentativa {tentativa}: {str(e)}\033[0m")
        except Exception as e:
            print(f"\033[1;31m[!] Erro inesperado na tentativa {tentativa}: {str(e)}\033[0m")

    print("\033[1;31m[!] Todas as tentativas falharam. Verifique sua conexão e a URL.\033[0m")
    return False

def mostrar_menu_config():
    global ATUALIZAR_COOKIES_AUTO
    while True:
        clear_screen()
        print("""\033[1;36m
╔════════════════════════════════════════╗
║           ⚙️  CONFIGURAÇÕES             ║
╠════════════════════════════════════════╣
║ 1. {} Atualização automática de cookies║
║ 2. ⚡ Instalar todas as dependências   ║
║ 0. 🔙 Voltar ao menu principal         ║
╚════════════════════════════════════════╝
\033[0m""".format("✅" if ATUALIZAR_COOKIES_AUTO else "❌"))

        opcao = input("\n\033[1;36m⚙️ Escolha uma opção: \033[0m").strip()

        if opcao == "0":
            break
        elif opcao == "1":
            ATUALIZAR_COOKIES_AUTO = not ATUALIZAR_COOKIES_AUTO
            status = "ativada" if ATUALIZAR_COOKIES_AUTO else "desativada"
            print(f"\033[1;32m[✓] Atualização automática de cookies {status}\033[0m")
            sleep(1)
        elif opcao == "2":
            instalar_dependencias_auto()
            input("\n\033[1;36mPressione Enter para continuar...\033[0m")
        else:
            print("\033[1;31m[!] Opção inválida. Tente novamente.\033[0m")
            sleep(1)

def mostrar_menu_principal():
    print("""\033[1;36m
╔════════════════════════════════════════╗
║    🎬 WOLF VIDEO DOWNLOADER PREMIUM    ║
╠════════════════════════════════════════╣
║ 1. 🎥 Baixar vídeo (melhor qualidade)  ║
║ 2. 📊 Escolher qualidade específica    ║
║ 3. 🎧 Converter para áudio             ║
║ 4. 📋 Listar formatos disponíveis      ║
║ 5. 🔄 Atualizar ferramentas            ║
║ 6. 🍪 Atualizar cookies manualmente    ║
║ 7. ⚙️ Configurações                     ║
║ 8. 📂 Baixar múltiplos vídeos          ║
║ 9. 🎶 Baixar múltiplos áudios          ║
║ 0. 🚪 Sair                             ║
╚════════════════════════════════════════╝
\033[0m""")

def main():
    clear_screen()
    mostrar_banner()

    # Configuração completa do ambiente
    verificar_e_configurar_ambiente()

    # Verifica se é Termux e ajusta permissões
    if 'com.termux' in HOME:
        print("\033[1;33m[•] Modo Termux detectado\033[0m")
        if not os.path.exists(PASTA_DOWNLOADS):
            os.makedirs(PASTA_DOWNLOADS, mode=0o755, exist_ok=True)

    while True:
        mostrar_menu_principal()
        opcao = input("\n\033[1;36m✨ Escolha uma opção [0-9]: \033[0m").strip()

        if opcao == "0":
            print("\n\033[1;32m[✓] Programa encerrado.\033[0m")
            break
        elif opcao == "7":
            mostrar_menu_config()
        elif opcao == "6":
            atualizar_cookies()
        elif opcao == "5":
            atualizar_ferramentas()
        elif opcao == "8":
            baixar_multiplas_urls(tipo='video')
        elif opcao == "9":
            baixar_multiplas_urls(tipo='audio')
        elif opcao in ["1", "2", "3", "4"]:
            link = input("\n\033[1;36m🔗 Digite a URL do vídeo: \033[0m").strip()

            if not link.startswith(('http://', 'https://')):
                print("\033[1;31m[!] URL inválida. Deve começar com http:// ou https://\033[0m")
                continue

            if opcao == "4":
                listar_formatos(link)
            elif opcao == "3":
                mostrar_menu_audio_formatos()
                opcao_audio = input("\n\033[1;36m🎵 Escolha o formato [1-6]: \033[0m").strip()
                if opcao_audio in FORMATOS_AUDIO:
                    formato = FORMATOS_AUDIO[opcao_audio]
                    if baixar_video(link, formato['code'], None, formato['params']):
                        print(f"\033[1;32m[✓] Arquivo salvo em: {PASTA_DOWNLOADS}\033[0m")
            elif opcao == "1":
                if baixar_video(link, 'mp4'):
                    print(f"\033[1;32m[✓] Arquivo salvo em: {PASTA_DOWNLOADS}\033[0m")
            elif opcao == "2":
                listar_formatos(link)
        else:
            print("\033[1;31m[!] Opção inválida. Tente novamente.\033[0m")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[1;31m[!] Programa interrompido pelo usuário.\033[0m")
        sys.exit(0)
