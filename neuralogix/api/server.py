import os
import uuid
import shutil
import tempfile
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from neuralogix.pilots.pilot_i.evaluate import PilotIEvaluator
from neuralogix.core.packs.loader import PackLoader

app = FastAPI(title="NeuraLogix VOR API", version="0.7.2")

# Temporary directory for results
TEMP_RESULTS_DIR = os.path.join(tempfile.gettempdir(), "neuralogix_api_results")
os.makedirs(TEMP_RESULTS_DIR, exist_ok=True)

class QARequest(BaseModel):
    corpus: List[Dict[str, str]]
    questions: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    seed: int = 42
    fast: bool = False

def cleanup_job(path: str):
    """Cleanup temp files after a delay or certain conditions."""
    if os.path.exists(path):
        if os.path.isdir(path): shutil.rmtree(path)
        else: os.remove(path)

@app.get("/health")
def health():
    return {"status": "healthy", "version": "0.7.1", "mode": "VOR"}

@app.post("/v1/qa/run")
async def run_qa_inline(
    background_tasks: BackgroundTasks,
    request: QARequest
):
    """Run QA with inline JSON request."""
    run_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_RESULTS_DIR, run_id)
    os.makedirs(job_dir, exist_ok=True)
    
    try:
        pack_path = job_dir
        corpus_path = os.path.join(pack_path, "corpus.jsonl")
        questions_path = os.path.join(pack_path, "questions.jsonl")
        
        # Write corpus
        with open(corpus_path, "w") as f:
            for doc in request.corpus:
                f.write(json.dumps(doc) + "\n")
        
        # Write questions
        with open(questions_path, "w") as f:
            for q in request.questions:
                f.write(json.dumps(q) + "\n")
        
        # Compute actual SHA256 hashes
        import hashlib
        def compute_sha256(path):
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        
        corpus_hash = compute_sha256(corpus_path)
        questions_hash = compute_sha256(questions_path)
        
        manifest = {
            "pack_name": request.metadata.get("pack_name", "api_run") if request.metadata else "api_run",
            "version": "1.0.0",
            "files": [
                {"path": "corpus.jsonl", "sha256": corpus_hash},
                {"path": "questions.jsonl", "sha256": questions_hash}
            ]
        }
        with open(os.path.join(pack_path, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        evaluator = PilotIEvaluator(pack_path)
        report = evaluator.run_all(fast=request.fast, seeds=[request.seed])
        
        pack_name = evaluator.pack_data["metadata"]["pack_name"]
        summary_file = f"results/pilot_i_{pack_name}.summary.json"
        
        with open(summary_file, "r") as f:
            summary_data = json.load(f)
            
        background_tasks.add_task(cleanup_job, job_dir)

        return {
            "run_id": run_id,
            "summary": summary_data,
            "evidence_url": f"/v1/artifacts/{run_id}/evidence" 
        }

    except Exception as e:
        background_tasks.add_task(cleanup_job, job_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/qa/upload")
async def run_qa_upload(
    background_tasks: BackgroundTasks,
    pack_zip: UploadFile = File(...),
    seed: int = 42,
    fast: bool = False
):
    """Run QA with ZIP pack upload."""
    run_id = str(uuid.uuid4())
    job_dir = os.path.join(TEMP_RESULTS_DIR, run_id)
    os.makedirs(job_dir, exist_ok=True)
    
    try:
        import zipfile
        import io
        zip_data = await pack_zip.read()
        with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
            z.extractall(job_dir)
        pack_path = job_dir

        evaluator = PilotIEvaluator(pack_path)
        report = evaluator.run_all(fast=fast, seeds=[seed])
        
        pack_name = evaluator.pack_data["metadata"]["pack_name"]
        summary_file = f"results/pilot_i_{pack_name}.summary.json"
        
        with open(summary_file, "r") as f:
            summary_data = json.load(f)
            
        background_tasks.add_task(cleanup_job, job_dir)

        return {
            "run_id": run_id,
            "summary": summary_data,
            "evidence_url": f"/v1/artifacts/{run_id}/evidence" 
        }

    except Exception as e:
        background_tasks.add_task(cleanup_job, job_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/artifacts/{run_id}/evidence")
def get_evidence(run_id: str):
    return {"message": "Evidence is stored in the results/ directory on the server."}
