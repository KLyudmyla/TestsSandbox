import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agent import DocumentSearchAgent

app = FastAPI(
    title="LLM RAG Agent Service",
    description="A simple FastAPI service wrapper around our Document Search Agent for testing purposes."
)

# Initialize the agent. It will look for OPENAI_API_KEY in environment variables.
# We do this at the module level so the agent persists across API calls.
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set!")

agent = DocumentSearchAgent(openai_api_key=api_key)

# Mock corporate knowledge base to preload into our in-memory vector store on startup
MOCK_KNOWLEDGE_BASE = [
    "Company remote work policy: Employees can work remotely up to 3 days a week.",
    "The office kitchen is cleared every Friday at 4 PM. Do not leave your food there.",
    "Our primary tech stack consists of Python, FastAPI, and React.",
    "To request a new laptop, fill out the form IT-01 on the internal portal."
]


@app.on_event("startup")
def preload_documents():
    """
    Preloads mock documents into the agent's vector store when the server starts.
    """
    print("Preloading mock documents into the vector store...")
    agent.upload_documents(MOCK_KNOWLEDGE_BASE)
    print("Documents successfully loaded!")


# Define the request structure using Pydantic for validation
class QueryRequest(BaseModel):
    question: str


# Define the response structure
class QueryResponse(BaseModel):
    answer: str


@app.post("/query", response_model=QueryResponse)
def ask_agent(request: QueryRequest):
    """
    Endpoint to send questions to the LLM agent.
    The agent will search through documents and formulate an answer.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # Call our agent's ask method
        agent_response = agent.ask(user_input=request.question)
        return QueryResponse(answer=agent_response["output"])
    except Exception as e:
        # Handle unexpected errors gracefully
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")