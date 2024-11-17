from models import UserProfile, Education, ProfessionalExperience
from nlp_processor import NLPProcessor
from data_pipeline import DataProcessor
from typing import Tuple, Dict, Any, List
from datetime import datetime
import re

class ProfileManager:
    def __init__(self):
        self.profile = UserProfile()
        self.nlp = NLPProcessor()
        self.data_processor = DataProcessor()
        self.current_field = "name"
        self.field_weights = self.data_processor.field_weights
        self.conversation_history = []
        self.last_intent = None
        self.intent_confidence = 0.0

    def process_input(self, text: str) -> Tuple[str, bool]:
        """Process user input and update profile."""
        print(f"\nProcessing input: {text}")  # Debug print
        
        # Handle example requests
        if text.lower() in ["example", "examples"]:
            example = self.get_example_message()
            return example, False
        
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": text})
        
        # Detect user intent
        intent, confidence = self.nlp.detect_intent(text)
        self.last_intent = intent
        self.intent_confidence = confidence
        print(f"Detected intent: {intent} (confidence: {confidence})")
        
        # Handle different intents
        if intent == "help":
            return self.handle_help_request(text), False
        elif intent == "ask_question":
            return self.handle_question(text), False
        elif intent == "modify":
            return self.handle_modification_request(text), False
        elif intent == "complete":
            return self.handle_completion_request(), True
        elif intent == "exit":
            return self.handle_exit_request(), True
            
        # Extract entities and infer information
        extracted_data = self.data_processor.extract_entities(text)
        print(f"Extracted data: {extracted_data}")

        # If we're expecting a name and get simple text, treat it as the name
        if self.current_field == "name" and text.strip():
            self.profile.name = text.strip()
            self.current_field = "age"
            return "Nice to meet you, {}! Now, could you tell me your age?".format(self.profile.name), True

        # Handle age input with various formats
        if self.current_field == "age":
            # Remove common words and extract the number
            age_text = text.lower().strip()
            age_text = age_text.replace('years', '').replace('year', '')
            age_text = age_text.replace('old', '').replace('im', '').replace("i'm", '')
            age_text = age_text.replace('i am', '').strip()
            
            # Try to extract the number
            try:
                age = int(''.join(filter(str.isdigit, age_text)))
                if 0 <= age <= 120:  # Reasonable age range
                    self.profile.age = age
                    self.current_field = "location"
                    return f"Got it! {age} years old. Now, where are you located?", True
                else:
                    return "That age doesn't seem right. Please enter a valid age between 0 and 120.", False
            except ValueError:
                return "I didn't catch your age. Please enter it as a number (e.g., '40' or '40 years').", False

        # Handle direct input based on current field
        if not extracted_data and self.current_field:
            # Try to extract information using ChatGPT first
            gpt_info = self.nlp.process_with_llm(text, self.current_field)
            
            if self.current_field == "name":
                if 'name' in gpt_info:
                    self.profile.name = gpt_info['name']
                    self.current_field = "age"
                    return f"Nice to meet you, {self.profile.name}! Now, could you tell me your age?", True
                return "I didn't quite catch your name. Could you please state it clearly?", False
                
            elif self.current_field == "age":
                if 'age' in gpt_info:
                    age = gpt_info['age']
                    if 0 <= age <= 120:
                        self.profile.age = age
                        self.current_field = "location"
                        return f"Got it! {age} years old. Now, where are you located?", True
                return "I didn't catch your age. Please enter it as a number (e.g., '40' or '40 years').", False
                
            elif self.current_field == "location":
                # Clean up the input text
                cleaned_text = text.strip()
                
                # Handle common location phrases
                location_patterns = [
                    (r"i(?:'m| am) (?:from|in|at|living in) (.*)", 1),
                    (r"i live in (.*)", 1),
                    (r"based in (.*)", 1),
                    (r"located in (.*)", 1),
                    (r"my location is (.*)", 1),
                    (r"(.*)", 0)  # Catch-all pattern
                ]
                
                location = None
                for pattern, group in location_patterns:
                    match = re.search(pattern, cleaned_text, re.IGNORECASE)
                    if match:
                        location = match.group(group).strip()
                        break
                
                if location:
                    # Clean up the location
                    location = location.strip('.,')
                    # Capitalize each word
                    location = ' '.join(word.capitalize() for word in location.split())
                    self.profile.location = location
                    self.current_field = "education_degree"
                    return "Great! Now let's talk about your education. What degree did you earn?", True
                
                return "Could you please tell me where you live? For example: 'Durban, South Africa' or just 'Durban'", False
                
            elif self.current_field == "education_degree":
                # First try GPT understanding
                if gpt_info and 'degree_type' in gpt_info:
                    degree_parts = []
                    degree_parts.append(gpt_info['degree_type'])
                    
                    if 'field_of_study' in gpt_info:
                        degree_parts.append(f"in {gpt_info['field_of_study']}")
                    elif 'abbreviation' in gpt_info:
                        # If we have an abbreviation but no field, try to expand it
                        abbrev_expansions = {
                            'MSC': 'Science',
                            'MS': 'Science',
                            'MA': 'Arts',
                            'MBA': 'Business Administration',
                            'MENG': 'Engineering',
                            'BSC': 'Science',
                            'BA': 'Arts',
                            'BENG': 'Engineering',
                            'BE': 'Engineering',
                            'PHD': 'Philosophy'
                        }
                        abbrev = gpt_info['abbreviation'].upper()
                        if abbrev in abbrev_expansions:
                            degree_parts.append(f"in {abbrev_expansions[abbrev]}")
                    
                    degree = " ".join(degree_parts)
                    self.profile.education.degree = degree
                    self.current_field = "education_institution"
                    return "Great! And which institution did you attend?", True
                
                # If GPT fails, fall back to regex patterns
                cleaned_text = text.strip()
                degree_patterns = [
                    # Master's degree patterns
                    (r"(?:master(?:'s)?|ms|msc|ma|meng|mba|master of|masters in|masters of)\s+(?:of\s+)?(?:science\s+)?(?:in\s+)?([^,\.]+)", "Master's", 1),
                    # Bachelor's degree patterns
                    (r"(?:bachelor(?:'s)?|bs|bsc|ba|beng|bachelor of|bachelors in|bachelors of)\s+(?:of\s+)?(?:science\s+)?(?:in\s+)?([^,\.]+)", "Bachelor's", 1),
                    # PhD patterns
                    (r"(?:phd|ph\.d|doctorate|doctor of philosophy)\s+(?:in\s+)?([^,\.]+)?", "Ph.D.", 1),
                    # General degree pattern
                    (r"(?:degree in|diploma in|qualified in)\s+([^,\.]+)", "Degree", 1),
                    # Direct subject mention
                    (r"([^,\.]+)", "Degree", 0)
                ]
                
                for pattern, deg_type, group in degree_patterns:
                    match = re.search(pattern, cleaned_text, re.IGNORECASE)
                    if match:
                        field_of_study = match.group(group).strip() if match.group(group) else None
                        if field_of_study:
                            field_of_study = ' '.join(word.capitalize() for word in field_of_study.split())
                            degree = f"{deg_type} in {field_of_study}"
                        else:
                            degree = deg_type
                            
                        self.profile.education.degree = degree
                        self.current_field = "education_institution"
                        return "Great! And which institution did you attend?", True
                
                return "Could you tell me your degree? For example: 'Master's in Computer Science', 'MSc in Physics', or just 'BEng'", False
                
            elif self.current_field == "education_institution":
                # Try GPT understanding first
                gpt_info = self.nlp.process_with_llm(text, self.current_field)
                
                if gpt_info and 'institution' in gpt_info:
                    institution = gpt_info['institution']
                    if 'location' in gpt_info:
                        institution += f", {gpt_info['location']}"
                        
                    self.profile.education.institution = institution
                    self.current_field = "education_year"
                    return "What year did you graduate?", True
                
                # If GPT fails, accept direct input
                cleaned_text = text.strip()
                # Common institution abbreviations
                abbrev_map = {
                    'MIT': 'Massachusetts Institute of Technology',
                    'UCLA': 'University of California, Los Angeles',
                    'UC': 'University of California',
                    'NYU': 'New York University',
                    'UJ': 'University of Johannesburg',
                    'UCT': 'University of Cape Town',
                    'WITS': 'University of the Witwatersrand'
                }
                
                # Check if input is a known abbreviation
                upper_text = cleaned_text.upper()
                if upper_text in abbrev_map:
                    self.profile.education.institution = abbrev_map[upper_text]
                else:
                    self.profile.education.institution = cleaned_text
                    
                self.current_field = "education_year"
                return "What year did you graduate?", True
                
            elif self.current_field == "education_year":
                # First try to parse as direct year input
                try:
                    year = int(text.strip())
                    if 1950 <= year <= 2030:
                        self.profile.education.graduation_year = year
                        self.current_field = "profession"
                        return "Thanks! Now, what is your current profession?", True
                    return "Please enter a valid graduation year between 1950 and 2030.", False
                except ValueError:
                    # If direct parsing fails, try GPT
                    gpt_info = self.nlp.process_with_llm(text, self.current_field)
                    if gpt_info and 'year' in gpt_info:
                        year = gpt_info['year']
                        if 1950 <= year <= 2030:
                            self.profile.education.graduation_year = year
                            self.current_field = "profession"
                            return "Thanks! Now, what is your current profession?", True
                        return "Please enter a valid graduation year between 1950 and 2030.", False
                    
                    # Try regex patterns as last resort
                    year_patterns = [
                        r"(?:in|year) (\d{4})",
                        r"graduated (?:in )?(\d{4})",
                        r"class of (\d{4})",
                        r"(\d{4})"
                    ]
                    
                    for pattern in year_patterns:
                        match = re.search(pattern, text)
                        if match:
                            try:
                                year = int(match.group(1))
                                if 1950 <= year <= 2030:
                                    self.profile.education.graduation_year = year
                                    self.current_field = "profession"
                                    return "Thanks! Now, what is your current profession?", True
                            except ValueError:
                                continue
                    
                    return "Please enter your graduation year (e.g., '2020' or 'graduated in 2020').", False
                
            elif self.current_field == "profession":
                # Clean up input
                cleaned_text = text.strip()
                
                # Common job titles and their variations
                job_titles = {
                    'data scientist': ['data scientist', 'ds', 'data science professional'],
                    'software engineer': ['software engineer', 'swe', 'software developer', 'programmer'],
                    'product manager': ['product manager', 'pm', 'product owner'],
                    'data analyst': ['data analyst', 'analyst', 'business analyst'],
                    'data engineer': ['data engineer', 'de'],
                    'researcher': ['researcher', 'research scientist', 'research engineer'],
                    'manager': ['manager', 'team lead', 'team leader'],
                    'developer': ['developer', 'dev', 'coder', 'programmer'],
                    'engineer': ['engineer', 'eng'],
                    'architect': ['architect', 'solutions architect', 'system architect']
                }
                
                # First try GPT understanding
                gpt_info = self.nlp.process_with_llm(text, self.current_field)
                if gpt_info and 'role' in gpt_info:
                    role = gpt_info['role']
                    if 'level' in gpt_info:
                        role = f"{gpt_info['level']} {role}"
                    if 'department' in gpt_info:
                        role = f"{role} in {gpt_info['department']}"
                        
                    self.profile.current_role = role
                    
                    # Add to professional experience
                    experience = ProfessionalExperience()
                    experience.role = role
                    experience.is_current = True
                    if not self.profile.professional_experience:
                        self.profile.professional_experience = []
                    self.profile.professional_experience.append(experience)
                    
                    self.current_field = "company"
                    return "Great! And which company do you work for?", True
                
                # Try direct matching
                lower_text = cleaned_text.lower()
                matched_role = None
                
                # Check for exact matches first
                for standard_title, variations in job_titles.items():
                    if lower_text in variations or lower_text == standard_title:
                        matched_role = standard_title.title()
                        break
                
                # Check for partial matches
                if not matched_role:
                    for standard_title, variations in job_titles.items():
                        if any(var in lower_text for var in variations):
                            matched_role = standard_title.title()
                            break
                
                # If we found a match or the input looks like a valid job title
                if matched_role or (len(cleaned_text.split()) <= 4 and all(len(word) > 1 for word in cleaned_text.split())):
                    role = matched_role or cleaned_text.title()
                    self.profile.current_role = role
                    
                    # Add to professional experience
                    experience = ProfessionalExperience()
                    experience.role = role
                    experience.is_current = True
                    if not self.profile.professional_experience:
                        self.profile.professional_experience = []
                    self.profile.professional_experience.append(experience)
                    
                    self.current_field = "company"
                    return "Great! And which company do you work for?", True
                
                return "Please tell me your current job title (e.g., 'Data Scientist', 'Software Engineer')", False
                
            elif self.current_field == "company":
                # Clean up input
                cleaned_text = text.strip()
                
                # Common company names and their variations/abbreviations
                company_map = {
                    'amazon': {
                        'variations': ['amazon', 'aws', 'amazon web services'],
                        'full_name': 'Amazon Web Services',
                        'industry': 'Technology'
                    },
                    'microsoft': {
                        'variations': ['microsoft', 'msft', 'ms'],
                        'full_name': 'Microsoft Corporation',
                        'industry': 'Technology'
                    },
                    'google': {
                        'variations': ['google', 'alphabet', 'goog'],
                        'full_name': 'Google LLC',
                        'industry': 'Technology'
                    },
                    'apple': {
                        'variations': ['apple', 'aapl'],
                        'full_name': 'Apple Inc.',
                        'industry': 'Technology'
                    },
                    'meta': {
                        'variations': ['meta', 'facebook', 'fb', 'instagram'],
                        'full_name': 'Meta Platforms Inc.',
                        'industry': 'Technology'
                    },
                    'netflix': {
                        'variations': ['netflix', 'nflx'],
                        'full_name': 'Netflix Inc.',
                        'industry': 'Entertainment'
                    },
                    'ibm': {
                        'variations': ['ibm', 'international business machines'],
                        'full_name': 'IBM Corporation',
                        'industry': 'Technology'
                    },
                    'oracle': {
                        'variations': ['oracle', 'orcl'],
                        'full_name': 'Oracle Corporation',
                        'industry': 'Technology'
                    },
                    'salesforce': {
                        'variations': ['salesforce', 'crm', 'sfdc'],
                        'full_name': 'Salesforce Inc.',
                        'industry': 'Technology'
                    }
                }
                
                # First try GPT understanding
                gpt_info = self.nlp.process_with_llm(text, self.current_field)
                if gpt_info and 'company_name' in gpt_info:
                    company = gpt_info['company_name']
                    if 'industry' in gpt_info:
                        company += f" ({gpt_info['industry']})"
                        
                    if self.profile.professional_experience:
                        self.profile.professional_experience[-1].company = company
                        self.current_field = "skills"
                        return "Thanks! Now, tell me about your technical skills and tools you're proficient in.", True
                
                # Try direct matching with company map
                lower_text = cleaned_text.lower()
                matched_company = None
                
                # Check for exact matches or variations
                for company_info in company_map.values():
                    if lower_text in company_info['variations']:
                        matched_company = {
                            'name': company_info['full_name'],
                            'industry': company_info['industry']
                        }
                        break
                
                if matched_company:
                    company = f"{matched_company['name']} ({matched_company['industry']})"
                else:
                    # Accept any reasonable company name
                    words = cleaned_text.split()
                    if 1 <= len(words) <= 4 and all(len(word) > 1 for word in words):
                        company = ' '.join(word.capitalize() for word in words)
                
                if matched_company or company:
                    if self.profile.professional_experience:
                        self.profile.professional_experience[-1].company = company
                        self.current_field = "skills"
                        return "Thanks! Now, tell me about your technical skills and tools you're proficient in.", True
                
                return "Please tell me which company you work for (e.g., 'Google', 'Microsoft', 'AWS')", False
                
            elif self.current_field == "skills":
                # Clean up input
                cleaned_text = text.strip()
                
                # Common skills and their variations
                skills_map = {
                    'programming_languages': {
                        'python': ['python', 'py'],
                        'javascript': ['javascript', 'js', 'node.js', 'nodejs'],
                        'java': ['java', 'jvm'],
                        'c++': ['c++', 'cpp'],
                        'ruby': ['ruby', 'rails', 'ruby on rails'],
                        'php': ['php'],
                        'swift': ['swift', 'ios'],
                        'kotlin': ['kotlin', 'android'],
                        'go': ['go', 'golang']
                    },
                    'data_science': {
                        'machine learning': ['machine learning', 'ml', 'deep learning', 'dl', 'ai'],
                        'data analysis': ['data analysis', 'data analytics', 'analytics'],
                        'statistics': ['statistics', 'statistical analysis', 'stats'],
                        'big data': ['big data', 'hadoop', 'spark'],
                        'data visualization': ['data visualization', 'data viz', 'tableau', 'power bi']
                    },
                    'frameworks': {
                        'tensorflow': ['tensorflow', 'tf'],
                        'pytorch': ['pytorch', 'torch'],
                        'react': ['react', 'reactjs', 'react.js'],
                        'angular': ['angular', 'angularjs'],
                        'vue': ['vue', 'vuejs', 'vue.js'],
                        'django': ['django'],
                        'flask': ['flask'],
                        'spring': ['spring', 'spring boot']
                    },
                    'cloud': {
                        'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda'],
                        'azure': ['azure', 'microsoft azure'],
                        'gcp': ['gcp', 'google cloud', 'google cloud platform'],
                        'docker': ['docker', 'container'],
                        'kubernetes': ['kubernetes', 'k8s']
                    },
                    'databases': {
                        'sql': ['sql', 'mysql', 'postgresql', 'oracle'],
                        'nosql': ['nosql', 'mongodb', 'cassandra', 'redis'],
                        'elasticsearch': ['elasticsearch', 'elk']
                    }
                }
                
                # First try GPT understanding
                gpt_info = self.nlp.process_with_llm(text, self.current_field)
                if any(key in gpt_info for key in ['technical_skills', 'tools', 'soft_skills']):
                    if 'technical_skills' in gpt_info:
                        self.profile.tools_technologies.extend(gpt_info['technical_skills'])
                    if 'tools' in gpt_info:
                        self.profile.tools_technologies.extend(gpt_info['tools'])
                    if 'soft_skills' in gpt_info:
                        if not hasattr(self.profile, 'soft_skills'):
                            self.profile.soft_skills = []
                        self.profile.soft_skills.extend(gpt_info['soft_skills'])
                    
                    self.current_field = "languages"
                    return "Great! What languages do you speak?", True
                
                # Try direct matching with skills map
                skills = set()
                words = cleaned_text.lower().split(',')
                words = [w.strip() for word in words for w in word.split('and')]
                
                for category in skills_map.values():
                    for skill, variations in category.items():
                        for word in words:
                            if any(var in word for var in variations):
                                skills.add(skill.title())
                
                if skills:
                    self.profile.tools_technologies.extend(list(skills))
                    self.current_field = "languages"
                    return "Great! What languages do you speak?", True
                
                # Accept any reasonable input
                if all(len(word.strip()) > 1 for word in words):
                    skills = [word.strip().title() for word in words]
                    self.profile.tools_technologies.extend(skills)
                    self.current_field = "languages"
                    return "Great! What languages do you speak?", True
                
                return "Please list your technical skills and tools (e.g., 'Python, Machine Learning, AWS, SQL')", False

            # If GPT couldn't help, fall back to original handling
            if self.current_field == "location":
                self.profile.location = text.strip()
                self.current_field = "education_degree"
                return "Great! Now let's talk about your education. What degree did you earn? (e.g., 'Bachelor's in Computer Science')", True
            elif self.current_field == "education_degree":
                self.profile.education.degree = text.strip()
                self.current_field = "education_institution"
                return "Great! And which institution did you attend?", True
            elif self.current_field == "education_institution":
                self.profile.education.institution = text.strip()
                self.current_field = "education_year"
                return "What year did you graduate?", True
            elif self.current_field == "education_year":
                try:
                    year = int(''.join(filter(str.isdigit, text)))
                    if 1950 <= year <= 2030:
                        self.profile.education.graduation_year = year
                        self.current_field = "profession"
                        return f"Thanks! Now, what is your current profession?", True
                    else:
                        return "Please enter a valid graduation year between 1950 and 2030.", False
                except ValueError:
                    return "I didn't catch the year. Please enter it as a number (e.g., '2020').", False
            elif self.current_field == "profession":
                # Process various ways of stating profession
                text = text.lower().strip()
                
                # Remove common filler words and phrases
                text = re.sub(r'\b(i am|i\'m|currently|working|as|a|an|the|in|at|for)\b', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Store the original input as profession
                self.profile.current_role = text.title()
                
                # Add to professional experience
                experience = ProfessionalExperience()
                experience.role = text.title()
                experience.is_current = True
                if not self.profile.professional_experience:
                    self.profile.professional_experience = []
                self.profile.professional_experience.append(experience)
                
                self.current_field = "company"
                return "Great! And which company do you work for?", True
            elif self.current_field == "company":
                # Store company information
                text = text.strip()
                if self.profile.professional_experience:
                    self.profile.professional_experience[-1].company = text
                    self.current_field = "skills"
                    return "Thanks! Now, tell me about your technical skills and tools you're proficient in.", True
                return "I couldn't save your company information. Let's try again.", False

            elif self.current_field == "education":
                # Parse education information
                degree_match = re.search(r"(?:have\s+)?(?:a\s+)?(Bachelor'?s|Master'?s|Ph\.?D\.?|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)(?:\s+(?:degree|in|of))?\s+(?:in\s+)?([^,]+)(?:\s+from\s+)?([^,]+)(?:\s*,\s*|\s+in\s+|\s+graduated\s+in\s+|\s+class\s+of\s+)(\d{4})", text, re.IGNORECASE)
                if degree_match:
                    # Extract education data
                    degree = degree_match.group(1)
                    major = degree_match.group(2).strip()
                    institution = degree_match.group(3).strip()
                    graduation_year = int(degree_match.group(4))
                    print(f"Extracted education data: degree={degree}, major={major}, institution={institution}, graduation_year={graduation_year}")  # Debug print
                    
                    # Create education data dictionary
                    edu_data = {
                        "education": {
                            "degree": degree,
                            "major": major,
                            "institution": institution,
                            "graduation_year": graduation_year
                        }
                    }
                    print(f"Created education data: {edu_data}")  # Debug print
                    
                    # Validate education data
                    valid_data, validation_messages = self.data_processor.validate_data(edu_data)
                    print(f"Validated education data: {valid_data}")  # Debug print
                    
                    if valid_data and "education" in valid_data:
                        # Create a new Education instance with the validated data
                        education = Education(
                            degree=valid_data["education"]["degree"],
                            major=valid_data["education"]["major"],
                            institution=valid_data["education"]["institution"],
                            graduation_year=valid_data["education"]["graduation_year"]
                        )
                        
                        # Update profile education
                        self.profile.education = education
                        print(f"Updated education: {self.profile.education}")  # Debug print
                        
                        # Calculate completeness
                        completeness_score = self.calculate_completeness()
                        print(f"Completeness score: {completeness_score}")
                        
                        # Update current field based on completion
                        self._update_current_field()
                        
                        # Generate response
                        response = self.generate_response(
                            intent="provide_info",
                            confidence=1.0,
                            valid_data=valid_data,
                            validation_messages=validation_messages,
                            completeness_score=completeness_score
                        )
                        
                        # Add bot response to conversation history
                        self.conversation_history.append({"role": "assistant", "content": response})
                        print(f"Final response: {response}")
                        
                        return response, True
        
        # Infer additional information
        inferred_data = self.nlp.infer_information(text, self.current_field, self.profile)
        print(f"Inferred data: {inferred_data}")
        
        # Merge extracted and inferred data
        all_data = {**extracted_data, **inferred_data}
        print(f"Input data: {all_data}")
        
        # Validate the data
        valid_data, validation_messages = self.data_processor.validate_data(all_data)
        print(f"Valid data: {valid_data}")
        
        # Update profile
        self.profile, update_messages = self.data_processor.update_profile(self.profile, valid_data)
        print(f"Updated profile: {self.profile.__dict__}")
        
        # Calculate completeness
        completeness_score = self.calculate_completeness()
        print(f"Completeness score: {completeness_score}")
        
        # Update current field based on completion
        self._update_current_field()
        
        # Generate response
        response = self.generate_response(
            intent=intent,
            confidence=confidence,
            valid_data=valid_data,
            validation_messages=validation_messages + update_messages,
            completeness_score=completeness_score
        )
        
        # Add bot response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        print(f"Final response: {response}")
        
        return response, bool(valid_data)  # Return True if data was updated
        
    def handle_help_request(self, text: str) -> str:
        """Handle help-related queries."""
        if "example" in text.lower():
            return self.get_example_message()
            
        help_responses = {
            "name": "Please tell me your full name (e.g., 'John Smith').",
            "age": "You can share your age directly (e.g., 'I'm 25') or mention your graduation year.",
            "location": "Tell me where you're located - city and country are helpful.",
            "education_degree": "What degree did you earn (e.g., 'Bachelor's in Computer Science')?",
            "education_institution": "Which institution did you attend?",
            "education_year": "What year did you graduate?",
            "experience": "Tell me about your work experience, including job titles, companies, and durations.",
            "skills": "List the technical skills, tools, and technologies you're proficient in.",
            "languages": "What languages do you speak? Include proficiency levels if you'd like.",
            "certifications": "Do you have any professional certifications or credentials?"
        }
        
        return help_responses.get(
            self.current_field,
            "I'm here to help build your professional profile. What would you like to know?"
        )

    def handle_question(self, text: str) -> str:
        """Handle user questions."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant explaining how to build a professional profile. Keep responses concise and relevant."},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating question response: {str(e)}")
            return "I'm here to help! Could you rephrase your question?"

    def handle_modification_request(self, text: str) -> str:
        """Handle requests to modify profile information."""
        # Extract field to modify
        fields = [
            "name", "age", "location", "education_degree", "education_institution", "education_year",
            "experience", "skills", "languages", "certifications"
        ]
        
        for field in fields:
            if field in text.lower():
                self.current_field = field
                return f"Sure, I can help you update your {field}. What would you like to change it to?"
                
        return "Which part of your profile would you like to modify?"

    def handle_completion_request(self) -> str:
        """Handle profile completion request."""
        completeness_score, _ = self.data_processor.calculate_completeness(self.profile)
        
        if completeness_score >= 0.8:
            summary = self.data_processor.generate_profile_summary(self.profile)
            return f"Great! Your profile is {completeness_score:.0%} complete. Here's a summary:\n\n{summary}"
        else:
            missing = self.data_processor.get_missing_fields(self.profile)
            return f"Your profile is {completeness_score:.0%} complete. We still need: {', '.join(missing)}"

    def handle_exit_request(self) -> str:
        """Handle exit request."""
        completeness_score, _ = self.data_processor.calculate_completeness(self.profile)
        
        if completeness_score >= 0.5:
            summary = self.data_processor.generate_profile_summary(self.profile)
            return f"Before you go, here's a summary of your profile:\n\n{summary}\n\nFeel free to return anytime to update your information!"
        else:
            return "Thanks for starting your profile! You can return anytime to complete it."

    def generate_response(self, intent: str, confidence: float, valid_data: Dict[str, Any],
                        validation_messages: List[str], completeness_score: float) -> str:
        """Generate appropriate response based on input and current state."""
        response = []
        
        # Handle validation messages
        if validation_messages:
            response.extend(validation_messages)
            
        # Acknowledge valid input
        if valid_data:
            if "name" in valid_data:
                response.append(f"Nice to meet you, {valid_data['name']}!")
            elif "age" in valid_data:
                response.append(f"Got it, {valid_data['age']} years old.")
            elif "location" in valid_data:
                response.append(f"Thanks! {valid_data['location']} is a great place.")
            elif "education" in valid_data:
                edu = valid_data["education"]
                edu_response = []
                if "degree" in edu:
                    edu_response.append(edu["degree"])
                if "major" in edu:
                    edu_response.append(f"in {edu['major']}")
                if "institution" in edu:
                    edu_response.append(f"from {edu['institution']}")
                if "graduation_year" in edu:
                    edu_response.append(f"({edu['graduation_year']})")
                if edu_response:
                    response.append(f"Great! I've recorded your {' '.join(edu_response)}.")
                    
        # Get next question based on current field
        next_question = self.get_next_question()
        if next_question:
            response.append(next_question)
            
        # Add completeness info
        response.append(f"Profile completeness: {completeness_score:.0f}%")
        
        return "\n".join(response)

    def get_next_question(self) -> str:
        """Get the next question based on current field."""
        questions = {
            "name": "What's your name?",
            "age": "What is your age?",
            "location": "Where are you located (city/country)?",
            "education_degree": "What degree did you earn?",
            "education_institution": "Which institution did you attend?",
            "education_year": "What year did you graduate?",
            "profession": "What is your current profession?",
            "company": "Which company do you work for?",
            "experience": "What's your professional experience?",
            "skills": "What tools and technologies are you experienced with?",
            "languages": "What languages do you speak?",
            "certifications": "Do you have any professional certifications?"
        }
        
        # Determine the next field to ask about
        if not self.profile.name:
            self.current_field = "name"
        elif not self.profile.age:
            self.current_field = "age"
        elif not self.profile.location:
            self.current_field = "location"
        elif not self.profile.education.degree:
            self.current_field = "education_degree"
        elif not self.profile.education.institution:
            self.current_field = "education_institution"
        elif not self.profile.education.graduation_year:
            self.current_field = "education_year"
        elif not self.profile.current_role:
            self.current_field = "profession"
        elif not self.profile.professional_experience or not any(exp.company for exp in self.profile.professional_experience):
            self.current_field = "company"
        elif not self.profile.tools_technologies:
            self.current_field = "skills"
        elif not self.profile.languages:
            self.current_field = "languages"
        elif not self.profile.certifications:
            self.current_field = "certifications"
        else:
            return "Your profile is complete! Is there anything you'd like to modify?"
            
        return questions.get(self.current_field, "Could you tell me more?")

    def get_field_prompt(self, field: str) -> str:
        """Get a specific prompt for the current field."""
        prompts = {
            "name": "Please tell me your full name.",
            "age": "What is your age?",
            "location": "Where are you located (city/country)?",
            "education_degree": "What degree did you earn?",
            "education_institution": "Which institution did you attend?",
            "education_year": "What year did you graduate?",
            "profession": "What is your current profession?",
            "company": "Which company do you work for?",
            "experience": "What's your professional experience? Include job titles, companies, and durations.",
            "skills": "What tools and technologies are you familiar with? List the main ones you use.",
            "languages": "What languages do you speak?",
            "certifications": "Do you have any professional certifications? Please list them."
        }
        return prompts.get(field, "Please provide more information.")

    def get_example_message(self) -> str:
        """Get example message based on current field."""
        examples = {
            "name": "For example: 'My name is John Smith' or just 'John Smith'",
            "age": "For example: '25' or 'I am 25 years old'",
            "location": "For example: 'I live in New York, USA' or just 'New York, USA'",
            "education_degree": "For example: 'Bachelor's in Computer Science'",
            "education_institution": "For example: 'Stanford University'",
            "education_year": "For example: '2019'",
            "profession": "For example: 'Software Engineer' or 'Data Scientist'",
            "company": "For example: 'Google' or 'Microsoft'",
            "experience": "For example: 'I worked as a Software Engineer at Google for 3 years'",
            "skills": "For example: 'I know Python, JavaScript, and React'",
            "languages": "For example: 'I speak English and Spanish'",
            "certifications": "For example: 'I have AWS Certified Solutions Architect and CISSP certifications'"
        }
        return examples.get(self.current_field, "Could you please be more specific?")

    def get_natural_transition(self, current_field: str, next_field: str) -> str:
        """Get a natural transition phrase between fields."""
        transitions = {
            ("name", "age"): [
                "Thanks for sharing your name! How old are you?",
                "Nice to meet you! Could you tell me your age?",
                "Great! And what's your age?"
            ],
            ("age", "location"): [
                "Thanks! Where are you currently located?",
                "And where are you based?",
                "Which city do you live in?"
            ],
            ("location", "education_degree"): [
                "Great! Now let's talk about your education. What degree did you earn? (e.g., 'Bachelor's in Computer Science')",
            ],
            ("education_degree", "education_institution"): [
                "Which institution did you attend?",
                "Where did you earn your degree?",
                "What's the name of your alma mater?"
            ],
            ("education_institution", "education_year"): [
                "What year did you graduate?",
                "When did you complete your degree?",
                "What's your graduation year?"
            ],
            ("education_year", "profession"): [
                "What's your current profession?",
                "Tell me about your current role.",
                "What do you do professionally?"
            ],
            ("profession", "company"): [
                "Which company do you work for?",
                "Where are you currently employed?",
                "What's the name of your current company?"
            ],
            ("company", "skills"): [
                "What tools and technologies do you work with?",
                "Which technical skills do you use most often?",
                "Tell me about the technologies you're experienced with."
            ],
            ("skills", "languages"): [
                "Which languages do you speak?",
                "Tell me about your language skills.",
                "What languages are you comfortable with?"
            ],
            ("languages", "certifications"): [
                "Do you have any professional certifications?",
                "Have you earned any certifications worth mentioning?",
                "Any professional certifications to add?"
            ]
        }
        
        key = (current_field, next_field)
        if key in transitions:
            # Use current time as seed for some variety
            seed = int(datetime.now().timestamp()) % len(transitions[key])
            return transitions[key][seed]
        return self.get_default_question(next_field)

    def get_default_question(self, field: str) -> str:
        """Get a default question for a field."""
        questions = {
            "name": "What's your name?",
            "age": "How old are you?",
            "location": "Where are you located?",
            "education_degree": "What degree did you earn?",
            "education_institution": "Which institution did you attend?",
            "education_year": "What year did you graduate?",
            "profession": "What is your current profession?",
            "company": "Which company do you work for?",
            "experience": "What's your professional experience?",
            "skills": "What tools and technologies are you experienced with?",
            "languages": "What languages do you speak?",
            "certifications": "Do you have any professional certifications?"
        }
        return questions.get(field, "Could you tell me more?")

    def calculate_completeness(self) -> float:
        """Calculate profile completeness score."""
        field_weights = {
            'name': 1.0,
            'age': 0.8,
            'location': 0.9,
            'education': 1.0,
            'current_role': 1.0,
            'professional_experience': 1.0,
            'tools_technologies': 0.9,
            'languages': 0.7,
            'certifications': 0.6
        }
        
        total_weight = sum(field_weights.values())
        current_score = 0.0
        
        # Basic fields
        if self.profile.name:
            current_score += field_weights['name']
        if self.profile.age:
            current_score += field_weights['age']
        if self.profile.location:
            current_score += field_weights['location']
            
        # Education
        if self.profile.education:
            education_score = 0.0
            if self.profile.education.degree:
                education_score += 0.4
            if self.profile.education.institution:
                education_score += 0.4
            if self.profile.education.graduation_year:
                education_score += 0.2
            current_score += field_weights['education'] * education_score
            
        # Professional Experience
        if self.profile.current_role:
            current_score += field_weights['current_role']
            
        if self.profile.professional_experience:
            exp_score = 0.0
            for exp in self.profile.professional_experience:
                if exp.role:
                    exp_score += 0.4
                if exp.company:
                    exp_score += 0.4
                if exp.duration or exp.is_current:
                    exp_score += 0.2
            exp_score = min(1.0, exp_score)  # Cap at 1.0
            current_score += field_weights['professional_experience'] * exp_score
            
        # Skills and additional info
        if self.profile.tools_technologies:
            current_score += field_weights['tools_technologies']
        if self.profile.languages:
            current_score += field_weights['languages']
        if self.profile.certifications:
            current_score += field_weights['certifications']
            
        # Calculate final percentage
        completeness = (current_score / total_weight) * 100
        return min(100, max(0, completeness))  # Ensure between 0 and 100

    def generate_summary(self) -> str:
        """Generate a professional summary of the user's profile."""
        return self.data_processor.generate_profile_summary(self.profile)

    def generate_profile_summary(self) -> Tuple[str, bool]:
        """Generate and return the profile summary."""
        summary = self.generate_summary()
        return f"\nHere's your complete profile summary:\n\n{summary}\n\nIs there anything you'd like to modify?", True

    def _update_current_field(self):
        """Update the current field based on profile completion."""
        if not self.profile.name:
            self.current_field = "name"
        elif not self.profile.age:
            self.current_field = "age"
        elif not self.profile.location:
            self.current_field = "location"
        elif not self.profile.education:
            self.current_field = "education_degree"
        elif not self.profile.education.degree:
            self.current_field = "education_degree"
        elif not self.profile.education.institution:
            self.current_field = "education_institution"
        elif not self.profile.education.graduation_year:
            self.current_field = "education_year"
        elif not self.profile.current_role:
            self.current_field = "profession"
        elif not self.profile.professional_experience or not any(exp.company for exp in self.profile.professional_experience):
            self.current_field = "company"
        elif not self.profile.tools_technologies:
            self.current_field = "skills"
        elif not self.profile.languages:
            self.current_field = "languages"
        elif not self.profile.certifications:
            self.current_field = "certifications"
        else:
            self.current_field = None
