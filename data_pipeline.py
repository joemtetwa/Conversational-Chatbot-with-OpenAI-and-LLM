from typing import Dict, List, Optional, Tuple, Any
import openai
from models import UserProfile, Education, ProfessionalExperience, Project
import re
from datetime import datetime
import json
import os
from dotenv import load_dotenv

class DataProcessor:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Set OpenAI API key
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
            
        self.field_weights = {
            # Basic Information (35%)
            "name": 0.10,
            "age": 0.05,
            "location": 0.05,
            "email": 0.05,
            "phone": 0.05,
            "linkedin": 0.03,
            "github": 0.02,
            
            # Education and Experience (30%)
            "education": 0.15,
            "professional_experience": 0.15,
            
            # Skills and Technologies (20%)
            "tools_technologies": 0.05,
            "programming_languages": 0.05,
            "frameworks": 0.05,
            "soft_skills": 0.05,
            
            # Additional Information (15%)
            "languages": 0.05,
            "certifications": 0.05,
            "projects": 0.05
        }
        
        # Define entity extraction prompts
        self.entity_extraction_prompt = """
        Extract structured information from the text and return a JSON object.
        Include as many details as possible from these categories:

        1. Basic Information:
        - name: Full name
        - age: Numeric age
        - location: City/Country
        - email: Email address
        - phone: Phone number
        - linkedin: LinkedIn URL
        - github: GitHub URL

        2. Education:
        - degree: Degree name
        - institution: School/University
        - graduation_year: Year
        - major: Field of study
        - gpa: GPA if mentioned
        - achievements: List of academic achievements

        3. Professional Experience:
        List of jobs with:
        - job_title: Position
        - company_name: Company
        - duration: Time period
        - start_date: Start date
        - end_date: End date
        - responsibilities: List of duties
        - projects: List of projects
        - achievements: List of achievements

        4. Skills:
        - tools_technologies: List of tools
        - programming_languages: List of languages
        - frameworks: List of frameworks
        - soft_skills: List of soft skills

        5. Additional Information:
        - languages: Languages spoken
        - certifications: Professional certifications
        - interests: Professional interests

        Text to analyze: {text}
        """
        
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text using OpenAI."""
        try:
            # Create a more specific prompt for the current context
            prompt = """
            Extract information from the following text and return it in JSON format.
            If you find a name, return it exactly as provided without modifications.
            If you're not sure about a value, don't include that field in the JSON.
            
            Example outputs:
            {"name": "Joe"} - for just a name
            {"name": "Joe Smith", "age": 25} - for name and age
            
            Current text to analyze: {text}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured information from text. Always return valid JSON."},
                    {"role": "user", "content": prompt.format(text=text)}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            print(f"OpenAI Response: {content}")  # Debug print
            
            try:
                extracted = json.loads(content)
                print(f"Extracted data: {extracted}")  # Debug print
                return extracted
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)}")  # Debug print
                return {}
                
        except Exception as e:
            print(f"Error in entity extraction: {str(e)}")
            return {}
            
    def validate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Validate extracted data and return tuple of (valid_data, validation_messages)."""
        valid_data = {}
        messages = []
        
        try:
            # Print debug information
            print(f"Input data: {data}")
            
            # Validate name
            if "name" in data:
                name = str(data["name"]).strip()
                if len(name) > 0:
                    valid_data["name"] = name
                else:
                    messages.append("Invalid name format")
                    
            # Validate age
            if "age" in data:
                try:
                    age = int(data["age"])
                    if 0 < age < 120:
                        valid_data["age"] = age
                    else:
                        messages.append("Age out of valid range")
                except (ValueError, TypeError):
                    messages.append("Invalid age format")
                    
            # Validate location
            if "location" in data:
                location = str(data["location"]).strip()
                if len(location) > 0:
                    valid_data["location"] = location
                    
            # Validate education
            if "education" in data and isinstance(data["education"], dict):
                edu_data = data["education"]
                valid_edu = {}
                
                # Validate degree
                if "degree" in edu_data:
                    degree = str(edu_data["degree"]).strip()
                    if len(degree) > 0:
                        valid_edu["degree"] = degree
                        
                # Validate major
                if "major" in edu_data:
                    major = str(edu_data["major"]).strip()
                    if len(major) > 0:
                        valid_edu["major"] = major
                        
                # Validate institution
                if "institution" in edu_data:
                    institution = str(edu_data["institution"]).strip()
                    if len(institution) > 0:
                        valid_edu["institution"] = institution
                        
                # Validate graduation year
                if "graduation_year" in edu_data:
                    try:
                        year = int(edu_data["graduation_year"])
                        current_year = datetime.now().year
                        if 1950 <= year <= current_year + 5:  # Allow future graduation dates up to 5 years
                            valid_edu["graduation_year"] = year
                            print(f"Validated graduation year: {year}")  # Debug print
                        else:
                            messages.append("Invalid graduation year")
                    except (ValueError, TypeError):
                        messages.append("Invalid graduation year format")
                
                if valid_edu:
                    valid_data["education"] = valid_edu
                    print(f"Validated education data: {valid_edu}")  # Debug print
                    
            print(f"Validated data: {valid_data}")
            print(f"Validation messages: {messages}")
            
        except Exception as e:
            messages.append(f"Error in data validation: {str(e)}")
            print(f"Error in data validation: {str(e)}")
            
        return valid_data, messages
            
    def update_profile(self, profile: UserProfile, new_data: Dict[str, Any]) -> Tuple[UserProfile, List[str]]:
        """Update profile with new data, handling conflicts and ambiguities."""
        messages = []
        print(f"Updating profile with new data: {new_data}")  # Debug print
        
        try:
            # Update basic fields
            if "name" in new_data:
                profile.name = new_data["name"]
                print(f"Updated name to: {profile.name}")
                
            if "age" in new_data:
                profile.age = new_data["age"]
                print(f"Updated age to: {profile.age}")
                
            if "location" in new_data:
                profile.location = new_data["location"]
                print(f"Updated location to: {profile.location}")
                
            # Update education
            if "education" in new_data:
                edu_data = new_data["education"]
                print(f"Updating education with: {edu_data}")
                
                # Create a new Education instance with the updated data
                education = Education(
                    degree=edu_data.get("degree", profile.education.degree),
                    major=edu_data.get("major", profile.education.major),
                    institution=edu_data.get("institution", profile.education.institution),
                    graduation_year=edu_data.get("graduation_year", profile.education.graduation_year)
                )
                
                # Update profile education
                profile.education = education
                print(f"Updated education: {profile.education}")
                
            # Update last_updated timestamp
            profile.last_updated = datetime.now().isoformat()
            print(f"Updated profile: {profile.__dict__}")
            
        except Exception as e:
            messages.append(f"Error updating profile: {str(e)}")
            print(f"Error updating profile: {str(e)}")
            
        return profile, messages

    def calculate_completeness(self, profile: UserProfile) -> Tuple[float, Dict[str, float]]:
        """Calculate profile completeness score and individual field scores."""
        try:
            scores = {}
            total_weight = 0
            total_score = 0
            
            # Basic Information
            if profile.name:
                scores["name"] = self.field_weights["name"]
                total_score += scores["name"]
            if profile.age:
                scores["age"] = self.field_weights["age"]
                total_score += scores["age"]
            if profile.location:
                scores["location"] = self.field_weights["location"]
                total_score += scores["location"]
                
            # Education
            edu_score = 0
            if profile.education:
                if profile.education.degree:
                    edu_score += 0.4
                if profile.education.institution:
                    edu_score += 0.3
                if profile.education.graduation_year:
                    edu_score += 0.3
            scores["education"] = edu_score * self.field_weights["education"]
            total_score += scores["education"]
            
            # Experience
            exp_score = 0
            if profile.professional_experience:
                exp_score = min(len(profile.professional_experience) / 2, 1.0)
            scores["professional_experience"] = exp_score * self.field_weights["professional_experience"]
            total_score += scores["professional_experience"]
            
            # Skills
            if profile.tools_technologies:
                scores["tools_technologies"] = self.field_weights["tools_technologies"]
                total_score += scores["tools_technologies"]
                
            # Languages
            if profile.languages:
                scores["languages"] = self.field_weights["languages"]
                total_score += scores["languages"]
                
            # Certifications
            if profile.certifications:
                scores["certifications"] = self.field_weights["certifications"]
                total_score += scores["certifications"]
                
            # Calculate total weight of scored fields
            total_weight = sum(self.field_weights[field] for field in scores.keys())
            
            # Normalize score if we have weights
            if total_weight > 0:
                normalized_score = total_score / total_weight
            else:
                normalized_score = 0
                
            return normalized_score, scores
            
        except Exception as e:
            print(f"Error calculating completeness: {str(e)}")
            return 0.0, {}
    
    def get_missing_fields(self, profile: UserProfile) -> List[str]:
        """Get list of missing or incomplete fields."""
        missing = []
        
        if not profile.name:
            missing.append("name")
        if not profile.age:
            missing.append("age")
        if not profile.location:
            missing.append("location")
            
        if not profile.education or not all([profile.education.degree, 
                                           profile.education.institution, 
                                           profile.education.graduation_year]):
            missing.append("education details")
            
        if not profile.professional_experience:
            missing.append("professional experience")
            
        if len(profile.tools_technologies) < 3:
            missing.append("tools and technologies")
        if len(profile.languages) < 1:
            missing.append("languages spoken")
            
        return missing

    def generate_profile_summary(self, profile: UserProfile) -> str:
        """Generate a professional summary of the user's profile using OpenAI."""
        try:
            # Create a structured profile text
            profile_text = f"""
            Name: {profile.name}
            Age: {profile.age}
            Location: {profile.location}
            
            Education:
            - Degree: {profile.education.degree}
            - Institution: {profile.education.institution}
            - Graduation Year: {profile.education.graduation_year}
            
            Professional Experience:
            {self._format_experience(profile.professional_experience)}
            
            Tools & Technologies: {', '.join(profile.tools_technologies)}
            
            Languages: {', '.join(profile.languages)}
            
            Certifications: {', '.join(profile.certifications)}
            """
            
            # Create the prompt for OpenAI
            prompt = """
            Generate a professional and engaging summary of this person's profile. 
            The summary should:
            1. Highlight key qualifications and experience
            2. Emphasize notable skills and achievements
            3. Be written in a professional yet personable tone
            4. Be concise (2-3 paragraphs)
            5. Include a statement about their potential value to employers
            
            Profile Information:
            {text}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional profile writer who creates compelling professional summaries."},
                    {"role": "user", "content": prompt.format(text=profile_text)}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating profile summary: {str(e)}")
            return "Unable to generate profile summary at this time."
    
    def _format_experience(self, experiences: List[ProfessionalExperience]) -> str:
        """Format professional experience list for the summary."""
        if not experiences:
            return "No professional experience listed"
            
        formatted = ""
        for exp in experiences:
            formatted += f"- {exp.job_title} at {exp.company_name} ({exp.duration})\n"
            if exp.notable_projects:
                formatted += "  Projects: " + ", ".join(exp.notable_projects) + "\n"
        return formatted
