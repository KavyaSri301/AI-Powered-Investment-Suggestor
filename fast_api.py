from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from orchestrator import OrchestratorAgent
import asyncio

app = FastAPI(title="Investment Chatbot API")
orchestrator = OrchestratorAgent()

conversation_history = {}

class QueryRequest(BaseModel):
    user_id: str
    query: str

@app.post("/query")
async def query_agent(request: QueryRequest):
    """
    Accepts JSON:
    {
        "user_id": "kavya123",
        "query": "I am 24 years old with income 20000 and want to start investing."
    }
    Maintains multi-turn context for each user_id.
    """
    user_id = request.user_id
    query = request.query.strip()

    try:
        if user_id not in conversation_history:
            conversation_history[user_id] = []

        conversation_history[user_id].append({"role": "user", "content": query})
        response = await asyncio.to_thread(orchestrator.handle_query, user_id, query)
        conversation_history[user_id].append({"role": "assistant", "content": response})

        return JSONResponse(content={
            "status": "success",
            "agent": response.get("agent"),
            "response": response.get("response"),
            "conversation": conversation_history[user_id]
        })

    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/history/{user_id}")
async def get_history(user_id: str):
    """Fetch conversation history for a user."""
    if user_id in conversation_history:
        return JSONResponse(content={
            "status": "success",
            "conversation": conversation_history[user_id]
        })
    return JSONResponse(content={
        "status": "error",
        "message": "No conversation found for this user."
    }, status_code=404)


@app.delete("/history/{user_id}")
async def clear_history(user_id: str):
    """Clear user conversation history."""
    if user_id in conversation_history:
        del conversation_history[user_id]
        return JSONResponse(content={
            "status": "success",
            "message": f"Conversation cleared for {user_id}."
        })
    return JSONResponse(content={
        "status": "error",
        "message": "No history found to delete."
    }, status_code=404)
