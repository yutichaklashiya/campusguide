import sys
import os
# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_utils import search_all_sheets, get_keywords, normalize_question

def test_bca_format():
    question = "BCA ni scholarship maate info aap"
    print(f"Question: {question}")
    
    q_norm = normalize_question(question)
    print(f"Normalized: {q_norm}")
    
    keywords = get_keywords(q_norm)
    print(f"Keywords: {keywords}")
    
    matches = search_all_sheets(question)
    print("\nMatches:")
    for i, m in enumerate(matches[:3]): # Top 3
        print(f"{i+1}. Sheet: {m['sheet']}, Score: {m['score']}")
        print(f"   Text: {m['row_text'][:200]}...")
        print("-" * 20)

if __name__ == "__main__":
    test_bca_format()
