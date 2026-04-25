# Application Manual – AI Location Scout

Welcome to the AI Business Location Scout! This application orchestrates real-time external data APIs, scraping logic, and sophisticated LLM analysis to help establish new commercial venues natively based on deep geographic insight into local markets and traffic indicators in Kazakhstan.

## 📥 1. Installation & Prerequisites
The application operates entirely offline locally with cloud service coordination (API Keys).

1. Install Python `3.10+`.
2. Activate your Virtual Environment: `.\\.venv\\Scripts\\Activate.ps1`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install apify-client beautifulsoup4 pytest
   ```
4. Define your keys in a `.env` file situated in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_key
   ANTHROPIC_API_KEY=your_anthropic_key
   TWOGIS_API_KEY=your_2gis_key
   APIFY_API_TOKEN=your_apify_token
   # Add any fallback configurations here.
   ```

## 🚀 2. Launching the App
1. From your active terminal in the root directory (`location_scout`), start the application using:
   ```bash
   python main.py
   ```
2. Alternatively, if you wish to run the backend engine without direct blocking:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🌍 3. Using the Web Interface
1. **Navigate:** Open your browser and go to `http://localhost:8000`.
2. **Form Configuration:** In the central card:
   - Select your intended **Business Type** (e.g. `Restaurant`, `Retail Store`).
   - Fill in your **Target City** (e.g. `Almaty`, `Astana`).
   - Slide your **Total Setup Budget (KZT)** natively representing your liquid capital.
   - Adjust the **Area Size** (m²). This acts as a hard filter parameter that bounds Krisha properties identically (e.g., `50 m²` precisely limits searches exclusively between `50m²` and `99m²` to block irrelevant Kiosks and Hangars).
3. **Execution:** Press the designated `Scout Locations` toggle.
4. **Data Aggregation Status:** Over the next ~15 to 45 seconds, independent processes will fetch OpenStreetMap coordinates, retrieve Foot-traffic Proxies from 2GIS, estimate Rent affordability matching your exact Area thresholds via Krisha.kz (or local database fallback), and finally pass the final structure through an AI evaluation check.
5. **Score Verification:** Once loaded, click directly on any of the "Scouted Locations" to inspect the `Overall Score` or interact with the immediate Google Maps / Krisha ad redirects displayed.
6. **Save to Favorites:** You can seamlessly bookmark any high-performing location by clicking **"☆ Save to Favorites"** on the generated card. 
   - This stores the location dynamically in your browser's `localStorage`, requiring no accounts or server databases.
   - Click the **"⭐ Saved"** link in the top-right navigation bar to open the Favorites Modal and review your saved properties at any time.

## 🧑‍💼 4. How to Find & Extract Candidates (HeadHunter)
1. Directly adjacent to the "Scouted Locations" header is the `Find Workers` tab. Click it!
2. The UI will instantly spin up a Cloud Apify Chromium instance using your backend `APIFY_TOKEN`.
3. The system translates your current `Business Category` parameter tightly to standard *Russian Job Roles*.
4. **Wait roughly ~15 seconds** for the Headless Chrome bypass logic to extract live target profiles from your designated `City`.
5. Once complete, you will see exactly up to 5 verified candidates featuring transparent Ages, Roles, Live Salaries, Experience histories, and explicitly functioning hot-links traversing right back into `hh.kz/resume/...` for instant hiring!

*Enjoy navigating your localized market!*
