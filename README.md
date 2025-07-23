# Martina Schedule Bot - VPS Deployment

A Telegram bot system for managing staff schedules and appointments, deployed on VPS for maximum reliability.

## 🚀 VPS Deployment

**For detailed deployment instructions, see [VPS_DEPLOYMENT_GUIDE.md](VPS_DEPLOYMENT_GUIDE.md)**

### Quick Setup:
1. **Get a VPS** (DigitalOcean recommended - $5/month)
2. **Clone this repository** to your VPS
3. **Run deployment script**: `./deploy.sh`
4. **Configure environment**: Copy `env.example` to `.env`
5. **Start services**: `sudo systemctl start martina-*`

## 📋 Features

- 👥 **Staff Management** (Add/Remove staff)
- 📅 **Schedule Management** (Set weekly schedules)
- 👀 **View Current Schedules**
- 📄 **Export PDF Reports**
- 📚 **Schedule History**
- 🗑️ **Reset All Schedules**
- 🔄 **Automatic Restarts**
- 📊 **System Monitoring**

## 🔧 Environment Variables

Create a `.env` file with:
```bash
BOT_TOKEN=your_admin_bot_token_here
STAFF_BOT_TOKEN=your_staff_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_PATH=/opt/martina-bot/shared_scheduler.db
PORT=10000
```

## 📁 Project Structure

- `bot_async.py` - Admin bot logic
- `staff_bot.py` - Staff bot logic
- `web_server.py` - Web server for health checks
- `config.py` - Configuration settings
- `database.py` - Database operations
- `pdf_generator.py` - PDF report generation
- `validators.py` - Input validation
- `deploy.sh` - VPS deployment script

## 🎯 Usage

### Admin Bot:
1. Send `/start` to your admin bot
2. Use inline keyboard to manage schedules
3. Only authorized admins can access

### Staff Bot:
1. Staff members send `/start` to staff bot
2. View their current schedules
3. Get notifications about changes

## 🔧 Management Commands

```bash
# Check service status
sudo systemctl status martina-*

# View logs
sudo journalctl -u martina-admin-bot -f

# Restart services
sudo systemctl restart martina-*

# Update application
cd /opt/martina-bot && git pull && sudo systemctl restart martina-*
```

## 💰 Cost

- **VPS Hosting**: $5-10/month (DigitalOcean)
- **Reliability**: 99.9% uptime
- **Performance**: Dedicated resources
- **Support**: Full system control

## 🎉 Benefits Over Render

- ✅ **No threading restrictions**
- ✅ **Stable, reliable operation**
- ✅ **Full process control**
- ✅ **Better performance**
- ✅ **Easier debugging**
- ✅ **Cost-effective long-term**

---

**Ready to deploy?** Follow the [VPS Deployment Guide](VPS_DEPLOYMENT_GUIDE.md) for step-by-step instructions! 🚀 