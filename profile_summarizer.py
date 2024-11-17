from transformers import pipeline
from models import UserProfile
from typing import Optional
import os

# Disable symlinks warning
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

class ProfileSummarizer:
    def __init__(self):
        # Using BART model fine-tuned for summarization
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=-1  # Use CPU. Change to 0 for GPU if available
        )

    def _create_profile_text(self, profile: UserProfile) -> str:
        """Convert profile information into a natural text format."""
        sections = []
        
        # Basic Information
        basic_info = []
        if profile.name:
            basic_info.append(f"{profile.name}")
        if profile.age:
            basic_info.append(f"is {profile.age} years old")
        if profile.location:
            basic_info.append(f"based in {profile.location}")
        if basic_info:
            sections.append(" ".join(basic_info) + ".")

        # Education
        if profile.education:
            edu_info = []
            if profile.education.degree:
                edu_info.append(f"holds a {profile.education.degree}")
            if profile.education.institution:
                edu_info.append(f"from {profile.education.institution}")
            if profile.education.graduation_year:
                edu_info.append(f"(graduated in {profile.education.graduation_year})")
            if edu_info:
                sections.append(" ".join(edu_info) + ".")

        # Professional Experience
        if profile.professional_experience:
            for exp in profile.professional_experience:
                exp_info = []
                if exp.role:
                    exp_info.append(f"works as {exp.role}")
                if exp.company:
                    exp_info.append(f"at {exp.company}")
                if exp_info:
                    sections.append(" ".join(exp_info) + ".")

        # Skills
        if profile.tools_technologies:
            sections.append(f"Skilled in {', '.join(profile.tools_technologies)}.")

        # Languages
        if profile.languages:
            sections.append(f"Speaks {', '.join(profile.languages)}.")

        # Combine all sections
        full_text = " ".join(sections)
        return full_text

    def generate_summary(self, profile: UserProfile) -> Optional[str]:
        """Generate a concise summary of the profile."""
        try:
            # Convert profile to text
            profile_text = self._create_profile_text(profile)
            if not profile_text:
                return None

            # Generate summary
            summary = self.summarizer(
                profile_text,
                max_length=130,
                min_length=30,
                do_sample=False
            )

            return summary[0]['summary_text']
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return None
