import os
import uuid
import asyncio
import json
from typing import Optional, List
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions.session import Session
from google.adk.events.event import Event
from google.genai import types
from config import MEMORY_USER_ID

MEMORY_FILE = "memory.json"

# google adk memory service
memory_service = InMemoryMemoryService()

# local cache to support get_all_memories and persistence
_all_memories_cache: List[dict] = []

def _load_memory_from_file():
    """Loads memories from the JSON file into the local cache."""
    global _all_memories_cache
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                _all_memories_cache = json.load(f)
        except Exception as e:
            print(f"⚠️ [MEMORY] Failed to load {MEMORY_FILE}: {e}")
            _all_memories_cache = []

def _save_memory_to_file():
    """Saves the local cache to the JSON file."""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(_all_memories_cache, f, indent=4)
    except Exception as e:
        print(f"⚠️ [MEMORY] Failed to save to {MEMORY_FILE}: {e}")

# load memories on startup
_load_memory_from_file()

# flag to track if service has been initialized
_service_initialized = False

async def _initialize_service():
    """Populates the InMemoryMemoryService with loaded memories."""
    global _service_initialized
    if _service_initialized:
        return
    
    for mem in _all_memories_cache:
        text = mem.get("text", "")
        if text:
            session = Session(
                app_name="aiops",
                user_id=MEMORY_USER_ID,
                id=f"mem-{uuid.uuid4().hex[:8]}"
            )
            event = Event(
                author="user",
                content=types.Content(role="user", parts=[types.Part(text=text)])
            )
            session.events.append(event)
            await memory_service.add_session_to_memory(session)
    
    _service_initialized = True

# don't initialize at module import time - will be done lazily when needed

async def save_memory(text: str, metadata: Optional[dict] = None):
    """
    Saves a memory for the user using ADK's InMemoryMemoryService and persists to JSON.
    """
    try:
        # Ensure service is initialized
        await _initialize_service()
        
        # 1. Add to ADK memory service (for vector search)
        session = Session(
            app_name="aiops",
            user_id=MEMORY_USER_ID,
            id=f"mem-{uuid.uuid4().hex[:8]}"
        )
        event = Event(
            author="user",
            content=types.Content(role="user", parts=[types.Part(text=text)])
        )
        session.events.append(event)
        await memory_service.add_session_to_memory(session)
        
        # 2. add to local cache and persist to JSON
        memory_entry = {
            "id": str(uuid.uuid4()),
            "text": text,
            "metadata": metadata or {},
            "timestamp": str(asyncio.get_event_loop().time()) # Simple timestamp
        }
        _all_memories_cache.append(memory_entry)
        _save_memory_to_file()
        
        print(f"💾 [MEMORY] Persisted to {MEMORY_FILE}")
        return f"Memory saved and persisted: {text}"
    except Exception as e:
        return f"Error saving memory: {str(e)}"

async def search_memory(query: str, limit: int = 5):
    """
    Searches for relevant memories using ADK's InMemoryMemoryService.
    """
    try:
        # ensure service is initialized
        await _initialize_service()
        
        response = await memory_service.search_memory(
            app_name="aiops",
            user_id=MEMORY_USER_ID,
            query=query
        )
        
        if not response or not response.memories:
            return {"status": "success", "memories": "", "count": 0}
        
        # extract text from MemoryEntry objects
        extracted_memories = []
        for entry in response.memories:
            if entry.content and entry.content.parts:
                text_parts = [p.text for p in entry.content.parts if p.text]
                if text_parts:
                    extracted_memories.append(" ".join(text_parts))
        
        # limit results
        results = extracted_memories[:limit]
        memories_text = "\n".join([f"- {m}" for m in results])
        
        return {
            "status": "success",
            "memories": memories_text,
            "count": len(results)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_all_memories():
    """
    Retrieves all memories from the local cache.
    """
    if not _all_memories_cache:
        return "No memories found."
    
    memories_text = "\n".join([f"- {m['text']}" for m in _all_memories_cache])
    return memories_text
