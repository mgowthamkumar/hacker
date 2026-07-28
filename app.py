import os
import uvicorn
from typing import Optional
from fastapi import FastAPI, Form, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from resume_profile_utils import resolve_profile_identity

# LangChain & Vector Store Imports
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

app = FastAPI(title="RAG Candidate Management System")

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# STEP 1: Global Storage & Embedding Model Initialization
# ---------------------------------------------------------
print("Loading HuggingFace Embeddings Model (all-MiniLM-L6-v2)...")
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initial seed data for the RAG Knowledge Base
initial_profiles = [
    "Candidate System Initialized. System supports profile retrieval for jobs, internships, and hackathons."
]

text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
initial_docs = text_splitter.create_documents(initial_profiles)

# Initialize FAISS Vector Database
print("Initializing FAISS Vector Store...")
vector_db = FAISS.from_documents(initial_docs, embedding_model)


# ---------------------------------------------------------
# STEP 2: Data Models
# ---------------------------------------------------------
class RAGQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3


# ---------------------------------------------------------
# STEP 3: API Endpoint - Submit & Index Registration Data
# ---------------------------------------------------------
@app.post("/submit-registration")
async def submit_registration(
    fullName: str = Form(...),
    emailAddress: str = Form(...),
    mobileNumber: str = Form(...),
    userType: str = Form(...),
    dob: str = Form(...),
    preferredDomain: str = Form("Not Specified"),
    experienceLevel: str = Form("Not Specified"),
    githubProfile: str = Form("Not Provided"),
    linkedinProfile: str = Form("Not Provided"),
    resumeFile: Optional[UploadFile] = File(None)
):
    try:
        # 1. Read file info if provided
        resume_info = "No resume uploaded."
        detected_name = ""
        detected_dob = ""
        resume_text = ""

        if resumeFile:
            resume_info = f"Uploaded resume file named '{resumeFile.filename}'"
            contents = await resumeFile.read()
            resume_text = contents.decode("utf-8", errors="ignore")

        resolved_full_name, resolved_dob = resolve_profile_identity(resume_text, fullName, dob)
        detected_name = resolved_full_name
        detected_dob = resolved_dob

        # 2. Format user profile into structured text for vector embedding
        profile_text = (
            f"REGISTERED USER PROFILE:\n"
            f"Full Name: {resolved_full_name}\n"
            f"Email Address: {emailAddress}\n"
            f"Mobile Number: {mobileNumber}\n"
            f"User Type/Role: {userType}\n"
            f"Date of Birth: {resolved_dob}\n"
            f"Preferred Domain: {preferredDomain}\n"
            f"Experience Level: {experienceLevel}\n"
            f"GitHub Profile: {githubProfile}\n"
            f"LinkedIn Profile: {linkedinProfile}\n"
            f"Resume Status: {resume_info}\n"
        )

        # 3. Create document and split into vector chunks
        doc = Document(
            page_content=profile_text,
            metadata={
                "email": emailAddress,
                "name": fullName,
                "role": userType,
                "domain": preferredDomain
            }
        )
        
        chunks = text_splitter.split_documents([doc])

        # 4. Ingest and Index into FAISS Vector Database (RAG Memory)
        vector_db.add_documents(chunks)
        print(f"[RAG INDEXED] Added profile for: {fullName} ({emailAddress})")

        return {
            "status": "success",
            "message": f"Account for {resolved_full_name} created and indexed into RAG memory successfully!",
            "user": {
                "fullName": resolved_full_name,
                "emailAddress": emailAddress,
                "userType": userType,
                "preferredDomain": preferredDomain,
                "experienceLevel": experienceLevel,
                "dob": resolved_dob
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process registration: {str(e)}")


# ---------------------------------------------------------
# STEP 4: API Endpoint - RAG Retrieval & Prompt Augmentation
# ---------------------------------------------------------
@app.post("/api/rag/query")
async def query_rag_system(request: RAGQueryRequest):
    """
    Retrieves matching registered candidate profiles from FAISS based on semantic query.
    """
    try:
        # Search vector DB for top-k similar matches
        search_results = vector_db.similarity_search(request.query, k=request.top_k)
        
        retrieved_contexts = [doc.page_content for doc in search_results]
        context_block = "\n---\n".join(retrieved_contexts)

        # Build augmented prompt (Ready to send to LLM such as OpenAI / HuggingFace / Llama)
        augmented_prompt = (
            f"System Prompt: You are an AI Career Assistant. Use the following candidate database "
            f"context to answer the user request accurately.\n\n"
            f"--- RETRIEVED CANDIDATE CONTEXT ---\n"
            f"{context_block}\n\n"
            f"--- USER QUESTION ---\n"
            f"{request.query}\n\n"
            f"--- RESPONSE ---"
        )

        return {
            "query": request.query,
            "match_count": len(retrieved_contexts),
            "retrieved_context": retrieved_contexts,
            "augmented_prompt": augmented_prompt
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


# ---------------------------------------------------------
# STEP 5: Execution Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000,root_path="/", reload=True)