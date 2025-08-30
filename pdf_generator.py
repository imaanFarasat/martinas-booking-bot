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
    
    def generate_schedule_pdf(self, schedule_data, week_dates=None, date_range=None, custom_filename=None, all_staff_names=None):
        """Generate PDF schedule"""
        try:
            print(f"DEBUG: Starting PDF generation with {len(schedule_data)} schedule entries")
            print(f"DEBUG: Schedule data sample: {schedule_data[:3] if schedule_data else 'No data'}")
            print(f"DEBUG: Schedule data type: {type(schedule_data)}")
            print(f"DEBUG: All staff names provided: {all_staff_names}")
            
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
            
            # Get all staff members - use provided list or extract from schedule data
            if all_staff_names:
                all_employees = set(all_staff_names)
                print(f"DEBUG: Using provided staff names: {all_employees}")
            else:
                all_employees = set()
                for record in schedule_data:
                    if len(record) >= 1:
                        all_employees.add(record[0])  # staff_name
                print(f"DEBUG: Extracted staff names from schedule data: {all_employees}")
            
            # Initialize employee schedules with "Not Set" for all days
            for employee in all_employees:
                employee_schedules[employee] = {}
                for day in days_order:
                    employee_schedules[employee][day] = "Not Set"
            
            # Now fill in the actual schedule data
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
                
                # Format day info based on working status
                if is_working:
                    if start_time and end_time and start_time.strip() and end_time.strip():
                        day_info = f"{start_time.strip()}-{end_time.strip()}"
                    else:
                        day_info = "Not Set"
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
            
            # Define special staff members who should appear at the end
            special_staff = ['Shanine', 'Kenza', 'Stacy']
            
            # Sort employees: regular staff first, then special staff
            regular_employees = []
            special_employees = []
            
            for employee in sorted(employee_schedules.keys()):
                if employee in special_staff:
                    special_employees.append(employee)
                else:
                    regular_employees.append(employee)
            
            # Combine lists with special staff at the end
            sorted_employees = regular_employees + special_employees
            print(f"DEBUG: Sorted employees - Regular: {regular_employees}, Special: {special_employees}")
            
            # Add employee rows
            if not employee_schedules:
                table_data.append(['No schedules found'] + [''] * 8)  # 7 days + 1 total hours column
            else:
                for employee in sorted_employees:  # Use the custom sorted order
                    schedule = employee_schedules[employee]
                    print(f"DEBUG: Adding employee row for: {employee}")
                    row = [employee]
                    total_hours = 0
                    
                    for day in days_order:
                        day_value = schedule.get(day, "Not Set")
                        row.append(day_value)
                        print(f"DEBUG: {day}: {day_value}")
                        
                        # Calculate hours for this day - improved logic
                        if (day_value != "Off" and 
                            day_value != "Not Set" and 
                            "-" in day_value):
                            try:
                                # Extract start and end times (format: "09:00-17:00")
                                times = day_value.split("-")
                                if len(times) == 2:
                                    start_time = times[0].strip()
                                    end_time = times[1].strip()
                                    
                                    # Validate time format (HH:MM)
                                    if ":" in start_time and ":" in end_time:
                                        # Convert to datetime objects for calculation
                                        start_dt = datetime.strptime(start_time, "%H:%M")
                                        end_dt = datetime.strptime(end_time, "%H:%M")
                                        
                                        # Calculate hours difference
                                        time_diff = end_dt - start_dt
                                        hours = time_diff.total_seconds() / 3600
                                        
                                        # Handle overnight shifts (negative hours)
                                        if hours < 0:
                                            hours += 24
                                        
                                        # Only add positive, reasonable hours (0-24)
                                        if 0 <= hours <= 24:
                                            total_hours += hours
                                        
                                        print(f"DEBUG: {day} hours calculated: {hours:.1f} (total now: {total_hours:.1f})")
                                    else:
                                        print(f"DEBUG: Invalid time format in '{day_value}' - no colons found")
                                else:
                                    print(f"DEBUG: Could not split '{day_value}' into 2 time parts")
                            except Exception as e:
                                print(f"DEBUG: Error calculating hours for '{day_value}': {e}")
                                # Don't add any hours for invalid time formats
                    
                    # Add total hours to the row (format to 1 decimal place)
                    row.append(f"{total_hours:.1f}h")
                    table_data.append(row)
                    print(f"DEBUG: {employee} total hours: {total_hours:.1f}")
            
            print(f"DEBUG: Final table data: {table_data}")
            
            # Create table with explicit column widths
            # Column widths: Employee (1.2"), 7 days (0.8" each), Total Hours (0.8")
            # Total width: 1.2 + (7 * 0.8) + 0.8 = 7.6 inches (fits within letter page ~8.5")
            col_widths = [1.2*inch] + [0.8*inch] * 7 + [0.8*inch]  # Employee + 7 days + Total Hours
            table = Table(table_data, colWidths=col_widths)
            
            # Create color scheme
            very_light_red = colors.Color(1.0, 0.95, 0.95)  # Very light red for "Off"
            very_light_yellow = colors.Color(1.0, 1.0, 0.9)  # Very light yellow for "Not Set"
            special_staff_color = colors.Color(0.95, 0.95, 1.0)  # Very light purple for special staff
            
            # Base table style
            table_style = [
                # Header styling - primary blue background
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),  # Slightly smaller header font
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),  # Reduce padding
                ('TOPPADDING', (0, 0), (-1, 0), 8),  # Reduce padding
                
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
                ('FONTSIZE', (0, 1), (0, -1), 9),  # Slightly smaller font for better fit
                
                # Total Hours column styling - light green background and bold text
                ('BACKGROUND', (-1, 1), (-1, -1), colors.lightgreen),
                ('FONTNAME', (-1, 1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (-1, 1), (-1, -1), 9),  # Slightly smaller font for better fit
                
                # Cell padding for better spacing
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                
                # Multi-line text support
                ('WORDWRAP', (0, 0), (-1, -1), True),
                
                # Ensure text fits within columns
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Slightly smaller font for better fit
                ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Reduce left padding
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),  # Reduce right padding
            ]
            
            # Add conditional styling for different cell values and special staff
            for row_idx, row in enumerate(table_data[1:], 1):  # Skip header row
                employee_name = row[0]  # First column is employee name
                
                # Check if this is a special staff member
                is_special_staff = employee_name in special_staff
                
                for col_idx, cell_value in enumerate(row[1:-1], 1):  # Skip employee name and Total Hours columns
                    if cell_value == "Off":
                        table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), very_light_red))
                    elif cell_value == "Not Set":
                        table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), very_light_yellow))
                    elif cell_value == "Not Set":
                        table_style.append(('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), very_light_yellow))
                
                # Apply special background color for special staff members (entire row except employee name and total hours columns)
                if is_special_staff:
                    # Apply special color to all schedule columns (1 to -2, excluding employee name and total hours)
                    table_style.append(('BACKGROUND', (1, row_idx), (-2, row_idx), special_staff_color))
                    # Also apply special color to employee name column for special staff
                    table_style.append(('BACKGROUND', (0, row_idx), (0, row_idx), special_staff_color))
                    # And apply special color to total hours column for special staff
                    table_style.append(('BACKGROUND', (-1, row_idx), (-1, row_idx), special_staff_color))
            
            table.setStyle(TableStyle(table_style))
            
            elements.append(table)
            
            elements.append(Spacer(1, 20))
            
            # Add legend
            legend_style = ParagraphStyle(
                'Legend',
                parent=getSampleStyleSheet()['Normal'],
                fontSize=9,
                leftIndent=0.5*inch
            )
            legend_text = """
            <b>Legend:</b><br/>
            • <b>Time:</b> Shows start-end times (e.g., 09:00-17:00)<br/>
            • <b>Off:</b> Staff member is not working this day<br/>
            • <b>Not Set:</b> Marked as working but times not specified<br/>
            • <b>Total Hours:</b> Sum of all working hours for the week<br/>
            • <b>Admin/Receptionist:</b> Staff with light purple background are admins or receptionists and listed at the end
            """
            legend = Paragraph(legend_text, legend_style)
            elements.append(legend)
            
            # Build PDF
            doc.build(elements)
            print(f"DEBUG: PDF generated successfully: {filename}")
            return filename
            
        except Exception as e:
            print(f"ERROR: Failed to generate PDF: {e}")
            import traceback
            traceback.print_exc()
            raise e 