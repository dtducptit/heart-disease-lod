# Healthcare Linked Open Data (LOD) Application

A complete **5-star Linked Open Data** application in the healthcare domain, demonstrating the full LOD pipeline from raw CSV data to a queryable SPARQL endpoint linked to DBpedia.

## 5-Star LOD Rating

| Level | Standard | Implementation |
|-------|----------|----------------|
| ★ | Available on the Web | Data served via HTTP endpoint |
| ★★ | Structured Format | Machine-readable data |
| ★★★ | Open Format | Source data in CSV (non-proprietary) |
| ★★★★ | RDF with URIs | Data converted to RDF/Turtle with W3C standards |
| ★★★★★ | Linked Data | Connected to DBpedia & Wikidata via `owl:sameAs` |

## Project Structure

```
heart-disease-lod/
├── ontology/
│   └── healthcare_ontology.ttl       # OWL ontology definition
├── data/
│   └── healthcare_dataset.csv        # Source dataset (3★)
├── scripts/
│   ├── generate_data.py              # Generate synthetic healthcare data
│   ├── csv_to_rdf.py                 # CSV → RDF converter (3★ → 4★)
│   └── link_dbpedia.py               # DBpedia linker (4★ → 5★)
├── output/
│   ├── healthcare_data.ttl           # 4★ RDF data
│   └── healthcare_linked.ttl         # 5★ Linked RDF data
├── app/
│   ├── app.py                        # Flask SPARQL endpoint
│   ├── templates/index.html          # Web UI
│   └── static/styles.css             # Styling
├── queries/
│   └── sample_queries.sparql         # Example SPARQL queries
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare Dataset
The application uses the `healthcare_dataset.csv` file in the `data/` directory. You can generate it using:
```bash
python scripts/generate_data.py
```
Or use the pre-downloaded Kaggle dataset.

### 3. Convert to RDF (3★ → 4★)
```bash
python scripts/csv_to_rdf.py
```
This processes 55,000+ records into ~1.3 million triples.

### 4. Link to DBpedia (4★ → 5★)
```bash
python scripts/link_dbpedia.py
```

### 5. Start SPARQL Endpoint
```bash
python app/app.py
```

Open http://localhost:5000 in your browser.

## Project Statistics

After running the full pipeline, the dataset reaches the following scale:

- **Total RDF Triples:** ~1,350,904
- **Patient Records:** 55,500
- **Unique Medical Practitioners:** 40,341
- **Unique Healthcare Facilities:** 39,876
- **External LOD Links:** 39+ (DBpedia, Wikidata)

## Dataset

Based on the [Kaggle Healthcare Dataset](https://www.kaggle.com/datasets/prasad22/healthcare-dataset) schema:

| Column | Type | Description |
|--------|------|-------------|
| Name | string | Patient name |
| Age | int | Patient age (18-85) |
| Gender | string | Male / Female |
| Blood Type | string | A+, A-, B+, B-, AB+, AB-, O+, O- |
| Medical Condition | string | Diabetes, Hypertension, Asthma, Arthritis, Cancer, Obesity |
| Date of Admission | date | Hospital admission date |
| Doctor | string | Attending physician |
| Hospital | string | Healthcare facility |
| Insurance Provider | string | Aetna, Blue Cross, Cigna, UnitedHealthcare, Medicare |
| Billing Amount | float | Cost of services (USD) |
| Room Number | int | Patient room |
| Admission Type | string | Emergency, Elective, Urgent |
| Discharge Date | date | Hospital discharge date |
| Medication | string | Aspirin, Ibuprofen, Penicillin, Paracetamol, Lipitor |
| Test Results | string | Normal, Abnormal, Inconclusive |

## Ontology Overview

### Classes
- **Patient** — Person receiving healthcare services (subclass of foaf:Person)
- **Admission** — Hospital admission event
- **Hospital** — Healthcare facility
- **Doctor** — Medical professional
- **InsuranceProvider** — Health insurance company
- **MedicalCondition** — Disease/diagnosis (Diabetes, Hypertension, etc.)
- **BloodType** — ABO+Rh classification
- **AdmissionType** — Urgency level (Emergency, Elective, Urgent)
- **Medication** — Prescribed drugs (Aspirin, Ibuprofen, etc.)
- **TestResult** — Test outcome (Normal, Abnormal, Inconclusive)

### Properties
| Type | Property | Domain → Range |
|------|----------|---------------|
| Object | hasAdmission | Patient → Admission |
| Object | attendedBy | Admission → Doctor |
| Object | admittedTo | Admission → Hospital |
| Object | hasInsurance | Patient → InsuranceProvider |
| Object | hasBloodType | Patient → BloodType |
| Object | hasMedicalCondition | Admission → MedicalCondition |
| Object | hasAdmissionType | Admission → AdmissionType |
| Object | prescribedMedication | Admission → Medication |
| Object | hasTestResult | Admission → TestResult |
| Data | patientName, age, gender | Patient → xsd:string/integer |
| Data | dateOfAdmission, dischargeDate | Admission → xsd:date |
| Data | billingAmount, roomNumber | Admission → xsd:float/integer |

## DBpedia Links

| Local Resource | Link Type | External Resource |
|---------------|-----------|-------------------|
| Diabetes | owl:sameAs | dbr:Diabetes |
| Hypertension | owl:sameAs | dbr:Hypertension |
| Asthma | owl:sameAs | dbr:Asthma |
| Arthritis | owl:sameAs | dbr:Arthritis |
| Cancer | owl:sameAs | dbr:Cancer |
| Obesity | owl:sameAs | dbr:Obesity |
| Aspirin | owl:sameAs | dbr:Aspirin |
| Ibuprofen | owl:sameAs | dbr:Ibuprofen |
| Penicillin | owl:sameAs | dbr:Penicillin |
| Paracetamol | owl:sameAs | dbr:Paracetamol |
| Lipitor | owl:sameAs | dbr:Atorvastatin |
| Patient | rdfs:seeAlso | dbr:Patient |
| Hospital | rdfs:seeAlso | dbr:Hospital |
| Doctor | rdfs:seeAlso | dbr:Physician |
| Patient | owl:sameAs | wikidata:Q181600 |
| Hospital | owl:sameAs | wikidata:Q16917 |

## SPARQL Endpoint

### Local Endpoint
- **URL**: `http://localhost:5000/sparql`
- **Methods**: GET, POST
- **Format**: JSON

### DBpedia Queries (Virtuoso)
Run these on https://dbpedia.org/sparql:

**Find diseases related to our dataset:**
```sparql
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?disease ?label
WHERE {
    ?disease a dbo:Disease ;
             rdfs:label ?label .
    FILTER (lang(?label) = 'en')
    FILTER (
        CONTAINS(LCASE(?label), 'diabetes') ||
        CONTAINS(LCASE(?label), 'hypertension') ||
        CONTAINS(LCASE(?label), 'asthma') ||
        CONTAINS(LCASE(?label), 'arthritis') ||
        CONTAINS(LCASE(?label), 'obesity')
    )
}
ORDER BY ?label
LIMIT 20
```

**Get medication details:**
```sparql
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?resource ?label ?type
WHERE {
    VALUES ?resource {
        dbr:Aspirin dbr:Ibuprofen dbr:Penicillin
        dbr:Paracetamol dbr:Atorvastatin
    }
    ?resource rdfs:label ?label .
    OPTIONAL { ?resource a ?type . FILTER(STRSTARTS(STR(?type), 'http://dbpedia.org/')) }
    FILTER (lang(?label) = 'en')
}
ORDER BY ?resource
```

## Technologies

- **Python 3.10+**
- **RDFLib** — RDF graph library
- **Flask** — Web framework
- **Pandas** — CSV processing
- **SPARQLWrapper** — DBpedia query proxy
- **OWL 2** — Ontology definition
- **RDF/Turtle** — Data serialization
- **SPARQL 1.1** — Query language

## References

- [Kaggle Healthcare Dataset](https://www.kaggle.com/datasets/prasad22/healthcare-dataset)
- [W3C RDF Primer](https://www.w3.org/TR/rdf-primer/)
- [5-Star Linked Open Data](https://5stardata.info/)
- [DBpedia](https://dbpedia.org/)
