import json
import re
import time
import hashlib
from typing import List, Optional
from .ontology_loader import FairScanOntologyLoader, JobDescription, CompanyProfile, HiringCriteria
from .person_loader import PersonDataLoader
from .kv_cache import PersistentKVCacheManager
from llama_cpp import Llama
import torch
from typing import Union
from pathlib import Path
from .job_selector import JobSelector
from typing import Dict, List, Optional, Tuple

class FairScanGradingSystem:
    def __init__(self, model_path: str, ontology_file: str, data_file: Optional[str] = None, use_gpu: bool = True):


        self.model_path = model_path
        self.use_gpu = use_gpu
        self.device = "cuda" if use_gpu else "cpu"
        
        self.kv_cache = PersistentKVCacheManager()
        self.person_loader = PersonDataLoader(data_file)
        self.ontology_loader = FairScanOntologyLoader(ontology_file)
        self.model = None
        
        self._load_models()
        self._prepare_base_context()
    
    def _load_models(self):
        """Load the language model"""
        try:
            gpu_layers = 25 if self.use_gpu and torch.cuda.is_available() else 0
            
            print("🔄 Loading language model...")
            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=gpu_layers,
                n_ctx=16384,        # Keep this - you need the context
                n_batch=2048,       # INCREASE for long documents
                n_threads=6,        # Optimize CPU usage
                verbose=False,
                use_mmap=True,
                use_mlock=True,
                temperature=0.05,   # Very low for consistency
                top_p=0.9,
                repeat_penalty=1.1,
            )
            print("✓ Language model loaded successfully")
   
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            exit(1)
    
    def _prepare_base_context(self):
        """Prepare the base system context including ontology"""
        person_context = self.person_loader.get_base_context()
        ontology_context = self.ontology_loader.get_ontology_context()
        
        additional_context = f"\n\nADDITIONAL EXPERT KNOWLEDGE:\n{person_context}" if person_context else ""
        
        self.base_system_prompt = f"""You are FairScan, an expert AI recruiter and resume evaluator designed to provide fair, objective, and bias-aware candidate assessments. You evaluate resumes against specific organizational criteria while actively mitigating hiring bias.

    CORE CAPABILITIES:
    - Analyze resumes against company-specific hiring criteria with professional precision
    - Provide objective scoring based on organizational standards and evidence
    - Generate structured JSON output with detailed assessments
    - Apply bias mitigation guidelines during evaluation
    - Offer constructive feedback and recommendations
    {ontology_context}
    EVALUATION GUIDELINES:
    When evaluating resumes, you must:
    1. Grade ONLY according to the criteria defined in the organizational ontology above
    2. Apply appropriate weights for each criteria based on importance (mandatory > important > required)
    3. Consider bias mitigation statements during evaluation
    4. Provide evidence-based scoring with specific examples from the resume
    5. Calculate weighted overall scores based on criteria importance
    6. Determine appropriate grade levels using the grading structure
    7. Identify strengths, weaknesses, and improvement recommendations
    8. Return results in structured JSON format ONLY
    9. Ensure mandatory criteria are clearly flagged if not met
    10. Focus EXCLUSIVELY on the hiring criteria defined in the ontology - do not invent or add criteria
    11. BE STRICT AND EVIDENCE-BASED: Award points only for demonstrated skills with concrete examples
    12. RECOGNIZE EQUIVALENT EXPERIENCE: Different approaches, industries, or methods can fulfill similar criteria
    13. DEPTH OVER BREADTH: Value substantial experience over superficial mentions

    BIAS MITIGATION:
    - Apply bias mitigation guidelines consistently
    - Focus on qualifications and evidence rather than assumptions
    - Consider diverse backgrounds and experiences as valuable
    - Avoid penalties for career gaps or non-traditional paths
    - Recognize that competencies can be demonstrated through various industries, roles, and contexts

    CRITICAL SCORING PRINCIPLES:
    - MANDATORY criteria scoring threshold: 70+ = "Met", <70 = "Not Met"
    - Look for EQUIVALENT skills and experiences across different contexts
    - Consider PROGRESSION and GROWTH in candidate's career trajectory
    - Value PRACTICAL APPLICATION and real-world results over theoretical knowledge
    - Account for INDUSTRY CONTEXT and different professional environments
    - Recognize TRANSFERABLE SKILLS between roles, industries, and functions

    You are now ready to receive resume evaluation requests with fair and objective assessment."""
        
        print(f"✓ Base system prompt with organizational ontology prepared ({len(self.base_system_prompt)} characters)")
        # Process and cache base context
        # =========================================NEW ============================================================
        print("🔄 Building permanent KV cache for organizational ontology...")
        self.model.reset()  # Start fresh
        tokens = self.model.tokenize(self.base_system_prompt.encode())
        self.model.eval(tokens)  # Process tokens to build KV cache
        self.base_state = self.model.save_state()  # Save permanent cache state
        print(f"✓ Permanent KV cache built ({len(tokens)} tokens)")
        # =========================================NEW ============================================================

    
    def _build_base_cache_if_needed(self):
        """Build base KV cache (organizational ontology)"""
        if self.kv_cache.should_build_base_cache(self.base_system_prompt):
            print("🔄 Building base KV cache with organizational ontology...")
            cache_prompt = self.base_system_prompt + "\n\nCACHE INITIALIZATION: ..."  # Your cache prompt
            
            response = self.model(
                cache_prompt,
                max_tokens=100,
                temperature=0.0,
                echo=False,
                stream=False
            )
            
            tokens = self.model.tokenize(self.base_system_prompt.encode())
            self.kv_cache.mark_base_cache_built(len(tokens))

    def _clear_evaluation_context(self):
        """Clear evaluation-specific context without touching base cache"""
        if self.kv_cache.should_clear_evaluation_context():
            # Clear model's evaluation context only
            if hasattr(self.model, 'reset'):
                self.model.reset()  # Full model reset if available
            elif hasattr(self.model, '_ctx'):
                # Clear llama.cpp context cache
                self.model._ctx.kv_cache_clear()
            
            self.kv_cache.clear_evaluation_context()
            print("🧹 Cleared previous evaluation context")

    def _ensure_kv_cache_persistence(self):
        """Ensure KV cache persists across evaluations"""
        # Set cache parameters explicitly
        if hasattr(self.model, 'cache'):
            self.model.cache.clear = False  # Prevent cache clearing
        
        # Store cache state
        self._cache_state = {
            'context_hash': self.kv_cache.base_context_hash,
            'tokens_cached': self.kv_cache.base_context_tokens,
            'built_at': time.time()
        }
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calculate letter grade based on percentage (0-100 scale)"""
        grading_structure = self.ontology_loader.get_grading_structure()
        
        for grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]:
            if percentage >= grading_structure[grade]["min"]:
                return grade
        return "F"
    
    def list_criteria(self, job_title: str) -> dict:
        """List all evaluation criteria for a specific job role"""
        job_role = self.ontology_loader.get_job_role(job_title)
        if not job_role:
            available_jobs = self.ontology_loader.get_all_job_titles()
            return {
                "error": f"Job title '{job_title}' not found in organizational ontology",
                "available_jobs": available_jobs
            }
        
        company_profile = self.ontology_loader.get_company_profile()
        
        criteria_info = {
            "job_title": job_role.title,
            "job_description": job_role.description,
            "company_name": company_profile.name if company_profile else "Organization",
            "company_values": company_profile.values if company_profile else [],
            "company_objectives": company_profile.objectives if company_profile else [],
            "work_style": company_profile.work_style if company_profile else "",
            "bias_mitigation": company_profile.bias_mitigation if company_profile else [],
            "total_criteria": len(job_role.criteria),
            "criteria_breakdown": []
        }
        
        total_weight = sum(criteria.weight for criteria in job_role.criteria)
        
        for criteria in job_role.criteria:
            criteria_detail = {
                "name": criteria.name,
                "importance": criteria.importance,
                "weight": criteria.weight,
                "weight_percentage": round((criteria.weight / total_weight * 100), 2) if total_weight > 0 else 0,
                "keywords": criteria.keywords,
                "description": getattr(criteria, 'description', 'No description available')
            }
            criteria_info["criteria_breakdown"].append(criteria_detail)
        
        return criteria_info

    def display_criteria(self, job_title: str):
        """Display criteria in a formatted way"""
        criteria_info = self.list_criteria(job_title)
        
        if "error" in criteria_info:
            print(f"❌ {criteria_info['error']}")
            if "available_jobs" in criteria_info:
                print("📋 Available job titles:")
                for job in criteria_info["available_jobs"]:
                    print(f"   • {job}")
            return
        
        print("=" * 70)
        print(f"📋 EVALUATION CRITERIA FOR: {criteria_info['job_title']}")
        print("=" * 70)
        print(f"🏢 Company: {criteria_info['company_name']}")
        print(f"📝 Job Description: {criteria_info['job_description']}")
        print()
        
        if criteria_info['company_values']:
            print("🎯 COMPANY VALUES:")
            for value in criteria_info['company_values']:
                print(f"   • {value}")
            print()
        
        if criteria_info['company_objectives']:
            print("🎯 COMPANY OBJECTIVES:")
            for objective in criteria_info['company_objectives']:
                print(f"   • {objective}")
            print()
        
        if criteria_info['work_style']:
            print(f"💼 WORK STYLE: {criteria_info['work_style']}")
            print()
        
        print(f"📊 EVALUATION CRITERIA ({criteria_info['total_criteria']} total criteria):")
        print("-" * 70)
        
        for i, criteria in enumerate(criteria_info['criteria_breakdown'], 1):
            print(f"{i}. {criteria['name']}")
            print(f"   Importance: {criteria['importance'].upper()}")
            print(f"   Weight: {criteria['weight']} ({criteria['weight_percentage']}%)")
            print(f"   Keywords: {', '.join(criteria['keywords'])}")
            if criteria['description'] != 'No description available':
                print(f"   Description: {criteria['description']}")
            print()
        
        if criteria_info['bias_mitigation']:
            print("⚖️ BIAS MITIGATION GUIDELINES:")
            for guideline in criteria_info['bias_mitigation']:
                print(f"   • {guideline}")
            print()
        
        print("=" * 70)

    def grade_resume_with_criteria_display(self, resume_text: str, job_title: str) -> dict:
        """Grade a resume with criteria display first"""
        
        # First display all criteria
        print("🔍 DISPLAYING EVALUATION CRITERIA BEFORE GRADING:")
        print()
        self.display_criteria(job_title)
        print()
        
        # Ask for confirmation to proceed
        if hasattr(self, 'interactive') and self.interactive:
            proceed = input("📊 Proceed with resume evaluation? (y/n): ").lower().strip()
            if proceed not in ['y', 'yes']:
                return {"message": "Evaluation cancelled by user"}
        
        print("🔄 Now proceeding with resume evaluation...")
        print()
        
        # Continue with existing grade_resume logic
        return self.grade_resume(resume_text, job_title)

   
    def grade_resume(self, resume_text: str, job_title: str) -> dict:
        """Enhanced grade resume method with improved prompting and contamination prevention"""
        try:
            # Restore base ontology state before each evaluation
            if hasattr(self, 'base_state'):
                self.model.load_state(self.base_state)
                print("⚡ Restored base ontology cache")
            else:
                # First-time initialization
                print("🔄 Building base KV cache with organizational ontology...")
                self._build_base_cache()
                self.base_state = self.model.save_state()
                print(f"✓ Permanent KV cache built ({self.kv_cache.base_context_tokens} tokens)")

            # Increment evaluation counter
            self.kv_cache.increment_evaluation_count()
            
            # Get job role criteria
            job_role = self.ontology_loader.get_job_role(job_title)
            if not job_role:
                available_jobs = self.ontology_loader.get_all_job_titles()
                return {
                    "error": f"Job title '{job_title}' not found in organizational ontology", 
                    "available_jobs": available_jobs
                }
            
            company_profile = self.ontology_loader.get_company_profile()
            
            # Format criteria with enhanced instructions
            criteria_prompt = self._format_criteria_for_prompt(job_role.criteria)
            
            # Create unique evaluation ID to prevent cross-contamination
            eval_id = hashlib.md5(f"{resume_text[:100]}{job_title}{time.time_ns()}".encode()).hexdigest()[:8]
            
            job_criteria_names = {c.name for c in job_role.criteria}
            print("JOB CRITERIA NAMES ", job_criteria_names)

            # Build enhanced scoring rubric
            scoring_rubric = self._build_enhanced_scoring_rubric(job_role.criteria)
            
            # Enhanced prompt with explicit scoring guidance
            grading_prompt = f"""RESUME EVALUATION - ID: {eval_id}

    POSITION: {job_role.title}
    COMPANY: {company_profile.name if company_profile else "Organization"}

    INSTRUCTION: Use ONLY the organizational ontology knowledge cached in your context. Ignore general training knowledge about job requirements, skills, or evaluation criteria not explicitly defined in the cached ontology.

    ENHANCED SCORING RUBRIC:
    {scoring_rubric}

    EVIDENCE REQUIREMENTS AND SCORING GUIDELINES:
    - Quote EXACT text from resume for each score
    - RECOGNIZE EQUIVALENT EXPERIENCES: Different industries, roles, or contexts can meet the same criteria
    - VALUE DEPTH: Years of experience + specific achievements + measurable outcomes + increasing responsibility
    - PROGRESSION MATTERS: Consider career growth and advancement over time
    - TRANSFERABLE SKILLS: Skills gained in one context often apply to another

    MANDATORY CRITERIA EVALUATION:
    - If criteria importance = "mandatory" AND score ≥ 70: Mark as "Met"
    - If criteria importance = "mandatory" AND score < 70: Mark as "Not Met"
    - Overall "Mandatory Criteria Met" = ALL mandatory criteria must be "Met"

    CRITICAL ASSESSMENT PRINCIPLES:
    1. EXPERIENCE can be demonstrated through: years in role, specific projects, achievements, responsibilities
    2. SKILLS can include: technical abilities, soft skills, certifications, training, practical application
    3. LEADERSHIP can encompass: formal management, project leadership, mentoring, initiative-taking, influence
    4. EDUCATION includes: formal degrees, certifications, training programs, continuous learning
    5. Consider EQUIVALENT EXPERIENCES across different industries, company sizes, and professional contexts

    RESUME TEXT:
    ---
    {resume_text}
    ---
    IMPORTANT NOTE: DONT AWARD CANDIDATE MARKS IF HE DOES NOT POSSES THE SKILL AND TECHNOLOGY
    ONLY AWARD MARKS BASED ON AVAILABLE SKILLS AND EXPERIENCE
    ADHERE TO GUIDELINES
    
    RESPONSE FORMAT (JSON only, no additional text):
    {{
        "evaluation_id": "{eval_id}",
        "evaluation_summary": "One sentence professional assessment focusing on key strengths and role fit based on what is in the resume only",
        "overall_score": <calculate weighted average>,
        "grade": "<A+/A/A-/B+/B/B-/C+/C/C-/D/F>",
        "hr_justification": {{
            "values_alignment": "How candidate's background and experience aligns with company values and culture",
            "professional_competency": "Key professional strengths with specific experience and demonstrated capabilities"
        }},
        "detailed_criteria_assessment": {{
            {self._generate_criteria_template(job_role.criteria)}
        }},
        "skills_inventory": {{
            "core_skills": ["primary skills and competencies mentioned in resume"],
            "tools_systems": ["tools, systems, software, or methodologies mentioned"], 
            "certifications": ["certifications, licenses, or credentials mentioned"]
        }},
        "strengths": ["specific strengths with evidence and professional context"],
        "weaknesses": ["specific areas for improvement based on criteria gaps"],
        "recommendations": ["actionable recommendations for professional development"],
        "mandatory_criteria_status": {{
            {self._generate_mandatory_template(job_role.criteria)}
        }},
        "quantifiable_achievements": ["any metrics, numbers, results, or measurable outcomes from resume"]

        "CONTINUE GENERATING UNTIL YOU HAVE COMPLETED ALL SECTIONS OF THE RESPONSE."

    }}"""

            print(f"🔄 Evaluating resume #{self.kv_cache.evaluation_count}...")
                        
            response = self.model(
                grading_prompt,
                max_tokens=4000,  # Increased for detailed responses
                temperature=0.0,   # Zero temperature for determinism
                top_p=1.0,         
                top_k=1,           
                repeat_penalty=1.15,
                stop=["\n\nEVALUATION", "RESUME EVALUATION", "---"],
                echo=False,
            )

            generated_text = response['choices'][0]['text'].strip()

            # print("GENERATED TEXT ", generated_text)

            # Extract and validate JSON
            json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    
                    # Enhanced validation
                    result = self._validate_and_enhance_result(result, job_role)
                    
                    print("RESULT ", result)

                    # Add metadata
                    result["job_title"] = job_role.title
                    result["company_name"] = company_profile.name if company_profile else "Organization"
                    result["evaluation_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    result["evaluation_number"] = self.kv_cache.evaluation_count
                    
                    print(f"✅ Resume evaluation #{self.kv_cache.evaluation_count} completed")
                    return result
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parsing failed: {e}")
                    return {"error": "Invalid JSON response", "raw_response": generated_text}
            else:
                return {"error": "No JSON found in response", "raw_response": generated_text}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"Evaluation failed: {str(e)}"}
        finally:
            # Always restore base state
            if hasattr(self, 'base_state'):
                self.model.load_state(self.base_state)

    def _build_enhanced_scoring_rubric(self, criteria):
        """Build enhanced scoring rubric with universal guidance"""
        rubric_lines = ["CRITERIA-SPECIFIC SCORING GUIDANCE:"]
        
        for criterion in criteria:
            keywords_str = ", ".join(criterion.keywords[:8])  # Include more keywords for context
            rubric_lines.append(f"• {criterion.name}: Look for evidence of {keywords_str}")
            rubric_lines.append(f"  - Consider: related experience, transferable skills, equivalent roles or responsibilities")
        
        rubric_lines.append("\nGENERAL PRINCIPLES:")
        rubric_lines.append("- Value demonstrated results and achievements over titles")
        rubric_lines.append("- Consider progression and growth over time")
        rubric_lines.append("- Recognize skills gained across different contexts")
        rubric_lines.append("- Look for specific examples and quantifiable outcomes")
        
        return "\n".join(rubric_lines)

    def _generate_criteria_template(self, criteria):
        """Generate JSON template for criteria assessment with universal structure"""
        templates = []
        for criterion in criteria:
            template = f'''"{criterion.name}": {{
                "score": <0-100>,
                "evidence_found": ["show only the specific quotes and examples from resume demonstrating this criteria"],
                "strength_level": "Basic/Intermediate/Advanced/Expert",
                "explanation": "Detailed justification based on evidence, experience level, and demonstrated competency"
            }}'''
            templates.append(template)
        return ",\n        ".join(templates)

    def _generate_mandatory_template(self, criteria):
        """Generate template for mandatory criteria status"""
        mandatory_criteria = [c for c in criteria if c.importance == "mandatory"]
        templates = []
        for criterion in mandatory_criteria:
            templates.append(f'"{criterion.name}": "Met/Not Met"')
        return ",\n        ".join(templates)

    def _format_simple_criteria(self, criteria):
            """Format criteria in simple, scannable format"""
            formatted = []
            for criterion in criteria:
                formatted.append(f"""
        {criterion.name} (Weight: {criterion.weight}, {criterion.importance}):
        - Keywords: {', '.join(criterion.keywords)}
        - Look for: {criterion.description}
        """)
            return '\n'.join(formatted)

    def _format_criteria_for_prompt(self, criteria: List[HiringCriteria]) -> str:
        """Enhanced criteria formatting with strength indicators"""
        formatted = []
        for i, c in enumerate(criteria, 1):
            formatted.append(
                f"{i}. {c.name} (Weight: {c.weight*100}%, Importance: {c.importance})\n"
                f"   Description: {c.description}\n"
                f"   Keywords: {', '.join(c.keywords)}\n"
                f"   Strength Indicators:\n"
                f"   - Basic: Familiar with concepts\n"
                f"   - Intermediate: Professional experience\n"
                f"   - Advanced: Leadership/expert-level"
            )
        return '\n'.join(formatted)

    def _validate_and_enhance_result(self, result: dict, job_role: JobDescription) -> dict:
        """Validate and enhance evaluation result"""
        # Calculate overall score if missing
        if "overall_score" not in result:
            total_weighted_score = 0
            total_weight = 0
            
            for criterion in job_role.criteria:
                if criterion.name in result.get("detailed_criteria_assessment", {}):
                    crit_data = result["detailed_criteria_assessment"][criterion.name]
                    score = crit_data.get("score", 0)
                    total_weighted_score += score * criterion.weight
                    total_weight += criterion.weight
                    print("DONE1WW")

            
            if total_weight > 0:
                result["overall_score"] = total_weighted_score / total_weight * 100
        # Ensure grade is calculated
        if "grade" not in result and "overall_score" in result:
            result["grade"] = self._calculate_grade(result["overall_score"])
        
        # Add missing sections
        if "technical_skills_inventory" not in result:
            result["technical_skills_inventory"] = {}
        
        if "quantifiable_achievements" not in result:
            result["quantifiable_achievements"] = []
        
        return result


    def evaluate_resume_file(self, resume_text: str, job_title: str) -> dict:
        try:
            return self.grade_resume(resume_text, job_title)
        except Exception as e:
            return {"error": f"Error reading resume file: {e}"}
        
    

    # Add these methods to FairScanGradingSystem class
    def _prepare_job_selector(self, use_offline: bool = True):
        print("🔄 Initializing job matching system...")
        self.job_selector = JobSelector(use_offline=use_offline)
        
        # Build job database from ontology
        job_data = self.ontology_loader.convert_to_job_selector_format()

        print("JOB DATA ",job_data)
        if job_data:
            self.job_selector.prepare_job_database(job_data)
            print(f"✓ Job selector initialized with {len(job_data)} positions")
        else:
            print("⚠️ No job data available for matching system")

    def find_best_job_match(self, resume_input: Union[str, Path]) -> Tuple[Optional[str], float]:
        """Find best matching job for a resume"""
        if not hasattr(self, 'job_selector'):
            self._prepare_job_selector()
        
        if isinstance(resume_input, Path) or (isinstance(resume_input, str) and resume_input.endswith('.pdf')):
            resume_text = self.job_selector.extract_resume_text(str(resume_input))
        else:
            resume_text = resume_input
        
        job_match, score = self.job_selector.find_top_match(resume_text)
        if job_match:
            print(f"🔍 Best job match: {job_match['title']} (score: {score:.3f})")
            return job_match['title'], score
        return None, 0.0