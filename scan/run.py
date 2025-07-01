# debug_raw_text.py
import pymupdf
import re

def debug_raw_extraction():
    pdf_path = "C:/Fairscan/takundajori/mysite/media/document_templates/template.pdf"
    
    # Extract raw text
    doc = pymupdf.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    lines = text.split('\n')
    
    # Find job-related content
    job_context = []
    capture_context = False
    context_lines = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Start capturing context around job titles
        if line.startswith("Job Title:") or line.startswith("Title:"):
            capture_context = True
            context_lines = 20  # Capture next 20 lines
            job_context.append(f"\n=== JOB CONTEXT STARTING AT LINE {i+1} ===")
        
        if capture_context and context_lines > 0:
            job_context.append(f"Line {i+1:3d}: '{line}'")
            context_lines -= 1
            
            if context_lines == 0:
                capture_context = False
                job_context.append("=== END CONTEXT ===\n")
    
    # Print all job contexts
    for line in job_context:
        print(line)
    
    # Also look for description patterns
    print("\n" + "="*60)
    print("SEARCHING FOR DESCRIPTION PATTERNS:")
    print("="*60)
    
    for i, line in enumerate(lines):
        line = line.strip()
        if "description:" in line.lower():
            print(f"Line {i+1}: {line}")
            # Show next few lines
            for j in range(1, 4):
                if i+j < len(lines):
                    next_line = lines[i+j].strip()
                    if next_line:
                        print(f"Line {i+1+j}: {next_line}")
            print()

if __name__ == "__main__":
    debug_raw_extraction()