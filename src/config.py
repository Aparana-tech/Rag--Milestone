import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Chunking Configuration
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Retrieval Configuration
TOP_K_RETRIEVAL = 20

# Model Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # HuggingFace local embedding model
LLM_MODEL = "llama-3.3-70b-versatile"  # Groq LLM model

# Database Configuration
CHROMA_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
