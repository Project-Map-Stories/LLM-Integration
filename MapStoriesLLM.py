import json
import time
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# ------------------------------------------------
# Konfiguration
# ------------------------------------------------
GEOJSON_PATH = "alle_restaurants.geojson"
OUTPUT_JSON = "vergleich_oeffnungszeiten.json"
OUTPUT_CSV = "vergleich_oeffnungszeiten.csv"
MODEL = "DeepSeek-V4-Flash-0731"
SLEEP_BETWEEN_REQUESTS = 1.0  # Sekunden, um LLMHub/Websites nicht zu bombardieren

client = OpenAI(
    base_url="https://api.llmhub.infs.ai/v1",
    api_key=""
)

# ------------------------------------------------
# 1. Website laden und Text extrahieren
# ------------------------------------------------
def get_website_text(url, timeout=10):
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
    except Exception as e:
        return None, str(e)

    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "noscript"]):
        element.decompose()

    return soup.get_text(" ", strip=True), None

# ------------------------------------------------
# 2. Öffnungszeiten per LLM aus Website-Text extrahieren
# ------------------------------------------------
def extract_opening_hours(name, website_text):
    prompt = f"""
Analysiere den folgenden Inhalt der Website des Restaurants "{name}". Finde die Öffnungszeiten des Restaurants. Verwende ausschliesslich Informationen aus dem Website-Inhalt. Erfinde keine Informationen. Falls du nichts findest, setze die Werte auf null. Gib die Antwort ausschliesslich als JSON in diesem Format zurück, ohne Markdown-Codeblock, ohne zusätzlichen Text:
{{
    "restaurant": "{name}",
    "opening_hours": {{
        "monday": "Öffnungszeiten oder null",
        "tuesday": "Öffnungszeiten oder null",
        "wednesday": "Öffnungszeiten oder null",
        "thursday": "Öffnungszeiten oder null",
        "friday": "Öffnungszeiten oder null",
        "saturday": "Öffnungszeiten oder null",
        "sunday": "Öffnungszeiten oder null"
    }}
}}
Website-Inhalt: {website_text[:8000]}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()
    content = content.removeprefix("\n").removeprefix("\n").removesuffix("\n").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"restaurant": name, "opening_hours": None, "raw_response": content}

# ------------------------------------------------
# 3. OSM-Öffnungszeiten mit Website-Öffnungszeiten vergleichen (per LLM)
# ------------------------------------------------
def compare_hours(name, osm_hours, website_hours_json):
    prompt = f"""
Vergleiche die Öffnungszeiten aus OpenStreetMap mit den von der Restaurant-Website extrahierten Öffnungszeiten für "{name}".

OSM (opening_hours-Syntax):
{osm_hours}

Website (JSON, pro Wochentag):
{json.dumps(website_hours_json, ensure_ascii=False, indent=2)}

Beurteile, ob die beiden Quellen inhaltlich übereinstimmen (Wochentage und Zeiten müssen nicht exakt gleich formatiert sein, aber inhaltlich gleich).

Antworte ausschliesslich als JSON, ohne Markdown-Codeblock:

{{
    "match": "ja" | "nein" | "teilweise" | "nicht pruefbar",
    "unterschiede": "kurze Beschreibung der Abweichungen oder leerer String"
}}
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.choices[0].message.content.strip()
    content = content.removeprefix("\n").removeprefix("\n").removesuffix("\n").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"match": "error", "unterschiede": content}

# ------------------------------------------------
# 4. Hauptlogik: alle Features durchgehen
# ------------------------------------------------
def main():
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        data = json.load(f)

    results = []
    total = len(data["features"])

    for i, feature in enumerate(data["features"], start=1):
        props = feature["properties"]
        name = props.get("name", "Unbenannt")
        website = props.get("website")
        osm_hours = props.get("opening_hours")

        row = {
            "name": name,
            "website": website,
            "osm_opening_hours": osm_hours
        }

        print(f"[{i}/{total}] {name} ...", end=" ")

        if not website:
            row["status"] = "keine Website vorhanden"
            print("übersprungen (keine Website)")
            results.append(row)
            continue

        text, err = get_website_text(website)
        if err:
            row["status"] = f"Fehler beim Laden der Website: {err}"
            print(f"Fehler: {err}")
            results.append(row)
            continue

        extracted = extract_opening_hours(name, text)
        row["website_opening_hours"] = extracted.get("opening_hours")

        if osm_hours:
            comparison = compare_hours(name, osm_hours, extracted.get("opening_hours"))
            row["match"] = comparison.get("match")
            row["unterschiede"] = comparison.get("unterschiede")
            print(f"match={row['match']}")
        else:
            row["match"] = "OSM hat keine Öffnungszeiten"
            print("OSM hat keine Öffnungszeiten, nur Website extrahiert")

        results.append(row)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    # JSON speichern
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # CSV speichern (einfacher Überblick für den Report)
    import csv
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "website", "osm_opening_hours", "match", "unterschiede", "status"])
        for r in results:
            writer.writerow([
                r.get("name", ""),
                r.get("website", ""),
                r.get("osm_opening_hours", ""),
                r.get("match", ""),
                r.get("unterschiede", ""),
                r.get("status", "")
            ])

    # Kurze Zusammenfassung
    match_counts = {}
    for r in results:
        m = r.get("match", r.get("status", "unbekannt"))
        match_counts[m] = match_counts.get(m, 0) + 1

    print("\n--- Zusammenfassung ---")
    for k, v in match_counts.items():
        print(f"{k}: {v}")

    print(f"\nFertig! Ergebnisse gespeichert in:\n- {OUTPUT_JSON}\n- {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
