
import json
import os

JSON_PATH = r'd:\CampusGuide\CampusGuide\charusat_dataset.json'

new_data = [
  {
    "Question": "CHARUSAT University ma B.Tech Computer Engineering ane Information Technology vachche actual difference su che? Placement ma kai better che? B.Tech CE vs IT Difference",
    "Answer": "At CHARUSAT, Computer Engineering (CE) focuses more on the internal workings of computers, Hardware-Software integration, Operating Systems, and Networking. Information Technology (IT) focuses on practical software application, Web Technologies, and Database Management. Placement-wise, both branches get identical opportunities at CHARUSAT with top recruiters like TCS, Infosys, and Amazon hiring from both. CE students may sometimes have a slight edge in core system-level roles.",
    "Department": "CSPIT/DEPSTAR",
    "Category": "Comparison"
  },
  {
    "Question": "Hu confuse chu BCA, BSc IT ane B.Tech IT vachche — kai course ma coding depth vadhu hoy ane placement better male? BCA vs BSc IT vs B.Tech IT",
    "Answer": "BCA (3 Years) focuses on basic programming and app development. BSc IT (3 Years) is a balanced approach between theory and practical IT. B.Tech IT (4 Years) provides the deepest technical knowledge and engineering principles. Placement-wise, B.Tech IT generally sees higher starting packages (avg. 4-6 LPA) and more global opportunities compared to BSc IT and BCA.",
    "Department": "CMPICA/CSPIT",
    "Category": "Comparison"
  },
  {
    "Question": "MSc IT ane MCA ma difference explain karo in terms of syllabus difficulty, industry demand ane salary growth? MSc IT vs MCA Comparison",
    "Answer": "MSc IT is research-oriented and focuses on the theoretical foundations of IT. MCA is a professional, industry-oriented degree emphasizing advanced coding and software architecture. MCA is generally preferred by top software firms for developer roles and often leads to faster salary growth due to specialized technical training.",
    "Department": "CMPICA",
    "Category": "Comparison"
  },
  {
    "Question": "ACPC thi admission levu better ke management quota? Placement ane degree value ma koi farak pade? Management Quota vs ACPC Admission",
    "Answer": "ACPC admission is based on merit (GUJCET/JEE) and is much more affordable. Management Quota offers more flexibility but at a higher tuition fee. There is NO difference in degree value or placement; companies treat all students equally regardless of their admission mode.",
    "Department": "General",
    "Category": "Admission"
  },
  {
    "Question": "Internal ane external marks ma ketlu weightage hoy che ane kai vadhu important che pass thava mate? Internal vs External Marks Weightage",
    "Answer": "At CHARUSAT, External Exams carry around 60-70% weightage, and Internal Assessments (Mid-sems, quizzes) carry 30-40%. You must pass both internal and external assessments independently to pass the subject.",
    "Department": "General",
    "Category": "Exam"
  },
  {
    "Question": "Internship karvu better ke direct placement prepare karvu? Kai thi vadhu benefit male? Internship vs Placement",
    "Answer": "Internships are highly recommended at CHARUSAT for real-world exposure and often lead to Pre-Placement Offers (PPO). Placement Preparation is necessary for interviews, but an internship provides the practical skills recruiters look for. Aim for both.",
    "Department": "General",
    "Category": "Career"
  },
  {
    "Question": "Hu coding ma average chu pan IT field ma career joiye che, to non-coding roles kaya che ane growth kevi hoy? Non-coding IT Career Roles",
    "Answer": "Non-coding roles include Quality Assurance (QA)/Testing, Business Analyst (BA), Technical Support Engineer, Digital Marketing, and UI/UX Design. While coding roles often start with higher pay, non-coding roles have excellent growth paths into management.",
    "Department": "General",
    "Category": "Career"
  },
  {
    "Question": "IT field ma private job better ke government job after studying at CHARUSAT University? Private vs Government Job IT",
    "Answer": "Private jobs offer rapid growth and high salary potential with global tech exposure. Government jobs (like PSUs) offer stability and security. Most CHARUSAT students prefer the private sector, but you can clear GATE for government PSU jobs.",
    "Department": "General",
    "Category": "Career"
  },
  {
    "Question": "College hostel ma rahvu better ke bahar PG ma? Cost ane comfort compare karo. Hostel vs PG Stay",
    "Answer": "The University Hostel is safer, more affordable, and helps in peer bonding with 24/7 security. A PG offers more freedom but is more expensive and requires managing your own meals. Most students prefer the hostel for the full campus experience.",
    "Department": "General",
    "Category": "Hostel"
  },
  {
    "Question": "AI/ML ane Web Development ma kai field easy che ane future ma demand vadhu kya che? AI/ML vs Web Development",
    "Answer": "Web Development is easier to start and has many job openings for beginners. AI/ML is mathematically intensive with a steeper learning curve but has high-paying specialized roles in the future. Start with Web Dev and specialize in AI/ML later if interested.",
    "Department": "General",
    "Category": "Career"
  },
  {
    "Question": "Backlog clear karta rehvu better ke ek var drop lai ne properly study karvu? Backlog vs Drop Year",
    "Answer": "Always clear backlogs while continuing studies. A drop year can negatively impact your career timeline and raise questions in interviews. CHARUSAT offers remedial exams and faculty support to help you clear backlogs.",
    "Department": "General",
    "Category": "Exam"
  },
  {
    "Question": "College lectures karta online YouTube learning vadhu effective che ke nahi? Online vs Offline Study",
    "Answer": "Both are complementary. College lectures provide structured learning and direct interaction with faculty. Online resources like YouTube are great for deep-diving into specific topics or learning industry trends. Use both.",
    "Department": "General",
    "Category": "Education"
  },
  {
    "Question": "Placement ma marks important che ke skills? Average CGPA hoy to job mali shake? Marks vs Skills Importance",
    "Answer": "Skills are the ultimate priority for hiring. However, a minimum CGPA (usually 6.5 - 7.0) is required by most companies as eligibility to sit for interviews. An average student with great skills can often secure a better job than a topper with no practical skills.",
    "Department": "General",
    "Category": "Placement"
  },
  {
    "Question": "Final year ma project strong banavvu better ke internship experience levu? Final Year Project vs Internship",
    "Answer": "The best approach is to combine them. Many students do an industry internship and use that work as their final year project, demonstrating real-world problem-solving to recruiters.",
    "Department": "General",
    "Category": "Career"
  },
  {
    "Question": "Attendance maintain karvu jaruri che ke self-study thi pan manage thai shake? Attendance vs Practical Knowledge",
    "Answer": "Attendance is compulsory at CHARUSAT (minimum 80% usually required). While self-study builds knowledge, classes ensure you don't miss labs, faculty tips, and project discussions. Balance both to excel.",
    "Department": "General",
    "Category": "Education"
  },
  {
    "Question": "Hu semester 3 ma chu ane mara 2 backlog che, attendance low che ane internship pan karvi che — aa situation ma priority su rakhvi joiye? Backlog and Internship Priority",
    "Answer": "Prioritize: 1. Clear Backlogs, 2. Improve Attendance, 3. Focus on Skills. Most companies won't hire students with active backlogs, so clear them first before seeking an internship.",
    "Department": "General",
    "Category": "Advice"
  },
  {
    "Question": "Internal ma pass chu pan external ma fail chu, grace thi pass thai sakay ke nahi? Grace Marks Rules",
    "Answer": "If you fail the external exam, you fail the subject regardless of internal marks. Grace marks are only given in rare cases (usually 1-2 marks) if you are very close to passing. You will likely need to appear for a remedial exam.",
    "Department": "General",
    "Category": "Exam"
  },
  {
    "Question": "Mane coding ma interest che pan marks average che — hu B.Tech karu ke BCA better choice? B.Tech vs BCA Decision",
    "Answer": "If you love coding and can work hard, B.Tech is better for long-term placement and global opportunities. If you find engineering subjects like Physics/Maths too hard, BCA is a great alternative focused purely on computer applications.",
    "Department": "General",
    "Category": "Advice"
  }
]

if os.path.exists(JSON_PATH):
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Remove old versions of these questions (deduplicate)
    # We identify them by their categories or content if needed
    categories_to_replace = {"Comparison", "Admission", "Exam", "Career", "Hostel", "Education", "Placement", "Advice"}
    
    # Filter out existing items that might overlap with our new ones
    filtered_data = [item for item in data if not ("Question" in item and any(cat in item.get("Category", "") for cat in categories_to_replace))]
    
    # Prepend new high-quality data
    final_data = new_data + filtered_data
    
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    print("Successfully updated charusat_dataset.json with improved English answers")
else:
    print(f"Error: {JSON_PATH} not found")
