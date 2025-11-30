"""
Script to list available Gemini models.
Run this to see what models are available for your API key.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables")
    exit(1)

genai.configure(api_key=api_key)

print("Fetching available Gemini models...\n")

try:
    # List all available models
    models = genai.list_models()
    
    print("Available Models:")
    print("=" * 80)
    
    # Filter for generation models (not embeddings)
    generation_models = []
    for model in models:
        # Check if model supports generateContent
        if 'generateContent' in model.supported_generation_methods:
            generation_models.append(model)
            print(f"\nModel Name: {model.name}")
            print(f"Display Name: {model.display_name}")
            print(f"Description: {model.description}")
            print(f"Supported Methods: {', '.join(model.supported_generation_methods)}")
            if hasattr(model, 'input_token_limit'):
                print(f"Input Token Limit: {model.input_token_limit}")
            if hasattr(model, 'output_token_limit'):
                print(f"Output Token Limit: {model.output_token_limit}")
            print("-" * 80)
    
    print(f"\n\nTotal generation models found: {len(generation_models)}")
    print("\nRecommended cheaper models:")
    print("- gemini-1.5-flash (fastest, cheapest)")
    print("- gemini-1.5-flash-latest")
    print("- gemini-pro (older but stable)")
    
except Exception as e:
    print(f"Error listing models: {str(e)}")
    print("\nTrying common model names manually...")
    
    # Try common model names
    common_models = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest", 
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-pro",
        "gemini-pro-latest"
    ]
    
    print("\nTesting common model names:")
    for model_name in common_models:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"✓ {model_name} - Available")
        except Exception as e:
            print(f"✗ {model_name} - Not available: {str(e)[:50]}")

