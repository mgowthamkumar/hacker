import json
import unittest
from fastapi.testclient import TestClient
from backendreal import app

class BackendRealFlowTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_parse_autofill_endpoint(self):
        sample_resume = """
        GOWTHAM KUMAR M
        mgowthamkumar472008@gmail.com
        Mobile: 260 1103 740
        Date of Birth: 2008-07-04
        GitHub: https://github.com/mgowthamkumar
        LinkedIn: https://linkedin.com/in/mgowthamkumar

        Career Objective:
        Engineering student specializing in Artificial Intelligence, RAG vector search, and deep learning.
        Proficient in Python, LangChain, PyTorch, and FastAPI.
        """
        response = self.client.post("/api/resume/parse-autofill", data={"resume_text": sample_resume})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("chunks", data)
        self.assertGreater(len(data["chunks"]), 0)
        self.assertEqual(data["telemetry"]["vector_dimension"], 384)
        
        # Verify extracted attributes
        extracted = data["data"]
        self.assertEqual(extracted["fullName"], "Gowtham Kumar M")
        self.assertEqual(extracted["emailAddress"], "mgowthamkumar472008@gmail.com")
        self.assertEqual(extracted["mobileNumber"], "260 1103 740")
        self.assertEqual(extracted["dob"], "2008-07-04")
        self.assertEqual(extracted["githubProfile"], "https://github.com/mgowthamkumar")
        self.assertEqual(extracted["linkedinProfile"], "https://www.linkedin.com/in/mgowthamkumar")
        self.assertEqual(extracted["preferredDomain"], "ai")
        # Ensure password is NOT present
        self.assertNotIn("password", extracted)
        self.assertNotIn("confirmPassword", extracted)

    def test_register_and_authenticate_permanent_password(self):
        test_email = "gowtham.test.profile@example.com"
        reg_payload = {
            "fullName": "Gowtham Kumar M",
            "emailAddress": test_email,
            "mobileNumber": "260 1103 740",
            "password": "PermanentSecretPass123!",
            "dob": "2008-07-04",
            "userType": "student",
            "experienceLevel": "fresher",
            "preferredDomain": "ai",
            "githubProfile": "https://github.com/mgowthamkumar",
            "githubUsername": "mgowthamkumar",
            "linkedinProfile": "https://linkedin.com/in/mgowthamkumar",
            "linkedinUsername": "mgowthamkumar"
        }

        # 1. Register candidate profile
        reg_res = self.client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(reg_res.status_code, 200)
        self.assertTrue(reg_res.json()["success"])

        # 2. Check profile chooser list
        profiles_res = self.client.get("/api/auth/profiles")
        self.assertEqual(profiles_res.status_code, 200)
        profiles = profiles_res.json()["profiles"]
        found = next((p for p in profiles if p["email"].lower() == test_email.lower()), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Gowtham Kumar M")

        # 3. Test wrong password login
        wrong_res = self.client.post("/api/auth/login", json={"email": test_email, "password": "WrongPassword"})
        self.assertEqual(wrong_res.status_code, 401)

        # 4. Test correct permanent password login
        correct_res = self.client.post("/api/auth/login", json={"email": test_email, "password": "PermanentSecretPass123!"})
        self.assertEqual(correct_res.status_code, 200)
        user = correct_res.json()["user"]
        self.assertEqual(user["name"], "Gowtham Kumar M")
        self.assertEqual(user["email"], test_email)

if __name__ == "__main__":
    unittest.main()
