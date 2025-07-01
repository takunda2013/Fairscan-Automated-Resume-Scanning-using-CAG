from datetime import datetime  # Correct import at the top of your file
import json
from celery import shared_task
import time
from django.db import transaction
import torch
from scan.main_engine.grading_system import FairScanGradingSystem
from django.contrib.auth.models import User

from .models import ProcessedResumeText, UploadedFile

@shared_task
def long_running_task(param1, param2):
    # Your actual work here
    # time.sleep(3)  # Simulate long process
    return f"Task completed with {param1} and {param2}"



# 1. Create the individual resume processing task
@shared_task(bind=True)
def process_single_resume(self, resume_data, user_id):
    """Process a single resume and save to database"""
    try:
        print(f"Processing resume: {resume_data['id']}")

       #========================================================
        resume_id = resume_data['id']


        resume = UploadedFile.objects.get(id=resume_id)
        
        # Your AI processing logic here...
        content = resume_data['content']

        print("CONTENT ", content)
        person_identifiers = resume_data['person_identifiers']
        
        # Example: Call your AI analyss function
        
        # Save results to database using transaction for safety
        with transaction.atomic():
            # Update the original resume status
            resume.scan_status = 'graded'
            resume.save()
            print("RESUME UPDATED")
            
        time.sleep(3)  # Simulate long process

       #========================================================
       # 
       #      
        # matched_job, match_score = FairScanGradingSystem.find_best_job_match(resume_input=content)

        # # Your LLM processing logic here
        # result = FairScanGradingSystem.grade_resume(resume_data['content'],matched_job)
        

        print("RESULT ", result)
        # NO PERSON IDENTIFIERS SHOULD BE PUT IN THE DB STRAIGHT   

        # # Save to database immediately after processing
        # from django.contrib.auth.models import User
        # user = User.objects.get(id=user_id)
        
        # generated_response = ProcessedResumeText(
        #     resume_name=resume_data['id'],
        #     processing_overall_score=result.get('score', 0.0),
        #     score_evaluation=result.get('evaluation', 'Processing completed'),
        #     processed_date=datetime.now(),
        #     processed_by=user
        # )
        # generated_response.save()
        
        print(f"✅ Completed and saved: {resume_data['id']}")
        
        # return {
        #     'status': 'success',
        #     'resume_name': resume_data['id'],
        #     'score': result.get('score', 0.0)
        # }
        return {
            'status': 'success',
            'resume_name': resume_data['id'],
            'score':  0.0
        }
        
    except Exception as exc:
        print(f"❌ Failed processing {resume_data['id']}: {exc}")
        raise self.retry(exc=exc, countdown=30, max_retries=2)


# 2. Create chain orchestrator task
@shared_task(bind=True)
def process_resume_chain(self, resume_list, user_id):
    """Process all resumes sequentially"""
    results = []

    print("LETS LOAD MODELS")
    model_path = r"C:\Fairscan\takundajori\mysite\scan\main_engine\models\Mistral-7B-Instruct-v0.3-Q3_K_L.gguf"
    ontology_path = r"C:\Fairscan\takundajori\mysite\media\generated\ontology.txt"
    # Initialize the grading system
    grading_system = FairScanGradingSystem(
        model_path= model_path,
        ontology_file=ontology_path,
        use_gpu=torch.cuda.is_available()  # Auto-detect GPU
    )
   
    print("MATCHED JOB ")
    
    for i, resume_data in enumerate(resume_list):
        try:
            print(f"Starting resume {i+1}/{len(resume_list)}: {resume_data['id']}")
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': len(resume_list),
                    'current_resume': resume_data['id'],
                    'completed': results
                }
            )
           
            
            time.sleep(3)  # Simulate long process
            
            content = resume_data['content']

            matched_job, match_score = grading_system.find_best_job_match(content)

            print("MATCHED JOB ", matched_job)

            MINIMUM_COMPATIBILITY_THRESHOLD = 0.28  # 25% minimum match required

            
            
            if match_score  < MINIMUM_COMPATIBILITY_THRESHOLD:
                # Candidate does not meet minimum requirements for any available position
                result = {
                    "compatibility_score": f"{match_score :.1%}",
                    "best_matching_position": matched_job,
                    "recommendation": "REJECT - Candidate does not meet minimum qualifications",
                    "reason": "The candidate's skills and experience do not align sufficiently with any of our current job openings. Consider keeping resume on file for future opportunities that may better match their profile."
                }
            else:
                result = grading_system.grade_resume(content, matched_job)

            print("DONE ", result)

            """
            Process resume grading result and save to database
            
            Args:
                content: Resume content
                matched_job: Job details for matching
                resume_name: Name of the resume file
                user: User who processed the resume
            """
            
            # Get grading result (assuming this returns a JSON object)
            
            # Parse JSON if result is a string, otherwise use directly
            if isinstance(result, str):
                grading_data = json.loads(result)
            else:
                grading_data = result
            
            if match_score < MINIMUM_COMPATIBILITY_THRESHOLD:
                overall_score = match_score * 100
            # Extract overall score
            else:
                overall_score = grading_data.get('overall_score', 0.0)

            resume = UploadedFile.objects.get(id=resume_data['id'])
        
            # Save results to database using transaction for safety
            with transaction.atomic():
                # Update the original resume status
                resume.scan_status = 'graded'
                resume.save()
                print("RESUME UPDATED")
            
            print("OVERALL SCORE ", overall_score)
            # Format the evaluation text with proper indentation
            evaluation_text = format_evaluation_text(grading_data, resume_data['person_identifiers'], user_id, match_score,matched_job)
            
            user = User.objects.get(id=user_id)

            # Create and save the model instance
            processed_resume = ProcessedResumeText.objects.create(
                resume_name=resume_data['resume_name'],
                processing_overall_score=overall_score,
                score_evaluation=evaluation_text,
                processed_by=user
            )


        except Exception as e:
            print(f"Error in chain for {resume_data['id']}: {e}")
            results.append({
                'status': 'failed',
                'resume_name': resume_data['id'],
                'error': str(e)
            })
    
    return {
        'status': 'completed',
        'total_processed': len(resume_list),
        'results': results
    }

def format_evaluation_text(grading_data, resume_name, user_id, match_score,matched_job):
    """
    Format the grading data as plain text with good indentation
    """
    user = User.objects.get(id=user_id)

    # Start with person identifiers and metadata
    evaluation_lines = []
    evaluation_lines.append("RESUME EVALUATION REPORT")
    evaluation_lines.append("=" * 50)
    evaluation_lines.append("")
    
    # Person identifiers
    evaluation_lines.append("PROCESSING DETAILS:")
    evaluation_lines.append(f"    Resume Name: {resume_name}")
    evaluation_lines.append(f"    Processed By: {user.get_full_name() or user.username}")
    evaluation_lines.append(f"    Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    evaluation_lines.append("")
    
    # Overall Score (included in the text as well)
    overall_score = grading_data.get('overall_score', 0.0)
    evaluation_lines.append("OVERALL ASSESSMENT:")
    evaluation_lines.append(f"    Overall Score: {overall_score}%")
    evaluation_lines.append("")
    evaluation_lines.append(f"SYSTEM JOB DESCRIPTION MATCH SCORE: {match_score :.1}")
    evaluation_lines.append("")
    evaluation_lines.append(f"SYSTEM JOB DESCRIPTION JOB MATCH: {matched_job}")
    evaluation_lines.append("")


    
    # Process different sections of the grading result
    for key, value in grading_data.items():
        if key == 'overall_score':
            continue  # Already handled above
            
        # Format section headers
        section_title = key.replace('_', ' ').title()
        evaluation_lines.append(f"{section_title.upper()}:")
        
        if isinstance(value, dict):
            # Handle nested dictionaries
            for sub_key, sub_value in value.items():
                sub_title = sub_key.replace('_', ' ').title()
                evaluation_lines.append(f"    {sub_title}:")
                
                if isinstance(sub_value, list):
                    for item in sub_value:
                        evaluation_lines.append(f"        • {item}")
                elif isinstance(sub_value, dict):
                    for nested_key, nested_value in sub_value.items():
                        nested_title = nested_key.replace('_', ' ').title()
                        evaluation_lines.append(f"        {nested_title}: {nested_value}")
                else:
                    evaluation_lines.append(f"        {sub_value}")
                    
        elif isinstance(value, list):
            # Handle lists
            for item in value:
                if isinstance(item, dict):
                    for item_key, item_value in item.items():
                        item_title = item_key.replace('_', ' ').title()
                        evaluation_lines.append(f"    {item_title}: {item_value}")
                else:
                    evaluation_lines.append(f"    • {item}")
                    
        else:
            # Handle simple values
            evaluation_lines.append(f"    {value}")
            
        evaluation_lines.append("")  # Add spacing between sections
    
    return "\n".join(evaluation_lines)
