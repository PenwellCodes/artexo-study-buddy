from typing import Any, Dict, List, Type

import google.generativeai as genai
import instructor
from anthropic import Anthropic
from openai import OpenAI
from pydantic import BaseModel

from config.settings import get_settings


class LLMFactory:
    def __init__(self, provider: str):
        self.provider = provider
        self.settings = getattr(get_settings(), provider)
        if provider == "gemini":
            genai.configure(api_key=self.settings.api_key)
        self.client = self._initialize_client()

    def _initialize_client(self) -> Any:
        client_initializers = {
            "openai": lambda s: instructor.from_openai(OpenAI(api_key=s.api_key)),
            "anthropic": lambda s: instructor.from_anthropic(
                Anthropic(api_key=s.api_key)
            ),
            "llama": lambda s: instructor.from_openai(
                OpenAI(base_url=s.base_url, api_key=s.api_key),
                mode=instructor.Mode.JSON,
            ),
            "gemini": lambda s: self._init_gemini_client(s),
        }

        initializer = client_initializers.get(self.provider)
        if initializer:
            return initializer(self.settings)
        raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _init_gemini_client(self, settings):
        """Initialize Gemini client, trying instructor first, then falling back to native API."""
        try:
            # Try to use instructor if it supports Gemini
            if hasattr(instructor, 'from_google'):
                return instructor.from_google(
                    genai.GenerativeModel(model_name=settings.default_model),
                    mode=instructor.Mode.JSON,
                )
        except (AttributeError, Exception):
            pass
        # Fall back to native Gemini API
        return genai.GenerativeModel(model_name=settings.default_model)

    def create_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Any:
        if self.provider == "gemini":
            return self._create_gemini_completion(response_model, messages, **kwargs)
        else:
            completion_params = {
                "model": kwargs.get("model", self.settings.default_model),
                "temperature": kwargs.get("temperature", self.settings.temperature),
                "max_retries": kwargs.get("max_retries", self.settings.max_retries),
                "max_tokens": kwargs.get("max_tokens", self.settings.max_tokens),
                "response_model": response_model,
                "messages": messages,
            }
            return self.client.chat.completions.create(**completion_params)
    
    def _create_gemini_completion(
        self, response_model: Type[BaseModel], messages: List[Dict[str, str]], **kwargs
    ) -> Any:
        """Create completion using Gemini API."""
        # Check if client is an instructor-wrapped client
        if hasattr(self.client, 'create'):
            try:
                # Try instructor-style API
                prompt = self._messages_to_gemini_prompt(messages)
                return self.client.create(
                    response_model=response_model,
                    prompt=prompt,
                    temperature=kwargs.get("temperature", self.settings.temperature),
                )
            except Exception:
                pass
        
        # Use native Gemini API with structured output
        import json
        prompt = self._build_gemini_prompt_with_schema(messages, response_model)
        
        generation_config = {
            "temperature": kwargs.get("temperature", self.settings.temperature),
        }
        if kwargs.get("max_tokens") or self.settings.max_tokens:
            generation_config["max_output_tokens"] = kwargs.get("max_tokens", self.settings.max_tokens)
        
        response = self.client.generate_content(
            prompt,
            generation_config=generation_config,
        )
        
        # Parse JSON response and validate against Pydantic model
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        try:
            data = json.loads(response_text)
            return response_model(**data)
        except (json.JSONDecodeError, Exception) as e:
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return response_model(**data)
            raise ValueError(f"Failed to parse Gemini response: {str(e)}")
    
    def _messages_to_gemini_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt string for Gemini."""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")
        return "".join(prompt_parts)
    
    def _build_gemini_prompt_with_schema(
        self, messages: List[Dict[str, str]], response_model: Type[BaseModel]
    ) -> str:
        """Build a prompt with JSON schema for structured output."""
        import json
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)
        
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(content)
            elif role == "user":
                prompt_parts.append(content)
            elif role == "assistant":
                prompt_parts.append(content)
        
        full_prompt = "\n\n".join(prompt_parts)
        full_prompt += f"\n\nPlease respond with a valid JSON object matching this schema:\n{schema_str}"
        return full_prompt
