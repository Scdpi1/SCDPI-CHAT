#!/usr/bin/env python3
"""
SCDPI CHAT - Cliente IRC Universal Multiplataforma
Versão 2.3 - Com reconexão automática e melhorias de UX
"""
import socket
import ssl
import time
import json
import os
import sys
import platform
import argparse
from pathlib import Path
from datetime import datetime  # NOVO: Para adicionar timestamps

# Configuração de cores para terminal
class Colors:
    if platform.system() == "Windows":
        try:
            import colorama
            colorama.init()
            RED = colorama.Fore.RED
            GREEN = colorama.Fore.GREEN
            YELLOW = colorama.Fore.YELLOW
            BLUE = colorama.Fore.BLUE
            MAGENTA = colorama.Fore.MAGENTA
            CYAN = colorama.Fore.CYAN
            WHITE = colorama.Fore.WHITE
            RESET = colorama.Style.RESET_ALL
            BOLD = colorama.Style.BRIGHT
        except ImportError:
            RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = BOLD = ''
    else:
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
        BOLD = '\033[1m'

def get_user_configuration():
    """Obtém configuração interativa do usuário"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔══════════════════════════════════════════╗")
    print("║           SCDPI CHAT - CONFIG            ║")
    print("║    Configure sua conexão IRC abaixo      ║")
    print("╚══════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    # Nickname (obrigatório)
    while True:
        nickname = input(f"{Colors.YELLOW}🔤 Seu nickname: {Colors.RESET}").strip()
        if nickname and ' ' not in nickname:
            break
        print(f"{Colors.RED}❌ Nickname é obrigatório e não pode conter espaços!{Colors.RESET}")
    
    # Configurações opcionais
    channel = input(f"{Colors.YELLOW}📺 Canal [{Colors.WHITE}#scdpi-test{Colors.YELLOW}]: {Colors.RESET}") or "#scdpi-test"
    if not channel.startswith('#'):
        channel = '#' + channel
    
    server = input(f"{Colors.YELLOW}🌐 Servidor [{Colors.WHITE}irc.libera.chat{Colors.YELLOW}]: {Colors.RESET}") or "irc.libera.chat"
    port = input(f"{Colors.YELLOW}🚪 Porta [{Colors.WHITE}6697{Colors.YELLOW}]: {Colors.RESET}") or "6697"
    use_ssl = input(f"{Colors.YELLOW}🔒 Usar SSL? (s/n) [{Colors.WHITE}s{Colors.YELLOW}]: {Colors.RESET}") or "s"
    
    config = {
        "nickname": nickname,
        "channels": [channel],
        "server": server,
        "port": int(port),
        "use_ssl": use_ssl.lower() == 's',
        "realname": f"{nickname} User",
        "server_password": ""
    }
    
    # NOVO: Salvar configuração automaticamente
    config_path = get_default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    
    return config

def get_default_config_path():
    """Retorna o path correto do config baseado no SO"""
    system = platform.system()
    if system == "Windows":
        return Path(os.environ['APPDATA']) / "SCDPI" / "config.json"
    elif "TERMUX" in os.environ:
        return Path.home() / ".config" / "scdpi" / "config.json"
    else:
        return Path.home() / ".config" / "scdpi" / "config.json"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='SCDPI CHAT - Cliente IRC com Notificações')
    parser.add_argument('--config', help='Arquivo de configuração personalizado')
    parser.add_argument('--nick', help='Nickname para usar')
    parser.add_argument('--channel', help='Canal para entrar')
    parser.add_argument('--server', help='Servidor IRC')
    parser.add_argument('--port', type=int, help='Porta do servidor')
    parser.add_argument('--no-ssl', action='store_true', help='Não usar SSL')
    parser.add_argument('--verbose', action='store_true', help='Modo detalhado')
    parser.add_argument('--version', action='store_true', help='Mostrar versão')
    return parser.parse_args()

class SCDPIChatUniversal:
    def __init__(self, args=None):
        self.args = args or parse_arguments()
        self.config = self.load_config()
        self.socket = None
        self.running = True
        self.current_channel = None
        self.reconnect_attempts = 0  # NOVO: Contador de tentativas de reconexão
        self.max_reconnect_attempts = 5  # NOVO: Máximo de tentativas
        self.joined_channels = set(self.config['channels'])  # NOVO: Rastrear canais ativos

    def load_config(self):
        """Carrega configuração com fallback para interativa"""
        if self.args.config:
            config_path = Path(self.args.config)
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"{Colors.RED}❌ Erro no arquivo de configuração: {e}{Colors.RESET}")
                    sys.exit(1)
        
        # Tenta carregar configuração padrão
        config_path = get_default_config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"{Colors.YELLOW}⚠️ Configuração padrão não encontrada, criando nova...{Colors.RESET}")
        
        # Se --nick foi fornecido, usar ele
        if self.args.nick:
            return self.create_minimal_config(self.args.nick)
        
        # Modo interativo
        return get_user_configuration()
    
    def create_minimal_config(self, nickname):
        """Cria configuração mínima com nickname"""
        return {
            "nickname": nickname,
            "channels": [self.args.channel or "#scdpi-test"],
            "server": self.args.server or "irc.libera.chat",
            "port": self.args.port or 6697,
            "use_ssl": not self.args.no_ssl,
            "realname": f"{nickname} User",
            "server_password": ""
        }
    
    def print_banner(self):
        """Exibe banner centralizado"""
        terminal_width = os.get_terminal_size().columns
        padding = (terminal_width - 50) // 2
        
        print(f"{Colors.BOLD}{Colors.CYAN}")
        print(" " * padding + "╔══════════════════════════════════════════╗")
        print(" " * padding + "║           SCDPI CHAT v2.3                ║")
        print(" " * padding + "║      Cliente IRC Multiplataforma         ║")
        print(" " * padding + "╚══════════════════════════════════════════╝")
        print(f"{Colors.RESET}")
        
        print(f"{Colors.YELLOW}📡 Conectando: {self.config['server']}:{self.config['port']}")
        print(f"👤 Nickname: {self.config['nickname']}")
        print(f"📺 Canais: {', '.join(self.config['channels'])}")
        print(f"💡 Comandos: /help para ajuda{Colors.RESET}")
        print("─" * terminal_width)
    
    def clear_screen(self):
        """Limpa a tela de forma multiplataforma"""
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')
    
    def connect(self):
        """Conecta ao servidor IRC"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            
            if self.config.get('use_ssl', True):
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.socket = context.wrap_socket(sock, server_hostname=self.config['server'])
            else:
                self.socket = sock
                print(f"{Colors.YELLOW}⚠️  Conexão não criptografada!{Colors.RESET}")
            
            print(f"{Colors.BLUE}🔗 Conectando a {self.config['server']}:{self.config['port']}...{Colors.RESET}")
            self.socket.connect((self.config['server'], self.config['port']))
            
            if self.config.get('server_password'):
                self.send(f"PASS {self.config['server_password']}\r\n")
            
            self.send(f"USER {self.config['nickname']} 0 * :{self.config['realname']}\r\n")
            self.send(f"NICK {self.config['nickname']}\r\n")
            
            print(f"{Colors.GREEN}✅ Conectado! Digite /help para ajuda{Colors.RESET}")
            self.reconnect_attempts = 0  # NOVO: Resetar contador de reconexão
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro de conexão: {e}{Colors.RESET}")
            return False
    
    def send(self, message):
        """Envia mensagem para o servidor"""
        try:
            self.socket.send(message.encode('utf-8'))
            if self.args.verbose:
                print(f"{Colors.YELLOW}📤 Enviado: {message.strip()}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao enviar: {e}{Colors.RESET}")
            self.running = False
    
    def receive(self):
        """Recebe dados do servidor"""
        try:
            self.socket.settimeout(0.5)
            data = self.socket.recv(4096).decode('utf-8', errors='ignore').strip()
            return data
        except socket.timeout:
            return None
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao receber: {e}{Colors.RESET}")
            return None

    def handle_message(self, data):
        """Processa mensagens do servidor"""
        if not data:
            return
        
        # Adicionar timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # ✅✅✅ CORREÇÃO CRÍTICA - RESPONDER PING IMEDIATAMENTE!
        if data.startswith("PING"):
            pong_response = data.replace("PING", "PONG")
            self.send(pong_response)
            if self.args.verbose:
                print(f"{Colors.GREEN}✅ [{timestamp}] PONG enviado: {pong_response}{Colors.RESET}")
            return
        
        # ✅ Filtrar mensagens técnicas que quebram a interface
        technical_patterns = ["CHANMODES", "MAXLIST", "TARGMAX", "PREFIX", "MODES", 
                             "NETWORK", "CASEMAPPING", "NICKLEN", "CHANNELLEN"]
        if any(pattern in data for pattern in technical_patterns):
            if self.args.verbose:
                print(f"{Colors.YELLOW}⚡ [{timestamp}] [Ignorado] {data}{Colors.RESET}")
            return
        
        # Mensagem de usuário
        if "PRIVMSG" in data:
            try:
                parts = data.split(' ', 3)
                sender = parts[0][1:].split('!')[0]
                target = parts[2]
                message = parts[3][1:] if parts[3].startswith(':') else parts[3]
                
                if target == self.config['nickname']:
                    # Mensagem privada
                    print(f"{Colors.MAGENTA}[{timestamp}] ✉️ {sender}: {message}{Colors.RESET}")
                else:
                    # Mensagem em canal
                    print(f"{Colors.CYAN}[{timestamp}] <{sender}@{target}> {Colors.WHITE}{message}{Colors.RESET}")
                    self.current_channel = target
                    
            except (IndexError, ValueError):
                if self.args.verbose:
                    print(f"{Colors.YELLOW}⚡ [{timestamp}] {data}{Colors.RESET}")
        
        # Outras mensagens importantes
        elif "001" in data:  # Welcome
            print(f"{Colors.GREEN}[{timestamp}] ✅ Conectado ao servidor!{Colors.RESET}")
            for channel in self.config.get('channels', []):
                self.send(f"JOIN {channel}\r\n")
                print(f"{Colors.BLUE}[{timestamp}] 🚪 Entrando em {channel}...{Colors.RESET}")
                self.joined_channels.add(channel)
        
        elif "433" in data:  # Nick em uso
            new_nick = f"{self.config['nickname']}_{os.getpid()}"
            print(f"{Colors.YELLOW}[{timestamp}] ⚠️ Nick em uso, tentando {new_nick}...{Colors.RESET}")
            self.config['nickname'] = new_nick
            self.send(f"NICK {new_nick}\r\n")
        
        elif "PART" in data or "QUIT" in data:
            parts = data.split(' ')
            if len(parts) > 2:
                channel = parts[2]
                if channel in self.joined_channels:
                    self.joined_channels.remove(channel)
                    if channel == self.current_channel:
                        self.current_channel = None
                    print(f"{Colors.BLUE}[{timestamp}] 👋 Saiu de {channel}{Colors.RESET}")
        
        else:
            # Mensagens gerais do servidor
            if self.args.verbose:
                print(f"{Colors.YELLOW}⚡ [{timestamp}] {data}{Colors.RESET}")
    
    def handle_user_input(self):
        """Processa entrada do usuário"""
        try:
            prompt = f"{Colors.GREEN}{self.config['nickname']}"
            if self.current_channel:
                prompt += f"{Colors.WHITE}@{Colors.CYAN}{self.current_channel}"
            prompt += f"{Colors.GREEN}> {Colors.RESET}"
            
            user_input = input(prompt).strip()
            
            if user_input.startswith('/'):
                self.handle_command(user_input[1:])
            elif user_input and self.current_channel:
                self.send(f"PRIVMSG {self.current_channel} :{user_input}\r\n")
                print(f"{Colors.CYAN}[{datetime.now().strftime('%H:%M:%S')}] <{self.config['nickname']}@{self.current_channel}> {Colors.WHITE}{user_input}{Colors.RESET}")
            elif user_input:
                print(f"{Colors.RED}❌ Não está em nenhum canal. Use /join #canal{Colors.RESET}")
                
        except (EOFError, KeyboardInterrupt):
            self.running = False
        except Exception as e:
            print(f"{Colors.RED}❌ Erro no input: {e}{Colors.RESET}")
    
    def handle_command(self, command):
        """Processa comandos do usuário"""
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if cmd == "join" and args:
            if not args.startswith('#'):
                args = '#' + args
            self.send(f"JOIN {args}\r\n")
            self.current_channel = args
            self.joined_channels.add(args)
            print(f"{Colors.BLUE}[{timestamp}] 🚪 Entrando em {args}...{Colors.RESET}")
            
        elif cmd == "part":
            channel = args or self.current_channel
            if channel:
                self.send(f"PART {channel}\r\n")
                print(f"{Colors.BLUE}[{timestamp}] 👋 Saindo de {channel}{Colors.RESET}")
                if channel in self.joined_channels:
                    self.joined_channels.remove(channel)
                if channel == self.current_channel:
                    self.current_channel = None
            else:
                print(f"{Colors.RED}[{timestamp}] ❌ Não está em nenhum canal{Colors.RESET}")
                
        elif cmd == "msg" and args:
            if ' ' in args:
                target, message = args.split(' ', 1)
                self.send(f"PRIVMSG {target} :{message}\r\n")
                print(f"{Colors.MAGENTA}[{timestamp}] ✉️ Para {target}: {message}{Colors.RESET}")
            else:
                print(f"{Colors.RED}[{timestamp}] ❌ Uso: /msg nick mensagem{Colors.RESET}")
                
        elif cmd == "nick" and args:
            if ' ' in args:
                print(f"{Colors.RED}[{timestamp}] ❌ Nickname não pode conter espaços{Colors.RESET}")
                return
            self.send(f"NICK {args}\r\n")
            self.config['nickname'] = args
            print(f"{Colors.GREEN}[{timestamp}] ✅ Nickname alterado para {args}{Colors.RESET}")
            
        elif cmd == "quit":
            self.running = False
            
        elif cmd == "help":
            self.show_help()
            
        elif cmd == "clear":
            self.clear_screen()
            self.print_banner()
            
        elif cmd == "names" and args:
            self.send(f"NAMES {args}\r\n")
            
        elif cmd == "whois" and args:
            self.send(f"WHOIS {args}\r\n")
            
        else:
            print(f"{Colors.RED}[{timestamp}] ❌ Comando desconhecido: {cmd}{Colors.RESET}")
    
    def show_help(self):
        """Mostra ajuda de comandos"""
        terminal_width = os.get_terminal_size().columns
        padding = (terminal_width - 50) // 2
        
        print(f"{Colors.BOLD}{Colors.GREEN}")
        print(" " * padding + "📋 Comandos Disponíveis:")
        print(f"{Colors.RESET}")
        print(f"{Colors.YELLOW}/join #canal    {Colors.WHITE}- Entrar em canal")
        print(f"{Colors.YELLOW}/part [canal]   {Colors.WHITE}- Sair do canal")
        print(f"{Colors.YELLOW}/msg nick msg   {Colors.WHITE}- Mensagem privada")
        print(f"{Colors.YELLOW}/nick novo_nick {Colors.WHITE}- Mudar nickname")
        print(f"{Colors.YELLOW}/names #canal   {Colors.WHITE}- Listar usuários")
        print(f"{Colors.YELLOW}/whois nick     {Colors.WHITE}- Informações do usuário")
        print(f"{Colors.YELLOW}/quit           {Colors.WHITE}- Sair")
        print(f"{Colors.YELLOW}/help           {Colors.WHITE}- Esta ajuda")
        print(f"{Colors.YELLOW}/clear          {Colors.WHITE}- Limpar tela{Colors.RESET}")
    
    def reconnect(self):
        """Tenta reconectar ao servidor em caso de falha"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"{Colors.RED}❌ Máximo de tentativas de reconexão atingido{Colors.RESET}")
            self.running = False
            return False
        
        print(f"{Colors.YELLOW}⚠️ Tentando reconectar... (Tentativa {self.reconnect_attempts + 1}/{self.max_reconnect_attempts}){Colors.RESET}")
        time.sleep(2 ** self.reconnect_attempts)  # Exponential backoff
        self.reconnect_attempts += 1
        if self.connect():
            # Reentrar nos canais
            for channel in self.joined_channels:
                self.send(f"JOIN {channel}\r\n")
                print(f"{Colors.BLUE}🚪 Reentrando em {channel}...{Colors.RESET}")
            return True
        return False
    
    def run(self):
        """Loop principal de execução"""
        if self.args.version:
            print("SCDPI CHAT v2.3 - Cliente IRC com reconexão automática")
            return
            
        self.clear_screen()
        self.print_banner()
        
        if not self.connect():
            print(f"{Colors.RED}❌ Falha na conexão. Verifique:{Colors.RESET}")
            print(f"1. Internet conectada")
            print(f"2. Servidor {self.config['server']} online")
            print(f"3. Porta {self.config['port']} aberta")
            print(f"4. Nickname único")
            return
        
        try:
            while self.running:
                try:
                    data = self.receive()
                    if data:
                        for line in data.split('\r\n'):
                            if line.strip():
                                self.handle_message(line)
                    else:
                        # Verificar conexão
                        self.send("PING :keepalive\r\n")
                        
                    self.handle_user_input()
                    time.sleep(0.1)
                    
                except (ConnectionResetError, BrokenPipeError, OSError):
                    print(f"{Colors.RED}❌ Conexão perdida!{Colors.RESET}")
                    if not self.reconnect():
                        break
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Desconectando...{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro crítico: {e}{Colors.RESET}")
        finally:
            if self.socket:
                try:
                    self.send("QUIT :SCDPI CHAT saindo\r\n")
                    self.socket.close()
                except:
                    pass
            print(f"{Colors.GREEN}✅ Conexão encerrada{Colors.RESET}")

def main():
    """Função principal"""
    args = parse_arguments()
    chat = SCDPIChatUniversal(args)
    chat.run()

if __name__ == "__main__":
    main()
