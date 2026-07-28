import unittest

from resume_profile_utils import resolve_profile_identity


class ResumeProfileUtilsTests(unittest.TestCase):
    def test_submitted_fields_are_preserved_over_resume_values(self):
        resume_text = "Name: Jane Smith\nDate of Birth: 1990-01-01"

        full_name, dob = resolve_profile_identity(resume_text, "John Doe", "2000-02-02")

        self.assertEqual(full_name, "John Doe")
        self.assertEqual(dob, "2000-02-02")

    def test_resume_values_are_used_when_form_fields_are_blank(self):
        resume_text = "Name: Jane Smith\nDate of Birth: 1990-01-01"

        full_name, dob = resolve_profile_identity(resume_text, "", "")

        self.assertEqual(full_name, "Jane Smith")
        self.assertEqual(dob, "1990-01-01")


if __name__ == "__main__":
    unittest.main()
