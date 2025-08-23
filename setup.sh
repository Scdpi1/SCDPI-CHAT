#!/bin/bash
# SCDPI CHAT - Instalador Universal
# Uso: curl -sL https://bit.ly/scdpi-chat | bash

echo "🔄 Baixando SCDPI CHAT..."
git clone https://github.com/seu-usuario/SCDPI-CHAT.git ~/.scdpi-chat

echo "📦 Instalando dependências..."
cd ~/.scdpi-chat

# Verifica se é Termux
if [ -d "/data/data/com.termux" ]; then
    pkg install python git openssl -y
else
    # Linux normal
    sudo apt-get update
    sudo apt-get install python3 python3-pip git openssl -y
fi

echo "🔧 Configurando..."
python3 -m pip install requests cryptography

echo "🎯 Criando link simbólico..."
sudo ln -sf ~/.scdpi-chat/scdpi_chat.py /usr/local/bin/scdpi-chat
sudo chmod +x /usr/local/bin/scdpi-chat

echo "📝 Configurando arquivo de configuração..."
mkdir -p ~/.config/scdpi
cp ~/.scdpi-chat/config_example.json ~/.config/scdpi/config.json
chmod 600 ~/.config/scdpi/config.json

echo "✅ Instalação concluída!"
echo " "
echo "🚀 Para usar: scdpi-chat"
echo "⚙️  Configure: nano ~/.config/scdpi/config.json"
