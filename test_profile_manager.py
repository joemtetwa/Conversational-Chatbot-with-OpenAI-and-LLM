from profile_manager import ProfileManager
from models import UserProfile, Education
import unittest

class TestProfileManager(unittest.TestCase):
    def setUp(self):
        self.profile_manager = ProfileManager()
        
    def test_name_input(self):
        """Test name input processing."""
        response, updated = self.profile_manager.process_input("Joe")
        self.assertTrue(updated)
        self.assertEqual(self.profile_manager.profile.name, "Joe")
        self.assertEqual(self.profile_manager.current_field, "age")
        
    def test_age_input(self):
        """Test age input processing."""
        # First set name
        self.profile_manager.process_input("Joe")
        
        # Then test age
        response, updated = self.profile_manager.process_input("40")
        self.assertTrue(updated)
        self.assertEqual(self.profile_manager.profile.age, 40)
        self.assertEqual(self.profile_manager.current_field, "location")
        
    def test_location_input(self):
        """Test location input processing."""
        # Set previous fields
        self.profile_manager.process_input("Joe")
        self.profile_manager.process_input("40")
        
        # Test location
        response, updated = self.profile_manager.process_input("Durban")
        self.assertTrue(updated)
        self.assertEqual(self.profile_manager.profile.location, "Durban")
        self.assertEqual(self.profile_manager.current_field, "education")
        
    def test_education_input(self):
        """Test education input processing."""
        # Set previous fields
        self.profile_manager.process_input("Joe")
        self.profile_manager.process_input("40")
        self.profile_manager.process_input("Durban")
        
        # Test education with graduation year
        education_input = "I have a Bachelor's in Computer Science from MIT, graduated in 2019"
        response, updated = self.profile_manager.process_input(education_input)
        self.assertTrue(updated)
        self.assertEqual(self.profile_manager.profile.education.degree, "Bachelor's")
        self.assertEqual(self.profile_manager.profile.education.major, "Computer Science")
        self.assertEqual(self.profile_manager.profile.education.institution, "MIT")
        self.assertEqual(self.profile_manager.profile.education.graduation_year, 2019)
        self.assertEqual(self.profile_manager.current_field, "experience")
        
    def test_example_requests(self):
        """Test example message requests."""
        # Test education example
        self.profile_manager.current_field = "education"
        response, updated = self.profile_manager.process_input("example")
        self.assertFalse(updated)
        self.assertIn("Bachelor's", response)
        self.assertIn("Computer Science", response)
        self.assertIn("MIT", response)
        
    def test_completeness(self):
        """Test profile completeness calculation."""
        # Empty profile should have low completeness
        self.assertLess(self.profile_manager.calculate_completeness(), 10)
        
        # Add basic info
        self.profile_manager.process_input("Joe")
        self.profile_manager.process_input("40")
        self.profile_manager.process_input("Durban")
        
        # Completeness should be higher but not complete
        completeness = self.profile_manager.calculate_completeness()
        self.assertGreater(completeness, 20)
        self.assertLess(completeness, 100)

if __name__ == '__main__':
    unittest.main()
