import json
import os
import re
from typing import List, Dict

# Path to the RAG database
RAG_DB_PATH = os.path.join(os.path.dirname(__file__), "cv_rag_db.json")

def load_rag_db() -> List[Dict]:
    """Loads the CV optimization guidelines from the JSON file."""
    if not os.path.exists(RAG_DB_PATH):
        return []
    try:
        with open(RAG_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading RAG database: {e}")
        return []

def tokenize(text: str) -> set:
    """Tokenizes text into a set of lowercase words (alphanumeric, length > 2)."""
    if not text:
        return set()
    # Replace non-alphanumeric with spaces and lowercase
    text_cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    # Return unique words of length > 2
    return {word for word in text_cleaned.split() if len(word) > 2}

def retrieve_guidelines(resume_text: str, job_description: str = "", limit: int = 3) -> List[Dict]:
    """
    Retrieves the top N most relevant CV guidelines based on keyword overlap
    between the input texts (Resume + Job Description) and the guideline contents.
    """
    guidelines = load_rag_db()
    if not guidelines:
        return []

    # Tokenize input texts
    input_tokens = tokenize(resume_text)
    if job_description:
        input_tokens.update(tokenize(job_description))

    scored_guidelines = []
    for g in guidelines:
        # Tokenize different parts of the guideline
        category_tokens = tokenize(g.get("category", ""))
        title_tokens = tokenize(g.get("title", ""))
        content_tokens = tokenize(g.get("content", ""))
        
        # Calculate overlaps with weights
        # Match in category = 3 pts per word
        # Match in title = 2 pts per word
        # Match in content = 1 pt per word
        cat_overlap = len(category_tokens.intersection(input_tokens))
        title_overlap = len(title_tokens.intersection(input_tokens))
        content_overlap = len(content_tokens.intersection(input_tokens))
        
        score = (cat_overlap * 3) + (title_overlap * 2) + content_overlap
        
        # Add a tiny heuristic bump based on specific keywords in resume
        # e.g., if resume doesn't have numbers/percent, prioritize metrics guideline
        if g["id"] == "impact_quantify":
            has_numbers = any(char.isdigit() for char in resume_text)
            if not has_numbers:
                score += 5 # strong boost for lack of numbers!
                
        # If resume uses "I" or "my" a lot, boost the no pronouns guideline
        if g["id"] == "gen_no_pronouns":
            first_person_count = len(re.findall(r"\b(i|my|we|our|me)\b", resume_text.lower()))
            if first_person_count > 2:
                score += 5

        # If job description is present but resume keywords don't match, boost ATS tailoring
        if g["id"] == "keywords_ats_alignment" and job_description:
            score += 4
            
        scored_guidelines.append((score, g))

    # Sort by score descending and return the guidelines
    scored_guidelines.sort(key=lambda x: x[0], reverse=True)
    
    # Return the selected guidelines as dictionaries
    return [g for score, g in scored_guidelines[:limit]]

if __name__ == "__main__":
    # Test retrieval
    test_cv = "I worked on python website. Assisted team with database bug fixing. My experience is great."
    test_jd = "Looking for a senior React engineer who knows Docker and AWS deployment."
    retrieved = retrieve_guidelines(test_cv, test_jd, limit=3)
    print("Retrieved guidelines:")
    for r in retrieved:
        print(f"- [{r['category'].upper()}] {r['title']}")
