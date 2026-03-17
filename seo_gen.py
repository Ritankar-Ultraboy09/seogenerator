import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_API_KEY = os.getenv("GROK_API_KEY")
HTTP_REFERER = os.getenv("HTTP_REFERER", "https://github.com/yourusername/seo-workflow")
X_TITLE = os.getenv("X_TITLE", "Real Estate SEO Generator")

from pathlib import Path

GENERATION_MODEL = "openai/gpt-oss-120b"
VERIFICATION_MODEL = "moonshotai/kimi-k2-instruct-0905"

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}. Create it in {PROMPTS_DIR}.")
    return path.read_text(encoding="utf-8")

GENERATION_PROMPT_TEMPLATE = load_prompt("generation_prompt.txt")
VERIFICATION_PROMPT_TEMPLATE = load_prompt("verification_prompt.txt")

def call_openrouter(model, prompt, temperature=0.7, max_tokens=4000):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        data=json.dumps(data)
    )
    
    if response.status_code != 200:
        raise Exception(f"Error from OpenRouter: {response.status_code} - {response.text}")
        
    result = response.json()
    return result['choices'][0]['message']['content']

def generate_seo_content(project_name):
    print(f"Generating content for project: {project_name}...")
    prompt = GENERATION_PROMPT_TEMPLATE.replace("{project_name}", project_name)
    content = call_openrouter(GENERATION_MODEL, prompt)
    return content

def verify_content(content):
    print("Verifying content structure...")
    prompt = VERIFICATION_PROMPT_TEMPLATE.replace("{content}", content)
    
    verification_text = call_openrouter(VERIFICATION_MODEL, prompt, temperature=0.1, max_tokens=1000)
    print("Verification model response preview:", verification_text[:300])
    
    try:
        parsed = None
        
        import re
        json_match = re.search(r'\{[^\{]*\}', verification_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(verification_text)

        if not isinstance(parsed, dict):
            raise ValueError("Parsed verification output is not a JSON object")
        
        return {
            "verification_passed": parsed.get("verification_passed", False),
            "errors": parsed.get("errors", []),
            "missing_sections": parsed.get("missing_sections", []),
            "warnings": parsed.get("warnings", [])
        }
    except Exception as e:
        print(f"Failed to parse verification response: {e}")
        print(f"Raw response: {verification_text}")
        return {
            "verification_passed": False,
            "errors": [f"Failed to parse verification response: {str(e)}"],
            "missing_sections": [],
            "warnings": []
        }

def save_content(project_name, content, verification_result):
    if not os.path.exists("output"):
        os.makedirs("output")
        
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    clean_name = "".join([c if c.isalnum() else "_" for c in project_name]).lower()
    filename = f"output/{clean_name}_{timestamp}.txt"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"PROJECT: {project_name}\n")
        f.write(f"TIMESTAMP: {timestamp}\n")
        f.write("-" * 50 + "\n")
        f.write("VERIFICATION RESULT:\n")
        f.write(json.dumps(verification_result, indent=2) + "\n")
        f.write("-" * 50 + "\n\n")
        f.write(content)
        
    print(f"Content saved to {filename}")
    return filename

def main():
    project_name = input("Enter the Project Name (e.g., Prestige Alcazar): ")
    if not project_name:
        print("Project name cannot be empty.")
        return
        
    try:
        content = generate_seo_content(project_name)
        verification_result = verify_content(content)
        
        if verification_result.get("verification_passed"):
            print("Verification passed!")
        else:
            print("⚠️ Verification failed with errors:")
            for err in verification_result.get("errors", []):
                print(f"  - {err}")
            for missing in verification_result.get("missing_sections", []):
                print(f"  - Missing: {missing}")
        
        save_content(project_name, content, verification_result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
