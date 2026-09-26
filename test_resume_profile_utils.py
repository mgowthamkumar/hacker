import unittest

from resume_profile_utils import (
    resolve_profile_identity,
    parse_and_embed_resume,
    chunk_resume_document,
    _extract_github_from_resume,
    _extract_linkedin_from_resume,
    _extract_domain_from_resume,
    _extract_email_from_resume,
    _extract_phone_from_resume
)


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

    def test_rag_chunking_and_embedding_autofill(self):
        sample_resume = """
        Gowtham Kumar
        Email: gowtham.kumar@example.com
        Phone: +91 9876543210
        Date of Birth: 2004-05-15
        GitHub: https://github.com/mgowthamkumar
        LinkedIn: https://www.linkedin.com/in/gowtham-kumar
        
        Summary:
        Motivated Computer Science student specializing in Artificial Intelligence, Deep Learning,
        and PyTorch. Built scalable RAG systems with LangChain and FAISS.
        
        Projects:
        - AutoHire AI: Generative AI Career Launchpad using Transformers and FastAPI.
        """

        result = parse_and_embed_resume(sample_resume, "gowtham_resume.pdf")

        self.assertTrue(result["success"])
        self.assertGreater(result["telemetry"]["chunks_count"], 0)
        self.assertEqual(result["data"]["fullName"], "Gowtham Kumar")
        self.assertEqual(result["data"]["emailAddress"], "gowtham.kumar@example.com")
        self.assertEqual(result["data"]["githubProfile"], "https://github.com/mgowthamkumar")
        self.assertEqual(result["data"]["linkedinProfile"], "https://www.linkedin.com/in/gowtham-kumar")
        self.assertEqual(result["data"]["preferredDomain"], "ai")

    def test_rag_handles_and_career_preferences(self):
        sample = """
        Alex Rivera
        Software Engineer
        alex.rivera@dev.io | (555) 234-5678
        GitHub: @torvalds
        LinkedIn: in/williamhgates
        Experience: 4 years of experience building modern web development React and Node.js microservices.
        """
        result = parse_and_embed_resume(sample, "alex_rivera_cv.txt")
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["fullName"], "Alex Rivera")
        self.assertEqual(result["data"]["emailAddress"], "alex.rivera@dev.io")
        self.assertEqual(result["data"]["githubProfile"], "https://github.com/torvalds")
        self.assertEqual(result["data"]["linkedinProfile"], "https://www.linkedin.com/in/williamhgates")
        self.assertEqual(result["data"]["preferredDomain"], "web_dev")
        self.assertEqual(result["data"]["experienceLevel"], "intermediate")
        self.assertEqual(result["data"]["userType"], "professional")

    def test_gowtham_profile_with_initial_and_no_password(self):
        sample = """
        GOWTHAM KUMAR M
        mgowthamkumar472008@gmail.com
        Mobile: 260 1103 740
        Date of Birth: 2008-07-04
        GitHub: https://github.com/mgowthamkumar
        LinkedIn: https://linkedin.com/in/mgowthamkumar

        Objective:
        Passionate AI & Machine Learning student building Generative AI, RAG architectures and Python applications.
        """
        result = parse_and_embed_resume(sample, "gowtham_profile.pdf")
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["fullName"], "Gowtham Kumar M")
        self.assertEqual(result["data"]["emailAddress"], "mgowthamkumar472008@gmail.com")
        self.assertEqual(result["data"]["mobileNumber"], "260 1103 740")
        self.assertEqual(result["data"]["dob"], "2008-07-04")
        self.assertEqual(result["data"]["githubProfile"], "https://github.com/mgowthamkumar")
        self.assertEqual(result["data"]["linkedinProfile"], "https://www.linkedin.com/in/mgowthamkumar")
        self.assertEqual(result["data"]["preferredDomain"], "ai")
        # Ensure password is NOT autofilled
        self.assertNotIn("password", result["data"])
        self.assertNotIn("confirmPassword", result["data"])


if __name__ == "__main__":
    unittest.main()
