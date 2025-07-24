from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import os
from config import PDF_FILENAME, PDF_TITLE, DAYS_OF_WEEK
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.filename = PDF_FILENAME
        self.title = PDF_TITLE
    
    def generate_schedule_pdf(self, schedule_data, week_dates=None, date_range=None, custom_filename=None):
        """Generate PDF schedule"""
        try:
            print(f"DEBUG: Starting PDF generation with {len(schedule_data)} schedule entries")
            print(f"DEBUG: Schedule data sample: {schedule_data[:3] if schedule_data else 'No data'}")
            print(f"DEBUG: Schedule data type: {type(schedule_data)}")
            
            # Use custom filename if provided, otherwise use default
            if custom_filename:
                filename = custom_filename
            else:
                filename = self.filename
            
            doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
            elements = []
            
            # Add title
            title_text = "Staff Schedule"
            if date_range:
                title_text += f" - {date_range}"
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=getSampleStyleSheet()['Title'],
                fontSize=16,
                spaceAfter=20,
                alignment=1  # Center alignment
            )
            title = Paragraph(title_text, title_style)
            elements.append(title)
            
            # Create table data
            # First, organize data by employee
            employee_schedules = {}
            days_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            print(f"DEBUG: Processing {len(schedule_data)} records")
            
            for record in schedule_data:
                print(f"DEBUG: Processing record: {record}")
                # Handle different record formats
                if len(record) == 6:
                    staff_name, day, schedule_date, is_working, start_time, end_time = record
                elif len(record) == 5:
                    staff_name, day, schedule_date, is_working, start_time = record
                    end_time = ""
                elif len(record) == 4:
                    staff_name, day, schedule_date, is_working = record
                    start_time = end_time = ""
                else:
                    print(f"DEBUG: Skipping record with unexpected format: {record}")
                    continue
                
                print(f"DEBUG: Staff name: {staff_name}, Day: {day}, Working: {is_working}")
                
                if staff_name not in employee_schedules:
                    employee_schedules[staff_name] = {}
                
                # Format date
                if week_dates and day in week_dates:
                    try:
                        if isinstance(week_dates[day], str):
                            date_obj = datetime.strptime(week_dates[day], '%Y-%m-%d')
                        else:
                            date_obj = week_dates[day]
                        date_str = date_obj.strftime('%b %d')
                    except:
                        date_str = "N/A"
                elif schedule_date:
                    try:
                        if isinstance(schedule_date, str):
                            date_obj = datetime.strptime(schedule_date, '%Y-%m-%d')
                        else:
                            date_obj = schedule_date
                        date_str = date_obj.strftime('%b %d')
                    except:
                        date_str = schedule_date
                else:
                    date_str = "N/A"
                
                # Format day with date and status
                if is_working:
                    time_str = f"{start_time}-{end_time}" if start_time and end_time else "Not set"
                    day_info = time_str
                else:
                    day_info = "Off"
                
                employee_schedules[staff_name][day] = day_info
            
            print(f"DEBUG: Employee schedules: {employee_schedules}")
            
            # Create table headers with multi-line format
            header_row = ['Employee']
            for day in days_order:
                if week_dates and day in week_dates:
                    date_obj = week_dates[day]
                    month_name = date_obj.strftime('%B')
                    day_num = date_obj.day
                    header_row.append(f"{day}\n({month_name} {day_num})")
                else:
                    header_row.append(f"{day}\n(N/A)")
            
            # Add Total Hours column
            header_row.append('Total Hours')
            
            table_data = [header_row]
            
            # Add employee rows
            if not employee_schedules:
                table_data.append(['No schedules found'] + [''] * 8)  # 7 days + 1 total hours column
            else:
                for employee, schedule in employee_schedules.items():
                    print(f"DEBUG: Adding employee row for: {employee}")
                    row = [employee]
                    total_hours = 0
                    
                    for day in days_order:
                        day_value = schedule.get(day, f"{day} - Not set")
                        row.append(day_value)
                        print(f"DEBUG: {day}: {day_value}")
                        
                        # Calculate hours for this day
                        if day_value != "Off" and "-" in day_value and "Not set" not in day_value:
                            try:
                                # Extract start and end times (format: "09:00-17:00")
                                times = day_value.split("-")
                                if len(times) == 2:
                                    start_time = times[0].strip()
                                    end_time = times[1].strip()
                                    
                                    # Convert to datetime objects for calculation
                                    start_dt = datetime.strptime(start_time, "%H:%M")
                                    end_dt = datetime.strptime(end_time, "%H:%M")
                                    
                                    # Calculate hours difference
                                    time_diff = end_dt - start_dt
                                    hours = time_diff.total_seconds() / 3600
                                    
                                    # Handle overnight shifts (negative hours)
                                    if hours < 0:
                                        hours += 24
                                    
                                    total_hours += hours
                            except Exception as e:
                                print(f"DEBUG: Error calculating hours for {day_value}: {e}")
                                # Don't add any hours for invalid time formats
                    
                    # Add total hours to the row
                    row.append(f"{total_hours:.1f}")
                    table_data.append(row)
            
            print(f"DEBUG: Final table data: {table_data}")
            
            # Create table
            table = Table(table_data)
            
            # Create a very light red color for "Off" cells
            very_light_red = colors.Color(1.0, 0.95, 0.95)  # Very light red
            
            # Base table style
            table_style = [
                # Header styling - primary blue background
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Content styling - white background
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Grid styling - light gray lines
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.blue),
                
                # Employee column styling - light blue background
                ('BACKGROUND', (0, 1), (0, -1), colors.lightblue),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (0, -1), 10),
                
                # Total Hours column styling - light green background and bold text
                ('BACKGROUND', (-1, 1), (-1, -1), colors.lightgreen),
                ('FONTNAME', (-1, 1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (-1, 1), (-1, -1), 10),
                
                # Cell padding for better spacing
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Multi-line text support
                ('WORDWRAP', (0, 0), (-1, -1), True),
            ]
            
            # Add conditional styling for "Off" cells
            for row_idx, row in enumerate(table_data[1:], 1):  # Skip header row
                for col_idx, cell_value in enumerate(row[1:-1], 1):  # Skip employee name column and Total Hours column
                    if cell_value == "Off":
                        table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), very_light_red))
            
            table.setStyle(TableStyle(table_style))
            
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            print(f"DEBUG: PDF generated successfully: {filename}")
            return filename
            
        except Exception as e:
            print(f"ERROR: Failed to generate PDF: {e}")
            import traceback
            traceback.print_exc()
            raise e 