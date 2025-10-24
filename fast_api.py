from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from orchestrator import OrchestratorAgent
import asyncio

app = FastAPI(title="Investment Chatbot API")
orchestrator = OrchestratorAgent()

# Define the request body
class QueryRequest(BaseModel):
    user_id: str
    query: str

@app.post("/query")
async def query_agent(request: QueryRequest):
    """
    Accepts JSON:
    {
        "user_id": "kavya123",
        "query": "I am kavya of age 24 years and my income is 30000 and want to start investment"
    }
    """
    user_id = request.user_id
    query = request.query

    try:
        # Orchestrator decides which agent to call
        response = await asyncio.to_thread(orchestrator.handle_query, user_id, query)
        return JSONResponse(content={"status": "success", "response": response})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
