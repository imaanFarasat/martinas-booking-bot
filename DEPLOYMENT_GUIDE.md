# 🚀 Online Deployment Guide

## **Option 1: Railway (Recommended)**

### **Step 1: Sign Up**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Create a new project

### **Step 2: Add Database**
1. Click "New" → "Database" → "MySQL"
2. Wait for database to be created
3. Copy the database connection details

### **Step 3: Deploy Your Code**
1. Click "New" → "GitHub Repo"
2. Connect your GitHub repository
3. Select your repository
4. Railway will automatically detect Python and deploy

### **Step 4: Set Environment Variables**
In Railway dashboard, go to your app → "Variables" and add:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=your_admin_id_here
MYSQL_HOST=your_railway_mysql_host
MYSQL_PORT=3306
MYSQL_USER=your_railway_mysql_user
MYSQL_PASSWORD=your_railway_mysql_password
MYSQL_DATABASE=your_railway_mysql_database
```

### **Step 5: Deploy**
1. Railway will automatically deploy when you push to GitHub
2. Your bot will be online 24/7!

---

## **Option 2: Render**

### **Step 1: Sign Up**
1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### **Step 2: Create Web Service**
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python main_start.py`

### **Step 3: Add Database**
1. Create a new PostgreSQL database (free tier available)
2. Or use external MySQL (PlanetScale, Railway, etc.)

### **Step 4: Set Environment Variables**
Add the same environment variables as above.

---

## **Option 3: Heroku**

### **Step 1: Sign Up**
1. Go to [heroku.com](https://heroku.com)
2. Create account

### **Step 2: Install Heroku CLI**
```bash
# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli

# Or use winget
winget install --id=Heroku.HerokuCLI
```

### **Step 3: Deploy**
```bash
# Login to Heroku
heroku login

# Create app
heroku create your-bot-name

# Add MySQL addon
heroku addons:create jawsdb:kitefin

# Set environment variables
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set ADMIN_IDS=your_admin_id

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

---

## **🔧 Required Code Changes**

### **1. Update main_start.py for Web Deployment**
```python
import os
import asyncio
from dotenv import load_dotenv
from bot_async import StaffSchedulerBot

load_dotenv()

async def main():
    bot = StaffSchedulerBot()
    await bot.run_async()

if __name__ == "__main__":
    # For web deployment, use this:
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting bot on port {port}")
    asyncio.run(main())
```

### **2. Add Web Server (Optional)**
```python
# Add to main_start.py for health checks
from flask import Flask
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!"

# Run both bot and web server
if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    asyncio.run(main())
```

---

## **💰 Cost Comparison**

| Platform | Free Tier | Paid Tier | Database |
|----------|-----------|-----------|----------|
| Railway | ✅ Yes | $5/month | ✅ Built-in |
| Render | ✅ Yes | $7/month | ✅ Built-in |
| Heroku | ❌ No | $5/month | ✅ Add-on |
| DigitalOcean | ❌ No | $5/month | ✅ $15/month |

---

## **🎯 Recommendation**

**Start with Railway** because:
- ✅ Free tier available
- ✅ Built-in MySQL database
- ✅ Simple deployment
- ✅ Good documentation
- ✅ Reliable service

---

## **📝 Next Steps**

1. **Choose your platform** (Railway recommended)
2. **Follow the setup guide** above
3. **Test your bot** online
4. **Monitor logs** to ensure it's working
5. **Set up monitoring** (optional)

Your bot will run 24/7 and work even when your computer is off! 🚀 