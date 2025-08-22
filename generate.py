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

# Local deployment - no costs since models run on your hardware

# Commercial API rates for comparison (2025 rates)
COMMERCIAL_RATES = {
    "gpt-5": {
        "cost_per_token": 0.005625  # Average of input ($0.00125/1K) and output ($0.01/1K) = $0.005625 per token
    },
    "claude-4-sonnet": {
        "cost_per_token": 0.009     # Average of input ($0.003/1K) and output ($0.015/1K) = $0.009 per token
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
        dict: Cost breakdown (simplified for local deployment)
    """
    # For local deployment, cost is always $0
    return {
        "request_cost": 0.0
    }

def calculate_commercial_cost(total_tokens, commercial_model="gpt-5"):
    """
    Calculate cost if using commercial APIs for comparison
    
    Args:
        total_tokens: Total number of tokens (input + output)
        commercial_model: Commercial model to compare against
    
    Returns:
        dict: Commercial cost breakdown
    """
    if commercial_model not in COMMERCIAL_RATES:
        commercial_model = "gpt-5"  # Default fallback
    
    rates = COMMERCIAL_RATES[commercial_model]
    total_cost = total_tokens * rates["cost_per_token"]
    
    return {
        "model": commercial_model,
        "total_cost": round(total_cost, 6),
        "cost_per_token": rates["cost_per_token"]
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
    for model in ["gpt-5", "claude-4-sonnet"]:
        commercial_costs[model] = calculate_commercial_cost(total_tokens, model)
    
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


