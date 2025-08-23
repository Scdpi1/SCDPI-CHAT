#!/usr/bin/env python3
"""
Instalador Automático SCDPI CHAT - Multiplataforma
"""
import os
import sys
import platform
from pathlib import Path

def run_command(command):
    """Executa comando de forma segura"""
    try:
        if platform.system() == "Windows":
            os.system(command)
        else:
            os.system(command)
        return True
    except:
        return False

def install_dependencies():
    """Instala dependências específicas por plataforma"""
    system = platform.system()
    
    print("🔧 Instalando dependências...")
    
    if system == "Windows":
        # Windows
        run_command("pip install requests cryptography")
        # Tentar instalar colorama para cores no Windows
        run_command("pip install colorama")
        
    elif "TERMUX" in os.environ:
        # Termux (Android)
        run_command("pkg install python -y")
        run_command("pip install requests cryptography")
        
    else:
        # Linux/Mac
        if run_command("which apt-get > /dev/null 2>&1"):
            # Debian/Ubuntu
            run_command("sudo apt-get update")
            run_command("sudo apt-get install python3 python3-pip -y")
        elif run_command("which yum > /dev/null 2>&1"):
            # RedHat/CentOS
            run_command("sudo yum install python3 python3-pip -y")
        elif run_command("which brew > /dev/null 2>&1"):
            # macOS
            run_command("brew install python3")
        
        run_command("pip3 install requests cryptography")
    
    return True

def setup_directories():
    """Configura diretórios necessários"""
    system = platform.system()
    
    print("📁 Configurando diretórios...")
    
    if system == "Windows":
        config_dir = Path(os.environ['APPDATA']) / "SCDPI"
    else:
        config_dir = Path.home() / ".config" / "scdpi"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Criar arquivo de configuração padrão se não existir
    config_file = config_dir / "config.json"
    if not config_file.exists():
        default_config = {
            "server": "irc.libera.chat",
            "port": 6697,
            "use_ssl": True,
            "nickname": "SCDPI-User",
            "realname": "SCDPI CHAT User",
            "channels": ["#scdpi-test"],
            "server_password": "",
            "notification_settings": {
                "enable_mentions": True,
                "enable_private_messages": True
            }
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            
            # Proteger arquivo no Unix
            if system != "Windows":
                config_file.chmod(0o600)
                
            print("✅ Arquivo de configuração criado")
            
        except Exception as e:
            print(f"❌ Erro ao criar config: {e}")
    
    return True

def main():
    """Função principal de instalação"""
    print("🚀 Instalador SCDPI CHAT Universal")
    print("=" * 50)
    
    # Verificar Python
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ é necessário")
        return False
    
    # Instalar dependências
    if not install_dependencies():
        print("❌ Erro ao instalar dependências")
        return False
    
    # Configurar diretórios
    if not setup_directories():
        print("❌ Erro ao configurar diretórios")
        return False
    
    print("=" * 50)
    print("✅ Instalação concluída com sucesso!")
    print("\n📝 Próximos passos:")
    print("1. Edite o arquivo de configuração:")
    
    system = platform.system()
    if system == "Windows":
        config_path = Path(os.environ['APPDATA']) / "SCDPI" / "config.json"
        print(f"   Notepad: {config_path}")
    else:
        config_path = Path.home() / ".config" / "scdpi" / "config.json"
        print(f"   nano {config_path}")
    
    print("\n2. Execute: python scdpi_chat.py")
    print("3. Configure seu nickname único e canais")
    print("\n💡 Dica: Altere pelo menos 'nickname' no config!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
