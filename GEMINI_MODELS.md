# Gemini Models Available

## Current Configuration

- **Default Model**: `models/gemini-2.5-flash` (cost-efficient, stable)

## Cheapest Options (Recommended for Cost Savings)

1. **models/gemini-2.5-flash-lite** ⭐ Cheapest

   - Lightest model, fastest, lowest cost
   - Input: 1M tokens, Output: 65K tokens
   - Best for: Simple Q&A, basic tasks

2. **models/gemini-2.0-flash-lite-001**

   - Stable version, very cheap
   - Input: 1M tokens, Output: 8K tokens
   - Good balance of cost and performance

3. **models/gemini-2.5-flash** (Currently Used)

   - Stable, fast, cost-efficient
   - Input: 1M tokens, Output: 65K tokens
   - Good for: General purpose, study assistant

4. **models/gemini-2.0-flash-001**
   - Stable, fast
   - Input: 1M tokens, Output: 8K tokens
   - Good alternative to 2.5-flash

## Pro Models (More Expensive - Not Recommended for Cost Savings)

- models/gemini-2.5-pro (most capable, most expensive)
- models/gemini-2.0-pro-exp (experimental)
- models/gemini-3-pro-preview (preview)

## How to Change Model

Edit `app/config/settings.py`:

```python
class GeminiSettings(LLMSettings):
    default_model: str = Field(default="models/gemini-2.5-flash-lite")  # Change here
```

## Model Comparison

| Model                 | Cost     | Speed     | Capability | Best For       |
| --------------------- | -------- | --------- | ---------- | -------------- |
| gemini-2.5-flash-lite | Lowest   | Fastest   | Basic      | Simple tasks   |
| gemini-2.0-flash-lite | Very Low | Very Fast | Good       | General use    |
| gemini-2.5-flash      | Low      | Fast      | Good       | Current choice |
| gemini-2.0-flash      | Low      | Fast      | Good       | Alternative    |
| gemini-2.5-pro        | High     | Slower    | Best       | Complex tasks  |

## Notes

- Flash models are optimized for speed and cost
- Lite models are even cheaper but may have lower quality
- Pro models are more capable but significantly more expensive
- All models support the same API interface
