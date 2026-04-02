import argparse
import csv
import json
import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from scrapper import get_scraped_details

load_dotenv()

GROK_API_KEY = os.getenv("GROK_API_KEY")
HTTP_REFERER = os.getenv("HTTP_REFERER", "https://github.com/yourusername/seo-workflow")
X_TITLE = os.getenv("X_TITLE", "Real Estate SEO Generator")

GENERATION_MODEL = "anthropic/claude-sonnet-4"
VERIFICATION_MODEL = "openrouter/auto"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SCRAPE_CACHE_DIR = Path(__file__).resolve().parent / "scrape_cache"
SCRAPE_CACHE_PATH = SCRAPE_CACHE_DIR / "nobroker_scrape_cache.json"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}. Create it in {PROMPTS_DIR}.")
    return path.read_text(encoding="utf-8")


def load_scrape_cache():
    if not SCRAPE_CACHE_DIR.exists():
        SCRAPE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if SCRAPE_CACHE_PATH.exists():
        try:
            return json.loads(SCRAPE_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_scrape_cache(cache):
    if not SCRAPE_CACHE_DIR.exists():
        SCRAPE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SCRAPE_CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


GENERATION_PROMPT_TEMPLATE = load_prompt("generation_prompt.txt")
VERIFICATION_PROMPT_TEMPLATE = load_prompt("verification_prompt.txt")


def call_openrouter(model, prompt, temperature=0.7, max_tokens=4000):
    if not GROK_API_KEY:
        raise ValueError("GROK_API_KEY is not set in environment. Set it in .env.")

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "HTTP-Referer": HTTP_REFERER,
        "X-Title": X_TITLE,
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        data=json.dumps(data)
    )
    if response.status_code != 200:
        raise Exception(f"Error from Groq: {response.status_code} - {response.text}")
    result = response.json()
    return result["choices"][0]["message"]["content"]


def parse_csv(csv_path, max_rows=None):
    rows = []
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            if max_rows and idx > max_rows:
                break
            normalized = {k.strip(): (v.strip() if v else "") for k, v in row.items()}
            rows.append(normalized)
    return rows


def to_project_title(row):
    name = row.get("Name", "").strip()
    locality = row.get("Locaity", row.get("Locality", "")).strip()
    city = row.get("City", "").strip()
    return " ".join([part for part in [name, locality, city] if part])




def build_generation_prompt(row, scraped):
    project_name = to_project_title(row)
    url = row.get("No Broker URL", row.get("No Broker Url", row.get("URL", ""))).strip()
    search_volume = row.get("SV", row.get("Search Volume", "")).strip()
    locality = row.get("Locaity", row.get("Locality", "")).strip()
    city = row.get("City", "").strip()

    prompt = GENERATION_PROMPT_TEMPLATE.replace("{project_name}", project_name)
    extra = [
        "\n\n---\nSEO INPUT CONTEXT:",
        f"Primary keyword: {project_name}",
        f"Locality: {locality}",
        f"City: {city}",
        f"Search volume: {search_volume} (use as market demand weight to fine-tune CTA urgency).",
        f"Reference URL: {url}",
        "Use this URL as the reference, and verify facts from it. If not found, state 'To be confirmed with the developer.'",
    ]
    if scraped:
        extra.append("Scraped details:")
        extra.append(f"NoBroker RERA: {scraped.get('nobroker_rera', 'To be confirmed with the developer.')}")
        extra.append(f"Builder Project RERA: {scraped.get('builder_rera', 'To be confirmed with the developer.')}")
        extra.append(f"Configurations: {scraped.get('configurations', 'To be confirmed with the developer.')}")
        extra.append(f"Page summary excerpt: {scraped.get('summary', '')[:900]}")
        proj_specs = scraped.get('project_specs', {})
        if proj_specs:
            extra.append("Project specifications:")
            extra.append(f"Unit configuration: {', '.join(proj_specs.get('unit_configuration', []))}")
            extra.append(f"Number of towers: {proj_specs.get('number_of_towers', '')}")
            extra.append(f"Number of units: {proj_specs.get('number_of_units', '')}")
            extra.append(f"Project area: {proj_specs.get('project_area', '')}")
            extra.append(f"Water supply: {proj_specs.get('water_supply', '')}")
            extra.append(f"Parking: {proj_specs.get('parking', '')}")
        amenities = scraped.get('amenities', [])
        if amenities:
            extra.append(f"Amenities: {', '.join(amenities)}")
        rera_data = scraped.get('rera_data', {})
        if rera_data:
            extra.append("RERA data:")
            extra.append(f"RERA registered: {rera_data.get('rera_registered', False)}")
            extra.append(f"NoBroker RERA ID: {rera_data.get('nobroker_rera_id', '')}")
            extra.append(f"Builder project RERA ID: {rera_data.get('builder_project_rera_id', '')}")
            extra.append(f"RERA state: {rera_data.get('rera_state', '')}")
            extra.append(f"RERA certificate available: {rera_data.get('rera_certificate_available', False)}")
            benefits = rera_data.get('rera_benefits', [])
            if benefits:
                extra.append(f"RERA benefits: {', '.join(benefits)}")

    return prompt + "\n" + "\n".join(extra)


def generate_seo_content(row, cache):
    project_name = to_project_title(row)
    print(f"\nGenerating content for: {project_name}")
    url = row.get("No Broker URL", row.get("No Broker Url", row.get("URL", ""))).strip()
    scraped = get_scraped_details(url, cache) if url else {"nobroker_rera": "", "builder_rera": "", "configurations": "", "summary": "", "project_specs": {}, "amenities": [], "rera_data": {}}
    prompt = build_generation_prompt(row, scraped)
    return call_openrouter(GENERATION_MODEL, prompt)


def verify_content(content):
    print("Verifying content structure...")
    prompt = VERIFICATION_PROMPT_TEMPLATE.replace("{content}", content)
    verification_text = call_openrouter(VERIFICATION_MODEL, prompt, temperature=0.1, max_tokens=1000)
    print("Verification model response preview:", verification_text[:300])
    try:
        json_match = re.search(r"\{[\s\S]*\}", verification_text)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(verification_text)

        if not isinstance(parsed, dict):
            raise ValueError("Parsed output is not JSON object")

        return {
            "verification_passed": parsed.get("verification_passed", False),
            "errors": parsed.get("errors", []),
            "missing_sections": parsed.get("missing_sections", []),
            "warnings": parsed.get("warnings", [])
        }
    except Exception as e:
        print(f"Failed to parse verification response: {e}")
        print("Raw verification output:", verification_text)
        return {
            "verification_passed": False,
            "errors": [f"Failed to parse verification response: {e}"],
            "missing_sections": [],
            "warnings": []
        }


def save_content(row, content, verification_result):
    if not os.path.exists("output"):
        os.makedirs("output")
    project_name = to_project_title(row)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_name = "".join([c if c.isalnum() else "_" for c in project_name])
    filename = f"output/{safe_name}_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"PROJECT: {project_name}\n")
        f.write(f"SOURCE URL: {row.get('No Broker URL', row.get('No Broker Url', ''))}\n")
        f.write(f"SEARCH VOLUME: {row.get('SV', row.get('Search Volume', ''))}\n")
        f.write(f"TIMESTAMP: {timestamp}\n")
        f.write("-" * 80 + "\n")
        f.write("VERIFICATION RESULT:\n")
        f.write(json.dumps(verification_result, indent=2) + "\n")
        f.write("-" * 80 + "\n\n")
        f.write(content)
    print(f"Saved output: {filename}")
    return filename


def run_for_rows(rows, cache):
    for idx, row in enumerate(rows, start=1):
        project_name = to_project_title(row)
        print(f"\n=== Processing row {idx}: {project_name} ===")
        try:
            content = generate_seo_content(row, cache)
            verification = verify_content(content)
            save_content(row, content, verification)
        except Exception as e:
            print(f"Failed row {idx} ({project_name}): {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate SEO content from CSV rows")
    parser.add_argument("--csv", default="seo_projs.csv", help="CSV file path (default seo_projs.csv)")
    parser.add_argument("--rows", type=int, default=None, help="Number of rows to process (default all)")
    parser.add_argument("--clear-scrape-cache", action="store_true", help="Clear scrape cache before running")
    args = parser.parse_args()
    if not os.path.exists(args.csv):
        print(f"CSV not found: {args.csv}")
        return
    if args.clear_scrape_cache and SCRAPE_CACHE_PATH.exists():
        SCRAPE_CACHE_PATH.unlink()
        print("Cleared scrape cache.")
    cache = load_scrape_cache()
    rows = parse_csv(args.csv, max_rows=args.rows)
    if not rows:
        print("No rows loaded from CSV.")
        return
    print(f"Loaded {len(rows)} rows from {args.csv}.")
    run_for_rows(rows, cache)
    save_scrape_cache(cache)


if __name__ == "__main__":
    main()
