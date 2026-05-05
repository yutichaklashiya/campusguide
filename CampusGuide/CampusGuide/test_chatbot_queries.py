import sys
import io

# Set stdout to use UTF-8 encoding for printing emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from main_app.chatbot_utils import get_response

def test_charusat_query():
    print("Testing 'charusat' query:")
    response = get_response("charusat")
    print(f"Response: {response}")
    if "private university" in response.lower() and "2009" in response:
        print("SUCCESS: University info found!")
    else:
        print("FAILURE: Incorrect response for 'charusat'")

def test_charusat_caps_query():
    print("\nTesting 'CHARUSAT' query:")
    response = get_response("CHARUSAT")
    print(f"Response: {response}")
    if "private university" in response.lower() and "2009" in response:
        print("SUCCESS: University info found!")
    else:
        print("FAILURE: Incorrect response for 'CHARUSAT'")

def test_tell_about_charusat_query():
    print("\nTesting 'tell me about charusat' query:")
    response = get_response("tell me about charusat")
    print(f"Response: {response}")
    if "private university" in response.lower() and "2009" in response:
        print("SUCCESS: University info found!")
    else:
        print("FAILURE: Incorrect response for 'tell me about charusat'")

def test_sports_query():
    print("\nTesting 'sports event' query:")
    response = get_response("sports event")
    print(f"Response: {response}")
    # The Spoural summary should be returned
    if "Spoural'26" in response and "Cricket" in response:
         print("SUCCESS: Sports events found!")
    else:
         print("FAILURE: Incorrect response for 'sports event'")

def test_cricket_query():
    print("\nTesting 'cricket' query:")
    response = get_response("cricket")
    print(f"Response: {response}")
    if "11-15 members" in response:
         print("SUCCESS: Correct cricket info found!")
    else:
         print("FAILURE: Incorrect response for 'cricket'")

def test_football_query():
    print("\nTesting 'football' query:")
    response = get_response("football")
    print(f"Response: {response}")
    if "6A Side (10-12 members)" in response and "5A Side (10-12 members)" in response:
         print("SUCCESS: Correct football info found!")
    else:
         print("FAILURE: Incorrect response for 'football'")

def test_frisbee_query():
    print("\nTesting 'frisbee' query:")
    response = get_response("frisbee")
    print(f"Response: {response}")
    if "12 members" in response:
         print("SUCCESS: Correct frisbee info found!")
    else:
         print("FAILURE: Incorrect response for 'frisbee'")

def test_chess_query():
    print("\nTesting 'chess' query:")
    response = get_response("chess")
    print(f"Response: {response}")
    if "1-5 members" in response and "Chess (Mix)" in response:
         print("SUCCESS: Correct chess info found!")
    else:
         print("FAILURE: Incorrect response for 'chess'")

def test_kabaddi_query():
    print("\nTesting 'kabaddi' query:")
    response = get_response("kabaddi")
    print(f"Response: {response}")
    if "7-12 members" in response:
         print("SUCCESS: Correct kabaddi info found!")
    else:
         print("FAILURE: Incorrect response for 'kabaddi'")

def test_whole_sports_query():
    print("\nTesting 'i want to whole information give me sports' query:")
    response = get_response("i want to whole information give me sports")
    print(f"Response: {response}")
    if "Cricket" in response and "Football" in response and "Volleyball" in response:
        print("SUCCESS: Comprehensive sports info found!")
    else:
        print("FAILURE: Incorrect response for whole sports query")

def test_spoural_info_query():
    print("\nTesting 'spoural information' query:")
    response = get_response("spoural information")
    print(f"Response: {response}")
    if "Full Sports List" in response and "Full Cultural List" in response:
        print("SUCCESS: Spoural summary info found!")
    else:
        print("FAILURE: Incorrect response for spoural info query")

def test_hostel_fees_query():
    print("\nTesting 'give me all hostel fees' query:")
    response = get_response("give me all hostel fees")
    # Clean up the response text for easier matching
    clean_response = response.replace("Γé╣", "₹").replace(",", "")
    print(f"Response: {response}")
    if "25000" in clean_response:
        print("SUCCESS: Updated A/C room fee found!")
    else:
        print("FAILURE: Updated A/C room fee not found.")

def test_msc_it_query():
    print("\nTesting 'tell about the Msc It' query:")
    response = get_response("tell about the Msc It")
    print(f"Response: {response}")
    if "M.Sc. Information Technology" in response and "CMPICA" in response:
        print("SUCCESS: M.Sc. IT info found!")
    else:
        print("FAILURE: Incorrect response for M.Sc. IT query")

def test_mca_query():
    print("\nTesting 'mca' query:")
    response = get_response("mca")
    print(f"Response: {response}")
    if "Master of Computer Applications" in response and "CMPICA" in response:
        print("SUCCESS: MCA course info found!")
    else:
        print("FAILURE: Incorrect response for MCA query")

def test_mpt_query():
    print("\nTesting 'mpt' query:")
    response = get_response("mpt")
    print(f"Response: {response}")
    if "MPT" in response and "Physiotherapy" in response:
        print("SUCCESS: MPT course info found!")
    else:
        print("FAILURE: Incorrect response for MPT query")

def test_bpt_query():
    print("\nTesting 'bpt' query:")
    response = get_response("bpt")
    print(f"Response: {response}")
    if "BPT" in response and "Physiotherapy" in response:
        print("SUCCESS: BPT course info found!")
    else:
        print("FAILURE: Incorrect response for BPT query")

def test_mtech_query():
    print("\nTesting 'all information about the m.tech' query:")
    response = get_response("all information about the m.tech")
    print(f"Response: {response}")
    if "Multiple programs found for 'MTECH'" in response or "M.Tech" in response:
        print("SUCCESS: M.Tech course info found!")
    else:
        print("FAILURE: Incorrect response for M.Tech query")

def test_mtech_no_dot_query():
    print("\nTesting 'mtech' query:")
    response = get_response("mtech")
    print(f"Response: {response}")
    if "Multiple programs found for 'MTECH'" in response or "M.Tech" in response:
        print("SUCCESS: M.Tech course info found!")
    else:
        print("FAILURE: Incorrect response for M.Tech query")

if __name__ == "__main__":
    test_charusat_query()
    test_charusat_caps_query()
    test_tell_about_charusat_query()
    test_sports_query()
    test_cricket_query()
    test_football_query()
    test_frisbee_query()
    test_chess_query()
    test_kabaddi_query()
    test_whole_sports_query()
    test_spoural_info_query()
    test_hostel_fees_query()
    test_msc_it_query()
    test_mca_query()
    test_mpt_query()
    test_bpt_query()
    test_mtech_query()
    test_mtech_no_dot_query()
