import os
import re
import json
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import config

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Minimum character threshold for quality validation
MIN_TEXT_LENGTH = 500

# The 15 specific URLs for our corpus
FUND_URLS = [
    "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-nifty-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-short-term-opportunities-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-bse-sensex-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-nifty-next-50-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-large-and-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-liquid-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-infrastructure-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-nifty-top-20-equal-weight-index-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-ultra-short-term-fund-direct-growth"
]


def extract_structured_data(soup):
    """
    Extracts structured fund data from the __NEXT_DATA__ JSON embedded
    in the Groww page HTML. This contains all key fund details.
    Returns a dict of structured fund information or None on failure.
    """
    next_data_script = soup.find('script', id='__NEXT_DATA__')
    if not next_data_script or not next_data_script.string:
        return None

    try:
        full_data = json.loads(next_data_script.string)
        mf_data = full_data.get('props', {}).get('pageProps', {}).get('mfServerSideData', {})
        if not mf_data:
            return None
        return mf_data
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"  -> Failed to parse __NEXT_DATA__: {e}")
        return None


def build_structured_json(mf_data, url):
    """
    Extracts the most relevant fields from the raw __NEXT_DATA__ JSON
    and returns a clean, structured JSON dict for the fund.
    """

    # Extract fund manager details
    fund_managers = []
    for fm in mf_data.get('fund_manager_details', []):
        fund_managers.append({
            "name": fm.get('person_name', 'N/A'),
            "education": fm.get('education', 'N/A'),
            "experience": fm.get('experience', 'N/A'),
            "managing_since": fm.get('date_from', 'N/A')
        })

    # Extract top holdings
    holdings = []
    for h in mf_data.get('holdings', [])[:10]:
        holdings.append({
            "name": h.get('company_name', 'N/A'),
            "sector": h.get('sector_name', 'N/A'),
            "percentage": h.get('corpus_per', 0)
        })

    # Extract lock-in info
    lock_in = mf_data.get('lock_in', {})
    lock_in_str = "None"
    if lock_in:
        years = lock_in.get('years', 0)
        months = lock_in.get('months', 0)
        days = lock_in.get('days', 0)
        if years or months or days:
            parts = []
            if years: parts.append(f"{years} year(s)")
            if months: parts.append(f"{months} month(s)")
            if days: parts.append(f"{days} day(s)")
            lock_in_str = ", ".join(parts)

    # Extract AMC info
    amc_info = mf_data.get('amc_info', {})

    # Extract RTA details
    rta = mf_data.get('rta_details', {})

    structured = {
        "fund_name": mf_data.get('scheme_name', 'N/A'),
        "fund_house": mf_data.get('fund_house', 'N/A'),
        "category": mf_data.get('category', 'N/A'),
        "sub_category": mf_data.get('sub_category', 'N/A'),
        "plan_type": mf_data.get('plan_type', 'N/A'),
        "scheme_type": mf_data.get('scheme_type', 'N/A'),
        "risk_level": mf_data.get('nfo_risk', 'N/A'),
        "nav": {
            "value": mf_data.get('nav', 'N/A'),
            "date": mf_data.get('nav_date', 'N/A')
        },
        "aum_crore": mf_data.get('aum', 'N/A'),
        "expense_ratio": mf_data.get('expense_ratio', 'N/A'),
        "exit_load": mf_data.get('exit_load', 'N/A'),
        "benchmark": mf_data.get('benchmark_name', 'N/A'),
        "min_sip_investment": mf_data.get('min_sip_investment', 'N/A'),
        "max_sip_investment": mf_data.get('max_sip_investment', 'N/A'),
        "min_lumpsum_investment": mf_data.get('min_investment_amount', 'N/A'),
        "sip_allowed": mf_data.get('sip_allowed', 'N/A'),
        "lumpsum_allowed": mf_data.get('lumpsum_allowed', 'N/A'),
        "lock_in": lock_in_str,
        "stamp_duty": mf_data.get('stamp_duty', 'N/A'),
        "launch_date": mf_data.get('launch_date', 'N/A'),
        "isin": mf_data.get('isin', 'N/A'),
        "description": mf_data.get('description', 'N/A'),
        "fund_managers": fund_managers,
        "top_holdings": holdings,
        "amc_info": {
            "name": amc_info.get('name', 'N/A'),
            "address": amc_info.get('address', 'N/A'),
            "phone": amc_info.get('phone', 'N/A'),
            "email": amc_info.get('email', 'N/A'),
            "total_aum": amc_info.get('aum', 'N/A'),
            "rank": amc_info.get('rank', 'N/A')
        },
        "rta_details": {
            "name": rta.get('rta_name', 'N/A'),
            "email": rta.get('email', 'N/A'),
            "website": rta.get('website', 'N/A')
        },
        "source_url": url,
        "scraped_date": datetime.now().strftime("%Y-%m-%d")
    }
    return structured


def build_readable_text(structured):
    """
    Converts the structured JSON into a clean, readable plain text
    document suitable for chunking and RAG retrieval.
    """
    lines = []
    lines.append(f"Fund Name: {structured['fund_name']}")
    lines.append(f"Fund House: {structured['fund_house']}")
    lines.append(f"Category: {structured['category']} - {structured['sub_category']}")
    lines.append(f"Plan Type: {structured['plan_type']} | Scheme Type: {structured['scheme_type']}")
    lines.append(f"Risk Level: {structured['risk_level']}")
    lines.append(f"ISIN: {structured['isin']}")
    lines.append(f"Launch Date: {structured['launch_date']}")
    lines.append("")

    lines.append(f"Description: {structured['description']}")
    lines.append("")

    nav = structured['nav']
    lines.append(f"NAV: ₹{nav['value']} (as of {nav['date']})")
    lines.append(f"AUM: ₹{structured['aum_crore']} Crore")
    lines.append(f"Expense Ratio: {structured['expense_ratio']}%")
    lines.append(f"Exit Load: {structured['exit_load']}")
    lines.append(f"Benchmark: {structured['benchmark']}")
    lines.append(f"Lock-in Period: {structured['lock_in']}")
    lines.append(f"Stamp Duty: {structured['stamp_duty']}")
    lines.append("")

    lines.append(f"Minimum SIP Investment: ₹{structured['min_sip_investment']}")
    lines.append(f"Maximum SIP Investment: ₹{structured['max_sip_investment']}")
    lines.append(f"Minimum Lumpsum Investment: ₹{structured['min_lumpsum_investment']}")
    lines.append(f"SIP Allowed: {structured['sip_allowed']}")
    lines.append(f"Lumpsum Allowed: {structured['lumpsum_allowed']}")
    lines.append("")

    # Fund managers
    lines.append("Fund Managers:")
    for fm in structured.get('fund_managers', []):
        lines.append(f"  - {fm['name']} (Education: {fm['education']}, Since: {fm['managing_since']})")
    lines.append("")

    # Top holdings
    lines.append("Top Holdings:")
    for h in structured.get('top_holdings', []):
        lines.append(f"  - {h['name']} | Sector: {h['sector']} | Weight: {h['percentage']}%")
    lines.append("")

    # AMC info
    amc = structured['amc_info']
    lines.append(f"AMC: {amc['name']}")
    lines.append(f"AMC Rank: #{amc['rank']} in India")
    lines.append(f"AMC Phone: {amc['phone']}")
    lines.append(f"AMC Email: {amc['email']}")
    lines.append("")

    # RTA details
    rta = structured['rta_details']
    lines.append(f"Registrar & Transfer Agent: {rta['name']}")
    lines.append(f"RTA Email: {rta['email']}")
    lines.append(f"RTA Website: {rta['website']}")

    return "\n".join(lines)


def save_outputs(fund_slug, structured_json, readable_text):
    """
    Save both the structured JSON and the cleaned readable text
    to the data/ directory.
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Save JSON
    json_path = os.path.join(data_dir, f"{fund_slug}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(structured_json, f, indent=2, ensure_ascii=False)
    logger.info(f"  -> Saved JSON: {json_path}")

    # Save readable text
    txt_path = os.path.join(data_dir, f"{fund_slug}.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(readable_text)
    logger.info(f"  -> Saved TXT:  {txt_path}")


def scrape_and_chunk():
    """
    Full ETL Pipeline:
      Step 1: Scrape the URLs and extract structured JSON from __NEXT_DATA__
      Step 2: Data Cleaning - Build structured JSON and readable text
      Step 3: Text Chunking (RecursiveCharacterTextSplitter)
      Step 4: Metadata Enrichment
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                       '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    all_chunks = []

    # Step 3: Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""]
    )

    current_date = datetime.now().strftime("%Y-%m-%d")

    for url in FUND_URLS:
        logger.info(f"Scraping URL: {url}")
        try:
            # Step 1: Fetch raw HTML
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                logger.warning(f"  -> Failed to fetch. Status code: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Step 1 (cont): Extract structured data from __NEXT_DATA__
            mf_data = extract_structured_data(soup)
            if not mf_data:
                logger.warning(f"  -> No structured data found in __NEXT_DATA__. Skipping.")
                continue

            # Step 2: Build structured JSON and readable text
            fund_slug = url.split('/')[-1].replace('-', '_')
            fund_name = mf_data.get('scheme_name', url.split('/')[-1].replace('-', ' ').title())

            structured_json = build_structured_json(mf_data, url)
            readable_text = build_readable_text(structured_json)

            # Step 2 (validation): Quality check
            if len(readable_text) < MIN_TEXT_LENGTH:
                logger.warning(
                    f"  -> SKIPPED: Only {len(readable_text)} chars extracted "
                    f"(minimum {MIN_TEXT_LENGTH}). Content may be corrupted."
                )
                continue

            # Save both JSON and TXT outputs
            save_outputs(fund_slug, structured_json, readable_text)

            # Step 4: Metadata Enrichment
            doc = Document(
                page_content=readable_text,
                metadata={
                    "source_url": url,
                    "fund_name": fund_name,
                    "last_updated": current_date
                }
            )

            # Step 3: Text Chunking
            chunks = text_splitter.split_documents([doc])
            
            # Context Injection: prepend fund name to prevent orphaned data
            for chunk in chunks:
                if not chunk.page_content.startswith(f"Fund Name: {fund_name}"):
                    chunk.page_content = f"Fund Name: {fund_name}\n\n" + chunk.page_content
            
            logger.info(f"  -> Cleaned: {len(readable_text)} chars. Chunks: {len(chunks)}")
            all_chunks.extend(chunks)

        except Exception as e:
            logger.error(f"  -> Error processing {url}: {str(e)}")

    logger.info(f"\nTotal chunks created across all funds: {len(all_chunks)}")
    return all_chunks


def embed_and_store(chunks):
    """
    Step 5: Vector Embedding & Storage
    Uses HuggingFace all-MiniLM-L6-v2 (local, no API key required)
    and stores embeddings in ChromaDB.
    """
    if not chunks:
        logger.warning("No chunks to store.")
        return

    logger.info(f"\nInitializing Embedding Model ({config.EMBEDDING_MODEL})...")
    embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

    # Clear existing DB contents to avoid duplicates, but DO NOT delete the mount point directory itself
    if os.path.exists(config.CHROMA_DB_DIR):
        import shutil
        for filename in os.listdir(config.CHROMA_DB_DIR):
            file_path = os.path.join(config.CHROMA_DB_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f'Failed to delete {file_path}. Reason: {e}')
        logger.info(f"  -> Cleared existing ChromaDB contents at {config.CHROMA_DB_DIR}")

    logger.info(f"Storing {len(chunks)} chunks into ChromaDB at {config.CHROMA_DB_DIR}...")
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=config.CHROMA_DB_DIR
    )

    if hasattr(db, 'persist'):
        db.persist()
    logger.info("Storage complete! Vector DB is ready.")


if __name__ == "__main__":
    chunks = scrape_and_chunk()
    if chunks:
        logger.info("\n--- Sample Chunk ---")
        logger.info(f"Metadata: {chunks[0].metadata}")
        logger.info(f"Content:\n{chunks[0].page_content[:500]}...")
        logger.info("---")
        embed_and_store(chunks)
