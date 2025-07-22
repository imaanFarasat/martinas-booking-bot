# 🚀 Deployment Guide - Booking Nail Bots

This guide will help you deploy both the Admin Bot and Staff Bot on Render.

## 📋 Prerequisites

1. **Two Telegram Bots** (created via @BotFather)
   - Admin Bot Token (for management)
   - Staff Bot Token (for staff viewing)

2. **Two GitHub Repositories**
   - Main repository (for admin bot)
   - Staff repository (for staff bot)

## 🤖 Bot 1: Admin Bot (Main Repository)

### Step 1: Create GitHub Repository
1. Create a new repository: `imaanFarasat/booking-nail`
2. Upload all files from this directory (except staff files)

### Step 2: Deploy on Render
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `booking-nail-admin-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main_start.py`

### Step 3: Set Environment Variables
Add these environment variables in Render:
- `BOT_TOKEN` = Your admin bot token
- `ADMIN_IDS` = Your admin user IDs (comma-separated)
- `DATABASE_PATH` = `/opt/render/project/src/staff_scheduler.db`

### Step 4: Deploy
Click **"Create Web Service"** and wait for deployment.

## 👥 Bot 2: Staff Bot (Separate Repository)

### Step 1: Create Staff Repository
1. Create new repository: `imaanFarasat/booking-nail-staff-bot`
2. Copy these files to the new repository:
   - `staff_bot_standalone.py`
   - `staff_requirements.txt`
   - `staff_config.py`
   - `README_staff.md`
   - `render_staff.yaml` (rename to `render.yaml`)

### Step 2: Deploy on Render
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your staff GitHub repository
4. Configure:
   - **Name**: `booking-nail-staff-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r staff_requirements.txt`
   - **Start Command**: `python staff_bot_standalone.py`

### Step 3: Set Environment Variables
Add these environment variables in Render:
- `STAFF_BOT_TOKEN` = `7610615551:AAE-BsH3KdqVYlrb6txqDa9Vc3OCrDesfFw`
- `DATABASE_PATH` = `/opt/render/project/src/shared_scheduler.db`

### Step 4: Deploy
Click **"Create Web Service"** and wait for deployment.

## 🔧 Environment Variables Summary

### Admin Bot
```
BOT_TOKEN=your_admin_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_PATH=/opt/render/project/src/staff_scheduler.db
```

### Staff Bot
```
STAFF_BOT_TOKEN=7610615551:AAE-BsH3KdqVYlrb6txqDa9Vc3OCrDesfFw
DATABASE_PATH=/opt/render/project/src/shared_scheduler.db
```

## 📁 File Structure

### Main Repository (Admin Bot)
```
booking-nail/
├── main_start.py          # Entry point
├── bot_async.py           # Main bot logic
├── config.py              # Configuration
├── database.py            # Database operations
├── pdf_generator.py       # PDF generation
├── validators.py          # Input validation
├── requirements.txt       # Dependencies
├── render.yaml           # Render config
├── README.md             # Documentation
└── .gitignore           # Git ignore
```

### Staff Repository (Staff Bot)
```
booking-nail-staff-bot/
├── staff_bot_standalone.py  # Staff bot logic
├── staff_requirements.txt   # Dependencies
├── staff_config.py         # Configuration
├── render.yaml            # Render config
└── README_staff.md        # Documentation
```

## ✅ Verification Steps

### Admin Bot
1. Start the admin bot: `/start`
2. Verify admin access
3. Test staff management
4. Test schedule creation

### Staff Bot
1. Start the staff bot: `/start`
2. Select a staff member
3. View current schedule
4. Test staff switching

## 🔗 Bot Links

After deployment, you'll have:
- **Admin Bot**: `https://t.me/your_admin_bot_username`
- **Staff Bot**: `https://t.me/your_staff_bot_username`

## 🛠️ Troubleshooting

### Common Issues
1. **Bot not responding**: Check environment variables
2. **Database errors**: Verify database path
3. **Import errors**: Check requirements.txt
4. **Token conflicts**: Ensure separate tokens

### Logs
Check Render logs for both services to debug issues.

## 📞 Support

If you encounter issues:
1. Check Render deployment logs
2. Verify environment variables
3. Test bot tokens manually
4. Check database connectivity

---

**Both bots are now ready for deployment! 🎉** 