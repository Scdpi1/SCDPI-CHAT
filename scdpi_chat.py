#!/usr/bin/env python3
"""
SCDPI CHAT - Cliente IRC Universal Multiplataforma
Versão 2.1 - Modo Interativo como irssi
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

# Configuração de cores para terminal
class Colors:
    if platform.system() == "Windows":
        # No Windows, desativar cores se não suportado
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
        # Unix/Linux/Termux
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'
        BOLD = '\033[1m'

def get_interactive_config():
    """Obtém configuração interativa como irssi"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("🔧 Configuração Rápida (estilo irssi)")
    print("=" * 50)
    print(f"{Colors.RESET}")
    
    nickname = input(f"{Colors.YELLOW}Nickname [{Colors.WHITE}scdpi-user{Colors.YELLOW}]: {Colors.RESET}") or "scdpi-user"
    channel = input(f"{Colors.YELLOW}Canal [{Colors.WHITE}#scdpi{Colors.YELLOW}]: {Colors.RESET}") or "#scdpi"
    server = input(f"{Colors.YELLOW}Servidor [{Colors.WHITE}irc.libera.chat{Colors.YELLOW}]: {Colors.RESET}") or "irc.libera.chat"
    port = input(f"{Colors.YELLOW}Porta [{Colors.WHITE}6697{Colors.YELLOW}]: {Colors.RESET}") or "6697"
    use_ssl = input(f"{Colors.YELLOW}Usar SSL? (s/n) [{Colors.WHITE}s{Colors.YELLOW}]: {Colors.RESET}") or "s"
    
    return {
        "server": server,
        "port": int(port),
        "use_ssl": use_ssl.lower() == 's',
        "nickname": nickname,
        "realname": f"{nickname} User",
        "channels": [channel],
        "server_password": "",
        "notification_settings": {
            "enable_mentions": True,
            "enable_private_messages": True
        }
    }

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='SCDPI CHAT - Cliente IRC com Notificações')
    parser.add_argument('--config', help='Arquivo de configuração personalizado')
    parser.add_argument('--nick', help='Nickname para usar')
    parser.add_argument('--channel', help='Canal para entrar')
    parser.add_argument('--server', help='Servidor IRC')
    parser.add_argument('--port', type=int, help='Porta do servidor')
    parser.add_argument('--no-ssl', action='store_true', help='Não usar SSL')
    parser.add_argument('--verbose', action='store_true', help='Modo verbose')
    parser.add_argument('--version', action='store_true', help='Mostrar versão')
    return parser.parse_args()

class SCDPIChatUniversal:
    def __init__(self, args=None):
        self.args = args or parse_arguments()
        self.config = self.load_config()
        self.socket = None
        self.running = True
        self.current_channel = None
        
    def get_config_path(self):
        """Retorna o path correto do config baseado no SO"""
        system = platform.system()
        
        if system == "Windows":
            return Path(os.environ['APPDATA']) / "SCDPI" / "config.json"
        elif "TERMUX" in os.environ:
            return Path.home() / ".config" / "scdpi" / "config.json"
        else:  # Linux/Mac
            return Path.home() / ".config" / "scdpi" / "config.json"
    
    def load_config(self):
        """Carrega configuração com fallback para interativa"""
        # Se --config foi especificado, usar esse arquivo
        if self.args.config:
            config_path = Path(self.args.config)
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    print(f"{Colors.RED}❌ Erro no arquivo de configuração: {config_path}{Colors.RESET}")
                    sys.exit(1)
            else:
                print(f"{Colors.RED}❌ Arquivo de configuração não encontrado: {config_path}{Colors.RESET}")
                sys.exit(1)
        
        config_path = self.get_config_path()
        
        # Criar diretório se não existir
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if self.args.verbose:
                    print(f"{Colors.GREEN}✅ Configuração carregada de {config_path}{Colors.RESET}")
                
                return config
            except (json.JSONDecodeError, IOError):
                print(f"{Colors.RED}❌ Erro no config, usando modo interativo{Colors.RESET}")
        
        # Modo interativo como irssi
        print(f"{Colors.YELLOW}⚡ Arquivo de configuração não encontrado.{Colors.RESET}")
        print(f"{Colors.YELLOW}⚡ Iniciando modo interativo (estilo irssi)...{Colors.RESET}")
        
        config = get_interactive_config()
        
        # Salvar configuração para próxima vez
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # Proteger arquivo no Unix
            if platform.system() != "Windows":
                config_path.chmod(0o600)
                
            if self.args.verbose:
                print(f"{Colors.GREEN}✅ Configuração salva em {config_path}{Colors.RESET}")
        except IOError as e:
            print(f"{Colors.YELLOW}⚠️  Não foi possível salvar configuração: {e}{Colors.RESET}")
        
        return config
    
    def print_banner(self):
        """Exibe banner bonito"""
        print(f"{Colors.BOLD}{Colors.CYAN}")
        print("╔══════════════════════════════════════════╗")
        print("║           SCDPI CHAT v2.1               ║")
        print("║      Cliente IRC - Modo Interativo      ║")
        print("╚══════════════════════════════════════════╝")
        print(f"{Colors.RESET}")
        print(f"{Colors.YELLOW}📡 Conectando: {self.config['server']}:{self.config['port']}")
        print(f"👤 Nickname: {self.config['nickname']}")
        print(f"📺 Canal: {self.config['channels'][0]}")
        print(f"💡 Comandos: /help para ajuda{Colors.RESET}")
        print("─" * 50)
    
    def clear_screen(self):
        """Limpa a tela de forma multiplataforma"""
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')
    
    def connect(self):
        """Conecta ao servidor IRC de forma robusta"""
        try:
            # Aplicar argumentos de linha de comando
            if self.args.nick:
                self.config['nickname'] = self.args.nick
            if self.args.channel:
                self.config['channels'] = [self.args.channel]
            if self.args.server:
                self.config['server'] = self.args.server
            if self.args.port:
                self.config['port'] = self.args.port
            if self.args.no_ssl:
                self.config['use_ssl'] = False
            
            # Criar socket básico
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)  # Timeout de 10 segundos
            
            if self.config.get('use_ssl', True):
                context = ssl.create_default_context()
                # Para compatibilidade, verificação mais relaxada
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.socket = context.wrap_socket(sock, server_hostname=self.config['server'])
            else:
                self.socket = sock
                print(f"{Colors.YELLOW}⚠️  Conexão NÃO criptografada!{Colors.RESET}")
            
            # Conectar
            print(f"{Colors.BLUE}🔗 Conectando a {self.config['server']}:{self.config['port']}...{Colors.RESET}")
            self.socket.connect((self.config['server'], self.config['port']))
            
            # Autenticação
            if self.config.get('server_password'):
                self.send(f"PASS {self.config['server_password']}\r\n")
            
            # Enviar credenciais
            self.send(f"USER {self.config['nickname']} 0 * :{self.config['realname']}\r\n")
            self.send(f"NICK {self.config['nickname']}\r\n")
            
            print(f"{Colors.GREEN}✅ Conectado! Digite /help para ajuda{Colors.RESET}")
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ Erro de conexão: {e}{Colors.RESET}")
            return False
    
    def send(self, message):
        """Envia mensagem para o servidor"""
        try:
            self.socket.send(message.encode('utf-8'))
        except Exception as e:
            print(f"{Colors.RED}❌ Erro ao enviar: {e}{Colors.RESET}")
            self.running = False
    
    def receive(self):
        """Recebe dados do servidor com timeout"""
        try:
            self.socket.settimeout(0.5)  # Timeout não-bloqueante
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
        
        # Responder PING
        if data.startswith("PING"):
            self.send(data.replace("PING", "PONG"))
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
                    print(f"{Colors.MAGENTA}✉️ {sender}: {message}{Colors.RESET}")
                else:
                    # Mensagem em canal
                    print(f"{Colors.CYAN}<{sender}> {Colors.WHITE}{message}{Colors.RESET}")
                    self.current_channel = target
                    
            except (IndexError, ValueError):
                print(f"{Colors.YELLOW}⚡ {data}{Colors.RESET}")
        
        # Outras mensagens importantes
        elif "001" in data:  # Welcome
            print(f"{Colors.GREEN}✅ Conectado ao servidor!{Colors.RESET}")
            for channel in self.config.get('channels', []):
                self.send(f"JOIN {channel}\r\n")
                print(f"{Colors.BLUE}🚪 Entrando em {channel}...{Colors.RESET}")
        
        elif "433" in data:  # Nick em uso
            new_nick = f"{self.config['nickname']}_{os.getpid()}"
            print(f"{Colors.YELLOW}⚠️ Nick em uso, tentando {new_nick}...{Colors.RESET}")
            self.config['nickname'] = new_nick
            self.send(f"NICK {new_nick}\r\n")
        
        else:
            # Mensagens gerais do servidor
            if self.args.verbose:
                print(f"{Colors.YELLOW}⚡ {data}{Colors.RESET}")
    
    def handle_user_input(self):
        """Processa entrada do usuário de forma segura"""
        try:
            # Prompt colorido
            prompt = f"{Colors.GREEN}{self.config['nickname']}"
            if self.current_channel:
                prompt += f"{Colors.WHITE}@{Colors.CYAN}{self.current_channel}"
            prompt += f"{Colors.GREEN}> {Colors.RESET}"
            
            user_input = input(prompt).strip()
            
            if user_input.startswith('/'):
                self.handle_command(user_input[1:])
            elif user_input and self.current_channel:
                self.send(f"PRIVMSG {self.current_channel} :{user_input}\r\n")
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
        
        if cmd == "join" and args:
            if not args.startswith('#'):
                args = '#' + args
            self.send(f"JOIN {args}\r\n")
            self.current_channel = args
            print(f"{Colors.BLUE}🚪 Entrando em {args}...{Colors.RESET}")
            
        elif cmd == "part":
            channel = args or self.current_channel
            if channel:
                self.send(f"PART {channel}\r\n")
                print(f"{Colors.BLUE}👋 Saindo de {channel}{Colors.RESET}")
                if channel == self.current_channel:
                    self.current_channel = None
            else:
                print(f"{Colors.RED}❌ Não está em nenhum canal{Colors.RESET}")
                
        elif cmd == "msg" and args:
            if ' ' in args:
                target, message = args.split(' ', 1)
                self.send(f"PRIVMSG {target} :{message}\r\n")
                print(f"{Colors.MAGENTA}✉️ Para {target}: {message}{Colors.RESET}")
            else:
                print(f"{Colors.RED}❌ Uso: /msg nick mensagem{Colors.RESET}")
                
        elif cmd == "nick" and args:
            self.send(f"NICK {args}\r\n")
            self.config['nickname'] = args
            print(f"{Colors.GREEN}✅ Nickname alterado para {args}{Colors.RESET}")
            
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
            print(f"{Colors.RED}❌ Comando desconhecido: {cmd}{Colors.RESET}")
    
    def show_help(self):
        """Mostra ajuda de comandos"""
        print(f"{Colors.BOLD}{Colors.GREEN}📋 Comandos Disponíveis:{Colors.RESET}")
        print(f"{Colors.YELLOW}/join #canal    {Colors.WHITE}- Entrar em canal")
        print(f"{Colors.YELLOW}/part [canal]   {Colors.WHITE}- Sair do canal")
        print(f"{Colors.YELLOW}/msg nick msg   {Colors.WHITE}- Mensagem privada")
        print(f"{Colors.YELLOW}/nick novo_nick {Colors.WHITE}- Mudar nickname")
        print(f"{Colors.YELLOW}/names #canal   {Colors.WHITE}- Listar usuários")
        print(f"{Colors.YELLOW}/whois nick     {Colors.WHITE}- Informações do usuário")
        print(f"{Colors.YELLOW}/quit           {Colors.WHITE}- Sair")
        print(f"{Colors.YELLOW}/help           {Colors.WHITE}- Esta ajuda")
        print(f"{Colors.YELLOW}/clear          {Colors.WHITE}- Limpar tela{Colors.RESET}")
    
    def run(self):
        """Loop principal de execução"""
        if self.args.version:
            print("SCDPI CHAT v2.1 - Modo Interativo")
            return
            
        self.clear_screen()
        self.print_banner()
        
        if not self.connect():
            print(f"{Colors.RED}❌ Falha na conexão. Verifique:\n")
            print(f"1. Internet conectada")
            print(f"2. Servidor {self.config['server']} online")
            print(f"3. Porta {self.config['port']} aberta")
            print(f"4. Nickname único{Colors.RESET}")
            return
        
        # Loop principal
        try:
            while self.running:
                # Verificar mensagens do servidor
                data = self.receive()
                if data:
                    for line in data.split('\r\n'):
                        if line.strip():
                            self.handle_message(line)
                
                # Verificar input do usuário
                self.handle_user_input()
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Desconectando...{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Erro crítico: {e}{Colors.RESET}")
        finally:
            # Limpeza final
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
