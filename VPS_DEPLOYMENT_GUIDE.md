# 🚀 VPS Deployment Guide - Martina Schedule Bot

## 🎯 **Why VPS is Better Than Render**

- ✅ **No threading restrictions**
- ✅ **Full process control**
- ✅ **Better performance**
- ✅ **More reliable**
- ✅ **Easier debugging**
- ✅ **Cost-effective**

## 📋 **Step-by-Step VPS Setup**

### **Step 1: Get a VPS**

**Recommended: DigitalOcean**
1. Go to [digitalocean.com](https://digitalocean.com)
2. Create account and add payment method
3. Create a new droplet:
   - **Distribution**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($5-10/month)
   - **Datacenter**: Choose closest to you
   - **Authentication**: SSH key (recommended) or password

### **Step 2: Connect to Your VPS**

```bash
# SSH into your VPS
ssh root@your_server_ip

# Create a new user (optional but recommended)
adduser martina
usermod -aG sudo martina
su - martina
```

### **Step 3: Deploy Your Application**

```bash
# Clone your repository
git clone https://github.com/imaanFarasat/martina-schedule.git
cd martina-schedule

# Make deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

### **Step 4: Configure Environment Variables**

```bash
# Copy environment template
cp env.example .env

# Edit with your actual values
nano .env
```

**Fill in your .env file:**
```bash
BOT_TOKEN=7599431109:AAGE2tue6LaZLpRr1sIkWziO6cpR_N88px8
STAFF_BOT_TOKEN=7808288730:AAHHYFW4FBJ8TVOKYk5M79QMEaGYjc7eTRs
ADMIN_IDS=6830394970,7936434438
DATABASE_PATH=/opt/martina-bot/shared_scheduler.db
PORT=10000
```

### **Step 5: Start Your Services**

```bash
# Start all services
sudo systemctl start martina-admin-bot
sudo systemctl start martina-staff-bot
sudo systemctl start martina-web-server

# Check status
sudo systemctl status martina-admin-bot
sudo systemctl status martina-staff-bot
sudo systemctl status martina-web-server
```

### **Step 6: Test Your Bots**

1. **Test Admin Bot**: Send `/start` to your admin bot
2. **Test Staff Bot**: Send `/start` to your staff bot
3. **Test Web Server**: Visit `http://your_server_ip:10000`

## 🔧 **Management Commands**

### **Service Management**
```bash
# Start services
sudo systemctl start martina-admin-bot
sudo systemctl start martina-staff-bot
sudo systemctl start martina-web-server

# Stop services
sudo systemctl stop martina-admin-bot
sudo systemctl stop martina-staff-bot
sudo systemctl stop martina-web-server

# Restart services
sudo systemctl restart martina-admin-bot
sudo systemctl restart martina-staff-bot
sudo systemctl restart martina-web-server

# Check status
sudo systemctl status martina-*
```

### **View Logs**
```bash
# View admin bot logs
sudo journalctl -u martina-admin-bot -f

# View staff bot logs
sudo journalctl -u martina-staff-bot -f

# View web server logs
sudo journalctl -u martina-web-server -f
```

### **Update Your Application**
```bash
# Pull latest changes
cd /opt/martina-bot
git pull

# Install new dependencies (if any)
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart martina-*
```

## 🔒 **Security Setup (Optional)**

### **Firewall Configuration**
```bash
# Allow SSH, HTTP, and your bot port
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 10000
sudo ufw enable
```

### **SSL Certificate (Optional)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 📊 **Monitoring**

### **Check Resource Usage**
```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Service status
sudo systemctl status martina-*
```

### **Database Backup**
```bash
# Backup database
cp /opt/martina-bot/shared_scheduler.db /opt/martina-bot/backup_$(date +%Y%m%d).db

# Restore database
cp /opt/martina-bot/backup_20250123.db /opt/martina-bot/shared_scheduler.db
```

## 🆘 **Troubleshooting**

### **Common Issues**

**Service won't start:**
```bash
# Check logs
sudo journalctl -u martina-admin-bot -n 50

# Check environment variables
cat /opt/martina-bot/.env
```

**Bot not responding:**
```bash
# Check if bot is running
sudo systemctl status martina-admin-bot

# Check logs for errors
sudo journalctl -u martina-admin-bot -f
```

**Database issues:**
```bash
# Check database file
ls -la /opt/martina-bot/shared_scheduler.db

# Check permissions
sudo chown martina:martina /opt/martina-bot/shared_scheduler.db
```

## 💰 **Cost Comparison**

| Platform | Monthly Cost | Features |
|----------|-------------|----------|
| **Render** | $0 (Free tier) | Limited, unreliable |
| **VPS** | $5-10 | Full control, reliable |
| **AWS Lambda** | $1-5 | Serverless, complex |
| **Railway** | $5-20 | Easy, good features |

## 🎉 **Benefits of VPS Migration**

- ✅ **No more threading issues**
- ✅ **Stable, reliable operation**
- ✅ **Full control over environment**
- ✅ **Better performance**
- ✅ **Easier debugging**
- ✅ **Cost-effective long-term**

---

**Ready to migrate?** Follow the steps above and enjoy a stable, reliable bot system! 🚀 