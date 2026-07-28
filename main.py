from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

app = FastAPI()

# Enable CORS so HTML can query the local Python backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Knowledge Base
raw_documents = [
    "User Alice joined in 2023. Her email is alice@example.com and she is an Admin.",
    "User Bob joined in 2024. His email is bob@example.com and he is a Standard User.",
    "The system logout policy requires clearing local storage and invalidating session tokens.",
    "Profile pictures must be uploaded in PNG or JPEG format under 2MB."
]

# 2. Vector Store Setup
text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
docs = text_splitter.create_documents(raw_documents)
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = FAISS.from_documents(docs, embedding_model)

class ChatRequest(BaseModel):
    query: str
    user_email: str

@app.post("/api/chat")
async def rag_chat(request: ChatRequest):
    # Retrieve relevant context from FAISS
    results = vector_db.similarity_search(request.query, k=2)
    retrieved_chunks = [doc.page_content for doc in results]
    
    # Construct context string
    context_str = "\n".join(retrieved_chunks)
    
    # Return formatted context (Ready to display or pass to an LLM)
    return {
        "user": request.user_email,
        "query": request.query,
        "retrieved_context": retrieved_chunks,
        "answer": f"Based on knowledge base:\n{context_str}"
    }