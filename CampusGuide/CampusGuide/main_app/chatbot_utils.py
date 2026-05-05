import pandas as pd
import re
import os
import difflib
import json
from datetime import datetime, timedelta

# --- LLM INITIALIZATION ---
OLLAMA_MODEL = "phi3" # User specified phi3

try:
    import ollama
except ImportError:
    ollama = None

def ask_ollama(question, context):
    """Calls local Ollama (phi3) with the RAG context."""
    if not ollama:
        return None
    
    prompt = f"""
You are an official AI Assistant for CHARUSAT (Charotar University of Science and Technology). 
Your task is to provide accurate, well-formatted information based ONLY on the provided context.
This context contains information about University courses, departments, Scholarship schemes, and Spoural'26 Events:
- Government Scholarship schemes (like MYSY, CMSS, PRAGATI, Post Matric SC/ST/OBC).
- CHARUSAT Merit Scholarship schemes (for CSPIT, DEPSTAR, and other institutes).
- Spoural'26 Events: Details about Sports events (Cricket, Football, etc.) and Cultural events.

CONTEXT:
{context}

USER QUESTION: {question}

INSTRUCTIONS:
1. If the query is about Spoural'26 or Sports/Cultural events:
   - Provide detailed information from the context about the specific event (Cricket, Dance, etc.).
   - Include participant rules (Boys/Girls/Faculty) and any other specific details.
   - If the user asks for a list, list all relevant events from the context.
2. For Scholarships and Courses:
   - Identify the exact institute (CSPIT, DEPSTAR, etc.) and program from the context.
   - For Government Scholarships: Provide the full name, eligibility, amount, and process.
   - For CHARUSAT Merit Scholarships: State the Institute, Program, Branches, Fees, and ACPC Merit Rank for 100% scholarship.
3. STRICTURE: If the user asks for a specific institute (e.g., only "CSPIT"), DO NOT include information for other institutes (e.g., "DEPSTAR") unless they share the exact same rules in the context.
4. Format your answer using clear headings and bullet points. Avoid long paragraphs.
5. Provide a factual answer in Gujarati followed by a clean English translation.

ANSWER:"""
    
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[
            {'role': 'user', 'content': prompt},
        ])
        return response['message']['content'].strip()
    except Exception as e:
        print(f"Ollama Error: {e}")
        return None

# --- DATA LOADING ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- GLOBAL CONTEXT FOR FOLLOW-UP QUERIES ---
LAST_CONTEXT = {
    "course": None,
    "department": None,
    "pending_btech_intent": None,
    "last_btech_intent": None
}
# Update to the latest excel file containing Clubs, Cells, and Holidays
EXCEL_PATH = os.path.join(BASE_DIR, 'University_Data.xlsx')
JSON_PATH = os.path.join(BASE_DIR, 'charusat_dataset.json')
GOVERNMENT_SCHOLARSHIP_JSON_PATH = os.path.join(BASE_DIR, 'data', 'government_scholarships.json')
CHARUSAT_MERIT_SCHOLARSHIP_JSON_PATH = os.path.join(BASE_DIR, 'data', 'charusat_merit_scholarships.json')
SPOURAL_EVENTS_JSON_PATH = os.path.join(BASE_DIR, 'data', 'spoural_events.json')

# Load the structured dataset from JSON file
STRUCTURED_DATASET = []
try:
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            STRUCTURED_DATASET = json.load(f)
except Exception as e:
    print(f"Error loading JSON dataset: {e}")

# Load scholarship datasets from JSON files
SCHOLARSHIP_DATASET = []

# 1. Load Government Scholarships
try:
    if os.path.exists(GOVERNMENT_SCHOLARSHIP_JSON_PATH):
        with open(GOVERNMENT_SCHOLARSHIP_JSON_PATH, 'r', encoding='utf-8') as f:
            gov_scholarships_data = json.load(f)
            # Flatten the data for easier searching
            for category_data in gov_scholarships_data:
                category = category_data.get('category', '')
                for scholarship in category_data.get('scholarships', []):
                    # Combine all scholarship details into a searchable string
                    scholarship_info = f"### 🎓 {scholarship.get('name', '')}\n\n"
                    scholarship_info += f"**Category:** {category}\n"
                    if 'beneficiaries' in scholarship:
                        scholarship_info += f"**Beneficiaries:** {scholarship.get('beneficiaries', '')}\n"
                    
                    eligibility = scholarship.get('eligibility_criteria', [])
                    if eligibility:
                        scholarship_info += "\n**📋 Eligibility Criteria:**\n"
                        for crit in eligibility:
                            scholarship_info += f"- {crit}\n"
                        
                    scholarship_info += f"\n**💰 Scholarship Amount:**\n{scholarship.get('scholarship_amount', '')}\n"
                    
                    process = scholarship.get('process', [])
                    if process:
                        scholarship_info += "\n**📝 Application Process:**\n"
                        for step in process:
                            scholarship_info += f"- {step}\n"
                    
                    if 'notes' in scholarship:
                        scholarship_info += f"\n**ℹ️ Additional Notes:**\n{scholarship.get('notes', '')}\n"
                    
                    scholarship_info += "\n---\n"
                    
                    SCHOLARSHIP_DATASET.append({
                        "name": scholarship.get('name', ''),
                        "category": category,
                        "full_info": scholarship_info,
                        "type": "government"
                    })
except Exception as e:
    print(f"Error loading government scholarship JSON dataset: {e}")

# 2. Load CHARUSAT Merit Scholarships
try:
    if os.path.exists(CHARUSAT_MERIT_SCHOLARSHIP_JSON_PATH):
        with open(CHARUSAT_MERIT_SCHOLARSHIP_JSON_PATH, 'r', encoding='utf-8') as f:
            merit_scholarships_data = json.load(f)
            
            # --- NEW: Group by Institute to provide full info when asked for institute ---
            institute_groups = {}
            for item in merit_scholarships_data:
                inst = item.get('institute', '').upper()
                if inst not in institute_groups:
                    institute_groups[inst] = []
                institute_groups[inst].append(item)

            for inst, items in institute_groups.items():
                full_inst_info = f"### 🏛️ CHARUSAT Merit Scholarship - {inst}\n\n"
                full_inst_info += f"**Institute:** {inst}\n"
                
                # Add all programs for this institute
                for item in items:
                    prog_type = item.get('program_type', '')
                    duration = item.get('duration', '')
                    
                    # Group details by program name
                    program_details = {}
                    for detail in item.get('details', []):
                        prog_name = detail.get('program', detail.get('branches', [''])[0])
                        if prog_name not in program_details:
                            program_details[prog_name] = []
                        program_details[prog_name].append(detail)
                    
                    for prog_name, details in program_details.items():
                        full_inst_info += f"\n#### 🎓 Program: {prog_name}\n"
                        full_inst_info += f"- **Type:** {prog_type}\n"
                        full_inst_info += f"- **Duration:** {duration}\n"
                        
                        first_detail = details[0]
                        if 'fees' in first_detail:
                            full_inst_info += f"- **Fees:** ₹. {first_detail.get('fees', '')}\n"
                        
                        full_inst_info += "\n**💰 Scholarship Details:**\n"
                        for detail in details:
                            if 'hsc_marks_2026' in detail:
                                full_inst_info += f"- HSC Marks {detail['hsc_marks_2026']}: {detail.get('scholarship_scheme', '')}\n"
                            elif 'acpc_merit_rank_2026' in detail:
                                full_inst_info += f"- ACPC Rank {detail['acpc_merit_rank_2026']}: {detail.get('scholarship_scheme', '')}\n"
                            else:
                                full_inst_info += f"- {detail.get('scholarship_scheme', '')}\n"
                            
                            if 'notes' in detail:
                                full_inst_info += f"  *(Notes: {detail['notes']})*\n"
                        
                    if 'special_schemes' in item:
                        full_inst_info += "\n**✨ Special Schemes:**\n"
                        for scheme in item['special_schemes']:
                            full_inst_info += f"- **{scheme.get('name', '')}:** {scheme.get('description', '')}\n"
                    
                    if 'general_rules' in item:
                        full_inst_info += "\n**📜 General Rules:**\n"
                        for rule in item['general_rules']:
                            full_inst_info += f"- {rule}\n"
                    
                full_inst_info += "\n---\n"
                
                SCHOLARSHIP_DATASET.append({
                    "name": f"CHARUSAT Merit Scholarship - {inst} (All Programs)",
                    "category": inst,
                    "full_info": full_inst_info,
                    "type": "charusat_merit"
                })

            # Also keep individual program blocks for specific searches
            for item in merit_scholarships_data:
                institute = item.get('institute', '')
                prog_type = item.get('program_type', '')
                duration = item.get('duration', '')
                
                program_details = {}
                for detail in item.get('details', []):
                    prog_name = detail.get('program', detail.get('branches', [''])[0])
                    if prog_name not in program_details:
                        program_details[prog_name] = []
                    program_details[prog_name].append(detail)
                
                for prog_name, details in program_details.items():
                    merit_info = f"### 🎓 {prog_name} Merit Scholarship\n\n"
                    merit_info += f"**Institute:** {institute}\n"
                    merit_info += f"**Program Type:** {prog_type}\n"
                    merit_info += f"**Duration:** {duration}\n"
                    
                    first_detail = details[0]
                    if 'fees' in first_detail:
                        merit_info += f"**Fees:** ₹. {first_detail.get('fees', '')}\n"
                    
                    merit_info += "\n**💰 Scholarship Details:**\n"
                    for detail in details:
                        if 'hsc_marks_2026' in detail:
                            merit_info += f"- HSC Marks {detail['hsc_marks_2026']}: {detail.get('scholarship_scheme', '')}\n"
                        elif 'acpc_merit_rank_2026' in detail:
                            merit_info += f"- ACPC Rank {detail['acpc_merit_rank_2026']}: {detail.get('scholarship_scheme', '')}\n"
                        else:
                            merit_info += f"- {detail.get('scholarship_scheme', '')}\n"
                        
                        if 'notes' in detail:
                            merit_info += f"  *(Notes: {detail['notes']})*\n"
                    
                    if 'special_schemes' in item:
                        merit_info += "\n**✨ Special Schemes:**\n"
                        for scheme in item['special_schemes']:
                            merit_info += f"- **{scheme.get('name', '')}:** {scheme.get('description', '')}\n"
                    
                    if 'general_rules' in item:
                        merit_info += "\n**📜 General Rules:**\n"
                        for rule in item['general_rules']:
                            merit_info += f"- {rule}\n"
                    
                    merit_info += "\n---\n"
                    
                    SCHOLARSHIP_DATASET.append({
                        "name": f"CHARUSAT Merit Scholarship ({institute} {prog_type} - {prog_name})",
                        "category": institute,
                        "full_info": merit_info,
                        "type": "charusat_merit"
                    })
except Exception as e:
    print(f"Error loading CHARUSAT merit scholarship JSON dataset: {e}")

# 3. Load Spoural Events
SPOURAL_DATASET = []
try:
    if os.path.exists(SPOURAL_EVENTS_JSON_PATH):
        with open(SPOURAL_EVENTS_JSON_PATH, 'r', encoding='utf-8') as f:
            spoural_data = json.load(f)
            for item in spoural_data:
                category = item.get("category", "")
                if category == "Sports Events":
                    event_name = item.get("event_name", "")
                    parts = item.get("participants", {})
                    info = f"### 🏆 Spoural'26 Sports: {event_name}\n"
                    info += f"- **Category:** {category}\n"
                    if "composition" in parts:
                        info += f"- **Team Composition:** {parts['composition']}\n"
                        info += f"- **Total Members:** {parts['total']}\n"
                    else:
                        info += f"- **Boys:** {parts.get('boys', 'N/A')}\n"
                        info += f"- **Girls:** {parts.get('girls', 'N/A')}\n"
                        if "min" in parts and "max" in parts:
                            info += f"- **Members Required:** Min {parts['min']}, Max {parts['max']}\n"
                    info += f"- **Faculty Participation:** {parts.get('faculty', 'N/A')}\n"
                    
                    SPOURAL_DATASET.append({
                        "name": event_name,
                        "category": category,
                        "full_info": info
                    })
                elif category == "Cultural Events":
                    sub_cat = item.get("sub_category", "")
                    events = item.get("events", [])
                    info = f"### 🎨 Spoural'26 Cultural: {sub_cat}\n"
                    info += f"- **Category:** {category}\n"
                    info += f"- **Sub-Category:** {sub_cat}\n"
                    info += "**Events:**\n"
                    for event in events:
                        info += f"  - {event}\n"
                    
                    SPOURAL_DATASET.append({
                        "name": f"{category} - {sub_cat}",
                        "category": category,
                        "full_info": info
                    })
                elif "Summary" in category:
                    SPOURAL_DATASET.append({
                        "name": item.get("event_name", ""),
                        "category": category,
                        "full_info": f"### 📝 {item.get('event_name', '')}\n\n{item.get('description', '')}"
                    })
except Exception as e:
    print(f"Error loading Spoural events JSON dataset: {e}")

# Keep an alias for compatibility if needed elsewhere
GOVERNMENT_SCHOLARSHIP_DATASET = SCHOLARSHIP_DATASET

sheets = {}
try:
    if os.path.exists(EXCEL_PATH):
        xl = pd.ExcelFile(EXCEL_PATH)
        for name in xl.sheet_names:
            df = xl.parse(name)
            
            # Special handling for Faculty sheet
            if name == 'Faculties_mem_info':
                # Parse without assuming headers, treat first row as data
                df = xl.parse(name, header=None)
                
                # Rename columns to expected names
                if len(df.columns) >= 6:
                    df.columns = ['member_name', 'designation', 'qualification', 'specialization', 'emai_id', 'department_id']
            
            # NEW: Global data cleaning for all sheets
            # 1. Forward fill NaN values for merged cells (common in Excel)
            df = df.ffill()
            # 2. Convert all column names to string and lowercase for consistent matching
            df.columns = [str(col).strip().lower() for col in df.columns]
            
            sheets[name] = df
except Exception as e:
    print(f"Error loading Excel: {e}")

# --- TRANSLATION INITIALIZATION ---
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

# --- UTILS ---
def is_gujarati(text):
    """Detects if text contains Gujarati characters or common transliterated Gujarati words."""
    if not text: return False
    # Gujarati script range: \u0a80-\u0aff
    if re.search(r'[\u0a80-\u0aff]', text):
        return True
    
    # Common transliterated Gujarati keywords
    guj_keywords = {"su", "che", "ketli", "kyare", "kevu", "kai", "vachche", "male", "bhadvu", "paisa", "ketlu", "ma", "nathi", "hoy", "bane", "rahvu", "karo", "kya", "karvu", "ane", "vachche", "su", "shu"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if words.intersection(guj_keywords):
        return True
    return False

def translate_to_gujarati(text):
    """Translates English text to Gujarati using deep_translator if available."""
    if not GoogleTranslator or not text:
        return text
    try:
        # Translate to Gujarati
        translated = GoogleTranslator(source='en', target='gu').translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def clean_text(text):
    if not isinstance(text, str): return ""
    return re.sub(r'[^\w\s]', '', text).lower().strip()

def fuzzy_match(query, target_list, cutoff=0.6):
    """Returns the best match from a list of strings if similarity is above cutoff."""
    matches = difflib.get_close_matches(query, target_list, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def is_casual_pleasantry(q_lower):
    """Short friendly phrases (not mixed with course/admission queries)."""
    q = q_lower.strip()
    if len(q) > 100:
        return False
    if any(
        k in q
        for k in (
            "course", "courses", "fee", "fees", "pdpias", "cspit", "depstar", "cmpica", "rpcp",
            "admission", "eligibility", "charusat", "hostel", "library", "placement", "scholarship",
            "btech", "mtech", "bca", "mca", "bsc", "msc",
        )
    ):
        return False
    patterns = [
        r"\bnice\s+to\s+(talk|meet|speak)\b",
        r"\bgood\s+to\s+(talk|meet|speak)\b",
        r"\bpleasure\s+(to\s+)?(meet|talk)\b",
        r"\bgreat\s+(talking|chatting)\s+with\s+you\b",
        r"\bnice\s+(talking|chatting)\s+with\s+you\b",
        r"\bnice\s+talking\s+to\s+you\b",
    ]
    return any(re.search(p, q) for p in patterns)

def is_simple_greeting(q_lower):
    """Short standalone greetings (hi, hello, hiii, good morning, etc.)."""
    q = re.sub(r"\s+", " ", q_lower.strip())
    q = re.sub(r"^[!?.\s]+|[!?.\s]+$", "", q)
    if len(q) > 60:
        return False
    if any(
        k in q
        for k in (
            "course", "courses", "fee", "fees", "admission", "charusat", "hostel", "btech", "pdpias",
            "cspit", "depstar", "library", "placement", "scholarship", "eligibility",
        )
    ):
        return False
    if re.match(r"^h+i+$", q):
        return True
    return bool(
        re.match(
            r"^(hello|hey|hi|yo|greetings|namaste|namaskar|sup|good\s+(morning|afternoon|evening|day))"
            r"(\s+(there|mate|friend|buddy))?$",
            q,
        )
    )

def format_courses_for_institute(institute_key):
    """List all rows from Course_info where department contains institute_key (case-insensitive)."""
    course_df = sheets.get("Course_info")
    if course_df is None or course_df.empty:
        return None
    key = institute_key.lower().strip()

    def _norm_course_key(name):
        """Merge duplicates like same course repeated in the sheet with tiny spelling differences."""
        s = re.sub(r"[^a-z0-9]+", "", (name or "").lower().strip())
        return s

    by_norm = {}
    for _, row in course_df.iterrows():
        dept = str(row.get("department", "")).lower()
        if key not in dept:
            continue
        cname = str(row.get("course_name", "")).strip()
        if not cname or cname.lower() == "nan":
            continue
        dur = str(row.get("duration", "")).strip()
        elig = str(row.get("eligibility", "")).strip()
        nk = _norm_course_key(cname)
        if nk in by_norm:
            continue
        by_norm[nk] = (cname, dur, elig)

    if not by_norm:
        return None

    items = list(by_norm.values())

    def _sort_key(t):
        name_lower = t[0].lower()
        online_last = 1 if "online" in name_lower else 0
        return (online_last, name_lower)

    items.sort(key=_sort_key)

    institute_label = institute_key.upper()
    blocks = []
    for i, (cname, dur, elig) in enumerate(items, 1):
        blocks.append(
            f"{i}. **{cname}**\n"
            f"   - **Duration:** {dur or 'N/A'}\n"
            f"   - **Eligibility:** {elig or 'N/A'}"
        )
    body = "\n\n".join(blocks)
    return f"### {institute_label} — All courses\n\n{body}"

def normalize_question(q):
    q = q.lower().strip()
    
    # NEW: Handle common typos
    q = re.sub(r'\bwhoo+\b', 'who', q)
    q = re.sub(r'\bwhaa+t\b', 'what', q)
    q = re.sub(r'\bhoww+\b', 'how', q)
    q = re.sub(r'\bwhyy+\b', 'why', q)
    q = re.sub(r'\bwher+e\b', 'where', q)
    q = re.sub(r'\bavilable\b', 'available', q)
    
    # NEW: Handle specific Gujarati words that map to important technical terms
    guj_to_eng = {
        "vachche": "difference",
        "su chhe": "what is",
        "su che": "what is",
        "shu": "what",
        "kai": "which",
        "male": "available",
        "bhadvu": "study",
        "paisa": "fees",
        "ketlu": "how much",
        "che": "is",
        "chhe": "is",
        "nathi": "not",
        "nahi": "not",
        "hoy": "is",
        "bane": "both",
        "rahvu": "stay",
        "karo": "do",
        "kya": "where",
        "karvu": "do",
        "farak": "difference",
        "levu": "take",
        "pade": "affects",
        "laaykaat": "eligibility",
        "laykat": "eligibility",
        "laykaat": "eligibility",
        "dikri": "girl",
        "dikrio": "girls",
        "chokri": "girl",
        "chokrio": "girls",
        "kanya": "girl"
    }
    for g, e in guj_to_eng.items():
        # Use word boundaries for replacements to avoid hijacking substrings (e.g. "chess" becoming "isss")
        q = re.sub(r'\b' + re.escape(g) + r'\b', e, q)
    
    # Remove titles/honorifics if they are part of a word (e.g., kalpitsir -> kalpit)
    q = re.sub(r'(\w+)(sir|mam|mem|maam|madam)$', r'\1', q)
    # Remove standalone titles
    q = re.sub(r'\b(sir|mam|mem|maam|madam|dr|mr|ms|mrs|prof)\b', '', q)
    
    # Handle common course acronyms without dots
    q = re.sub(r'\bb\s?\.?\s?tech\b', 'btech', q)
    q = re.sub(r'\bm\s?\.?\s?tech\b', 'mtech', q)
    q = re.sub(r'\bbscit\b', 'bsc it', q)
    q = re.sub(r'\bmscit\b', 'msc it', q)
    q = re.sub(r'\bb\s?\.?\s?sc\b', 'bsc', q)
    q = re.sub(r'\bm\s?\.?\s?sc\b', 'msc', q)
    q = re.sub(r'\bb\s?\.?\s?ba\b', 'bba', q)
    q = re.sub(r'\bm\s?\.?\s?ba\b', 'mba', q)
    q = re.sub(r'\bb\s?\.?\s?pt\b', 'bpt', q)
    q = re.sub(r'\bm\s?\.?\s?pt\b', 'mpt', q)
    q = re.sub(r'\bc\s?\.?\s?s\s?\.?\s?e\b', 'cse', q)
    q = re.sub(r'\bc\s?\.?\s?e\b', 'ce', q)
    q = re.sub(r'\be\s?\.?\s?e\b', 'ee', q)
    q = re.sub(r'\bm\s?\.?\s?e\b', 'me', q)
    q = re.sub(r'\bc\s?\.?\s?l\b', 'cl', q)
    q = re.sub(r'\ba\s?\.?\s?i\s?\.?\s?m\s?\.?\s?l\b', 'aiml', q)
    
    # Handle Institute Aliases
    q = q.replace("iiim", "i2im")
    q = q.replace("faculty of management", "i2im")
    q = q.replace("management department", "i2im")
    q = q.replace("management faculty", "i2im")
    q = q.replace("faculty of computer application", "cmpica")
    q = q.replace("faculty of applied sciences", "pdpias")
    q = q.replace("faculty of technology", "cspit")
    q = q.replace("faculty of nursing", "mtin")
    q = q.replace("faculty of physiotherapy", "arip")
    q = q.replace("physiotherapy department", "arip")
    q = q.replace("physiotherapy institute", "arip")
    q = q.replace("physiotherapy faculty", "arip")
    q = q.replace("faculty of pharmacy", "rpcp")
    q = q.replace("faculty of medical sciences", "bdias")
    q = q.replace("paramedical", "bdias")
    q = q.replace("bdiaps", "bdias")
    q = q.replace("i2im", "i2im") # just to be safe with normalization
    
    # Handle role titles
    q = q.replace("principle", "principal")
    q = q.replace("dean", "dean")
    q = q.replace("hod", "hod")
    q = q.replace("head", "head")
    q = q.replace("chancellor", "chancellor")
    
    # Also remove dots from existing acronyms
    q = re.sub(r'(\b[a-zA-Z])\.([a-zA-Z])', r'\1\2', q)
    
    # Handle pluralization for common terms
    q = re.sub(r'\bhostels\b', 'hostel', q)
    q = re.sub(r'\bexams\b', 'exam', q)
    q = re.sub(r'\bfees\b', 'fee', q) # normalize to fee for keyword matching
    q = re.sub(r'\bbooks\b', 'book', q)
    q = re.sub(r'\bcourses\b', 'course', q)
    q = re.sub(r'\blibraries\b', 'library', q)
    
    # Handle Gujarati terms and common variations
    mappings = {
        "su che": "what is",
        "ketli": "how many",
        "ma": "in",
        "univercity": "university",
        "cource": "course",
        "detail": "details",
        "info": "information",
        "fess": "fee",
        "back": "bck",
        "microbiolory": "microbiology",
        "biotechnoloy": "biotechnology",
        "eligiblity": "eligibility",
        "eligability": "eligibility",
        "informantion": "information",
    }
    for k, v in mappings.items():
        # Use word boundaries for replacements
        q = re.sub(r'\b' + re.escape(k) + r'\b', v, q)
    return q

def get_keywords(question):
    # Remove common filler words
    # NOTE: "it" is NOT in stop_words because it often refers to "Information Technology"
    # NOTE: "who" is NOT in stop_words because it often refers to people (faculty)
    stop_words = {"what", "is", "the", "of", "in", "at", "for", "with", "a", "an", "about", "give", "me", "show", "list", "tell", "please", "how", "much", "does", "cost", "may", "can", "i", "do", "you", "to", "from", "by", "on", "ni", "ap", "mate", "chhe", "che", "na"}
    
    # Handle "full form" as a single token
    question = question.lower()
    if "full form" in question:
        question = question.replace("full form", "full_form")
    
    # Remove dots from acronyms for better tokenization (e.g., b.tech -> btech)
    question = re.sub(r'(\b[a-zA-Z])\.([a-zA-Z])', r'\1\2', question)
    
    words = re.findall(r'\b\w+\b', question)
    keywords = [w for w in words if w not in stop_words]
    
    processed_keywords = []
    for kw in keywords:
        # Remove "sir", "mam", "mem", "maam" from the end of a word
        clean_kw = re.sub(r"(sir|mam|mem|maam|madam|dr|mr|ms|mrs)$", "", kw)
        # Allow single character if it's a digit (e.g. '5' for BCK-5)
        if clean_kw and (len(clean_kw) > 1 or clean_kw.isdigit()):
            processed_keywords.append(clean_kw)
    return processed_keywords

def search_all_sheets(question):
    q_norm = normalize_question(question)
    keywords = get_keywords(q_norm)
    if not keywords: return []
    
    matches = []
    q_clean = clean_text(q_norm)

    # --- KEYWORD BOOSTING FOR SPECIFIC SCHEMES AND COURSES ---
    target_boost_keyword = None
    is_scholarship_query = any(kw in keywords for kw in ["scholarship", "merit", "yojana", "scheme", "bhadvu", "paisa", "free", "matric", "mysy", "cmss", "pragati"])
    is_spoural_query_keywords = any(kw in keywords for kw in ["event", "events", "sports", "cultural", "spoural", "activity", "activities", "cricket", "football", "volleyball", "kabaddi", "chess", "badminton", "basketball", "handball", "tug of war", "frisbee", "singing", "dance", "quiz", "debate", "elocution", "vaad vivad", "poetry", "rangoli", "mehndi", "nail art", "clay", "painting", "cartooning", "collage", "photography"])
    is_general_university_query = any(kw in keywords for kw in ["charusat", "university", "about", "established", "year", "grade", "accreditation", "naac"]) and len(keywords) <= 2

    if "full_form" in keywords:
        target_boost_keyword = "full_form"
    elif any(kw in keywords for kw in ["mysy", "swavalamban"]):
        target_boost_keyword = "mysy"
    elif any(kw in keywords for kw in ["cmss", "chief", "minister"]):
        target_boost_keyword = "cmss"
    elif any(kw in keywords for kw in ["pragati", "girl"]):
        target_boost_keyword = "pragati"
    elif "syllabus" in keywords:
        target_boost_keyword = "syllabus"
    elif any(kw in keywords for kw in ["sc", "matric"]):
        target_boost_keyword = "post matric scholarship for sc"
    elif any(kw in keywords for kw in ["st", "matric"]):
        target_boost_keyword = "post matric scholarship for st"
    elif any(kw in keywords for kw in ["sebc", "obc", "matric"]):
        target_boost_keyword = "post matric scholarship for sebc"
    elif "bca" in keywords:
        target_boost_keyword = "online bca" if "online" in keywords else "bca"
    elif "nursing" in keywords or "mtin" in keywords:
        target_boost_keyword = "nursing"
    elif "mba" in keywords or "iiim" in keywords:
        target_boost_keyword = "online mba" if "online" in keywords else "mba"
    elif "it" in keywords or "information technology" in q_norm:
        target_boost_keyword = "information technology"
    elif "pharmacy" in keywords or "b.pharm" in keywords or "rpcp" in keywords:
        target_boost_keyword = "pharmacy"
    elif "blis" in keywords:
        target_boost_keyword = "blis"
    elif "bba" in keywords:
        target_boost_keyword = "online bba" if "online" in keywords else "bba"
    elif any(kw in keywords for kw in ["hostel", "accommodation", "stay", "room"]):
        target_boost_keyword = "hostel"
    elif any(kw in keywords for kw in ["library", "book", "issue", "borrow", "return", "timings"]):
        target_boost_keyword = "library"
    elif is_spoural_query_keywords:
        target_boost_keyword = "spoural"
    elif "mysy" in keywords:
        target_boost_keyword = "mysy"
    elif "cmss" in keywords:
        target_boost_keyword = "cmss"
    elif "pragati" in keywords:
        target_boost_keyword = "pragati"
    elif "post" in keywords and "matric" in keywords:
        target_boost_keyword = "post matric"

    # 1. Search Spoural Events Dataset (HIGHEST PRIORITY for events)
    for item in SPOURAL_DATASET:
        info = item["full_info"]
        info_clean = clean_text(info)
        
        # Use keyword matching
        kw_match = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', info_clean))
        kw_ratio = kw_match / len(keywords) if keywords else 0
        
        if kw_ratio >= 0.2:
            # ONLY give massive boost if it's explicitly an events query
            if is_spoural_query_keywords:
                score = 50000.0 + (kw_ratio * 10000.0) # Massive base score for Spoural
                
                # Boost for direct event name match
                if any(kw in item["name"].lower() for kw in keywords):
                    score += 100000.0 # Extreme boost for direct event name
                
                # Boost for Summary items if user asks for general "sports" or "cultural"
                if "Summary" in item.get("category", ""):
                    if ("sports" in keywords and "Sports" in item["category"]) or \
                       ("cultural" in keywords and "Cultural" in item["category"]):
                        score += 200000.0 # Summary items win for general queries
            else:
                # If not an event query, penalize Spoural items so they don't hijack "charusat"
                score = -5000000.0 # Massive penalty
                
            matches.append({
                "sheet": "Spoural_Events",
                "row_text": info,
                "score": score
            })

    # 2. Search the structured dataset (from JSON)
    for item in STRUCTURED_DATASET:
        # NEW: CRITICAL BLOCK - If NOT a scholarship query, skip scholarship-related JSON results entirely
        if not is_scholarship_query:
            item_cat = item.get("Category", "").lower()
            if "scholarship" in item_cat:
                continue
                
        # NEW: CRITICAL BLOCK - If query is for Hostel Fees, skip scholarship-related JSON results
        if "hostel" in keywords and ("fee" in keywords or "fees" in keywords):
            if "scholarship" in item.get("Question", "").lower() or "scholarship" in item.get("Answer", "").lower():
                continue
        
        # NEW: CRITICAL BLOCK - If query is for Spoural Events, penalize generic sports/campus life info
        if is_spoural_query_keywords:
            item_q_text = str(item.get("Question", "")).lower()
            if any(kw in item_q_text for kw in ["sports facilities", "campus life", "vibrant campus"]):
                # Don't skip, just penalize heavily so Spoural wins
                score_penalty = 80000.0
            else:
                score_penalty = 0
        else:
            score_penalty = 0
                
        if "Question" in item and "Answer" in item:
            q_val = item["Question"]
            item_a = item["Answer"]
            
            item_q_norm = normalize_question(q_val)
            item_q = clean_text(item_q_norm)
            item_a_clean = clean_text(item_a)
            
            # Use fuzzy ratio
            ratio = difflib.SequenceMatcher(None, q_clean, item_q).ratio()
            
            # Use keyword matching - Prioritize Question matches over Answer matches
            kw_match_q = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', item_q))
            kw_match_a = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', item_a_clean))
            
            kw_ratio_q = kw_match_q / len(keywords) if keywords else 0
            kw_ratio_a = kw_match_a / len(keywords) if keywords else 0
            
            # Use original search texts for better matching
            found_in_search = any(re.search(r'\b' + re.escape(kw) + r'\b', item_q) for kw in keywords)
            
            # Boost score for JSON matches
            if ratio > 0.4 or kw_ratio_q >= 0.5 or found_in_search:
                # JSON matches get a base boost of 100.0
                # We weight kw_ratio_q (Question match) much higher than kw_ratio_a
                score = 100.0 + (ratio * 200.0) + (kw_ratio_q * 500.0) + (kw_ratio_a * 100.0) - score_penalty
                
                # --- NEW: CRITICAL SCHEME/COURSE MATCHING ---
                if target_boost_keyword and target_boost_keyword in item_q.lower():
                    score += 1000000.0 # Guaranteed winner for that specific scheme/course (Increased boost)
                
                # PENALTY: If NOT a scholarship query, penalize scholarship categories in JSON
                if not is_scholarship_query:
                    item_cat = item.get("Category", "").lower()
                    if "scholarship" in item_cat:
                        score -= 5000000.0 # Massive penalty to prevent hijacking general queries
                
                # PREVENT "charusat" in JSON from hijacking Excel university info
                if len(keywords) == 1 and "charusat" in keywords:
                    if "charusat" in item_q.lower() or "charusat" in item_a.lower():
                        score -= 5000000.0 # Massive penalty to let Excel win
                
                # --- NEW: If generic scholarship query but course-specific answer, boost it
                if "scholarship" in keywords and target_boost_keyword and target_boost_keyword in item_q.lower():
                    score += 100000.0
                
                # PREVENT GENERIC "University" JSON from outscoring specific Excel sheet matches
                if any(kw in keywords for kw in ["established", "year", "grade", "accreditation", "naac"]):
                    score -= 500.0
                
                # SPECIAL BOOST: If "CE" and "IT" and "difference" or "placement" are in query
                # specifically for the CE vs IT question
                if ("ce" in keywords or "computer" in keywords) and ("it" in keywords or "information" in keywords):
                    if "difference" in keywords or "vachche" in keywords or "comparison" in keywords or "placement" in keywords:
                        if "ce" in item_q and "it" in item_q and "difference" in item_q:
                            if "placement" in keywords and "placement" in item_q:
                                score += 500.0 # Extreme boost for placement match
                            else:
                                score += 400.0 # General comparison boost
                
                # NEW SPECIAL BOOST: List of Institutes
                if any(kw in keywords for kw in ["institute", "institutes", "department", "departments", "collage"]):
                    if "kai kai institute" in q_clean or "list of institutes" in item_q.lower() or "all department details" in item_q.lower():
                        if "all department details" in q_clean:
                            score += 800.0 # Extra boost for full details
                        else:
                            score += 600.0
                
                # NEW SPECIAL BOOST: Engineering Courses
                if "engineering" in keywords and ("course" in keywords or "courses" in keywords or "branch" in keywords):
                    if "engineering courses" in item_q.lower():
                        score += 600.0

                # NEW SPECIAL BOOST: ACPC vs Management Quota
                if "acpc" in keywords and ("management" in keywords or "quota" in keywords):
                    if "acpc" in item_q and "management" in item_q:
                        score += 600.0 # Extreme boost for the specific admission comparison
                
                # NEW SPECIAL BOOST: Admission Dates
                if ("admission" in keywords or "admissions" in keywords) and ("open" in keywords or "start" in keywords or "date" in keywords or "kyare" in keywords or "last" in keywords or "may" in keywords or "june" in keywords):
                    if "admission" in item_q.lower() and ("date" in item_q.lower() or "session" in item_q.lower() or "may" in item_q.lower() or "june" in item_q.lower() or "open" in item_q.lower()):
                        score += 900.0 # High priority for admission date queries
                
                # NEW SPECIAL BOOST: Scholarship Dates
                if "scholarship" in keywords and ("last" in keywords or "date" in keywords or "deadline" in keywords or "kyare" in keywords):
                    if "scholarship" in item_q.lower() and ("date" in item_q.lower() or "deadline" in item_q.lower()):
                        score += 900.0 # High priority for scholarship date queries
                
                # NEW SPECIAL BOOST: Specific Scholarship Schemes from PDF
                if any(kw in keywords for kw in ["mysy", "cmss", "pragati", "post matric", "kanya kelavani"]):
                    if any(skw in item_q.lower() for skw in ["mysy", "cmss", "pragati", "post matric", "kanya kelavani"]):
                        # If query is for a specific code like 6.1 or 5, but this Excel item is generic, penalize it
                        query_codes = re.findall(r'\b\d+(?:\.\d+)?\b', q_clean)
                        if query_codes:
                            score -= 2000.0 # Heavy penalty to let structured JSON win
                        else:
                            score += 1000.0 # Extreme boost for specific scheme matches
                
                # NEW SPECIAL BOOST: Institute Merit Scholarship from PDF
                if "merit" in keywords and any(kw in keywords for kw in ["cspit", "depstar", "rpcp", "pdpias", "cmpica", "iiim", "arip", "mtin", "bdias", "nursing", "physiotherapy", "management", "pharmacy", "blis", "bca", "it"]):
                    if "merit scholarship" in item_q.lower() and any(kw in item_q.lower() for kw in ["cspit", "depstar", "rpcp", "pdpias", "cmpica", "iiim", "arip", "mtin", "bdias", "nursing", "physiotherapy", "management", "pharmacy", "blis", "bca", "it"]):
                        # Same penalty if a specific code is requested
                        query_codes = re.findall(r'\b\d+(?:\.\d+)?\b', q_clean)
                        if query_codes:
                            score -= 2000.0
                        else:
                            score += 2500.0 # Guaranteed winner for specific institute/course merit scholarship
                
                # NEW SPECIAL BOOST: University Info (Excel Sheet)
                if any(kw in keywords for kw in ["university", "established", "year", "grade", "accreditation", "naac", "location", "about", "charusat"]):
                    if "university" in item_q.lower() or "charusat" in item_q.lower():
                        score += 2000000.0 # Guaranteed winner for "charusat" or "university" queries
                    # PENALIZE if it's from JSON but we want Excel to win
                    score -= 1000000.0
                
                # NEW SPECIAL BOOST: Full Form
                if "full_form" in keywords:
                    if "full form" in item_q.lower() or "what is charusat" in item_q.lower():
                        score += 2000.0
                
                # NEW: Penalty for generic library info in JSON when asking about timings/rules
                if target_boost_keyword == "library" and any(kw in keywords for kw in ["timings", "issue", "borrow", "return", "rules"]):
                    if "facility" in item_q.lower() or "how big" in item_q.lower():
                        score -= 8000.0
                
                if "1" in keywords and "april" in keywords:
                    if "1 april" in item_q.lower():
                        score += 1000.0 # Extreme boost for specific start date
                
                # --- PENALTIES TO PREVENT MISMATCHES ---
                
                # CRITICAL: Penalty for mismatched departments
                if ("nursing" in keywords or "mtin" in keywords) and ("management" in item_q.lower() or "iiim" in item_q.lower() or "bca" in item_q.lower()):
                    score -= 3000.0
                if ("management" in keywords or "iiim" in keywords) and ("nursing" in item_q.lower() or "mtin" in item_q.lower() or "bca" in item_q.lower()):
                    score -= 3000.0
                if ("bca" in keywords or "cmpica" in keywords) and ("nursing" in item_q.lower() or "management" in item_q.lower() or "pdpias" in item_q.lower()):
                    score -= 3000.0
                if ("blis" in keywords or "humanities" in keywords) and ("nursing" in item_q.lower() or "management" in item_q.lower() or "bca" in item_q.lower()):
                    score -= 3000.0
                if ("pharmacy" in keywords or "rpcp" in keywords) and ("bca" in item_q.lower() or "nursing" in item_q.lower() or "management" in item_q.lower()):
                    score -= 3000.0
                if ("bca" in keywords or "cmpica" in keywords) and ("pharmacy" in item_q.lower() or "rpcp" in item_q.lower()):
                    score -= 3000.0
                
                # NEW: Penalty for generic scholarship rules when a specific course is mentioned
                if target_boost_keyword and "general scholarship" in item_q.lower():
                    score -= 2000.0
                if "acpc" in keywords and "placement" in item_q and "acpc" not in item_q:
                    score -= 300.0
                
                # 2. Financial Aid/Afford vs Career/Jobs
                if ("afford" in keywords or "financial" in keywords or "crisis" in keywords) and ("job" in item_q or "private" in item_q or "career" in item_q):
                    score -= 500.0 
                
                # 3. Hostel Refund vs Internship
                if ("hostel" in keywords and "refund" in keywords) and ("internship" in item_q or "ppo" in item_q):
                    score -= 500.0 
                
                # 4. Hostel Availability vs Refund (STRICT)
                if "hostel" in keywords and ("available" in keywords or "facility" in keywords or "is there" in q_norm):
                    if "refund" in item_q or "policy" in item_q:
                        score -= 500000.0 # Massive penalty for refund answers when asking about availability
                    if "available" in item_q or "facility" in item_q or "only available for girls" in item_a.lower():
                        score += 500000.0 # Massive boost for availability answer

                # 5. Hostel Fees vs Scholarship (STRICT)
                if "hostel" in keywords and ("fee" in keywords or "fees" in keywords):
                    if "scholarship" in item_q.lower() or "scholarship" in item_a.lower():
                        score -= 5000000.0 # Extreme penalty for scholarship answers (Increased)
                    if "hostel fees" in item_q.lower() or "hostel fee" in item_q.lower() or "hostel fees" in item_a.lower():
                        score += 5000000.0 # Extreme boost for the direct hostel fee answer (Increased)
                    # Penalize any generic fee or scholarship mention to ensure hostel-specific answer wins
                    if "tuition" in item_q.lower() or "academic" in item_q.lower():
                        score -= 2000000.0

                # 6. Admission vs Irrelevant categories
                if ("acpc" in keywords or "admission" in keywords) and ("career" in item_q or "job" in item_q or "coding" in item_q or "exam" in item_q or "marks" in item_q or "grade" in item_q or "external" in item_q or "web" in item_q or "ai/ml" in item_q or "mca" in item_q or "msc" in item_q or "bca" in item_q or "bsc" in item_q or "attendance" in item_q or "study" in item_q or "online" in item_q or "youtube" in item_q or "hostel" in item_q or "backlog" in item_q or "internship" in item_q):
                    score -= 300.0
                
                # 7. Prevent Scholarship answers from hijacking generic "last date" queries
                if "scholarship" in item_q and "scholarship" not in keywords:
                    if "last" in keywords or "date" in keywords or "deadline" in keywords:
                        score -= 500.0 # Penalty for scholarship answers if query doesn't mention scholarship
                
                # 8. Faculty vs Scholarship
                if any(kw in keywords for kw in ["faculty", "faculties", "teacher", "professor", "principal", "dean", "hod", "head", "chancellor"]) and "scholarship" in item_q.lower():
                    score -= 5000.0 # Massive penalty for scholarship answers if query is about faculty/staff
                
                # NEW: Penalty for role-specific query matching a scholarship that just mentions the department
                if any(kw in keywords for kw in ["principal", "dean", "hod", "head", "chancellor"]) and ("scholarship" in item_q.lower() or "fees" in item_q.lower()):
                    score -= 5000.0
                
                # NEW: Penalty for library queries matching financial aid
                if target_boost_keyword == "library" and any(kw in item_q.lower() for kw in ["financial", "aid", "distress", "scholarship", "fees"]):
                    score -= 5000.0
                
                # PREVENT "CE vs IT" from hijacking generic queries
                if "difference" in item_q and "ce" in item_q and "it" in item_q:
                    if not (("ce" in keywords or "computer" in keywords) and ("it" in keywords or "information" in keywords)):
                        score -= 800.0 # Massive penalty if it's the comparison answer but query doesn't ask for both
                    
                matches.append({
                    "sheet": "Structured_Dataset",
                    "row_text": item_a,
                    "score": score
                })
    

    # 3. Search Scholarship Datasets (from JSON)
    if is_scholarship_query:
        for item in SCHOLARSHIP_DATASET:
            # NEW: CRITICAL BLOCK - If query is for Hostel Fees, skip scholarship results entirely
            if "hostel" in keywords and ("fee" in keywords or "fees" in keywords):
                continue
                
            info = item["full_info"]
            info_clean = clean_text(info)
            
            # Use keyword matching
            kw_match = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', info_clean))
            kw_ratio = kw_match / len(keywords) if keywords else 0
            
            if kw_ratio >= 0.15: # Even lower threshold for scholarships to ensure recall
                score = 150.0 + (kw_ratio * 500.0)
                
                # Boost for specific scheme names or institute names
                # Clean name for matching (remove special characters like parentheses)
                clean_item_name = re.sub(r'[^\w\s]', ' ', item["name"]).lower()
                name_tokens = clean_item_name.split()
                
                # Filter out generic words from the name boost to avoid false positives
                generic_words = {"scholarship", "scheme", "yojana", "program", "programme", "post", "matric", "students", "only", "for"}
                specific_name_tokens = [t for t in name_tokens if t not in generic_words and len(t) > 2]
                
                # If any specific part of the name matches a keyword, give it a massive boost
                name_match_found = False
                
                # --- NUMERIC CODE LOGIC (STRICT) ---
                query_numeric_codes = re.findall(r'\b\d+(?:\.\d+)?\b', " ".join(keywords))
                # CRITICAL: Extract codes ONLY from the original name to ensure precision
                item_name_numeric_codes = re.findall(r'\b\d+(?:\.\d+)?\b', item["name"].lower())
                
                if query_numeric_codes:
                    # Check for exact matches in the scholarship name
                    has_exact_code_match = any(code in item_name_numeric_codes for code in query_numeric_codes)
                    
                    if has_exact_code_match:
                        score += 2000000.0 # UNBEATABLE PRIORITY for exact code match in name
                        name_match_found = True
                    elif item_name_numeric_codes:
                        # If this item has a numeric code but it doesn't match the query code
                        # (e.g. user asked for 5, but this item is 6.1)
                        score -= 1500000.0 # CRITICAL: Massive penalty for code mismatch
                # --- END NUMERIC CODE LOGIC ---

                for kw in keywords:
                    # Check for BCK-X patterns
                    if kw.startswith('bck'):
                        # Normalize and check for exact BCK match in name
                        normalized_name = item["name"].lower().replace(" ", "").replace("-", "")
                        normalized_kw = kw.replace("-", "")
                        
                        # If kw is just "bck", it shouldn't match "bck61" unless the name is also just "bck"
                        if len(normalized_kw) > 3: # it's like "bck5"
                            if normalized_kw in normalized_name:
                                score += 500000.0
                                name_match_found = True
                                break
                        elif normalized_kw == "bck":
                            # If query is just "bck", any bck item is relevant but not a definitive winner
                            if "bck" in normalized_name:
                                score += 50000.0
                                # Don't set name_match_found = True to allow other keywords to match
                    
                    if not name_match_found:
                        for token in specific_name_tokens:
                            # Partial match or fuzzy match (handles girls vs girl, etc.)
                            if kw in token or token in kw or difflib.SequenceMatcher(None, kw, token).ratio() > 0.8:
                                name_match_found = True
                                break
                    if name_match_found: break
                
                if name_match_found:
                    score += 50000.0 # General boost for any name match
                    
                # Boost for category/institute names
                clean_category = re.sub(r'[^\w\s]', ' ', item["category"]).lower()
                category_tokens = clean_category.split()
                if any(kw in keywords for kw in category_tokens if len(kw) > 1):
                    score += 10000.0
                
                # Additional boost for government scholarship queries
                if item.get("type") == "government" and any(kw in keywords for kw in ["government", "sarkari", "state", "gujarat"]):
                    score += 10000.0
                
                # Define item_info_lower early for category boosting
                item_info_lower = item["full_info"].lower()
                item_name_lower = item["name"].lower()
                
                # --- NEW: Category-Specific Boosting (Gender, Caste, etc.) ---
                if any(kw in keywords for kw in ["girl", "girls", "female", "kanya", "dikri"]):
                    if any(term in item_info_lower for term in ["girl", "female", "kanya", "woman", "women"]):
                        score += 100000.0 # Massive boost for matching gender queries
                
                if any(kw in keywords for kw in ["sc", "st", "obc", "ebc", "sebc", "minority"]):
                    if any(kw in item_info_lower for kw in ["sc", "st", "obc", "ebc", "sebc", "minority"]):
                        score += 100000.0 # Massive boost for matching category queries
                
                # --- NEW: CRITICAL INSTITUTE AND PROGRAM FILTERING ---
                
                # --- Course vs Institute Logic (Refined) ---
                # Check if user is asking for a specific course vs an entire institute
                institutes_list = ["cspit", "depstar", "cmpica", "pdpias", "rpcp", "mtin", "arip", "i2im", "iiim", "bdias", "cips", "class"]
                query_institutes = [inst for inst in institutes_list if inst in keywords]
                
                if query_institutes:
                    # If it's an institute query, prioritize "All Programs" block
                    if "(all programs)" in item_name_lower:
                        score += 500000.0 # Extreme boost for the consolidated block
                    else:
                        # Penalty for individual blocks to keep output clean
                        is_course_query = any(prog in keywords for prog in ["btech", "mtech", "bca", "mca", "bsc", "msc", "bpt", "mpt", "pharm", "mba", "bba", "radiology", "optometry", "paramedical", "imaging", "laboratory", "anaesthesia"])
                        if not is_course_query:
                            score -= 100000.0 
                else:
                    # If it's a specific course query, penalize the "All Programs" block
                    if "(all programs)" in item_name_lower:
                        score -= 300000.0 # Extreme penalty
                
                # --- Specific Course Boosting ---
                if "bpt" in keywords or "physiotherapy" in keywords:
                    if "undergraduate (b.pt)" in item_info_lower:
                        score += 100000.0
                    elif "postgraduate (m.pt)" in item_info_lower:
                        if "mpt" not in keywords and "master" not in keywords:
                            score -= 80000.0
                
                if "mpt" in keywords:
                    if "postgraduate (m.pt)" in item_info_lower:
                        score += 100000.0
                    elif "undergraduate (b.pt)" in item_info_lower:
                        score -= 80000.0

                # --- BSC IT vs BSC (General) vs MSC IT vs MCA ---
                if "it" in keywords or "information technology" in keywords:
                    if "msc" in keywords:
                        # Looking for M.Sc. IT
                        if "postgraduate (m.sc. it)" in item_info_lower:
                            score += 100000.0 # Massive boost for exact block
                        elif "postgraduate" in item_info_lower and "mca" in item_info_lower:
                            score -= 100000.0 # Massive penalty for MCA block
                        
                        program_line = ""
                        for line in item_info_lower.split('\n'):
                            if line.startswith("program:"):
                                program_line = line
                                break
                        if "msc" not in program_line and "master of science" not in program_line:
                            score -= 80000.0
                    elif "mca" in keywords:
                        # Looking for MCA
                        if "postgraduate (mca)" in item_info_lower:
                            score += 100000.0
                        elif "postgraduate" in item_info_lower and "m.sc. it" in item_info_lower:
                            score -= 100000.0
                            
                        program_line = ""
                        for line in item_info_lower.split('\n'):
                            if line.startswith("program:"):
                                program_line = line
                                break
                        if "mca" not in program_line and "master of computer applications" not in program_line:
                            score -= 80000.0
                    elif "bsc" in keywords:
                        # Looking for B.Sc. IT
                        if "undergraduate (b.sc. it)" in item_info_lower:
                            score += 100000.0
                        elif "undergraduate" in item_info_lower and "bca" in item_info_lower:
                            score -= 100000.0
                            
                        program_line = ""
                        for line in item_info_lower.split('\n'):
                            if line.startswith("program:"):
                                program_line = line
                                break
                        if "bsc" not in program_line and "bachelor of science" not in program_line:
                            score -= 80000.0
                elif "bsc" in keywords:
                    # Looking for B.Sc. (General) (Must be PDPIAS)
                    if "it" in item_info_lower or "information technology" in item_info_lower:
                        score -= 50000.0 # Extreme penalty
                    if "pdpias" in item_info_lower:
                        score += 50000.0 # Extreme boost
                    elif "cmpica" in item_info_lower:
                        score -= 30000.0 # High penalty
                elif "bca" in keywords:
                    # Looking for BCA (Must be CMPICA and not B.Sc. IT block)
                    if "undergraduate (bca)" in item_info_lower:
                        score += 100000.0
                    elif "undergraduate" in item_info_lower and "b.sc. it" in item_info_lower:
                        score -= 100000.0
                    
                    program_line = ""
                    for line in item_info_lower.split('\n'):
                        if line.startswith("program:"):
                            program_line = line
                            break
                    if "bca" not in program_line and "bachelor of computer applications" not in program_line:
                        score -= 80000.0
                    if "cmpica" in item_info_lower:
                        score += 50000.0
                elif "mca" in keywords:
                    # Looking for MCA (but IT not in keywords)
                    program_line = ""
                    for line in item_info_lower.split('\n'):
                        if line.startswith("program:"):
                            program_line = line
                            break
                    if "mca" not in program_line and "master of computer applications" not in program_line:
                        score -= 80000.0
                    if "cmpica" in item_info_lower:
                        score += 50000.0
                
                # --- Institute Filtering ---
                if query_institutes:
                    item_category_lower = item["category"].lower()
                    # Special handling for I2IM/IIIM
                    if "iiim" in keywords or "i2im" in keywords:
                        if "iiim" not in item_category_lower and "i2im" not in item_category_lower:
                            score -= 100000.0 # Extreme penalty for wrong institute
                    # If query asks for specific institute but item is from another
                    elif not any(inst in item_category_lower for inst in query_institutes):
                        score -= 10000.0 # Massive penalty for wrong institute
                
                # --- Program Filtering (General) ---
                programs = ["btech", "mtech", "bca", "mba", "mca"]
                query_programs = [prog for prog in programs if prog in keywords]
                
                if query_programs:
                    # If query asks for BCA but item is for B.Tech, etc.
                    if not any(prog in item_info_lower for prog in query_programs):
                        score -= 10000.0 # Massive penalty for wrong program
                    
                # Boost for scholarship related terms
                if any(kw in keywords for kw in ["scholarship", "scheme", "yojana", "merit", "fees", "fee"]):
                    score += 500.0
                
                # Additional boost for specific merit scholarship queries
                if item["type"] == "charusat_merit" and "merit" in keywords:
                    score += 1000.0
                    
                sheet_name = "Government_Scholarships" if item["type"] == "government" else "CHARUSAT_Merit_Scholarships"
                
                matches.append({
                    "sheet": sheet_name,
                    "row_text": info,
                    "score": score
                })

    # 3. Search Excel sheets if available - LOWER PRIORITY
    for sheet_name, df in sheets.items():
        # Check if 'Question' and 'Answer' columns exist
        has_q_a = 'Question' in df.columns and 'Answer' in df.columns
        
        for idx, row in df.iterrows():
            # Skip rows that are clearly headers or empty
            row_values = [str(val).lower() for val in row.values if str(val) != 'nan']
            if not row_values or 'member_name' in row_values:
                continue

            if has_q_a:
                row_q_norm = normalize_question(str(row['Question']))
                row_q = clean_text(row_q_norm)
                row_a = str(row['Answer'])
                
                # Fuzzy match question
                similarity = difflib.SequenceMatcher(None, q_clean, row_q).ratio()
                is_substring = q_clean in row_q or row_q in q_clean
                
                # Also check for keyword overlap
                kw_match_count = sum(1 for kw in keywords if kw in row_q or kw in row_a.lower())
                
                if similarity > 0.5 or is_substring or kw_match_count >= len(keywords) * 0.7:
                    score = (similarity * 1.5) + (kw_match_count / len(keywords) if keywords else 0)
                    if is_substring:
                        score += 0.5

                    # Boost institute-wise placement answers from Excel when user asks placements.
                    if "placement" in keywords or "placements" in keywords:
                        # Common placement sheet names in the Excel file.
                        if sheet_name.lower() in {"placement", "placements", "placement_info"}:
                            score += 5000.0
                        # Extra boost if the institute name from query appears in the question/answer.
                        inst_aliases = ["cspit", "depstar", "cmpica", "pdpias", "rpcp", "mtin", "arip", "i2im", "iiim", "bdias"]
                        if any(inst in keywords for inst in inst_aliases):
                            if any(inst in row_q_norm or inst in row_a.lower() for inst in inst_aliases):
                                score += 2000.0
                    
                    matches.append({
                        "sheet": sheet_name,
                        "row_text": row_a,
                        "score": score
                    })
            else:
                # Include column names to help matching (especially for "timings", "fees", etc.)
                # Replace underscores with spaces to help keyword matching with \b
                row_text = " ".join(f"{col.replace('_', ' ')} {val}" for col, val in row.items() if str(val) != "nan").lower()
                row_text_norm = normalize_question(row_text)
                
                # Check for keyword matches
                kw_match_count = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', row_text_norm))
                
                # Fuzzy match the whole query against the row text
                similarity = difflib.SequenceMatcher(None, q_clean, row_text_norm).ratio()
                
                # Check for whole-word keyword match (important for short queries)
                is_sub = any(re.search(r'\b' + re.escape(kw) + r'\b', row_text_norm) for kw in keywords)
                
                if kw_match_count >= len(keywords) * 0.7 or similarity > 0.4 or is_sub:
                    # Specific formatting for Faculty sheet if it matches
                    if sheet_name == 'Faculties_mem_info':
                        # Use column mapping if available, else generic
                        if len(row) >= 5:
                            name = str(row.get('member_name', row.iloc[0]))
                            desig = str(row.get('designation', row.iloc[1]))
                            qual = str(row.get('qualification', row.iloc[2]))
                            spec = str(row.get('specialization', row.iloc[3]))
                            email = str(row.get('emai_id', row.iloc[4]))
                            dept = str(row.get('department_id', row.iloc[5])) if len(row) > 5 else ""
                            
                            formatted_text = f"**Faculty Member:** {name}\n**Designation:** {desig}\n**Qualification:** {qual}\n**Specialization:** {spec}\n**Email:** {email}\n**Department:** {dept}"
                        else:
                            formatted_text = " | ".join(f"{col}: {val}" for col, val in row.items() if str(val) != "nan")
                    elif sheet_name == 'University':
                        name = str(row.get('name', ''))
                        est = str(row.get('established_year', ''))
                        loc = str(row.get('location', ''))
                        acc = str(row.get('accreditation', ''))
                        about = str(row.get('about_university', ''))
                        email = str(row.get('email', ''))
                        
                        # NEW: Improved fallback formatting based on query intent
                        if "full_form" in keywords:
                            formatted_text = f"CHARUSAT stands for **{name}**."
                        elif "about" in q_norm or "tell me" in q_norm or (len(keywords) == 1 and "charusat" in keywords):
                            # The user specifically mentioned about_university column is the answer
                            formatted_text = about
                        else:
                            formatted_text = f"**University:** {name}\n**Established Year:** {est}\n**Location:** {loc}\n**Accreditation:** {acc}\n**About:** {about}\n**Email:** {email}"
                    elif sheet_name == 'Fees_info':
                        c_name = str(row.get('course_name', ''))
                        fee = str(row.get('tuition_fees', ''))
                        mode = str(row.get('payment_mode', ''))
                        
                        if any(kw in q_norm for kw in ["how", "pay", "method", "mode", "way", "process"]):
                            formatted_text = f"The annual fees for **{c_name}** is **{fee}**. You can pay via: {mode}."
                        else:
                            formatted_text = f"The annual fees for **{c_name}** is **{fee}**."
                    elif sheet_name == 'Department':
                        f_name = str(row.get('faculty_name', ''))
                        i_name = str(row.get('institute_name', ''))
                        progs = str(row.get('programs', ''))
                        formatted_text = f"### 🏛️ {i_name}\n**Faculty:** {f_name}\n**Programs Offered:** {progs}"
                    else:
                        formatted_text = " | ".join(f"{col}: {val}" for col, val in row.items() if str(val) != "nan")

                    # Excel matches get a base score of 0 to ensure they stay below JSON matches (which start at 4.0+)
                    final_score = (similarity * 1.5) + (kw_match_count / len(keywords) if keywords else 0)
                    
                    # SPECIAL BOOST for Faculty sheet in Excel
                    if sheet_name == 'Faculties_mem_info':
                        role_keywords = ["faculty", "faculties", "teacher", "professor", "sir", "mam", "dr", "principal", "dean", "hod", "head", "chancellor"]
                        if any(kw in keywords for kw in role_keywords):
                            final_score += 5000.0 # Massive boost for faculty queries
                            
                            # EXTRA BOOST: If query specifically matches a designation in this row (with synonyms)
                            row_desig = str(row.get('designation', '')).lower()
                            
                            # Synonym mapping for designation matching
                            synonyms = {
                                "hod": ["head", "hod"],
                                "head": ["head", "hod"],
                                "principal": ["principal", "director"],
                                "dean": ["dean"]
                            }
                            
                            for kw in keywords:
                                # Check direct match or via synonyms
                                matched_role = False
                                if kw in row_desig:
                                    matched_role = True
                                elif kw in synonyms:
                                    if any(syn in row_desig for syn in synonyms[kw]):
                                        matched_role = True
                                
                                if matched_role:
                                    final_score += 4000.0 # Role match is very important
                                
                            # EXTRA BOOST: If department also matches
                            row_dept = str(row.get('department_id', '')).lower()
                            if any(kw in row_dept for kw in keywords if kw not in role_keywords):
                                final_score += 6000.0 # Department match must override role match in other departments
                        
                        # Penalty for role-specific query matching a row without that role
                        if any(kw in keywords for kw in ["principal", "dean", "hod", "head"]):
                            row_desig = str(row.get('designation', '')).lower()
                            has_role = False
                            for kw in ["principal", "dean", "hod", "head"]:
                                if kw in keywords:
                                    syns = synonyms.get(kw, [kw])
                                    if any(syn in row_desig for syn in syns):
                                        has_role = True
                                        break
                            if not has_role:
                                final_score -= 3000.0 # Penalize rows that don't have the requested role
                        
                        # BOOST for name-based faculty queries (e.g., "Dhara Patel")
                        if not any(kw in keywords for kw in role_keywords):
                            # Common Indian surnames and first names
                            name_indicators = ["patel", "shah", "kumar", "singh", "gupta", "joshi", "mehta", "desai", "trivedi", "solanki", "dhara", "priya", "rahul", "amit", "neha", "kiran", "vijay", "anil", "sunil", "manoj", "suresh", "ramesh", "mahesh", "rajesh", "dinesh", "mukesh", "naresh", "paresh", "jignesh", "hardik", "darshan", "vishal", "nirav", "bhavin", "chirag", "dhaval", "fenil", "gautam", "hemant", "jay", "kunal", "lalit", "milan", "nilesh", "om", "parth", "quresh", "raj", "sanjay", "tarun", "umang", "viral", "yash", "zuber"]
                            if len(keywords) >= 2 and len(keywords) <= 3 and any(kw in name_indicators for kw in keywords):
                                final_score += 15000.0 # High boost for name-based faculty searches to override Department matches
                    
                    # SPECIAL BOOST for Library sheet
                    if sheet_name == 'Library':
                        if any(kw in keywords for kw in ["library", "book", "issue", "borrow", "return", "timings"]):
                            final_score += 15000.0 # Even more boost for library queries
                            
                            # Format library info nicely
                            timings = str(row.get('library_timings', ''))
                            digital = str(row.get('digital_resources', ''))
                            rules = str(row.get('borrowing_rules', ''))
                            
                            # SELECTIVE FORMATTING based on query
                            if any(kw in keywords for kw in ["fine", "fines", "late", "submit"]):
                                formatted_text = "**Library Fine Details:**\nFor specific information regarding late return fines, please contact the Librarian at the central library."
                            elif any(kw in keywords for kw in ["issue", "borrow", "return", "book"]):
                                formatted_text = f"**Library Borrowing Rules:**\n{rules}"
                            elif "timings" in keywords:
                                formatted_text = f"**Library Timings:**\n{timings}"
                            else:
                                formatted_text = f"**Library Information:**\n- **Timings:** {timings}\n- **Digital Resources:** {digital}\n- **Borrowing Rules:** {rules}"
                            
                            matches.append({
                                "sheet": sheet_name,
                                "row_text": formatted_text,
                                "score": final_score
                            })
                            continue # Already added

                    # SPECIAL BOOST for Syllabus sheet
                    if sheet_name == 'Syllabus':
                        if "syllabus" in keywords:
                            final_score += 25000.0 # Absolute priority for syllabus queries
                            
                            # The sheet seems to have 'Department' and 'Syllabus' (which contains the link)
                            dept = str(row.get('department', '')).strip()
                            link = str(row.get('syllabus', '')).strip()
                            
                            if not link or link == "nan":
                                # Fallback if columns are named differently
                                for col, val in row.items():
                                    if "http" in str(val):
                                        link = str(val)
                                    elif "dept" in str(col).lower():
                                        dept = str(val)
                            
                            formatted_text = f"You can find the syllabus for **{dept}** at this link:\n{link}"
                            
                            matches.append({
                                "sheet": sheet_name,
                                "row_text": formatted_text,
                                "score": final_score
                            })
                            continue

                    # SPECIAL BOOST for University sheet in Excel
                    if sheet_name == 'University':
                        if any(kw in keywords for kw in ["established", "year", "grade", "accreditation", "naac", "location", "about", "full_form", "university"]):
                            final_score += 5000000.0 # Guaranteed winner
                        if "charusat" in keywords and len(keywords) <= 2:
                            final_score += 5000000.0 # Guaranteed winner for "charusat"
                    
                    # SPECIAL BOOST for Fees sheet in Excel
                    if sheet_name == 'Fees_info':
                        if "online" in keywords and "online" in str(row.get('course_name', '')).lower():
                            final_score += 5000.0 # Absolute priority for online course fees if requested
                        elif "online" not in keywords and "online" in str(row.get('course_name', '')).lower():
                            final_score -= 2000.0 # Penalty for online course fees if NOT requested
                    
                    # SPECIAL BOOST for Department sheet in Excel
                    if sheet_name == 'Department':
                        # If query is just the institute/department name (e.g. "CMPICA")
                        inst_name = str(row.get('institute_name', '')).lower()
                        fac_name = str(row.get('faculty_name', '')).lower()
                        if len(keywords) <= 2 and any(kw in inst_name or kw in fac_name for kw in keywords):
                            final_score += 10000.0 # Extremely high priority for institute overview
                        elif any(kw in inst_name or kw in fac_name for kw in keywords):
                            final_score += 5000.0
                        
                        # PENALIZE Department matches if query looks like a name search
                        name_indicators = ["patel", "shah", "kumar", "singh", "gupta", "joshi", "mehta", "desai", "trivedi", "solanki", "dhara", "priya", "rahul", "amit", "neha", "kiran", "vijay", "anil", "sunil", "manoj", "suresh", "ramesh", "mahesh", "rajesh", "dinesh", "mukesh", "naresh", "paresh", "jignesh", "hardik", "darshan", "vishal", "nirav", "bhavin", "chirag", "dhaval", "fenil", "gautam", "hemant", "jay", "kunal", "lalit", "milan", "nilesh", "om", "parth", "quresh", "raj", "sanjay", "tarun", "umang", "viral", "yash", "zuber"]
                        if any(kw in name_indicators for kw in keywords):
                            final_score -= 10000.0 # Strong penalty for Department when searching for names

                    
                    matches.append({
                        "sheet": sheet_name,
                        "row_text": formatted_text,
                        "score": final_score
                    })
 
    # Sort matches by score
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Increase limit if we have many high-scoring faculty matches
    limit = 5
    if matches and matches[0]['sheet'] == 'Faculties_mem_info' and matches[0]['score'] > 10000:
        # If it's a role-based query, we might want to return all relevant people
        top_score = matches[0]['score']
        # Include all matches that are within 10% of the top score from the same sheet
        limit = 0
        for m in matches:
            if m['sheet'] == 'Faculties_mem_info' and m['score'] >= top_score * 0.9:
                limit += 1
            else:
                break
        limit = max(5, min(limit, 15)) # Between 5 and 15
        
    return matches[:limit]

def build_context(matches):
    ctx = ""
    for m in matches:
        if m['sheet'] == "Structured_Dataset":
             ctx += f"[JSON Dataset] {m['row_text']}\n"
        elif m['sheet'] == "Government_Scholarships":
             ctx += f"[Government Scholarship Info] {m['row_text']}\n"
        elif m['sheet'] == "CHARUSAT_Merit_Scholarships":
             ctx += f"[CHARUSAT Merit Scholarship Info] {m['row_text']}\n"
        elif m['sheet'] == "Spoural_Events":
             ctx += f"[Spoural'26 Event Info] {m['row_text']}\n"
        else:
             ctx += f"[Excel: {m['sheet']}] {m['row_text']}\n"
    return ctx

def is_weekend_holiday(check_date):
    """Returns True if the date is a Sunday or 2nd/4th Saturday."""
    if check_date.weekday() == 6: # Sunday
        return True, "Sunday"
    
    if check_date.weekday() == 5: # Saturday
        day = check_date.day
        # Determine if it's 2nd or 4th Saturday
        # Day 8-14 is 2nd week, 22-28 is 4th week
        week_num = (day - 1) // 7 + 1
        if week_num == 2:
            return True, "2nd Saturday"
        if week_num == 4:
            return True, "4th Saturday"
            
    return False, None

def get_chatbot_response(question, original_input=None):
    global LAST_CONTEXT
    
    # Quick direct answer for hostel availability queries.
    q_hostel_check = normalize_question(question)
    if "hostel" in q_hostel_check and any(word in q_hostel_check for word in ["fee", "fees", "cost", "charge"]):
        if any(word in q_hostel_check for word in ["boy", "boys", "male"]):
            return "Boys hostel is outside the CHARUSAT campus. For the latest boys hostel fee structure, please contact the hostel office/inquiry desk directly."
        if any(word in q_hostel_check for word in ["girl", "girls", "female"]):
            return "For girls hostel at CHARUSAT campus, please contact the hostel office/inquiry desk for the latest fee structure and room availability."

    if "hostel" in q_hostel_check and any(
        phrase in q_hostel_check
        for phrase in ["is there", "available", "facility", "do you have", "has hostel"]
    ):
        if any(word in q_hostel_check for word in ["boy", "boys", "male"]):
            return "Yes, boys hostel facility is available, and it is outside the CHARUSAT campus."
        if any(word in q_hostel_check for word in ["girl", "girls", "female"]):
            return "Yes, girls hostel facility is available, and it is inside the CHARUSAT campus."
        return "Yes, hostel facilities are available at CHARUSAT. Girls hostel is inside the campus, and boys hostel is outside the CHARUSAT campus."

    # Direct library information should come from Library sheet, not from course matching.
    q_library_check = normalize_question(question)
    if "library" in q_library_check:
        library_course_intent_words = ["blis", "mlis", "course", "program", "admission", "eligibility", "fee", "fees", "phd"]
        if not any(w in q_library_check for w in library_course_intent_words):
            library_df = sheets.get('Library')
            if library_df is not None and not library_df.empty:
                row = library_df.iloc[0]
                timings = str(row.get('library_timings', '')).strip()
                digital = str(row.get('digital_resources', '')).strip()
                borrowing = str(row.get('borrowing_rules', '')).strip()
                response = "### 📚 CHARUSAT Library Information\n\n"
                if timings and timings.lower() != "nan":
                    response += f"- **Timings:** {timings}\n"
                if digital and digital.lower() != "nan":
                    response += f"- **Digital Resources:** {digital}\n"
                if borrowing and borrowing.lower() != "nan":
                    response += f"- **Borrowing Rules:** {borrowing}\n"
                return response.strip()

    # NEW: HARD-CODED PRIORITY FOR CHARUSAT (University Info) - Highest Priority
    # Check if the query is just "charusat" or "tell me about charusat"
    q_simple = clean_text(question)
    if q_simple == "charusat" or \
       (re.search(r'\bcharusat\b', q_simple) and any(kw in q_simple for kw in ["tell", "about", "what", "is", "details", "info", "information"])):
        # Ensure we don't accidentally match "Mr. & Ms. Charusat" here
        if "mr" not in q_simple and "ms" not in q_simple and "event" not in q_simple and "sports" not in q_simple and "cultural" not in q_simple and "library" not in q_simple:
            university_df = sheets.get('University')
            if university_df is not None and not university_df.empty:
                row = university_df.iloc[0]
                about = str(row.get('about_university', ''))
                if about and about != 'nan':
                    return about

    # Normalize and get keywords
    q_lower = normalize_question(question)
    keywords = get_keywords(q_lower)
    user_lang_source = original_input if original_input else question
    prefers_gujarati = is_gujarati(user_lang_source)

    if is_simple_greeting(q_lower):
        if prefers_gujarati:
            return "નમસ્તે! હું CampusGuide છું — CHARUSAT વિશે admissions, courses, fees, placements કે બીજું કંઈ પૂછો, હું મદદ કરીશ."
        return "Hi there! I'm CampusGuide, your CHARUSAT assistant. Ask me about admissions, courses, fees, placements, hostels, or anything else about the university."

    if is_casual_pleasantry(q_lower):
        if prefers_gujarati:
            return "તમારી સાથે વાત કરીને સારું લાગ્યું! CHARUSAT વિશે કંઈ પણ પૂછો — admission, courses, fees, placements."
        return "Likewise! I'm glad to chat. Feel free to ask me anything about CHARUSAT — admissions, courses, fees, or placements."

    # BPT/MPT full forms (physiotherapy — not MCA). Skip if MCA is also asked so a combined answer can be built downstream.
    if "full_form" in keywords and ("mpt" in keywords or "bpt" in keywords) and "mca" not in keywords:
        lines = []
        if "bpt" in keywords:
            lines.append("- **BPT** — Bachelor of Physiotherapy")
        if "mpt" in keywords:
            lines.append("- **MPT** — Master of Physiotherapy")
        if lines:
            header = "### 📖 સંક્ષિપ્ત નામ / Full forms\n\n" if prefers_gujarati else "### 📖 Full forms\n\n"
            return header + "\n".join(lines)

    # Institute / department hint from query (CSPIT, DEPSTAR, etc.)
    institute_alias_map = {
        "cspit": "cspit",
        "depstar": "depstar",
        "cmpica": "cmpica",
        "pdpias": "pdpias",
        "rpcp": "rpcp",
        "i2im": "i2im",
        "iiim": "i2im",
        "mtin": "mtin",
        "arip": "arip",
        "bdias": "bdias",
        "class": "class",
    }
    resolved_institute = next((institute_alias_map[kw] for kw in keywords if kw in institute_alias_map), None)
    if not resolved_institute:
        for alias, canon in institute_alias_map.items():
            if alias in q_lower:
                resolved_institute = canon
                break

    # All courses for a named institute/department (Course_info sheet — department column)
    if resolved_institute and not any(kw in keywords for kw in ["fee", "fees", "fess", "paisa", "cost", "pay"]):
        wants_institute_course_list = (
            ("course" in keywords or "courses" in keywords or "program" in keywords)
            and any(
                kw in keywords
                for kw in [
                    "all",
                    "list",
                    "information",
                    "info",
                    "details",
                    "everything",
                    "every",
                    "overview",
                    "summary",
                ]
            )
        ) or (
            resolved_institute
            and re.search(r"\ball\s+courses?\b", q_lower)
            and ("course" in keywords or "courses" in keywords)
        ) or (
            resolved_institute
            and ("course" in keywords or "courses" in keywords)
            and re.search(r"\bcourses?\s+(in|at|of)\s+", q_lower)
        )
        if wants_institute_course_list:
            inst_courses_text = format_courses_for_institute(resolved_institute)
            if inst_courses_text:
                return inst_courses_text

    # Branch tokens for B.Tech clarification flow
    btech_branch_tokens = {
        "ce": ["ce", "computer engineering"],
        "it": ["it", "information technology"],
        "cse": ["cse", "computer science"],
        "ec": ["ec", "electronics"],
        "me": ["me", "mechanical"],
        "cl": ["cl", "civil", "civil engineering", "civil and infrastructure", "construction"],
        "ee": ["ee", "electrical"],
    }
    non_btech_program_tokens = {"bsc", "msc", "bca", "mca", "bba", "mba", "mpt", "bpt", "blis", "pharmacy", "nursing"}

    def detect_btech_branch(text, kw_list):
        merged = f"{text} {' '.join(kw_list)}"
        for branch_code, aliases in btech_branch_tokens.items():
            if any(re.search(r"\b" + re.escape(alias) + r"\b", merged) for alias in aliases):
                return branch_code
        return None

    def get_btech_course_row(branch_code, institute_hint=None):
        course_df_local = sheets.get('Course_info')
        if course_df_local is None:
            return None
        aliases = btech_branch_tokens.get(branch_code, [])
        for _, row in course_df_local.iterrows():
            if institute_hint and institute_hint not in str(row.get("department", "")).lower():
                continue
            c_name = str(row.get('course_name', '')).lower()
            if "b.tech" in c_name or "btech" in c_name:
                if any(re.search(r"\b" + re.escape(alias) + r"\b", c_name) for alias in aliases):
                    return row
        return None

    def get_course_fee_info(course_name):
        fees_df_local = sheets.get('Fees_info')
        if fees_df_local is None or not course_name:
            return None, None

        target = clean_text(str(course_name)).replace(" ", "")
        for _, row in fees_df_local.iterrows():
            fee_course_name = str(row.get('course_name', '')).strip()
            fee_name_norm = clean_text(fee_course_name).replace(" ", "")
            if not fee_name_norm:
                continue
            if target in fee_name_norm or fee_name_norm in target:
                fee = str(row.get('tuition_fees', '')).strip()
                mode = str(row.get('payment_mode', '')).strip()
                if not fee or fee.lower() == "nan":
                    fee = None
                if not mode or mode.lower() == "nan":
                    mode = None
                return fee, mode
        return None, None

    def course_token_matches(course_name_text, token):
        """
        Robust token matcher for course names:
        - supports dotted tokens like 'msc.' or 'b.sc'
        - keeps word-boundary behavior for short tokens like 'it'
        """
        c_text = str(course_name_text).lower()
        token_raw = str(token).lower().strip()
        if not token_raw:
            return False
        token_clean = re.sub(r'[^a-z0-9]+', '', token_raw)
        if not token_clean:
            return False

        # BPT / MPT: physiotherapy only (never confuse MPT with MCA or other "master" programs).
        if token_clean == "bpt":
            return "physiotherapy" in c_text and "bachelor" in c_text
        if token_clean == "mpt":
            return "physiotherapy" in c_text and "master" in c_text

        # B.Tech branch short codes: require the right phrase in the title (avoid only "btech" matching every row).
        if "b.tech" in c_text or "btech" in c_text:
            if token_clean == "it":
                return "information technology" in c_text
            if token_clean == "me":
                return "mechanical" in c_text
            if token_clean == "ec":
                return "electronics" in c_text and "communication" in c_text
            if token_clean == "ee":
                return "electrical" in c_text
            if token_clean == "cl":
                return "civil" in c_text
            if token_clean in {"aiml", "ai"}:
                return "artificial intelligence" in c_text or "machine learning" in c_text
            if token_clean == "ce":
                return "computer engineering" in c_text and "computer science" not in c_text
            if token_clean == "cse":
                return "computer science" in c_text

        # Strict word boundary match first.
        if re.search(r'\b' + re.escape(token_clean) + r'\b', c_text):
            return True

        # Fallback normalized contains for dotted/compact variants (e.g. "msc." vs "msc").
        c_norm = re.sub(r'[^a-z0-9]+', '', c_text)
        return token_clean in c_norm

    # If previous turn was "B.Tech eligibility/fees" and user now gives branch, answer directly.
    pending_btech_intent = LAST_CONTEXT.get("pending_btech_intent")
    mentions_non_btech_program = any(tok in keywords for tok in non_btech_program_tokens)
    if pending_btech_intent in {"eligibility", "fees", "info"} and not mentions_non_btech_program:
        selected_branch = detect_btech_branch(q_lower, keywords)
        if selected_branch:
            branch_row = get_btech_course_row(selected_branch, resolved_institute)
            if branch_row is not None:
                full_name = str(branch_row.get('course_name', 'B.Tech')).strip()
                dept = str(branch_row.get('department', '')).strip()
                if pending_btech_intent == "eligibility":
                    eligibility = str(branch_row.get('eligibility', 'Not available right now.')).strip()
                    LAST_CONTEXT["pending_btech_intent"] = None
                    LAST_CONTEXT["last_btech_intent"] = "eligibility"
                    LAST_CONTEXT["course"] = full_name
                    LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                    return f"### 🎓 {full_name}\n\n- **Eligibility:** {eligibility}"
                if pending_btech_intent == "info":
                    duration = str(branch_row.get('duration', '')).strip()
                    eligibility = str(branch_row.get('eligibility', 'Not available right now.')).strip()
                    LAST_CONTEXT["pending_btech_intent"] = None
                    LAST_CONTEXT["last_btech_intent"] = "info"
                    LAST_CONTEXT["course"] = full_name
                    LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                    return (
                        f"### 🎓 {full_name}\n\n"
                        f"- **Department/Institute:** {dept}\n"
                        f"- **Duration:** {duration}\n"
                        f"- **Eligibility:** {eligibility}"
                    )
                fee, _ = get_course_fee_info(full_name)
                if not fee:
                    fee = str(branch_row.get('tuition_fees', branch_row.get('fees', 'Not available right now.'))).strip()
                LAST_CONTEXT["pending_btech_intent"] = None
                LAST_CONTEXT["last_btech_intent"] = "fees"
                LAST_CONTEXT["course"] = full_name
                LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                return f"### 💰 {full_name}\n\n- **Annual Fees:** {fee}"

    # Pronoun-based follow-up should resolve before generic program matching.
    # Example: "what are the fees for it?" / "what are its fees?" after the last course answer.
    has_pronoun_followup = (
        any(token in q_lower for token in [" it ", " this ", " that ", "it?", "this?", "that?", " its ", " its?"])
        or re.search(r"\bits\b", q_lower)
    )
    is_fee_followup = any(kw in keywords for kw in ["fee", "fees", "fess", "paisa", "cost", "pay"])
    explicit_course_tokens = {"bsc", "msc", "bca", "mca", "btech", "mtech", "bba", "mba", "bpt", "mpt", "pharmacy", "nursing", "blis", "ce", "cse", "ec", "ee", "me", "cl"}
    mentions_explicit_course = any(tok in keywords for tok in explicit_course_tokens)
    if (
        LAST_CONTEXT.get("course")
        and has_pronoun_followup
        and is_fee_followup
        and not mentions_explicit_course
        and "hostel" not in q_lower
        and "hostel" not in keywords
    ):
        fee, mode = get_course_fee_info(LAST_CONTEXT["course"])
        if fee:
            LAST_CONTEXT["last_btech_intent"] = "fees"
            if any(kw in q_lower for kw in ["how", "pay", "method", "mode", "way", "process"]) and mode:
                return f"The annual fees for **{LAST_CONTEXT['course']}** is **{fee}**. You can pay via: {mode}."
            return f"### 💰 {LAST_CONTEXT['course']}\n\n- **Annual Fees:** {fee}"

    # Pronoun-based follow-up for eligibility/duration/info (avoid "it" => IT).
    is_eligibility_followup = any(kw in keywords for kw in ["eligibility", "laykaat", "requirement", "criteria", "condition", "marks", "mark"])
    is_duration_followup = "duration" in keywords
    is_info_followup = any(kw in keywords for kw in ["info", "information", "details"])
    if (
        LAST_CONTEXT.get("course")
        and has_pronoun_followup
        and (is_eligibility_followup or is_duration_followup or is_info_followup)
        and not mentions_explicit_course
        and "hostel" not in q_lower
        and "hostel" not in keywords
    ):
        course_df_follow = sheets.get("Course_info")
        if course_df_follow is not None and not course_df_follow.empty:
            target = clean_text(str(LAST_CONTEXT["course"])).replace(" ", "")
            best_row = None
            best_score = -1
            for _, row in course_df_follow.iterrows():
                c_name = str(row.get("course_name", "")).strip()
                if not c_name:
                    continue
                c_norm = clean_text(c_name).replace(" ", "")
                # Exact-ish match wins; otherwise keep a reasonable contains match.
                score = 0
                if c_norm == target:
                    score = 100
                elif target and (target in c_norm or c_norm in target):
                    score = 50
                if score > best_score:
                    best_score = score
                    best_row = row
            if best_row is not None and best_score >= 50:
                full_name = str(best_row.get("course_name", "")).strip() or LAST_CONTEXT["course"]
                dept = str(best_row.get("department", "")).strip()
                duration = str(best_row.get("duration", "")).strip()
                eligibility = str(best_row.get("eligibility", "")).strip()
                LAST_CONTEXT["course"] = full_name
                LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                if is_eligibility_followup and not (is_duration_followup or is_info_followup):
                    return f"### 🎓 {full_name}\n\n- **Eligibility:** {eligibility}"
                return (
                    f"### 🎓 {full_name}\n\n"
                    f"- **Department/Institute:** {dept}\n"
                    f"- **Duration:** {duration}\n"
                    f"- **Eligibility:** {eligibility}"
                )

    # If user sends only a B.Tech branch code/name after a previous B.Tech intent,
    # keep returning the same concise branch-specific format.
    selected_branch = detect_btech_branch(q_lower, keywords)
    short_branch_followup = len(keywords) <= 2 and selected_branch is not None and not mentions_non_btech_program
    previous_btech_context = "b.tech" in str(LAST_CONTEXT.get("course", "")).lower() or LAST_CONTEXT.get("last_btech_intent") in {"eligibility", "fees", "info"}
    if short_branch_followup and previous_btech_context:
        branch_row = get_btech_course_row(selected_branch, resolved_institute)
        if branch_row is not None:
            full_name = str(branch_row.get('course_name', 'B.Tech')).strip()
            dept = str(branch_row.get('department', '')).strip()
            intent = LAST_CONTEXT.get("last_btech_intent") or "eligibility"
            LAST_CONTEXT["course"] = full_name
            LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
            if intent == "fees":
                fee, _ = get_course_fee_info(full_name)
                if not fee:
                    fee = str(branch_row.get('tuition_fees', branch_row.get('fees', 'Not available right now.'))).strip()
                return f"### 💰 {full_name}\n\n- **Annual Fees:** {fee}"
            if intent == "info":
                duration = str(branch_row.get('duration', '')).strip()
                eligibility = str(branch_row.get('eligibility', 'Not available right now.')).strip()
                return (
                    f"### 🎓 {full_name}\n\n"
                    f"- **Department/Institute:** {dept}\n"
                    f"- **Duration:** {duration}\n"
                    f"- **Eligibility:** {eligibility}"
                )
            eligibility = str(branch_row.get('eligibility', 'Not available right now.')).strip()
            return f"### 🎓 {full_name}\n\n- **Eligibility:** {eligibility}"
    
    # NEW: HARD-CODED PRIORITY FOR B.TECH ELIGIBILITY
    # Check if user is asking about B.Tech eligibility/requirements
    is_btech_eligibility = ("btech" in keywords or "b.tech" in q_lower) and any(kw in keywords for kw in ["eligibility", "laykaat", "requirement", "criteria", "condition", "mark", "marks", "exam", "score", "entrance", "gujcet", "jee"])
    is_btech_fees = ("btech" in keywords or "b.tech" in q_lower) and any(kw in keywords for kw in ["fee", "fees", "fess", "paisa", "cost", "pay"])
    is_btech_all_info = ("btech" in keywords or "b.tech" in q_lower) and (
        any(kw in keywords for kw in ["info", "information", "details", "everything", "summary", "overview"])
        or ("all" in keywords and "info" in keywords)
        or ("all" in keywords and "information" in keywords)
    )
    selected_branch = detect_btech_branch(q_lower, keywords)

    if is_btech_eligibility and not selected_branch:
        LAST_CONTEXT["pending_btech_intent"] = "eligibility"
        if prefers_gujarati:
            return "B.Tech ni kai branch ni eligibility joiye che? Please branch bolo: **CE (Computer Engineering) / IT / CSE / EC / ME / CL (Civil Engineering) / EE**."
        return "Which B.Tech branch eligibility do you want? Please choose: **CE (Computer Engineering) / IT / CSE / EC / ME / CL (Civil Engineering) / EE**."

    if is_btech_fees and not selected_branch:
        LAST_CONTEXT["pending_btech_intent"] = "fees"
        if prefers_gujarati:
            return "B.Tech ni kai branch ni fees joiye che? Please branch bolo: **CE (Computer Engineering) / IT / CSE / EC / ME / CL (Civil Engineering) / EE**."
        return "Which B.Tech branch fees do you want? Please choose: **CE (Computer Engineering) / IT / CSE / EC / ME / CL (Civil Engineering) / EE**."

    if is_btech_all_info and not selected_branch:
        LAST_CONTEXT["pending_btech_intent"] = "info"
        if prefers_gujarati:
            return "B.Tech ni kai branch ni badhi information joiye che? Please branch bolo: **CE (Computer Engineering) / IT / CSE / EC / ME / CL (Civil Engineering) / EE**."
        return "Which B.Tech branch do you want full information for? Please choose: **CE (Computer Engineering) / IT / CSE / EC / ME / CL (Civil Engineering) / EE**."

    if is_btech_all_info and selected_branch:
        branch_row = get_btech_course_row(selected_branch, resolved_institute)
        if branch_row is not None:
            full_name = str(branch_row.get('course_name', 'B.Tech')).strip()
            dept = str(branch_row.get('department', '')).strip()
            duration = str(branch_row.get('duration', '')).strip()
            eligibility = str(branch_row.get('eligibility', 'Not available right now.')).strip()
            LAST_CONTEXT["pending_btech_intent"] = None
            LAST_CONTEXT["last_btech_intent"] = "info"
            LAST_CONTEXT["course"] = full_name
            LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
            return (
                f"### 🎓 {full_name}\n\n"
                f"- **Department/Institute:** {dept}\n"
                f"- **Duration:** {duration}\n"
                f"- **Eligibility:** {eligibility}"
            )

    if is_btech_eligibility:
        # If branch is already specified in first query, return branch-specific eligibility.
        if selected_branch:
            branch_row = get_btech_course_row(selected_branch, resolved_institute)
            if branch_row is not None:
                full_name = str(branch_row.get('course_name', 'B.Tech')).strip()
                dept = str(branch_row.get('department', '')).strip()
                eligibility = str(branch_row.get('eligibility', 'Not available right now.')).strip()
                LAST_CONTEXT["pending_btech_intent"] = None
                LAST_CONTEXT["last_btech_intent"] = "eligibility"
                LAST_CONTEXT["course"] = full_name
                LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                return f"### 🎓 {full_name}\n\n- **Eligibility:** {eligibility}"

        # Look for B.Tech eligibility entry in the structured dataset
        for item in STRUCTURED_DATASET:
            if "eligibility criteria" in item.get("Question", "").lower() and "b.tech" in item.get("Question", "").lower():
                return item.get("Answer")

    # Direct fees resolver: prefer exact course-token match from Fees_info.
    # This avoids wrong cross-matches like "Msc IT fees" -> "Bsc IT".
    asks_fees_global = any(kw in keywords for kw in ["fee", "fees", "fess", "paisa", "cost", "pay"])
    if asks_fees_global:
        fees_df_direct = sheets.get('Fees_info')
        if fees_df_direct is not None:
            fee_noise_tokens = {"fee", "fees", "fess", "paisa", "cost", "pay", "annual", "yearly", "for", "of", "it", "this", "that"}
            query_tokens = [kw for kw in keywords if kw not in fee_noise_tokens]
            if query_tokens:
                required_tokens = []
                optional_tokens = []
                for token in query_tokens:
                    # Special handling: many sheet rows use full names and may not include BPT/MPT short code.
                    if token == "bpt":
                        required_tokens.extend(["bachelor", "physiotherapy"])
                        optional_tokens.append("bpt")
                    elif token == "mpt":
                        required_tokens.extend(["master", "physiotherapy"])
                        optional_tokens.append("mpt")
                    else:
                        required_tokens.append(token)
                # Keep order but remove duplicates
                required_tokens = list(dict.fromkeys(required_tokens))
                optional_tokens = list(dict.fromkeys(optional_tokens))

                fee_candidates = []
                for _, row in fees_df_direct.iterrows():
                    c_name = str(row.get('course_name', '')).strip()
                    c_name_lower = c_name.lower()
                    if not c_name:
                        continue

                    # Every required query token must match the course name.
                    if not all(course_token_matches(c_name_lower, token) for token in required_tokens):
                        continue
                    match_score = sum(1 for token in required_tokens if course_token_matches(c_name_lower, token))
                    match_score += sum(1 for token in optional_tokens if course_token_matches(c_name_lower, token))
                    fee_value = str(row.get('tuition_fees', '')).strip()
                    payment_mode = str(row.get('payment_mode', '')).strip()
                    fee_candidates.append((match_score, len(c_name), c_name, fee_value, payment_mode))

                if fee_candidates:
                    # "fees of bca" should return both Online and Regular/Offline BCA (if available).
                    asks_bca_only = "bca" in query_tokens and "online" not in keywords and "offline" not in keywords
                    if asks_bca_only:
                        bca_rows = []
                        for _, _, c_name, fee_value, _ in fee_candidates:
                            c_lower = c_name.lower()
                            if not re.search(r"\bbca\b", c_lower):
                                continue
                            mode_label = "Online BCA" if "online" in c_lower else "Regular BCA"
                            fee_text = fee_value if fee_value and fee_value.lower() != "nan" else "Not available right now."
                            bca_rows.append((mode_label, c_name, fee_text))

                        if bca_rows:
                            # Remove duplicates while preserving order.
                            seen = set()
                            unique_rows = []
                            for item in bca_rows:
                                key = (item[0].lower(), item[2].lower())
                                if key in seen:
                                    continue
                                seen.add(key)
                                unique_rows.append(item)

                            LAST_CONTEXT["course"] = "BCA"
                            resp = "### 💰 BCA Fees\n\n"
                            for mode_label, c_name, fee_text in unique_rows:
                                resp += f"- **{mode_label}** ({c_name}): {fee_text}\n"
                            return resp.strip()

                    fee_candidates.sort(key=lambda x: (-x[0], x[1]))
                    _, _, selected_course, selected_fee, selected_mode = fee_candidates[0]
                    LAST_CONTEXT["course"] = selected_course
                    LAST_CONTEXT["last_btech_intent"] = "fees" if "b.tech" in selected_course.lower() else LAST_CONTEXT.get("last_btech_intent")
                    if not selected_fee or selected_fee.lower() == "nan":
                        selected_fee = "Not available right now."
                    if not selected_mode or selected_mode.lower() == "nan":
                        selected_mode = ""
                    if any(kw in keywords for kw in ["how", "method", "mode", "way", "process"]) and selected_mode:
                        return f"### 💰 {selected_course}\n\n- **Annual Fees:** {selected_fee}\n- **Payment Mode:** {selected_mode}"
                    return f"### 💰 {selected_course}\n\n- **Annual Fees:** {selected_fee}"
    
    # NEW: GENERIC PROGRAM HANDLER (Highest Priority for any program query)
    # This matches BPT, MPT, B.Tech, BCA, etc. by searching Course_info
    course_df = sheets.get('Course_info')
    if course_df is not None:
        # Exclude common words to find the potential program name
        exclude = {
            "tell", "about", "all", "information", "info", "give", "me", "show", "details",
            "program", "course", "degree", "the",
            # Intent/meta tokens — not part of course titles (avoid "btech + eligibility" matching every B.Tech row)
            "eligibility", "laykaat", "requirement", "criteria", "condition", "mark", "marks",
            "exam", "score", "entrance", "gujcet", "jee",
            "fee", "fees", "fess", "cost", "pay", "paisa",
            "charusat", "university",
        }
        program_keywords = [kw for kw in keywords if kw not in exclude]
        
        # Check if query is specifically about M.Tech (handle both 'm.tech' and 'mtech' via keywords)
        if "mtech" in keywords:
            program_keywords = ["mtech"]

        explicit_degree_tokens = [t for t in program_keywords if t in {"bsc", "msc", "bca", "mca", "btech", "mtech", "bba", "mba"}]

        def row_matches_btech_ce_vs_cse(c_name_lower):
            """B.Tech Computer Engineering vs Computer Science and Engineering."""
            if "btech" not in keywords and "b.tech" not in q_lower:
                return True
            wants_cse = "cse" in program_keywords or (
                "computer" in program_keywords and "science" in program_keywords
            )
            wants_ce_only = (
                "computer" in program_keywords
                and "engineering" in program_keywords
                and not wants_cse
            )
            if wants_cse:
                if "computer science" not in c_name_lower:
                    return False
            elif wants_ce_only:
                if "computer science" in c_name_lower:
                    return False
            return True

        def row_matches_institute(row):
            if not resolved_institute:
                return True
            dept = str(row.get("department", "")).lower()
            return resolved_institute in dept

        if program_keywords:
            best_match = None
            max_pk_match = 0
            
            # SPECIAL CASE: vague MPT/BPT (e.g. just "BPT" / "physiotherapy") → ARIP overview via search.
            # Eligibility, duration, fees, syllabus, admission, etc. must use Course_info (not MCA hijack).
            asks_physio_course_facts = any(
                kw in keywords
                for kw in [
                    "eligibility", "laykaat", "requirement", "criteria", "condition",
                    "duration", "admission", "entrance",
                    "fee", "fees", "fess", "syllabus",
                    "information", "details",
                ]
            )
            is_physio_query = any(pk in ["mpt", "bpt", "physiotherapy"] for pk in program_keywords)
            # If user includes specialization terms (e.g. neurological/musculoskeletal),
            # we must resolve via Course_info instead of generic ARIP overview.
            has_physio_specialization_terms = any(
                pk not in {"mpt", "bpt", "physiotherapy"} for pk in program_keywords
            )
            if is_physio_query and not asks_physio_course_facts and not has_physio_specialization_terms:
                pass
            else:
                for _, row in course_df.iterrows():
                    c_name = str(row.get('course_name', '')).lower()
                    if not row_matches_institute(row):
                        continue
                    if not row_matches_btech_ce_vs_cse(c_name):
                        continue
                    if explicit_degree_tokens and not all(course_token_matches(c_name, t) for t in explicit_degree_tokens):
                        continue
                    
                    # Count how many program keywords match this course name
                    pk_match_count = sum(1 for pk in program_keywords if course_token_matches(c_name, pk))
                    
                    if pk_match_count > max_pk_match:
                        max_pk_match = pk_match_count
                        best_match = row
                    elif pk_match_count > 0 and pk_match_count == max_pk_match:
                        # TIE BREAKER:
                        if best_match is not None:
                            c_name_raw = str(row.get('course_name', '')).lower()
                            best_name_raw = str(best_match.get('course_name', '')).lower()
                            
                            c_name_norm = c_name_raw.replace(".", "").replace(" ", "")
                            best_name_norm = best_name_raw.replace(".", "").replace(" ", "")
                            pk_norm = "".join(program_keywords).replace(".", "").replace(" ", "")
                            
                            # PRIORITY 1: Exact match (normalized)
                            if c_name_norm == pk_norm and best_name_norm != pk_norm:
                                best_match = row
                                continue
                            if best_name_norm == pk_norm and c_name_norm != pk_norm:
                                continue
                            
                            # PRIORITY 2: Prefer regular courses over Online ones unless "online" is in query
                            asked_online = "online" in keywords
                            is_current_online = "online" in c_name_raw
                            is_best_online = "online" in best_name_raw
                            if not asked_online:
                                if is_current_online and not is_best_online:
                                    continue # Keep best
                                if not is_current_online and is_best_online:
                                    best_match = row
                                    continue
                            
                            # PRIORITY 3: Prefer shorter course name (more specific)
                            if len(c_name_raw) < len(best_name_raw):
                                best_match = row

                if best_match is not None and (max_pk_match >= 1):
                    asks_fees = any(kw in keywords for kw in ["fee", "fees", "fess", "paisa", "cost", "pay"])
                    asks_seats = any(kw in keywords for kw in ["seat", "seats", "intake", "capacity", "vacancy", "vacancies", "ketli", "kiti", "kitli"])
                    # Check if there are multiple matches for the same keyword
                    # e.g., 'mtech' has many specializations
                    all_matching_courses = []
                    for _, row in course_df.iterrows():
                        c_name = str(row.get('course_name', '')).lower()
                        if not row_matches_institute(row):
                            continue
                        if not row_matches_btech_ce_vs_cse(c_name):
                            continue
                        if explicit_degree_tokens and not all(course_token_matches(c_name, t) for t in explicit_degree_tokens):
                            continue
                        pk_match_count = sum(1 for pk in program_keywords if course_token_matches(c_name, pk))
                        if pk_match_count == max_pk_match:
                            # Tie break for 'online'
                            asked_online = "online" in keywords
                            is_online = "online" in c_name
                            if asked_online == is_online:
                                all_matching_courses.append(row)
                    
                    if len(all_matching_courses) > 1:
                        if asks_fees:
                            resp = f"### 💰 Fee details for '{' '.join(program_keywords).upper()}':\n\n"
                            for row in all_matching_courses:
                                c_name = str(row.get('course_name', '')).strip()
                                dept = str(row.get('department', '')).strip()
                                fee, _ = get_course_fee_info(c_name)
                                fee_text = fee if fee else "Not available right now."
                                resp += f"- **{c_name}** ({dept}): **{fee_text}**\n"
                            return resp

                        if asks_seats:
                            resp = f"### 🎓 Seat Intake for '{' '.join(program_keywords).upper()}':\n\n"
                            for row in all_matching_courses:
                                c_name = str(row.get('course_name', '')).strip()
                                intake = str(row.get('intake', '')).strip()
                                intake_text = intake if intake and intake.lower() != 'nan' else 'Not available right now.'
                                resp += f"- **{c_name}**: **{intake_text}**\n"
                            return resp

                        # Return a list of all matching courses
                        resp = f"### 🎓 Multiple programs found for '{' '.join(program_keywords).upper()}':\n\n"
                        for row in all_matching_courses:
                            c_name = str(row.get('course_name', ''))
                            duration = str(row.get('duration', ''))
                            dept = str(row.get('department', ''))
                            resp += f"- **{c_name}** ({dept})\n"
                        resp += "\n*Please ask for a specific specialization to get more details.*"
                        return resp
                    
                    # Single best match
                    duration = str(best_match.get('duration', ''))
                    eligibility = str(best_match.get('eligibility', ''))
                    dept = str(best_match.get('department', ''))
                    full_name = str(best_match.get('course_name', ''))
                    intake = str(best_match.get('intake', '')).strip()
                    intake_text = intake if intake and intake.lower() != 'nan' else 'Not available right now.'
                    if asks_seats:
                        LAST_CONTEXT["course"] = full_name
                        LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                        return f"### 🎓 {full_name}\n\n- **Intake Seats:** {intake_text}\n- **Department/Institute:** {dept}\n- **Duration:** {duration}\n- **Eligibility:** {eligibility}"
                    if asks_fees:
                        fee, mode = get_course_fee_info(full_name)
                        fee_text = fee if fee else "Not available right now."
                        LAST_CONTEXT["course"] = full_name
                        LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                        LAST_CONTEXT["last_btech_intent"] = "fees" if "b.tech" in full_name.lower() else LAST_CONTEXT.get("last_btech_intent")
                        if any(kw in keywords for kw in ["how", "method", "mode", "way", "process"]) and mode:
                            return f"### 💰 {full_name}\n\n- **Annual Fees:** {fee_text}\n- **Payment Mode:** {mode}"
                        return f"### 💰 {full_name}\n\n- **Annual Fees:** {fee_text}"
                    LAST_CONTEXT["course"] = full_name
                    LAST_CONTEXT["department"] = dept if dept else LAST_CONTEXT.get("department")
                    return f"### 🎓 {full_name}\n\n" \
                            f"- **Department/Institute:** {dept}\n" \
                            f"- **Duration:** {duration}\n" \
                            f"- **Eligibility:** {eligibility}"

    # NEW: HARD-CODED PRIORITY FOR HOSTEL FEES
    # We check if 'hostel' and 'fee' are in keywords, 
    # BUT we must make sure it's not a course query like 'm.tech' or 'mtech'
    is_hostel_fee_query = "hostel" in keywords and ("fee" in keywords or "fees" in keywords)
    is_any_course_query = any(kw in keywords for kw in ["mtech", "mca", "msc", "btech", "bca", "bsc", "mpt", "bpt"])
    
    if is_hostel_fee_query and not is_any_course_query:
        for item in STRUCTURED_DATASET:
            if "hostel fees ketli chhe" in item.get("Question", "").lower():
                return item.get("Answer")

    # NEW: HARD-CODED PRIORITY FOR HOSTEL FEES (To avoid any RAG/LLM confusion)
    # (Moved lower to let more specific queries win)
    
    # We let Spoural queries fall through to search_all_sheets and RAG for LLM processing
    # as requested by the user ("llm trough read karav").
    
    # NEW: HARD-CODED PRIORITY FOR SPOURAL (To avoid course info hijacking)
    is_spoural_main_query = any(kw in keywords for kw in ["spoural", "event", "events"])
    if is_spoural_main_query:
        if any(kw in keywords for kw in ["all", "whole", "full", "list", "information", "info", "give", "show"]) or len(keywords) == 1:
            summary_info = []
            for item in SPOURAL_DATASET:
                if "Summary" in item.get("category", ""):
                    summary_info.append(item.get("full_info"))
            
            if summary_info:
                return "\n\n".join(summary_info)

    # NEW: HARD-CODED PRIORITY FOR SPORTS (To avoid course info hijacking)
    is_sports_query = any(kw in keywords for kw in ["sports", "sport", "game", "games"])
    if is_sports_query and any(kw in keywords for kw in ["all", "whole", "full", "list", "information", "info", "give", "show"]):
        sports_summary = ""
        all_sports = []
        for item in SPOURAL_DATASET:
            if item.get("category") == "Sports Events Summary":
                sports_summary = item.get("full_info")
            elif item.get("category") == "Sports Events":
                all_sports.append(item.get("full_info"))
        
        if all_sports:
            resp = sports_summary + "\n\n" if sports_summary else "### 🏆 CHARUSAT Spoural'26 Sports Events\n\n"
            resp += "\n".join(all_sports)
            return resp
    
    # NEW: Specific sports event matching to prevent course hijacking (e.g. cricket, football)
    if is_sports_query or any(kw in keywords for kw in ["cricket", "football", "volleyball", "kabaddi", "chess", "badminton", "basketball", "handball", "tug of war", "frisbee"]):
        for item in SPOURAL_DATASET:
            if item.get("category") == "Sports Events":
                # Check if the event name is in the query
                if any(kw in item["name"].lower() for kw in keywords):
                    return item["full_info"]

    # 1. Specific handling for Syllabus (High priority)
    if "syllabus" in keywords:
        syllabus_df = sheets.get('Syllabus')
        course_df = sheets.get('Course_info')
        if syllabus_df is not None:
            # Exclude "syllabus" and filler words to find the department/institute
            exclude = {"syllabus", "list", "show", "give", "me", "tell", "about", "in", "at", "who", "are", "name", "all", "the", "of", "any", "some", "charusat", "university"}
            dept_candidates = [kw for kw in keywords if kw not in exclude]
            
            if dept_candidates:
                # NEW: Detect explicit institute mentions (e.g. 'DEPSTAR', 'CSPIT')
                institutes_list = ["cspit", "depstar", "rpcp", "pdpias", "cmpica", "iiim", "i2im", "arip", "mtin", "bdias", "cips", "class"]
                explicit_institutes = [inst for inst in institutes_list if inst in dept_candidates]

                # NEW: Try to find which department this course belongs to first using Course_info sheet
                target_depts = []
                display_name = " ".join(dept_candidates).upper()
                
                # SPECIAL HANDLING: BPT/MPT to include Physiotherapy keywords for matching
                # ALSO: Remove 'sem', 'semester', and numbers for Course_info lookup to avoid matching failures
                lookup_candidates = [cand for cand in dept_candidates if cand not in ["sem", "semester"] and not cand.isdigit()]
                if "bpt" in dept_candidates or "mpt" in dept_candidates:
                    lookup_candidates.append("physiotherapy")
                
                if course_df is not None:
                    matched_courses = []
                    
                    # --- STRATEGY: Try 'AND' match first for multiple keywords (e.g. 'BSC' and 'IT') ---
                    # This prevents 'BSC IT' from matching 'BSC Nursing' (MTIN) or 'BSC' (PDPIAS)
                    if len(lookup_candidates) >= 2:
                        for _, row in course_df.iterrows():
                            c_name = str(row.get('course_name', '')).lower()
                            c_dept = str(row.get('department', '')).lower()
                            # Check if ALL keywords match this course name OR its department
                            if all(re.search(r'\b' + re.escape(cand) + r'\b', c_name) or re.search(r'\b' + re.escape(cand) + r'\b', c_dept) for cand in lookup_candidates):
                                dept = str(row.get('department', '')).strip()
                                if dept and dept.lower() not in target_depts:
                                    target_depts.append(dept.lower())
                                matched_courses.append(str(row.get('course_name', '')))
                    
                    # --- FALLBACK: If no 'AND' match, try matching ANY keyword ---
                    if not target_depts:
                        for _, row in course_df.iterrows():
                            c_name = str(row.get('course_name', '')).lower()
                            # Use word boundaries for course names
                            if any(re.search(r'\b' + re.escape(cand) + r'\b', c_name) for cand in lookup_candidates):
                                dept = str(row.get('department', '')).strip()
                                if dept and dept.lower() not in target_depts:
                                    target_depts.append(dept.lower())
                                
                                # Keep track of the actual course name for display if it's a specific match
                                if any(cand == c_name or re.search(r'\b' + re.escape(cand) + r'\b', c_name) for cand in lookup_candidates):
                                    matched_courses.append(str(row.get('course_name', '')))
                    
                    if len(matched_courses) == 1:
                        display_name = matched_courses[0]
                    elif len(dept_candidates) >= 1:
                        # If multiple matches, keep the user's specific terminology (e.g. "Bsc IT")
                        display_name = " ".join(dept_candidates).title()
                
                # Combine search terms: original candidates + identified departments
                search_terms = dept_candidates + target_depts
                # Add physiotherapy to search terms if BPT/MPT is present to help find ARIP row in Syllabus
                if "bpt" in dept_candidates or "mpt" in dept_candidates:
                    search_terms.append("physiotherapy")
                
                # Define high-weight keywords that should almost certainly identify the department
                high_weight_keywords = ["microbiology", "nursing", "physiotherapy", "pharmacy", "management", "biotechnology", "biochemistry", "chemistry"]
                
                best_matches = []
                for _, row in syllabus_df.iterrows():
                    # Check all columns for the department name match
                    row_text = " ".join(str(val).lower() for val in row.values if str(val) != "nan")
                    
                    # Count how many search terms match this row to find the most specific one
                    # Use word boundaries to avoid matching 'IT' in 'INSTITUTE'
                    match_count = 0
                    for term in search_terms:
                        if re.search(r'\b' + re.escape(term) + r'\b', row_text):
                            # Give much higher weight to identified departments and high-weight keywords
                            if term in target_depts or term in high_weight_keywords:
                                match_count += 10
                            else:
                                match_count += 1
                    
                    # If we have target_depts, we MUST match at least one of them to consider this row relevant
                    # unless target_depts is empty.
                    # CRITICAL: If an institute was explicitly mentioned, only allow that institute.
                    is_relevant = True
                    if explicit_institutes:
                        is_relevant = any(re.search(r'\b' + re.escape(inst) + r'\b', row_text) for inst in explicit_institutes)
                    elif target_depts:
                        # Be strict: if we found a department from Course_info, the row MUST mention it
                        is_relevant = any(re.search(r'\b' + re.escape(dept) + r'\b', row_text) for dept in target_depts)
                    
                    if match_count > 0 and is_relevant:
                        dept_name = str(row.get('department', row.get('Department', ''))).strip()
                        link = ""
                        for val in row.values:
                            if "http" in str(val):
                                link = str(val).strip()
                                break
                        
                        if link:
                            best_matches.append({
                                "dept": dept_name,
                                "link": link,
                                "count": match_count
                            })
                
                if best_matches:
                    # Sort by match count descending to get the most specific result
                    best_matches.sort(key=lambda x: x['count'], reverse=True)
                    top_count = best_matches[0]['count']
                    top_matches = [m for m in best_matches if m['count'] == top_count]
                    
                    if len(top_matches) == 1:
                        m = top_matches[0]
                        if is_gujarati(question):
                            return f"તમે **{display_name}** માટેનો સિલેબસ આ લિંક પરથી મેળવી શકો છો:\n{m['link']}"
                        return f"You can find the syllabus for **{display_name}** at this link:\n{m['link']}"
                    else:
                        # Multiple specific matches, list them
                        resp = f"You can find the syllabus for **{display_name}** at these links:\n\n"
                        for m in top_matches:
                            resp += f"- **{m['dept']}**: {m['link']}\n"
                        return resp

            # If no specific department match, but they just asked "syllabus", list all
            all_syllabi = []
            for _, row in syllabus_df.iterrows():
                dept = str(row.get('department', row.get('Department', ''))).strip()
                link = str(row.get('syllabus', row.get('Syllabus', ''))).strip()
                if "http" not in link:
                    for val in row.values:
                        if "http" in str(val):
                            link = str(val).strip()
                            break
                if dept and "http" in link:
                    all_syllabi.append(f"- **{dept}**: {link}")
            
            if all_syllabi:
                resp = "Here are the syllabus links for various departments at CHARUSAT:\n\n" + "\n".join(all_syllabi)
                return resp

    # 1. Specific handling for "charusat" university info (Highest priority)
    if len(keywords) == 1 and "charusat" in keywords:
        university_df = sheets.get('University')
        if university_df is not None and not university_df.empty:
            row = university_df.iloc[0]
            about = str(row.get('about_university', ''))
            if about and about != 'nan':
                return about

    # 2. Specific handling for Holidays (Highest priority)
    if any(kw in keywords for kw in ["holiday", "holidays", "vacation", "off", "closed", "rain", "raining", "emergency", "flood", "cyclone"]):
        # Check for emergency/situational holiday (e.g. heavy rain)
        if any(kw in keywords for kw in ["rain", "raining", "emergency", "flood", "cyclone"]):
            return "In case of emergency situations like heavy rain or other unforeseen circumstances, the University will notify you regarding any changes in schedule via your official WhatsApp groups or email."
        
        holiday_df = sheets.get('Holiday')
        
        # Determine target date
        target_date = datetime.now() # Default today
        date_name = "today"
        
        if "tomorrow" in q_lower:
            target_date = target_date + timedelta(days=1)
            date_name = "tomorrow"
        elif "yesterday" in q_lower:
            target_date = target_date - timedelta(days=1)
            date_name = "yesterday"
        
        # 1a. Check for weekend holiday (Sunday, 2nd/4th Saturday)
        is_weekend, weekend_type = is_weekend_holiday(target_date)
        
        # 1b. Check the Holiday sheet
        sheet_holiday = None
        if holiday_df is not None:
            target_date_str = target_date.strftime("%Y-%m-%d")
            for _, row in holiday_df.iterrows():
                h_date = str(row.get('Date ', row.get('Date', '')))
                if target_date_str in h_date:
                    sheet_holiday = str(row.get('Holiday', ''))
                    break
        
        # 1c. Handle specific weekend queries (e.g. "Is 2nd saturday holiday?")
        if "2nd saturday" in q_lower:
            return "Yes, the 2nd Saturday of every month is a holiday at CHARUSAT."
        if "4th saturday" in q_lower:
            return "Yes, the 4th Saturday of every month is a holiday at CHARUSAT."
        if "saturday" in q_lower and "2nd" not in q_lower and "4th" not in q_lower:
            return "At CHARUSAT, only the 2nd and 4th Saturdays are holidays. Other Saturdays are working days."
        if "sunday" in q_lower:
            return "Yes, Sunday is always a holiday at CHARUSAT."

        # 1d. Final response for today/tomorrow/yesterday
        if any(kw in q_lower for kw in ["today", "tomorrow", "yesterday"]):
            if sheet_holiday:
                return f"Yes, {date_name} ({target_date.strftime('%d %B')}) is a holiday for **{sheet_holiday}**."
            if is_weekend:
                return f"Yes, {date_name} ({target_date.strftime('%d %B')}) is a holiday because it's a **{weekend_type}**."
            return f"No, {date_name} ({target_date.strftime('%d %B')}) is a working day."

        # 1e. General list or specific search
        if holiday_df is not None:
            exclude = {"holiday", "holidays", "vacation", "is", "there", "any", "of", "on", "at", "charusat", "university", "list", "show", "give", "me", "tell", "please", "the", "a", "an", "off", "closed", "what", "when", "which", "are"}
            holiday_candidates = [kw for kw in keywords if kw not in exclude]
            
            # If the query is about listing holidays (e.g. "list of holidays", "all holidays")
            is_list_query = any(kw in q_lower for kw in ["list", "show", "all", "what are", "give me"]) or not holiday_candidates
            
            if holiday_candidates and not is_list_query:
                # Try to find the specific holiday with fuzzy matching
                all_holiday_names = [str(row.get('holiday', '')).lower() for _, row in holiday_df.iterrows()]
                
                for cand in holiday_candidates:
                    # 1. Try exact substring match first
                    for _, row in holiday_df.iterrows():
                        h_name = str(row.get('holiday', '')).lower()
                        if cand in h_name or h_name in cand:
                            h_display = str(row.get('holiday', ''))
                            h_date = str(row.get('date', ''))
                            if " " in h_date: h_date = h_date.split(" ")[0]
                            return f"Yes, there is a holiday for **{h_display}**."
                    
                    # 2. Try fuzzy matching
                    best_match = fuzzy_match(cand, all_holiday_names, cutoff=0.7)
                    if best_match:
                        # Find the row for this match
                        for _, row in holiday_df.iterrows():
                            if str(row.get('holiday', '')).lower() == best_match:
                                h_display = str(row.get('holiday', ''))
                                return f"Yes, there is a holiday for **{h_display}**."
                
                # If not found in sheet, use LLM to explain nicely
                holiday_list_str = "\n".join([f"- {row.get('Holiday', '')}: {row.get('Date ', row.get('Date', ''))}" for _, row in holiday_df.iterrows()])
                context = f"Official CHARUSAT Holiday List 2026:\n{holiday_list_str}\n\nNote: Sundays and 2nd/4th Saturdays are also holidays."
                llm_resp = ask_ollama(question, context)
                if llm_resp:
                    return llm_resp
                
                return "According to the official university calendar, that specific day is not listed as a holiday."
            else:
                # List all
                h_list = []
                for _, row in holiday_df.iterrows():
                    h_name = str(row.get('Holiday', ''))
                    h_date = str(row.get('Date ', row.get('Date', '')))
                    if " " in h_date: h_date = h_date.split(" ")[0]
                    if h_name and h_name != "nan":
                        h_list.append(f"- **{h_name}**: {h_date}")
                
                resp = "Here are the university holidays:\n\n"
                resp += "- **Sundays**: Every week\n"
                resp += "- **2nd & 4th Saturdays**: Every month\n"
                if h_list:
                    resp += "\n**Academic Holidays 2026:**\n" + "\n".join(h_list)
                return resp

    # --- FOLLOW-UP CONTEXT HANDLING ---
    # If query asks "fees of it", "duration of it", etc.
    # We use a broader check for follow-ups
    # BUT: if the user mentions a specific course name (and NOT "it/this/that"), it's NOT a follow-up
    has_explicit_course = any(kw in keywords for kw in ["bca", "mca", "btech", "mtech", "bsc", "msc", "bba", "mba", "nursing", "physiotherapy", "pharmacy", "blis", "it", "engineering", "data science"])
    has_pronoun = any(kw in q_lower for kw in ["it", "this", "that"])
    
    # NEW: Exclude hostel/holiday/spoural from follow-up logic to avoid hijacking
    is_hostel_query = "hostel" in keywords
    is_holiday_query = "holiday" in keywords
    is_spoural_query = any(kw in keywords for kw in ["event", "sports", "cultural", "spoural", "activity", "activities", "cricket", "football", "volleyball", "kabaddi", "chess", "badminton", "basketball", "handball", "tug of war", "singing", "dance", "quiz"])
    
    is_follow_up = (not is_hostel_query and not is_holiday_query and not is_spoural_query) and \
                   ((any(kw in q_lower for kw in ["it", "this", "that", "course", "fee", "fees", "fess", "duration", "eligibility"]) or \
                    (len(keywords) <= 3 and any(kw in keywords for kw in ["fee", "fees", "duration", "eligibility", "pay", "cost"]))) \
                    and (has_pronoun or not has_explicit_course))
    
    if is_follow_up and LAST_CONTEXT["course"]:
        # If asking about fees
        if any(kw in keywords for kw in ["fee", "fees", "fess", "paisa", "cost", "pay"]):
            fees_df = sheets.get('Fees_info')
            if fees_df is not None:
                # Match course from context in Fees_info
                for _, row in fees_df.iterrows():
                    c_name = str(row.get('course_name', '')).lower()
                    if LAST_CONTEXT["course"].lower() in c_name or c_name in LAST_CONTEXT["course"].lower():
                        fee = str(row.get('tuition_fees', ''))
                        mode = str(row.get('payment_mode', ''))
                        
                        # Only show payment mode if specifically asked
                        if any(kw in q_lower for kw in ["how", "pay", "method", "mode", "way", "process"]):
                            return f"The annual fees for **{LAST_CONTEXT['course']}** is **{fee}**. You can pay via: {mode}."
                        else:
                            return f"The annual fees for **{LAST_CONTEXT['course']}** is **{fee}**."
            
            # If we couldn't find it in Fees_info but we are sure it's about fees,
            # we don't fall through to RAG yet, we update the question to include context
            question = f"{LAST_CONTEXT['course']} fees"
            # Re-normalize and get keywords for the new question to help search_all_sheets
            q_lower = normalize_question(question)
            keywords = get_keywords(q_lower)
        
        # If asking about duration/eligibility
        if any(kw in keywords for kw in ["duration", "eligibility", "years", "time"]):
            course_df = sheets.get('Course_info')
            if course_df is not None:
                for _, row in course_df.iterrows():
                    c_name = str(row.get('course_name', '')).lower()
                    if LAST_CONTEXT["course"].lower() in c_name or c_name in LAST_CONTEXT["course"].lower():
                        dur = str(row.get('duration', ''))
                        elig = str(row.get('eligibility', ''))
                        return f"The duration for **{LAST_CONTEXT['course']}** is **{dur}** and eligibility is: {elig}."

    # 1. Check for acknowledgments / farewells first (Keep it quick)
    q_words = q_lower.split()
    acknowledgments = {"hello", "hi", "hey", "ok", "okay", "thanks", "thank you", "got it", "nice", "good", "perfect"}
    farewells = {"bye", "by", "goodbye", "see you"}

    if any(word in farewells for word in q_words) and len(q_words) <= 2:        
        return "Goodbye! Have a nice day! Please feel free to come back if you have more queries related to CHARUSAT."

    if all(word in acknowledgments for word in q_words) and len(q_words) > 0:   
        if any(w in ["hello", "hi", "hey"] for w in q_words):
            return "Hello! How can I help you today with information about CHARUSAT?"
        return "You're welcome! Please feel free to ask me another query or doubt related to CHARUSAT."

    # 1. NEW: Specific handling for listing faculties by department/institute
    if any(kw in keywords for kw in ["faculty", "faculties", "teacher", "professor"]):
        faculty_df = sheets.get('Faculties_mem_info')
        if faculty_df is not None:
            # Filter keywords to find potential department/institute names
            # Exclude faculty-related keywords and general verbs/adjectives
            exclude = {"faculty", "faculties", "teacher", "professor", "list", "show", "give", "me", "tell", "about", "in", "at", "who", "are", "name", "all", "the", "of", "any", "some"}
            dept_candidates = [kw for kw in keywords if kw not in exclude]
            
            if dept_candidates:
                matching_faculties = []
                # Try to find which candidate is actually a department
                # We'll check all candidates against the department_id column
                
                for _, row in faculty_df.iterrows():
                    dept_val = str(row.get('department_id', '')).lower()
                    email_val = str(row.get('emai_id', '')).lower()
                    
                    # Check if any candidate matches the department or email
                    if any(cand in dept_val or (len(cand) > 3 and cand in email_val) for cand in dept_candidates):
                        name = str(row.get('member_name', ''))
                        desig = str(row.get('designation', ''))
                        if name and name != "nan" and name != "member_name":
                            matching_faculties.append(f"- **{name}** ({desig})")
                
                if matching_faculties:
                    # Remove duplicates if any
                    matching_faculties = list(dict.fromkeys(matching_faculties))
                    dept_display = dept_candidates[0].upper()
                    
                    # Update context
                    LAST_CONTEXT["department"] = dept_display
                    
                    resp = f"Here are the faculty members of **{dept_display}**:\n\n" + "\n".join(matching_faculties)
                    return resp

    # 3. NEW: Specific handling for listing courses by department/institute
    if any(kw in keywords for kw in ["course", "courses", "program", "programs", "branch", "branches"]):
        course_df = sheets.get('Course_info')
        if course_df is not None:
            # Exclude course-related keywords
            exclude = {"course", "courses", "program", "programs", "branch", "branches", "list", "show", "give", "me", "tell", "about", "in", "at", "who", "are", "name", "all", "the", "of", "any", "some"}
            dept_candidates = [kw for kw in keywords if kw not in exclude]
            
            if dept_candidates:
                matching_courses = []
                primary_dept = dept_candidates[0]
                
                # Check for 'department' or 'department_id' column
                dept_col = 'department' if 'department' in course_df.columns else 'department_id' if 'department_id' in course_df.columns else None
                
                if dept_col:
                    for _, row in course_df.iterrows():
                        dept_val = str(row.get(dept_col, '')).lower()
                        if primary_dept in dept_val:
                            c_name = str(row.get('course_name', ''))
                            duration = str(row.get('duration', ''))
                            if c_name and c_name != "nan" and c_name != "course_name":
                                matching_courses.append(f"- **{c_name}** ({duration})")
                
                if matching_courses:
                    matching_courses = list(dict.fromkeys(matching_courses))
                    
                    # Update context
                    LAST_CONTEXT["department"] = primary_dept.upper()
                    
                    resp = f"Here are the courses offered by **{primary_dept.upper()}**:\n\n" + "\n".join(matching_courses)
                    return resp

    # 4. NEW: Institute-wise placement info (from Placement sheet)
    if any(kw in keywords for kw in ["placement", "placements", "package", "packages"]):
        placements_df = None
        for s_name in ["Placement", "Placements", "Placement_info"]:
            df_candidate = sheets.get(s_name)
            if df_candidate is not None:
                placements_df = df_candidate
                break
        if placements_df is not None:
            # Prefer explicit institute alias (cmpica, cspit, etc.); fallback to resolved_institute.
            inst_aliases = ["cspit", "depstar", "cmpica", "pdpias", "rpcp", "mtin", "arip", "i2im", "iiim", "bdias"]
            query_inst = next((inst for inst in inst_aliases if inst in keywords), None) or resolved_institute
            if query_inst:
                query_inst = str(query_inst).lower()
                matching_rows = []
                for _, row in placements_df.iterrows():
                    row_text = " ".join(str(val).lower() for val in row.values if str(val) != "nan")
                    if query_inst in row_text:
                        matching_rows.append(row)

                if matching_rows:
                    lines = []
                    title_inst = query_inst.upper()
                    asks_top_recruiters = (
                        "recruiter" in keywords
                        or "recruiters" in keywords
                        or ("top" in keywords and ("company" in keywords or "companies" in keywords))
                    )
                    lines.append(f"### 🎓 Placement overview for {title_inst}")

                    def get_row_value(row_obj, aliases):
                        # Case-insensitive lookup across possible column spellings.
                        for alias in aliases:
                            for col in row_obj.index:
                                if str(col).strip().lower() == alias.lower():
                                    value = str(row_obj.get(col, "")).strip()
                                    if value and value.lower() != "nan":
                                        return value
                        return ""

                    for row in matching_rows:
                        inst_name = get_row_value(row, ["institute", "Institute"]) or title_inst
                        prog = get_row_value(row, ["program", "course", "course_name"])
                        year = get_row_value(row, ["year", "batch", "academic_year"])
                        highest = get_row_value(row, ["highest_package", "highest package", "highest"])
                        average = get_row_value(row, ["average_package", "average package", "average"])
                        placed = get_row_value(row, ["students_placed", "students placed", "placed_students", "placed"])
                        percent = get_row_value(row, ["placement_percentage", "placement percentage", "percentage"])
                        recruiters = get_row_value(
                            row,
                            ["recruiters", "top_recruiters", "top recruiters", "companies", "major_recruiters"]
                        )

                        if asks_top_recruiters and recruiters:
                            lines.append(f"#### {inst_name}")
                            lines.append(f"- **Top Recruiters:** {recruiters}")
                            continue

                        block_lines = []
                        block_lines.append(f"#### {inst_name}")
                        if prog:
                            block_lines.append(f"- **Program:** {prog}")
                        if year:
                            block_lines.append(f"- **Year:** {year}")
                        if highest:
                            block_lines.append(f"- **Highest Package:** {highest}")
                        if average:
                            block_lines.append(f"- **Average Package:** {average}")
                        if placed:
                            block_lines.append(f"- **Students Placed:** {placed}")
                        if percent:
                            block_lines.append(f"- **Placement Percentage:** {percent}")
                        if recruiters:
                            block_lines.append(f"- **Major Recruiters:** {recruiters}")

                        if block_lines:
                            # Separate multiple program/year blocks with a blank line
                            lines.append("\n".join(block_lines))
                        else:
                            # Fallback for unknown Placement sheet schema: show row details as key-values.
                            kv_pairs = []
                            for col in row.index:
                                val = str(row.get(col, "")).strip()
                                if val and val.lower() != "nan":
                                    kv_pairs.append(f"- **{str(col).replace('_', ' ').title()}:** {val}")
                            if kv_pairs:
                                lines.append("\n".join(kv_pairs))

                    if len(lines) > 1:
                        return "\n\n".join(lines)

    # 5. NEW: Specific handling for cells and their emails
    if any(kw in keywords for kw in ["cell", "cells"]) or (any(kw in keywords for kw in ["email", "emails"]) and "cell" in q_lower):
        cells_df = sheets.get('Cells')
        if cells_df is not None:
            cells_list = []
            for _, row in cells_df.iterrows():
                name = str(row.get('cell_name', ''))
                email = str(row.get('email', ''))
                purpose = str(row.get('purpose', ''))
                if name and name != "nan":
                    # Clean up email if it's long/descriptive
                    clean_email = email
                    if "email at" in email.lower():
                        clean_email = email.split("email at")[-1].strip()
                    elif "at " in email.lower() and "@" in email:
                        clean_email = email.split("at ")[-1].strip()
                    
                    cells_list.append(f"- **{name}**: {clean_email} ({purpose})")
            
            if cells_list:
                return "Here are the various cells at CHARUSAT and their contact emails:\n\n" + "\n".join(cells_list)

    # 6. NEW: Specific handling for clubs by department/institute
    if any(kw in keywords for kw in ["club", "clubs"]):
        clubs_df = sheets.get('Clubs')
        if clubs_df is not None:
            exclude = {"club", "clubs", "list", "show", "give", "me", "tell", "about", "in", "at", "who", "are", "name", "all", "the", "of", "university"}
            dept_candidates = [kw for kw in keywords if kw not in exclude and difflib.SequenceMatcher(None, kw, "charusat").ratio() < 0.8]
            
            # If we have a specific department, filter by it
            if dept_candidates:
                matching_clubs = []
                primary_dept = dept_candidates[0]
                
                for _, row in clubs_df.iterrows():
                    inst_val = str(row.get('institute', '')).lower()
                    if primary_dept in inst_val:
                        c_name = str(row.get('club_name', ''))
                        purpose = str(row.get('purpose', ''))
                        if c_name and c_name != "nan":
                            matching_clubs.append(f"- **{c_name}**: {purpose}")
                
                if matching_clubs:
                    matching_clubs = list(dict.fromkeys(matching_clubs))
                    heading = f"### 🎯 Clubs at {primary_dept.upper()}\n\n"
                    intro = (
                        "Here are the active student clubs:\n\n"
                        if primary_dept.lower() == "cmpica"
                        else ""
                    )
                    # Extra blank line between clubs for better readability
                    resp = heading + intro + "\n\n".join(matching_clubs)
                    return resp

            # If no specific department match was found OR "all" was explicitly asked
            if "all" in keywords or any(difflib.SequenceMatcher(None, kw, "charusat").ratio() > 0.8 for kw in keywords) or not dept_candidates:
                all_clubs = []
                for _, row in clubs_df.iterrows():
                    c_name = str(row.get('club_name', ''))
                    purpose = str(row.get('purpose', ''))
                    inst = str(row.get('institute', ''))
                    if c_name and c_name != "nan":
                        all_clubs.append(f"- **{c_name}** ({inst}): {purpose}")
                
                if all_clubs:
                    return "Here are all the clubs available at CHARUSAT across different institutes:\n\n" + "\n".join(all_clubs)

    # 7. NEW: Specific handling for "Is there [course]?" or "[course] available?"
    is_course_query = (any(re.search(r'\b' + re.escape(kw) + r'\b', q_lower) for kw in ["is there", "available", "have", "provide", "offer"]) or \
                      (re.search(r'\bis\b', q_lower) and any(kw in q_lower for kw in ["there", "available"]))) and \
                      not any(kw in keywords for kw in ["scholarship", "scheme", "yojana", "merit", "hostel", "holiday", "library", "event", "sports", "cultural", "spoural"])
    
    if is_course_query:
        course_df = sheets.get('Course_info')
        if course_df is not None:
            # Clean keywords for matching
            exclude = {"is", "there", "in", "at", "charusat", "charsuat", "charusat", "university", "available", "have", "provide", "offer", "any", "some", "the", "a", "an", "do", "you", "are", "of", "course", "event", "sports", "cultural", "spoural"}
            # We also include the original keywords but cleaned of dots for better matching
            potential_courses = [kw for kw in keywords if kw not in exclude and difflib.SequenceMatcher(None, kw, "charusat").ratio() < 0.8]
            
            all_matches = []
            
            # --- STRATEGY 1: Try combined phrase first (e.g., "data science") ---
            if len(potential_courses) >= 2:
                combined_pc = " ".join(potential_courses).lower().replace(".", "")
                for _, row in course_df.iterrows():
                    c_name = str(row.get('course_name', '')).lower()
                    c_name_clean = c_name.replace(".", "").lower()
                    
                    if combined_pc in c_name_clean:
                        match_info = {
                            "name": str(row.get('course_name', '')),
                            "dept": str(row.get('department', row.get('department_id', ''))),
                            "duration": str(row.get('duration', ''))
                        }
                        if match_info not in all_matches:
                            all_matches.append(match_info)
            
            # --- STRATEGY 2: If no combined match, try AND match (e.g., "B.Sc" AND "IT") ---
            if not all_matches and len(potential_courses) >= 2:
                for _, row in course_df.iterrows():
                    c_name = str(row.get('course_name', '')).lower()
                    c_name_clean = c_name.replace(".", "").lower()
                    
                    if all(re.search(r'\b' + re.escape(pc.lower().replace(".", "")) + r'\b', c_name_clean) for pc in potential_courses):
                        match_info = {
                            "name": str(row.get('course_name', '')),
                            "dept": str(row.get('department', row.get('department_id', ''))),
                            "duration": str(row.get('duration', ''))
                        }
                        if match_info not in all_matches:
                            all_matches.append(match_info)
            
            # --- STRATEGY 3: Try individual keywords (only if Strategy 1 & 2 failed or single keyword) ---
            if not all_matches:
                # Filter potential_courses to avoid very generic terms matching everything
                # if we have multiple keywords
                generic_terms = {"science", "technology", "engineering", "management", "studies", "program", "diploma"}
                
                search_keywords = potential_courses
                if len(potential_courses) >= 2:
                    search_keywords = [kw for kw in potential_courses if kw.lower() not in generic_terms]
                    # If everything was generic, just use the first one
                    if not search_keywords:
                        search_keywords = [potential_courses[0]]

                for pc in search_keywords:
                    if len(pc) < 2: continue
                    pc_clean = pc.replace(".", "").lower()
                    
                    for _, row in course_df.iterrows():
                        c_name = str(row.get('course_name', '')).lower()
                        c_name_clean = c_name.replace(".", "").lower()
                        
                        # Special check for IT acronym
                        is_it_match = (pc_clean == "it" and "information technology" in c_name_clean)
                        
                        # Use word boundaries for matching short acronyms or specific terms
                        if is_it_match or re.search(r'\b' + re.escape(pc_clean) + r'\b', c_name_clean) or \
                           (len(pc_clean) > 4 and pc_clean in c_name_clean):
                            match_info = {
                                "name": str(row.get('course_name', '')),
                                "dept": str(row.get('department', row.get('department_id', ''))),
                                "duration": str(row.get('duration', ''))
                            }
                            if match_info not in all_matches:
                                all_matches.append(match_info)
            
            if all_matches:
                # Update context with the first match for follow-ups
                LAST_CONTEXT["course"] = all_matches[0]["name"]
                LAST_CONTEXT["department"] = all_matches[0]["dept"]
                
                if len(all_matches) == 1:
                    m = all_matches[0]
                    return f"Yes, **{m['name']}** is available at CHARUSAT (Department: {m['dept']}, Duration: {m['duration']})."
                else:
                    # Try to find the most representative term for the response
                    # Extract the term from the original question if possible
                    course_term = "the requested course"
                    match = re.search(r'(?:is there|available|offer|provide)\s+(?:course of|course)?\s*(.*?)(?:\s+in|\s+at|\?|$)', q_lower)
                    if match:
                        course_term = match.group(1).strip().upper()
                    elif potential_courses:
                        course_term = potential_courses[-1].upper()
                    
                    resp = f"Yes, there are courses of **{course_term}**:\n\n"
                    for m in all_matches:
                        resp += f"- **{m['name']}** ({m['dept']}, {m['duration']})\n"
                    return resp
            else:
                # NEW: If it's definitely a course query but no match found in Course_info
                return "No, there is no such course at CHARUSAT."

    # 8. NEW: Specific handling for Spoural Events (Prioritize context for RAG)
    is_spoural_query = any(kw in keywords for kw in ["event", "sports", "cultural", "spoural", "activity", "activities"]) or \
                      any(kw in keywords for kw in ["cricket", "football", "volleyball", "kabaddi", "chess", "badminton", "basketball", "handball", "tug of war", "frisbee", "singing", "dance", "quiz", "debate", "elocution", "vaad vivad", "poetry", "rangoli", "mehndi", "nail art", "clay", "painting", "cartooning", "collage", "photography"])
    
    # We let Spoural queries fall through to search_all_sheets and RAG for LLM processing
    # as requested by the user ("llm trough read karav").

    # 4. Search all sheets for relevant context (RAG)
    matches = search_all_sheets(question)
    
    # NEW: Filter out matches with negative scores (penalized items)
    matches = [m for m in matches if m.get('score', 0) > 0.4]
    
    # --- NEW: STRICT INSTITUTE FILTERING FOR RAG ---
    institutes = ["cspit", "depstar", "rpcp", "pdpias", "cmpica", "iiim", "arip", "mtin", "bdias"]
    query_institutes = [inst for inst in institutes if inst in keywords]
    
    if query_institutes and matches:
        # Filter matches to ONLY include those that mention the requested institute
        # or are from general datasets that don't belong to a specific institute
        filtered_matches = []
        for m in matches:
            m_text = m['row_text'].lower()
            # If match belongs to a specific institute, it must be the requested one
            # We check if the match text contains any of the WRONG institutes
            other_institutes = [inst for inst in institutes if inst not in query_institutes]
            
            # If the match explicitly mentions one of the WRONG institutes in its primary identification
            # (e.g., "Institute: DEPSTAR" when query is for CSPIT)
            is_wrong_institute = False
            for wrong_inst in other_institutes:
                # Use stricter pattern to avoid partial word matches
                if re.search(r'\b' + re.escape(wrong_inst) + r'\b', m_text):
                    # Check if it also mentions the CORRECT institute. 
                    # If it only mentions the wrong one, filter it out.
                    if not any(re.search(r'\b' + re.escape(right_inst) + r'\b', m_text) for right_inst in query_institutes):
                        is_wrong_institute = True
                        break
            
            if not is_wrong_institute:
                filtered_matches.append(m)
        matches = filtered_matches

    # --- NEW: STRICT PROGRAM FILTERING FOR RAG ---
    # Special handling for bsc vs bsc it
    if "bsc" in keywords and "it" in keywords:
        # Looking for B.Sc. IT (Must be CMPICA)
        # Try to find ANY match in the FULL system that matches CMPICA and IT
        all_matches = search_all_sheets(question)
        filtered_matches = [m for m in all_matches if ("cmpica" in m['row_text'].lower() or "bca" in m['row_text'].lower()) and ("it" in m['row_text'].lower() or "information technology" in m['row_text'].lower())]
        
        # If no CMPICA IT match, look for ANY IT match but EXCLUDE PDPIAS B.Sc. General
        if not filtered_matches:
            filtered_matches = [m for m in all_matches if ("it" in m['row_text'].lower() or "information technology" in m['row_text'].lower()) and "pdpias" not in m['row_text'].lower()]
            
        if filtered_matches:
            # Sort to ensure merit scholarship comes first if available
            filtered_matches.sort(key=lambda x: "merit" in x['row_text'].lower(), reverse=True)
            # Take only the top ones
            matches = filtered_matches[:5]
        else:
            # Fallback within existing matches: filter out PDPIAS
            filtered_matches = [m for m in matches if "pdpias" not in m['row_text'].lower()]
            if filtered_matches:
                matches = filtered_matches
            
    elif "bsc" in keywords and "it" not in keywords:
        # Looking for B.Sc. (General) (Must be PDPIAS)
        all_matches = search_all_sheets(question)
        filtered_matches = [m for m in all_matches if "pdpias" in m['row_text'].lower() and "it" not in m['row_text'].lower() and "information technology" not in m['row_text'].lower()]
        
        if filtered_matches:
            filtered_matches.sort(key=lambda x: "merit" in x['row_text'].lower(), reverse=True)
            matches = filtered_matches[:5]
        else:
            # Strictly filter out IT from existing matches
            filtered_matches = [m for m in matches if "it" not in m['row_text'].lower() and "information technology" not in m['row_text'].lower()]
            if filtered_matches:
                matches = filtered_matches
    else:
        programs = ["btech", "mtech", "bca", "bsc", "mba", "mca"]
        query_programs = [prog for prog in programs if prog in keywords]
        
        if query_programs and matches:
            filtered_matches = []
            for m in matches:
                m_text = m['row_text'].lower()
                other_programs = [prog for prog in programs if prog not in query_programs]
                
                is_wrong_program = False
                for wrong_prog in other_programs:
                    # Use stricter boundaries for program codes (e.g. \bbca\b)
                    if re.search(r'\b' + re.escape(wrong_prog) + r'\b', m_text):
                        # Special case: "B.Sc. IT" shouldn't match "B.Tech" but "B.Sc." matches "B.Sc. IT"
                        # If it mentions a wrong program but NOT the right one, filter it out
                        if not any(re.search(r'\b' + re.escape(right_prog) + r'\b', m_text) for right_prog in query_programs):
                            is_wrong_program = True
                            break
                
                if not is_wrong_program:
                    filtered_matches.append(m)
            
            # If we have matches after filtering, update the list
            if filtered_matches:
                matches = filtered_matches

    # 3. Use LLM if matches are found (RAG Mode)
    if matches and matches[0]['score'] > 0.4:
        # NEW: Direct return for extremely high confidence matches to avoid LLM confusion/hallucination
        if matches[0]['score'] > 1000000 and matches[0]['sheet'] == "Structured_Dataset":
            return matches[0]['row_text']
            
        context = build_context(matches)
        
        # Check if the top match is from Scholarship datasets
        is_scholarship_query = any(m['sheet'] in ["Government_Scholarships", "CHARUSAT_Merit_Scholarships"] for m in matches[:2])
        
        # Call LLM
        llm_response = ask_ollama(question, context)
        
        if llm_response and len(llm_response) > 10: # Ensure we got a meaningful LLM answer
            return llm_response
        
        # If it's a Scholarship query and LLM is not configured or failed, 
        # we will fallback to the raw structured info (which we've already formatted nicely).
        # We only return an error if NO matches were found at all (handled by top-level logic).
        
        # Fallback to rule-based if LLM fails (only for specific data sources like faculty)
        if matches and is_scholarship_query:
            # Aggregate multiple scholarship matches if it's a generic category query
            # (e.g. "girls scholarship", "sc scholarship")
            is_generic_scholarship_query = any(kw in keywords for kw in ["girl", "girls", "female", "kanya", "sc", "st", "obc", "ebc", "sebc", "minority", "bck", "matric"])
            
            if is_generic_scholarship_query:
                scholarship_list = []
                top_score = matches[0].get('score', 0)
                
                # If top score is massive (numeric code match), be much stricter about what to include
                # (e.g. only include other scholarships with the SAME numeric code match)
                inclusion_threshold = top_score * 0.3
                if top_score > 1000000:
                    inclusion_threshold = top_score * 0.8
                
                seen_names = set()
                
                # Check if it's specifically a girls/female query
                is_girls_query = any(kw in keywords for kw in ["girl", "girls", "female", "kanya", "dikri"])
                
                for m in matches:
                    if m.get('sheet') in ["Government_Scholarships", "CHARUSAT_Merit_Scholarships"] and m.get('score', 0) >= inclusion_threshold:
                        m_text = m.get('row_text', '')
                        
                        # Extract name to avoid duplicates
                        name_match = re.search(r'### 🎓 (.*?)\n', m_text)
                        name = name_match.group(1) if name_match else m_text[:100].strip()

                        # STRICTURE: If girls query, we must be very selective
                        if is_girls_query:
                            # Primary check: Does the TITLE mention girls?
                            title_has_gender = any(term in name.lower() for term in ["girl", "female", "kanya", "woman", "women", "dikri"])
                            # Secondary check: Does the Beneficiaries field mention girls?
                            beneficiaries_match = re.search(r'\*\*Beneficiaries:\*\* (.*?)\n', m_text)
                            beneficiaries_has_gender = beneficiaries_match and any(term in beneficiaries_match.group(1).lower() for term in ["girl", "female", "kanya", "woman", "women", "dikri"])
                            
                            # If neither title nor beneficiaries mentions girls, it's likely a general scholarship
                            # with just a small sub-scheme (like B.Tech merit), so we exclude it from "girls-only" query.
                            if not (title_has_gender or beneficiaries_has_gender):
                                continue

                        # Normalize BCK names to avoid variations of the same scheme (e.g. BCK-5 variations)
                        norm_name = name.lower()
                        bck_match = re.search(r'(bck\s?-\s?\d+)', norm_name)
                        if bck_match:
                            norm_name = bck_match.group(1)
                        
                        if norm_name not in seen_names:
                            scholarship_list.append(m_text)
                            seen_names.add(norm_name)
                    
                    if len(scholarship_list) >= 5: # Limit to top 5 unique relevant matches
                        break
                
                if scholarship_list:
                    if len(scholarship_list) == 1:
                        return scholarship_list[0]
                    
                    resp_body = "\n".join(scholarship_list)
                    return f"Here are the scholarship schemes matching your query:\n\n{resp_body}"
  
        if matches and matches[0].get('sheet') == 'Faculties_mem_info' and len(matches) > 1:
            # Aggregate multiple faculty matches
            faculty_list = []
            top_score = matches[0].get('score', 0)
            for m in matches:
                # If the score is close to the top match, it's likely another relevant person
                if m.get('sheet') == 'Faculties_mem_info' and m.get('score', 0) >= top_score * 0.9:
                    faculty_list.append(m.get('row_text', ''))
                else:
                    break
            
            if len(faculty_list) > 1:
                # Get the role and department from keywords to format the response
                role = next((kw.upper() for kw in keywords if kw in ["principal", "dean", "hod", "head"]), "FACULTY")
                dept = next((kw.upper() for kw in keywords if kw not in ["principal", "dean", "hod", "head", "faculty", "who", "whom", "whoo"]), "the department")
                
                resp = f"Here are the {role} members for **{dept}**:\n\n"
                resp += "\n---\n".join(faculty_list)
                return resp
        
        if matches:
            # TIE-BREAKER: If we have multiple matches with the same score, 
            # and one is Course_info while another is Department, prefer Course_info.
            top_score = matches[0].get('score', 0)
            course_matches = [m for m in matches if m.get('sheet') == 'Course_info' and m.get('score', 0) >= top_score * 0.95]
            if course_matches:
                return course_matches[0].get('row_text', '')
                
            top_match = matches[0]
            return top_match.get('row_text', '')

    # 4. Handle acknowledgments / farewells as fallback (Keep it quick)
    q_words = q_lower.split()
    acknowledgments = {"hello", "hi", "hey", "ok", "okay", "thanks", "thank you", "got it", "nice", "good", "perfect"}
    farewells = {"bye", "by", "goodbye", "see you"}

    if any(word in farewells for word in q_words) and len(q_words) <= 2:        
        return "Goodbye! Have a nice day! Please feel free to come back if you have more queries related to CHARUSAT."

    if all(word in acknowledgments for word in q_words) and len(q_words) > 0:   
        if any(w in ["hello", "hi", "hey"] for w in q_words):
            return "Hello! How can I help you today with information about CHARUSAT?"
        return "You're welcome! Please feel free to ask me another query or doubt related to CHARUSAT."

    # 5. Handle specific placement/faculty/holiday/course logic as fallback if needed
    
    return "Sorry, I couldn't find specific information about that for CHARUSAT. Please try asking about admissions, courses, fees, or placements."

def get_response(user_input, original_input=None):
    """Main entry point for chatbot response."""
    try:
        if not user_input or not user_input.strip():
            return "Please enter a valid question."
            
        # Call the advanced response generator that uses Excel data
        return get_chatbot_response(user_input, original_input)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return "Sorry, I'm having trouble processing your request right now. 😅"

if __name__ == "__main__":
    print("--- CHARUSAT Campus Guide Chatbot ---")
    print("Type 'exit' or 'quit' to stop.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = get_response(user_input)
        print(f"Chatbot: {response}")
