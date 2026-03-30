# AI Location Scout — System Architecture & Processes

This document details the complete end-to-end architecture, process pipelines, and real-time data integration methodologies used by the AI Business Location Scout application.

## ⚙️ Core Stack Overview
* **Frontend:** A highly dynamic structural dashboard powered by pure Vanilla Javascript, modular CSS, and an embedded responsive HTML UI. Features seamless tab management and custom asynchronous fetch loaders.
* **Backend:** Built natively on **FastAPI (Python)**. Highly asymmetric, designed around the non-blocking asynchronous `uvicorn` architecture to perform multiple intensive web scrapes simultaneously alongside AI inferences.

---

## 📡 Data Sources & Integrations

The system evaluates completely off real-market signals. Below is the exact breakdown of where all the intelligence originates from:

### 1. 2GIS API (Map & Geo-Spatial Intelligence)
* **Usage:** Provides core business logic for traffic scaling and competitor density parsing.
* **Competitor Gap:** Translates your exact selected English Business Category into 2GIS query tags (e.g. `rubric_id=164`), mapping all existing similar businesses within a 1km radius.
* **Foot Traffic Proxy:** Resolves the general density of infrastructure branches within a 400m radius of an evaluated zone to simulate realistic pedestrian/commercial traffic estimates accurately.

### 2. OpenStreetMap (OSM / Nominatim)
* **Usage:** Used primarily for fallback physical Geocoding.
* **Methodology:** When you input a "Target City", OSM translates this text directly into hard `lat, lon` geographic coordinates which serve as the anchors for the 2GIS spatial scanning parameters.

### 3. Krisha.kz (Commercial Real Estate Properties)
* **Usage:** Captures real-time lease listings matching your exact size preferences.
* **Methodology:** Instead of mock prices, the app executes an HTTP crawler via `BeautifulSoup` against Krisha's live public directory in your target city. 
* **Filter Algorithm:** Dynamically maps properties. If you select "100 m²", the URL explicitly clamps results (`?das[live.square][from]=100&das[to]=199`), and then mathematically cross-verifies the titles to ruthlessly block any unassociated "Promoted/Sponsored Ads" that falsely bypassed the filters.

### 4. HeadHunter.kz (Local Candidate Resourcing)
* **Usage:** Supplies immediate, relevant worker resumes situated locally in your Target City.
* **Methodology:** We bypass HeadHunter's aggressive bot-firewalls by instantiating **Apify Cloud Web Scrapers**. 
* **Data Flow:** The application translates the active `Business Type` into Russian `hh.kz` Job Keywords (e.g. Restaurant -> *шеф-повар, оффициант*), and triggers a Headless Chromium browser remotely via Apify. It manipulates the DOM in runtime to parse out accurate live Salaries, Ages, and actual Profile Links, surfacing exactly 5 candidates natively straight back into the Application Tab.

### 5. Google / Anthropic / Local LLM (AI Analytics Engine)
* **Usage:** Coordinates the logic between all disparate web numbers and formulates a single concise qualitative recommendation.
* **Methodology:** Processes your explicit Budget and Area Size against the Krisha Rent Averages and foot traffic metrics to compile the **Rent Affordability** and **Demographic Fit** scores visible on the card outputs.

---

## 🔁 Live Request Flow (Step-By-Step)
1. **Trigger:** The User launches `localhost:8000` and dispatches standard configuration payloads (City, Budget, Area Size, Category).
2. **Geo-Location:** Fast API routes the City to Nominatim, capturing precise anchor coordinates.
3. **Data Fetching:** 2GIS maps immediately index competitor matrices. At the exact same micro-second, the Krisha.kz scraper scrapes local rentals matching the requested `Area Size`.
4. **Scoring:** The results compile via the AI orchestration pipeline merging budget limitations against gathered metric gaps, rendering the unified JSON array of Scouted Zones.
5. **Secondary Trigger (Workers):** Toggling over to the "Find Workers" UI block spins up an isolated background process pinging Apify's API endpoint, compiling live resumes directly through the HeadHunter ecosystem to conclude the workflow pipeline flawlessly!
