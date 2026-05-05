import re

def get_chatbot_response(question, original_input=None):
    # This is a placeholder for the actual function in chatbot_utils.py
    # We'll only replace the relevant part in the actual file.
    pass

# Corrected section for chatbot_utils.py:
"""
            else:
                for _, row in course_df.iterrows():
                    c_name = str(row.get('course_name', '')).lower()
                    
                    # Count how many program keywords match this course name
                    pk_match_count = sum(1 for pk in program_keywords if re.search(r'\b' + re.escape(pk) + r'\b', c_name))
                    
                    if pk_match_count > max_pk_match:
                        max_pk_match = pk_match_count
                        best_match = row
                    elif pk_match_count > 0 and pk_match_count == max_pk_match:
                        # TIE BREAKER:
                        if best_match is not None:
                            # 1. Penalize "Online" courses unless explicitly asked
                            current_is_online = "online" in c_name
                            best_is_online = "online" in str(best_match.get('course_name', '')).lower()
                            asked_online = "online" in keywords
                            
                            if asked_online:
                                if current_is_online and not best_is_online:
                                    best_match = row
                                    continue
                            else:
                                if best_is_online and not current_is_online:
                                    best_match = row
                                    continue
                            
                            # 2. Prefer exact match for program names
                            c_name_norm = c_name.replace(".", "").replace(" ", "")
                            best_name_norm = str(best_match.get('course_name', '')).lower().replace(".", "").replace(" ", "")
                            pk_norm = "".join(program_keywords).replace(".", "").replace(" ", "")
                            
                            if c_name_norm == pk_norm and best_name_norm != pk_norm:
                                best_match = row
                                continue
                            
                            # 3. Prefer shorter course name (more specific)
                            if len(c_name) < len(str(best_match.get('course_name', '')).lower()):
                                best_match = row

                if best_match is not None and (max_pk_match >= 1):
                    duration = str(best_match.get('duration', ''))
                    eligibility = str(best_match.get('eligibility', ''))
                    dept = str(best_match.get('department', ''))
                    full_name = str(best_match.get('course_name', ''))
                    return f"### 🎓 {full_name}\n\n" \
                            f"- **Department/Institute:** {dept}\n" \
                            f"- **Duration:** {duration}\n" \
                            f"- **Eligibility:** {eligibility}"
"""
