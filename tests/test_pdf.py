import sys
import os

# Add project root to sys.path so we can import from project
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from pdf_generator import generate_critique_pdf

# Mock critique data matching the schema
mock_data = {
    "overall_score": 82,
    "scores": {
        "impact": 75,
        "presentation": 85,
        "experience": 90,
        "keywords": 78
    },
    "summary": "This is a strong CV that highlights key achievements. It aligns well with the software engineer profile but requires slight optimizations in keyword density.",
    "strengths": [
        {
            "category": "Experience",
            "point": "Strong technical background in Python and FastAPI",
            "detail": "The work history clearly demonstrates the implementation of backend services using FastAPI and clean architectures."
        }
    ],
    "improvements": [
        {
            "category": "Quantification",
            "point": "Quantify achievements using metrics",
            "detail": "Several bullet points describe tasks without presenting the results or business impact. Try to use percentages or numbers."
        }
    ],
    "keyword_analysis": {
        "matched": ["Python", "FastAPI", "SQLite", "API Design"],
        "missing": ["Docker", "CI/CD", "Unit Testing"],
        "critical_percentage": 57
    },
    "section_critique": {
        "summary": "Clean and concise, but could mention years of experience.",
        "experience": "Detailed, although some bullets are slightly weak in result description.",
        "projects_skills": "Skills section is well organized. Project section could use web links."
    },
    "bullet_rewrites": [
        {
            "original": "Worked on python code and fixed bugs.",
            "improved": "Refactored critical Python backend codebase, reducing runtime latency by 15% and resolving 40+ legacy bugs.",
            "rationale": "Uses active verbs, quantifies impact with a metric, and clearly defines scope of work."
        }
    ]
}

def test_pdf_generation():
    print("Starting PDF generation test...")
    pdf_bytes = generate_critique_pdf(mock_data, "John_Doe_Resume.pdf", "Senior Backend Engineer")
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "test_critique_report.pdf")
    
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
        
    print(f"PDF report generated successfully! Saved to: {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
    
    if os.path.getsize(output_path) > 1000:
        print("Verification PASSED: PDF file size is valid.")
    else:
        print("Verification FAILED: PDF file is empty or too small.")

if __name__ == "__main__":
    test_pdf_generation()
