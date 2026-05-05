import json
import os
import sys

# Add absolute path to main_app
sys.path.append('d:/CampusGuide/CampusGuide/CampusGuide')
sys.path.append('d:/CampusGuide/CampusGuide/CampusGuide/main_app')

from chatbot_utils import SCHOLARSHIP_DATASET

def test_bdias_scholarship():
    bdias_all = [item for item in SCHOLARSHIP_DATASET if "BDIAS (All Programs)" in item["name"]]
    if bdias_all:
        print(f"--- {bdias_all[0]['name']} ---")
        print(bdias_all[0]['full_info'])
    else:
        print("BDIAS (All Programs) block NOT FOUND")

if __name__ == "__main__":
    test_bdias_scholarship()
