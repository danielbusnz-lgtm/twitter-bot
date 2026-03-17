#!/bin/bash
# deploy.sh — set up twitter-bot on a fresh Ubuntu droplet
#
# Usage: ./deploy.sh <server_ip>
# Example: ./deploy.sh 45.55.121.238
#
# Requires sshpass: sudo apt-get install -y sshpass
# Requires a .env file in the same directory as this script

set -e

IP=$1
if [ -z "$IP" ]; then
    echo "Usage: ./deploy.sh <server_ip>"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Enter root password for $IP:"
read -s PASSWORD

echo ""
echo "Deploying to $IP..."

run() {
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no root@$IP "$1"
}

copy() {
    sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no "$1" root@$IP:"$2"
}

# Install deps
echo "[1/5] Installing system packages..."
run "apt-get update -y -q && apt-get install -y -q python3 python3-pip python3-venv git"

# Clone repo
echo "[2/5] Cloning repo..."
run "git clone https://github.com/danielbusnz-lgtm/twitter-bot.git ~/twitter-bot 2>/dev/null || (cd ~/twitter-bot && git pull)"

# Python venv + deps
echo "[3/5] Installing Python dependencies..."
run "cd ~/twitter-bot && python3 -m venv venv && venv/bin/pip install -q tweepy anthropic python-dotenv requests"

# Copy .env
echo "[4/5] Copying .env..."
copy "$SCRIPT_DIR/.env" "/root/twitter-bot/.env"

# Set up cron
echo "[5/5] Setting up cron..."
CRON="*/30 * * * * cd /root/twitter-bot && /root/twitter-bot/venv/bin/python3 /root/twitter-bot/auto_tweet.py >> /root/twitter-bot/cron.log 2>&1"
run "(crontab -l 2>/dev/null | grep -v auto_tweet; echo '$CRON') | crontab -"

# Test run
echo ""
echo "Testing..."
run "cd /root/twitter-bot && venv/bin/python3 auto_tweet.py"

echo ""
echo "Done. Bot is live on $IP."
echo "Check logs: ssh root@$IP 'tail -f /root/twitter-bot/cron.log'"
