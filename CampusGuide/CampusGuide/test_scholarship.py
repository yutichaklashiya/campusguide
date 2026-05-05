
import sys
import os

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main_app.chatbot_utils import get_response

def test_queries():
    queries = [
        "MYSY scholarship mate eligibility su che?",
        "What is the amount for CMSS scholarship?",
        "SC category na students mate kai scholarship che?",
        "Pragati scholarship scholarship eligibility?"
    ]
    
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    for query in queries:
        print(f"\nQuery: {query}")
        try:
            response = get_response(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_queries()
