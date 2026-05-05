
import sys
import os
import io

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main_app.chatbot_utils import get_response

def test_queries():
    # Set encoding for Windows terminal
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    queries = [
        "How may I issue a book?",
        "What is the fine if I submit book late?",
        "What are the library timings?"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = get_response(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_queries()
