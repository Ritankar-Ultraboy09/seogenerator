import re
import requests
from bs4 import BeautifulSoup

def safe_text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text(separator=' ', strip=True)


def extract_field_from_text(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return m.group(1).strip()
    return ""


def extract_project_specs(text):
    project_specs = {
        "unit_configuration": [],
        "number_of_towers": None,
        "number_of_units": None,
        "project_area": None,
        "possession_status": "",
        "possession_date": "",
        "water_supply": "",
        "parking": "",
        "price_range": None
    }
    config_match = re.search(r"Unit Configuration\s*([0-9.,\s]+BHK)", text, re.I)
    if config_match:
        configs = config_match.group(1).replace(' ', '').split(',')
        project_specs["unit_configuration"] = [c.strip() for c in configs if c.strip()]

    towers_match = re.search(r"No\.?\s*Of\s*Towers?\s*(\d+)", text, re.I)
    if towers_match:
        project_specs["number_of_towers"] = int(towers_match.group(1))

    units_match = re.search(r"Units?\s*(\d+|NA)", text, re.I)
    if units_match:
        val = units_match.group(1)
        project_specs["number_of_units"] = None if val == "NA" else int(val)

    area_match = re.search(r"Project\s*Area\s*(\d+|NA)", text, re.I)
    if area_match:
        val = area_match.group(1)
        project_specs["project_area"] = None if val == "NA" else val

    status_match = re.search(r"(Ready to Move|Under Construction)", text, re.I)
    if status_match:
        project_specs["possession_status"] = status_match.group(1)

    date_match = re.search(r"Possession\s*in\s*[:\-\s]*([A-Za-z0-9\s]+?)(?:\s+Show|\s+Interest|$)", text, re.I)
    if date_match:
        project_specs["possession_date"] = date_match.group(1)

    water_match = re.search(r"Water\s*Supply\s*[:\-\s]*([A-Za-z\s]+?)(?:\s+Unit|\s+NA|\s+No|$)", text, re.I)
    if water_match:
        project_specs["water_supply"] = water_match.group(1).strip()
    parking = ""
    text_lower = text.lower()
    if "covered car parking" in text_lower:
        parking = "Covered"
    elif "open parking" in text_lower:
        parking = "Open"
    elif "visitor parking" in text_lower:
        parking = "Visitor"
    project_specs["parking"] = parking
    

    price_match = re.search(r"(?:₹|Rs\.?|INR)?\s*[\d.]+\s*(?:Cr(?:ore)?|Lakh|L)\s*(?:to|[-–—])\s*(?:₹|Rs\.?|INR)?\s*[\d.]+\s*(?:Cr(?:ore)?|Lakh|L)?", text, re.I)
    if price_match:
        project_specs["price_range"] = price_match.group(0).strip()
    return project_specs


def extract_amenities(text):
    possible_amenities = [
        "Wifi",
        "Air Conditioner",
        "Gas Pipeline",
        "Power Backup",
        "Common Garden",
        "Lift",
        "Swimming Pool",
        "Gym",
        "Security",
        "Club House",
        "Tennis Court",
        "CCTV Camera",
        "Vastu Compliant",
        "Fire Safety",
        "Intercom",
        "Bike Parking",
        "Children's Play Area",
        "Covered Car Parking"
    ]
    amenities = []
    for amenity in possible_amenities:
        if re.search(r'\b' + re.escape(amenity) + r'\b', text, re.I):
            amenities.append(amenity)
    return amenities


def extract_rera_data(text):
    rera_data = {
        "rera_registered": False,
        "nobroker_rera_id": "",
        "builder_project_rera_id": "",
        "rera_state": "",
        "rera_certificate_available": False,
        "rera_benefits": []
    }
    if re.search(r'\bRERA\b', text, re.I):
        rera_data["rera_registered"] = True
        rera_data["rera_certificate_available"] = True
        rera_data["rera_benefits"] = [
            "Timely Dispute Resolution - resolved within 120 days",
            "Quality Assurance - developers liable for defects",
            "Buyer Protection - grievance redressal through RERA",
            "Transparency & Tracking - project progress trackable"
        ]
    nobroker_id = extract_field_from_text(text, [
        r"nobroker\s*rera\s*id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"nobroker\s*rera\s*Id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"NoBroker\s*RERA\s*id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"NoBroker\s*RERA\s*Id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"RERA\s*ID\s*[:\-\s]*([A-Z0-9\-\/]+)"
    ])
    if nobroker_id:
        rera_data["nobroker_rera_id"] = nobroker_id
    builder_id = extract_field_from_text(text, [
        r"builder\s*project\s*rera\s*id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"Builder\s*Project\s*RERA\s*id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"Builder\s*Project\s*RERA\s*Id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"Project\s*RERA\s*id\s*[:\-\s]*([A-Z0-9\-\/]+)",
        r"Project\s*RERA\s*Id\s*[:\-\s]*([A-Z0-9\-\/]+)"
    ])
    if builder_id:
        rera_data["builder_project_rera_id"] = builder_id


    state_keywords = {
        'Maharashtra': r'maharera|maharashtra',
        'Karnataka': r'karnataka|karnataka rera',
        'Tamil Nadu': r'tamil nadu|tnrera',
        'Uttar Pradesh': r'uttar pradesh|uprera',
        'Gujarat': r'gujarat|gajarera',
        'Rajasthan': r'rajasthan|rera rajasthan',
        'Delhi': r'delhi|dperera',
        'Punjab': r'punjab|pbrera',
        'Haryana': r'haryana|hrera',
        'Madhya Pradesh': r'madhya pradesh|mprera',
        'Kerala': r'kerala|keralarera',
        'Andhra Pradesh': r'andhra pradesh|apera'
    }
    for state, pattern in state_keywords.items():
        if re.search(pattern, text, re.I):
            rera_data["rera_state"] = state
            break

    return rera_data


def scrape_nobroker_details(url):
    details = {
        "nobroker_rera": "",
        "builder_rera": "",
        "configurations": "",
        "summary": "",
        "project_specs": {},
        "amenities": [],
        "rera_data": {}
    }
    if not url:
        return details
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        text = safe_text_from_html(resp.text)
        details["summary"] = text[:1200]
        details["project_specs"] = extract_project_specs(text)
        details["configurations"] = ', '.join(details["project_specs"].get('unit_configuration', []))
        details["amenities"] = extract_amenities(text)
        details["rera_data"] = extract_rera_data(text)
        details["nobroker_rera"] = details["rera_data"].get('nobroker_rera_id', '')
        details["builder_rera"] = details["rera_data"].get('builder_project_rera_id', '')
    except Exception as e:
        details["summary"] = f"Scrape failed for {url}: {e}"
    return details


def get_scraped_details(url, cache):
    if not url:
        return {"nobroker_rera": "", "builder_rera": "", "configurations": "", "summary": "", "project_specs": {}, "amenities": [], "rera_data": {}}
    if url in cache:
        return cache[url]
    details = scrape_nobroker_details(url)
    cache[url] = details
    return details