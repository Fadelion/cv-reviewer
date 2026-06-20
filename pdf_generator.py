import io
from datetime import datetime
from fpdf import FPDF
from typing import Dict, Any, List

def clean_text(text: str) -> str:
    """Sanitizes text to avoid Latin-1 encoding issues in standard PDF fonts."""
    if not text:
        return ""
    # Map common unicode characters to standard ASCII/Latin-1 equivalents
    replacements = {
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "*",
        "\u200b": "",
        "\xa0": " ",
        "\u2026": "...",
        "\xe9": "e",  # common accents
        "\xe0": "a",
        "\xe8": "e",
        "\xf9": "u",
        "\xe2": "a",
        "\xea": "e",
        "\xee": "i",
        "\xf4": "o",
        "\xfb": "u",
        "\xeb": "e",
        "\xef": "i",
        "\xfc": "u",
        "\xe7": "c",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Encode as latin-1, replace unsupported characters with spaces or ignore to prevent crashes
    return text.encode("latin-1", "replace").decode("latin-1")

class ResumeCritiquePDF(FPDF):
    def __init__(self, filename: str, job_title: str):
        super().__init__()
        self.filename = clean_text(filename)
        self.job_title = clean_text(job_title)
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Draw a top brand accent bar
        self.set_fill_color(80, 70, 229) # Indigo
        self.rect(0, 0, 210, 4, "F")
        
        # Header text
        self.set_font("helvetica", "B", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, "ResumeAI Critique & ATS Optimization Report", align="L")
        self.cell(0, 5, datetime.now().strftime("%Y-%m-%d"), align="R", new_x="LMARGIN", new_y="NEXT")
        # Separator line
        self.set_draw_color(220, 224, 230)
        self.line(15, 21, 195, 21)
        self.ln(5)

    def footer(self):
        # Position at 15 mm from bottom
        self.set_y(-15)
        # Separator line
        self.set_draw_color(220, 224, 230)
        self.line(15, 282, 195, 282)
        
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        # Print page number and footer note
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="R")
        self.set_x(15)
        self.cell(0, 10, "Powered by ResumeAI - Structured Evaluation Engine", align="L")

    def chapter_title(self, label: str, icon_color=(80, 70, 229)):
        """Creates a styled section header with colored left bar indicator."""
        self.ln(4)
        current_y = self.get_y()
        # Draw colored vertical accent bar
        self.set_fill_color(*icon_color)
        self.rect(15, current_y, 3, 7, "F")
        
        self.set_x(20)
        self.set_font("helvetica", "B", 13)
        self.set_text_color(33, 37, 41)
        self.cell(0, 7, clean_text(label), new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

def generate_critique_pdf(data: Dict[str, Any], filename: str, job_title: str) -> bytes:
    pdf = ResumeCritiquePDF(filename, job_title)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. Title Banner
    pdf.set_y(25)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 10, "CV EVALUATION REPORT", new_x="LMARGIN", new_y="NEXT")
    
    # Metadata Subtitle Card
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(80, 70, 229) # Indigo
    pdf.cell(32, 6, "DOCUMENT NAME: ")
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 6, pdf.filename, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(80, 70, 229)
    pdf.cell(32, 6, "TARGET ROLE: ")
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(33, 37, 41)
    pdf.cell(0, 6, pdf.job_title, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(4)
    
    # 2. Score Breakdown Layout
    overall_score = data.get("overall_score", 0)
    scores = data.get("scores", {})
    
    # Determine color theme based on score
    if overall_score >= 80:
        score_color = (20, 160, 90)  # Emerald
        score_text = "Competitive CV"
    elif overall_score >= 50:
        score_color = (220, 130, 20) # Amber
        score_text = "Good Base (Updates Advised)"
    else:
        score_color = (210, 40, 80)  # Rose
        score_text = "Critical Updates Needed"
        
    # Draw Score Box Card
    pdf.set_fill_color(245, 246, 250)
    pdf.set_draw_color(220, 224, 230)
    pdf.rect(15, pdf.get_y(), 180, 30, "FD")
    
    # Overall Score Text in Card
    pdf.set_y(pdf.get_y() + 4)
    pdf.set_x(20)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 110, 120)
    pdf.cell(50, 5, "OVERALL CV CALIBER", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(20)
    pdf.set_font("helvetica", "B", 18)
    pdf.set_text_color(*score_color)
    pdf.cell(50, 8, f"{overall_score} / 100", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_x(20)
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(50, 5, score_text)
    
    # Draw Component Scores in the same card (Shift x and draw next to overall score)
    pdf.set_y(pdf.get_y() - 13)
    
    categories = [
        ("Impact", scores.get("impact", 0)),
        ("Presentation", scores.get("presentation", 0)),
        ("Experience Quality", scores.get("experience", 0)),
        ("Keyword Fit", scores.get("keywords", 0))
    ]
    
    # Format component scores on the right side of the card
    start_x = 85
    col_width = 50
    for idx, (cat_name, cat_val) in enumerate(categories):
        # Calculate grid position
        col = idx % 2
        row = idx // 2
        x_pos = start_x + (col * col_width)
        y_pos = pdf.get_y() + (row * 10)
        
        pdf.set_xy(x_pos, y_pos)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(80, 90, 100)
        pdf.cell(col_width - 12, 4, clean_text(cat_name))
        
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(33, 37, 41)
        pdf.cell(10, 4, f"{cat_val}%", align="R", new_x="LMARGIN", new_y="NEXT")
        
        # Mini progress bar
        pdf.set_xy(x_pos, y_pos + 4.5)
        pdf.set_draw_color(220, 224, 230)
        pdf.set_fill_color(230, 232, 240)
        pdf.rect(x_pos, y_pos + 4.5, col_width - 2, 2, "FD")
        
        # Fill mini progress bar
        pdf.set_fill_color(80, 70, 229)
        pdf.rect(x_pos, y_pos + 4.5, (col_width - 2) * (cat_val / 100.0), 2, "F")
        
    pdf.set_y(pdf.get_y() + 8)
    pdf.ln(4)
    
    # 3. Executive AI Evaluation
    pdf.chapter_title("Executive AI Evaluation", icon_color=(80, 70, 229))
    summary = data.get("summary", "")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5, clean_text(summary))
    pdf.ln(2)
    
    # 4. ATS Keyword Gap Finder
    keyword_analysis = data.get("keyword_analysis", {})
    critical_percent = keyword_analysis.get("critical_percentage", 0)
    
    pdf.chapter_title(f"ATS Keyword Gap Finder (Match Score: {critical_percent}%)", icon_color=(20, 160, 90))
    
    # Match percentage info
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, "Note: Missing keywords represent crucial industry competencies expected in candidate profiles for this role.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    # Column list of Matched vs Missing — true two-column layout
    start_y = pdf.get_y()
    
    # Left column: Matched keywords
    pdf.set_xy(15, start_y)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(20, 160, 90)  # Success Green
    # Keep cursor X at 15 after header using ln() instead of new_y="NEXT"
    pdf.cell(85, 5, "Matched Competencies")
    pdf.ln(5)
    pdf.set_x(15)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    
    matched_list = keyword_analysis.get("matched", [])
    if matched_list:
        matched_str = ", ".join(matched_list)
        pdf.multi_cell(85, 4.5, clean_text(matched_str))
    else:
        pdf.cell(85, 5, "No major matches detected.")
        pdf.ln(5)
        
    end_left_y = pdf.get_y()
        
    # Right column: Missing keywords — reset Y to start_y to align with left header
    right_col_x = 110
    
    pdf.set_xy(right_col_x, start_y)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(210, 40, 80)  # Danger Red
    # Use cell with new_x="RIGHT" so cursor stays at right_col_x after the header
    pdf.cell(85, 5, "Missing Critical Keywords")
    pdf.ln(5)
    pdf.set_x(right_col_x)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)
    
    missing_list = keyword_analysis.get("missing", [])
    if missing_list:
        missing_str = ", ".join(missing_list)
        pdf.multi_cell(85, 4.5, clean_text(missing_str))
    else:
        pdf.cell(85, 5, "All critical keywords present!")
        pdf.ln(5)
        
    end_right_y = pdf.get_y()
    
    # Advance past whichever column was longer
    pdf.set_y(max(end_left_y, end_right_y) + 4)
    pdf.ln(2)
    
    # 5. Section Critique
    pdf.chapter_title("Section-by-Section Critique", icon_color=(220, 130, 20))
    section_critique = data.get("section_critique", {})
    
    sections = [
        ("Summary / Profile Objective", section_critique.get("summary", "No summary feedback provided.")),
        ("Professional Work History", section_critique.get("experience", "No experience feedback provided.")),
        ("Projects, Education & Technical Skills", section_critique.get("projects_skills", "No skills feedback provided."))
    ]
    
    for title, feedback in sections:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(80, 70, 229)
        pdf.cell(0, 5, clean_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 4.5, clean_text(feedback))
        pdf.ln(2)
        
    pdf.ln(2)
    
    # 6. Strengths vs Improvements
    pdf.chapter_title("Key Feedback Highlights", icon_color=(80, 70, 229))
    
    # Strengths Header
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(20, 160, 90) # Green
    pdf.cell(0, 6, "KEY STRENGTHS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(220, 224, 230)
    
    strengths = data.get("strengths", [])
    if strengths:
        for idx, item in enumerate(strengths):
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(33, 37, 41)
            # Prefix Category
            cat_text = f"[{item.get('category', '').upper()}] "
            pdf.cell(pdf.get_string_width(cat_text), 5, clean_text(cat_text))
            
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 5, clean_text(item.get("point", "")), new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 4, clean_text(item.get("detail", "")))
            pdf.ln(1.5)
    else:
        pdf.set_font("helvetica", "", 9.5)
        pdf.cell(0, 5, "No specific strengths highlighted.", new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(3)
    
    # Improvements Header
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(210, 40, 80) # Red
    pdf.cell(0, 6, "AREAS FOR IMPROVEMENT", new_x="LMARGIN", new_y="NEXT")
    
    improvements = data.get("improvements", [])
    if improvements:
        for idx, item in enumerate(improvements):
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(33, 37, 41)
            cat_text = f"[{item.get('category', '').upper()}] "
            pdf.cell(pdf.get_string_width(cat_text), 5, clean_text(cat_text))
            
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 5, clean_text(item.get("point", "")), new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 4, clean_text(item.get("detail", "")))
            pdf.ln(1.5)
    else:
        pdf.set_font("helvetica", "", 9.5)
        pdf.cell(0, 5, "No immediate areas for improvement specified.", new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(4)
    
    # 7. STAR Bullet Rewrites
    bullet_rewrites = data.get("bullet_rewrites", [])
    if bullet_rewrites:
        pdf.chapter_title("STAR Bullet Point Optimizer", icon_color=(80, 70, 229))
        
        pdf.set_font("helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, "Optimized sentences below are designed to highlight impact using action verbs and STAR criteria.", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        for idx, bullet in enumerate(bullet_rewrites):
            # Outer box border
            start_y = pdf.get_y()
            
            # To draw a nice border card around each rewrite, we calculate cell heights
            # But simpler and more robust in FPDF is drawing colored blocks:
            pdf.set_fill_color(252, 242, 242) # Weak red background for Original
            pdf.rect(15, start_y, 180, 1, "F")
            
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(210, 40, 80)
            pdf.cell(20, 5, "Original: ")
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(160, 4.5, f"\"{clean_text(bullet.get('original', ''))}\"")
            
            pdf.ln(1)
            
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(20, 160, 90)
            pdf.cell(20, 5, "Optimized: ")
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(33, 37, 41)
            pdf.multi_cell(160, 4.5, f"\"{clean_text(bullet.get('improved', ''))}\"")
            
            pdf.ln(1)
            
            pdf.set_font("helvetica", "B", 9.5)
            pdf.set_text_color(80, 70, 229)
            pdf.cell(20, 5, "Rationale: ")
            pdf.set_font("helvetica", "I", 8.5)
            pdf.set_text_color(80, 90, 100)
            pdf.multi_cell(160, 4, clean_text(bullet.get("rationale", "")))
            
            pdf.ln(4)
            # Separator line
            pdf.set_draw_color(235, 238, 242)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

    # Write to bytes stream and return bytes
    # FPDF2 allows writing output directly to a bytes-like object or file path.
    # Passing no arguments to output() returns the byte string in fpdf2
    pdf_bytes = pdf.output()
    return pdf_bytes
