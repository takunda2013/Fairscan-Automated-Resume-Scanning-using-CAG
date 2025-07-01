# test_extraction_debug.py
import pymupdf
import re
from typing import Dict, List

class DebugOntologyConverter:
    def __init__(self):
        self.sections = {
            'COMPANY PROFILE': '',
            'AIM': '',
            'OBJECTIVES': [],
            'COMPANY VALUES': [],
            'WORK STYLE': [],
            'COMMUNICATION SKILLS': [],
            'JOB DESCRIPTIONS': [],
            'BIAS MITIGATING STATEMENTS': []
        }

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            print(f"Opening PDF: {pdf_path}")
            doc = pymupdf.open(pdf_path)
            text = ""
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                print(f"Page {page_num + 1} extracted {len(page_text)} characters")
                text += page_text
            doc.close()
            print(f"Total text extracted: {len(text)} characters")
            print("First 500 characters:")
            print("=" * 50)
            print(text[:500])
            print("=" * 50)
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def debug_parse_lines(self, text: str):
        """Debug function to show what lines are being processed"""
        lines = text.split('\n')
        print(f"\nTotal lines: {len(lines)}")
        print("\nFirst 20 lines:")
        print("-" * 50)
        
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            print(f"Line {i+1:2d}: '{line}'")
            
            # Check for job title
            if line.startswith("Job Title:") or line.startswith("Title:"):
                print(f"    -> JOB TITLE FOUND!")
            
            # Check for description
            if line.startswith("Description:"):
                print(f"    -> DESCRIPTION FOUND!")
            
            # Check for hiring criteria
            if line.upper() == "HIRING CRITERIA":
                print(f"    -> HIRING CRITERIA FOUND!")
        
        print("-" * 50)
        
        # Look for job-related content throughout the document
        job_lines = []
        desc_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("Job Title:") or line.startswith("Title:"):
                job_lines.append((i+1, line))
            if line.startswith("Description:"):
                desc_lines.append((i+1, line))
        
        print(f"\nFound {len(job_lines)} job title lines:")
        for line_num, content in job_lines:
            print(f"  Line {line_num}: {content}")
        
        print(f"\nFound {len(desc_lines)} description lines:")
        for line_num, content in desc_lines:
            print(f"  Line {line_num}: {content}")

    def simple_test_parse(self, text: str):
        """Simple parsing test to see what's happening"""
        lines = text.split('\n')
        
        print("\nSimple parsing test:")
        print("=" * 50)
        
        in_job_section = False
        current_job_title = None
        current_description = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Look for job titles
            if line.startswith("Job Title:") or line.startswith("Title:"):
                current_job_title = line.split(":", 1)[1].strip()
                in_job_section = True
                print(f"FOUND JOB: {current_job_title}")
                continue
            
            # Look for descriptions
            if in_job_section and line.startswith("Description:"):
                current_description = line.split(":", 1)[1].strip()
                print(f"FOUND DESC: {current_description}")
                
                # Look ahead for continuation
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith(("HIRING", "Job Title:", "Description:", "Importance:", "Keywords:", "Weight:")):
                        current_description += " " + next_line
                        print(f"CONTINUING DESC: {next_line}")
                    else:
                        break
                
                print(f"FINAL DESC: {current_description}")
                continue
            
            # Reset on new sections
            if line.upper() in ["HIRING CRITERIA", "--- DIVIDER ---"] or re.match(r'^[-=*_]{5,}$', line):
                in_job_section = False
                current_job_title = None
                current_description = None

def main():
    print("Starting debug extraction...")
    
    # Test with your file
    converter = DebugOntologyConverter()
    
    # Try to detect file type
    pdf_path = "C:/Fairscan/takundajori/mysite/media/document_templates/template.pdf"
    docx_path = "C:/Fairscan/takundajori/mysite/media/document_templates/template.docx"
    
    # Check which file exists
    import os
    if os.path.exists(pdf_path):
        print(f"Found PDF file: {pdf_path}")
        text = converter.extract_text_from_pdf(docx_path)
    elif os.path.exists(docx_path):
        print(f"Found DOCX file: {docx_path}")
        print("ERROR: This script only handles PDF files. Convert DOCX to PDF first.")
        return
    else:
        print("No template file found!")
        print(f"Looked for: {pdf_path}")
        print(f"Looked for: {docx_path}")
        return
    
    if text:
        converter.debug_parse_lines(text)
        converter.simple_test_parse(text)
    else:
        print("No text extracted!")

if __name__ == "__main__":
    main()