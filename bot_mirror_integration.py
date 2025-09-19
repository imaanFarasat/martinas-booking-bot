#!/usr/bin/env python3
"""
Bot Integration for Smart Mirror System
Add this to bot_async.py to integrate the smart mirror functionality
"""

from smart_mirror_system import SmartMirrorSystem
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

class BotMirrorIntegration:
    def __init__(self):
        self.mirror_system = SmartMirrorSystem()
    
    async def show_mirror_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show smart mirror menu"""
        current_week_start = self.mirror_system.get_current_week_start()
        previous_week_start = self.mirror_system.get_previous_week_start()
        next_week_start = self.mirror_system.get_next_week_start()
        
        text = "🔄 *Smart Mirror System*\n\n"
        text += "Copy schedules from one week to another with smart staff handling.\n\n"
        text += f"📅 *Current week:* {current_week_start} to {current_week_start + timedelta(days=6)}\n"
        text += f"📅 *Previous week:* {previous_week_start} to {previous_week_start + timedelta(days=6)}\n"
        text += f"📅 *Next week:* {next_week_start} to {next_week_start + timedelta(days=6)}\n\n"
        text += "Choose what to mirror:"
        
        keyboard = [
            [
                InlineKeyboardButton("📅 Previous → Next Week", callback_data="mirror_prev_next"),
                InlineKeyboardButton("📅 Current → Next Week", callback_data="mirror_curr_next")
            ],
            [
                InlineKeyboardButton("👥 View Staff Changes", callback_data="view_staff_changes"),
                InlineKeyboardButton("✏️ Edit Next Week Day", callback_data="edit_next_week_day")
            ],
            [
                InlineKeyboardButton("📋 View Next Week", callback_data="view_next_week"),
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_main")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return "MIRROR_MENU"
    
    async def handle_mirror_prev_next(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mirror previous week to next week"""
        query = update.callback_query
        await query.answer()
        
        # Show processing message
        await query.edit_message_text(
            "🔄 Mirroring previous week to next week...\n\n⏳ Please wait, this may take a moment.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            previous_week_start = self.mirror_system.get_previous_week_start()
            next_week_start = self.mirror_system.get_next_week_start()
            
            # Perform smart mirror
            result = self.mirror_system.smart_mirror_week(
                previous_week_start, 
                next_week_start, 
                "PREVIOUS WEEK"
            )
            
            # Show results
            text = self.mirror_system.get_mirror_summary_text(result)
            text += "\n\n🔄 *Smart Mirror Complete!*"
            
            keyboard = [
                [InlineKeyboardButton("✏️ Edit Next Week Day", callback_data="edit_next_week_day")],
                [InlineKeyboardButton("📋 View Next Week", callback_data="view_next_week")],
                [InlineKeyboardButton("🔙 Back to Mirror Menu", callback_data="mirror_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error during mirror operation: {str(e)}\n\n🔙 Back to mirror menu.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Mirror Menu", callback_data="mirror_menu")
                ]])
            )
        
        return "MIRROR_MENU"
    
    async def handle_mirror_curr_next(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mirror current week to next week"""
        query = update.callback_query
        await query.answer()
        
        # Show processing message
        await query.edit_message_text(
            "🔄 Mirroring current week to next week...\n\n⏳ Please wait, this may take a moment.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            current_week_start = self.mirror_system.get_current_week_start()
            next_week_start = self.mirror_system.get_next_week_start()
            
            # Perform smart mirror
            result = self.mirror_system.smart_mirror_week(
                current_week_start, 
                next_week_start, 
                "CURRENT WEEK"
            )
            
            # Show results
            text = self.mirror_system.get_mirror_summary_text(result)
            text += "\n\n🔄 *Smart Mirror Complete!*"
            
            keyboard = [
                [InlineKeyboardButton("✏️ Edit Next Week Day", callback_data="edit_next_week_day")],
                [InlineKeyboardButton("📋 View Next Week", callback_data="view_next_week")],
                [InlineKeyboardButton("🔙 Back to Mirror Menu", callback_data="mirror_menu")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error during mirror operation: {str(e)}\n\n🔙 Back to mirror menu.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Mirror Menu", callback_data="mirror_menu")
                ]])
            )
        
        return "MIRROR_MENU"
    
    async def show_edit_day_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show day selection for editing next week"""
        text = "✏️ *Edit Next Week Day*\n\n"
        text += "Choose which day you want to edit:"
        
        keyboard = []
        for i, day in enumerate(DAYS_OF_WEEK):
            keyboard.append([InlineKeyboardButton(f"📅 {day}", callback_data=f"edit_day_{day.lower()}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Mirror Menu", callback_data="mirror_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return "EDIT_DAY_MENU"
    
    async def handle_edit_day(self, update: Update, context: ContextTypes.DEFAULT_TYPE, day: str):
        """Handle editing a specific day"""
        query = update.callback_query
        await query.answer()
        
        next_week_start = self.mirror_system.get_next_week_start()
        target_week_dates = self.mirror_system.get_week_dates(next_week_start)
        target_date = target_week_dates[day]
        
        # Get current schedules for this day
        day_schedules = self.mirror_system.get_week_schedules(next_week_start)
        day_schedules = [s for s in day_schedules if s[2] == day]  # Filter by day
        
        if not day_schedules:
            await query.edit_message_text(
                f"❌ No schedules found for {day} ({target_date})\n\n🔙 Back to day selection.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back to Day Selection", callback_data="edit_next_week_day")
                ]])
            )
            return "EDIT_DAY_MENU"
        
        # Show staff for this day
        text = f"✏️ *Editing {day} ({target_date})*\n\n"
        text += "👥 *Staff scheduled for this day:*\n\n"
        
        for i, schedule in enumerate(day_schedules):
            staff_name = schedule[1]
            is_working = schedule[4]
            start_time = schedule[5]
            end_time = schedule[6]
            
            if is_working:
                time_info = f"{start_time}-{end_time}" if start_time and end_time else "Not Set"
            else:
                time_info = "OFF"
            
            text += f"{i+1}. **{staff_name}**: {time_info}\n"
        
        text += "\nChoose what to do:"
        
        keyboard = [
            [InlineKeyboardButton("🔄 Turn All OFF", callback_data=f"turn_all_off_{day.lower()}")],
            [InlineKeyboardButton("✏️ Edit Individual Staff", callback_data=f"edit_individual_{day.lower()}")],
            [InlineKeyboardButton("✅ Keep As Is", callback_data="edit_next_week_day")],
            [InlineKeyboardButton("🔙 Back to Day Selection", callback_data="edit_next_week_day")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        return "EDIT_DAY_OPTIONS"

# Add these to the main bot_async.py file:

# 1. Add to main menu keyboard:
# [InlineKeyboardButton("🔄 Smart Mirror", callback_data="smart_mirror")]

# 2. Add to handle_main_menu:
# elif query.data == "smart_mirror":
#     return await self.show_mirror_menu(update, context)

# 3. Add conversation states:
# MIRROR_MENU = "mirror_menu"
# EDIT_DAY_MENU = "edit_day_menu"
# EDIT_DAY_OPTIONS = "edit_day_options"

# 4. Add to conversation handler:
# CallbackQueryHandler(self.handle_mirror_menu, pattern="^mirror_"),
# CallbackQueryHandler(self.handle_edit_day_menu, pattern="^edit_day_"),
# CallbackQueryHandler(self.handle_edit_day_options, pattern="^edit_individual_|^turn_all_off_"),
