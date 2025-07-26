import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)
from telegram.constants import ParseMode
import os

from config import BOT_TOKEN, ADMIN_IDS, DAYS_OF_WEEK
from database_factory import get_database_manager
from pdf_generator import PDFGenerator
from validators import ScheduleValidator

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
MAIN_MENU, STAFF_MANAGEMENT, ADD_STAFF, REMOVE_STAFF, SCHEDULE_MENU, SCHEDULE_INPUT, BULK_ADD_COUNT, BULK_ADD_NAMES, VIEW_SCHEDULES, BULK_SCHEDULE, WEEKLY_STATS, SCHEDULE_TEMPLATES, SCHEDULE_HISTORY, WEEK_SELECTION = range(14)

class StaffSchedulerBot:
    def __init__(self):
        self.db = get_database_manager()
        self.pdf_gen = PDFGenerator()
        self.user_states = {}  # Store user conversation states
        self.toronto_tz = pytz.timezone('America/Toronto')
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id in ADMIN_IDS
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user_id = update.effective_user.id
        
        # Add debugging for admin access
        print(f"DEBUG: /start called by user_id: {user_id}")
        print(f"DEBUG: ADMIN_IDS: {ADMIN_IDS}")
        print(f"DEBUG: Is admin? {self.is_admin(user_id)}")
        logger.info(f"Admin bot /start received from user {user_id}")
        
        if not self.is_admin(user_id):
            print(f"DEBUG: User {user_id} is NOT authorized")
            logger.info(f"User {user_id} is NOT authorized")
            await update.message.reply_text(
                "❌ You are not authorized to use this bot. Please contact the administrator."
            )
            return ConversationHandler.END
        
        print(f"DEBUG: User {user_id} is authorized, showing main menu")
        logger.info(f"User {user_id} is authorized, showing main menu")
        await self.show_main_menu(update, context)
        return MAIN_MENU
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu options"""
        text = "🤖 *Staff Scheduler Bot*\n\n"
        text += "Welcome to the staff scheduling system. What would you like to do?"
        
        keyboard = [
            [
                InlineKeyboardButton("👥 Staff Management", callback_data="staff_management"),
                InlineKeyboardButton("📅 Set Schedule", callback_data="set_schedule")
            ],
            [
                InlineKeyboardButton("📋 View Current Schedules", callback_data="view_current_schedules"),
                InlineKeyboardButton("📄 Export PDF", callback_data="export_pdf")
            ],
            [
                InlineKeyboardButton("🔄 Bulk Schedule", callback_data="bulk_schedule"),
                InlineKeyboardButton("📚 Schedule History", callback_data="schedule_history")
            ],
            [
                InlineKeyboardButton("📊 Weekly Stats", callback_data="weekly_stats"),
                InlineKeyboardButton("🔧 Templates", callback_data="schedule_templates")
            ],
            [
                InlineKeyboardButton("🗑️ Reset All Schedules", callback_data="reset_all_schedules")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return MAIN_MENU
    
    async def handle_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu button clicks"""
        query = update.callback_query
        await query.answer()
        
        # Add debugging for admin access
        user_id = update.effective_user.id
        print(f"DEBUG: handle_main_menu called by user_id: {user_id}")
        print(f"DEBUG: Button clicked: {query.data}")
        print(f"DEBUG: Is admin? {self.is_admin(user_id)}")
        
        if query.data == "staff_management":
            return await self.show_staff_management(update, context)
        elif query.data == "set_schedule":
            return await self.show_week_selection_for_all(update, context)
        elif query.data == "view_current_schedules":
            return await self.view_schedules(update, context)
        elif query.data == "export_pdf":
            print(f"DEBUG: export_pdf button clicked by user_id: {user_id}")
            return await self.show_pdf_week_selection(update, context)
        elif query.data == "bulk_schedule":
            await self.show_bulk_schedule_menu(update, context)
            return BULK_SCHEDULE
        elif query.data == "weekly_stats":
            await self.show_weekly_stats(update, context)
            return WEEKLY_STATS
        elif query.data == "schedule_templates":
            await self.show_schedule_templates(update, context)
            return SCHEDULE_TEMPLATES
        elif query.data == "reset_all_schedules":
            return await self.reset_all_schedules(update, context)
        elif query.data == "schedule_history":
            await self.show_schedule_history(update, context)
            return SCHEDULE_HISTORY
        elif query.data.startswith("view_week_"):
            week_key = query.data.split("_")[2]
            return await self.view_week_schedule(update, context, week_key)
        elif query.data.startswith("quick_edit_"):
            # Clear context to ensure fresh data
            context.user_data.clear()
            staff_name = query.data.split("_", 2)[2]
            return await self.quick_edit_staff(update, context, staff_name)
        
        return MAIN_MENU
    
    async def show_staff_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show staff management menu"""
        keyboard = [
            [InlineKeyboardButton("➕ Add Single Staff", callback_data="add_staff")],
            [InlineKeyboardButton("📝 Bulk Add Staff (1-5)", callback_data="bulk_add_staff")],
            [InlineKeyboardButton("➖ Remove Staff", callback_data="remove_staff")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        staff_list = self.db.get_all_staff()
        staff_text = "\n".join([f"• {name}" for _, name in staff_list]) if staff_list else "No staff members"
        
        text = f"👥 *Staff Management*\n\n*Current Staff:*\n{staff_text}"
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return STAFF_MANAGEMENT
    
    async def handle_staff_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle staff management button clicks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_staff":
            await query.edit_message_text(
                "➕ *Add Single Staff Member*\n\nPlease enter the staff member's name:",
                parse_mode=ParseMode.MARKDOWN
            )
            return ADD_STAFF
        elif query.data == "bulk_add_staff":
            keyboard = [
                [InlineKeyboardButton("1", callback_data="bulk_count_1")],
                [InlineKeyboardButton("2", callback_data="bulk_count_2")],
                [InlineKeyboardButton("3", callback_data="bulk_count_3")],
                [InlineKeyboardButton("4", callback_data="bulk_count_4")],
                [InlineKeyboardButton("5", callback_data="bulk_count_5")],
                [InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📝 *Bulk Add Staff*\n\nHow many staff members do you want to add?\n\nSelect a number between 1-5:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return BULK_ADD_COUNT
        elif query.data == "remove_staff":
            return await self.show_remove_staff_menu(update, context)
        elif query.data == "back_main":
            return await self.show_main_menu(update, context)
        elif query.data == "back_staff_management":
            return await self.show_staff_management(update, context)
        
        return STAFF_MANAGEMENT
    
    async def add_staff_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle adding new staff member"""
        staff_name = update.message.text.strip()
        
        # Validate staff name
        is_valid, error_msg = ScheduleValidator.validate_staff_name(staff_name)
        if not is_valid:
            keyboard = [[InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"❌ {error_msg}\n\nPlease try again or go back:",
                reply_markup=reply_markup
            )
            return ADD_STAFF
        
        # Add staff to database
        staff_id = self.db.add_staff(staff_name)
        if staff_id is None:
            keyboard = [[InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"❌ Staff member '{staff_name}' already exists.\n\nPlease try again or go back:",
                reply_markup=reply_markup
            )
            return ADD_STAFF
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Staff member '{staff_name}' added successfully!",
            reply_markup=reply_markup
        )
        return STAFF_MANAGEMENT
    
    async def show_remove_staff_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show menu to remove staff members"""
        staff_list = self.db.get_all_staff()
        
        if not staff_list:
            keyboard = [[InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                "❌ No staff members to remove.",
                reply_markup=reply_markup
            )
            return STAFF_MANAGEMENT
        
        keyboard = []
        for staff_id, name in staff_list:
            keyboard.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"remove_{staff_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(
            "➖ *Remove Staff Member*\n\nSelect a staff member to remove:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return REMOVE_STAFF
    
    async def handle_remove_staff(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle removing staff member"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_staff_management":
            return await self.show_staff_management(update, context)
        
        if query.data.startswith("remove_"):
            staff_id = int(query.data.split("_")[1])
            staff_info = self.db.get_staff_by_id(staff_id)
            
            if staff_info:
                staff_name = staff_info[1]
                self.db.remove_staff(staff_id)
                
                keyboard = [[InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"✅ Staff member '{staff_name}' removed successfully!",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    "❌ Staff member not found.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")
                    ]])
                )
        
        return STAFF_MANAGEMENT
    
    async def handle_bulk_add_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bulk add count selection"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_staff_management":
            return await self.show_staff_management(update, context)
        
        if query.data.startswith("bulk_count_"):
            count = int(query.data.split("_")[2])
            context.user_data['bulk_count'] = count
            
            await query.edit_message_text(
                f"📝 *Bulk Add {count} Staff Members*\n\n"
                f"Please enter the names of {count} staff members, one per line:\n\n"
                f"*Example:*\n"
                f"Bea\n"
                f"Mobina\n"
                f"Mira\n"
                f"Trecia\n\n"
                f"*Format:* One name per line",
                parse_mode=ParseMode.MARKDOWN
            )
            return BULK_ADD_NAMES
    
    async def handle_bulk_add_names(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bulk add names input"""
        names_text = update.message.text.strip()
        expected_count = context.user_data.get('bulk_count', 0)
        
        # Split names by lines and clean them
        names = [name.strip() for name in names_text.split('\n') if name.strip()]
        
        if len(names) != expected_count:
            keyboard = [[InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"❌ You entered {len(names)} names, but expected {expected_count}.\n\n"
                f"Please enter exactly {expected_count} names, one per line, or go back:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return BULK_ADD_NAMES
        
        # Validate and add names
        added_names = []
        failed_names = []
        
        for name in names:
            is_valid, error_msg = ScheduleValidator.validate_staff_name(name)
            if is_valid:
                staff_id = self.db.add_staff(name)
                if staff_id is not None:
                    added_names.append(name)
                else:
                    failed_names.append(f"{name} (already exists)")
            else:
                failed_names.append(f"{name} ({error_msg})")
        
        # Create result message
        result_text = "📝 *Bulk Add Results*\n\n"
        
        if added_names:
            result_text += f"✅ *Successfully Added:*\n"
            for name in added_names:
                result_text += f"• {name}\n"
            result_text += "\n"
        
        if failed_names:
            result_text += f"❌ *Failed to Add:*\n"
            for name in failed_names:
                result_text += f"• {name}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Staff Management", callback_data="back_staff_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(result_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        # Clear user data
        context.user_data.pop('bulk_count', None)
        
        return STAFF_MANAGEMENT
    
    async def show_schedule_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show schedule menu with staff list"""
        staff_list = self.db.get_all_staff()
        
        if not staff_list:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                "❌ No staff members available. Please add staff first.",
                reply_markup=reply_markup
            )
            return MAIN_MENU
        
        # Get selected week information
        week_dates = context.user_data.get('week_dates', {})
        week_start = context.user_data.get('week_start')
        
        if week_dates and week_start:
            date_range = self.format_date_range(week_dates)
            text = f"📅 *Set Schedule*\n\n*Selected Week:* {date_range}\n\nSelect a staff member to set their schedule:"
        else:
            text = "📅 *Set Schedule*\n\nSelect a staff member to set their schedule:"
        
        keyboard = []
        for staff_id, name in staff_list:
            keyboard.append([InlineKeyboardButton(f"📅 {name}", callback_data=f"schedule_{staff_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Week Selection", callback_data="back_week_selection")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return SCHEDULE_MENU
    
    async def handle_schedule_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle schedule menu button clicks"""
        query = update.callback_query
        await query.answer()
        
        print(f"DEBUG: Schedule menu callback data: {query.data}")
        
        if query.data == "back_main":
            return await self.show_main_menu(update, context)
        elif query.data == "back_week_selection":
            return await self.show_week_selection_for_all(update, context)
        
        if query.data.startswith("schedule_"):
            staff_id = int(query.data.split("_")[1])
            staff_info = self.db.get_staff_by_id(staff_id)
            
            print(f"DEBUG: Selected staff_id: {staff_id}, staff_info: {staff_info}")
            
            if staff_info:
                context.user_data['current_staff_id'] = staff_id
                context.user_data['current_staff_name'] = staff_info[1]
                print(f"DEBUG: Setting up schedule for {staff_info[1]}")
                
                # Get the selected week from context (set by week selection)
                week_dates = context.user_data.get('week_dates', {})
                week_start = context.user_data.get('week_start')
                
                if week_dates and week_start:
                    # Check if staff already has a schedule for the selected week
                    existing_schedule = self.db.get_staff_schedule_for_week(staff_id, week_start)
                    if existing_schedule:
                        # Staff has existing schedule for selected week, show it with edit options
                        schedule_list = []
                        for day in DAYS_OF_WEEK:
                            if day in existing_schedule:
                                day_data = existing_schedule[day]
                                schedule_list.append((
                                    day,
                                    day_data['is_working'],
                                    day_data['start_time'],
                                    day_data['end_time']
                                ))
                        return await self.show_existing_schedule(update, context, schedule_list)
                    else:
                        # No existing schedule for selected week, start fresh
                        return await self.show_schedule_input_form(update, context)
                else:
                    # No week selected, show week selection
                    return await self.show_week_selection(update, context)
        
        return SCHEDULE_MENU
    
    async def show_schedule_input_form(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show schedule input form for a staff member"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        # Get week dates from context (set by week selection)
        week_dates = context.user_data.get('week_dates', {})
        week_start = context.user_data.get('week_start')
        
        # Use selected week from context, or calculate current week if not set
        if not week_dates:
            week_dates = context.user_data.get('week_dates', {})
            week_start = context.user_data.get('week_start')
            
            if not week_dates or not week_start:
                # Fallback to current week if no week selected
                week_dates, week_start = self.calculate_week_dates()
                context.user_data['week_dates'] = week_dates
                context.user_data['week_start'] = week_start
        
        date_range = self.format_date_range(week_dates)
        
        text = f"📅 *Set Schedule for {staff_name}*\n\n"
        text += f"*Week:* {date_range}\n"
        text += f"*Location:* Toronto, Canada\n\n"
        text += f"Please select the days when {staff_name} will be OFF:"
        
        # Initialize schedule data with all days as working
        schedule_data = {}
        for day in DAYS_OF_WEEK:
            schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': '', 'date': week_dates[day]}
        
        context.user_data['schedule_data'] = schedule_data
        
        return await self.show_off_days_selection(update, context)
    
    async def show_existing_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE, existing_schedule):
        """Show existing schedule for a staff member with edit options"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        # Clear any old schedule data to prevent interference, but preserve week context
        old_staff_id = context.user_data.get('current_staff_id')
        old_staff_name = context.user_data.get('current_staff_name')
        week_dates = context.user_data.get('week_dates', {})
        week_start = context.user_data.get('week_start')
        
        context.user_data.clear()
        context.user_data['current_staff_id'] = old_staff_id
        context.user_data['current_staff_name'] = old_staff_name
        context.user_data['week_dates'] = week_dates
        context.user_data['week_start'] = week_start
        
        print(f"DEBUG: show_existing_schedule - Preserved week context: {week_dates}")
        
        print(f"DEBUG: show_existing_schedule - Cleared context and set fresh data for {staff_name}")
        print(f"DEBUG: Existing schedule data: {existing_schedule}")
        
        # Convert database format to our schedule format
        schedule_data = {}
        for day in DAYS_OF_WEEK:
            schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
        
        # Fill in existing schedule data
        for day, is_working, start_time, end_time in existing_schedule:
            # Convert times to proper format for display and context
            formatted_start = self.format_time_for_display(start_time)
            formatted_end = self.format_time_for_display(end_time)
            
            print(f"DEBUG: Processing {day}: working={is_working}, start={start_time}->{formatted_start}, end={end_time}->{formatted_end}")
            
            schedule_data[day] = {
                'is_working': bool(is_working),
                'start_time': formatted_start or '',
                'end_time': formatted_end or ''
            }
        
        context.user_data['schedule_data'] = schedule_data
        print(f"DEBUG: Final schedule_data in context: {schedule_data}")
        
        # Use selected week from context, or calculate current week if not set
        week_dates = context.user_data.get('week_dates', {})
        week_start = context.user_data.get('week_start')
        
        if not week_dates or not week_start:
            # Fallback to current week if no week selected
            week_dates, week_start = self.calculate_week_dates()
            context.user_data['week_dates'] = week_dates
            context.user_data['week_start'] = week_start
            print(f"DEBUG: Fallback to current week in show_existing_schedule: {week_dates}")
        else:
            print(f"DEBUG: Using selected week in show_existing_schedule: {week_dates}")
        
        # Build display text
        text = f"📅 *{staff_name}'s Current Schedule*\n\n"
        text += "*You already added these times and days:*\n\n"
        
        working_days = []
        off_days = []
        
        for day in DAYS_OF_WEEK:
            day_data = schedule_data[day]
            if day_data['is_working'] and day_data['start_time'] and day_data['end_time']:
                working_days.append(f"✅ {day}: {day_data['start_time']} - {day_data['end_time']}")
            elif not day_data['is_working']:
                off_days.append(f"🔴 {day}: OFF")
            else:
                working_days.append(f"⏰ {day}: Not set")
        
        if working_days:
            text += "*Working Days:*\n"
            text += "\n".join(working_days) + "\n\n"
        
        if off_days:
            text += "*Off Days:*\n"
            text += "\n".join(off_days) + "\n\n"
        
        text += "*Do you want to edit this schedule?*"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Edit Schedule", callback_data="edit_existing_schedule"),
                InlineKeyboardButton("❌ No, Keep Current", callback_data="back_schedule_menu")
            ],
            [InlineKeyboardButton("👀 Back to View Schedules", callback_data="view_current_schedules")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def show_off_days_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show off days selection interface"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        week_dates = context.user_data.get('week_dates', {})
        week_start = context.user_data.get('week_start')
        
        # Use selected week from context, or calculate current week if not set
        if not week_dates or not week_start:
            # Fallback to current week if no week selected
            week_dates, week_start = self.calculate_week_dates()
            context.user_data['week_dates'] = week_dates
            context.user_data['week_start'] = week_start
            print(f"DEBUG: show_off_days_selection - Fallback to current week: {week_dates}")
        else:
            print(f"DEBUG: show_off_days_selection - Using selected week: {week_dates}")
        
        date_range = self.format_date_range(week_dates)
        
        text = f"📅 *Select Off Days for {staff_name}*\n\n"
        text += f"*Week:* {date_range}\n\n"
        text += f"*Click on days to mark them as OFF:*\n"
        
        # Show current selection
        selected_off_days = context.user_data.get('selected_off_days', [])
        if selected_off_days:
            off_days_text = ", ".join(selected_off_days)
            text += f"\n*Selected OFF days:* {off_days_text}\n"
        
        keyboard = []
        
        # Create day selection buttons with dates
        for day in DAYS_OF_WEEK:
            date = week_dates.get(day, '')
            date_str = date.strftime("%b %d") if date else ""
            
            if day in selected_off_days:
                button_text = f"🔴 {day} ({date_str})"
                callback_data = f"toggle_off_day_{day}"
            else:
                button_text = f"🟢 {day} ({date_str})"
                callback_data = f"toggle_off_day_{day}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("✅ Confirm Off Days", callback_data="confirm_off_days"),
            InlineKeyboardButton("❌ Cancel", callback_data="back_schedule_menu")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def handle_schedule_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle schedule input interactions"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_schedule_menu":
            return await self.show_schedule_menu(update, context)
        elif query.data == "save_schedule":
            return await self.save_schedule(update, context)
        elif query.data == "reset_schedule":
            # Reset all days to Working (On)
            schedule_data = {}
            for day in DAYS_OF_WEEK:
                schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
            context.user_data['schedule_data'] = schedule_data
            return await self.show_weekly_schedule_view(update, context)
        elif query.data.startswith("edit_day_"):
            day = query.data.split("_")[2]
            context.user_data['editing_day'] = day
            return await self.show_day_edit_view(update, context)
        elif query.data == "toggle_day_status":
            return await self.toggle_day_status(update, context)
        elif query.data == "set_start_time":
            context.user_data['waiting_for'] = 'start_time'
            await query.edit_message_text(
                f"⏰ *Set Start Time*\n\nPlease enter the start time in HH:MM format (e.g., 12:10):\n\n*Valid range:* 09:45 to 21:00",
                parse_mode=ParseMode.MARKDOWN
            )
            return SCHEDULE_INPUT
        elif query.data == "set_end_time":
            context.user_data['waiting_for'] = 'end_time'
            await query.edit_message_text(
                f"⏰ *Set End Time*\n\nPlease enter the end time in HH:MM format (e.g., 21:00):\n\n*Valid range:* 09:45 to 21:00",
                parse_mode=ParseMode.MARKDOWN
            )
            return SCHEDULE_INPUT
        elif query.data == "done_editing_day":
            # Refresh data from database before showing weekly view
            staff_id = context.user_data.get('current_staff_id')
            if staff_id:
                await self.refresh_schedule_data(context, staff_id)
            return await self.show_weekly_schedule_view(update, context)
        elif query.data == "back_to_week":
            # Refresh data from database before showing weekly view
            staff_id = context.user_data.get('current_staff_id')
            if staff_id:
                await self.refresh_schedule_data(context, staff_id)
            return await self.show_weekly_schedule_view(update, context)
        elif query.data == "back_to_day_edit":
            return await self.back_to_day_edit(update, context)
        elif query.data == "start_multi_select":
            # Start multi-select mode
            context.user_data['multi_select_mode'] = True
            context.user_data['selected_off_days'] = []
            return await self.show_weekly_schedule_view(update, context)
        elif query.data.startswith("toggle_off_day_"):
            # Toggle a day in off days selection
            day = query.data.split("_")[3]
            selected_off_days = context.user_data.get('selected_off_days', [])
            
            if day in selected_off_days:
                selected_off_days.remove(day)
            else:
                selected_off_days.append(day)
            
            context.user_data['selected_off_days'] = selected_off_days
            return await self.show_off_days_selection(update, context)
        elif query.data == "confirm_off_days":
            return await self.show_off_days_confirmation(update, context)
        elif query.data == "cancel_multi_select":
            # Cancel multi-select mode
            context.user_data['multi_select_mode'] = False
            context.user_data['selected_off_days'] = []
            return await self.show_weekly_schedule_view(update, context)
        elif query.data == "back_to_multi_select":
            # Go back to multi-select mode
            context.user_data['multi_select_mode'] = True
            return await self.show_weekly_schedule_view(update, context)
        elif query.data == "apply_off_days":
            return await self.apply_off_days(update, context)
        elif query.data == "continue_editing":
            return await self.show_weekly_schedule_view(update, context)
        elif query.data == "set_working_hours":
            return await self.show_working_hours_setup(update, context)
        elif query.data == "confirm_working_hours":
            return await self.confirm_working_hours(update, context)
        elif query.data == "reset_working_hours":
            # Reset only working days to have no times
            schedule_data = context.user_data.get('schedule_data', {})
            for day in DAYS_OF_WEEK:
                day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
                if day_data['is_working']:
                    schedule_data[day]['start_time'] = ''
                    schedule_data[day]['end_time'] = ''
            context.user_data['schedule_data'] = schedule_data
            return await self.show_working_hours_setup(update, context)
        elif query.data == "back_to_hours_setup":
            return await self.show_working_hours_setup(update, context)
        elif query.data == "back_to_schedule":
            return await self.show_weekly_schedule_view(update, context)
        elif query.data == "continue_time_setting":
            return await self.start_time_setting(update, context)
        elif query.data == "view_complete_schedule":
            return await self.show_final_schedule_summary(update, context)
        elif query.data == "back_to_time_setting":
            return await self.start_time_setting(update, context)
        elif query.data == "start_over":
            return await self.show_off_days_selection(update, context)
        elif query.data == "back_to_off_selection":
            return await self.show_off_days_selection(update, context)
        elif query.data == "cancel_time_setting":
            return await self.show_off_days_selection(update, context)
        elif query.data.startswith("start_"):
            return await self.handle_start_time_selection(update, context)
        elif query.data.startswith("end_"):
            return await self.handle_end_time_selection(update, context)
        elif query.data == "edit_schedule":
            return await self.show_edit_options(update, context)
        elif query.data == "edit_off_days":
            return await self.edit_off_days(update, context)
        elif query.data == "edit_time_slots":
            return await self.edit_time_slots(update, context)
        elif query.data == "back_to_summary":
            return await self.show_final_schedule_summary(update, context)
        elif query.data.startswith("edit_day_"):
            return await self.edit_specific_day(update, context)
        elif query.data.startswith("edit_start_"):
            return await self.handle_edit_start_time(update, context)
        elif query.data.startswith("edit_end_"):
            return await self.handle_edit_end_time(update, context)
        elif query.data == "continue_time_setting":
            return await self.start_time_setting(update, context)
        elif query.data == "back_to_time_setting":
            return await self.start_time_setting(update, context)
        elif query.data == "edit_existing_schedule":
            return await self.show_edit_options(update, context)
        elif query.data == "finish_editing":
            return await self.show_final_schedule_summary(update, context)
        elif query.data == "edit_another_day":
            return await self.show_edit_options(update, context)
        elif query.data == "edit_next_day":
            return await self.edit_next_day(update, context)
        elif query.data == "cancel_editing":
            return await self.show_final_schedule_summary(update, context)
        elif query.data == "show_start_time_picker":
            return await self.show_start_time_picker(update, context)
        elif query.data == "show_end_time_picker":
            return await self.show_end_time_picker(update, context)
        elif query.data == "back_to_day_edit":
            return await self.back_to_day_edit(update, context)
        elif query.data.startswith("select_day_"):
            day = query.data.split("_")[2]
            selected_days = context.user_data.get('selected_days_for_edit', [])
            if day not in selected_days:
                selected_days.append(day)
            context.user_data['selected_days_for_edit'] = selected_days
            return await self.edit_time_slots(update, context)
        elif query.data.startswith("deselect_day_"):
            day = query.data.split("_")[2]
            selected_days = context.user_data.get('selected_days_for_edit', [])
            if day in selected_days:
                selected_days.remove(day)
            context.user_data['selected_days_for_edit'] = selected_days
            return await self.edit_time_slots(update, context)
        elif query.data == "select_all_days":
            schedule_data = context.user_data.get('schedule_data', {})
            working_days = []
            for day in DAYS_OF_WEEK:
                day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
                if day_data['is_working']:
                    working_days.append(day)
            context.user_data['selected_days_for_edit'] = working_days
            return await self.edit_time_slots(update, context)
        elif query.data == "clear_day_selection":
            context.user_data['selected_days_for_edit'] = []
            return await self.edit_time_slots(update, context)
        elif query.data == "edit_selected_days":
            return await self.edit_selected_days(update, context)
        elif query.data == "back_to_edit_options":
            return await self.show_edit_options(update, context)
        elif query.data == "set_start_all_selected":
            return await self.set_start_time_all_selected(update, context)
        elif query.data == "set_end_all_selected":
            return await self.set_end_time_all_selected(update, context)
        elif query.data == "set_both_all_selected":
            return await self.set_both_times_all_selected(update, context)
        elif query.data.startswith("set_start_all_"):
            return await self.handle_set_start_all(update, context)
        elif query.data.startswith("set_end_all_"):
            return await self.handle_set_end_all(update, context)
        elif query.data.startswith("set_both_all_"):
            return await self.handle_set_both_all(update, context)
        elif query.data == "back_to_edit_selected":
            return await self.edit_selected_days(update, context)
        elif query.data == "back_to_day_selection":
            return await self.edit_time_slots(update, context)
        elif query.data == "skip_current_day":
            return await self.skip_current_day(update, context)
        elif query.data == "cancel_editing_selected":
            return await self.cancel_editing_selected(update, context)
        elif query.data == "continue_to_next_day":
            return await self.continue_to_next_day(update, context)
        elif query.data == "reset_all_schedules":
            return await self.reset_all_schedules(update, context)
        elif query.data == "schedule_history":
            return await self.show_schedule_history(update, context)
        elif query.data.startswith("view_week_"):
            week_key = query.data.split("_")[2]
            return await self.view_week_schedule(update, context, week_key)
        
        return SCHEDULE_INPUT
    
    async def handle_start_time_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle start time selection from time picker"""
        selected_time = update.callback_query.data.split("_")[1]
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if not remaining_days:
            await update.callback_query.answer("❌ No days remaining")
            return await self.show_final_schedule_summary(update, context)
        
        current_day = remaining_days[0]
        schedule_data = context.user_data.get('schedule_data', {})
        
        if current_day not in schedule_data:
            schedule_data[current_day] = {'is_working': True, 'start_time': '', 'end_time': ''}
        
        schedule_data[current_day]['start_time'] = selected_time
        context.user_data['schedule_data'] = schedule_data
        
        # Show progress update
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"✅ *{current_day} Start Time Set!*\n\n"
        text += f"{staff_name} will start at {selected_time} on {current_day}\n\n"
        
        # Show remaining days
        text += f"*Remaining Days:*\n"
        for i, day in enumerate(remaining_days, 1):
            text += f"{i}. {day}\n"
        
        text += f"\n*Setting times for:* {current_day}\n"
        text += f"Start: ✅ {selected_time}\n"
        text += f"End: {'✅ ' + schedule_data[current_day]['end_time'] if schedule_data[current_day]['end_time'] else '⏰ Not set'}\n\n"
        text += f"Please select the end time:"
        
        # End time options
        end_times = ["14:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
        
        keyboard = []
        end_row = []
        for time in end_times:
            if time == schedule_data[current_day].get('end_time'):
                end_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"end_{time}"))
            else:
                end_row.append(InlineKeyboardButton(f"🔴 {time}", callback_data=f"end_{time}"))
        keyboard.append(end_row)
        
        # Action buttons
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_time_setting")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def handle_end_time_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle end time selection from time picker"""
        selected_time = update.callback_query.data.split("_")[1]
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if not remaining_days:
            await update.callback_query.answer("❌ No days remaining")
            return await self.show_final_schedule_summary(update, context)
        
        current_day = remaining_days[0]
        schedule_data = context.user_data.get('schedule_data', {})
        
        if current_day not in schedule_data:
            schedule_data[current_day] = {'is_working': True, 'start_time': '', 'end_time': ''}
        
        # Validate time range
        start_time = schedule_data[current_day].get('start_time', '')
        if start_time:
            time_valid, time_error = ScheduleValidator.validate_time_range(start_time, selected_time)
            if not time_valid:
                await update.callback_query.answer(f"❌ {time_error}")
                return SCHEDULE_INPUT
        
        schedule_data[current_day]['end_time'] = selected_time
        context.user_data['schedule_data'] = schedule_data
        
        # Check if both times are set
        if schedule_data[current_day]['start_time'] and schedule_data[current_day]['end_time']:
            # Both times set, move to next day
            remaining_days.pop(0)
            context.user_data['remaining_working_days'] = remaining_days
            
            # Show completion message with progress
            staff_name = context.user_data.get('current_staff_name', 'Unknown')
            start_time = schedule_data[current_day]['start_time']
            end_time = schedule_data[current_day]['end_time']
            
            text = f"✅ *{current_day} Complete!*\n\n"
            text += f"{staff_name} will work on {current_day}:\n"
            text += f"*{start_time} - {end_time}*\n\n"
            
            if remaining_days:
                # Show remaining days and continue
                text += f"*Remaining Days:*\n"
                for i, day in enumerate(remaining_days, 1):
                    text += f"{i}. {day}\n"
                
                keyboard = [
                    [InlineKeyboardButton("✏️ Edit This Day", callback_data=f"edit_day_{current_day}")],
                    [InlineKeyboardButton("⏰ Continue to Next", callback_data="continue_time_setting")]
                ]
            else:
                # All days completed
                text += "All working days completed!"
                keyboard = [
                    [InlineKeyboardButton("✏️ Edit This Day", callback_data=f"edit_day_{current_day}")],
                    [InlineKeyboardButton("📅 View Complete Schedule", callback_data="view_complete_schedule")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            # Show updated interface with selected end time
            return await self.show_time_picker_with_selection(update, context)
        
        return SCHEDULE_INPUT
    
    async def show_time_picker_with_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show time picker with current selections highlighted"""
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if not remaining_days:
            return await self.show_final_schedule_summary(update, context)
        
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        current_day = remaining_days[0]
        schedule_data = context.user_data.get('schedule_data', {})
        day_data = schedule_data.get(current_day, {'is_working': True, 'start_time': '', 'end_time': ''})
        
        text = f"⏰ *Set Working Times for {staff_name}*\n\n"
        text += f"*Available Working Days:*\n"
        
        for i, day in enumerate(remaining_days, 1):
            text += f"{i}. {day}\n"
        
        text += f"\n*Setting times for:* {current_day}\n"
        text += f"Start: {day_data['start_time'] or 'Not set'}\n"
        text += f"End: {day_data['end_time'] or 'Not set'}\n\n"
        text += f"Please select the remaining time:"
        
        # Start time options (9:45 AM to 5 PM)
        start_times = ["09:45", "10:00", "11:00", "12:00", "13:00", "15:00", "17:00"]
        end_times = ["14:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
        
        keyboard = []
        
        # Start time row
        start_row = []
        for time in start_times:
            if time == day_data['start_time']:
                start_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"start_{time}"))
            else:
                start_row.append(InlineKeyboardButton(f"🟢 {time}", callback_data=f"start_{time}"))
        keyboard.append(start_row)
        
        # End time row
        end_row = []
        for time in end_times:
            if time == day_data['end_time']:
                end_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"end_{time}"))
            else:
                end_row.append(InlineKeyboardButton(f"🔴 {time}", callback_data=f"end_{time}"))
        keyboard.append(end_row)
        
        # Action buttons
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_time_setting")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def show_off_days_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show confirmation for selected off days"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        selected_off_days = context.user_data.get('selected_off_days', [])
        
        if not selected_off_days:
            text = f"📅 *Confirm Schedule for {staff_name}*\n\n"
            text += f"✅ *No Off Days Selected*\n\n"
            text += f"{staff_name} will work *all 7 days* of the week.\n\n"
            text += f"You will be prompted to set working times for each day.\n\n"
            text += "Is this correct?"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Continue", callback_data="apply_off_days"),
                    InlineKeyboardButton("❌ No, Go Back", callback_data="back_to_off_selection")
                ]
            ]
        else:
            off_days_text = ", ".join(selected_off_days)
            text = f"📅 *Confirm Off Days for {staff_name}*\n\n"
            text += f"The OFF days for {staff_name} will be:\n\n"
            text += f"*{off_days_text}*\n\n"
            text += "Is this correct?"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Confirm", callback_data="apply_off_days"),
                    InlineKeyboardButton("❌ No, Go Back", callback_data="back_to_off_selection")
                ]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def apply_off_days(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Apply the selected off days to the schedule and start time setting"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        selected_off_days = context.user_data.get('selected_off_days', [])
        schedule_data = context.user_data.get('schedule_data', {})
        
        # Apply off days to schedule
        for day in DAYS_OF_WEEK:
            if day not in schedule_data:
                schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
            
            if day in selected_off_days:
                schedule_data[day]['is_working'] = False
                schedule_data[day]['start_time'] = ''
                schedule_data[day]['end_time'] = ''
            else:
                schedule_data[day]['is_working'] = True
        
        context.user_data['schedule_data'] = schedule_data
        context.user_data['selected_off_days'] = []
        
        # Get working days that need times set
        working_days = [day for day in DAYS_OF_WEEK if day not in selected_off_days]
        context.user_data['remaining_working_days'] = working_days.copy()
        
        # Start setting times for the first working day
        return await self.start_time_setting(update, context)
    
    async def start_time_setting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the step-by-step time setting process"""
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if not remaining_days:
            # All days are done, show final summary
            return await self.show_final_schedule_summary(update, context)
        
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        current_day = remaining_days[0]
        schedule_data = context.user_data.get('schedule_data', {})
        week_dates = context.user_data.get('week_dates', {})
        date_range = self.format_date_range(week_dates)
        
        text = f"⏰ *Set Working Times for {staff_name}*\n\n"
        text += f"*Week:* {date_range}\n\n"
        
        # Show current schedule progress with dates
        text += f"*Current Schedule:*\n"
        for day in DAYS_OF_WEEK:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            date = week_dates.get(day, '')
            date_str = date.strftime("%b %d") if date else ""
            
            if day_data['is_working'] and day_data['start_time'] and day_data['end_time']:
                text += f"✅ {day} ({date_str}): {day_data['start_time']} - {day_data['end_time']}\n"
            elif not day_data['is_working']:
                text += f"🔴 {day} ({date_str}): OFF\n"
            else:
                text += f"⏰ {day} ({date_str}): Not set\n"
        
        text += f"\n*Available Working Days:*\n"
        for i, day in enumerate(remaining_days, 1):
            date = week_dates.get(day, '')
            date_str = date.strftime("%b %d") if date else ""
            text += f"{i}. {day} ({date_str})\n"
        
        current_date = week_dates.get(current_day, '')
        current_date_str = current_date.strftime("%B %d") if current_date else ""
        
        text += f"\n*Setting times for:* {current_day} ({current_date_str})\n\n"
        text += f"Please select the start and end times:"
        
        # Start time options (9:45 AM to 5 PM)
        start_times = ["09:45", "10:00", "11:00", "12:00", "13:00", "15:00", "17:00"]
        end_times = ["14:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
        
        keyboard = []
        
        # Start time row
        start_row = []
        for time in start_times:
            start_row.append(InlineKeyboardButton(f"🟢 {time}", callback_data=f"start_{time}"))
        keyboard.append(start_row)
        
        # End time row
        end_row = []
        for time in end_times:
            end_row.append(InlineKeyboardButton(f"🔴 {time}", callback_data=f"end_{time}"))
        keyboard.append(end_row)
        
        # Action buttons
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_time_setting")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def show_final_schedule_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the final schedule summary"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        schedule_data = context.user_data.get('schedule_data', {})
        week_dates = context.user_data.get('week_dates', {})
        date_range = self.format_date_range(week_dates)
        
        # Build the complete schedule summary
        text = f"📅 *{staff_name}'s Complete Schedule*\n\n"
        text += f"*Week:* {date_range}\n"
        text += f"*Location:* Toronto, Canada\n\n"
        
        # Show all days with their status and times
        for day in DAYS_OF_WEEK:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            date = week_dates.get(day, '')
            date_str = date.strftime("%B %d") if date else ""
            
            if day_data['is_working'] and day_data['start_time'] and day_data['end_time']:
                text += f"✅ *{day} ({date_str}):* {day_data['start_time']} - {day_data['end_time']}\n"
            elif not day_data['is_working']:
                text += f"🔴 *{day} ({date_str}):* OFF\n"
            else:
                text += f"⏰ *{day} ({date_str}):* Not set\n"
        
        text += f"\nIs this schedule correct for {staff_name}?"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Save", callback_data="save_schedule"),
                InlineKeyboardButton("✏️ Edit", callback_data="edit_schedule")
            ],
            [InlineKeyboardButton("👀 Back to View Schedules", callback_data="view_current_schedules")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def show_edit_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show edit options for the schedule"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"✏️ *Edit {staff_name}'s Schedule*\n\n"
        text += f"What would you like to edit?"
        
        keyboard = [
            [InlineKeyboardButton("📅 Change Off Days", callback_data="edit_off_days")],
            [InlineKeyboardButton("⏰ Change Time Slots", callback_data="edit_time_slots")],
            [InlineKeyboardButton("🔙 Back to Summary", callback_data="back_to_summary")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def edit_off_days(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit off days for the current staff member"""
        # Get current off days from schedule data
        schedule_data = context.user_data.get('schedule_data', {})
        current_off_days = []
        
        for day in DAYS_OF_WEEK:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if not day_data['is_working']:
                current_off_days.append(day)
        
        # Set current off days as selected
        context.user_data['selected_off_days'] = current_off_days
        
        # Use selected week from context, or calculate current week if not set
        week_dates = context.user_data.get('week_dates', {})
        week_start = context.user_data.get('week_start')
        
        if not week_dates or not week_start:
            # Fallback to current week if no week selected
            week_dates, week_start = self.calculate_week_dates()
            context.user_data['week_dates'] = week_dates
            context.user_data['week_start'] = week_start
            print(f"DEBUG: edit_off_days - Fallback to current week: {week_dates}")
        else:
            print(f"DEBUG: edit_off_days - Using selected week: {week_dates}")
        
        # Go to off days selection
        return await self.show_off_days_selection(update, context)
    
    async def edit_time_slots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit time slots for the current staff member"""
        # Get current working days from schedule data
        schedule_data = context.user_data.get('schedule_data', {})
        working_days = []
        
        for day in DAYS_OF_WEEK:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['is_working']:
                working_days.append(day)
        
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"✏️ *Edit Time Slots for {staff_name}*\n\n"
        text += f"*Select the days you want to edit:*\n\n"
        
        # Show current schedule
        text += f"*Current Schedule:*\n"
        for day in working_days:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['start_time'] and day_data['end_time']:
                text += f"✅ {day}: {day_data['start_time']} - {day_data['end_time']}\n"
            else:
                text += f"⏰ {day}: Not set\n"
        
        text += f"\n*Click on days to select/deselect them:*"
        
        # Initialize selected days list if not exists
        if 'selected_days_for_edit' not in context.user_data:
            context.user_data['selected_days_for_edit'] = []
        
        keyboard = []
        
        # Create day selection buttons
        for day in working_days:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            current_time = f"{day_data['start_time']} - {day_data['end_time']}" if day_data['start_time'] and day_data['end_time'] else "Not set"
            
            if day in context.user_data['selected_days_for_edit']:
                # Day is selected
                button_text = f"✅ {day} ({current_time})"
                callback_data = f"deselect_day_{day}"
            else:
                # Day is not selected
                button_text = f"⭕ {day} ({current_time})"
                callback_data = f"select_day_{day}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Action buttons
        keyboard.append([
            InlineKeyboardButton("✅ Edit Selected Days", callback_data="edit_selected_days"),
            InlineKeyboardButton("🔄 Select All", callback_data="select_all_days")
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Clear Selection", callback_data="clear_day_selection"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_edit_options")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def edit_specific_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE, day=None):
        """Edit a specific day's times"""
        if day is None:
            day = update.callback_query.data.split("_")[2]  # edit_day_Tuesday -> Tuesday
        
        # Set the editing_day context variable for time picker functions
        context.user_data['editing_day'] = day
        
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        schedule_data = context.user_data.get('schedule_data', {})
        day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
        
        text = f"✏️ *Edit {day} for {staff_name}*\n\n"
        text += f"Current times: {day_data['start_time']} - {day_data['end_time']}\n\n"
        text += f"Please select new times:"
        
        # Start time options (9:45 AM to 5 PM)
        start_times = ["09:45", "10:00", "11:00", "12:00", "13:00", "15:00", "17:00"]
        end_times = ["14:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
        
        keyboard = []
        
        # Start time row
        start_row = []
        for time in start_times:
            if time == day_data['start_time']:
                start_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"edit_start_{day}_{time}"))
            else:
                start_row.append(InlineKeyboardButton(f"🟢 {time}", callback_data=f"edit_start_{day}_{time}"))
        keyboard.append(start_row)
        
        # End time row
        end_row = []
        for time in end_times:
            if time == day_data['end_time']:
                end_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"edit_end_{day}_{time}"))
            else:
                end_row.append(InlineKeyboardButton(f"🔴 {time}", callback_data=f"edit_end_{day}_{time}"))
        keyboard.append(end_row)
        
        # Action buttons
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_edit_confirmation")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def handle_edit_start_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle start time selection when editing a specific day"""
        print(f"DEBUG: handle_edit_start_time called")
        # edit_start_Tuesday_10:00 -> Tuesday, 10:00
        parts = update.callback_query.data.split("_")
        day = parts[2]
        selected_time = parts[3]
        
        print(f"DEBUG: Editing day {day} with start time {selected_time}")
        
        schedule_data = context.user_data.get('schedule_data', {})
        if day not in schedule_data:
            schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
        
        schedule_data[day]['start_time'] = selected_time
        context.user_data['schedule_data'] = schedule_data
        
        print(f"DEBUG: Start time set in context data for {day}")
        
        # Show end time picker (enforce both times must be set)
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"✏️ *Editing {day} for {staff_name}*\n\n"
        text += f"*Start time set:* {selected_time}\n"
        text += f"*Current end time:* {schedule_data[day]['end_time'] or 'Not set'}\n\n"
        text += f"⚠️ *Both start and end times must be set when editing*\n\n"
        text += f"*Please select the end time:*"
        
        # End time options (exactly like original)
        end_times = ["14:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
        
        keyboard = []
        end_row = []
        for time in end_times:
            if time == schedule_data[day].get('end_time'):
                end_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"edit_end_{day}_{time}"))
            else:
                end_row.append(InlineKeyboardButton(f"🔴 {time}", callback_data=f"edit_end_{day}_{time}"))
        keyboard.append(end_row)
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("⏭️ Skip This Day", callback_data="skip_current_day"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_editing_selected")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def handle_edit_end_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle end time selection when editing a specific day"""
        print(f"DEBUG: handle_edit_end_time called")
        # edit_end_Tuesday_19:00 -> Tuesday, 19:00
        parts = update.callback_query.data.split("_")
        day = parts[2]
        selected_time = parts[3]
        
        print(f"DEBUG: Editing day {day} with end time {selected_time}")
        
        schedule_data = context.user_data.get('schedule_data', {})
        if day not in schedule_data:
            schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
        
        # Validate time range
        start_time = schedule_data[day].get('start_time', '')
        if start_time:
            time_valid, time_error = ScheduleValidator.validate_time_range(start_time, selected_time)
            if not time_valid:
                await update.callback_query.answer(f"❌ {time_error}")
                return SCHEDULE_INPUT
        
        schedule_data[day]['end_time'] = selected_time
        context.user_data['schedule_data'] = schedule_data
        
        print(f"DEBUG: End time set in context data for {day}")
        
        # CRITICAL FIX: Save this single day to database immediately
        await self.save_single_day_edit(update, context, day)
        
        print(f"DEBUG: About to call show_edit_confirmation")
        # Show confirmation message
        return await self.show_edit_confirmation(update, context, day)
    
    async def show_edit_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, edited_day):
        """Show confirmation after editing a day"""
        print(f"DEBUG: show_edit_confirmation called for day: {edited_day}")
        
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        schedule_data = context.user_data.get('schedule_data', {})
        day_data = schedule_data.get(edited_day, {'is_working': True, 'start_time': '', 'end_time': ''})
        
        text = f"✅ *{edited_day} Updated!*\n\n"
        text += f"{staff_name}'s schedule for {edited_day}:\n"
        text += f"*{day_data['start_time']} - {day_data['end_time']}*\n\n"
        
        # Check if we're in multi-day editing mode
        remaining_days = context.user_data.get('remaining_working_days', [])
        selected_days = context.user_data.get('selected_days_for_edit', [])
        
        if remaining_days and selected_days:
            # We're in multi-day editing mode
            text += f"*Editing Progress:*\n"
            text += f"Completed: {len(selected_days) - len(remaining_days) + 1}/{len(selected_days)}\n"
            text += f"Remaining: {len(remaining_days) - 1} days\n\n"
            
            if len(remaining_days) > 1:
                # More days to edit
                next_day = remaining_days[1] if len(remaining_days) > 1 else None
                text += f"*Next day to edit:* {next_day}\n\n"
                
                keyboard = [
                    [InlineKeyboardButton("✏️ Edit This Day Again", callback_data=f"edit_day_{edited_day}")],
                    [InlineKeyboardButton("⏭️ Continue to Next Day", callback_data="continue_to_next_day")],
                    [InlineKeyboardButton("✅ Finish Editing", callback_data="finish_editing")]
                ]
            else:
                # Last day completed
                text += f"*All selected days completed!*\n\n"
                
                keyboard = [
                    [InlineKeyboardButton("✏️ Edit This Day Again", callback_data=f"edit_day_{edited_day}")],
                    [InlineKeyboardButton("✅ Finish Editing", callback_data="finish_editing")]
                ]
        else:
            # Single day editing mode (original behavior)
            # Show current full schedule
            text += f"*Current Complete Schedule:*\n"
            for day in DAYS_OF_WEEK:
                day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
                if day_data['is_working'] and day_data['start_time'] and day_data['end_time']:
                    text += f"✅ {day}: {day_data['start_time']} - {day_data['end_time']}\n"
                elif not day_data['is_working']:
                    text += f"🔴 {day}: OFF\n"
                else:
                    text += f"⏰ {day}: Not set\n"
            
            text += f"\n*Is everything good now, or do you want to edit another day?*"
            
            keyboard = [
                [InlineKeyboardButton("✏️ Edit This Day", callback_data=f"edit_day_{edited_day}")],
                [InlineKeyboardButton("⏭️ Next Day", callback_data="edit_next_day")],
                [InlineKeyboardButton("✅ All Good", callback_data="finish_editing")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_editing")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        print(f"DEBUG: About to edit message with new confirmation options")
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def show_working_hours_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show working hours setup interface"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        schedule_data = context.user_data.get('schedule_data', {})
        
        # Get working days
        working_days = []
        for day in DAYS_OF_WEEK:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['is_working']:
                working_days.append(day)
        
        text = f"⏰ *Set Working Hours for {staff_name}*\n\n"
        text += "*Working Days:*\n"
        
        keyboard = []
        
        for day in working_days:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            
            if day_data['start_time'] and day_data['end_time']:
                time_info = f"{day_data['start_time']} - {day_data['end_time']}"
                status_emoji = "✅"
            else:
                time_info = "Not set"
                status_emoji = "⏰"
            
            text += f"{status_emoji} *{day}:* {time_info}\n"
            keyboard.append([InlineKeyboardButton(f"{status_emoji} {day}", callback_data=f"edit_day_{day}")])
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("✅ Confirm All Hours", callback_data="confirm_working_hours"),
            InlineKeyboardButton("🔄 Reset Hours", callback_data="reset_working_hours")
        ])
        keyboard.append([InlineKeyboardButton("🔙 Back to Schedule", callback_data="back_to_schedule")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def confirm_working_hours(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show confirmation for working hours"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        schedule_data = context.user_data.get('schedule_data', {})
        
        # Check if all working days have times set
        working_days_without_times = []
        working_days_with_times = []
        
        for day in DAYS_OF_WEEK:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['is_working']:
                if day_data['start_time'] and day_data['end_time']:
                    working_days_with_times.append(f"{day}: {day_data['start_time']} - {day_data['end_time']}")
                else:
                    working_days_without_times.append(day)
        
        if working_days_without_times:
            # Some working days don't have times set
            missing_days_text = ", ".join(working_days_without_times)
            text = f"⚠️ *Incomplete Working Hours*\n\n"
            text += f"The following working days don't have times set:\n\n"
            text += f"*{missing_days_text}*\n\n"
            text += "Please set times for all working days before confirming."
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Hours Setup", callback_data="back_to_hours_setup")]]
        else:
            # All working days have times set
            working_schedule_text = "\n".join(working_days_with_times)
            off_days = [day for day in DAYS_OF_WEEK if not schedule_data.get(day, {}).get('is_working', True)]
            off_days_text = ", ".join(off_days) if off_days else "None"
            
            text = f"📅 *Confirm Schedule for {staff_name}*\n\n"
            text += f"*Working Schedule:*\n{working_schedule_text}\n\n"
            text += f"*Off Days:* {off_days_text}\n\n"
            text += "Is this schedule correct?"
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Save Schedule", callback_data="save_schedule"),
                    InlineKeyboardButton("❌ No, Edit More", callback_data="back_to_hours_setup")
                ]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def show_day_edit_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show edit view for a specific day"""
        day = context.user_data.get('editing_day')
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        schedule_data = context.user_data.get('schedule_data', {})
        
        day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
        
        # Create keyboard for the day
        keyboard = []
        
        # Status toggle button
        status_text = "🟢 Working" if day_data['is_working'] else "🔴 Off"
        keyboard.append([InlineKeyboardButton(f"Status: {status_text}", callback_data="toggle_day_status")])        
        if day_data['is_working']:
            # Show current times
            start_time = day_data['start_time'] or 'Not set'
            end_time = day_data['end_time'] or 'Not set'
            
            # Time picker buttons - Start Time
            keyboard.append([InlineKeyboardButton(f"🕐 Start Time: {start_time}", callback_data="show_start_time_picker")])
            
            # Time picker buttons - End Time  
            keyboard.append([InlineKeyboardButton(f"🕐 End Time: {end_time}", callback_data="show_end_time_picker")])
        
        # Navigation buttons
        keyboard.append([
            InlineKeyboardButton("✅ Done", callback_data="done_editing_day"),
            InlineKeyboardButton("🔙 Back to Week", callback_data="back_to_week")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"📅 *Editing {day} for {staff_name}*\n\n"
        
        if day_data['is_working']:
            text += f"Status: 🟢 Working\n"
            text += f"Start Time: {day_data['start_time'] or 'Not set'}\n"
            text += f"End Time: {day_data['end_time'] or 'Not set'}\n\n"
            text += f"*Click the time buttons below to set start and end times*"
        else:
            text += f"Status: 🔴 Off"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return SCHEDULE_INPUT
    
    async def handle_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle time input from user"""
        time_input = update.message.text.strip()
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if not remaining_days:
            await update.message.reply_text("❌ Invalid input. Please use the buttons.")
            return await self.start_time_setting(update, context)
        
        # Validate time range format (HH:MM - HH:MM)
        is_valid, error_msg = self.validate_time_range_format(time_input)
        if not is_valid:
            keyboard = [[InlineKeyboardButton("🔙 Back to Time Setting", callback_data="back_to_time_setting")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"❌ {error_msg}\n\nPlease use format: HH:MM - HH:MM (e.g., 9:23 - 18:45)",
                reply_markup=reply_markup
            )
            return SCHEDULE_INPUT
        
        # Parse start and end times
        start_time, end_time = time_input.split(' - ')
        
        # Validate individual times
        start_valid, start_error = ScheduleValidator.validate_time_format(start_time)
        if not start_valid:
            await update.message.reply_text(f"❌ Start time error: {start_error}")
            return SCHEDULE_INPUT
        
        end_valid, end_error = ScheduleValidator.validate_time_format(end_time)
        if not end_valid:
            await update.message.reply_text(f"❌ End time error: {end_error}")
            return SCHEDULE_INPUT
        
        # Validate time range
        time_valid, time_error = ScheduleValidator.validate_time_range(start_time, end_time)
        if not time_valid:
            await update.message.reply_text(f"❌ {time_error}")
            return SCHEDULE_INPUT
        
        # Get current day and update schedule data
        current_day = remaining_days[0]
        schedule_data = context.user_data.get('schedule_data', {})
        
        if current_day not in schedule_data:
            schedule_data[current_day] = {'is_working': True, 'start_time': '', 'end_time': ''}
        
        schedule_data[current_day]['start_time'] = start_time
        schedule_data[current_day]['end_time'] = end_time
        context.user_data['schedule_data'] = schedule_data
        
        # Remove current day from remaining days
        remaining_days.pop(0)
        context.user_data['remaining_working_days'] = remaining_days
        
        # Show completion message for current day
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"✅ *{current_day} Times Set!*\n\n"
        text += f"{staff_name} will work on {current_day}:\n"
        text += f"*{start_time} - {end_time}*\n\n"
        
        if remaining_days:
            # Show remaining days and ask for next
            text += f"*Remaining Days:*\n"
            for i, day in enumerate(remaining_days, 1):
                text += f"{i}. {day}\n"
            text += f"\nPlease enter the time for {remaining_days[0]}:"
            
            keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_time_setting")]]
        else:
            # All days completed
            text += "All working days completed!"
            keyboard = [[InlineKeyboardButton("📅 View Complete Schedule", callback_data="view_complete_schedule")]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        
        return SCHEDULE_INPUT
    
    def validate_time_range_format(self, time_input):
        """
        Validate time range format HH:MM - HH:MM
        Returns: (is_valid, error_message)
        """
        if not time_input:
            return False, "Time range cannot be empty"
        
        # Check if it contains the dash separator
        if ' - ' not in time_input:
            return False, "Time range must be in format: HH:MM - HH:MM"
        
        # Split and check we have exactly two parts
        parts = time_input.split(' - ')
        if len(parts) != 2:
            return False, "Time range must have exactly one dash separator"
        
        start_time, end_time = parts
        
        # Check that both parts are not empty
        if not start_time.strip() or not end_time.strip():
            return False, "Both start and end times must be provided"
        
        return True, ""
    
    async def toggle_day_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle working status for the current editing day"""
        day = context.user_data.get('editing_day')
        schedule_data = context.user_data.get('schedule_data', {})
        
        if day not in schedule_data:
            schedule_data[day] = {'is_working': False, 'start_time': '', 'end_time': ''}
        
        # Toggle status
        schedule_data[day]['is_working'] = not schedule_data[day]['is_working']
        
        # Clear times if switching to Off
        if not schedule_data[day]['is_working']:
            schedule_data[day]['start_time'] = ''
            schedule_data[day]['end_time'] = ''
        
        context.user_data['schedule_data'] = schedule_data
        
        # CRITICAL FIX: Save the status change immediately to database
        await self.save_single_day_edit(update, context, day)
        
        return await self.show_day_edit_view(update, context)
    
    async def save_single_day_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE, day):
        """Save a single day edit immediately to database"""
        try:
            staff_id = context.user_data.get('current_staff_id')
            staff_name = context.user_data.get('current_staff_name', 'Unknown')
            schedule_data = context.user_data.get('schedule_data', {})
            
            if not staff_id:
                logger.error(f"save_single_day_edit: No staff_id in context for {day}")
                return False
            
            day_data = schedule_data.get(day, {})
            if not day_data:
                logger.error(f"save_single_day_edit: No day_data for {day}")
                return False
            
            is_working = day_data.get('is_working', True)
            start_time = day_data.get('start_time', '') if is_working else None
            end_time = day_data.get('end_time', '') if is_working else None
            
            # Don't save if working but missing times (treat empty strings as missing)
            if is_working and (not start_time or start_time.strip() == '' or not end_time or end_time.strip() == ''):
                logger.warning(f"save_single_day_edit: {day} is working but missing times - start:'{start_time}', end:'{end_time}'")
                return False
            
            # Get week dates for schedule_date - ensure they exist
            week_dates = context.user_data.get('week_dates', {})
            if not week_dates:
                # Initialize week dates if not set
                week_dates, week_start = self.calculate_week_dates()
                context.user_data['week_dates'] = week_dates
                context.user_data['week_start'] = week_start
                print(f"DEBUG: Initialized week_dates for single day save: {week_dates}")
            
            schedule_date = week_dates.get(day)
            
            user_id = update.effective_user.id
            
            logger.info(f"SINGLE DAY SAVE: {staff_name} {day} -> working:{is_working}, start:{start_time}, end:{end_time}, date:{schedule_date}")
            print(f"DEBUG: SINGLE DAY SAVE: {staff_name} {day} -> working:{is_working}, start:{start_time}, end:{end_time}")
            print(f"DEBUG: About to call db.save_schedule with staff_id={staff_id}")
            
            # Save to database
            try:
                success = self.db.save_schedule(
                    staff_id=staff_id,
                    day_of_week=day,
                    is_working=is_working,
                    start_time=start_time,
                    end_time=end_time,
                    schedule_date=schedule_date,
                    changed_by=f"SINGLE_EDIT_{user_id}"
                )
                
                if success:
                    logger.info(f"✅ Single day save successful: {staff_name} {day}")
                    print(f"DEBUG: ✅ Single day save successful: {staff_name} {day}")
                    
                    # VERIFICATION: Read back immediately to confirm it saved
                    print(f"DEBUG: Verifying save by reading fresh data...")
                    fresh_schedule = self.db.get_staff_schedule(staff_id)
                    for day_name, is_work, start_t, end_t in fresh_schedule:
                        if day_name == day:
                            print(f"DEBUG: VERIFICATION - {day} in DB: working={is_work}, start={start_t}, end={end_t}")
                            break
                else:
                    logger.error(f"❌ Single day save failed: {staff_name} {day}")
                    print(f"DEBUG: ❌ Single day save failed: {staff_name} {day}")
                
                return success
                
            except Exception as save_ex:
                logger.error(f"Exception during db.save_schedule: {save_ex}")
                print(f"DEBUG: Exception during db.save_schedule: {save_ex}")
                return False
            
        except Exception as e:
            logger.error(f"Exception in save_single_day_edit for {day}: {e}")
            print(f"DEBUG: Exception in save_single_day_edit for {day}: {e}")
            return False
    
    async def refresh_schedule_data(self, context, staff_id):
        """Refresh schedule data from database to ensure we have the latest data"""
        try:
            # Get fresh schedule data from database
            existing_schedule = self.db.get_staff_schedule(staff_id)
            
            # Convert to our format
            schedule_data = {}
            for day in DAYS_OF_WEEK:
                schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
            
            # Fill in existing schedule data
            for day, is_working, start_time, end_time in existing_schedule:
                formatted_start = self.format_time_for_display(start_time)
                formatted_end = self.format_time_for_display(end_time)
                
                schedule_data[day] = {
                    'is_working': bool(is_working),
                    'start_time': formatted_start or '',
                    'end_time': formatted_end or ''
                }
            
            # Update context with fresh data
            context.user_data['schedule_data'] = schedule_data
            print(f"DEBUG: Refreshed schedule data from database for staff_id {staff_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing schedule data: {e}")
            return False
    
    async def save_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save the complete schedule for the staff member"""
        staff_id = context.user_data.get('current_staff_id')
        schedule_data = context.user_data.get('schedule_data', {})
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        if not staff_id:
            logger.error("save_schedule called without staff_id in context")
            await update.callback_query.edit_message_text("❌ Error: Staff ID not found.")
            return await self.show_main_menu(update, context)
        
        logger.info(f"Starting save_schedule for {staff_name} (ID: {staff_id})")
        logger.debug(f"Schedule data: {schedule_data}")
        
        # Validate complete schedule
        is_valid, errors = ScheduleValidator.validate_schedule_data(schedule_data)
        if not is_valid:
            error_text = "\n".join(errors)
            logger.warning(f"Schedule validation failed for {staff_name}: {errors}")
            
            # Show detailed error message with option to continue editing
            text = f"❌ *Schedule validation errors for {staff_name}:*\n\n{error_text}\n\n"
            text += "Please complete all working day times before saving."
            
            keyboard = [
                [InlineKeyboardButton("✏️ Continue Editing", callback_data="edit_schedule")],
                [InlineKeyboardButton("🔙 Back to Summary", callback_data="back_to_summary")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return SCHEDULE_INPUT
        
        logger.info(f"Validation passed for {staff_name}, proceeding to save...")
        
        # Save to database with dates
        user_id = update.effective_user.id
        saved_count = 0
        failed_saves = []
        
        try:
            # Create scheduling session for tracking
            week_dates = context.user_data.get('week_dates', {})
            week_start = context.user_data.get('week_start')
            
            if week_start:
                session_id = self.db.create_scheduling_session(week_start, f"SINGLE_{user_id}")
                logger.info(f"Created scheduling session {session_id} for {staff_name}")
            
            for day_name, day_data in schedule_data.items():
                if day_name not in ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                    logger.warning(f"Skipping invalid day: {day_name}")
                    continue
                
                try:
                    schedule_date = day_data.get('date') or week_dates.get(day_name)
                    is_working = day_data.get('is_working', True)
                    start_time = day_data.get('start_time', '') if is_working else None
                    end_time = day_data.get('end_time', '') if is_working else None
                    
                    logger.debug(f"Saving {staff_name} {day_name}: working={is_working}, start={start_time}, end={end_time}, date={schedule_date}")
                    
                    success = self.db.save_schedule(
                        staff_id=staff_id,
                        day_of_week=day_name,
                        is_working=is_working,
                        start_time=start_time,
                        end_time=end_time,
                        schedule_date=schedule_date,
                        changed_by=f"USER_{user_id}"
                    )
                    
                    if success:
                        saved_count += 1
                        logger.info(f"Successfully saved {day_name} for {staff_name}")
                    else:
                        failed_saves.append(day_name)
                        logger.error(f"Failed to save {day_name} for {staff_name}")
                        
                except Exception as e:
                    logger.error(f"Exception saving {day_name} for {staff_name}: {e}")
                    failed_saves.append(day_name)
            
            # Complete the session if successful
            if week_start and saved_count > 0 and not failed_saves:
                self.db.complete_scheduling_session(session_id)
                logger.info(f"Completed scheduling session {session_id}")
            
        except Exception as e:
            logger.error(f"Critical error during save_schedule for {staff_name}: {e}")
            failed_saves = list(schedule_data.keys())  # Mark all as failed
        
        logger.info(f"Save complete for {staff_name} - {saved_count} successful, {len(failed_saves)} failed")
        
        # Show appropriate success/failure message
        if failed_saves:
            failed_text = ", ".join(failed_saves)
            text = f"⚠️ *Partial Save Failed*\n\n"
            text += f"❌ *Could not save:* {failed_text}\n"
            text += f"✅ *Successfully saved:* {saved_count} days\n\n"
            text += f"❗ *Database Error:* Some changes for {staff_name} could not be saved.\n"
            text += f"Please check the console logs for details and try again."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="save_schedule")],
                [InlineKeyboardButton("✏️ Edit Schedule", callback_data="edit_schedule")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return SCHEDULE_INPUT
        
        # All saves successful
        week_dates = context.user_data.get('week_dates', {})
        date_range = self.format_date_range(week_dates)
        
        # Clear any cached data to ensure fresh data is fetched
        context.user_data.clear()
        logger.info(f"Cleared context data after successful save for {staff_name}")
        
        # Check if all staff have schedules
        staff_without_schedules = self.db.get_staff_without_complete_schedules()
        
        if staff_without_schedules:
            # Get next staff member
            next_staff = staff_without_schedules[0]
            next_staff_id, next_staff_name, schedule_count = next_staff
            
            text = f"✅ *Schedule saved for {staff_name}*\n\n"
            text += f"*Week:* {date_range}\n"
            text += f"*Location:* Toronto, Canada\n\n"
            text += f"Successfully saved {saved_count} days.\n\n"
            text += f"Next staff member to schedule: *{next_staff_name}*"
            
            keyboard = [
                [InlineKeyboardButton("📅 Schedule Next Staff", callback_data="set_schedule")],
                [InlineKeyboardButton("👀 View Updated Schedules", callback_data="view_current_schedules")],
                [InlineKeyboardButton("📄 Generate PDF", callback_data="export_pdf")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
        else:
            # All staff scheduled
            text = f"🎉 *All Staff Scheduled!*\n\n"
            text += f"*Week:* {date_range}\n"
            text += f"*Location:* Toronto, Canada\n\n"
            text += f"Successfully saved {saved_count} days for {staff_name}.\n\n"
            text += f"All staff members have been scheduled for this week."
            
            keyboard = [
                [InlineKeyboardButton("👀 View Updated Schedules", callback_data="view_current_schedules")],
                [InlineKeyboardButton("📄 Generate PDF", callback_data="export_pdf")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    
    async def cancel_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel schedule input"""
        context.user_data.clear()
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "❌ Schedule input cancelled.",
            reply_markup=reply_markup
        )
        
        return MAIN_MENU
    
    def format_time_for_display(self, time_value):
        """Convert time value (timedelta, string, or None) to HH:MM format for display
        
        This function handles:
        - MySQL timedelta objects (e.g., datetime.timedelta(seconds=18000) for 05:00:00)
        - String time formats (e.g., "05:00", "05:00:00", "5:00")
        - None/empty values
        - Invalid formats
        """
        if not time_value:
            return None
        
        try:
            # Case 1: MySQL timedelta object
            if hasattr(time_value, 'total_seconds'):
                total_seconds = int(time_value.total_seconds())
                # Handle negative timedeltas (shouldn't happen but being safe)
                if total_seconds < 0:
                    return None
                
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                
                # Ensure valid time range (0-23 hours, 0-59 minutes)
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    return f"{hours:02d}:{minutes:02d}"
                else:
                    print(f"DEBUG: Invalid time from timedelta: {hours}:{minutes}")
                    return None
            
            # Case 2: String formats
            elif isinstance(time_value, str):
                time_str = time_value.strip()
                if not time_str:
                    return None
                
                # Handle various string formats
                if ':' in time_str:
                    parts = time_str.split(':')
                    
                    # Handle HH:MM:SS format (convert to HH:MM)
                    if len(parts) == 3:
                        try:
                            hours = int(parts[0])
                            minutes = int(parts[1])
                            # Ignore seconds part
                            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                                return f"{hours:02d}:{minutes:02d}"
                        except ValueError:
                            pass
                    
                    # Handle HH:MM format
                    elif len(parts) == 2:
                        try:
                            hours = int(parts[0])
                            minutes = int(parts[1])
                            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                                return f"{hours:02d}:{minutes:02d}"
                        except ValueError:
                            pass
                
                # Handle single number (assume hours)
                else:
                    try:
                        hours = int(time_str)
                        if 0 <= hours <= 23:
                            return f"{hours:02d}:00"
                    except ValueError:
                        pass
                
                print(f"DEBUG: Could not parse time string: '{time_str}'")
                return None
            
            # Case 3: Other types (datetime.time, etc.)
            elif hasattr(time_value, 'hour') and hasattr(time_value, 'minute'):
                # datetime.time object
                return f"{time_value.hour:02d}:{time_value.minute:02d}"
            
            else:
                # Try to convert to string and parse
                str_value = str(time_value).strip()
                if str_value and str_value != 'None':
                    return self.format_time_for_display(str_value)
                
                return None
        
        except Exception as e:
            print(f"DEBUG: Error formatting time value '{time_value}' (type: {type(time_value)}): {e}")
            return None
    
    async def view_schedules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all current schedules"""
        try:
            # Clear any cached data to ensure fresh data is fetched
            context.user_data.clear()
            logger.info("Fetching current schedules - cleared context for fresh data")
            
            # Get all schedules from database
            schedules = self.db.get_all_schedules()
            logger.info(f"Retrieved {len(schedules)} schedule records from database")
            
            if not schedules:
                text = "📋 *Current Schedules Overview*\n\n"
                text += "No schedules found. Create schedules for your staff first."
                
                keyboard = [
                    [InlineKeyboardButton("📅 Create Schedule", callback_data="set_schedule")],
                    [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                query = update.callback_query
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                return MAIN_MENU
            
            # Process schedules
            staff_schedules = {}
            
            for staff_name, day, schedule_date, is_working, start_time, end_time in schedules:
                if staff_name not in staff_schedules:
                    staff_schedules[staff_name] = {}
                
                # Convert times to proper format
                formatted_start = self.format_time_for_display(start_time)
                formatted_end = self.format_time_for_display(end_time)
                
                logger.debug(f"Processing {staff_name} {day}: working={is_working}, start={start_time}->{formatted_start}, end={end_time}->{formatted_end}")
                
                if is_working and formatted_start and formatted_end:
                    staff_schedules[staff_name][day] = f"✅ {formatted_start}-{formatted_end}"
                elif not is_working:
                    staff_schedules[staff_name][day] = "🔴 OFF"
                else:
                    staff_schedules[staff_name][day] = "⏰ Not Set"
            
            logger.info(f"Processed schedules for {len(staff_schedules)} staff members")
            
            # Create schedule text
            text = "📋 *Current Schedules Overview*\n\n"
            text += f"*Last updated: {datetime.now().strftime('%H:%M:%S')}*\n\n"
            
            # Get all staff for comparison
            all_staff = self.db.get_all_staff()
            staff_names = [name for _, name in all_staff]
            
            for staff_name in staff_names:
                schedule = staff_schedules.get(staff_name, {})
                text += f"*{staff_name}:*\n"
                
                # Count working days and off days
                working_days = 0
                off_days = 0
                incomplete_days = 0
                
                for day in DAYS_OF_WEEK:
                    day_status = schedule.get(day, "⏰ Not Set")
                    text += f"  {day}: {day_status}\n"
                    
                    if "✅" in day_status:
                        working_days += 1
                    elif "🔴" in day_status:
                        off_days += 1
                    else:
                        incomplete_days += 1
                
                # Add summary
                text += f"  📊 *Summary:* {working_days} working, {off_days} off, {incomplete_days} incomplete\n\n"
            
            # Add action buttons
            keyboard = []
            
            # Quick edit buttons for each staff
            for staff_name in staff_names:
                keyboard.append([InlineKeyboardButton(f"✏️ Edit {staff_name}", callback_data=f"quick_edit_{staff_name}")])
            
            # Other options
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data="view_current_schedules"),
                InlineKeyboardButton("📄 Export PDF", callback_data="export_pdf")
            ])
            keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"Error in view_schedules: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            error_text = "❌ *Error Loading Schedules*\n\n"
            error_text += "There was a problem loading the current schedules. "
            error_text += "Please try again or contact the administrator if the problem persists."
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data="view_current_schedules")],
                [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query:
                await update.callback_query.edit_message_text(error_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(error_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
            return MAIN_MENU
    
    def prepare_schedules_for_pdf(self, raw_schedules):
        """Convert raw database schedules to PDF-ready format with proper time strings"""
        converted_schedules = []
        
        for record in raw_schedules:
            if len(record) >= 6:
                staff_name, day, schedule_date, is_working, start_time, end_time = record[:6]
                
                # Convert times to string format
                formatted_start = self.format_time_for_display(start_time) or ""
                formatted_end = self.format_time_for_display(end_time) or ""
                
                print(f"DEBUG: Converting {staff_name} {day}: {start_time} -> {formatted_start}, {end_time} -> {formatted_end}")
                
                converted_schedules.append((
                    staff_name, 
                    day, 
                    schedule_date, 
                    is_working, 
                    formatted_start, 
                    formatted_end
                ))
            else:
                print(f"DEBUG: Skipping malformed record: {record}")
        
        print(f"DEBUG: Converted {len(converted_schedules)} schedule records for PDF")
        return converted_schedules
    
    async def export_pdf_for_week(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export PDF for a specific selected week"""
        try:
            # Get the selected week information from context
            week_dates = context.user_data.get('pdf_week_dates', {})
            week_start = context.user_data.get('pdf_week_start')
            date_range = context.user_data.get('pdf_date_range', 'Selected Week')
            
            if not week_dates or not week_start:
                await update.callback_query.edit_message_text(
                    "❌ Error: No week selected for PDF export.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]])
                )
                return MAIN_MENU
            
            # Get schedules for the selected week
            week_end = week_start + timedelta(days=6)
            schedules = self.db.get_all_schedules()
            
            # Filter schedules for the selected week
            week_schedules = []
            for schedule in schedules:
                if len(schedule) >= 3 and schedule[2]:  # schedule_date exists
                    try:
                        schedule_date = datetime.strptime(schedule[2], '%Y-%m-%d').date()
                        if week_start <= schedule_date <= week_end:
                            week_schedules.append(schedule)
                    except (ValueError, TypeError):
                        continue
            
            if not week_schedules:
                await update.callback_query.edit_message_text(
                    f"❌ No schedules found for {date_range}.\n\nCreate schedules first to export PDF.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]])
                )
                return MAIN_MENU
            
            # Send a "generating" message first to prevent timeout
            query = update.callback_query
            await query.edit_message_text(
                f"⏳ Generating PDF for {date_range}... Please wait.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Convert schedules to PDF-ready format
            pdf_ready_schedules = self.prepare_schedules_for_pdf(week_schedules)
            
            # Generate PDF with selected week dates
            pdf_filename = self.pdf_gen.generate_schedule_pdf(pdf_ready_schedules, week_dates, date_range)
            
            # Send PDF
            with open(pdf_filename, 'rb') as pdf_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=pdf_file,
                    filename=pdf_filename,
                    caption=f"📄 Weekly Staff Schedule - {date_range}"
                )
            
            # Show success message
            await query.edit_message_text(
                f"✅ PDF exported successfully!\n\n📄 *{date_range}*\n\nPDF has been sent to this chat.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]),
                parse_mode=ParseMode.MARKDOWN
            )
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"Error exporting PDF for week: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Error generating PDF: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]])
            )
            return MAIN_MENU

    async def export_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate and send PDF schedule"""
        # Add debugging for admin access
        user_id = update.effective_user.id
        print(f"DEBUG: export_pdf called by user_id: {user_id}")
        print(f"DEBUG: ADMIN_IDS: {ADMIN_IDS}")
        print(f"DEBUG: Is admin? {self.is_admin(user_id)}")
        
        # Clear any user_data that might interfere with PDF generation
        # This prevents conflicts when multiple admins use the bot simultaneously
        context.user_data.clear()
        
        schedules = self.db.get_all_schedules()
        print(f"DEBUG: Found {len(schedules)} schedules in database")
        
        if not schedules:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                "❌ No schedules found. Please set schedules first.",
                reply_markup=reply_markup
            )
            return MAIN_MENU
        
        # Check if all staff have complete schedules - for information only, don't filter
        staff_without_schedules = self.db.get_staff_without_complete_schedules()
        warning_message = ""
        
        if staff_without_schedules:
            missing_staff = [name for _, name, _ in staff_without_schedules]
            warning_message = f"\n\n📋 *INFO: Partial schedules included for:*\n"
            warning_message += f"{chr(10).join([f'• {name}' for name in missing_staff])}\n"
            warning_message += f"\nPDF will show all available schedules (including incomplete ones)."
        
        # Generate PDF with ALL schedules (no filtering)
        try:
            print(f"DEBUG: Starting PDF generation with {len(schedules)} schedule records")
            
            # Send a "generating" message first to prevent timeout
            query = update.callback_query
            await query.edit_message_text(
                f"⏳ Generating PDF... Please wait.{warning_message}",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Calculate week dates for current week
            now = datetime.now(self.toronto_tz)
            days_since_sunday = now.weekday() + 1
            if days_since_sunday == 7:
                days_since_sunday = 0
            week_start = now.date() - timedelta(days=days_since_sunday)
            
            week_dates = {}
            for i, day in enumerate(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']):
                week_dates[day] = week_start + timedelta(days=i)
            
            # Calculate date range for display
            date_range = self.format_date_range(week_dates)
            print(f"DEBUG: Date range: {date_range}")
            
            # Convert schedules to PDF-ready format (use ALL schedules, no filtering)
            pdf_ready_schedules = self.prepare_schedules_for_pdf(schedules)
            
            print(f"DEBUG: Calling PDF generator with {len(pdf_ready_schedules)} converted records...")
            pdf_filename = self.pdf_gen.generate_schedule_pdf(pdf_ready_schedules, week_dates, date_range)
            print(f"DEBUG: PDF generated successfully: {pdf_filename}")
            
            # Send PDF
            with open(pdf_filename, 'rb') as pdf_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=pdf_file,
                    filename=pdf_filename,
                    caption="📄 Weekly Staff Schedule"
                )
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            success_message = "✅ PDF generated and sent successfully!"
            if warning_message:
                success_message += warning_message
            
            await query.edit_message_text(
                success_message,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                f"❌ Error generating PDF: {str(e)}\n\nPlease check the console for more details.",
                reply_markup=reply_markup
            )
        
        return MAIN_MENU
    
    async def start_over(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the scheduling process over for the current staff member"""
        staff_id = context.user_data.get('current_staff_id')
        if not staff_id:
            await update.callback_query.edit_message_text("❌ Error: Staff ID not found.")
            return await self.show_main_menu(update, context)
        
        # Reset schedule data for the current staff member
        self.db.reset_staff_schedule(staff_id)
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            "✅ Scheduling process started over for this staff member.",
            reply_markup=reply_markup
        )
        
        return await self.show_schedule_input_form(update, context)
    
    def run(self):
        """Run the bot (synchronous version)"""
        import asyncio
        asyncio.run(self.run_async())
    
    async def run_async(self):
        """Run the bot (asynchronous version with webhook support)"""
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Create conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(self.handle_main_menu)
                ],
                STAFF_MANAGEMENT: [
                    CallbackQueryHandler(self.handle_staff_management)
                ],
                ADD_STAFF: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_staff_handler)
                ],
                BULK_ADD_COUNT: [
                    CallbackQueryHandler(self.handle_bulk_add_count)
                ],
                BULK_ADD_NAMES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_bulk_add_names)
                ],
                REMOVE_STAFF: [
                    CallbackQueryHandler(self.handle_remove_staff)
                ],
                SCHEDULE_MENU: [
                    CallbackQueryHandler(self.handle_schedule_menu)
                ],
                SCHEDULE_INPUT: [
                    CallbackQueryHandler(self.handle_schedule_input),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_time_input)
                ],
                VIEW_SCHEDULES: [
                    CallbackQueryHandler(self.view_schedules)
                ],
                BULK_SCHEDULE: [
                    CallbackQueryHandler(self.handle_bulk_schedule)
                ],
                WEEKLY_STATS: [
                    CallbackQueryHandler(self.handle_weekly_stats)
                ],
                SCHEDULE_TEMPLATES: [
                    CallbackQueryHandler(self.handle_schedule_templates)
                ],
                SCHEDULE_HISTORY: [
                    CallbackQueryHandler(self.handle_schedule_history)
                ],
                WEEK_SELECTION: [
                    CallbackQueryHandler(self.handle_week_selection)
                ]
            },
            fallbacks=[CommandHandler("start", self.start)],
            per_message=False
        )
        
        application.add_handler(conv_handler)
        
        try:
            # Initialize the application
            await application.initialize()
            await application.start()
            
            # Check if we're running on Railway or other cloud platform
            webhook_url = os.getenv('WEBHOOK_URL')
            
            if webhook_url:
                # Production mode with webhooks
                logger.info(f"🌐 Production mode - Webhook URL: {webhook_url}")
                
                try:
                    # Set webhook
                    await application.bot.set_webhook(url=webhook_url)
                    logger.info("✅ Webhook set successfully")
                    
                    # Start webhook server
                    await application.updater.start_webhook(
                        listen="0.0.0.0",
                        port=int(os.getenv('PORT', 8000)),
                        webhook_url=webhook_url,
                        drop_pending_updates=True
                    )
                    logger.info("🌐 Webhook server started")
                    
                    # Keep running until interrupted
                    await self._keep_running()
                        
                except Exception as webhook_error:
                    logger.error(f"❌ Webhook setup failed: {webhook_error}")
                    logger.info("🔄 Falling back to polling mode")
                    
                    # Clear webhook and use polling instead
                    try:
                        await application.bot.delete_webhook()
                    except:
                        pass
                    
                    # Use polling as fallback
                    await application.updater.start_polling(
                        drop_pending_updates=True,
                        allowed_updates=['message', 'callback_query']
                    )
                    logger.info("🔧 Polling started as fallback")
                    
                    # Keep running until interrupted
                    await self._keep_running()
            else:
                # Development mode with polling
                logger.info("🔧 Development mode - Using polling")
                
                # Start polling
                await application.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=['message', 'callback_query']
                )
                logger.info("✅ Polling started successfully")
                
                # Keep running until interrupted
                await self._keep_running()
                
        except Exception as e:
            logger.error(f"❌ Error running bot: {e}")
            raise
        finally:
            # Ensure proper cleanup
            try:
                logger.info("🔄 Stopping bot...")
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                logger.info("✅ Bot shutdown completed")
            except Exception as shutdown_error:
                logger.error(f"⚠️ Error during shutdown: {shutdown_error}")
                # Don't re-raise shutdown errors
    
    async def _keep_running(self):
        """Keep the bot running until interrupted"""
        try:
            # Run indefinitely
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Bot task cancelled")
            raise
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            raise
    
    async def edit_next_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Move to edit the next day in the schedule"""
        schedule_data = context.user_data.get('schedule_data', {})
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        # Find the next day that needs editing (has times but might want to change)
        current_day_index = -1
        for i, day in enumerate(DAYS_OF_WEEK):
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['is_working'] and day_data['start_time'] and day_data['end_time']:
                current_day_index = i
                break
        
        # Find next day to edit
        next_day = None
        for i in range(current_day_index + 1, len(DAYS_OF_WEEK)):
            day = DAYS_OF_WEEK[i]
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['is_working']:
                next_day = day
                break
        
        if next_day:
            # Show edit interface for next day
            return await self.edit_specific_day(update, context, next_day)
        else:
            # No more days to edit, show final summary
            return await self.show_final_schedule_summary(update, context)
    
    async def show_start_time_picker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show time picker for start time"""
        day = context.user_data.get('editing_day')
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        # Handle case where editing_day is not set
        if not day:
            await update.callback_query.answer("❌ No day selected for editing")
            return await self.show_edit_options(update, context)
        
        text = f"🕐 *Select Start Time for {day}*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"Day: {day}\n\n"
        text += f"*Choose a start time:*"
        
        # Create simpler time picker keyboard
        keyboard = []
        start_times = ["09:45", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "17:00"]
        
        # Create rows of 5 time slots each
        for i in range(0, len(start_times), 5):
            row = []
            for j in range(5):
                if i + j < len(start_times):
                    time_slot = start_times[i + j]
                    row.append(InlineKeyboardButton(time_slot, callback_data=f"edit_start_{day}_{time_slot}"))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Day Edit", callback_data="back_to_day_edit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def show_end_time_picker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show time picker for end time"""
        day = context.user_data.get('editing_day')
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        # Handle case where editing_day is not set
        if not day:
            await update.callback_query.answer("❌ No day selected for editing")
            return await self.show_edit_options(update, context)
        
        text = f"🕐 *Select End Time for {day}*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"Day: {day}\n\n"
        text += f"*Choose an end time:*"
        
        # Create simpler time picker keyboard
        keyboard = []
        end_times = ["17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
        
        # Create rows of 5 time slots each
        for i in range(0, len(end_times), 5):
            row = []
            for j in range(5):
                if i + j < len(end_times):
                    time_slot = end_times[i + j]
                    row.append(InlineKeyboardButton(time_slot, callback_data=f"edit_end_{day}_{time_slot}"))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Day Edit", callback_data="back_to_day_edit")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def back_to_day_edit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Go back to day edit view"""
        # Check if editing_day is set
        editing_day = context.user_data.get('editing_day')
        if not editing_day:
            await update.callback_query.answer("❌ No day selected for editing")
            return await self.show_edit_options(update, context)
        
        return await self.show_day_edit_view(update, context)
    
    async def edit_selected_days(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit multiple selected days individually"""
        selected_days = context.user_data.get('selected_days_for_edit', [])
        
        if not selected_days:
            await update.callback_query.answer("❌ No days selected. Please select days first.")
            return await self.edit_time_slots(update, context)
        
        # Set the selected days as remaining days for individual editing
        context.user_data['remaining_working_days'] = selected_days.copy()
        
        # Start editing the first selected day
        return await self.start_editing_selected_days(update, context)
    
    async def start_editing_selected_days(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing selected days one by one"""
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if not remaining_days:
            # All days edited, show final summary
            return await self.show_final_schedule_summary(update, context)
        
        current_day = remaining_days[0]
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        schedule_data = context.user_data.get('schedule_data', {})
        day_data = schedule_data.get(current_day, {'is_working': True, 'start_time': '', 'end_time': ''})
        
        text = f"✏️ *Editing {current_day} for {staff_name}*\n\n"
        text += f"*Current times:* {day_data['start_time']} - {day_data['end_time']}\n\n"
        text += f"*Remaining days to edit:* {len(remaining_days)}\n"
        text += f"Progress: {len(context.user_data.get('selected_days_for_edit', [])) - len(remaining_days) + 1}/{len(context.user_data.get('selected_days_for_edit', []))}\n\n"
        text += f"*Please select the start and end times:*"
        
        # Create time picker keyboard with exact same format as original
        keyboard = []
        
        # Start time options (exactly like original: 9:45 AM to 5 PM)
        start_times = ["09:45", "10:00", "11:00", "12:00", "13:00", "15:00", "17:00"]
        end_times = ["14:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
        
        # Start time row
        start_row = []
        for time in start_times:
            if time == day_data['start_time']:
                start_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"edit_start_{current_day}_{time}"))
            else:
                start_row.append(InlineKeyboardButton(f"🟢 {time}", callback_data=f"edit_start_{current_day}_{time}"))
        keyboard.append(start_row)
        
        # End time row
        end_row = []
        for time in end_times:
            if time == day_data['end_time']:
                end_row.append(InlineKeyboardButton(f"✅ {time}", callback_data=f"edit_end_{current_day}_{time}"))
            else:
                end_row.append(InlineKeyboardButton(f"🔴 {time}", callback_data=f"edit_end_{current_day}_{time}"))
        keyboard.append(end_row)
        
        # Add action buttons
        keyboard.append([
            InlineKeyboardButton("⏭️ Skip This Day", callback_data="skip_current_day"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_editing_selected")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def set_start_time_all_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set start time for all selected days"""
        selected_days = context.user_data.get('selected_days_for_edit', [])
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"🕐 *Set Start Time for All Selected Days*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"Days: {', '.join(selected_days)}\n\n"
        text += f"*Choose a start time that will apply to all selected days:*"
        
        # Create time picker keyboard
        keyboard = []
        time_slots = [
            "09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15", "11:30", "11:45",
            "12:00", "12:15", "12:30", "12:45", "13:00", "13:15", "13:30", "13:45", "14:00",
            "14:15", "14:30", "14:45", "15:00", "15:15", "15:30", "15:45", "16:00", "16:15",
            "16:30", "16:45", "17:00", "17:15", "17:30", "17:45", "18:00", "18:15", "18:30",
            "18:45", "19:00", "19:15", "19:30", "19:45", "20:00", "20:15", "20:30", "20:45", "21:00"
        ]
        
        # Create rows of 4 time slots each
        for i in range(0, len(time_slots), 4):
            row = []
            for j in range(4):
                if i + j < len(time_slots):
                    time_slot = time_slots[i + j]
                    row.append(InlineKeyboardButton(time_slot, callback_data=f"set_start_all_{time_slot}"))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Edit Options", callback_data="back_to_edit_selected")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def set_end_time_all_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set end time for all selected days"""
        selected_days = context.user_data.get('selected_days_for_edit', [])
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"🕐 *Set End Time for All Selected Days*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"Days: {', '.join(selected_days)}\n\n"
        text += f"*Choose an end time that will apply to all selected days:*"
        
        # Create time picker keyboard
        keyboard = []
        time_slots = [
            "09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15", "11:30", "11:45",
            "12:00", "12:15", "12:30", "12:45", "13:00", "13:15", "13:30", "13:45", "14:00",
            "14:15", "14:30", "14:45", "15:00", "15:15", "15:30", "15:45", "16:00", "16:15",
            "16:30", "16:45", "17:00", "17:15", "17:30", "17:45", "18:00", "18:15", "18:30",
            "18:45", "19:00", "19:15", "19:30", "19:45", "20:00", "20:15", "20:30", "20:45", "21:00"
        ]
        
        # Create rows of 4 time slots each
        for i in range(0, len(time_slots), 4):
            row = []
            for j in range(4):
                if i + j < len(time_slots):
                    time_slot = time_slots[i + j]
                    row.append(InlineKeyboardButton(time_slot, callback_data=f"set_end_all_{time_slot}"))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Edit Options", callback_data="back_to_edit_selected")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def set_both_times_all_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set both start and end times for all selected days"""
        selected_days = context.user_data.get('selected_days_for_edit', [])
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        text = f"⏰ *Set Both Times for All Selected Days*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"Days: {', '.join(selected_days)}\n\n"
        text += f"*Choose a time range that will apply to all selected days:*"
        
        # Create time range picker keyboard
        keyboard = []
        time_ranges = [
            "09:45 - 18:00", "10:00 - 18:00", "10:00 - 19:00", "10:00 - 20:00",
            "11:00 - 19:00", "11:00 - 20:00", "12:00 - 20:00", "12:00 - 21:00",
            "13:00 - 21:00", "14:00 - 21:00"
        ]
        
        # Create rows of 2 time ranges each
        for i in range(0, len(time_ranges), 2):
            row = []
            for j in range(2):
                if i + j < len(time_ranges):
                    time_range = time_ranges[i + j]
                    row.append(InlineKeyboardButton(time_range, callback_data=f"set_both_all_{time_range}"))
            keyboard.append(row)
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Edit Options", callback_data="back_to_edit_selected")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def handle_set_start_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle setting start time for all selected days"""
        selected_time = update.callback_query.data.split("_")[3]  # set_start_all_10:00 -> 10:00
        selected_days = context.user_data.get('selected_days_for_edit', [])
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        schedule_data = context.user_data.get('schedule_data', {})
        
        # Apply start time to all selected days
        for day in selected_days:
            if day not in schedule_data:
                schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
            schedule_data[day]['start_time'] = selected_time
        
        context.user_data['schedule_data'] = schedule_data
        
        # Show confirmation
        text = f"✅ *Start Time Updated for All Selected Days!*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"Start Time: {selected_time}\n"
        text += f"Days: {', '.join(selected_days)}\n\n"
        
        # Show updated schedule for selected days
        text += f"*Updated Schedule:*\n"
        for day in selected_days:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['start_time'] and day_data['end_time']:
                text += f"✅ {day}: {day_data['start_time']} - {day_data['end_time']}\n"
            elif day_data['start_time']:
                text += f"⏰ {day}: {day_data['start_time']} - (end time needed)\n"
            else:
                text += f"❌ {day}: Not set\n"
        
        keyboard = [
            [InlineKeyboardButton("🕐 Set End Time for All", callback_data="set_end_all_selected")],
            [InlineKeyboardButton("✏️ Edit More Days", callback_data="back_to_day_selection")],
            [InlineKeyboardButton("✅ All Done", callback_data="finish_editing")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def handle_set_end_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle setting end time for all selected days"""
        selected_time = update.callback_query.data.split("_")[3]  # set_end_all_19:00 -> 19:00
        selected_days = context.user_data.get('selected_days_for_edit', [])
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        schedule_data = context.user_data.get('schedule_data', {})
        
        # Apply end time to all selected days
        for day in selected_days:
            if day not in schedule_data:
                schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
            
            # Validate time range if start time exists
            start_time = schedule_data[day].get('start_time', '')
            if start_time:
                time_valid, time_error = ScheduleValidator.validate_time_range(start_time, selected_time)
                if not time_valid:
                    await update.callback_query.answer(f"❌ {time_error} for {day}")
                    continue
            
            schedule_data[day]['end_time'] = selected_time
        
        context.user_data['schedule_data'] = schedule_data
        
        # Show confirmation
        text = f"✅ *End Time Updated for All Selected Days!*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"End Time: {selected_time}\n"
        text += f"Days: {', '.join(selected_days)}\n\n"
        
        # Show updated schedule for selected days
        text += f"*Updated Schedule:*\n"
        for day in selected_days:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['start_time'] and day_data['end_time']:
                text += f"✅ {day}: {day_data['start_time']} - {day_data['end_time']}\n"
            elif day_data['end_time']:
                text += f"⏰ {day}: (start time needed) - {day_data['end_time']}\n"
            else:
                text += f"❌ {day}: Not set\n"
        
        keyboard = [
            [InlineKeyboardButton("🕐 Set Start Time for All", callback_data="set_start_all_selected")],
            [InlineKeyboardButton("✏️ Edit More Days", callback_data="back_to_day_selection")],
            [InlineKeyboardButton("✅ All Done", callback_data="finish_editing")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def handle_set_both_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle setting both start and end times for all selected days"""
        time_range = update.callback_query.data.split("_", 3)[3]  # set_both_all_10:00 - 19:00 -> 10:00 - 19:00
        start_time, end_time = time_range.split(" - ")
        selected_days = context.user_data.get('selected_days_for_edit', [])
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        schedule_data = context.user_data.get('schedule_data', {})
        
        # Apply both times to all selected days
        for day in selected_days:
            if day not in schedule_data:
                schedule_data[day] = {'is_working': True, 'start_time': '', 'end_time': ''}
            
            # Validate time range
            time_valid, time_error = ScheduleValidator.validate_time_range(start_time, end_time)
            if not time_valid:
                await update.callback_query.answer(f"❌ {time_error} for {day}")
                continue
            
            schedule_data[day]['start_time'] = start_time
            schedule_data[day]['end_time'] = end_time
        
        context.user_data['schedule_data'] = schedule_data
        
        # Show confirmation
        text = f"✅ *Both Times Updated for All Selected Days!*\n\n"
        text += f"Staff: {staff_name}\n"
        text += f"Time Range: {start_time} - {end_time}\n"
        text += f"Days: {', '.join(selected_days)}\n\n"
        
        # Show updated schedule for selected days
        text += f"*Updated Schedule:*\n"
        for day in selected_days:
            day_data = schedule_data.get(day, {'is_working': True, 'start_time': '', 'end_time': ''})
            if day_data['start_time'] and day_data['end_time']:
                text += f"✅ {day}: {day_data['start_time']} - {day_data['end_time']}\n"
            else:
                text += f"❌ {day}: Not set\n"
        
        keyboard = [
            [InlineKeyboardButton("✏️ Edit More Days", callback_data="back_to_day_selection")],
            [InlineKeyboardButton("✅ All Done", callback_data="finish_editing")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return SCHEDULE_INPUT
    
    async def skip_current_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Skip the current day and move to the next"""
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if remaining_days:
            # Remove current day and continue with next
            remaining_days.pop(0)
            context.user_data['remaining_working_days'] = remaining_days
            
            if remaining_days:
                # Continue with next day
                return await self.start_editing_selected_days(update, context)
            else:
                # All days completed
                return await self.show_final_schedule_summary(update, context)
        else:
            return await self.show_final_schedule_summary(update, context)
    
    async def cancel_editing_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the editing process and go back to day selection"""
        # Clear the remaining days and selected days
        context.user_data['remaining_working_days'] = []
        context.user_data['selected_days_for_edit'] = []
        
        return await self.edit_time_slots(update, context)
    
    async def continue_to_next_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Continue to the next day in the editing sequence"""
        remaining_days = context.user_data.get('remaining_working_days', [])
        
        if remaining_days:
            # Remove the current day (which was just edited)
            remaining_days.pop(0)
            context.user_data['remaining_working_days'] = remaining_days
            
            if remaining_days:
                # Continue with next day
                return await self.start_editing_selected_days(update, context)
            else:
                # All days completed
                return await self.show_final_schedule_summary(update, context)
        else:
            return await self.show_final_schedule_summary(update, context)
    
    def calculate_week_dates(self, start_date=None):
        """Calculate the week dates starting from the given date (or today)"""
        if start_date is None:
            # Use Toronto timezone
            toronto_tz = pytz.timezone('America/Toronto')
            start_date = datetime.now(toronto_tz).date()
        
        # Calculate the current week's Sunday (0=Monday, 6=Sunday in Python weekday())
        # For Sunday scheduling, we want to find THIS week's Sunday, not next week's
        days_since_sunday = (start_date.weekday() + 1) % 7  # Convert to Sunday=0 system
        week_start = start_date - timedelta(days=days_since_sunday)
        
        # If today IS Sunday and we're scheduling, use today as the start of the current week
        if start_date.weekday() == 6:  # Sunday
            week_start = start_date
        
        # Calculate all week dates
        week_dates = {}
        for i, day in enumerate(DAYS_OF_WEEK):
            date = week_start + timedelta(days=i)
            week_dates[day] = date
        
        return week_dates, week_start
    
    def format_date_range(self, week_dates):
        """Format the date range for display"""
        if not week_dates or not isinstance(week_dates, dict):
            return "Current Week"
        
        # Check if we have the required days
        if DAYS_OF_WEEK[0] not in week_dates or DAYS_OF_WEEK[-1] not in week_dates:
            return "Current Week"
        
        start_date = week_dates[DAYS_OF_WEEK[0]]
        end_date = week_dates[DAYS_OF_WEEK[-1]]
        
        if not start_date or not end_date:
            return "Current Week"
        
        # Convert string dates to datetime objects if needed
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return "Current Week"
        
        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return "Current Week"
        
        start_str = start_date.strftime("%B %d")
        end_str = end_date.strftime("%B %d")
        
        if start_date.year != end_date.year:
            start_str += f", {start_date.year}"
            end_str += f", {end_date.year}"
        elif start_date.month != end_date.month:
            start_str += f", {start_date.year}"
            end_str += f", {start_date.year}"
        else:
            end_str += f", {start_date.year}"
        
        return f"{start_str} - {end_str}"
    
    async def reset_all_schedules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset all schedules to start fresh"""
        # Clear all schedules from database
        self.db.reset_all_schedules()
        
        text = "🗑️ *All Schedules Reset*\n\n"
        text += "✅ All existing schedules have been cleared.\n"
        text += "✅ Database has been updated with new date functionality.\n\n"
        text += "You can now start fresh with the new date-enabled scheduling system."
        
        keyboard = [
            [InlineKeyboardButton("📅 Start New Schedule", callback_data="set_schedule")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    
    async def show_schedule_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show schedule history with available weeks"""
        week_schedules = self.db.get_schedule_history()
        
        if not week_schedules:
            keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                "📚 *Schedule History*\n\nNo historical schedules found.\n\nOnly schedules with dates are stored in history.",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return MAIN_MENU
        
        text = "📚 *Schedule History*\n\n*Available Weeks:*\n\n"
        
        keyboard = []
        
        # Sort weeks by date (newest first)
        sorted_weeks = sorted(week_schedules.items(), key=lambda x: x[1]['week_start'], reverse=True)
        
        for week_key, week_info in sorted_weeks:
            week_start = week_info['week_start']
            week_end = week_start + timedelta(days=6)
            
            # Format date range
            start_str = week_start.strftime("%B %d")
            end_str = week_end.strftime("%B %d")
            if week_start.year != week_end.year:
                start_str += f", {week_start.year}"
                end_str += f", {week_end.year}"
            else:
                end_str += f", {week_start.year}"
            
            date_range = f"{start_str} - {end_str}"
            
            # Count staff with schedules
            staff_count = len(set(schedule[0] for schedule in week_info['schedules']))
            
            text += f"📅 *{date_range}*\n"
            text += f"   👥 {staff_count} staff members\n\n"
            
            # Add button for this week
            keyboard.append([InlineKeyboardButton(f"📅 {date_range}", callback_data=f"view_week_{week_key}")])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    
    async def view_week_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE, week_key):
        """View and export a specific week's schedule"""
        week_schedules = self.db.get_schedule_history()
        
        if week_key not in week_schedules:
            keyboard = [[InlineKeyboardButton("🔙 Back to History", callback_data="schedule_history")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                "❌ Week not found in history.",
                reply_markup=reply_markup
            )
            return MAIN_MENU
        
        week_info = week_schedules[week_key]
        week_start = week_info['week_start']
        week_end = week_start + timedelta(days=6)
        schedules = week_info['schedules']
        
        # Format date range
        start_str = week_start.strftime("%B %d")
        end_str = week_end.strftime("%B %d")
        if week_start.year != week_end.year:
            start_str += f", {week_start.year}"
            end_str += f", {week_end.year}"
        else:
            end_str += f", {week_start.year}"
        
        date_range = f"{start_str} - {end_str}"
        
        # Create week dates dictionary for PDF
        week_dates = {}
        for i, day in enumerate(DAYS_OF_WEEK):
            week_dates[day] = week_start + timedelta(days=i)
        
        # Store in context for PDF generation
        context.user_data['historical_week_dates'] = week_dates
        context.user_data['historical_date_range'] = date_range
        context.user_data['historical_schedules'] = schedules
        
        # Format schedule data for display
        staff_schedules = {}
        for staff_name, day, schedule_date, is_working, start_time, end_time in schedules:
            if staff_name not in staff_schedules:
                staff_schedules[staff_name] = {}
            
            # Convert times to proper format for display
            formatted_start = self.format_time_for_display(start_time)
            formatted_end = self.format_time_for_display(end_time)
            
            if is_working and formatted_start and formatted_end:
                staff_schedules[staff_name][day] = f"✅ {formatted_start}-{formatted_end}"
            elif not is_working:
                staff_schedules[staff_name][day] = "🔴 OFF"
            else:
                staff_schedules[staff_name][day] = "⏰ Not Set"
        
        # Create display text
        text = f"📅 *Week Schedule: {date_range}*\n\n"
        
        for staff_name, schedule in staff_schedules.items():
            text += f"*{staff_name}:*\n"
            for day in DAYS_OF_WEEK:
                day_status = schedule.get(day, "⏰ Not Set")
                date = week_dates[day]
                date_str = date.strftime("%b %d")
                text += f"  {day} ({date_str}): {day_status}\n"
            text += "\n"
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("📄 Export PDF", callback_data="export_historical_pdf")],
            [InlineKeyboardButton("🔙 Back to History", callback_data="schedule_history")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    
    async def export_historical_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export PDF for a historical week"""
        schedules = context.user_data.get('historical_schedules', [])
        week_dates = context.user_data.get('historical_week_dates', {})
        date_range = context.user_data.get('historical_date_range', '')
        
        if not schedules:
            keyboard = [[InlineKeyboardButton("🔙 Back to History", callback_data="schedule_history")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                "❌ No schedule data found for this week.",
                reply_markup=reply_markup
            )
            return MAIN_MENU
        
        try:
            print(f"DEBUG: Starting historical PDF generation for {date_range}")
            
            # Send a "generating" message first to prevent timeout
            query = update.callback_query
            await query.edit_message_text(
                f"⏳ Generating PDF for {date_range}... Please wait.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Convert schedules to PDF-ready format
            pdf_ready_schedules = self.prepare_schedules_for_pdf(schedules)
            print(f"DEBUG: Historical converted data for {len(pdf_ready_schedules)} records")
            
            # Create a unique filename for historical PDF
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = self.pdf_gen.filename
            historical_filename = f"schedule_{date_range.replace(' ', '_').replace(',', '')}_{timestamp}.pdf"
            
            print(f"DEBUG: Calling PDF generator for historical data...")
            pdf_filename = self.pdf_gen.generate_schedule_pdf(pdf_ready_schedules, week_dates, date_range, historical_filename)
            print(f"DEBUG: Historical PDF generated successfully: {pdf_filename}")
            
            # Send PDF
            with open(pdf_filename, 'rb') as pdf_file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=pdf_file,
                    filename=historical_filename,
                    caption=f"📄 Historical Schedule: {date_range}"
                )
            
            keyboard = [
                [InlineKeyboardButton("🔙 Back to History", callback_data="schedule_history")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ Historical PDF generated and sent successfully!\n\n*Week:* {date_range}",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error generating historical PDF: {e}")
            import traceback
            traceback.print_exc()
            
            keyboard = [[InlineKeyboardButton("🔙 Back to History", callback_data="schedule_history")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query = update.callback_query
            await query.edit_message_text(
                f"❌ Error generating historical PDF: {str(e)}\n\nPlease check the console for more details.",
                reply_markup=reply_markup
            )
        
        return MAIN_MENU
    
    async def show_bulk_schedule_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bulk scheduling options"""
        text = "🔄 *Bulk Scheduling Options*\n\n"
        text += "Choose how you want to schedule your team:"
        
        keyboard = [
            [InlineKeyboardButton("📋 Copy from Previous Week", callback_data="copy_previous_week")],
            [InlineKeyboardButton("📅 Schedule All Staff (Fresh)", callback_data="schedule_all_fresh")],
            [InlineKeyboardButton("📊 Apply Template", callback_data="apply_template")],
            [InlineKeyboardButton("⚡ Quick Schedule (Same Times)", callback_data="quick_schedule")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    
    async def copy_previous_week(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Copy schedules from previous week"""
        try:
            # Calculate current and previous week dates
            week_dates, week_start = self.calculate_week_dates()
            date_range = self.format_date_range(week_dates)
            
            # Get previous week's schedules
            previous_schedules = self.db.get_previous_week_schedules(week_start)
            
            if not previous_schedules:
                text = "❌ *No Previous Week Found*\n\n"
                text += "No schedules found for the previous week to copy from.\n\n"
                text += "Would you like to create fresh schedules instead?"
                
                keyboard = [
                    [InlineKeyboardButton("📅 Create Fresh Schedules", callback_data="schedule_all_fresh")],
                    [InlineKeyboardButton("🔙 Back to Bulk Menu", callback_data="bulk_schedule")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
                return MAIN_MENU
            
            # Organize previous schedules by staff
            staff_schedules = {}
            for staff_name, staff_id, day_of_week, schedule_date, is_working, start_time, end_time in previous_schedules:
                if staff_name not in staff_schedules:
                    staff_schedules[staff_name] = {'staff_id': staff_id, 'schedule': {}}
                
                # Format times for display
                formatted_start = self.format_time_for_display(start_time)
                formatted_end = self.format_time_for_display(end_time)
                
                staff_schedules[staff_name]['schedule'][day_of_week] = {
                    'is_working': bool(is_working),
                    'start_time': formatted_start or '',
                    'end_time': formatted_end or '',
                    'date': week_dates[day_of_week]  # Update to current week dates
                }
            
            # Store in context for editing
            context.user_data['bulk_schedule_data'] = staff_schedules
            context.user_data['week_dates'] = week_dates
            context.user_data['week_start'] = week_start
            
            # Show preview
            text = f"📋 *Preview: Copy from Previous Week*\n\n"
            text += f"*Target Week:* {date_range}\n\n"
            text += f"Found schedules for {len(staff_schedules)} staff members:\n\n"
            
            for staff_name, data in staff_schedules.items():
                schedule = data['schedule']
                working_days = sum(1 for day_data in schedule.values() if day_data.get('is_working', True))
                off_days = 7 - working_days
                text += f"*{staff_name}:* {working_days} working, {off_days} off\n"
            
            text += f"\nWould you like to proceed with copying these schedules?"
            
            keyboard = [
                [InlineKeyboardButton("✅ Copy & Save All", callback_data="confirm_copy_previous")],
                [InlineKeyboardButton("✏️ Copy & Edit First", callback_data="copy_and_edit")],
                [InlineKeyboardButton("🔙 Back to Bulk Menu", callback_data="bulk_schedule")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"Error copying previous week: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Error accessing previous week data: {str(e)}\n\nPlease try again or contact administrator.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bulk_schedule")]])
            )
            return MAIN_MENU
    
    async def confirm_copy_previous(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and save copied schedules from previous week"""
        try:
            bulk_schedule_data = context.user_data.get('bulk_schedule_data', {})
            week_start = context.user_data.get('week_start')
            
            if not bulk_schedule_data or not week_start:
                await update.callback_query.edit_message_text(
                    "❌ No schedule data found. Please try again.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bulk_schedule")]])
                )
                return MAIN_MENU
            
            # Show progress message
            await update.callback_query.edit_message_text(
                "⏳ *Copying Schedules...*\n\nPlease wait while we copy the previous week's schedules.",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Prepare data for bulk save
            schedules_data = []
            for staff_name, data in bulk_schedule_data.items():
                staff_id = data['staff_id']
                schedule_data = data['schedule']
                schedules_data.append((staff_id, staff_name, schedule_data))
            
            # Detect conflicts before saving
            conflicts, warnings = self.db.detect_schedule_conflicts(schedules_data, week_start)
            
            # Create scheduling session
            session_id = self.db.create_scheduling_session(week_start, f"BULK_COPY_{update.effective_user.id}")
            
            # Save all schedules atomically
            success, saved_count, failed_saves = self.db.save_bulk_schedules(schedules_data, week_start, f"BULK_COPY_{update.effective_user.id}")
            
            if success:
                # Complete the session
                self.db.complete_scheduling_session(session_id)
                
                # Clear context
                context.user_data.clear()
                
                date_range = self.format_date_range(context.user_data.get('week_dates', {}))
                
                text = f"✅ *Schedules Copied Successfully!*\n\n"
                text += f"*Week:* {date_range}\n"
                text += f"*Saved:* {saved_count} total day schedules\n"
                text += f"*Staff:* {len(schedules_data)} people\n\n"
                
                # Add conflict warnings if any
                if conflicts:
                    text += f"⚠️ *Conflicts Detected:*\n"
                    for conflict in conflicts[:3]:  # Show first 3
                        text += f"{conflict}\n"
                    if len(conflicts) > 3:
                        text += f"... and {len(conflicts)-3} more\n"
                    text += "\n"
                
                if warnings:
                    text += f"📋 *Warnings:*\n"
                    for warning in warnings[:3]:  # Show first 3
                        text += f"{warning}\n"
                    if len(warnings) > 3:
                        text += f"... and {len(warnings)-3} more\n"
                    text += "\n"
                
                text += f"All schedules have been copied from the previous week!"
                
                keyboard = [
                    [InlineKeyboardButton("👀 View Schedules", callback_data="view_current_schedules")],
                    [InlineKeyboardButton("📄 Generate PDF", callback_data="export_pdf")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
                ]
            else:
                text = f"⚠️ *Partial Copy Completed*\n\n"
                text += f"*Saved:* {saved_count} day schedules\n"
                text += f"*Failed:* {len(failed_saves)} operations\n\n"
                if failed_saves:
                    text += f"*Errors:*\n"
                    for error in failed_saves[:3]:
                        text += f"• {error}\n"
                    if len(failed_saves) > 3:
                        text += f"... and {len(failed_saves)-3} more\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Try Again", callback_data="confirm_copy_previous")],
                    [InlineKeyboardButton("👀 View Current Status", callback_data="view_current_schedules")],
                    [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"Error confirming copy previous: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Error saving schedules: {str(e)}\n\nPlease try again or contact administrator.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bulk_schedule")]])
            )
            return MAIN_MENU
    
    async def show_weekly_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show weekly coverage statistics and insights"""
        try:
            week_dates, week_start = self.calculate_week_dates()
            date_range = self.format_date_range(week_dates)
            
            # Get coverage stats
            stats = self.db.get_weekly_coverage_stats(week_start)
            
            if not stats:
                text = f"📊 *Weekly Coverage Stats*\n\n"
                text += f"*Week:* {date_range}\n\n"
                text += "No schedules found for this week.\n\n"
                text += "Create schedules first to see coverage statistics."
                
                keyboard = [
                    [InlineKeyboardButton("📅 Create Schedules", callback_data="set_schedule")],
                    [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
                ]
            else:
                text = f"📊 *Weekly Coverage Stats*\n\n"
                text += f"*Week:* {date_range}\n\n"
                
                total_staff = 0
                total_working_days = 0
                critical_days = []
                
                for day_of_week, total, working, off in stats:
                    if total > total_staff:
                        total_staff = total
                    total_working_days += working
                    
                    coverage_percent = (working / total * 100) if total > 0 else 0
                    
                    if coverage_percent <= 50:
                        status = "🚨"
                        critical_days.append(day_of_week)
                    elif coverage_percent <= 75:
                        status = "⚠️"
                    else:
                        status = "✅"
                    
                    text += f"*{day_of_week}:* {status} {working}/{total} staff ({coverage_percent:.0f}%)\n"
                
                text += f"\n📈 *Summary:*\n"
                text += f"• Total Staff: {total_staff}\n"
                text += f"• Total Working Days: {total_working_days}\n"
                text += f"• Average Coverage: {(total_working_days / (len(stats) * total_staff) * 100):.0f}%\n"
                
                if critical_days:
                    text += f"\n🚨 *Critical Coverage Days:*\n"
                    for day in critical_days:
                        text += f"• {day}\n"
                
                keyboard = [
                    [InlineKeyboardButton("📋 View Schedules", callback_data="view_current_schedules")],
                    [InlineKeyboardButton("✏️ Edit Schedules", callback_data="set_schedule")],
                    [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"Error showing weekly stats: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Error loading statistics: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_main")]])
            )
            return MAIN_MENU
    
    async def show_schedule_templates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available schedule templates"""
        try:
            templates = self.db.get_schedule_templates()
            
            text = "🔧 *Schedule Templates*\n\n"
            
            if not templates:
                text += "No templates found. You can create templates by saving common schedule patterns.\n\n"
                text += "Templates help you quickly apply the same schedule structure to multiple weeks."
                
                keyboard = [
                    [InlineKeyboardButton("➕ Create Template", callback_data="create_template")],
                    [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")]
                ]
            else:
                text += f"Available templates ({len(templates)}):\n\n"
                
                keyboard = []
                for template in templates[:10]:  # Show first 10 templates
                    name = template['name']
                    description = template['description'] or "No description"
                    created_by = template['created_by']
                    
                    text += f"*{name}*\n"
                    text += f"  📝 {description[:50]}\n"
                    text += f"  👤 Created by: {created_by}\n\n"
                    
                    keyboard.append([InlineKeyboardButton(f"📋 Apply: {name}", callback_data=f"apply_template_{template['id']}")])
                
                if len(templates) > 10:
                    text += f"... and {len(templates) - 10} more templates\n"
                
                keyboard.append([InlineKeyboardButton("➕ Create New Template", callback_data="create_template")])
                keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"Error showing schedule templates: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Error loading templates: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_main")]])
            )
            return MAIN_MENU
    
    async def quick_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick schedule all staff with same times"""
        try:
            # Get all staff
            all_staff = self.db.get_all_staff()
            
            if not all_staff:
                await update.callback_query.edit_message_text(
                    "❌ No staff members found. Add staff first.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👥 Add Staff", callback_data="staff_management")]])
                )
                return MAIN_MENU
            
            text = f"⚡ *Quick Schedule Setup*\n\n"
            text += f"This will set the same schedule for all {len(all_staff)} staff members.\n\n"
            text += f"*Staff:* {', '.join([name for _, name in all_staff])}\n\n"
            text += f"Choose a common schedule pattern:"
            
            keyboard = [
                [InlineKeyboardButton("🌞 Monday-Friday (9:00-17:00)", callback_data="quick_pattern_weekdays")],
                [InlineKeyboardButton("📅 6 Days/Week (10:00-18:00)", callback_data="quick_pattern_six_days")],
                [InlineKeyboardButton("🏪 Full Week (12:00-20:00)", callback_data="quick_pattern_full_week")],
                [InlineKeyboardButton("⚙️ Custom Pattern", callback_data="quick_pattern_custom")],
                [InlineKeyboardButton("🔙 Back to Bulk Menu", callback_data="bulk_schedule")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            return MAIN_MENU
            
        except Exception as e:
            logger.error(f"Error in quick schedule: {e}")
            await update.callback_query.edit_message_text(
                f"❌ Error setting up quick schedule: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bulk_schedule")]])
            )
            return MAIN_MENU

    # Handler functions for conversation states
    async def handle_bulk_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bulk schedule menu callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "bulk_schedule":
            await self.show_bulk_schedule_menu(update, context)
            return BULK_SCHEDULE
        elif query.data == "copy_previous_week":
            await self.copy_previous_week(update, context)
            return BULK_SCHEDULE
        elif query.data == "confirm_copy_previous":
            await self.confirm_copy_previous(update, context)
            return BULK_SCHEDULE
        elif query.data == "quick_schedule":
            await self.quick_schedule(update, context)
            return BULK_SCHEDULE
        elif query.data == "back_main":
            return await self.show_main_menu(update, context)
        
        return BULK_SCHEDULE

    async def handle_weekly_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle weekly stats callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_main":
            return await self.show_main_menu(update, context)
        elif query.data == "refresh_stats":
            await self.show_weekly_stats(update, context)
            return WEEKLY_STATS
        
        return WEEKLY_STATS

    async def handle_schedule_templates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle schedule templates callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_main":
            return await self.show_main_menu(update, context)
        elif query.data.startswith("template_"):
            template_id = query.data.split("_", 1)[1]
            await self.apply_template(update, context, template_id)
            return SCHEDULE_TEMPLATES
        
        return SCHEDULE_TEMPLATES

    async def handle_schedule_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle schedule history callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "schedule_history":
            await self.show_schedule_history(update, context)
            return SCHEDULE_HISTORY
        elif query.data == "back_main":
            return await self.show_main_menu(update, context)
        elif query.data.startswith("view_week_"):
            week_key = query.data.split("_")[2]
            await self.view_week_schedule(update, context, week_key)
            return SCHEDULE_HISTORY
        
        return SCHEDULE_HISTORY

    async def handle_week_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle week selection callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "back_schedule_menu":
            return await self.show_schedule_menu(update, context)
        elif query.data == "back_main":
            return await self.show_main_menu(update, context)
        
        # Calculate the selected week dates
        current_week_dates, current_week_start = self.calculate_week_dates()
        
        # Handle PDF export week selection
        if query.data in ["export_pdf_current", "export_pdf_next", "export_pdf_after_next"]:
            if query.data == "export_pdf_current":
                week_dates = current_week_dates
                week_start = current_week_start
            elif query.data == "export_pdf_next":
                week_dates, week_start = self.calculate_week_dates(current_week_start + timedelta(days=7))
            elif query.data == "export_pdf_after_next":
                week_dates, week_start = self.calculate_week_dates(current_week_start + timedelta(days=14))
            
            # Store selected week dates in context for PDF generation
            context.user_data['pdf_week_dates'] = week_dates
            context.user_data['pdf_week_start'] = week_start
            context.user_data['pdf_date_range'] = self.format_date_range(week_dates)
            
            # Generate PDF for the selected week
            return await self.export_pdf_for_week(update, context)
        
        # Handle "all staff" week selection (new flow)
        elif query.data in ["select_week_all_current", "select_week_all_next", "select_week_all_after_next"]:
            if query.data == "select_week_all_current":
                week_dates = current_week_dates
                week_start = current_week_start
            elif query.data == "select_week_all_next":
                week_dates, week_start = self.calculate_week_dates(current_week_start + timedelta(days=7))
            elif query.data == "select_week_all_after_next":
                week_dates, week_start = self.calculate_week_dates(current_week_start + timedelta(days=14))
            
            # Store selected week dates in context
            context.user_data['week_dates'] = week_dates
            context.user_data['week_start'] = week_start
            
            # Show staff selection menu for the selected week
            return await self.show_schedule_menu(update, context)
        
        # Handle historical PDF export
        elif query.data == "export_pdf_historical":
            return await self.show_schedule_history(update, context)
        
        # Handle individual staff week selection (existing flow)
        elif query.data in ["select_week_current", "select_week_next", "select_week_after_next"]:
            if query.data == "select_week_current":
                week_dates = current_week_dates
                week_start = current_week_start
            elif query.data == "select_week_next":
                week_dates, week_start = self.calculate_week_dates(current_week_start + timedelta(days=7))
            elif query.data == "select_week_after_next":
                week_dates, week_start = self.calculate_week_dates(current_week_start + timedelta(days=14))
            
            # Store selected week dates in context
            context.user_data['week_dates'] = week_dates
            context.user_data['week_start'] = week_start
            
            # Check if staff already has a schedule for this week
            staff_id = context.user_data.get('current_staff_id')
            if staff_id:
                existing_schedule = self.db.get_staff_schedule_for_week(staff_id, week_start)
                if existing_schedule:
                    # Convert to the format expected by show_existing_schedule
                    schedule_list = []
                    for day in DAYS_OF_WEEK:
                        if day in existing_schedule:
                            day_data = existing_schedule[day]
                            schedule_list.append((
                                day,
                                day_data['is_working'],
                                day_data['start_time'],
                                day_data['end_time']
                            ))
                    return await self.show_existing_schedule(update, context, schedule_list)
            
            # No existing schedule, start fresh
            return await self.show_schedule_input_form(update, context)
        
        return await self.show_schedule_menu(update, context)

    async def show_pdf_week_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show week selection options for PDF export"""
        # Calculate three week options
        current_week_dates, current_week_start = self.calculate_week_dates()
        next_week_dates, next_week_start = self.calculate_week_dates(current_week_start + timedelta(days=7))
        week_after_next_dates, week_after_next_start = self.calculate_week_dates(current_week_start + timedelta(days=14))
        
        # Get current date in Toronto timezone
        toronto_tz = pytz.timezone('America/Toronto')
        today = datetime.now(toronto_tz).date()
        
        # Format date ranges
        current_range = self.format_date_range(current_week_dates)
        next_range = self.format_date_range(next_week_dates)
        week_after_next_range = self.format_date_range(week_after_next_dates)
        
        # Check which days in current week are in the past
        current_week_past_days = []
        current_week_remaining_days = []
        for day, date in current_week_dates.items():
            if date < today:
                current_week_past_days.append(day)
            else:
                current_week_remaining_days.append(day)
        
        text = f"📄 *Export PDF Schedule*\n\n"
        text += f"Select which week's schedule to export as PDF:\n\n"
        
        # Current week option
        if current_week_remaining_days:
            text += f"🔄 *Current Week ({current_range})*\n"
            if current_week_past_days:
                text += f"   ⚠️ {len(current_week_past_days)} days completed, {len(current_week_remaining_days)} days remaining\n"
            else:
                text += f"   ✅ Full week available\n"
        else:
            text += f"❌ *Current Week ({current_range})*\n"
            text += f"   ⏰ All days in the past\n"
        
        text += f"\n📅 *Next Week ({next_range})*\n"
        text += f"   ✅ Full week available\n"
        
        text += f"\n📅 *Week After Next ({week_after_next_range})*\n"
        text += f"   ✅ Full week available\n"
        
        text += f"\n📚 *Historical Weeks*\n"
        text += f"   📖 View and export any past week\n"
        
        keyboard = []
        
        # Add current week button only if there are remaining days
        if current_week_remaining_days:
            keyboard.append([InlineKeyboardButton(f"🔄 Current Week ({current_range})", callback_data="export_pdf_current")])
        
        keyboard.append([InlineKeyboardButton(f"📅 Next Week ({next_range})", callback_data="export_pdf_next")])
        keyboard.append([InlineKeyboardButton(f"📅 Week After Next ({week_after_next_range})", callback_data="export_pdf_after_next")])
        keyboard.append([InlineKeyboardButton("📚 Historical Weeks", callback_data="export_pdf_historical")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WEEK_SELECTION

    async def show_week_selection_for_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show week selection options for all staff scheduling"""
        # Calculate three week options
        current_week_dates, current_week_start = self.calculate_week_dates()
        next_week_dates, next_week_start = self.calculate_week_dates(current_week_start + timedelta(days=7))
        week_after_next_dates, week_after_next_start = self.calculate_week_dates(current_week_start + timedelta(days=14))
        
        # Get current date in Toronto timezone
        toronto_tz = pytz.timezone('America/Toronto')
        today = datetime.now(toronto_tz).date()
        
        # Format date ranges
        current_range = self.format_date_range(current_week_dates)
        next_range = self.format_date_range(next_week_dates)
        week_after_next_range = self.format_date_range(week_after_next_dates)
        
        # Check which days in current week are in the past
        current_week_past_days = []
        current_week_remaining_days = []
        for day, date in current_week_dates.items():
            if date < today:
                current_week_past_days.append(day)
            else:
                current_week_remaining_days.append(day)
        
        text = f"📅 *Choose Week for Scheduling*\n\n"
        text += f"Select which 7-day period you want to schedule:\n\n"
        
        # Current week option
        if current_week_remaining_days:
            text += f"🔄 *Current Week ({current_range})*\n"
            if current_week_past_days:
                text += f"   ⚠️ {len(current_week_past_days)} days completed, {len(current_week_remaining_days)} days remaining\n"
            else:
                text += f"   ✅ Full week available\n"
        else:
            text += f"❌ *Current Week ({current_range})*\n"
            text += f"   ⏰ All days in the past\n"
        
        text += f"\n📅 *Next Week ({next_range})*\n"
        text += f"   ✅ Full week available\n"
        
        text += f"\n📅 *Week After Next ({week_after_next_range})*\n"
        text += f"   ✅ Full week available\n"
        
        keyboard = []
        
        # Add current week button only if there are remaining days
        if current_week_remaining_days:
            keyboard.append([InlineKeyboardButton(f"🔄 Current Week ({current_range})", callback_data="select_week_all_current")])
        
        keyboard.append([InlineKeyboardButton(f"📅 Next Week ({next_range})", callback_data="select_week_all_next")])
        keyboard.append([InlineKeyboardButton(f"📅 Week After Next ({week_after_next_range})", callback_data="select_week_all_after_next")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WEEK_SELECTION

    async def show_week_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show week selection options before starting schedule"""
        staff_name = context.user_data.get('current_staff_name', 'Unknown')
        
        # Calculate three week options
        current_week_dates, current_week_start = self.calculate_week_dates()
        next_week_dates, next_week_start = self.calculate_week_dates(current_week_start + timedelta(days=7))
        week_after_next_dates, week_after_next_start = self.calculate_week_dates(current_week_start + timedelta(days=14))
        
        # Get current date in Toronto timezone
        toronto_tz = pytz.timezone('America/Toronto')
        today = datetime.now(toronto_tz).date()
        
        # Format date ranges
        current_range = self.format_date_range(current_week_dates)
        next_range = self.format_date_range(next_week_dates)
        week_after_next_range = self.format_date_range(week_after_next_dates)
        
        # Check which days in current week are in the past
        current_week_past_days = []
        current_week_remaining_days = []
        for day, date in current_week_dates.items():
            if date < today:
                current_week_past_days.append(day)
            else:
                current_week_remaining_days.append(day)
        
        text = f"📅 *Choose Week for {staff_name}*\n\n"
        text += f"Select which 7-day period you want to schedule:\n\n"
        
        # Current week option
        if current_week_remaining_days:
            text += f"🔄 *Current Week ({current_range})*\n"
            if current_week_past_days:
                text += f"   ⚠️ {len(current_week_past_days)} days completed, {len(current_week_remaining_days)} days remaining\n"
            else:
                text += f"   ✅ Full week available\n"
        else:
            text += f"❌ *Current Week ({current_range})*\n"
            text += f"   ⏰ All days in the past\n"
        
        text += f"\n📅 *Next Week ({next_range})*\n"
        text += f"   ✅ Full week available\n"
        
        text += f"\n📅 *Week After Next ({week_after_next_range})*\n"
        text += f"   ✅ Full week available\n"
        
        keyboard = []
        
        # Add current week button only if there are remaining days
        if current_week_remaining_days:
            keyboard.append([InlineKeyboardButton(f"🔄 Current Week ({current_range})", callback_data="select_week_current")])
        
        keyboard.append([InlineKeyboardButton(f"📅 Next Week ({next_range})", callback_data="select_week_next")])
        keyboard.append([InlineKeyboardButton(f"📅 Week After Next ({week_after_next_range})", callback_data="select_week_after_next")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Staff List", callback_data="back_schedule_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return WEEK_SELECTION

if __name__ == "__main__":
    bot = StaffSchedulerBot()
    bot.run() 
