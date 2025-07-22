import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler
import sqlite3
import os

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECT_STAFF, STAFF_MENU, VIEW_SCHEDULE, VIEW_HISTORY, VIEW_WEEK = range(5)

class DatabaseManager:
    def __init__(self):
        # Use shared database path for Render deployment
        self.db_path = os.getenv('DATABASE_PATH', 'shared_scheduler.db')
    
    def get_all_staff(self):
        """Get all staff members"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM staff ORDER BY name')
        staff = cursor.fetchall()
        conn.close()
        return staff
    
    def get_staff_by_id(self, staff_id):
        """Get staff member by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM staff WHERE id = ?', (staff_id,))
        staff = cursor.fetchone()
        conn.close()
        return staff
    
    def get_staff_schedule_for_week(self, staff_id, week_start):
        """Get a specific staff member's schedule for a week"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        week_end = week_start + timedelta(days=6)
        
        cursor.execute('''
            SELECT day_of_week, schedule_date, is_working, start_time, end_time
            FROM schedules
            WHERE staff_id = ? AND schedule_date BETWEEN ? AND ?
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
        ''', (staff_id, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')))
        
        schedules = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary format
        schedule_dict = {}
        for day, schedule_date, is_working, start_time, end_time in schedules:
            schedule_dict[day] = {
                'schedule_date': schedule_date,
                'is_working': is_working,
                'start_time': start_time,
                'end_time': end_time
            }
        
        return schedule_dict
    
    def get_staff_schedule(self, staff_id):
        """Get all schedules for a staff member (without dates)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, staff_id, day_of_week, schedule_date, is_working, start_time, end_time
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
        schedules = cursor.fetchall()
        conn.close()
        return schedules

class StaffBot:
    def __init__(self, token: str):
        self.token = token
        self.db = DatabaseManager()
        self.toronto_tz = pytz.timezone('America/Toronto')
        self.DAYS_OF_WEEK = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        await self.show_staff_selection(update, context)
        return SELECT_STAFF
    
    async def show_staff_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show staff selection menu"""
        staff_list = self.db.get_all_staff()
        
        if not staff_list:
            await update.message.reply_text(
                "❌ No staff members found in the database.\n\n"
                "Please contact your manager to add staff members first."
            )
            return ConversationHandler.END
        
        keyboard = []
        for staff_id, name in staff_list:
            keyboard.append([InlineKeyboardButton(name, callback_data=f"staff_{staff_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "👥 *Staff Schedule Viewer*\n\nPlease select your name to view your schedule:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return SELECT_STAFF
    
    async def handle_staff_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle staff selection"""
        query = update.callback_query
        await query.answer()
        
        staff_id = int(query.data.split('_')[1])
        staff_info = self.db.get_staff_by_id(staff_id)
        
        if not staff_info:
            await query.edit_message_text("❌ Staff member not found.")
            return ConversationHandler.END
        
        staff_name = staff_info[1]
        context.user_data['staff_id'] = staff_id
        context.user_data['staff_name'] = staff_name
        
        await self.show_staff_menu(update, context)
        return STAFF_MENU
    
    async def show_staff_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show staff menu"""
        staff_name = context.user_data.get('staff_name', 'Unknown')
        
        keyboard = [
            [InlineKeyboardButton("📅 View Current Schedule", callback_data="view_current_schedule")],
            [InlineKeyboardButton("📚 View Schedule History", callback_data="view_schedule_history")],
            [InlineKeyboardButton("🔄 Change Staff Member", callback_data="change_staff")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"👤 *{staff_name}*\n\nWhat would you like to do?"
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return STAFF_MENU
    
    async def handle_staff_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle staff menu button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "view_current_schedule":
            return await self.view_current_schedule(update, context)
        elif query.data == "view_schedule_history":
            return await self.show_schedule_history(update, context)
        elif query.data == "change_staff":
            return await self.show_staff_selection(update, context)
        elif query.data == "back_to_menu":
            return await self.show_staff_menu(update, context)
        
        return STAFF_MENU
    
    async def view_current_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View current week's schedule for the staff member"""
        staff_id = context.user_data.get('staff_id')
        staff_name = context.user_data.get('staff_name')
        
        # Get current week start (Sunday)
        now = datetime.now(self.toronto_tz)
        days_since_sunday = now.weekday() + 1  # Monday=0, so Sunday=6, but we want Sunday=0
        if days_since_sunday == 7:
            days_since_sunday = 0
        week_start = now - timedelta(days=days_since_sunday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        schedules = self.db.get_staff_schedule_for_week(staff_id, week_start)
        
        text = f"📅 *{staff_name}'s Schedule*\n\n"
        text += f"*Week of {week_start.strftime('%B %d, %Y')}*\n\n"
        
        # Check if we have any schedules
        if not schedules:
            text += "No schedule found for this week.\n\n"
            text += "This could mean:\n"
            text += "• No schedule has been set for this week yet\n"
            text += "• Contact your manager to set up your schedule"
        else:
            # Check if all days are OFF
            all_off = True
            for day in self.DAYS_OF_WEEK:
                schedule = schedules.get(day, {})
                if schedule.get('is_working'):
                    all_off = False
                    break
            
            if all_off:
                text += "📅 *Your Schedule for This Week:*\n\n"
                text += "You are scheduled OFF for all days this week.\n\n"
                text += "*Daily Breakdown:*\n"
                for day in self.DAYS_OF_WEEK:
                    day_date = week_start + timedelta(days=self.DAYS_OF_WEEK.index(day))
                    text += f"• {day} ({day_date.strftime('%b %d')}): 🔴 OFF\n"
            else:
                for day in self.DAYS_OF_WEEK:
                    day_date = week_start + timedelta(days=self.DAYS_OF_WEEK.index(day))
                    schedule = schedules.get(day, {})
                    
                    if schedule.get('is_working'):
                        start_time = schedule.get('start_time', 'Not set')
                        end_time = schedule.get('end_time', 'Not set')
                        text += f"*{day} ({day_date.strftime('%b %d')}):* ✅ {start_time}-{end_time}\n"
                    else:
                        text += f"*{day} ({day_date.strftime('%b %d')}):* 🔴 OFF\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("🔄 Change Staff", callback_data="change_staff")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return STAFF_MENU
    
    async def show_schedule_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show schedule history for the staff member"""
        staff_id = context.user_data.get('staff_id')
        staff_name = context.user_data.get('staff_name')
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")],
            [InlineKeyboardButton("🔄 Change Staff", callback_data="change_staff")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(
            f"📚 *{staff_name}'s Schedule History*\n\nHistorical schedules feature coming soon!\n\nFor now, please use the main bot to view historical schedules.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return STAFF_MENU
    
    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(self.token).build()
        
        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                SELECT_STAFF: [CallbackQueryHandler(self.handle_staff_selection)],
                STAFF_MENU: [CallbackQueryHandler(self.handle_staff_menu)],
                VIEW_SCHEDULE: [CallbackQueryHandler(self.handle_staff_menu)],
                VIEW_HISTORY: [CallbackQueryHandler(self.handle_staff_menu)],
                VIEW_WEEK: [CallbackQueryHandler(self.handle_staff_menu)]
            },
            fallbacks=[CommandHandler("start", self.start)]
        )
        
        application.add_handler(conv_handler)
        
        # Start the bot
        print("Staff bot started...")
        application.run_polling()

if __name__ == "__main__":
    # Get token from environment
    STAFF_BOT_TOKEN = os.getenv('STAFF_BOT_TOKEN')
    
    if not STAFF_BOT_TOKEN or STAFF_BOT_TOKEN == 'YOUR_STAFF_BOT_TOKEN_HERE':
        print("❌ Error: STAFF_BOT_TOKEN environment variable not set")
        print("Please set the STAFF_BOT_TOKEN environment variable")
        exit(1)
    
    bot = StaffBot(STAFF_BOT_TOKEN)
    bot.run() 