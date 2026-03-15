import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HTTP_REFERER = os.getenv("HTTP_REFERER", "https://github.com/yourusername/seo-workflow")
X_TITLE = os.getenv("X_TITLE", "Real Estate SEO Generator")

GENERATION_MODEL = "llama-3.3-70b-versatile"
VERIFICATION_MODEL = "google/gemini-2.0-flash-lite-preview-02-05:free" 

GENERATION_PROMPT_TEMPLATE = """You are a senior SEO content strategist specializing in Indian real estate. Generate a complete SEO-optimized content page for the project name provided.

CRITICAL: Before writing, search and verify all facts — pricing, RERA, configurations, possession, distances, phases. Cross-check at least 2 sources. Never invent data. Unverifiable fields → write "To be confirmed with the developer."

## STRUCTURE — FOLLOW EXACTLY, IN ORDER, NO DEVIATIONS

**1. H1 TITLE**
`[Project Name] — [City] | [Configurations] | [Locality, Address] | Starting [Verified Price]`
Primary keyword must appear naturally. Include price only if verified.

**2. ABOUT [PROJECT NAME]**
3–4 prose paragraphs. No bullet points. Each paragraph must be 4–6 sentences. Total word count for this section: 200–280 words. Write like a knowledgeable friend who has visited — not a brochure. Cover: what the project is and where it sits, scale (land, towers, units) woven naturally into sentences, who it suits and why, design philosophy. Be honest. No unsubstantiated superlatives.

**3. PROJECT AT A GLANCE**
Two-column table. Verified rows only.

| Detail | Information |
|---|---|
| Developer | |
| Project Name | |
| Location | |
| Total Land Area | |
| Total Towers | |
| Floors Per Tower | |
| Total Units | |
| Configurations | |
| Unit Size Range | |
| Starting Price | |
| Open Space | |
| Clubhouses | |
| Total Amenities | |
| Project Status | |
| Possession Date | |
| RERA Number | |

**4. APARTMENT CONFIGURATIONS & SIZES**
Four-column table:

| Configuration | Size | Starting Price | Best Suited For |

One row per available configuration. After the table: 2–3 human paragraphs highlighting the standout configuration and why. Mention Vastu compliance, balcony, ventilation, natural light if verified.

**5. LOCATION — WHY [LOCALITY] MAKES SENSE**
Four bold-labelled paragraphs in this order:

**Getting to Work** — Metro name + verified distance, key IT parks + distances, major road access.
**Schools Nearby** — Minimum 3 verified schools with distances.
**Healthcare** — Minimum 3 verified hospitals/clinics with distances.
**Shopping & Daily Needs** — Minimum 2 malls/markets + nearest bus stop.

If known negatives exist (waterlogging, traffic, noise) — state them honestly. This is mandatory, not optional.

**6. AMENITIES**
Open with total amenity count and clubhouse details. Then five bold-labelled paragraphs — no bullet points:

**Fitness & Wellness | Recreation & Social | For Children | Green Spaces | Convenience & Infrastructure**

Call out genuinely distinctive features specifically. Explain why they matter to a real resident, not a brochure reader.

**7. CONSTRUCTION QUALITY & SPECIFICATIONS**
Two-column table, verified rows only:

| Element | Specification |
|---|---|
| Structure | |
| Living & Bedroom Flooring | |
| Bathroom & Kitchen Flooring | |
| Kitchen Counter | |
| Bathroom Fittings | |
| Electrical Wiring | |
| Windows | |
| Doors | |
| Lifts | |
| Power Backup | |
| Water Supply | |

One closing paragraph on the developer's quality track record.

**8. WHY THIS IS a GOOD INVESTMENT**
Four bold-labelled paragraphs:

**Metro / Infrastructure Connectivity | Developer Track Record | Rental Demand | Scale and Self-Sufficiency**

Close with one honest caveat paragraph on investment risk.

**9. PHASES — WHERE THINGS STAND**
*Skip entirely if single-phase project. If phase information cannot be confirmed through research, write exactly: "Phase details for [Project Name] are not publicly confirmed at the time of writing — contact the developer directly for launch and possession timelines." Do not invent phase details.*

For each confirmed phase write: name + launch year, current status, possession date, one sentence on what it means for a buyer today. Close with a "What This Means for You as a Buyer" paragraph.

**10. FREQUENTLY ASKED QUESTIONS**
*Research before writing. Do not invent questions.*

Search these sources before compiling:
Google PAA → Reddit → MagicBricks / 99acres / Housing.com Q&A → NoBroker / CommonFloor forums → Google Maps reviews

Rules:
- 6–10 questions maximum
- Every question must come from actual research across listed platforms
- Prioritise questions appearing across multiple sources
- Must include at least one concern, hesitation or negative real buyers are raising
- If fewer than 6 questions can be sourced from research, state explicitly: "Additional FAQs sourced from common buyer patterns in this project category" and flag which questions those are — do not silently fill gaps
- Let research dictate topics entirely — do not default to a fixed question list

Format: **Bold the question.** Answer in 2–5 plain sentences. No sub-bullets inside answers.

**11. GET IN TOUCH**
Two-sentence opener. Then:

**Call / WhatsApp:** | **Email:** | **Site Address:** | **Office Hours:**

**12. DISCLAIMER**
*Copy verbatim:*
*Disclaimer: All prices, possession dates and project details are based on publicly available information and subject to change. RERA numbers are verifiable on the relevant state RERA portal. Verify all details with the developer or an authorised channel partner before making any purchase decision.*

## GLOBAL SEO RULES

**No repetition across sections.** Each fact, figure or selling point appears in its most relevant section only. Reference briefly elsewhere if needed — never restate in full across multiple sections.

**Primary keyword** — In H1, About opening, at least one subheading, naturally throughout body, in every FAQ answer. No stuffing.

**Supporting keywords** — Weave in organically: [Project] + price / RERA / review / possession date / [city] and [configuration] + apartments in [locality].

**Serve three searcher intents:**
- Informational → About, Location, Amenities
- Commercial → Configurations, Investment, Phases
- Transactional → Get in Touch, price/RERA FAQs

**E-E-A-T** — Always include RERA number. Always use verified distances — never vague claims. State known negatives honestly. Use real numbers, names and dates throughout.

**Tone** — Honest, specific, human. No fluff: luxurious, world-class, magnificent, dream home.

## INPUT
**Primary Keyword:** {project_name}

Research everything. Write in exact section order. No sections skipped or renamed.
"""

VERIFICATION_PROMPT_TEMPLATE = """You are a content quality checker. Your job is to analyze the provided content and verify it meets structural requirements.  REQUIRED SECTIONS (must exist in this exact order): 1. H1 title containing the project name 2. \"About [Project Name]\" section (200-280 words) 3. \"Project at a Glance\" table with minimum 15 rows 4. \"Apartment Configurations & Sizes\" table with 4 columns 5. \"Location — Why [Locality] Makes Sense\" section with 4 bold subsections 6. \"Amenities\" section with 5 bold subsections 7. \"Construction Quality & Specifications\" table 8. \"Why This Is a Good Investment\" section with 4 bold subsections 9. \"Phases — Where Things Stand\" section (or explicit skip note if single-phase) 10. \"Frequently Asked Questions\" with minimum 6 questions 11. \"Get in Touch\" section 12. \"Disclaimer\" section with exact required text  VERIFICATION CHECKLIST: - All 12 sections present in correct order - Tables are properly formatted with headers - FAQ section has 6-10 questions (each question bolded) - About section word count is between 200-280 words - No placeholder text like \"[Project Name]\" left unfilled - No Lorem Ipsum or dummy content - Disclaimer text is present and complete  RESPOND ONLY IN THIS JSON FORMAT (nothing else): {{   \"verification_passed\": true,   \"missing_sections\": [],   \"errors\": [],   \"warnings\": [] }}  OR if verification fails: {{   \"verification_passed\": false,   \"missing_sections\": [\"Section 3: Project at a Glance table\", \"Section 10: FAQ\"],   \"errors\": [\"About section only 150 words (requires 200-280)\", \"FAQ has only 4 questions (requires 6-10)\"],   \"warnings\": [\"Placeholder text '[Project Name]' found in Section 5\"] }}

Content to verify:
{content}
"""

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
        "https://api.groq.com/openai/v1/hat/completions",
        headers=headers,
        data=json.dumps(data)
    )
    
    if response.status_code != 200:
        raise Exception(f"Error from OpenRouter: {response.status_code} - {response.text}")
        
    result = response.json()
    return result['choices'][0]['message']['content']

def generate_seo_content(project_name):
    print(f"Generating content for project: {project_name}...")
    prompt = GENERATION_PROMPT_TEMPLATE.format(project_name=project_name)
    content = call_openrouter(GENERATION_MODEL, prompt)
    return content

def verify_content(content):
    print("Verifying content structure...")
    prompt = VERIFICATION_PROMPT_TEMPLATE.format(content=content)
    # Using lower temperature for verification to get consistent JSON
    verification_text = call_openrouter(VERIFICATION_MODEL, prompt, temperature=0.1, max_tokens=1000)
    
    try:
        # Extract JSON from response (handle markdown code blocks if any)
        import re
        json_match = re.search(r'\{.*\}', verification_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            return json.loads(verification_text)
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
            print("✅ Verification passed!")
        else:
            print("⚠️ Verification failed with errors:")
            for err in verification_result.get("errors", []):
                print(f"  - {err}")
            for missing in verification_result.get("missing_sections", []):
                print(f"  - Missing: {missing}")
        
        save_content(project_name, content, verification_result)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
