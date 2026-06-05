import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag import query_assistant

def test_rag_pipeline():
    queries = [
        "What is the NAV of HDFC Defence Fund?",
        "Who is the fund manager for HDFC Balanced Advantage Fund?",
        "Is HDFC Gold ETF a good investment right now?", # Should be blocked
        "What are the top 3 holdings of HDFC Liquid Fund?"
    ]
    
    for q in queries:
        print("\n" + "="*50)
        print(f"Question: {q}")
        res = query_assistant(q)
        print(f"Intent: {res['intent']}")
        print(f"Answer: {res['answer']}")
        if res['sources']:
            print(f"Sources: {', '.join(res['sources'])}")
        if res.get('last_updated'):
            print(f"Last Updated: {res['last_updated']}")
        print("="*50)

if __name__ == "__main__":
    test_rag_pipeline()
