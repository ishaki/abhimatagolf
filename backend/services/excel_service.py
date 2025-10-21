from typing import List, Dict, Any, Optional
import pandas as pd
from io import BytesIO
from sqlmodel import Session, select
from models.participant import Participant
from models.scorecard import Scorecard
from models.event import Event
from models.event_division import EventDivision
from models.course import Course, Hole
from schemas.participant import ParticipantResponse
from schemas.scorecard import ScorecardResponse
from core.app_logging import logger
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.worksheet import Worksheet


class ExcelService:
    def __init__(self, session: Session):
        self.session = session

    def export_participants_to_excel(self, event_id: int) -> BytesIO:
        """Export participants for an event to Excel format."""
        try:
            # Get event information
            event = self.session.get(Event, event_id)
            if not event:
                raise ValueError(f"Event with ID {event_id} not found")

            # Get participants with their division information
            participants = self.session.exec(
                select(Participant, EventDivision)
                .join(EventDivision, Participant.division_id == EventDivision.id, isouter=True)
                .where(Participant.event_id == event_id)
            ).all()

            # Prepare data for Excel
            data = []
            for participant, division in participants:
                data.append({
                    'Name': participant.name,
                    'Handicap': participant.declared_handicap,
                    'Division': division.name if division else participant.division or 'N/A',
                    'Division ID': participant.division_id or '',
                    'Registered At': participant.registered_at.strftime('%Y-%m-%d %H:%M') if participant.registered_at else '',
                })

            # Create DataFrame
            df = pd.DataFrame(data)

            # Create Excel file in memory
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Write participants data
                df.to_excel(writer, sheet_name='Participants', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Participants']
                
                # Apply formatting
                self._format_participants_sheet(worksheet, event.name)
                
                # Add summary sheet
                self._add_summary_sheet(workbook, event, participants)

            output.seek(0)
            logger.info(f"Successfully exported {len(participants)} participants for event {event_id}")
            return output

        except Exception as e:
            logger.error(f"Error exporting participants to Excel: {str(e)}")
            raise

    def export_scorecards_to_excel(self, event_id: int) -> BytesIO:
        """Export scorecards for an event to Excel format."""
        try:
            # Get event information
            event = self.session.get(Event, event_id)
            if not event:
                raise ValueError(f"Event with ID {event_id} not found")

            # Get course information
            course = self.session.get(Course, event.course_id)
            if not course:
                raise ValueError(f"Course not found for event {event_id}")

            # Get holes for the course
            holes = self.session.exec(
                select(Hole).where(Hole.course_id == course.id).order_by(Hole.hole_number)
            ).all()

            # Get participants with their scorecards
            participants = self.session.exec(
                select(Participant, EventDivision)
                .join(EventDivision, Participant.division_id == EventDivision.id, isouter=True)
                .where(Participant.event_id == event_id)
            ).all()

            # Create Excel file in memory
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Create scorecard data
                scorecard_data = []
                
                for participant, division in participants:
                    # Get scorecards for this participant
                    scorecards = self.session.exec(
                        select(Scorecard, Hole)
                        .join(Hole, Scorecard.hole_id == Hole.id)
                        .where(Scorecard.participant_id == participant.id)
                        .order_by(Hole.hole_number)
                    ).all()

                    # Create a row for this participant
                    row = {
                        'Player': participant.name,
                        'Division': division.name if division else participant.division or 'N/A',
                        'Handicap': participant.declared_handicap,
                    }

                    # Add hole scores
                    hole_scores = {}
                    total_gross = 0
                    total_par = 0
                    
                    for scorecard, hole in scorecards:
                        hole_scores[hole.hole_number] = scorecard.score
                        if scorecard.score is not None:
                            total_gross += scorecard.score
                            total_par += hole.par

                    # Add hole columns
                    for hole in holes:
                        row[f'Hole {hole.hole_number}'] = hole_scores.get(hole.hole_number, '')
                        row[f'Par {hole.hole_number}'] = hole.par

                    # Add totals
                    row['Total Gross'] = total_gross if total_gross > 0 else ''
                    row['Total Par'] = total_par
                    row['Net Score'] = total_gross - participant.declared_handicap if total_gross > 0 else ''
                    row['To Par'] = total_gross - total_par if total_gross > 0 else ''

                    scorecard_data.append(row)

                # Create DataFrame
                df = pd.DataFrame(scorecard_data)

                # Write to Excel
                df.to_excel(writer, sheet_name='Scorecards', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Scorecards']
                
                # Apply formatting
                self._format_scorecards_sheet(worksheet, event.name, course.name)
                
                # Add summary sheet
                self._add_scorecard_summary_sheet(workbook, event, participants, holes)

            output.seek(0)
            logger.info(f"Successfully exported scorecards for {len(participants)} participants for event {event_id}")
            return output

        except Exception as e:
            logger.error(f"Error exporting scorecards to Excel: {str(e)}")
            raise

    def generate_participant_template(self) -> BytesIO:
        """Generate Excel template for participant upload."""
        try:
            # Create template data
            template_data = [
                {
                    'name': 'John Doe',
                    'declared_handicap': 12,
                    'division': 'Championship',
                    'division_id': 1
                },
                {
                    'name': 'Jane Smith',
                    'declared_handicap': 8,
                    'division': 'Ladies',
                    'division_id': 2
                },
                {
                    'name': 'Bob Johnson',
                    'declared_handicap': 18,
                    'division': 'Senior',
                    'division_id': 3
                }
            ]

            df = pd.DataFrame(template_data)

            # Create Excel file in memory
            output = BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Write template data
                df.to_excel(writer, sheet_name='Participants', index=False)
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Participants']
                
                # Apply formatting
                self._format_template_sheet(worksheet)
                
                # Add instructions sheet
                self._add_instructions_sheet(workbook)

            output.seek(0)
            logger.info("Successfully generated participant template")
            return output

        except Exception as e:
            logger.error(f"Error generating participant template: {str(e)}")
            raise

    def _format_participants_sheet(self, worksheet: Worksheet, event_name: str):
        """Apply formatting to participants sheet."""
        # Header formatting
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # Add title
        worksheet.insert_rows(1)
        worksheet.merge_cells('A1:E1')
        title_cell = worksheet['A1']
        title_cell.value = f"Participants - {event_name}"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal="center")

    def _format_scorecards_sheet(self, worksheet: Worksheet, event_name: str, course_name: str):
        """Apply formatting to scorecards sheet."""
        # Header formatting
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 15)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # Add title
        worksheet.insert_rows(1)
        worksheet.merge_cells('A1:Z1')
        title_cell = worksheet['A1']
        title_cell.value = f"Scorecards - {event_name} ({course_name})"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal="center")

    def _format_template_sheet(self, worksheet: Worksheet):
        """Apply formatting to template sheet."""
        # Header formatting
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # Add title
        worksheet.insert_rows(1)
        worksheet.merge_cells('A1:D1')
        title_cell = worksheet['A1']
        title_cell.value = "Participant Upload Template"
        title_cell.font = Font(bold=True, size=16)
        title_cell.alignment = Alignment(horizontal="center")

    def _add_summary_sheet(self, workbook, event: Event, participants: List):
        """Add summary sheet to participants export."""
        ws = workbook.create_sheet("Summary")
        
        # Add summary data
        summary_data = [
            ["Event Name", event.name],
            ["Event Date", event.start_date.strftime('%Y-%m-%d') if event.start_date else 'N/A'],
            ["Course", event.course.name if event.course else 'N/A'],
            ["Total Participants", len(participants)],
            ["Export Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        for i, (label, value) in enumerate(summary_data, 1):
            ws[f'A{i}'] = label
            ws[f'B{i}'] = value
            ws[f'A{i}'].font = Font(bold=True)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _add_scorecard_summary_sheet(self, workbook, event: Event, participants: List, holes: List):
        """Add summary sheet to scorecards export."""
        ws = workbook.create_sheet("Summary")
        
        # Add summary data
        summary_data = [
            ["Event Name", event.name],
            ["Event Date", event.start_date.strftime('%Y-%m-%d') if event.start_date else 'N/A'],
            ["Course", event.course.name if event.course else 'N/A'],
            ["Total Participants", len(participants)],
            ["Total Holes", len(holes)],
            ["Export Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        for i, (label, value) in enumerate(summary_data, 1):
            ws[f'A{i}'] = label
            ws[f'B{i}'] = value
            ws[f'A{i}'].font = Font(bold=True)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    def _add_instructions_sheet(self, workbook):
        """Add instructions sheet to template."""
        ws = workbook.create_sheet("Instructions")
        
        instructions = [
            "Participant Upload Template Instructions",
            "",
            "Required Columns:",
            "• name: Participant's full name (required)",
            "• declared_handicap: Golf handicap (0-54, optional, default: 0)",
            "• division: Division name (optional)",
            "• division_id: Division ID from event divisions (optional)",
            "",
            "Instructions:",
            "1. Fill in participant information in the 'Participants' sheet",
            "2. Remove example rows before uploading",
            "3. Ensure names are unique within the event",
            "4. Handicap values must be between 0 and 54",
            "5. Division ID must reference an existing event division",
            "",
            "File Format:",
            "• Save as Excel (.xlsx) format",
            "• Do not modify column headers",
            "• Do not add extra columns",
            "",
            "Validation:",
            "• Names cannot be empty",
            "• Handicaps must be numeric",
            "• Division IDs must be valid integers",
            "",
            "For support, contact the tournament administrator."
        ]
        
        for i, instruction in enumerate(instructions, 1):
            ws[f'A{i}'] = instruction
            if i == 1:  # Title
                ws[f'A{i}'].font = Font(bold=True, size=14)
            elif instruction.startswith("•"):  # Bullet points
                ws[f'A{i}'].font = Font(bold=True)
        
        # Auto-adjust column width
        ws.column_dimensions['A'].width = 80
