import os
import sys

# Ensure src is in Python path for direct uvicorn execution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import subprocess
import os
from rag import query_assistant

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Mutual Fund RAG Assistant API")

# Enable CORS for the Vite frontend (React defaults to 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    intent: str
    sources: list[str]
    last_updated: str | None = None

@app.post("/query", response_model=QueryResponse)
async def process_query_endpoint(request: QueryRequest):
    try:
        logger.info(f"Received query: {request.query}")
        
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        result = query_assistant(request.query)
        answer = result["answer"]
        
        # Phase 5: Output Validation & Formatting
        if result["intent"] == "Factual_Query":
            # Phase 5 Step 2: Append citations
            if result.get("sources"):
                citations = []
                for idx, source in enumerate(result["sources"], start=1):
                    citations.append(f"[[{idx}]]({source})")
                answer += "\n\nSources: " + ", ".join(citations)
                
            # Phase 5 Step 3: Append last updated footer
            if result.get("last_updated"):
                answer += f"\nLast updated from sources: {result['last_updated']}"
            
        return QueryResponse(
            answer=answer,
            intent=result["intent"],
            sources=result["sources"],
            last_updated=result.get("last_updated")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def run_ingestion_script():
    try:
        logger.info("Starting background ingestion pipeline...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            ["python", "ingestion.py"], 
            capture_output=True, 
            text=True, 
            cwd=script_dir
        )
        if result.returncode != 0:
            logger.error(f"Ingestion failed: {result.stderr}")
        else:
            logger.info("Ingestion completed successfully.")
    except Exception as e:
        logger.error(f"Exception during ingestion: {str(e)}")

@app.post("/trigger-ingestion")
async def trigger_ingestion_endpoint(background_tasks: BackgroundTasks):
    # In a production environment, you should add an API key check here
    # to prevent unauthorized triggers.
    background_tasks.add_task(run_ingestion_script)
    return {"status": "success", "message": "Ingestion pipeline triggered in the background."}
