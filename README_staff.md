# Booking Nail - Staff Bot

A Telegram bot for staff members to view their schedules.

## 🚀 Quick Deploy on Render

1. **Fork this repository**
2. **Create a new Web Service on Render**
3. **Connect your GitHub repository**
4. **Set environment variables:**
   - `STAFF_BOT_TOKEN` = Your staff bot token
   - `DATABASE_PATH` = `/opt/render/project/src/shared_scheduler.db`
5. **Deploy!**

## 📋 Features

- 👥 Staff Member Selection
- 📅 View Current Week Schedule
- 📚 Schedule History (Coming Soon)
- 🔄 Switch Between Staff Members

## 🔧 Environment Variables

- `STAFF_BOT_TOKEN` - Your Telegram staff bot token
- `DATABASE_PATH` - Shared database path (set automatically on Render)

## 📁 Project Structure

- `staff_bot_standalone.py` - Staff bot entry point and logic
- `staff_requirements.txt` - Python dependencies
- `staff_config.py` - Configuration settings

## 🎯 Usage

1. Start the bot with `/start`
2. Select your name from the staff list
3. View your current week's schedule
4. Switch to other staff members if needed

## 📝 Notes

- This is the **Staff Bot** for viewing schedules
- Admin management is handled by a separate bot
- Database is shared between both bots on Render
- Staff members have read-only access to schedules

## 🔗 Related

- **Admin Bot**: [booking-nail](https://github.com/imaanFarasat/booking-nail) - For managing schedules
- **Staff Bot**: This repository - For viewing schedules 