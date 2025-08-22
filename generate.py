from openai import OpenAI
import os
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import json
from datetime import datetime
import re
import tiktoken
# Note: Qwen tokenizer via transformers removed to avoid dependency conflicts.

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

client = OpenAI(api_key="dpais", base_url="http://localhost:8553/v1/openai")

# Cost configuration for different models (driven by per-token env variables)
# QWEN per-token rates (defaults can be overridden via environment variables)
# For local deployment, cost should be $0 since you're not paying external API fees
_QWEN_INPUT_COST_PER_TOKEN = float(os.environ.get("QWEN_INPUT_COST_PER_TOKEN", "0.0"))
_QWEN_OUTPUT_COST_PER_TOKEN = float(os.environ.get("QWEN_OUTPUT_COST_PER_TOKEN", "0.0"))

MODEL_COSTS = {
    "qwen2.5": {
        # Convert per-token to per-1k to reuse existing math
        "input_cost_per_1k_tokens": _QWEN_INPUT_COST_PER_TOKEN * 1000.0,
        "output_cost_per_1k_tokens": _QWEN_OUTPUT_COST_PER_TOKEN * 1000.0
    },
    "whisper": {
        # For local deployment, cost should be $0 since you're not paying external API fees
        "cost_per_minute": float(os.environ.get("WHISPER_COST_PER_MINUTE", "0.0"))
    }
}

# Commercial API rates for comparison (updated 2025 rates)
COMMERCIAL_RATES = {
    "gpt-5": {
        "input_cost_per_1k_tokens": 0.00125,    # $1.25 per million tokens = $0.00125 per 1K
        "output_cost_per_1k_tokens": 0.01       # $10.00 per million tokens = $0.01 per 1K
    },
    "claude-4-sonnet": {
        "input_cost_per_1k_tokens": 0.003,      # $3.00 per million tokens = $0.003 per 1K (≤200K context)
        "output_cost_per_1k_tokens": 0.015      # $15.00 per million tokens = $0.015 per 1K (≤200K context)
    },
    "claude-4-sonnet-large": {
        "input_cost_per_1k_tokens": 0.006,      # $6.00 per million tokens = $0.006 per 1K (>200K context)
        "output_cost_per_1k_tokens": 0.0225     # $22.50 per million tokens = $0.0225 per 1K (>200K context)
    }
}

# File to store cumulative cost data
COST_LOG_FILE = "cost_log.json"

QWEN_TOKENIZER = None

def load_cost_log():
    """Load cumulative cost data from file"""
    try:
        if os.path.exists(COST_LOG_FILE):
            with open(COST_LOG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading cost log: {e}")
    
    # Return default structure if file doesn't exist or error
    return {
        "total_cost": 0.0,
        "total_tokens": 0,
        "total_requests": 0,
        "last_updated": datetime.now().isoformat()
    }

def save_cost_log(cost_data):
    """Save cumulative cost data to file"""
    try:
        with open(COST_LOG_FILE, 'w') as f:
            json.dump(cost_data, f, indent=2)
    except Exception as e:
        print(f"Error saving cost log: {e}")

def count_tokens_accurate(text, model="gpt-4"):
    """
    Count tokens accurately using tiktoken (OpenAI's tokenizer)
    This provides much more accurate token counts than NLTK word tokenization.
    
    Args:
        text: Text to tokenize
        model: Model to use for tokenization (gpt-4, gpt-3.5-turbo, etc.)
    
    Returns:
        int: Accurate token count
    """
    if not text:
        return 0
    
    # Prefer model-specific tokenizers when available (disabled; using approximate or tiktoken)
    if model.lower().startswith("qwen"):
        # No Qwen tokenizer available; fall back
        return count_tokens_approximate(text)

    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Error with tiktoken, falling back to approximation: {e}")
        return count_tokens_approximate(text)

def count_tokens_approximate(text):
    """
    Improved approximation when tiktoken is not available
    Uses a more sophisticated approach than simple word counting
    """
    if not text:
        return 0
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Count characters and apply tokenization rules
    char_count = len(text)
    
    # Rough approximation: 1 token ≈ 4 characters for English text
    # This is more accurate than word counting
    estimated_tokens = char_count / 4
    
    # Add tokens for special characters and punctuation
    special_chars = len(re.findall(r'[^\w\s]', text))
    estimated_tokens += special_chars * 0.5
    
    return int(estimated_tokens)

def count_tokens_legacy(text):
    """
    Legacy method using NLTK word tokenization
    Kept for backward compatibility but not recommended
    """
    if not text:
        return 0
    
    # Tokenize by words
    word_tokens = word_tokenize(text)
    return len(word_tokens)

def calculate_cost(model_name, input_tokens, output_tokens, audio_duration_minutes=None):
    """
    Calculate cost for a request based on model and token usage
    
    Args:
        model_name: Name of the model (qwen2.5, whisper, etc.)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        audio_duration_minutes: Duration in minutes (for audio models)
    
    Returns:
        dict: Cost breakdown
    """
    if model_name not in MODEL_COSTS:
        return {
            "request_cost": 0.0,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "audio_cost": 0.0,
            "cost_per_1k_input": 0.0,
            "cost_per_1k_output": 0.0
        }
    
    model_costs = MODEL_COSTS[model_name]
    
    # Calculate text generation costs
    input_cost = (input_tokens / 1000) * model_costs.get("input_cost_per_1k_tokens", 0)
    output_cost = (output_tokens / 1000) * model_costs.get("output_cost_per_1k_tokens", 0)
    
    # Calculate audio transcription cost
    audio_cost = 0.0
    if audio_duration_minutes and "cost_per_minute" in model_costs:
        audio_cost = audio_duration_minutes * model_costs["cost_per_minute"]
    
    total_request_cost = input_cost + output_cost + audio_cost
    
    return {
        "request_cost": round(total_request_cost, 6),
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "audio_cost": round(audio_cost, 6),
        "cost_per_1k_input": model_costs.get("input_cost_per_1k_tokens", 0),
        "cost_per_1k_output": model_costs.get("output_cost_per_1k_tokens", 0)
    }

def calculate_commercial_cost(input_tokens, output_tokens, commercial_model="gpt-5"):
    """
    Calculate cost if using commercial APIs for comparison
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        commercial_model: Commercial model to compare against
    
    Returns:
        dict: Commercial cost breakdown
    """
    if commercial_model not in COMMERCIAL_RATES:
        commercial_model = "gpt-5"  # Default fallback
    
    rates = COMMERCIAL_RATES[commercial_model]
    
    input_cost = (input_tokens / 1000) * rates["input_cost_per_1k_tokens"]
    output_cost = (output_tokens / 1000) * rates["output_cost_per_1k_tokens"]
    total_cost = input_cost + output_cost
    
    return {
        "model": commercial_model,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
        "rates": rates
    }

def generate_response(system_prompt, user_input, audio_duration_minutes=None):
    response = client.chat.completions.create(
        model="qwen2.5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        stream=False
    )

    response_content = response.choices[0].message.content
    
    # Use accurate token counting with Qwen tokenizer
    input_tokens = count_tokens_accurate(system_prompt + user_input, model="qwen2.5")
    output_tokens = count_tokens_accurate(response_content, model="qwen2.5")
    total_tokens = input_tokens + output_tokens
    
    # Calculate local cost
    cost_data = calculate_cost("qwen2.5", input_tokens, output_tokens, audio_duration_minutes)
    
    # Calculate commercial comparison costs
    commercial_costs = {}
    for model in ["gpt-5", "claude-4-sonnet", "claude-4-sonnet-large"]:
        commercial_costs[model] = calculate_commercial_cost(input_tokens, output_tokens, model)
    
    # Update cumulative cost log
    cost_log = load_cost_log()
    cost_log["total_cost"] += cost_data["request_cost"]
    cost_log["total_tokens"] += total_tokens
    cost_log["total_requests"] += 1
    cost_log["last_updated"] = datetime.now().isoformat()
    save_cost_log(cost_log)
    
    return {
        'content': response_content,
        'token_usage': {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens
        },
        'cost_data': cost_data,
        'commercial_costs': commercial_costs,
        'cumulative_cost': cost_log["total_cost"]
    }


