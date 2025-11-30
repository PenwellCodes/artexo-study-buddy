import uuid
from typing import Dict, List, Optional
from datetime import datetime

import pandas as pd
from database.vector_store import VectorStore
from services.synthesizer import Synthesizer


class ChatService:
    """Service for managing conversation sessions and generating responses with memory."""
    
    def __init__(self, max_context_messages: int = 15):
        """
        Initialize the ChatService.
        
        Args:
            max_context_messages: Maximum number of messages to keep in context window
        """
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self.max_context_messages = max_context_messages
        self.vector_store = VectorStore()
    
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            Session ID (UUID string)
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: The session ID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} does not exist")
        
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of message dictionaries
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} does not exist")
        
        return self.sessions[session_id].copy()
    
    def get_context_window(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get the conversation history limited to the context window.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of message dictionaries (last N messages)
        """
        history = self.get_history(session_id)
        # Return the last max_context_messages
        return history[-self.max_context_messages:] if len(history) > self.max_context_messages else history
    
    def generate_response(self, session_id: str, user_message: str) -> str:
        """
        Generate a response to the user's message using conversation history and vector search.
        
        Args:
            session_id: The session ID
            user_message: The user's message
            
        Returns:
            The assistant's response
        """
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} does not exist")
        
        # Add user message to history
        self.add_message(session_id, "user", user_message)
        
        # Get conversation history for context
        conversation_history = self.get_context_window(session_id)
        
        # Perform vector search on the latest user question
        try:
            search_results = self.vector_store.search(user_message, limit=5)
        except Exception as e:
            # If search fails, use empty DataFrame
            import pandas as pd
            search_results = pd.DataFrame()
            # Log the error but continue with empty context
            import logging
            logging.warning(f"Vector search failed: {str(e)}")
        
        # Generate response with conversation history
        # Exclude the current user message from history (it's the last one)
        history_for_context = conversation_history[:-1] if len(conversation_history) > 1 else []
        
        try:
            response = Synthesizer.generate_response(
                question=user_message,
                context=search_results,
                conversation_history=history_for_context
            )
        except Exception as e:
            # If generation fails, provide a fallback response
            import logging
            logging.error(f"Response generation failed: {str(e)}")
            raise ValueError(f"Failed to generate response: {str(e)}")
        
        # Extract the answer
        answer = response.answer
        
        # Add assistant response to history
        self.add_message(session_id, "assistant", answer)
        
        return answer
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete a conversation session.
        
        Args:
            session_id: The session ID to delete
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

