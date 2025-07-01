
import json
import torch
from ontology_loader import FairScanOntologyLoader
from job_selector import JobSelector
from grading_system import FairScanGradingSystem
import fitz  # PyMuPDF

from pathlib import Path
from typing import Tuple, Optional, Union
from ontology_loader import FairScanOntologyLoader
from job_selector import JobSelector

def main():
    # Initialize the grading system
    grading_system = FairScanGradingSystem(
        model_path="./models/Mistral-7B-Instruct-v0.3-Q3_K_L.gguf",
        ontology_file="ontology.txt",
        use_gpu=torch.cuda.is_available()  # Auto-detect GPU

    )
    
    # Find best job match first
    resume_path = "13385306.pdf"  # or use text directly
    matched_job, match_score = grading_system.find_best_job_match(resume_path)
    
    if matched_job:
        print(f"\n⚡ Best matched job: {matched_job} (confidence: {match_score:.2f})")
        
        # Grade against the matched job

        doc = fitz.open(resume_path)
        text = ""
        for page in doc:
            text += page.get_text()

        result = grading_system.evaluate_resume_file(
            text,  # Can be file path or text
            matched_job
        )
        
        # Print results
        print("\nEvaluation Results: ", result)
        print(f"Overall Score: {result['overall_score']:.1f}")
        print(f"Grade: {result['grade']}")
        print("\nDetailed Criteria Assessment:")
        for criteria, details in result['detailed_criteria_assessment'].items():
            print(f"- {criteria}: {details['score']}/100")
        
        # Save results
        with open("evaluation_results.json", "w") as f:
            json.dump(result, f, indent=2)
    else:
        print("❌ No suitable job matches found")

if __name__ == "__main__":
    main()