#!/bin/bash
# VPS Deployment Script for Martina Schedule Bot

echo "🚀 Setting up Martina Schedule Bot on VPS..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /opt/martina-bot
sudo chown $USER:$USER /opt/martina-bot

# Clone or copy your code
echo "📋 Setting up application code..."
cd /opt/martina-bot

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service files
echo "⚙️ Creating systemd services..."

# Admin Bot Service
sudo tee /etc/systemd/system/martina-admin-bot.service > /dev/null <<EOF
[Unit]
Description=Martina Admin Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/martina-bot
Environment=PATH=/opt/martina-bot/venv/bin
ExecStart=/opt/martina-bot/venv/bin/python bot_async.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Staff Bot Service
sudo tee /etc/systemd/system/martina-staff-bot.service > /dev/null <<EOF
[Unit]
Description=Martina Staff Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/martina-bot
Environment=PATH=/opt/martina-bot/venv/bin
ExecStart=/opt/martina-bot/venv/bin/python staff_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Web Server Service
sudo tee /etc/systemd/system/martina-web-server.service > /dev/null <<EOF
[Unit]
Description=Martina Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/martina-bot
Environment=PATH=/opt/martina-bot/venv/bin
ExecStart=/opt/martina-bot/venv/bin/python web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
echo "🚀 Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable martina-admin-bot
sudo systemctl enable martina-staff-bot
sudo systemctl enable martina-web-server

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set environment variables in /opt/martina-bot/.env"
echo "2. Start services: sudo systemctl start martina-*-bot martina-web-server"
echo "3. Check status: sudo systemctl status martina-*"
echo "4. View logs: sudo journalctl -u martina-admin-bot -f" 