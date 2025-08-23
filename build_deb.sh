#!/bin/bash
# Script de construção do pacote DEB

PACKAGE_NAME="scdpi-chat"
VERSION="1.0.0"
ARCH="all"
DEB_DIR="scdpi-chat-deb"

echo "🔨 Construindo pacote DEB..."

# Verificar se a estrutura existe
if [ ! -d "$DEB_DIR" ]; then
    echo "❌ Diretório $DEB_DIR não encontrado!"
    exit 1
fi

# Verificar e corrigir permissões
echo "📋 Verificando permissões..."
chmod -R 755 "$DEB_DIR/DEBIAN"
chmod 644 "$DEB_DIR/DEBIAN/control"
chmod 644 "$DEB_DIR/DEBIAN/md5sums" 2>/dev/null || true

# Verificar scripts individualmente
[ -f "$DEB_DIR/DEBIAN/postinst" ] && chmod 755 "$DEB_DIR/DEBIAN/postinst"
[ -f "$DEB_DIR/DEBIAN/prerm" ] && chmod 755 "$DEB_DIR/DEBIAN/prerm"
[ -f "$DEB_DIR/DEBIAN/preinst" ] && chmod 755 "$DEB_DIR/DEBIAN/preinst"
[ -f "$DEB_DIR/DEBIAN/postrm" ] && chmod 755 "$DEB_DIR/DEBIAN/postrm"

# Verificar estrutura
echo "🏗️  Verificando estrutura..."
if [ ! -f "$DEB_DIR/DEBIAN/control" ]; then
    echo "❌ Arquivo control não encontrado!"
    exit 1
fi

# Construir pacote
echo "📦 Construindo pacote..."
dpkg-deb --build "$DEB_DIR"

if [ $? -eq 0 ]; then
    # Renomear
    mv "${DEB_DIR}.deb" "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    
    echo "✅ Pacote construído com sucesso!"
    echo "📦 Arquivo: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    
    # Verificar pacote
    echo "🔍 Verificando pacote..."
    dpkg -I "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    
    # Verificar conteúdo
    echo "📁 Conteúdo do pacote:"
    dpkg -c "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
else
    echo "❌ Erro ao construir pacote!"
    exit 1
fi
