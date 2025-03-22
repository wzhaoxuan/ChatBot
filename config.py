import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

def get_pinecone_api_key() -> str:
    """Get the Pinecone API key from environment variables."""
    api_key = os.getenv('PINECONE_API_KEY')
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables")
    return api_key

def get_pinecone_environment() -> str:
    """Get the Pinecone environment from environment variables."""
    environment = os.getenv('PINECONE_ENVIRONMENT')
    if not environment:
        raise ValueError("PINECONE_ENVIRONMENT not found in environment variables")
    return environment

def get_pinecone_index_name() -> str:
    """Get the Pinecone index name from environment variables."""
    index_name = os.getenv('PINECONE_INDEX_NAME')
    if not index_name:
        raise ValueError("PINECONE_INDEX_NAME not found in environment variables")
    return index_name

def get_gemini_api_key() -> str:
    """Get the Gemini API key from environment variables."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return api_key

def get_huggingface_api_key() -> str:
    """Get the Hugging Face API key from environment variables."""
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    if not api_key:
        raise ValueError("HUGGINGFACE_API_KEY not found in environment variables")
    return api_key

def validate_environment() -> bool:
    """Validate that all required environment variables are set."""
    required_vars = [
        'PINECONE_API_KEY',
        'PINECONE_ENVIRONMENT',
        'PINECONE_INDEX_NAME',
        'GEMINI_API_KEY',
        'HUGGINGFACE_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True 