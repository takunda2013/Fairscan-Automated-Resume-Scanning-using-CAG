import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional

@dataclass
class HiringCriteria:
    name: str
    description: str
    importance: str
    keywords: List[str]
    weight: float

@dataclass
class JobDescription:
    title: str
    description: str
    criteria: List[HiringCriteria]

@dataclass
class CompanyProfile:
    name: str
    description: str
    aim: str
    objectives: List[str]
    values: List[str]
    work_style: List[str]
    communication_skills: List[str]
    bias_mitigation: List[str]
    job_descriptions: List[JobDescription]

class FairScanOntologyLoader:
    def __init__(self, ontology_file: str):
        self.ontology_file = Path(ontology_file)
        self.company_profile: Optional[CompanyProfile] = None
        self.ontology_context = ""
        self.grading_structure = self._init_grading_structure()
        self.load_ontology()
    
    def _init_grading_structure(self) -> dict:
        return {
            "A+": {"min": 95, "description": "Exceptional candidate - exceeds all expectations"},
            "A": {"min": 90, "description": "Excellent candidate - strong fit for role"},
            "B+": {"min": 85, "description": "Very good candidate - above average qualifications"},
            "B": {"min": 80, "description": "Good candidate - meets most requirements"},
            "C+": {"min": 75, "description": "Acceptable candidate - meets basic requirements"},
            "C": {"min": 70, "description": "Marginal candidate - minimum acceptable level"},
            "D": {"min": 60, "description": "Below expectations - significant gaps"},
            "F": {"min": 0, "description": "Does not meet requirements - not suitable for role"}
        }
    
    def load_ontology(self):
        if not self.ontology_file.exists():
            print(f"Warning: Ontology file {self.ontology_file} not found.")
            return
        
        try:
            with open(self.ontology_file, 'r', encoding='utf-8') as f:
                ontology_text = f.read().strip()
            self._parse_fairscan_template(ontology_text)
            self._build_ontology_context()
        except Exception as e:
            print(f"Error loading ontology file: {e}")
    def load_ontology(self):
        """Load organizational ontology from FairScan template"""
        if not self.ontology_file.exists():
            print(f"Warning: Ontology file {self.ontology_file} not found. Creating default structure.")
            # self._create_default_ontology()
            return
        
        try:
            with open(self.ontology_file, 'r', encoding='utf-8') as f:
                ontology_text = f.read().strip()
            
            self._parse_fairscan_template(ontology_text)
            self._build_ontology_context()
            
            print(f"✓ Loaded FairScan organizational ontology:")
            print(f"   Company: {self.company_profile.name if self.company_profile else 'None'}")
            print(f"   Job Roles: {len(self.company_profile.job_descriptions) if self.company_profile else 0}")
            print(f"   Context Size: {len(self.ontology_context)} characters")
            
        except Exception as e:
            print(f"Error loading ontology file: {e}")
            self._create_default_ontology()
    
    
    
    def _parse_fairscan_template(self, text: str):
        """Parse FairScan template format with improved flexibility"""
        lines = text.split('\n')
        current_section = None
        current_job = None
        current_criteria = None
        
        # Initialize company data
        company_data = {
            "name": "",
            "description": "",
            "aim": "",
            "objectives": [],
            "values": [],
            "work_style": [],
            "communication_skills": [],
            "bias_mitigation": [],
            "job_descriptions": []
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and single # comments
            if not line or (line.startswith('#') and not line.startswith('##')):
                i += 1
                continue
            
            # Section headers (case insensitive matching)
            line_upper = line.upper()
            if line.startswith("## COMPANY PROFILE") or "COMPANY PROFILE" in line_upper:
                current_section = "company_profile"
            elif line.startswith("## AIM") or line_upper.startswith("## AIM"):
                current_section = "aim"
            elif line.startswith("## OBJECTIVES") or "OBJECTIVES" in line_upper:
                current_section = "objectives"
            elif line.startswith("## COMPANY VALUES") or "COMPANY VALUES" in line_upper or "VALUES" in line_upper:
                current_section = "values"
            elif line.startswith("## WORK STYLE") or "WORK STYLE" in line_upper:
                current_section = "work_style"
            elif line.startswith("## COMMUNICATION SKILLS") or "COMMUNICATION SKILLS" in line_upper:
                current_section = "communication_skills"
            elif line.startswith("## JOB DESCRIPTIONS") or "JOB DESCRIPTIONS" in line_upper or "JOBS" in line_upper:
                current_section = "job_descriptions"
            elif line.startswith("## BIAS MITIGATING") or "BIAS" in line_upper and "MITIGAT" in line_upper:
                current_section = "bias_mitigation"
            
            # Parse company profile
            elif current_section == "company_profile":
                if line.startswith("Company Name:") or line.startswith("Name:"):
                    company_data["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("Description:"):
                    company_data["description"] = line.split(":", 1)[1].strip()
            
            # Parse aim
            elif current_section == "aim" and line and not line.startswith("##"):
                if company_data["aim"]:
                    company_data["aim"] += " " + line
                else:
                    company_data["aim"] = line
            
            # Parse list sections
            elif current_section in ["objectives", "values", "work_style", "communication_skills", "bias_mitigation"]:
                if line.startswith("- "):
                    company_data[current_section].append(line[2:].strip())
                elif line and not line.startswith("##") and not line.startswith("###"):
                    # Handle non-bullet list items
                    company_data[current_section].append(line.strip())
            
            # Parse job descriptions
            elif current_section == "job_descriptions":
                # Handle divider FIRST before processing job titles
                if line.startswith("### ---") or line.startswith("### DIVIDER"):
                    print("HERE")
                      # Save current criteria if it exists
                    if current_criteria and current_job:
                        current_job["criteria"].append(current_criteria)
                    
                    if current_job:  # Save current job before resetting
                        criteria_objects = [HiringCriteria(**crit) for crit in current_job["criteria"]]
                        current_job["criteria"] = criteria_objects
                        company_data["job_descriptions"].append(JobDescription(**current_job))
                    current_job = None
                    current_criteria = None
                    i += 1  # MUST INCREMENT HERE
                    continue  # Skip divider line
                
                if line.startswith("### Job Title:") or line.startswith("### "):
                    # Save previous job
                    if current_job:
                        # Convert criteria dicts to HiringCriteria objects
                        criteria_objects = []
                        for crit in current_job["criteria"]:
                            criteria_objects.append(HiringCriteria(**crit))
                        current_job["criteria"] = criteria_objects
                        company_data["job_descriptions"].append(JobDescription(**current_job))
                    
                    # Start new job
                    job_title = line.split(":", 1)[1].strip() if ":" in line else line.replace("### ", "").strip()
                    current_job = {
                        "title": job_title,
                        "description": "",
                        "criteria": []
                    }
                
                elif line.startswith("Description:") and current_job:
                    current_job["description"] = line.split(":", 1)[1].strip()
                
                elif line.startswith("##### "):
                    # Save previous criteria
                    if current_criteria:
                        current_job["criteria"].append(current_criteria)
                    
                    # Start new criteria
                    criteria_name = line.split("##### ", 1)[1].strip()
                    current_criteria = {
                        "name": criteria_name,
                        "description": "",
                        "importance": "required",
                        "keywords": [],
                        "weight": 0.2
                    }
                
                elif current_criteria:
                    if line.startswith("Description:"):
                        current_criteria["description"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Importance:"):
                        current_criteria["importance"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Keywords:"):
                        keywords_text = line.split(":", 1)[1].strip()
                        current_criteria["keywords"] = [k.strip() for k in keywords_text.split(",")]
                    elif line.startswith("Weight:"):
                        try:
                            current_criteria["weight"] = float(line.split(":", 1)[1].strip())
                        except ValueError:
                            current_criteria["weight"] = 0.2
            
            i += 1
        
        # Add final items
        if current_criteria and current_job:
            current_job["criteria"].append(current_criteria)
        
        if current_job:
            criteria_objects = []
            for crit in current_job["criteria"]:
                criteria_objects.append(HiringCriteria(**crit))
            current_job["criteria"] = criteria_objects
            company_data["job_descriptions"].append(JobDescription(**current_job))
        
        # Create CompanyProfile object
        self.company_profile = CompanyProfile(**company_data)
        
        print(f"✓ Parsing complete! Found {len(self.company_profile.job_descriptions)} job roles")
    
    def _build_ontology_context(self):
        """Build comprehensive context string for KV caching"""
        if not self.company_profile:
            self.ontology_context = ""
            return
        
        context_parts = []
        
        # Company information
        context_parts.append("=== COMPANY PROFILE ===")
        context_parts.append(f"Company: {self.company_profile.name}")
        context_parts.append(f"Description: {self.company_profile.description}")
        context_parts.append(f"Aim: {self.company_profile.aim}")
        
        if self.company_profile.objectives:
            context_parts.append("\nObjectives:")
            for obj in self.company_profile.objectives:
                context_parts.append(f"- {obj}")
        
        if self.company_profile.values:
            context_parts.append(f"\nCompany Values: {', '.join(self.company_profile.values)}")
        if self.company_profile.work_style:
            context_parts.append(f"Work Style: {', '.join(self.company_profile.work_style)}")
        if self.company_profile.communication_skills:
            context_parts.append(f"Communication Skills: {', '.join(self.company_profile.communication_skills)}")
        
        # Job roles and criteria
        context_parts.append("\n=== JOB DESCRIPTIONS AND HIRING CRITERIA ===")
        for job in self.company_profile.job_descriptions:
            context_parts.append(f"\nJob Title: {job.title}")
            context_parts.append(f"Description: {job.description}")
            context_parts.append("Hiring Criteria:")
            
            for criteria in job.criteria:
                context_parts.append(f"""
- {criteria.name} (Importance: {criteria.importance}, Weight: {criteria.weight*100}%)
  Description: {criteria.description}
  Keywords: {', '.join(criteria.keywords)}""")
        
        # Bias mitigation
        if self.company_profile.bias_mitigation:
            context_parts.append("\n=== BIAS MITIGATION GUIDELINES ===")
            for statement in self.company_profile.bias_mitigation:
                context_parts.append(f"- {statement}")
        
        # Grading structure
        context_parts.append("\n=== GRADING STRUCTURE ===")
        for grade, info in self.grading_structure.items():
            context_parts.append(f"{grade}: {info['min']}%+ - {info['description']}")
        
        self.ontology_context = '\n'.join(context_parts)
    
    def get_ontology_context(self) -> str:
        """Get the complete ontology context for caching"""
        return self.ontology_context
    
    def get_job_role(self, title: str) -> Optional[JobDescription]:
        """Get specific job role by title (case insensitive)"""
        if not self.company_profile:
            return None
        
        title_lower = title.lower()
        for job in self.company_profile.job_descriptions:
            if job.title.lower() == title_lower:
                return job
        
        # Try partial matching
        for job in self.company_profile.job_descriptions:
            if title_lower in job.title.lower() or job.title.lower() in title_lower:
                return job
        
        return None
    
    def get_all_job_titles(self) -> List[str]:
        """Get list of all available job titles"""
        if not self.company_profile:
            return []
        return [job.title for job in self.company_profile.job_descriptions]
    
    def get_company_profile(self) -> Optional[CompanyProfile]:
        """Get the company profile"""
        return self.company_profile
    
    def get_grading_structure(self) -> dict:
        """Get the grading structure"""
        return self.grading_structure

    def convert_to_job_selector_format(self) -> List[Dict]:
        if not self.company_profile:
            return []
        
        job_data = []
        for job in self.company_profile.job_descriptions:
            requirements = ", ".join([c.name for c in job.criteria])
            skills = ", ".join(set(kw for c in job.criteria for kw in c.keywords))
            
            job_data.append({
                "id": f"ont_{job.title.replace(' ', '_')}",
                "title": job.title,
                "description": job.description,
                "requirements": requirements,
                "skills": skills
            })
        return job_data