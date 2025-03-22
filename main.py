import os
from dotenv import load_dotenv
import streamlit.web.bootstrap as bootstrap
import sys

def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        'PINECONE_API_KEY',
        'PINECONE_ENVIRONMENT',
        'GEMINI_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease ensure these variables are set in your .env file")
        return False
    return True

def main():
    # Load environment variables
    load_dotenv()
    
    # Validate environment variables
    if not validate_environment():
        sys.exit(1)
    
    # Run the Streamlit app from chat.py
    bootstrap.run("chat.py", "", [], {})

if __name__ == "__main__":
    main() 