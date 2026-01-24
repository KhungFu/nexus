#!/bin/bash

# Nexus Capital Corp - One Click Installer
echo "🏛️ Initialisiere Nexus Capital Corp Installation..."

# 1. Python venv erstellen
echo "📦 Erstelle virtuelle Umgebung..."
python3 -m venv venv
source venv/bin/activate

# 2. Abhängigkeiten installieren
echo "📥 Installiere Python-Abhängigkeiten..."
pip install --upgrade pip
pip install -r requirements.txt

# 3. .env Vorlage erstellen (falls nicht vorhanden)
if [ ! -f .env ]; then
    echo "📝 Erstelle .env Vorlage..."
    cat <<EOT >> .env
# CAPITAL.COM API
CAPITAL_API_KEY=dein_api_key
CAPITAL_IDENTIFIER=deine_email
CAPITAL_PASSWORD=dein_passwort

# TELEGRAM BOT
TELEGRAM_TOKEN=dein_bot_token
TELEGRAM_USER_ID=deine_chat_id

# GEMINI KI
GEMINI_API_KEY_1=dein_gemini_key_1
GEMINI_API_KEY_2=
GEMINI_API_KEY_3=
EOT
    echo "⚠️ BITTE BEARBEITE DIE .env DATEI UND FÜGE DEINE KEYS EIN!"
fi

# 4. Ordnerstruktur prüfen
echo "📂 Prüfe Dateistruktur..."
touch mentor_name.txt
touch error_log.json

echo "✅ Installation abgeschlossen."
echo "🚀 Starte den Bot mit: source venv/bin/activate && python nexus_ceo.py"
