# MapStoriesLLM — OSM Data Enrichment with AI

A Python project developed during the Study Week at **OST (Eastern Switzerland University of Applied Sciences)**. This tool enriches OpenStreetMap (OSM) restaurant data by extracting opening hours from official websites using Large Language Models (LLMs) and comparing them with existing OSM records.

## 🎯 Overview

OpenStreetMap is a valuable crowdsourced map database, but many POIs (Points of Interest) like restaurants have incomplete data—especially opening hours. This project addresses this gap by:

1. Loading restaurant data from a GeoJSON file exported from Overpass API / OSM
2. Extracting website content for each restaurant
3. Using an LLM to parse opening hours from unstructured website text
4. Comparing LLM-extracted hours with OSM `opening_hours` syntax
5. Generating structured JSON and CSV reports for analysis

### Problem Statement

Many OSM entries contain:
- ✗ No opening hours
- ✗ Inconsistent or outdated `opening_hours` values
- ✗ Unverified data across different sources

This tool automates data validation and enrichment using AI to cross-reference official sources.

## 🔧 Setup

### Prerequisites

- Python 3.9+
- pip package manager
- LLMHub API credentials

### Step 1: Install dependencies:
```bash
pip install requests beautifulsoup4 openai
```
### Step 2: Set your API key in MapStoriesLLM.py:
```api_key="YOUR_API_KEY"```
### Step 3: Place your alle_restaurants.geojson file in the same directory

## ▶️ Usage
```python MapStoriesLLM.py```

## 📦 Outputs
- vergleich_oeffnungszeiten.json — Full results
- vergleich_oeffnungszeiten.csv — Summary table

## ⚠️ Note
This project was completed during a one-week practical training. Some configuration may need adjustment for production use.

## 📄 License
MIT License — see [LICENSE](https://github.com/Project-Map-Stories/LLM-Integration/blob/main/LICENSE) file for details.
