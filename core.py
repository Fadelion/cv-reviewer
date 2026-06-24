import os
import json
from dotenv import load_dotenv
from groq import Groq
from typing import List, Dict, Any
from pydantic import BaseModel, Field, ValidationError

# Import custom RAG, DB history, and guardrails modules
from rag_retriever import retrieve_guidelines
from guardrails import (
    validate_lengths,
    detect_prompt_injection,
    verify_resume_domain,
    sanitize_and_repair_critique
)

# Load environment variables. First look locally, then in parent, then parent of parent.
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Pydantic schemas for structured output validation
class StrengthSchema(BaseModel):
    category: str = Field(..., description="Category of strength")
    point: str = Field(..., description="Short summary statement of strength")
    detail: str = Field(..., description="Full context and examples showing this strength")

class ImprovementSchema(BaseModel):
    category: str = Field(..., description="Category of improvement")
    point: str = Field(..., description="Short summary statement of improvement")
    detail: str = Field(..., description="Actionable advice and specific references to CV")

class KeywordAnalysisSchema(BaseModel):
    matched: List[str] = Field(default_factory=list, description="Keywords present in CV")
    missing: List[str] = Field(default_factory=list, description="Crucial keywords missing")
    critical_percentage: int = Field(..., ge=0, le=100, description="ATS keyword alignment score (0-100)")

class SectionCritiqueSchema(BaseModel):
    summary: str = Field(..., description="Feedback on professional summary/objective")
    experience: str = Field(..., description="Feedback on work experience section")
    projects_skills: str = Field(..., description="Feedback on projects, education, and skills sections")

class BulletRewriteSchema(BaseModel):
    original: str = Field(..., description="Weak bullet point from CV")
    improved: str = Field(..., description="Optimized high-impact STAR bullet point")
    rationale: str = Field(..., description="Explanation of why this rewrite is better")

class CategoryScoresSchema(BaseModel):
    impact: int = Field(..., ge=0, le=100)
    presentation: int = Field(..., ge=0, le=100)
    experience: int = Field(..., ge=0, le=100)
    keywords: int = Field(..., ge=0, le=100)

class CVReviewSchema(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    scores: CategoryScoresSchema
    summary: str = Field(..., description="Executive summary of the CV caliber")
    strengths: List[StrengthSchema]
    improvements: List[ImprovementSchema]
    keyword_analysis: KeywordAnalysisSchema
    section_critique: SectionCritiqueSchema
    bullet_rewrites: List[BulletRewriteSchema]

SYS_PROMPT_TEMPLATE = """You are a world-class professional CV reviewer, senior hiring manager, and ATS (Applicant Tracking System) specialist.
Your goal is to perform a rigorous, highly-actionable, and structured analysis of the user's Resume/CV, optionally comparing it to a target Job Description (if provided).

To assist you in this evaluation, here are some retrieved best-practice guidelines from our expert CV writing database:
--- RETRIEVED BEST PRACTICE GUIDELINES (RAG CONTEXT) ---
{rag_context}
-------------------------------------------------------
You MUST align your scores, critiques, and recommendations with these guidelines.

Analyze the CV on the following metrics:
1. **Impact**: How well achievements are quantified, action verbs used, and result-oriented bullet points (STAR method).
2. **Presentation**: Formatting, logical flow, reading ease, structure, and professional tone.
3. **Experience**: Depth of technical/business skills shown, career progression, and relevance.
4. **Keywords**: Presence of important sector-specific keywords and technical competencies.

You MUST respond with a single valid JSON object. Do not include any markdown styling like ```json ... ``` or wrapping in your output. Return only the raw JSON.

The JSON response MUST strictly follow this schema:
{{
  "overall_score": <int between 0 and 100>,
  "scores": {{
    "impact": <int 0-100>,
    "presentation": <int 0-100>,
    "experience": <int 0-100>,
    "keywords": <int 0-100>
  }},
  "summary": "<string: A compelling 3-4 sentence professional summary of the resume's caliber, strengths, and primary area of potential>",
  "strengths": [
    {{
      "category": "<string: category of strength>",
      "point": "<string: short statement of the strength>",
      "detail": "<string: full context and example from their CV showing this strength>"
    }}
  ],
  "improvements": [
    {{
      "category": "<string: category of improvement>",
      "point": "<string: short statement of the improvement area>",
      "detail": "<string: actionable advice on how to fix this, with references to their CV>"
    }}
  ],
  "keyword_analysis": {{
    "matched": ["list of key terms present in the CV"],
    "missing": ["list of important industry terms/skills that are missing or underrepresented based on their profile or job description"],
    "critical_percentage": <int 0-100 matching score based on target keywords>
  }},
  "section_critique": {{
    "summary": "<string: specific feedback on their professional summary/objective>",
    "experience": "<string: specific feedback on their work history section>",
    "projects_skills": "<string: specific feedback on projects, education, and technical skills sections>"
  }},
  "bullet_rewrites": [
    {{
      "original": "<string: a weak or vague bullet point from their CV>",
      "improved": "<string: a beautifully written, high-impact version using the STAR method, strong verbs, and realistic placeholders for metrics if needed>",
      "rationale": "<string: explanation of what was changed and why it is significantly better>"
    }}
  ]
}}

Be thorough, hyper-specific to the text provided, objective, and realistic. Keep the tone constructive, premium, and highly professional. Ensure your feedback is tailored exactly to the target job description if one is provided.

Language Customization:
Detect the language of the provided Resume/CV (e.g., French, English, Spanish). You MUST write all text values inside the JSON response (including summary, category names, points, details, critiques, bullet rewrites, and rationales) in that same detected language, while keeping the structural JSON keys strictly in English as defined in the schema. For example, if a CV is written in French, the entire feedback output values should be in French.
"""

def review_cv(resume_text: str, job_description: str = "", model: str = DEFAULT_MODEL) -> dict:
    if not groq_client:
        return {
            "error": "Groq API Key is not set. Please add GROQ_API_KEY to your environment or .env file.",
            "status_code": 401
        }
    
    # --- STEP 1: Guardrail Length Checks ---
    try:
        validate_lengths(resume_text, job_description)
    except ValueError as ve:
        return {
            "error": f"Guardrail Alert: {str(ve)}",
            "status_code": 400
        }

    # --- STEP 2: Guardrail Prompt Injection Check ---
    if detect_prompt_injection(resume_text) or (job_description and detect_prompt_injection(job_description)):
        return {
            "error": "Guardrail Alert: Security verification failed. Adversarial instructions or system override markers were detected in the input text.",
            "status_code": 400
        }

    # --- STEP 3: Guardrail Domain Check (Is it a Resume?) ---
    if not verify_resume_domain(resume_text):
        return {
            "error": "Guardrail Alert: The submitted text does not appear to be a professional Resume/CV. Please ensure your document contains details regarding experience, education, contact info, or skills.",
            "status_code": 400
        }

    # --- STEP 4: Retrieve Context (RAG) ---
    retrieved_guides = retrieve_guidelines(resume_text, job_description, limit=3)
    
    # Format the guidelines into the system prompt template
    rag_context_parts = []
    for idx, g in enumerate(retrieved_guides):
        rag_context_parts.append(
            f"Rule {idx+1}: {g['title']}\n"
            f"Category: {g['category']}\n"
            f"Guideline: {g['content']}\n"
            f"Example before: {g['examples']['before']}\n"
            f"Example after: {g['examples']['after']}\n"
        )
    rag_context_str = "\n".join(rag_context_parts)
    sys_prompt = SYS_PROMPT_TEMPLATE.format(rag_context=rag_context_str)

    # --- STEP 5: Build User Prompt ---
    user_content = f"--- RESUME/CV TEXT ---\n{resume_text}\n\n"
    if job_description.strip():
        user_content += f"--- TARGET JOB DESCRIPTION ---\n{job_description}\n\n"
    else:
        user_content += "--- TARGET JOB DESCRIPTION ---\nNot provided. Analyze the CV generally for professional excellence and industry standards based on its apparent domain.\n\n"

    user_content += "Analyze the above resume. Output the strict structured JSON feedback matching the required schema."

    result_text = ""
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content},
            ],
            model=model,
            temperature=0.2, # Low temperature for consistent JSON structure
            response_format={"type": "json_object"} # Force JSON mode on Groq
        )
        
        # --- STEP 6: Parse and Validate Structured Output ---
        result_text = response.choices[0].message.content or ""
        parsed_json = json.loads(result_text)
        
        try:
            # Validate against Pydantic schema
            validated_model = CVReviewSchema.model_validate(parsed_json)
            final_critique = validated_model.model_dump()
        except ValidationError as ve:
            print(f"Pydantic Validation failed, invoking repair guardrail: {ve}")
            # Fallback to sanitization/repair function to guarantee structure is returned
            final_critique = sanitize_and_repair_critique(parsed_json)
            
        # Inject the retrieved RAG guidelines into the critique response so the frontend can display them!
        final_critique["retrieved_context"] = retrieved_guides
        return final_critique
        
    except json.JSONDecodeError as je:
        # If the LLM failed to output JSON, return a repaired dummy structure
        print(f"JSONDecodeError, constructing fallback structure: {je}")
        fallback = sanitize_and_repair_critique({})
        fallback["summary"] = f"Warning: Could not parse LLM output. Raw response: {result_text if result_text else str(je)}"
        fallback["retrieved_context"] = retrieved_guides
        return fallback
    except Exception as e:
        return {
            "error": f"LLM Inference Error: {str(e)}",
            "status_code": 500
        }

if __name__ == "__main__":
    # Test execution
    test_resume = """
    John Doe
    Email: john.doe@email.com
    Software Engineer at Acme Corp (2023 - Present)
    * Worked on python code.
    * Helped team build API endpoints.
    * Did some bug fixing.
    Education: BSc in Computer Science, University of Technology.
    Skills: Python, HTML, CSS.
    """
    print("Testing CV review process with RAG and Guardrails...")
    result = review_cv(test_resume)
    print(json.dumps(result, indent=2))
