import re
from typing import Optional, Tuple, List, Any, Dict
from models import UserProfile, Education, ProfessionalExperience
import openai
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class NLPProcessor:
    @staticmethod
    def extract_name(text: str) -> Optional[str]:
        """Extract name from text using pattern matching."""
        patterns = [
            r"(?:my name is|i'm|i am|call me) ([A-Za-z\s]+)",
            r"^([A-Za-z\s]+)$",
            r"(?:this is) ([A-Za-z\s]+)",
            r"([A-Za-z\s]+) (?:here|speaking)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                name = match.group(1).strip()
                # Filter out common words that might be mistaken for names
                if name not in ["yes", "no", "okay", "hi", "hello"]:
                    return name.title()
        return None

    @staticmethod
    def extract_age(text: str) -> Optional[int]:
        """Extract age from text."""
        patterns = [
            r"(?:i am|i'm|im) (\d+)(?: years old)?",
            r"^(\d+)$",
            r"(\d+)(?: years old)",
            r"age(?:d)? (\d+)",
            r"(\d+)(?: years?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    age = int(match.group(1))
                    if 0 < age < 120:  # Basic age validation
                        return age
                except ValueError:
                    continue
        return None

    @staticmethod
    def extract_location(text: str) -> Optional[str]:
        """Extract location information."""
        patterns = [
            r"(?:i(?:'m| am) (?:from|in|at|living in)) ([A-Za-z\s,]+)",
            r"(?:i live in) ([A-Za-z\s,]+)",
            r"(?:based in) ([A-Za-z\s,]+)",
            r"(?:located in) ([A-Za-z\s,]+)",
            r"(?:my location is) ([A-Za-z\s,]+)",
            r"^([A-Za-z]+(?:\s*,\s*[A-Za-z]+)?)"  # Matches "City" or "City, Country"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                location = match.group(1).strip()
                # Filter out common words that might be mistaken for locations
                if location not in ["here", "there", "somewhere"]:
                    # Properly capitalize location parts
                    parts = [part.strip().title() for part in location.split(',')]
                    return ', '.join(parts)
        return None

    @staticmethod
    def extract_education(text: str) -> Optional[Education]:
        """Extract education information using both regex and GPT."""
        # First try pattern matching
        degree_patterns = [
            r"(?:i have|earned|got|studying|completed|finished) (?:a|an)? ([^,\.]+?) (?:degree|diploma)",
            r"([^,\.]+?)(?: degree| diploma) (?:from|at)",
            r"^([^,\.]+?) (?:from|at)",
            r"masters? (?:of|in) [^,\.]+",
            r"bachelor'?s? (?:of|in) [^,\.]+",
            r"phd(?: in)? [^,\.]+",
            r"doctorate(?: in)? [^,\.]+",
        ]
        
        institution_patterns = [
            r"(?:from|at) (?:the )?([^,\.]+?)(?:\sin|\s?[\.,]|$)",
            r"(?:university|college|institute) (?:of )?([^,\.]+?)(?:\sin|\s?[\.,]|$)",
        ]
        
        year_patterns = [
            r"(?:in|year) (\d{4})",
            r"graduated (?:in )?(\d{4})",
            r"class of (\d{4})",
        ]

        education = Education()
        
        # Try to extract degree
        for pattern in degree_patterns:
            match = re.search(pattern, text.lower())
            if match:
                education.degree = match.group(1).strip().title()
                break
        
        # Try to extract institution
        for pattern in institution_patterns:
            match = re.search(pattern, text.lower())
            if match:
                education.institution = match.group(1).strip().title()
                break
        
        # Try to extract year
        for pattern in year_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    year = int(match.group(1))
                    if 1950 <= year <= 2030:  # Basic validation
                        education.graduation_year = year
                        break
                except ValueError:
                    continue

        # If regex didn't get all fields, try GPT
        if not (education.degree and education.institution and education.graduation_year):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """Extract education information from the text. 
                        Return a JSON object with these fields:
                        - degree: The full degree name
                        - institution: The university or institution name
                        - graduation_year: The year of graduation (integer)
                        Only include fields where information is clearly provided."""},
                        {"role": "user", "content": text}
                    ]
                )
                
                gpt_info = json.loads(response.choices[0].message['content'])
                
                if not education.degree and 'degree' in gpt_info:
                    education.degree = gpt_info['degree']
                if not education.institution and 'institution' in gpt_info:
                    education.institution = gpt_info['institution']
                if not education.graduation_year and 'graduation_year' in gpt_info:
                    education.graduation_year = gpt_info['graduation_year']
                
            except Exception as e:
                print(f"Error processing with GPT: {str(e)}")

        return education if education.degree or education.institution else None

    @staticmethod
    def extract_professional_experience(text: str) -> Optional[List[ProfessionalExperience]]:
        """Extract professional experience using both pattern matching and GPT."""
        experiences = []
        
        # Pattern matching for common formats
        job_patterns = [
            r"(?:i (?:am|work) (?:as|at)(?: an?)? ([^,\.]+?)(?:at|in|with|for)(?: the)? ([^,\.]+?)(?:for|since)? ?(\d+(?:\.\d+)? years?)?)",
            r"([^,\.]+?) (?:at|@|in) ([^,\.]+?)(?:for|since)? ?(\d+(?:\.\d+)? years?)?",
            r"(?:i'?m)(?: an?)? ([^,\.]+?)(?: at|@|in) ([^,\.]+?)(?:for|since)? ?(\d+(?:\.\d+)? years?)?"
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                exp = ProfessionalExperience()
                exp.job_title = match.group(1).strip().title()
                exp.company_name = match.group(2).strip().title()
                if len(match.groups()) > 2 and match.group(3):
                    exp.duration = match.group(3).strip()
                if exp.job_title and exp.company_name:
                    experiences.append(exp)
        
        # If pattern matching fails, try GPT
        if not experiences:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """Extract professional experience information from the text.
                        Return a JSON array of experiences, where each experience has:
                        - job_title: The person's role or position
                        - company_name: The company or organization name
                        - duration: How long they worked there
                        - notable_projects: List of notable projects or responsibilities (if mentioned)
                        Only include experiences that are clearly mentioned in the text."""},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3
                )
                
                gpt_info = json.loads(response.choices[0].message['content'])
                if isinstance(gpt_info, list):
                    for exp_data in gpt_info:
                        exp = ProfessionalExperience(
                            job_title=exp_data.get('job_title', ''),
                            company_name=exp_data.get('company_name', ''),
                            duration=exp_data.get('duration', ''),
                            notable_projects=exp_data.get('notable_projects', [])
                        )
                        if exp.job_title and exp.company_name:
                            experiences.append(exp)
                            
            except Exception as e:
                print(f"Error processing with GPT: {str(e)}")
        
        return experiences if experiences else None

    @staticmethod
    def extract_tools_technologies(text: str) -> Optional[List[str]]:
        """Extract tools and technologies from text using both pattern matching and GPT."""
        # Common technology keywords
        tech_keywords = {
            'languages': ['python', 'javascript', 'java', 'c++', 'ruby', 'php', 'typescript', 'golang', 'rust', 'swift'],
            'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node', 'express', 'rails'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'dynamodb'],
            'cloud': ['aws', 'azure', 'gcp', 'cloud', 'kubernetes', 'docker', 'terraform'],
            'tools': ['git', 'jenkins', 'jira', 'confluence', 'webpack', 'nginx', 'linux', 'windows']
        }
        
        # Pattern matching for technology mentions
        tech_pattern = r'(?:use|using|work(?:ing)? with|experienced in|proficient in|skilled in|knowledge of) ([^,.]+)'
        technologies = set()
        
        # Try pattern matching first
        matches = re.finditer(tech_pattern, text.lower())
        for match in matches:
            tech_text = match.group(1).strip()
            # Split by common separators
            techs = re.split(r'(?:,|\s+and\s+|\s+&\s+|\s+)', tech_text)
            for tech in techs:
                tech = tech.strip()
                if tech:
                    # Check against known keywords
                    for category in tech_keywords.values():
                        if tech in category:
                            technologies.add(tech.title())
                    # Add if it looks like a technology (no common words)
                    if not any(word in tech for word in ['the', 'with', 'using', 'and', 'or', 'in']):
                        technologies.add(tech.title())
        
        # If pattern matching didn't find much, try GPT
        if len(technologies) < 2:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """Extract tools and technologies from the text.
                        Return a JSON array of technology names. Include:
                        - Programming languages
                        - Frameworks and libraries
                        - Databases
                        - Cloud platforms and services
                        - Development tools
                        Only include technologies that are clearly mentioned in the text."""},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3
                )
                
                gpt_techs = json.loads(response.choices[0].message['content'])
                if isinstance(gpt_techs, list):
                    for tech in gpt_techs:
                        if isinstance(tech, str) and tech.strip():
                            technologies.add(tech.strip().title())
                            
            except Exception as e:
                print(f"Error processing with GPT: {str(e)}")
        
        return list(technologies) if technologies else None

    @staticmethod
    def extract_languages(text: str) -> Optional[List[dict]]:
        """Extract spoken languages and proficiency levels."""
        # Common language proficiency levels and their variations
        proficiency_levels = {
            'native': ['native', 'mother tongue', 'first language'],
            'fluent': ['fluent', 'fluently', 'proficient', 'advanced'],
            'intermediate': ['intermediate', 'conversational', 'working knowledge'],
            'basic': ['basic', 'beginner', 'elementary']
        }
        
        # Common language names
        common_languages = [
            'english', 'spanish', 'french', 'german', 'italian', 'portuguese', 'russian',
            'mandarin', 'chinese', 'japanese', 'korean', 'arabic', 'hindi', 'bengali',
            'dutch', 'swedish', 'norwegian', 'danish', 'finnish', 'polish', 'turkish',
            'vietnamese', 'thai', 'indonesian', 'malay', 'tagalog', 'swahili'
        ]
        
        # Pattern matching for language mentions
        language_patterns = [
            r"(?:speak|know|use|understand) ([^,.]+?)(?:(?:,| and| &) )?([^,.]*?)(?: (?:at )?(?:an? )?([^,.]+?) level)?(?:ly)?(?=[,.]|$)",
            r"([^,.]+?) (?:speaker|proficiency|level)(?: at)?(?: an?)? ([^,.]+)?",
            r"(?:native|fluent|intermediate|basic)(?: in)? ([^,.]+)",
            r"([^,.]+?)(?: (?:-|:)? ?([^,.]+))?"
        ]
        
        languages = []
        
        # Try pattern matching first
        for pattern in language_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                groups = match.groups()
                
                # Extract language and proficiency from different group combinations
                lang = None
                prof = None
                
                for group in groups:
                    if not group:
                        continue
                    words = group.strip().split()
                    for word in words:
                        if word in common_languages:
                            lang = word
                        for level, variants in proficiency_levels.items():
                            if word in variants:
                                prof = level
                
                if lang:
                    # Default to 'fluent' if no proficiency specified
                    if not prof:
                        prof = 'fluent'
                    languages.append({
                        'language': lang.title(),
                        'proficiency': prof.title()
                    })
        
        # If pattern matching didn't find anything or found too little, try GPT
        if not languages:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": """Extract spoken languages and proficiency levels from the text.
                        Return a JSON array where each item has:
                        - language: The language name
                        - proficiency: The proficiency level (Native, Fluent, Intermediate, Basic)
                        Only include languages that are clearly mentioned in the text."""},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.3
                )
                
                gpt_langs = json.loads(response.choices[0].message['content'])
                if isinstance(gpt_langs, list):
                    for lang_info in gpt_langs:
                        if isinstance(lang_info, dict) and 'language' in lang_info and 'proficiency' in lang_info:
                            languages.append({
                                'language': lang_info['language'].title(),
                                'proficiency': lang_info['proficiency'].title()
                            })
                            
            except Exception as e:
                print(f"Error processing with GPT: {str(e)}")
        
        return languages if languages else None

    @staticmethod
    def process_with_llm(text: str, field: str) -> Dict:
        """Process text using OpenAI's GPT model for advanced entity extraction."""
        try:
            field_prompts = {
                "name": """Extract the person's name from the text. Be flexible in understanding different formats.
                Return a JSON object with:
                - name: The full name, properly capitalized
                
                Examples:
                "my name is john smith" -> {"name": "John Smith"}
                "i'm jane doe" -> {"name": "Jane Doe"}
                "call me mike" -> {"name": "Mike"}""",
                
                "age": """Extract the person's age from the text. Be flexible in understanding different formats.
                Return a JSON object with:
                - age: The age as a number
                
                Examples:
                "i am 25 years old" -> {"age": 25}
                "45" -> {"age": 45}
                "age: 30" -> {"age": 30}""",
                
                "location": """Extract location information from the text. Be flexible in understanding different formats.
                Return a JSON object with:
                - city: The city name
                - country: The country name
                - state: The state/province (if mentioned)
                
                Examples:
                "I live in New York, USA" -> {"city": "New York", "country": "USA"}
                "Based in London" -> {"city": "London"}
                "Tokyo, Japan" -> {"city": "Tokyo", "country": "Japan"}""",
                
                "education_degree": """Extract degree information from the text. Be flexible in understanding various formats.
                Return a JSON object with:
                - degree_type: The standardized type (e.g., "Master's", "Bachelor's", "Ph.D.")
                - field_of_study: The field or major
                - abbreviation: The degree abbreviation if given (e.g., "MSc", "BEng")
                
                Examples:
                "MSc in Data Science" -> {"degree_type": "Master's", "field_of_study": "Data Science", "abbreviation": "MSc"}
                "BEng" -> {"degree_type": "Bachelor's", "field_of_study": "Engineering", "abbreviation": "BEng"}
                "Master of Business Administration" -> {"degree_type": "Master's", "field_of_study": "Business Administration", "abbreviation": "MBA"}""",
                
                "education_institution": """Extract institution information from the text. Be flexible in understanding various formats and abbreviations.
                Return a JSON object with:
                - institution: The full institution name
                - abbreviation: Common abbreviation if used (e.g., MIT, UCLA)
                - location: Location if mentioned
                
                Examples:
                "MIT" -> {"institution": "Massachusetts Institute of Technology", "abbreviation": "MIT"}
                "University of California, Berkeley" -> {"institution": "University of California, Berkeley", "abbreviation": "UC Berkeley"}
                "Stanford" -> {"institution": "Stanford University"}""",
                
                "education_year": """Extract graduation year from the text. Be flexible in understanding different formats.
                Return a JSON object with:
                - year: The graduation year as a number
                
                Examples:
                "graduated in 2019" -> {"year": 2019}
                "class of 2020" -> {"year": 2020}
                "2018" -> {"year": 2018}""",
                
                "profession": """Extract profession information from the text. Be flexible in understanding different formats.
                Return a JSON object with:
                - role: The job title/role
                - level: The seniority level if mentioned (e.g., Senior, Lead, Junior)
                - department: The department/area if mentioned
                
                Examples:
                "Senior Software Engineer" -> {"role": "Software Engineer", "level": "Senior"}
                "Data Scientist" -> {"role": "Data Scientist"}
                "Lead Developer in AI team" -> {"role": "Developer", "level": "Lead", "department": "AI"}""",
                
                "company": """Extract company information from the text. Be flexible in understanding different formats.
                Return a JSON object with:
                - company_name: The company name
                - industry: The industry if mentioned
                
                Examples:
                "Google" -> {"company_name": "Google", "industry": "Technology"}
                "Working at Microsoft" -> {"company_name": "Microsoft", "industry": "Technology"}
                "Tesla Motors" -> {"company_name": "Tesla", "industry": "Automotive"}""",
                
                "skills": """Extract skills information from the text. Be flexible in understanding different formats.
                Return a JSON object with:
                - technical_skills: Array of technical skills
                - tools: Array of tools/software
                - soft_skills: Array of soft skills
                
                Examples:
                "I know Python, JavaScript and React" -> {"technical_skills": ["Python", "JavaScript"], "tools": ["React"]}
                "Expert in machine learning and data analysis" -> {"technical_skills": ["Machine Learning", "Data Analysis"]}"""
            }

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": field_prompts.get(field, "Extract relevant information from the text.")},
                    {"role": "user", "content": text}
                ]
            )
            
            return json.loads(response.choices[0].message['content'])
        except Exception as e:
            print(f"Error processing with LLM: {str(e)}")
            return {}

    @staticmethod
    def get_contextual_response(field: str, value: str) -> Optional[str]:
        """Get contextual information about a given field value using GPT."""
        field_prompts = {
            "location": """Given the location '{}', provide a brief, interesting fact about it. 
            Focus on one of these aspects: weather, culture, economy, or notable features. 
            Keep it conversational and brief (max 15 words).""",
            
            "education": """Given the education detail '{}', share an interesting fact about the field 
            or institution. Focus on career prospects, notable alumni, or field importance. 
            Keep it conversational and brief (max 15 words).""",
            
            "professional_experience": """Given the role '{}', mention an interesting trend or fact 
            about this profession. Focus on future outlook or industry impact. 
            Keep it conversational and brief (max 15 words).""",
            
            "tools_technologies": """Given the technology '{}', share an interesting fact about its 
            usage or importance. Focus on industry adoption or future potential. 
            Keep it conversational and brief (max 15 words)."""
        }
        
        if field not in field_prompts:
            return None
            
        try:
            print(f"\n🤖 GPT Request - Getting context for {field}: {value}")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable assistant providing brief, interesting facts. Keep responses natural and conversational."},
                    {"role": "user", "content": field_prompts[field].format(value)}
                ],
                temperature=0.7,
                max_tokens=30
            )
            
            fact = response.choices[0].message['content'].strip()
            print(f"🤖 GPT Response: {fact}")
            
            # Remove common prefixes that GPT might add
            fact = re.sub(r'^(Fun fact:|Did you know|Interesting:|Note:)\s*', '', fact, flags=re.IGNORECASE)
            # Ensure first letter is capitalized
            fact = fact[0].upper() + fact[1:] if fact else fact
            return fact
            
        except Exception as e:
            print(f"❌ Error getting GPT response: {str(e)}")
            return None

    @staticmethod
    def validate_input(field: str, value: Any) -> Tuple[bool, str]:
        """Validate input values for specific fields."""
        validators = {
            "name": lambda x: bool(re.match(r'^[A-Za-z\s\'-]{2,50}$', x)),
            "age": lambda x: isinstance(x, int) and 15 <= x <= 120,
            "location": lambda x: bool(re.match(r'^[A-Za-z\s,\'-]{2,100}$', x)),
            "graduation_year": lambda x: isinstance(x, int) and 1950 <= x <= datetime.now().year,
            "email": lambda x: bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', x)),
            "phone": lambda x: bool(re.match(r'^\+?[\d\s-]{10,20}$', x))
        }
        
        error_messages = {
            "name": "Name should contain only letters, spaces, hyphens, and apostrophes (2-50 characters).",
            "age": "Age should be between 15 and 120.",
            "location": "Location should contain only letters, spaces, commas, hyphens, and apostrophes (2-100 characters).",
            "graduation_year": f"Graduation year should be between 1950 and {datetime.now().year}.",
            "email": "Please enter a valid email address.",
            "phone": "Please enter a valid phone number (10-20 digits, can include spaces and hyphens)."
        }
        
        if field not in validators:
            return True, ""
            
        is_valid = validators[field](value)
        error_message = "" if is_valid else error_messages[field]
        return is_valid, error_message

    @staticmethod
    def infer_age_from_graduation(graduation_year: int) -> Optional[int]:
        """Infer approximate age from graduation year."""
        current_year = datetime.now().year
        if 1950 <= graduation_year <= current_year:
            # Assume typical graduation age of 22 for undergrad
            return current_year - graduation_year + 22
        return None

    @staticmethod
    def infer_experience_duration(text: str) -> Optional[str]:
        """Infer duration from context clues."""
        # Add year-based inference
        year_pattern = r'(?:since|from|in) (\d{4})'
        year_match = re.search(year_pattern, text.lower())
        if year_match:
            start_year = int(year_match.group(1))
            current_year = datetime.now().year
            years = current_year - start_year
            return f"{years} years"
        return None

    @staticmethod
    def detect_intent(text: str) -> Tuple[str, float]:
        """Detect the user's intent from their input."""
        intents = {
            "provide_info": [
                r"(?:my|i|the) (?:name|age|location|education|experience|skills|language)",
                r"(?:i am|i'm|i've|i have|i worked|i studied)",
                r"(?:graduated|completed|achieved|earned|received)",
            ],
            "ask_question": [
                r"\?$",
                r"(?:what|how|when|where|why|can you|could you)",
                r"(?:tell me|explain|show|help)",
            ],
            "confirm": [
                r"(?:yes|yeah|correct|right|exactly|sure|ok|okay)",
                r"(?:that's right|that is correct|sounds good)",
            ],
            "deny": [
                r"(?:no|nope|incorrect|wrong|not right|not correct)",
                r"(?:that's wrong|that is incorrect)",
            ],
            "modify": [
                r"(?:change|update|modify|edit|revise)",
                r"(?:different|instead|rather)",
            ],
            "complete": [
                r"(?:done|finished|complete|that's all|that's it)",
                r"(?:move on|next|continue|proceed)",
            ],
            "help": [
                r"(?:help|confused|unclear|don't understand|do not understand)",
                r"(?:example|explain|clarify|what do you mean)",
            ],
            "greet": [
                r"(?:hi|hello|hey|good morning|good afternoon|good evening)",
                r"(?:greetings|welcome|nice to meet)",
            ],
            "exit": [
                r"(?:bye|goodbye|exit|quit|leave|end)",
                r"(?:thank you|thanks|that's all for now)",
            ]
        }
        
        # Check each intent's patterns
        max_score = 0
        detected_intent = "unknown"
        
        for intent, patterns in intents.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text.lower()):
                    score += 1
            score = score / len(patterns)
            if score > max_score:
                max_score = score
                detected_intent = intent
                
        # Use OpenAI for more nuanced intent detection
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an intent detection system. Classify the user's intent into one of these categories: provide_info, ask_question, confirm, deny, modify, complete, help, greet, exit. Return ONLY the category name."},
                    {"role": "user", "content": f"Classify this text: {text}"}
                ],
                temperature=0.3,
                max_tokens=10
            )
            
            ai_intent = response.choices[0].message.content.strip().lower()
            if ai_intent in intents and max_score < 0.8:  # Trust AI if pattern matching isn't confident
                detected_intent = ai_intent
                max_score = 0.8
                
        except Exception as e:
            print(f"Error in AI intent detection: {str(e)}")
            
        return detected_intent, max_score

    @staticmethod
    def infer_information(text: str, current_field: str, profile: UserProfile) -> Dict[str, Any]:
        """Infer implicit information from context."""
        inferred_data = {}
        
        try:
            # Only infer age from graduation year if age is not already set
            if not profile.age and ("graduated" in text.lower() or "graduation" in text.lower()):
                year_match = re.search(r'\b(19|20)\d{2}\b', text)
                if year_match:
                    grad_year = int(year_match.group())
                    current_year = datetime.now().year
                    if "high school" in text.lower():
                        inferred_age = current_year - grad_year + 18
                    else:  # Assume college graduation
                        inferred_age = current_year - grad_year + 22
                    inferred_data["age"] = inferred_age
                    
            # Infer location from company or university
            if "company" in text.lower() or "university" in text.lower() or "college" in text.lower():
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Extract location information from the text. Return ONLY the city and/or country if mentioned."},
                            {"role": "user", "content": text}
                        ],
                        temperature=0.3,
                        max_tokens=50
                    )
                    location = response.choices[0].message.content.strip()
                    if location and location.lower() not in ["none", "no location", "not mentioned"]:
                        inferred_data["location"] = location
                except Exception as e:
                    print(f"Error in location inference: {str(e)}")
                    
            # Infer skills from experience
            if "experience" in current_field and ("developed" in text.lower() or "built" in text.lower() or "created" in text.lower()):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Extract technical skills, tools, and technologies mentioned in the text. Return them as a comma-separated list."},
                            {"role": "user", "content": text}
                        ],
                        temperature=0.3,
                        max_tokens=100
                    )
                    skills = [s.strip() for s in response.choices[0].message.content.split(",")]
                    if skills:
                        inferred_data["tools_technologies"] = skills
                except Exception as e:
                    print(f"Error in skills inference: {str(e)}")
                    
            # Infer education details
            if "education" in current_field:
                edu_patterns = {
                    "degree": r"(Bachelor'?s|Master'?s|Ph\.?D\.?|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)",
                    "major": r"(?:in|of) ([A-Za-z\s]+?)(?:from|at|,|\.|$)",
                    "institution": r"(?:from|at) ([A-Za-z\s]+)(?:in|,|\.|$)"
                }
                
                for field, pattern in edu_patterns.items():
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        if "education" not in inferred_data:
                            inferred_data["education"] = {}
                        inferred_data["education"][field] = match.group(1).strip()
                        
            # Infer professional experience details
            if "experience" in current_field:
                exp_patterns = {
                    "duration": r"(\d+)\s*(?:year|yr|month|mo)s?",
                    "job_title": r"(?:as|a|an)\s+([A-Za-z\s]+?)(?:at|in|with|,|\.|$)",
                    "company_name": r"(?:at|with|for)\s+([A-Za-z\s]+?)(?:in|for|,|\.|$)"
                }
                
                for field, pattern in exp_patterns.items():
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        if "professional_experience" not in inferred_data:
                            inferred_data["professional_experience"] = {}
                        inferred_data["professional_experience"][field] = match.group(1).strip()
                        
        except Exception as e:
            print(f"Error in information inference: {str(e)}")
            
        return inferred_data
