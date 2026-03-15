# SEO Content Generator

This script replicates the n8n workflow for generating SEO-optimized real estate content.

## Setup

1.  **Environment:** The project uses the virtual environment in `SEOGen`.
2.  **API Key:** Ensure your OpenRouter API key is in the `.env` file.
    ```env
    OPENROUTER_API_KEY=your_key_here
    ```
3.  **Dependencies:** Install requirements (already done if you followed my steps).
    ```bash
    .\SEOGen\Scripts\pip.exe install -r requirements.txt
    ```

## Usage

Run the script using the Python executable in the virtual environment:

```bash
.\SEOGen\Scripts\python.exe seo_gen.py
```

You will be prompted to enter a Project Name. The script will then:
1.  **Generate** the SEO content using the specified model (`liquid/lfm-2.5-1.2b-thinking:free`).
2.  **Verify** the structure using Gemini (`google/gemini-2.0-flash-lite-preview-02-05:free`).
3.  **Save** the output to the `output/` directory as a text file.

## Configuration

You can change the models or prompts directly in `seo_gen.py`.

- `GENERATION_MODEL`: Currently set to `liquid/lfm-2.5-1.2b-thinking:free`.
- `VERIFICATION_MODEL`: Currently set to `google/gemini-2.0-flash-lite-preview-02-05:free`.
