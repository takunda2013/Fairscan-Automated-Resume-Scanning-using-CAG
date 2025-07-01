import time
import fitz  # PyMuPDF
import re
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from datetime import datetime
from scan.models import ProcessedResumeText

def extract_text(file_path):
    """Extract text from a PDF or DOCX file."""
    try:
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

# def clean_text(text):
#     """Remove whitespace and personal contact information from the text."""
#     # Remove excessive whitespace (new lines and spaces)
#     text = re.sub(r'\s+', ' ', text).strip()

#     # Remove phone numbers (common patterns)
#     text = re.sub(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', '[REDACTED]', text)

#     # Remove email addresses
#     text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED]', text)

#     # Remove URLs (including social media links)
#     text = re.sub(r'(http[s]?://|www\.)\S+', '[REDACTED]', text)

#     # Remove addresses (basic pattern for street addresses)
#     text = re.sub(r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Plaza|Pl|Court|Ct)\b', '[REDACTED]', text)

#     return text

def clean_text_with_tracking(text):
    """Remove whitespace and personal contact information from the text, tracking what was removed."""
    removed_items = {
        'phone_numbers': [],
        'emails': [],
        'urls': [],
        'addresses': []
    }
    
    original_text = text
    
    # Remove excessive whitespace (new lines and spaces)
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove phone numbers (common patterns)
    phone_matches = re.findall(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', text)
    if phone_matches:
        removed_items['phone_numbers'] = [''.join(match) for match in phone_matches]
    text = re.sub(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', '[REDACTED]', text)

    # Remove email addresses
    email_matches = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_matches:
        removed_items['emails'] = email_matches
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED]', text)

    # Remove URLs (including social media links)
    url_matches = re.findall(r'(http[s]?://|www\.)\S+', text)
    if url_matches:
        removed_items['urls'] = url_matches
    text = re.sub(r'(http[s]?://|www\.)\S+', '[REDACTED]', text)

    # Remove addresses (basic pattern for street addresses)
    address_matches = re.findall(r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Plaza|Pl|Court|Ct)\b', text)
    if address_matches:
        removed_items['addresses'] = address_matches
    text = re.sub(r'\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Plaza|Pl|Court|Ct)\b', '[REDACTED]', text)

    return text, removed_items

def create_prompt(resume_path):
    """Create a comprehensive prompt for the LLM."""
    resume_text = extract_text(resume_path)
    if resume_text:
        # clean_resume = clean_text(resume_text)
        clean_resume, identifiers =  clean_text_with_tracking(resume_text)

       
        return clean_resume, identifiers
    return "Failed to generate the prompt."



def increment_number(n):
    num = 0

    for _ in range(n):
        print(num )
        num += 1
        time.sleep(1)
    return num


# CREATE A FUNCTION THAT EXTRACTS JOB DESCRIPTIONS FROM THE ONTLOGY DOCUMENT

def generate_pdf(doc_id):
    try:
        # Get the document from the database
        document = ProcessedResumeText.objects.get(id=doc_id)

        # Create PDF content using ReportLab
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)

        # Page settings
        page_width, page_height = letter
        margin = 50
        usable_width = page_width - (2 * margin)
        
        y_position = page_height - margin
        line_height = 14
        
        def check_new_page():
            nonlocal y_position
            if y_position < margin + 50:  # Leave space at bottom
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y_position = page_height - margin
            return y_position
        
        def draw_text_line(text, font_size=10, bold=False, indent=0):
            nonlocal y_position
            check_new_page()
            
            font_name = "Helvetica-Bold" if bold else "Helvetica"
            pdf.setFont(font_name, font_size)
            pdf.drawString(margin + indent, y_position, text)
            y_position -= line_height
        
        def process_formatted_text(text):
            """Process the formatted evaluation text and render it properly"""
            nonlocal y_position
            
            lines = text.split('\n')  # Split by actual line breaks
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines but add small spacing
                if not line:
                    y_position -= 5
                    continue
                
                # Handle different formatting styles
                if '=====' in line:
                    # Skip separator lines
                    continue
                elif line.endswith(':') and not line.startswith(' '):
                    # Main headers
                    draw_text_line(line, font_size=11, bold=True)
                    y_position -= 3  # Extra space after headers
                elif line.startswith('    ') and line.strip().endswith(':'):
                    # Sub-headers (indented)
                    clean_line = line.strip()
                    draw_text_line(clean_line, font_size=10, bold=True, indent=20)
                elif line.startswith('        '):
                    # Sub-sub items (double indented)
                    clean_line = line.strip()
                    if clean_line.startswith('•'):
                        draw_text_line(clean_line, font_size=9, indent=40)
                    else:
                        draw_text_line(clean_line, font_size=9, indent=40)
                elif line.startswith('    '):
                    # Regular indented content
                    clean_line = line.strip()
                    if clean_line.startswith('•'):
                        draw_text_line(clean_line, font_size=9, indent=30)
                    else:
                        # Handle long lines that need wrapping
                        if len(clean_line) > 80:
                            words = clean_line.split()
                            current_line = ""
                            
                            for word in words:
                                test_line = current_line + " " + word if current_line else word
                                if len(test_line) <= 80:
                                    current_line = test_line
                                else:
                                    if current_line:
                                        draw_text_line(current_line, font_size=9, indent=30)
                                    current_line = word
                            
                            if current_line:
                                draw_text_line(current_line, font_size=9, indent=30)
                        else:
                            draw_text_line(clean_line, font_size=9, indent=30)
                else:
                    # Regular lines
                    if len(line) > 80:
                        # Wrap long lines
                        words = line.split()
                        current_line = ""
                        
                        for word in words:
                            test_line = current_line + " " + word if current_line else word
                            if len(test_line) <= 80:
                                current_line = test_line
                            else:
                                if current_line:
                                    draw_text_line(current_line, font_size=9)
                                current_line = word
                        
                        if current_line:
                            draw_text_line(current_line, font_size=9)
                    else:
                        draw_text_line(line, font_size=9)

        # Start with document header
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(margin, y_position, "RESUME EVALUATION REPORT")
        y_position -= 30

        # Add basic info at the top
        draw_text_line(f"Candidate Name: {document.resume_name}", font_size=12, bold=True)
        draw_text_line(f"Date Processed: {document.processed_date.strftime('%Y-%m-%d %H:%M:%S')}", font_size=10)
        draw_text_line(f"Overall Score: {document.processing_overall_score}", font_size=12, bold=True)
        draw_text_line(f"Processed By: {document.processed_by.username}", font_size=10)
        
        y_position -= 20  # Extra space before main content
        
        # Process the formatted evaluation text
        evaluation_text = str(document.score_evaluation)
        process_formatted_text(evaluation_text)

        # Save the PDF
        pdf.save()
        buffer.seek(0)

        print("DOC GENERATED")
        return buffer

    except ProcessedResumeText.DoesNotExist:
        print("Document not found")
        return None
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None
