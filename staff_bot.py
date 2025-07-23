import logging
import os
import sqlite3
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, ConversationHandler
)
from telegram.constants import ParseMode

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
STAFF_BOT_TOKEN = os.getenv('STAFF_BOT_TOKEN')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'shared_scheduler.db')

# Conversation states
SELECT_STAFF, VIEW_SCHEDULE = range(2)

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
            
            # Get schedule data
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
            
            # Convert to dictionary format
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

class StaffBot:
    def __init__(self):
        self.db = DatabaseManager()
        self.toronto_tz = pytz.timezone('America/Toronto')
        self.token = STAFF_BOT_TOKEN
        
        if not self.token:
            logger.error("❌ STAFF_BOT_TOKEN not set")
            raise ValueError("STAFF_BOT_TOKEN environment variable is required")
    
    async def start(self, update: Update, context):
        """Start command handler"""
        logger.info(f"Staff bot started by user: {update.effective_user.id}")
        
        # Get all staff members
        staff_list = self.db.get_all_staff()
        
        if not staff_list:
            await update.message.reply_text(
                "❌ No staff members found in the database.\n\n"
                "Please contact the administrator to add staff members."
            )
            return ConversationHandler.END
        
        # Create keyboard with staff names
        keyboard = []
        for staff_id, name in staff_list:
            keyboard.append([InlineKeyboardButton(name, callback_data=f"staff_{staff_id}")])
        
        keyboard.append([InlineKeyboardButton("🔄 Refresh Staff List", callback_data="refresh_staff")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 *Welcome to the Staff Schedule Viewer!*\n\n"
            "Please select your name to view your current schedule:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        
        return SELECT_STAFF
    
    async def handle_staff_selection(self, update: Update, context):
        """Handle staff member selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "refresh_staff":
            # Refresh staff list
            staff_list = self.db.get_all_staff()
            
            if not staff_list:
                await query.edit_message_text(
                    "❌ No staff members found in the database.\n\n"
                    "Please contact the administrator to add staff members."
                )
                return ConversationHandler.END
            
            keyboard = []
            for staff_id, name in staff_list:
                keyboard.append([InlineKeyboardButton(name, callback_data=f"staff_{staff_id}")])
            
            keyboard.append([InlineKeyboardButton("🔄 Refresh Staff List", callback_data="refresh_staff")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👋 *Welcome to the Staff Schedule Viewer!*\n\n"
                "Please select your name to view your current schedule:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return SELECT_STAFF
        
        if query.data.startswith("staff_"):
            staff_id = int(query.data.split("_")[1])
            staff_info = self.db.get_staff_by_id(staff_id)
            
            if not staff_info:
                await query.edit_message_text("❌ Staff member not found.")
                return ConversationHandler.END
            
            staff_name = staff_info[1]
            context.user_data['current_staff_id'] = staff_id
            context.user_data['current_staff_name'] = staff_name
            
            # Get staff schedule
            schedule = self.db.get_staff_schedule(staff_id)
            
            if not schedule:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Staff List", callback_data="back_to_staff_list")],
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
                return VIEW_SCHEDULE
            
            # Display schedule
            schedule_text = self.format_schedule(schedule, staff_name)
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Staff List", callback_data="back_to_staff_list")],
                [InlineKeyboardButton("🔄 Refresh", callback_data=f"staff_{staff_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                schedule_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return VIEW_SCHEDULE
    
    async def handle_schedule_view(self, update: Update, context):
        """Handle schedule view actions"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_to_staff_list":
            # Go back to staff selection
            staff_list = self.db.get_all_staff()
            
            keyboard = []
            for staff_id, name in staff_list:
                keyboard.append([InlineKeyboardButton(name, callback_data=f"staff_{staff_id}")])
            
            keyboard.append([InlineKeyboardButton("🔄 Refresh Staff List", callback_data="refresh_staff")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👋 *Welcome to the Staff Schedule Viewer!*\n\n"
                "Please select your name to view your current schedule:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return SELECT_STAFF
        
        elif query.data.startswith("staff_"):
            # Refresh current staff schedule
            staff_id = int(query.data.split("_")[1])
            staff_info = self.db.get_staff_by_id(staff_id)
            
            if not staff_info:
                await query.edit_message_text("❌ Staff member not found.")
                return ConversationHandler.END
            
            staff_name = staff_info[1]
            schedule = self.db.get_staff_schedule(staff_id)
            
            if not schedule:
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Staff List", callback_data="back_to_staff_list")],
                    [InlineKeyboardButton("🔄 Refresh", callback_data=f"staff_{staff_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"📅 *Schedule for {staff_name}*\n\n"
                    "❌ No schedule found.\n\n"
                    "Please contact the administrator to set your schedule.",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN
                )
                return VIEW_SCHEDULE
            
            schedule_text = self.format_schedule(schedule, staff_name)
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to Staff List", callback_data="back_to_staff_list")],
                [InlineKeyboardButton("🔄 Refresh", callback_data=f"staff_{staff_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                schedule_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return VIEW_SCHEDULE
    
    def format_schedule(self, schedule, staff_name):
        """Format schedule for display"""
        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        # Calculate current week dates
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
    
    def run(self):
        """Run the bot"""
        logger.info("Starting staff bot...")
        logger.info(f"Using database: {DATABASE_PATH}")
        
        # Create application using Application class (newer API pattern)
        from telegram.ext import Application
        
        # Create application
        application = Application.builder().token(self.token).build()
        
        # Create conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                SELECT_STAFF: [
                    CallbackQueryHandler(self.handle_staff_selection)
                ],
                VIEW_SCHEDULE: [
                    CallbackQueryHandler(self.handle_schedule_view)
                ]
            },
            fallbacks=[CommandHandler("start", self.start)]
        )
        
        application.add_handler(conv_handler)
        
        # Start the bot
        logger.info("Staff bot is starting...")
        application.run_polling()

if __name__ == "__main__":
    try:
        logger.info("Initializing staff bot...")
        bot = StaffBot()
        logger.info("Staff bot initialized successfully")
        bot.run()
    except Exception as e:
        logger.error(f"Error starting staff bot: {e}")
        import traceback
        traceback.print_exc()
        # Exit with error code for Render to detect failure
        exit(1) 