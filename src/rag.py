import os
import logging
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import config
from guardrails import process_guardrails

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Initialize Embeddings
logger.info("Initializing embeddings model...")
embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

# Initialize ChromaDB Vector Store
logger.info(f"Connecting to ChromaDB at {config.CHROMA_DB_DIR}...")
vectorstore = Chroma(persist_directory=config.CHROMA_DB_DIR, embedding_function=embeddings)

# Initialize Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": config.TOP_K_RETRIEVAL})

# Initialize LLM
llm = ChatGroq(
    model=config.LLM_MODEL,
    api_key=config.GROQ_API_KEY,
    temperature=0.0
)

# Phase 4, Step 2: Strict RAG Prompt Template
RAG_PROMPT_TEMPLATE = """You are a facts-only mutual fund assistant.
Use ONLY the provided context to answer. If the answer is not in the context, reply 'I do not have information on this'.
Your response MUST NOT exceed 3 sentences.

Context:
{context}

Question:
{question}

Answer:"""

prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def query_assistant(question: str) -> dict:
    """
    Phase 4 Pipeline:
    1. Check Intent Guardrails (Phase 3)
    2. Semantic Retrieval from ChromaDB
    3. Generate constrained LLM response
    """
    logger.info(f"Processing query: '{question}'")
    
    # 1. Guardrails check
    guardrail_result = process_guardrails(question)
    if not guardrail_result["passed"]:
        logger.info(f"Guardrail blocked query. Intent: {guardrail_result['intent']}")
        return {
            "answer": guardrail_result["response"],
            "intent": guardrail_result["intent"],
            "sources": []
        }
    
    # 2. Retrieve source documents
    docs = retriever.invoke(question)
    context_str = format_docs(docs)
    
    # 3. Generate response
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context_str, "question": question})
    
    # Extract unique source URLs and the latest updated date
    sources = []
    last_updated = None
    for doc in docs:
        if "source_url" in doc.metadata and doc.metadata["source_url"] not in sources:
            sources.append(doc.metadata["source_url"])
        if "last_updated" in doc.metadata:
            # Keep the most recent date if multiple chunks exist
            date_str = doc.metadata["last_updated"]
            if last_updated is None or date_str > last_updated:
                last_updated = date_str
                
    # Limit the displayed sources to a maximum of 5, so the UI isn't cluttered
    sources = sources[:5]

    # Phase 5: Output Validation & Formatting (Max 3 sentences)
    import re
    # Simple regex to split by sentence endings (.?!) followed by space
    sentences = re.split(r'(?<=[.!?]) +', answer.strip())
    if len(sentences) > 3:
        logger.warning(f"Response exceeded 3 sentences ({len(sentences)}). Truncating.")
        answer = " ".join(sentences[:3])
                
    return {
        "answer": answer,
        "intent": guardrail_result["intent"],
        "sources": sources,
        "last_updated": last_updated
    }
