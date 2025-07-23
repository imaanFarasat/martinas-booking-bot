#!/usr/bin/env python3
"""
Combined bot that handles both admin and staff functions
Simple, single-process approach that works reliably on Render
"""
import logging
import os
import sqlite3
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler, Application
)
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
STAFF_BOT_TOKEN = os.getenv('STAFF_BOT_TOKEN')
ADMIN_IDS_STR = os.getenv('ADMIN_IDS', '')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'shared_scheduler.db')

# Parse admin IDs
ADMIN_IDS = []
if ADMIN_IDS_STR:
    for admin_id in ADMIN_IDS_STR.split(','):
        try:
            ADMIN_IDS.append(int(admin_id.strip()))
        except ValueError:
            print(f"Warning: Invalid admin ID '{admin_id}'")

# Conversation states
MAIN_MENU, STAFF_VIEW, ADMIN_MENU = range(3)

class DatabaseManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
        logger.info(f"Database path: {self.db_path}")
    
    def get_all_staff(self):
        """Get all staff members"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM staff ORDER BY name')
            staff = cursor.fetchall()
            conn.close()
            logger.info(f"Found {len(staff)} staff members")
            return staff
        except Exception as e:
            logger.error(f"Error getting staff: {e}")
            return []
    
    def get_staff_by_id(self, staff_id):
        """Get staff member by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM staff WHERE id = ?', (staff_id,))
            staff = cursor.fetchone()
            conn.close()
            return staff
        except Exception as e:
            logger.error(f"Error getting staff by ID: {e}")
            return None
    
    def get_staff_schedule(self, staff_id):
        """Get schedule for a staff member"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT day_of_week, is_working, start_time, end_time
                FROM schedules 
                WHERE staff_id = ?
                ORDER BY 
                    CASE day_of_week
                        WHEN 'Sunday' THEN 1
                        WHEN 'Monday' THEN 2
                        WHEN 'Tuesday' THEN 3
                        WHEN 'Wednesday' THEN 4
                        WHEN 'Thursday' THEN 5
                        WHEN 'Friday' THEN 6
                        WHEN 'Saturday' THEN 7
                    END
            ''', (staff_id,))
            
            schedule_data = cursor.fetchall()
            conn.close()
            
            schedule = {}
            for day, is_working, start_time, end_time in schedule_data:
                schedule[day] = {
                    'is_working': bool(is_working),
                    'start_time': start_time or '',
                    'end_time': end_time or ''
                }
            
            logger.info(f"Found schedule for staff {staff_id}: {len(schedule)} days")
            return schedule
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            return {}

class CombinedBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.toronto_tz = pytz.timezone('America/Toronto')
        self.token = BOT_TOKEN or STAFF_BOT_TOKEN
        
        if not self.token:
            logger.error("❌ No bot token set")
            raise ValueError("BOT_TOKEN or STAFF_BOT_TOKEN environment variable is required")
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id in ADMIN_IDS
    
    async def start(self, update: Update, context):
        """Start command handler"""
        user_id = update.effective_user.id
        logger.info(f"Bot started by user: {user_id}")
        
        if self.is_admin(user_id):
            # Show admin menu
            await self.show_admin_menu(update, context)
            return ADMIN_MENU
        else:
            # Show staff menu
            await self.show_staff_menu(update, context)
            return STAFF_VIEW
    
    async def show_admin_menu(self, update: Update, context):
        """Show admin menu"""
        keyboard = [
            [InlineKeyboardButton("👥 Staff Management", callback_data="admin_staff")],
            [InlineKeyboardButton("📅 View Schedules", callback_data="admin_schedules")],
            [InlineKeyboardButton("📄 Export PDF", callback_data="admin_pdf")],
            [InlineKeyboardButton("👤 Switch to Staff View", callback_data="switch_to_staff")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🤖 *Admin Panel*\n\nWelcome! What would you like to do?"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def show_staff_menu(self, update: Update, context):
        """Show staff menu"""
        staff_list = self.db.get_all_staff()
        
        if not staff_list:
            await update.message.reply_text(
                "❌ No staff members found in the database.\n\n"
                "Please contact the administrator to add staff members."
            )
            return ConversationHandler.END
        
        keyboard = []
        for staff_id, name in staff_list:
            keyboard.append([InlineKeyboardButton(name, callback_data=f"staff_{staff_id}")])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh Staff List", callback_data="refresh_staff")])
        
        if self.is_admin(update.effective_user.id):
            keyboard.append([InlineKeyboardButton("🔧 Switch to Admin View", callback_data="switch_to_admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "👋 *Welcome to the Staff Schedule Viewer!*\n\nPlease select your name to view your current schedule:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_admin_menu(self, update: Update, context):
        """Handle admin menu button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "admin_staff":
            await query.edit_message_text("👥 Staff management features coming soon!")
            return ADMIN_MENU
        elif query.data == "admin_schedules":
            await query.edit_message_text("📅 Schedule viewing features coming soon!")
            return ADMIN_MENU
        elif query.data == "admin_pdf":
            await query.edit_message_text("📄 PDF export features coming soon!")
            return ADMIN_MENU
        elif query.data == "switch_to_staff":
            return await self.show_staff_menu(update, context)
    
    async def handle_staff_menu(self, update: Update, context):
        """Handle staff menu button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "refresh_staff":
            return await self.show_staff_menu(update, context)
        elif query.data == "switch_to_admin":
            return await self.show_admin_menu(update, context)
        elif query.data.startswith("staff_"):
            staff_id = int(query.data.split("_")[1])
            staff_info = self.db.get_staff_by_id(staff_id)
            
            if not staff_info:
                await query.edit_message_text("❌ Staff member not found.")
                return STAFF_VIEW
            
            staff_name = staff_info[1]
            schedule = self.db.get_staff_schedule(staff_id)
            
            if not schedule:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Staff List", callback_data="back_to_staff")],
                    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_staff")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"📅 *Schedule for {staff_name}*\n\n"
                    "❌ No schedule found.\n\n"
                    "Please contact the administrator to set your schedule.",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                return STAFF_VIEW
            
            schedule_text = self.format_schedule(schedule, staff_name)
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Staff List", callback_data="back_to_staff")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_staff")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                schedule_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return STAFF_VIEW
    
    def format_schedule(self, schedule, staff_name):
        """Format schedule for display"""
        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        now = datetime.now(self.toronto_tz)
        days_since_sunday = now.weekday() + 1
        if days_since_sunday == 7:
            days_since_sunday = 0
        week_start = now.date() - timedelta(days=days_since_sunday)
        
        week_dates = {}
        for i, day in enumerate(days_of_week):
            week_dates[day] = week_start + timedelta(days=i)
        
        text = f"📅 *Schedule for {staff_name}*\n\n"
        text += f"📅 *Week of {week_start.strftime('%B %d, %Y')}*\n\n"
        
        for day in days_of_week:
            date = week_dates[day]
            date_str = date.strftime('%a, %b %d')
            
            if day in schedule and schedule[day]:
                day_schedule = schedule[day]
                
                if day_schedule.get('is_working', False):
                    start_time = day_schedule.get('start_time', '')
                    end_time = day_schedule.get('end_time', '')
                    
                    if start_time and end_time:
                        text += f"✅ *{date_str}* - {start_time} to {end_time}\n"
                    else:
                        text += f"⚠️ *{date_str}* - Times not set\n"
                else:
                    text += f"❌ *{date_str}* - OFF\n"
            else:
                text += f"❓ *{date_str}* - No schedule\n"
        
        text += "\n💡 *Need to update your schedule? Contact your administrator.*"
        
        return text
    
    async def run(self):
        """Run the bot"""
        logger.info("Starting combined bot...")
        logger.info(f"Using database: {DATABASE_PATH}")
        logger.info(f"Admin IDs: {ADMIN_IDS}")
        
        application = Application.builder().token(self.token).build()
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                ADMIN_MENU: [
                    CallbackQueryHandler(self.handle_admin_menu)
                ],
                STAFF_VIEW: [
                    CallbackQueryHandler(self.handle_staff_menu)
                ]
            },
            fallbacks=[CommandHandler("start", self.start)]
        )
        
        application.add_handler(conv_handler)
        
        logger.info("Combined bot is starting...")
        await application.initialize()
        await application.updater.start_polling(drop_pending_updates=True, allowed_updates=None)

if __name__ == "__main__":
    try:
        import asyncio
        bot = CombinedBot()
        asyncio.run(bot.run())
    except Exception as e:
        logger.error(f"Error starting combined bot: {e}")
        import traceback
        traceback.print_exc()
        exit(1) 