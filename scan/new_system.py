# # ontology_builder.py
# import pymupdf
# import re
# import json
# from typing import Dict, List, Tuple, Optional
# from dataclasses import dataclass, asdict
# from collections import defaultdict

# @dataclass
# class HiringCriteria:
#     description: str
#     importance: str  # mandatory, important, required
#     keywords: List[str]
#     weight: float

# @dataclass
# class JobDescription:
#     title: str
#     description: str
#     hiring_criteria: Dict[str, HiringCriteria]

# @dataclass
# class CompanyOntology:
#     company_name: str = ""
#     company_description: str = ""
#     aim: str = ""
#     objectives: List[str] = None
#     values: List[str] = None
#     work_style: List[str] = None
#     communication_skills: List[str] = None
#     job_descriptions: List[JobDescription] = None
#     bias_mitigating_statements: List[str] = None
    
#     def __post_init__(self):
#         if self.objectives is None:
#             self.objectives = []
#         if self.values is None:
#             self.values = []
#         if self.work_style is None:
#             self.work_style = []
#         if self.communication_skills is None:
#             self.communication_skills = []
#         if self.job_descriptions is None:
#             self.job_descriptions = []
#         if self.bias_mitigating_statements is None:
#             self.bias_mitigating_statements = []

# class OntologyExtractor:
#     def __init__(self):
#         # Define patterns for different sections
#         self.section_patterns = {
#             'company_name': [
#                 r'company\s*name\s*:?\s*(.+)',
#                 r'organization\s*name\s*:?\s*(.+)',
#                 r'firm\s*name\s*:?\s*(.+)'
#             ],
#             'company_description': [
#                 r'company\s*description\s*:?\s*(.+)',
#                 r'about\s*us\s*:?\s*(.+)',
#                 r'overview\s*:?\s*(.+)'
#             ],
#             'aim': [
#                 r'aim\s*:?\s*(.+)',
#                 r'mission\s*:?\s*(.+)',
#                 r'purpose\s*:?\s*(.+)'
#             ],
#             'objectives': [
#                 r'objectives?\s*:?',
#                 r'goals?\s*:?',
#                 r'targets?\s*:?'
#             ],
#             'values': [
#                 r'values?\s*:?',
#                 r'principles?\s*:?',
#                 r'core\s*values?\s*:?'
#             ],
#             'work_style': [
#                 r'work\s*style\s*:?',
#                 r'working\s*style\s*:?',
#                 r'culture\s*:?'
#             ],
#             'communication_skills': [
#                 r'communication\s*skills?\s*:?',
#                 r'language\s*requirements?\s*:?',
#                 r'languages?\s*:?'
#             ]
#         }
        
#         # Job-related patterns
#         self.job_patterns = {
#             'job_title': [
#                 r'job\s*title\s*:?\s*(.+)',
#                 r'position\s*:?\s*(.+)',
#                 r'role\s*:?\s*(.+)',
#                 r'title\s*:?\s*(.+)'
#             ],
#             'job_description': [
#                 r'job\s*description\s*:?\s*(.+)',
#                 r'description\s*:?\s*(.+)',
#                 r'responsibilities\s*:?\s*(.+)'
#             ]
#         }
        
#         # Hiring criteria patterns
#         self.criteria_patterns = {
#             'technical_proficiency': ['technical', 'programming', 'coding', 'languages', 'frameworks'],
#             'experience': ['experience', 'years', 'background', 'history'],
#             'education': ['education', 'degree', 'qualification', 'certification'],
#             'skills': ['skills', 'abilities', 'competencies'],
#             'leadership': ['leadership', 'management', 'mentoring', 'team lead'],
#             'communication': ['communication', 'presentation', 'writing'],
#             'problem_solving': ['problem solving', 'analytical', 'debugging'],
#             'quality': ['quality', 'testing', 'best practices']
#         }
        
#         # Importance keywords
#         self.importance_keywords = {
#             'mandatory': ['mandatory', 'required', 'must have', 'essential'],
#             'important': ['important', 'preferred', 'desirable', 'valuable'],
#             'required': ['needed', 'necessary', 'should have']
#         }

#     def extract_from_pdf(self, pdf_path: str) -> CompanyOntology:
#         """Extract text from PDF and build ontology"""
#         # Extract raw text
#         doc = pymupdf.open(pdf_path)
#         text = ""
#         for page in doc:
#             text += page.get_text()
#         doc.close()
        
#         lines = [line.strip() for line in text.split('\n') if line.strip()]
        
#         # Build ontology
#         ontology = CompanyOntology()
        
#         # Extract basic company information
#         self._extract_basic_info(lines, ontology)
        
#         # Extract lists (objectives, values, etc.)
#         self._extract_lists(lines, ontology)
        
#         # Extract job descriptions
#         self._extract_job_descriptions(lines, ontology)
        
#         # Extract bias mitigation statements
#         self._extract_bias_statements(lines, ontology)
        
#         return ontology
    
#     def _extract_basic_info(self, lines: List[str], ontology: CompanyOntology):
#         """Extract basic company information"""
#         for i, line in enumerate(lines):
#             line_lower = line.lower()
            
#             # Company name
#             for pattern in self.section_patterns['company_name']:
#                 match = re.search(pattern, line_lower)
#                 if match and not ontology.company_name:
#                     ontology.company_name = match.group(1).strip()
#                     break
            
#             # Company description
#             for pattern in self.section_patterns['company_description']:
#                 match = re.search(pattern, line_lower)
#                 if match and not ontology.company_description:
#                     # Get description from this line and potentially next lines
#                     desc = match.group(1).strip()
#                     if len(desc) < 20 and i + 1 < len(lines):  # Short description, check next line
#                         desc += " " + lines[i + 1]
#                     ontology.company_description = desc
#                     break
            
#             # Aim/Mission
#             for pattern in self.section_patterns['aim']:
#                 match = re.search(pattern, line_lower)
#                 if match and not ontology.aim:
#                     aim = match.group(1).strip()
#                     if len(aim) < 20 and i + 1 < len(lines):  # Short aim, check next line
#                         aim += " " + lines[i + 1]
#                     ontology.aim = aim
#                     break
    
#     def _extract_lists(self, lines: List[str], ontology: CompanyOntology):
#         """Extract list-based sections like objectives, values, etc."""
#         current_section = None
        
#         for i, line in enumerate(lines):
#             line_lower = line.lower()
#             line_clean = line.strip()
            
#             # Check if this line starts a new section
#             for section_name, patterns in self.section_patterns.items():
#                 if section_name in ['company_name', 'company_description', 'aim']:
#                     continue  # Already handled
                    
#                 for pattern in patterns:
#                     if re.search(pattern, line_lower):
#                         current_section = section_name
#                         break
#                 if current_section:
#                     break
            
#             # If we're in a section, collect items
#             if current_section and line_clean:
#                 # Skip the header line
#                 if any(re.search(pattern, line_lower) for pattern in self.section_patterns[current_section]):
#                     continue
                
#                 # Check if this looks like a list item
#                 if (line_clean.startswith('-') or 
#                     line_clean.startswith('•') or 
#                     line_clean.startswith('*') or
#                     re.match(r'^\d+\.', line_clean) or
#                     (len(line_clean) < 100 and not line_clean.endswith(':'))):
                    
#                     item = re.sub(r'^[-•*\d\.\s]+', '', line_clean).strip()
#                     if item:
#                         if current_section == 'objectives':
#                             ontology.objectives.append(item)
#                         elif current_section == 'values':
#                             ontology.values.append(item)
#                         elif current_section == 'work_style':
#                             ontology.work_style.append(item)
#                         elif current_section == 'communication_skills':
#                             ontology.communication_skills.append(item)
#                 else:
#                     # End of section if we hit a long line or new header
#                     current_section = None
    
#     def _extract_job_descriptions(self, lines: List[str], ontology: CompanyOntology):
#         """Extract job descriptions and hiring criteria"""
#         i = 0
#         while i < len(lines):
#             line = lines[i].strip()
#             line_lower = line.lower()
            
#             # Look for job title
#             job_title = None
#             for pattern in self.job_patterns['job_title']:
#                 match = re.search(pattern, line_lower)
#                 if match:
#                     job_title = match.group(1).strip()
#                     break
            
#             if job_title:
#                 # Found a job, extract its details
#                 job_desc = ""
#                 hiring_criteria = {}
                
#                 # Look for job description in next few lines
#                 j = i + 1
#                 while j < len(lines) and j < i + 10:  # Look ahead max 10 lines
#                     next_line = lines[j].strip()
#                     next_line_lower = next_line.lower()
                    
#                     # Check for description
#                     for pattern in self.job_patterns['job_description']:
#                         match = re.search(pattern, next_line_lower)
#                         if match:
#                             job_desc = match.group(1).strip()
#                             if len(job_desc) < 30 and j + 1 < len(lines):
#                                 job_desc += " " + lines[j + 1].strip()
#                             break
                    
#                     if job_desc:
#                         break
#                     j += 1
                
#                 # Extract hiring criteria
#                 criteria_start = j if job_desc else i + 1
#                 hiring_criteria = self._extract_hiring_criteria(lines, criteria_start, min(len(lines), criteria_start + 50))
                
#                 # Create job description object
#                 job = JobDescription(
#                     title=job_title,
#                     description=job_desc,
#                     hiring_criteria=hiring_criteria
#                 )
                
#                 ontology.job_descriptions.append(job)
                
#                 # Skip ahead to avoid re-processing
#                 i = criteria_start + 20
#             else:
#                 i += 1
    
#     def _extract_hiring_criteria(self, lines: List[str], start: int, end: int) -> Dict[str, HiringCriteria]:
#         """Extract hiring criteria from a section of lines"""
#         criteria = {}
#         current_criterion = None
        
#         for i in range(start, min(end, len(lines))):
#             line = lines[i].strip()
#             line_lower = line.lower()
            
#             if not line:
#                 continue
            
#             # Check if this line defines a new criterion
#             criterion_name = self._identify_criterion_type(line_lower)
#             if criterion_name:
#                 current_criterion = criterion_name
                
#                 # Extract details for this criterion
#                 description = ""
#                 importance = "required"  # default
#                 keywords = []
#                 weight = 0.1  # default
                
#                 # Look for description in same line or next lines
#                 if ':' in line:
#                     description = line.split(':', 1)[1].strip()
                
#                 # Look ahead for more details
#                 j = i + 1
#                 while j < min(end, i + 5) and j < len(lines):
#                     next_line = lines[j].strip().lower()
                    
#                     # Check for importance indicators
#                     for imp_level, keywords_list in self.importance_keywords.items():
#                         if any(keyword in next_line for keyword in keywords_list):
#                             importance = imp_level
#                             break
                    
#                     # Extract keywords (look for comma-separated technical terms)
#                     if (',' in next_line and 
#                         any(tech_term in next_line for tech_term in 
#                             ['python', 'java', 'javascript', 'react', 'angular', 'aws', 'docker', 'testing'])):
#                         keywords = [kw.strip() for kw in next_line.split(',')]
#                         keywords = [kw for kw in keywords if len(kw) > 2]  # Filter short words
                    
#                     j += 1
                
#                 # Create hiring criteria object
#                 if current_criterion:
#                     criteria[current_criterion] = HiringCriteria(
#                         description=description or f"Skills and experience in {current_criterion}",
#                         importance=importance,
#                         keywords=keywords,
#                         weight=self._calculate_weight(importance, len(keywords))
#                     )
        
#         return criteria
    
#     def _identify_criterion_type(self, line_lower: str) -> Optional[str]:
#         """Identify what type of hiring criterion this line represents"""
#         for criterion_type, keywords in self.criteria_patterns.items():
#             if any(keyword in line_lower for keyword in keywords):
#                 return criterion_type.replace('_', ' ').title()
#         return None
    
#     def _calculate_weight(self, importance: str, num_keywords: int) -> float:
#         """Calculate weight based on importance and number of keywords"""
#         base_weights = {
#             'mandatory': 0.3,
#             'important': 0.2,
#             'required': 0.15
#         }
        
#         base = base_weights.get(importance, 0.1)
#         # Adjust based on number of keywords (more keywords = more important)
#         keyword_bonus = min(0.1, num_keywords * 0.02)
#         return round(base + keyword_bonus, 2)
    
#     def _extract_bias_statements(self, lines: List[str], ontology: CompanyOntology):
#         """Extract bias mitigation and diversity statements"""
#         bias_keywords = [
#             'diversity', 'inclusion', 'equal opportunity', 'discrimination',
#             'underrepresented', 'minorities', 'gender', 'age', 'disability',
#             'bias', 'fair', 'equitable'
#         ]
        
#         for line in lines:
#             line_lower = line.lower()
#             if any(keyword in line_lower for keyword in bias_keywords):
#                 if len(line.strip()) > 20:  # Avoid short fragments
#                     ontology.bias_mitigating_statements.append(line.strip())
    
#     def generate_ontology_file(self, ontology: CompanyOntology, output_path: str):
#         """Generate a formatted ontology file"""
#         with open(output_path, 'w', encoding='utf-8') as f:
#             f.write("# FAIRSCAN ORGANIZATIONAL ONTOLOGY\n\n")
            
#             # Company profile
#             f.write("## COMPANY PROFILE\n")
#             f.write(f"Company Name: {ontology.company_name}\n")
#             f.write(f"Description: {ontology.company_description}\n\n")
            
#             # Aim
#             if ontology.aim:
#                 f.write("## AIM\n")
#                 f.write(f"{ontology.aim}\n\n")
            
#             # Objectives
#             if ontology.objectives:
#                 f.write("## OBJECTIVES\n")
#                 for obj in ontology.objectives:
#                     f.write(f"- {obj}\n")
#                 f.write("\n")
            
#             # Values
#             if ontology.values:
#                 f.write("## COMPANY VALUES\n")
#                 for value in ontology.values:
#                     f.write(f"- {value}\n")
#                 f.write("\n")
            
#             # Work style
#             if ontology.work_style:
#                 f.write("## WORK STYLE\n")
#                 for style in ontology.work_style:
#                     f.write(f"- {style}\n")
#                 f.write("\n")
            
#             # Communication skills
#             if ontology.communication_skills:
#                 f.write("## COMMUNICATION SKILLS\n")
#                 for skill in ontology.communication_skills:
#                     f.write(f"- {skill}\n")
#                 f.write("\n")
            
#             # Job descriptions
#             if ontology.job_descriptions:
#                 f.write("## JOB DESCRIPTIONS\n\n")
                
#                 for i, job in enumerate(ontology.job_descriptions):
#                     f.write(f"### Job Title: {job.title}\n")
#                     f.write(f"Description: {job.description}\n\n")
                    
#                     if job.hiring_criteria:
#                         f.write("#### HIRING CRITERIA\n\n")
                        
#                         for criterion_name, criterion in job.hiring_criteria.items():
#                             f.write(f"##### {criterion_name}\n")
#                             f.write(f"Description: {criterion.description}\n")
#                             f.write(f"Importance: {criterion.importance}\n")
#                             if criterion.keywords:
#                                 f.write(f"Keywords: {', '.join(criterion.keywords)}\n")
#                             f.write(f"Weight: {criterion.weight}\n\n")
                    
#                     if i < len(ontology.job_descriptions) - 1:
#                         f.write("### --- DIVIDER ---\n\n")
            
#             # Bias mitigation statements
#             if ontology.bias_mitigating_statements:
#                 f.write("## BIAS MITIGATING STATEMENTS\n")
#                 for statement in ontology.bias_mitigating_statements:
#                     f.write(f"- {statement}\n")

# # Usage example
# def main():
#     # Initialize extractor
#     extractor = OntologyExtractor()
    
#     # Extract ontology from PDF
#     pdf_path = "C:/Fairscan/takundajori/mysite/media/document_templates/template.pdf"
    
#     try:
#         ontology = extractor.extract_from_pdf(pdf_path)
        
#         # Generate ontology file
#         output_path = "extracted_ontology.txt"
#         extractor.generate_ontology_file(ontology, output_path)
        
#         print(f"Ontology extracted and saved to: {output_path}")
        
#         # Print summary
#         print(f"\nExtracted Information Summary:")
#         print(f"Company: {ontology.company_name}")
#         print(f"Jobs found: {len(ontology.job_descriptions)}")
#         print(f"Objectives: {len(ontology.objectives)}")
#         print(f"Values: {len(ontology.values)}")
#         print(f"Bias statements: {len(ontology.bias_mitigating_statements)}")
        
#         # Also save as JSON for programmatic use
#         json_output = "extracted_ontology.json"
#         with open(json_output, 'w', encoding='utf-8') as f:
#             # Convert to dict, handling dataclass serialization
#             ontology_dict = asdict(ontology)
#             json.dump(ontology_dict, f, indent=2, ensure_ascii=False)
        
#         print(f"JSON version saved to: {json_output}")
        
#     except Exception as e:
#         print(f"Error processing PDF: {e}")
#         print("Please check the file path and ensure the PDF is accessible.")

# if __name__ == "__main__":
#     main()