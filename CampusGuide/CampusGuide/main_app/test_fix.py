import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from chatbot_utils import get_chatbot_response

def test_query(query):
    print(f"\nQuery: {query}")
    response = get_chatbot_response(query)
    try:
        print(f"Response: {response}")
    except UnicodeEncodeError:
        print(f"Response: {response.encode('ascii', 'ignore').decode('ascii')}")

if __name__ == "__main__":
    test_query("Tell me about charusat")
    test_query("CHARUSAT full form")
    test_query("When do admission forms open?")
    test_query("faculties in cmpiCA")
    test_query("name all the faculties in cmpica")
    test_query("CMPICA Courses")
    test_query("Is there physiotherapy in charusat??")
    test_query("Tell me fees of it")
    test_query("is there bsc it in charusat?")
    test_query("online bca fees")
    test_query("how can we pay fees?")
    test_query("Is there bba in charusat?")
    test_query("is there course of data science?")
    test_query("is there nursing in charsuat?")
    test_query("charusat cells and their emails")
    test_query("CSPIT clubs")
    test_query("all the clubs at charusat")
    test_query("is there holiday of good friday?")
    test_query("list of holidays")
