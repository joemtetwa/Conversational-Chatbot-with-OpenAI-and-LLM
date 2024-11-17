from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Education:
    degree: str = ""
    institution: str = ""
    graduation_year: int = 0
    major: str = ""
    gpa: float = 0.0
    achievements: List[str] = field(default_factory=list)

@dataclass
class ProfessionalExperience:
    job_title: str = ""
    company_name: str = ""
    duration: str = ""
    start_date: str = ""
    end_date: str = ""
    responsibilities: List[str] = field(default_factory=list)
    notable_projects: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

@dataclass
class Project:
    name: str = ""
    description: str = ""
    technologies: List[str] = field(default_factory=list)
    role: str = ""
    duration: str = ""
    outcomes: List[str] = field(default_factory=list)

@dataclass
class UserProfile:
    # Basic Information
    name: str = ""
    age: int = 0
    location: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    
    # Professional Summary
    summary: str = ""
    headline: str = ""
    
    # Education and Experience
    education: Education = field(default_factory=Education)
    professional_experience: List[ProfessionalExperience] = field(default_factory=list)
    
    # Skills and Technologies
    tools_technologies: List[str] = field(default_factory=list)
    programming_languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    
    # Projects and Achievements
    projects: List[Project] = field(default_factory=list)
    recent_achievements: List[str] = field(default_factory=list)
    
    # Additional Information
    languages: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    
    # Profile Metadata
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    completeness_score: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert profile to dictionary format."""
        return {
            "basic_info": {
                "name": self.name,
                "age": self.age,
                "location": self.location,
                "email": self.email,
                "phone": self.phone,
                "linkedin": self.linkedin,
                "github": self.github
            },
            "professional_summary": {
                "summary": self.summary,
                "headline": self.headline
            },
            "education": {
                "degree": self.education.degree,
                "institution": self.education.institution,
                "graduation_year": self.education.graduation_year,
                "major": self.education.major,
                "gpa": self.education.gpa,
                "achievements": self.education.achievements
            },
            "experience": [
                {
                    "title": exp.job_title,
                    "company": exp.company_name,
                    "duration": exp.duration,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "responsibilities": exp.responsibilities,
                    "projects": exp.notable_projects,
                    "achievements": exp.achievements
                }
                for exp in self.professional_experience
            ],
            "skills": {
                "tools_technologies": self.tools_technologies,
                "programming_languages": self.programming_languages,
                "frameworks": self.frameworks,
                "soft_skills": self.soft_skills
            },
            "projects": [
                {
                    "name": proj.name,
                    "description": proj.description,
                    "technologies": proj.technologies,
                    "role": proj.role,
                    "duration": proj.duration,
                    "outcomes": proj.outcomes
                }
                for proj in self.projects
            ],
            "achievements": self.recent_achievements,
            "additional_info": {
                "languages": self.languages,
                "certifications": self.certifications,
                "interests": self.interests
            },
            "metadata": {
                "last_updated": self.last_updated,
                "completeness_score": self.completeness_score
            }
        }

    def from_dict(self, data: dict) -> None:
        """Update profile from dictionary format."""
        basic_info = data.get("basic_info", {})
        self.name = basic_info.get("name", self.name)
        self.age = basic_info.get("age", self.age)
        self.location = basic_info.get("location", self.location)
        self.email = basic_info.get("email", self.email)
        self.phone = basic_info.get("phone", self.phone)
        self.linkedin = basic_info.get("linkedin", self.linkedin)
        self.github = basic_info.get("github", self.github)
        
        summary = data.get("professional_summary", {})
        self.summary = summary.get("summary", self.summary)
        self.headline = summary.get("headline", self.headline)
        
        edu = data.get("education", {})
        self.education = Education(
            degree=edu.get("degree", self.education.degree),
            institution=edu.get("institution", self.education.institution),
            graduation_year=edu.get("graduation_year", self.education.graduation_year),
            major=edu.get("major", self.education.major),
            gpa=edu.get("gpa", self.education.gpa),
            achievements=edu.get("achievements", self.education.achievements)
        )
        
        if "experience" in data:
            self.professional_experience = []
            for exp in data["experience"]:
                self.professional_experience.append(ProfessionalExperience(
                    job_title=exp.get("title", ""),
                    company_name=exp.get("company", ""),
                    duration=exp.get("duration", ""),
                    start_date=exp.get("start_date", ""),
                    end_date=exp.get("end_date", ""),
                    responsibilities=exp.get("responsibilities", []),
                    notable_projects=exp.get("projects", []),
                    achievements=exp.get("achievements", [])
                ))
        
        skills = data.get("skills", {})
        self.tools_technologies = skills.get("tools_technologies", self.tools_technologies)
        self.programming_languages = skills.get("programming_languages", self.programming_languages)
        self.frameworks = skills.get("frameworks", self.frameworks)
        self.soft_skills = skills.get("soft_skills", self.soft_skills)
        
        if "projects" in data:
            self.projects = []
            for proj in data["projects"]:
                self.projects.append(Project(
                    name=proj.get("name", ""),
                    description=proj.get("description", ""),
                    technologies=proj.get("technologies", []),
                    role=proj.get("role", ""),
                    duration=proj.get("duration", ""),
                    outcomes=proj.get("outcomes", [])
                ))
        
        self.recent_achievements = data.get("achievements", self.recent_achievements)
        
        additional = data.get("additional_info", {})
        self.languages = additional.get("languages", self.languages)
        self.certifications = additional.get("certifications", self.certifications)
        self.interests = additional.get("interests", self.interests)
