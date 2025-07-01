import argparse
from fairscan.grading_system import FairScanGradingSystem

def main():
    parser = argparse.ArgumentParser(description="FairScan Resume Grading System")
    parser.add_argument("--model", required=True, help="Path to language model file")
    parser.add_argument("--ontology", required=True, help="Path to organizational ontology file")
    parser.add_argument("--resume", help="Path to resume file to evaluate")
    parser.add_argument("--job", help="Job title to evaluate against")
    parser.add_argument("--output", help="Output file for results (JSON format)")
    
    args = parser.parse_args()
    
    grading_system = FairScanGradingSystem(
        model_path=args.model,
        ontology_file=args.ontology
    )
    
    if args.resume and args.job:
        result = grading_system.evaluate_resume_file(args.resume, args.job)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()