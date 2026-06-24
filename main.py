import io
import traceback
import json
import os
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, ValidationError

from core import review_cv, GROQ_API_KEY
import history_db
from pdf_generator import generate_critique_pdf

# Initialize Database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup phase: Initialize database
    history_db.init_db()
    yield
    # Shutdown phase: No specific cleanup needed for SQLite

class ReviewRequest(BaseModel):
    resume_text: str = Field(min_length=1, description="Raw CV or resume text")
    job_description: str = Field(default="", description="Target job description")
    model: str = Field(default="llama-3.3-70b-versatile", description="Groq model name")
    filename: str = Field(default="Pasted Resume", description="Original filename or label")


class HealthResponse(BaseModel):
    status: str
    api_key_configured: bool
    message: str


class ReviewResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    scores: dict
    summary: str
    strengths: list[dict]
    improvements: list[dict]
    keyword_analysis: dict
    section_critique: dict
    bullet_rewrites: list[dict]
    retrieved_context: list[dict] = []


app = FastAPI(title="AI CV Reviewer API", description="AI powered professional resume critique system", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"},
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health", response_model=HealthResponse)
async def health_status():
    return {
        "status": "healthy",
        "api_key_configured": GROQ_API_KEY is not None,
        "message": "AI CV Reviewer backend is running successfully"
    }

@app.post("/api/review", response_model=ReviewResponse)
async def api_review_cv(request: Request):
    try:
        data = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON payload"}
        )

    try:
        if not isinstance(data, dict):
            return JSONResponse(
                status_code=400,
                content={"error": "JSON body must be an object"}
            )

        payload = ReviewRequest.model_validate(data)
        resume_text = payload.resume_text
        job_description = payload.job_description
        model = payload.model
        filename = payload.filename
        
        if not resume_text.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Resume text cannot be empty"}
            )
            
        result = review_cv(resume_text, job_description, model=model)
        
        if "error" in result:
            status_code = result.get("status_code", 500)
            return JSONResponse(
                status_code=status_code,
                content={"error": result["error"]}
            )
            
        # Extract metadata to save in Persistent Memory History
        overall_score = result.get("overall_score", 0)
        keyword_match = result.get("keyword_analysis", {}).get("critical_percentage", 0)
        
        job_title = "General Critique"
        if job_description.strip():
            # Extract first line of Job Description up to 40 chars for history listing
            first_line = job_description.strip().split("\n")[0]
            job_title = first_line[:40] + ("..." if len(first_line) > 40 else "")
            
        try:
            # Save successful analysis to SQLite history
            critique_id = history_db.save_critique(
                filename=filename,
                job_title=job_title,
                overall_score=overall_score,
                keyword_match=keyword_match,
                cv_text=resume_text,
                job_description=job_description,
                result_json_str=json.dumps(result)
            )
            result["id"] = critique_id
        except Exception as db_err:
            print(f"Failed to save critique to history database: {db_err}")
            # Do not block the API response if database saving fails
            
        return result
        
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal Server Error: {str(e)}"}
        )

@app.get("/api/history")
async def get_critique_history():
    try:
        history = history_db.get_history()
        return history
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Error fetching history: {str(e)}"}
        )

@app.get("/api/history/{critique_id}")
async def get_critique_detail(critique_id: int):
    try:
        critique = history_db.get_critique_by_id(critique_id)
        if not critique:
            return JSONResponse(
                status_code=404,
                content={"error": "Critique record not found"}
            )
        return critique
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Error fetching critique details: {str(e)}"}
        )

@app.get("/api/history/{critique_id}/pdf")
async def get_critique_pdf(critique_id: int):
    try:
        critique = history_db.get_critique_by_id(critique_id)
        if not critique:
            return JSONResponse(
                status_code=404,
                content={"error": "Critique record not found"}
            )
        
        result_data = critique.get("result_json", {})
        filename = critique.get("filename", "Resume_Critique")
        job_title = critique.get("job_title", "General Critique")
        
        # Generate the PDF bytes
        pdf_bytes = generate_critique_pdf(result_data, filename, job_title)
        
        # Clean up output filename
        safe_filename = filename.replace(" ", "_")
        if not safe_filename.lower().endswith(".pdf"):
            safe_filename += ".pdf"
            
        headers = {
            "Content-Disposition": f'attachment; filename="ResumeAI_Report_{safe_filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers=headers
        )
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Error generating PDF report: {str(e)}"}
        )

@app.delete("/api/history/{critique_id}")
async def delete_critique_record(critique_id: int):
    try:
        success = history_db.delete_critique(critique_id)
        if not success:
            return JSONResponse(
                status_code=404,
                content={"error": "Critique record not found or already deleted"}
            )
        return {"message": "Critique record deleted successfully"}
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Error deleting critique: {str(e)}"}
        )

@app.post("/api/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    try:
        # Check file extension
        filename = (file.filename or "").lower()
        if not filename.endswith('.pdf'):
            return JSONResponse(
                status_code=400,
                content={"error": "Uploaded file is not a PDF"}
            )
            
        contents = await file.read()
        
        try:
            from pypdf import PdfReader
            pdf_file = io.BytesIO(contents)
            reader = PdfReader(pdf_file)
            
            text = ""
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            
            text = text.strip()
            
            if not text:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Could not extract any readable text from this PDF file. Please ensure it is not a scanned image."}
                )
                
            return {"filename": file.filename, "text": text}
            
        except ImportError:
            return JSONResponse(
                status_code=500,
                content={"error": "pypdf library is not installed on the server. Please install python dependencies."}
            )
            
    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": f"Error parsing PDF: {str(e)}"}
        )

# Mount the static directory for the web interface
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Starting AI CV Reviewer API Server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
