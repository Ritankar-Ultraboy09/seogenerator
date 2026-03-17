# SEO Content Generator
# OUTPUTS in .txt as of now. 

---

## ✅ Quick Start (Windows)

1. **Activate the virtual environment**

   ```powershell
   .\SEOGen\Scripts\Activate.ps1
   ```

2. **Install dependencies** (if not already installed):

   ```powershell
   .\SEOGen\Scripts\pip.exe install -r requirements.txt
   ```

3. **Create the `.env` file** in the project root (next to `seo_gen.py`) and add your OpenRouter key:

   ```env
   GROK_API_KEY=your_openrouter_api_key_here
   ```

4. **Run the generator script**:

   ```powershell
   .\SEOGen\Scripts\python.exe seo_gen.py
   ```

5. Enter a project name when prompted (e.g., `Prestige Alcazar`). The script will generate content, run verification, and save results to `output/`.

---

## 📁 What the code does

- **Generates SEO content** using the model defined in `seo_gen.py` (`GENERATION_MODEL`).
- **Verifies output structure** using a second model (`VERIFICATION_MODEL`).
- **Saves results** to `output/` in a timestamped `.txt` file:
  - Includes the raw generated content
  - Includes verification results (pass/fail, errors, missing sections)

---

## 🛠️ Configuration (Customize)

### Models
Update the models in `seo_gen.py` as needed:

- `GENERATION_MODEL` (used for SEO content)
- `VERIFICATION_MODEL` (used to validate structure)

### Prompts
Customize these prompt templates (used to steer generation/verification):

- `prompts/generation_prompt.txt`
- `prompts/verification_prompt.txt`

---

## 📦 Files & Folders (What to keep, what to ignore)

### ✅ Important folders/files

- `seo_gen.py` — main script
- `prompts/` — prompt templates used by the script
- `output/` — generated outputs (created automatically if missing)
- `.env` — contains your API key (should be created manually)

### 🚫 Ignored / not committed

These are already ignored via `.gitignore`, so you don’t need to create them manually:

- `SEOGen/` (virtual environment)
- `output/` (generated results)
- `__pycache__/`
- `.env`

If you plan to use a different folder for output, update the script accordingly.

---

## 🔍 Troubleshooting

- **Missing `GROK_API_KEY`**: Make sure `.env` exists and is loaded. If it’s missing, the script will fail with an API key error.
- **Prompt files missing**: Ensure `prompts/generation_prompt.txt` and `prompts/verification_prompt.txt` exist.
- **API errors**: The script raises exceptions with raw API error text, so check the terminal output.

---

If you want, I can also help you add a simple command-line interface (CLI) with arguments for project name, output path, and model overrides.