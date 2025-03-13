"""
Microsoft Graph FastAPI Server

This FastAPI server provides comprehensive access to Microsoft Graph API functionality, 
enabling AI agents to interact with Microsoft 365 services and data through a chat interface. 
The server uses the Semantic Kernel framework and wraps the GraphAgent class to provide 
a seamless integration with AI workflows.

Key capabilities include:

User Management:
- Retrieve organization user directory
- Search and find users by name or email
- Manage user profiles and information
- Cache user data for efficient lookups

Email Operations:
- Send emails with rich text content
- Read and process inbox messages
- Search emails by subject, body, or sender
- Filter messages based on criteria (read, unread, flagged, etc.)

To Do and Task Management:
- Create task lists
- Add and manage tasks
- Set due dates and priorities
- Track task completion status

The server handles authentication and session management automatically, using Azure AD credentials 
to securely access Microsoft Graph API endpoints. It provides a high-level, REST API interface 
that abstracts away the complexity of direct Microsoft Graph API interactions.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import logging
import json
import uuid
from datetime import datetime

import sys
sys.path.append("./")
sys.path.append("./src")



# Import the Orchestrator
from sk_orchestrator import Orchestrator


from utils.server_data_models import *

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Microsoft Graph Chat API",
    description=__doc__,
    version="1.0.0",
    openapi_tags=[
        {"name": "chat", "description": "Chat with the Microsoft Graph assistant"},
        {"name": "health", "description": "Health check endpoints"},
        {"name": "conversations", "description": "Manage conversation history"}
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to serve static files for frontend
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except Exception as e:
    logger.info(f"No static files directory found: {e}")



# Global orchestrator instance
orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup"""
    global orchestrator
    try:
        orchestrator = Orchestrator()
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        # We'll initialize it on first request if it fails here

# In-memory conversation store (replace with a proper database for production)
conversations: Dict[str, List[Dict[str, Any]]] = {}

@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@app.get("/health/readiness", tags=["health"])
async def readiness_check():
    """Check if the service is ready to accept requests"""
    global orchestrator
    if orchestrator is None:
        try:
            orchestrator = Orchestrator()
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not ready", "reason": str(e)}
            )
    return {"status": "ready"}

@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest):
    """
    Chat with the Microsoft Graph assistant
    
    This endpoint allows you to send a message to the assistant and receive a response.
    The assistant can help with Microsoft Graph operations like managing emails, users,
    tasks, and more.
    
    - **message**: The user message to send to the assistant
    - **user_id**: Optional user ID to identify the sender
    - **conversation_id**: Optional ID to continue an existing conversation
    """
    global orchestrator
    
    # Initialize orchestrator if not already done
    if orchestrator is None:
        orchestrator = Orchestrator()
        try:
            orchestrator = Orchestrator()
            logger.info("Orchestrator initialized for request")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service initialization failed: {str(e)}"
            )
    
    try:
        # Process the chat request
        conversation_id = request.conversation_id or f"conv_{str(uuid.uuid4())[:8]}"
        current_time = datetime.now().isoformat()
        
        # Get existing conversation or create new one
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Store the user message
        conversations[conversation_id].append({
            "role": "user",
            "content": request.message,
            "timestamp": current_time
        })
        
        # Get response from orchestrator
        response = await orchestrator.chat(request.message, conversations[conversation_id])
        
        # Store the assistant response
        conversations[conversation_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": current_time
        })
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            timestamp=current_time
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing your request: {str(e)}"
        )

@app.get("/conversations/{conversation_id}", tags=["conversations"])
async def get_conversation(conversation_id: str):
    """
    Get the history of a conversation by ID
    
    This endpoint returns the full history of messages for a specific conversation.
    
    - **conversation_id**: The ID of the conversation to retrieve
    """
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found"
        )
    
    # Get conversation history
    messages = conversations[conversation_id]
    
    # Format response
    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "message_count": len(messages)
    }

@app.get("/conversations", tags=["conversations"])
async def list_conversations():
    """
    List all conversation IDs
    
    This endpoint returns a list of all conversation IDs.
    """
    conversation_summaries = []
    for conv_id, messages in conversations.items():
        conversation_summaries.append({
            "id": conv_id,
            "message_count": len(messages),
            "last_updated": messages[-1]["timestamp"] if messages else None
        })
    
    return {"conversations": conversation_summaries}

@app.delete("/conversations/{conversation_id}", tags=["conversations"])
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation by ID
    
    This endpoint deletes a specific conversation by its ID.
    
    - **conversation_id**: The ID of the conversation to delete
    """
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found"
        )
    
    # Delete the conversation
    del conversations[conversation_id]
    
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}

@app.post("/conversations/{conversation_id}/clear", tags=["conversations"])
async def clear_conversation(conversation_id: str):
    """
    Clear the message history of a conversation
    
    This endpoint clears all messages from a specific conversation but keeps the conversation ID.
    
    - **conversation_id**: The ID of the conversation to clear
    """
    if conversation_id not in conversations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found"
        )
    
    # Clear the conversation messages
    conversations[conversation_id] = []
    
    return {"status": "success", "message": f"Conversation {conversation_id} cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)