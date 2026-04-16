# Heart Disease Linked Open Data (LOD) Application

A complete **5-star Linked Open Data** application in the health domain (heart disease prediction), demonstrating the full LOD pipeline from raw CSV data to a queryable SPARQL endpoint linked to DBpedia.

## 🌟 5-Star LOD Rating

| Level | Standard | Implementation |
|-------|----------|----------------|
| ★ | Available on the Web | Data served via HTTP endpoint |
| ★★ | Structured Format | Machine-readable data |
| ★★★ | Open Format | Source data in CSV (non-proprietary) |
| ★★★★ | RDF with URIs | Data converted to RDF/Turtle with W3C standards |
| ★★★★★ | Linked Data | Connected to DBpedia & Wikidata via `owl:sameAs` |

## 📁 Project Structure

```
heart-disease-lod/
├── ontology/
│   └── heart_disease_ontology.ttl    # OWL ontology definition
├── data/
│   └── heart.csv                     # Source dataset (3★)
├── scripts/
│   ├── generate_data.py              # Generate realistic heart disease data
│   ├── csv_to_rdf.py                 # CSV → RDF converter (3★ → 4★)
│   └── link_dbpedia.py               # DBpedia linker (4★ → 5★)
├── output/
│   ├── heart_disease_data.ttl        # 4★ RDF data
│   └── heart_disease_linked.ttl      # 5★ Linked RDF data
├── app/
│   ├── app.py                        # Flask SPARQL endpoint
│   ├── templates/index.html          # Web UI
│   └── static/styles.css             # Styling
├── queries/
│   └── sample_queries.sparql         # Example SPARQL queries
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Dataset
```bash
python scripts/generate_data.py
```

### 3. Convert to RDF (3★ → 4★)
```bash
python scripts/csv_to_rdf.py
```

### 4. Link to DBpedia (4★ → 5★)
```bash
python scripts/link_dbpedia.py
```

### 5. Start SPARQL Endpoint
```bash
python app/app.py
```

Open http://localhost:5000 in your browser.

## 📊 Ontology Overview

### Classes
- **Patient** — Person with clinical measurements (subclass of foaf:Person)
- **Diagnosis** — Heart disease diagnostic result
- **ClinicalMeasurement** — Clinical test results
- **ChestPainType** — Enumeration (Typical Angina, Atypical, Non-anginal, Asymptomatic)
- **ECGResult** — ECG classification (Normal, ST-T Abnormality, LVH)
- **STSlope** — ST segment slope (Upsloping, Flat, Downsloping)
- **ThalassemiaType** — Blood disorder type (Normal, Fixed Defect, Reversible Defect)

### Properties
| Type | Property | Domain → Range |
|------|----------|---------------|
| Object | hasDiagnosis | Patient → Diagnosis |
| Object | hasMeasurement | Patient → ClinicalMeasurement |
| Object | hasChestPainType | Patient → ChestPainType |
| Object | hasECGResult | Measurement → ECGResult |
| Data | age, sex | Patient → xsd:integer/string |
| Data | cholesterol, restingBP, maxHR | Measurement → xsd:integer |
| Data | hasHeartDisease | Diagnosis → xsd:boolean |

## 🌐 DBpedia Links

The dataset is connected to the LOD Cloud through:

| Local Resource | Link Type | External Resource |
|---------------|-----------|------------------|
| ThalassemiaType | owl:sameAs | dbr:Thalassemia |
| TypicalAngina | owl:sameAs | dbr:Angina_pectoris |
| LVH | owl:sameAs | dbr:Left_ventricular_hypertrophy |
| Patient | rdfs:seeAlso | dbr:Patient |
| cholesterol | rdfs:seeAlso | dbr:Cholesterol |
| restingBP | rdfs:seeAlso | dbr:Blood_pressure |
| Patient (class) | owl:sameAs | wikidata:Q181600 |

## 🔍 SPARQL Endpoint

### Local Endpoint
- **URL**: `http://localhost:5000/sparql`
- **Methods**: GET, POST
- **Format**: JSON

### Example Query (curl)
```bash
curl -X POST http://localhost:5000/sparql \
  -H "Content-Type: application/json" \
  -d '{"query": "PREFIX hdo: <http://example.org/heart-disease-ontology#> SELECT (COUNT(?p) AS ?count) WHERE { ?p a hdo:Patient }"}'
```

### DBpedia Queries (Virtuoso)
Run these on https://dbpedia.org/sparql (Virtuoso):

**Query 1: Find heart-related diseases**
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?disease ?label
WHERE {
    ?disease a dbo:Disease ;
             rdfs:label ?label .
    FILTER (lang(?label) = 'en')
    FILTER (
        CONTAINS(LCASE(?label), 'heart') ||
        CONTAINS(LCASE(?label), 'cardiac') ||
        CONTAINS(LCASE(?label), 'coronary') ||
        CONTAINS(LCASE(?label), 'angina')
    )
}
ORDER BY ?label
LIMIT 20
```

**Query 2: Get details for linked resources (Thalassemia, Angina, etc.)**
```sparql
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?resource ?label ?type
WHERE {
    VALUES ?resource {
        dbr:Thalassemia
        dbr:Angina
        dbr:Cholesterol
        dbr:Electrocardiography
        dbr:Blood_pressure
        dbr:Left_ventricular_hypertrophy
    }
    ?resource rdfs:label ?label .
    OPTIONAL { ?resource a ?type . FILTER(STRSTARTS(STR(?type), 'http://dbpedia.org/')) }
    FILTER (lang(?label) = 'en')
}
ORDER BY ?resource
```

> **Note**: `dbr:Heart_disease` is a redirect page in DBpedia (no labels/abstracts). Use `dbr:Cardiovascular_disease` for the main resource.

## 🛠 Technologies

- **Python 3.10+**
- **RDFLib** — RDF graph library for Python
- **Flask** — Web framework for SPARQL endpoint
- **Pandas** — CSV data processing
- **SPARQLWrapper** — DBpedia query proxy
- **OWL 2** — Ontology definition
- **RDF/Turtle** — Data serialization format
- **SPARQL 1.1** — Query language

## 📖 References

- [UCI Heart Disease Dataset](https://archive.ics.uci.edu/ml/datasets/Heart+Disease)
- [Kaggle: Heart Disease Prediction](https://www.kaggle.com/code/farzadnekouei/heart-disease-prediction)
- [W3C RDF Primer](https://www.w3.org/TR/rdf-primer/)
- [5-Star Linked Open Data](https://5stardata.info/)
- [DBpedia](https://dbpedia.org/)
