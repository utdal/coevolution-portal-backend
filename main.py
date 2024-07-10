from fastapi import FastAPI, Response
import worker

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/jobs/{job_id}/status")
async def job_status(job_id: str):
    job = worker.celery.AsyncResult(job_id)
    return {"status": job.state}

@app.get("/jobs/{job_id}/result")
async def job_result(job_id: str, response: Response):
    job = worker.celery.AsyncResult(job_id)
    if job.state == 'SUCCESS':
        return job.result
    
    response.status_code = 202
    return {"status": job.state}


@app.post("/api/msa")
async def generate_msa(seq: str):
    job = worker.generate_msa_task.delay(seq)
    return {"job_id": job.id}

@app.post("/api/di")
async def get_DI_pairs(msa: str):
    job = worker.get_DI_pairs.delay(msa)
    return {"job_id": job.id}