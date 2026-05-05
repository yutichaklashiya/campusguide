
import sys
import os
import io
from datetime import datetime

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main_app.chatbot_utils import get_response

def test_rakshabandhan():
    # Set encoding for Windows terminal
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    query = "is there holiday on rakhshabandhan?"
    
    print(f"Query: {query}")
    try:
        response = get_response(query)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rakshabandhan()
