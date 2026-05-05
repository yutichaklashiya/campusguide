
import json
import os

JSON_PATH = r'd:\CampusGuide\CampusGuide\charusat_dataset.json'

new_data = [
    {
        "Question": "Best course su recommend karso? which course is best to choose in charusat university",
        "Answer": "At CHARUSAT, the 'best' course depends entirely on your personal interests, aptitude, and long-term career goals. \n\n- If you are passionate about technology and coding, **B.Tech (CE/IT/CSE)** or **MCA** are highly recommended due to excellent placement records.\n- If you are interested in business and leadership, **BBA** or **MBA** at I2IM are great choices.\n- For healthcare and research, **B.Pharm**, **Nursing**, or **B.Sc/M.Sc** in Applied Sciences offer strong career paths.\n\nWe recommend reviewing the curriculum of the courses that interest you and speaking with our admission counselors to make an informed decision.",
        "Category": "Advice"
    }
]

if os.path.exists(JSON_PATH):
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Prepend new data
    data = new_data + data
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Successfully added 'Best Course Recommendation' to the dataset.")
else:
    print(f"Error: {JSON_PATH} not found")
