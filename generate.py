from openai import OpenAI
import os
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

client = OpenAI(api_key="dpais", base_url="http://localhost:8553/v1/openai")


def count_tokens(text):
    """
    Count tokens in text using NLTK word tokenization.
    This provides a reasonable approximation of token count.
    """
    if not text:
        return 0
    
    # Tokenize by words
    word_tokens = word_tokenize(text)
    return len(word_tokens)


def generate_response(system_prompt, user_input):
    response = client.chat.completions.create(
        model="qwen2.5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        stream=False
    )

    response_content = response.choices[0].message.content
    
    # Calculate token usage
    input_tokens = count_tokens(system_prompt) + count_tokens(user_input)
    output_tokens = count_tokens(response_content)
    total_tokens = input_tokens + output_tokens
    
    return {
        'content': response_content,
        'token_usage': {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens
        }
    }


