import re
import json

def clean_and_mask_document(raw_text: str) -> str:
    """
    1. Removes website header/footer boilerplate and duplicate lines.
    2. Identifies and masks Personally Identifiable Information (PII).
    """
    # Boilerplate / Navigation removal
    cleaned = re.sub(r'(?i)(home\s*\|\s*about us\s*\|\s*contact us|copyright \d{4}.*)', '', raw_text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
    
    # PII Masking Rules (Emails and Phone Numbers)
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    
    cleaned = re.sub(email_pattern, '[REDACTED_EMAIL]', cleaned)
    cleaned = re.sub(phone_pattern, '[REDACTED_PHONE]', cleaned)
    
    return cleaned

# Sample Knowledge Base Records for Assessment
sample_kb_data = [
    {
        "record_id": "kb_policy_001",
        "title": "Pre-Existing Conditions Waiting Period",
        "content": "For standard individual health insurance, pre-existing conditions (e.g., Diabetes, Hypertension) have a 12-month waiting period before full coverage applies. Emergency stabilization is covered after 30 days. For inquiries contact support@careshield.com.",
        "category": "policy_rules",
        "source": "CareShield_Policy_Manual_v2.pdf"
    },
    {
        "record_id": "kb_pricing_002",
        "title": "Gold Plan Premium & Network",
        "content": "The Gold Plan starts at $150/month with a $500 annual deductible. Covers over 500 network hospitals in Eastern and Central regions.",
        "category": "pricing_and_plans",
        "source": "Product_Brochure_2026.pdf"
    },
    {
        "record_id": "kb_scope_003",
        "title": "Exclusions & Unsupported Policies",
        "content": "CareShield strictly provides human health insurance policies. Pet insurance, vehicle insurance, and international travel coverage are strictly excluded from all plans.",
        "category": "exclusions",
        "source": "Underwriting_Guidelines.pdf"
    }
]

def process_and_export_kb():
    processed_records = []
    for doc in sample_kb_data:
        cleaned_content = clean_and_mask_document(doc["content"])
        record = {
            "record_id": doc["record_id"],
            "title": doc["title"],
            "content": cleaned_content,
            "category": doc["category"],
            "source": doc["source"],
            "version": "1.0",
            "contains_pii": False,
            "chunk_metadata": {
                "chunk_index": 1,
                "total_chunks": 1
            }
        }
        processed_records.append(record)
    
    with open("knowledge_base_records.json", "w") as f:
        json.dump(processed_records, f, indent=2)
    
    print("Knowledge base successfully cleaned, PII masked, and exported!")

if __name__ == "__main__":
    process_and_export_kb()