# Booking Nail - Admin Bot

A Telegram bot for managing staff schedules and appointments.

## 🚀 Quick Deploy on Render

1. **Fork this repository**
2. **Create a new Web Service on Render**
3. **Connect your GitHub repository**
4. **Set environment variables:**
   - `BOT_TOKEN` = Your main bot token
   - `ADMIN_IDS` = Your admin user IDs (comma-separated)
5. **Deploy!**

## 📋 Features

- 👥 Staff Management (Add/Remove staff)
- 📅 Schedule Management (Set weekly schedules)
- 👀 View Current Schedules
- 📄 Export PDF Reports
- 📚 Schedule History
- 🗑️ Reset All Schedules

## 🔧 Environment Variables

- `BOT_TOKEN` - Your Telegram bot token
- `ADMIN_IDS` - Comma-separated list of admin user IDs
- `DATABASE_PATH` - Database file path (auto-set on Render)

## 📁 Project Structure

- `main_start.py` - Main bot entry point
- `bot_async.py` - Main bot logic
- `config.py` - Configuration settings
- `database.py` - Database operations
- `pdf_generator.py` - PDF report generation
- `validators.py` - Input validation

## 🎯 Usage

1. Start the bot with `/start`
2. Use the inline keyboard to navigate
3. Only authorized admins can access the bot

## 📝 Notes

- This is the **Admin Bot** for managing schedules
- Staff members use a separate bot to view their schedules
- Database is shared between both bots on Render 