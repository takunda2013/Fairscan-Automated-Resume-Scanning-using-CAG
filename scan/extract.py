import pymupdf
import re
from typing import Dict, List

class EnhancedOntologyConverter:
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
            doc = pymupdf.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def _is_criterion_title(self, line: str) -> bool:
        """Check if line is a criterion title - generic approach for any field"""
        # Skip empty lines
        if not line or not line.strip():
            return False
        
        # Skip lines that are clearly field definitions
        if any(x in line.lower() for x in ['description:', 'importance:', 'keywords:', 'weight:']):
            return False
        
        # Skip lines that look like dividers or sections
        if line.upper() in ['HIRING CRITERIA', '--- DIVIDER ---'] or re.match(r'^[-=*_]{3,}', line):
            return False
        
        # Skip lines that are clearly job-related headers
        if line.lower().startswith('job title:') or line.lower().startswith('title:'):
            return False
        
        # Skip lines that start with lowercase (likely descriptions)
        if line[0].islower():
            return False
        
        # Skip lines that look like full sentences (contain periods or end punctuation)
        if re.search(r'[.!?]', line):
            return False
        
        # Skip lines that are too long to be titles (likely descriptions)
        if len(line.split()) > 8:
            return False
        
        # Skip lines with common description starter words
        description_starters = [
            'demonstrated', 'experience in', 'ability to', 'proficiency in', 
            'skills in', 'knowledge of', 'understanding of', 'familiarity with',
            'capable of', 'responsible for', 'lead', 'develop', 'manage', 'ensure',
            'create', 'implement', 'maintain', 'support', 'analyze', 'design'
        ]
        
        line_lower = line.lower()
        if any(starter in line_lower for starter in description_starters):
            return False
        
        # Skip lines with too many common connecting words (indicates descriptions)
        connecting_words = ['the', 'and', 'with', 'for', 'to', 'of', 'in', 'on', 'at', 'by', 'from']
        word_count = len(line.split())
        connecting_count = sum(1 for word in line.lower().split() if word in connecting_words)
        
        # If more than 30% of words are connecting words, it's likely a description
        if word_count > 2 and (connecting_count / word_count) > 0.3:
            return False
        
        # Positive indicators for criterion titles:
        # - Starts with uppercase letter
        # - Reasonable length (1-8 words)
        # - No sentence-ending punctuation
        # - Title case or all caps words
        return (line[0].isupper() and 
                1 <= len(line.split()) <= 8 and
                not line.endswith((':', ';', ',')))

    def _parse_criterion_line(self, line: str, criterion: Dict):
        """Parse a line of criterion details into the criterion dictionary"""
        # First check if this is the start of a new field
        field_match = re.match(
            r'(?i)(description|importance|keywords|weight)\s*:\s*(.*)',
            line
        )
        
        if field_match:
            key = field_match.group(1).lower()
            value = field_match.group(2).strip()
            
            if key == "description":
                criterion["description"] = value
                criterion["_current_field"] = "description"
            elif key == "importance":
                criterion["importance"] = value
                criterion["_current_field"] = "importance"
            elif key == "keywords":
                # Handle both comma-separated and space-separated keywords
                if ',' in value:
                    criterion["keywords"] = [k.strip() for k in value.split(',') if k.strip()]
                else:
                    criterion["keywords"] = [k.strip() for k in value.split() if k.strip()]
                criterion["_current_field"] = "keywords"
            elif key == "weight":
                try:
                    criterion["weight"] = float(value)
                except ValueError:
                    criterion["weight"] = value
                criterion["_current_field"] = "weight"
        else:
            # This is a continuation line - append to the current field
            current_field = criterion.get("_current_field")
            
            # If no current field is set, we need to determine what this line is
            if not current_field:
                # Check if this is clearly an importance value
                if line.lower().strip() in ['mandatory', 'important', 'required', 'optional', 'preferred', 'nice to have']:
                    criterion["importance"] = line.strip()
                    criterion["_current_field"] = "importance"
                    return
                
                # Check if this is clearly a weight value (number)
                if re.match(r'^\d*\.?\d+$', line.strip()):
                    try:
                        criterion["weight"] = float(line.strip())
                        criterion["_current_field"] = "weight"
                        return
                    except ValueError:
                        pass
                
                # Check if this looks like keywords (contains commas or tech terms)
                if (',' in line or 
                    any(tech_indicator in line.lower() for tech_indicator in 
                        ['java', 'python', 'javascript', 'html', 'css', 'sql', 'api', 'framework', 
                        'testing', 'design', 'management', 'leadership', 'communication'])):
                    if not criterion.get("keywords"):
                        criterion["keywords"] = []
                    if ',' in line:
                        new_keywords = [k.strip() for k in line.split(',') if k.strip()]
                    else:
                        new_keywords = [k.strip() for k in line.split() if k.strip()]
                    criterion["keywords"].extend(new_keywords)
                    criterion["_current_field"] = "keywords"
                    return
                
                # Default: treat as description if it's substantial text
                if len(line.strip()) > 0:
                    criterion["_current_field"] = "description"
                    current_field = "description"
            
            # Handle continuation based on current field
            if current_field == "description":
                if criterion.get("description"):
                    criterion["description"] += " " + line.strip()
                else:
                    criterion["description"] = line.strip()
            elif current_field == "importance":
                if criterion.get("importance"):
                    criterion["importance"] += " " + line.strip()
                else:
                    criterion["importance"] = line.strip()
            elif current_field == "keywords":
                # For keywords, add new words to the list
                if not criterion.get("keywords"):
                    criterion["keywords"] = []
                if ',' in line:
                    new_keywords = [k.strip() for k in line.split(',') if k.strip()]
                else:
                    new_keywords = [k.strip() for k in line.split() if k.strip()]
                criterion["keywords"].extend(new_keywords)

    def parse_template_structure(self, text: str) -> Dict:
        """Parse the PDF text into structured ontology sections"""
        lines = text.split('\n')
        lines = self._merge_broken_lines(lines)
        current_section = None
        content_buffer = []

        section_patterns = {
            r'COMPANY PROFILE': 'COMPANY PROFILE',
            r'AIM': 'AIM',
            r'OBJECTIVES': 'OBJECTIVES',
            r'COMPANY VALUES': 'COMPANY VALUES',
            r'WORK STYLE': 'WORK STYLE',
            r'COMMUNICATION SKILLS': 'COMMUNICATION SKILLS',
            r'BIAS MITIGATING STATEMENTS': 'BIAS MITIGATING STATEMENTS'
        }

        job_mode = False
        current_job = None
        current_criteria = None
        job_description_continues = False
        # Add debug flag
        debug_mode = True

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if debug_mode:
                print(f"Processing line: '{line[:50]}...' | Job mode: {job_mode} | Job desc continues: {job_description_continues}")

            # SECTION HEADERS
            section_found = False
            for pattern, section_name in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Save any pending job and criteria before switching sections
                    if current_criteria and current_job:
                        if "_current_field" in current_criteria:
                            del current_criteria["_current_field"]
                        current_job["criteria"].append(current_criteria)
                        current_criteria = None
                    if current_job:
                        self.sections["JOB DESCRIPTIONS"].append(current_job)
                        current_job = None
                    
                    if current_section and content_buffer:
                        self._save_section_content(current_section, content_buffer)
                    current_section = section_name
                    content_buffer = []
                    job_mode = False
                    job_description_continues = False
                    section_found = True
                    if debug_mode:
                        print(f"  -> Found section: {section_name}")
                    break

            if section_found:
                continue

            # JOB TITLE DETECTION
            if line.startswith("Job Title:") or line.startswith("Title:"):
                # Save previous job if exists
                if current_criteria and current_job:
                    if "_current_field" in current_criteria:
                        del current_criteria["_current_field"]
                    current_job["criteria"].append(current_criteria)
                    current_criteria = None
                if current_job:
                    self.sections["JOB DESCRIPTIONS"].append(current_job)
                
                job_title = line.split(":", 1)[1].strip()
                current_job = {
                    "title": job_title,
                    "description": "",
                    "criteria": [],
                    "divider": None
                }
                job_mode = True
                job_description_continues = False
                current_criteria = None
                if debug_mode:
                    print(f"  -> Found job title: {job_title}")
                continue

            # JOB DESCRIPTION - Fixed logic
            if job_mode and current_job and line.startswith("Description:"):
                description_text = line.split(":", 1)[1].strip()
                current_job["description"] = description_text
                job_description_continues = True
                if debug_mode:
                    print(f"  -> Found job description start: {description_text[:30]}...")
                continue

            # HIRING CRITERIA SECTION
            if job_mode and current_job and line.upper() == "HIRING CRITERIA":
                job_description_continues = False
                if debug_mode:
                    print(f"  -> Found HIRING CRITERIA section")
                continue

            # DIVIDER DETECTION
            if (line == "--- DIVIDER ---" or 
                re.match(r'^={5,}\s*Page\s*\d+\s*={5,}$', line) or
                re.match(r'^[-=*_]{5,}$', line)):
                # Save current criteria before ending job
                if current_criteria and current_job:
                    if "_current_field" in current_criteria:
                        del current_criteria["_current_field"]
                    current_job["criteria"].append(current_criteria)
                    current_criteria = None
                if current_job:
                    current_job["divider"] = line
                    self.sections["JOB DESCRIPTIONS"].append(current_job)
                    if debug_mode:
                        print(f"  -> Saved job with description: '{current_job['description'][:50]}...'")
                    current_job = None
                job_mode = False
                job_description_continues = False
                continue

            # HIRING CRITERIA PARSING
            if job_mode and current_job:
                # Check if we're continuing a job description - FIXED LOGIC
                if (job_description_continues and 
                    not line.startswith(('Description:', 'Importance:', 'Keywords:', 'Weight:')) and 
                    not self._is_criterion_title(line) and
                    line.upper() != "HIRING CRITERIA"):
                    # This line continues the job description
                    if current_job["description"]:
                        current_job["description"] += " " + line.strip()
                    else:
                        current_job["description"] = line.strip()
                    if debug_mode:
                        print(f"  -> Continuing job description: {line[:30]}...")
                    continue
                
                # Check if this is a new criterion title
                if self._is_criterion_title(line):
                    # Save previous criteria
                    if current_criteria:
                        if "_current_field" in current_criteria:
                            del current_criteria["_current_field"]
                        current_job["criteria"].append(current_criteria)
                    
                    # Create new criteria
                    current_criteria = {
                        "name": line.strip(),
                        "description": "",
                        "importance": "",
                        "keywords": [],
                        "weight": None,
                        "_current_field": None
                    }
                    job_description_continues = False
                    if debug_mode:
                        print(f"  -> Found criterion title: {line}")
                    continue

                # Parse criterion details
                if current_criteria:
                    self._parse_criterion_line(line, current_criteria)
                    job_description_continues = False
                    continue

            # OTHER SECTION CONTENT
            if current_section and not job_mode and not self._is_template_instruction(line):
                content_buffer.append(line)

        # Save any remaining content
        if current_section and content_buffer:
            self._save_section_content(current_section, content_buffer)
        
        # Save final job and criteria
        if current_criteria and current_job:
            if "_current_field" in current_criteria:
                del current_criteria["_current_field"]
            current_job["criteria"].append(current_criteria)
        if current_job:
            self.sections["JOB DESCRIPTIONS"].append(current_job)
            if debug_mode:
                print(f"  -> Final job saved with description: '{current_job['description'][:50]}...'")

        return self.sections

    def create_complete_ontology(self) -> str:
        """Generate the complete ontology with proper dividers"""
        ontology = "# FAIRSCAN ORGANIZATIONAL ONTOLOGY\n\n"
        
        sections_order = [
            'COMPANY PROFILE',
            'AIM',
            'OBJECTIVES',
            'COMPANY VALUES',
            'WORK STYLE',
            'COMMUNICATION SKILLS',
            'JOB DESCRIPTIONS',
            'BIAS MITIGATING STATEMENTS'
        ]
        
        for section in sections_order:
            content = self.sections.get(section)
            if not content:
                continue
                
            ontology += f"## {section}\n"
            
            if isinstance(content, list):
                for idx, item in enumerate(content):
                    if isinstance(item, dict):  # Job description
                        # Add job content
                        ontology += f"### Job Title: {item.get('title', '')}\n"
                        # FIXED: Always show description if it exists
                        if item.get('description') and item.get('description').strip():
                            ontology += f"Description: {item.get('description', '')}\n\n"
                        else:
                            ontology += "Description: [No description found]\n\n"
                        
                        # Add hiring criteria
                        if item.get('criteria'):
                            ontology += "#### HIRING CRITERIA\n\n"
                            for criterion in item['criteria']:
                                ontology += f"##### {criterion.get('name', '')}\n"
                                if criterion.get('description'):
                                    ontology += f"Description: {criterion.get('description', '')}\n"
                                if criterion.get('importance'):
                                    ontology += f"Importance: {criterion.get('importance', '')}\n"
                                if criterion.get('keywords'):
                                    ontology += f"Keywords: {', '.join(criterion.get('keywords', []))}\n"
                                if criterion.get('weight') is not None:
                                    ontology += f"Weight: {criterion.get('weight', '')}\n"
                                ontology += "\n"
                        
                        # Add divider if it exists and not last item
                        if item.get('divider') and idx < len(content) - 1:
                            ontology += f"### {item['divider']}\n\n"
                            
                    else:  # Regular list item
                        ontology += f"- {item}\n"
                ontology += "\n"
            else:  # Text content
                ontology += f"{content}\n\n"
        
        return ontology.strip()

    def _merge_broken_lines(self, lines: List[str]) -> List[str]:
        """Merge lines split mid-sentence (PDF artifacts)"""
        merged = []
        buffer = ""
        for line in lines:
            line = line.strip()
            if not line:
                if buffer:
                    merged.append(buffer)
                    buffer = ""
                continue
                
            # Check if line ends with punctuation or is likely a new item
            if line.endswith((".", ":", "!", "?")) or line.startswith(("-", "•", "*")) or len(line) < 60:
                if buffer:
                    merged.append(buffer)
                    buffer = ""
                merged.append(line)
            else:
                buffer += " " + line if buffer else line
        if buffer:
            merged.append(buffer)
        return merged

    def _is_template_instruction(self, line: str) -> bool:
        """Check if line is template instruction text to skip"""
        skip_patterns = [
            r'^e\.g\.?',
            r'^E\.g\.?',
            r'briefly describe',
            r'main company aims',
            r'company objectives as a list',
            r'list of jobs available',
            r'note that these are',
            r'for each criterion',
            r'here you can mention',
            r'if applicable',
            r'\(mandatory, important or required\)'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False

    def _save_section_content(self, section: str, content: List[str]):
        """Save content to appropriate section"""
        if section in ['OBJECTIVES', 'COMPANY VALUES', 'WORK STYLE', 
                     'COMMUNICATION SKILLS', 'BIAS MITIGATING STATEMENTS']:
            cleaned_content = []
            for item in content:
                if item and item.strip() and not item.strip() in ['-', '•', '*']:
                    cleaned_item = re.sub(r'^[-•*]\s*', '', item.strip())
                    if cleaned_item:
                        cleaned_content.append(cleaned_item)
            self.sections[section].extend(cleaned_content)
        else:
            cleaned_text = ' '.join([c.strip() for c in content if c.strip()])
            if section == 'COMPANY PROFILE':
                cleaned_text = re.sub(r'Company Name:\s*[^:]*Company Name:\s*', 'Company Name: ', cleaned_text)
                cleaned_text = re.sub(r'Description:\s*[^:]*Description:\s*', 'Description: ', cleaned_text)
            self.sections[section] = cleaned_text

    def convert_pdf_to_ontology(self, pdf_path: str, output_path: str = "ontology_output.txt") -> bool:
        """Main conversion function"""
        print(f"Extracting text from {pdf_path}...")
        pdf_text = self.extract_text_from_pdf(pdf_path)
        if not pdf_text:
            print("Failed to extract text from PDF")
            return False
            
        print("Parsing template structure...")
        self.parse_template_structure(pdf_text)
        
        print("Creating ontology structure...")
        ontology_content = self.create_complete_ontology()
        
        print(f"Saving to {output_path}...")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ontology_content)
            print("Conversion successful!")
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

