"""
Healthcare LOD - SPARQL Endpoint & Web Interface
==================================================
A Flask web application providing a SPARQL endpoint and web UI
for querying the Healthcare Linked Open Data.

Usage:
    python app.py
    Open http://localhost:5000 in your browser
"""

import os
import json
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON

# ============================================================================
# App Configuration
# ============================================================================
app = Flask(__name__)
CORS(app)

HCO = Namespace("http://example.org/healthcare-ontology#")
HCD = Namespace("http://example.org/healthcare-data/")

rdf_graph = None

# ============================================================================
# Sample SPARQL Queries
# ============================================================================
SAMPLE_QUERIES = {
    "1. All Patients (LIMIT 20)": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?patient ?name ?age ?gender
WHERE {
    ?patient a hco:Patient ;
             hco:patientName ?name ;
             hco:age ?age ;
             hco:gender ?gender .
}
ORDER BY ?name
LIMIT 20""",

    "2. Patients by Medical Condition": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name ?age ?gender ?conditionLabel
WHERE {
    ?patient a hco:Patient ;
             hco:patientName ?name ;
             hco:age ?age ;
             hco:gender ?gender ;
             hco:hasAdmission ?admission .
    ?admission hco:hasMedicalCondition ?condition .
    ?condition rdfs:label ?conditionLabel .
}
ORDER BY ?conditionLabel ?name
LIMIT 30""",

    "3. Emergency Admissions": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?name ?age ?conditionLabel ?hospital ?billing
WHERE {
    ?patient a hco:Patient ;
             hco:patientName ?name ;
             hco:age ?age ;
             hco:hasAdmission ?admission .
    ?admission hco:hasAdmissionType hco:Emergency ;
               hco:hasMedicalCondition ?cond ;
               hco:admittedTo ?hosp ;
               hco:billingAmount ?billing .
    ?cond rdfs:label ?conditionLabel .
    ?hosp hco:hospitalName ?hospital .
}
ORDER BY DESC(?billing)
LIMIT 20""",

    "4. Average Billing by Medical Condition": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?conditionLabel (AVG(?billing) AS ?avgBilling) (COUNT(?admission) AS ?totalAdmissions)
WHERE {
    ?admission a hco:Admission ;
               hco:hasMedicalCondition ?cond ;
               hco:billingAmount ?billing .
    ?cond rdfs:label ?conditionLabel .
}
GROUP BY ?conditionLabel
ORDER BY DESC(?avgBilling)""",

    "5. Statistics by Admission Type": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?admTypeLabel (COUNT(?admission) AS ?total) (AVG(?billing) AS ?avgCost)
WHERE {
    ?admission a hco:Admission ;
               hco:hasAdmissionType ?admType ;
               hco:billingAmount ?billing .
    ?admType rdfs:label ?admTypeLabel .
}
GROUP BY ?admTypeLabel
ORDER BY DESC(?total)""",

    "6. Medication Prescription Statistics": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?medLabel ?condLabel (COUNT(?adm) AS ?prescriptions)
WHERE {
    ?adm a hco:Admission ;
         hco:prescribedMedication ?med ;
         hco:hasMedicalCondition ?cond .
    ?med rdfs:label ?medLabel .
    ?cond rdfs:label ?condLabel .
}
GROUP BY ?medLabel ?condLabel
ORDER BY ?medLabel ?condLabel""",

    "7. Test Results Distribution": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?resultLabel ?condLabel (COUNT(?adm) AS ?count)
WHERE {
    ?adm a hco:Admission ;
         hco:hasTestResult ?result ;
         hco:hasMedicalCondition ?cond .
    ?result rdfs:label ?resultLabel .
    ?cond rdfs:label ?condLabel .
}
GROUP BY ?resultLabel ?condLabel
ORDER BY ?condLabel ?resultLabel""",

    "8. Full Patient Admission Profile": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?name ?age ?gender ?bloodType ?condition ?admType ?hospital ?doctor ?medication ?testResult ?billing ?admDate ?dischDate
WHERE {
    ?patient a hco:Patient ;
             hco:patientName ?name ;
             hco:age ?age ;
             hco:gender ?gender ;
             hco:hasBloodType ?bt ;
             hco:hasAdmission ?adm .
    ?bt rdfs:label ?bloodType .
    ?adm hco:hasMedicalCondition ?cond ;
         hco:hasAdmissionType ?at ;
         hco:admittedTo ?hosp ;
         hco:attendedBy ?doc ;
         hco:prescribedMedication ?med ;
         hco:hasTestResult ?tr ;
         hco:billingAmount ?billing ;
         hco:dateOfAdmission ?admDate ;
         hco:dischargeDate ?dischDate .
    ?cond rdfs:label ?condition .
    ?at rdfs:label ?admType .
    ?hosp hco:hospitalName ?hospital .
    ?doc hco:doctorName ?doctor .
    ?med rdfs:label ?medication .
    ?tr rdfs:label ?testResult .
}
ORDER BY ?name
LIMIT 15""",

    "9. Linked Data - DBpedia Connections": """PREFIX hco: <http://example.org/healthcare-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?localResource ?linkType ?externalResource
WHERE {
    {
        ?localResource owl:sameAs ?externalResource .
        BIND("owl:sameAs" AS ?linkType)
    }
    UNION
    {
        ?localResource rdfs:seeAlso ?externalResource .
        BIND("rdfs:seeAlso" AS ?linkType)
    }
    FILTER(STRSTARTS(STR(?externalResource), "http://dbpedia.org/") ||
           STRSTARTS(STR(?externalResource), "http://www.wikidata.org/"))
}
ORDER BY ?linkType ?localResource""",

    "10. Ontology Classes & Properties": """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?type ?name ?label
WHERE {
    {
        ?name rdf:type owl:Class .
        BIND("Class" AS ?type)
    }
    UNION
    {
        ?name rdf:type owl:ObjectProperty .
        BIND("Object Property" AS ?type)
    }
    UNION
    {
        ?name rdf:type owl:DatatypeProperty .
        BIND("Datatype Property" AS ?type)
    }
    FILTER(STRSTARTS(STR(?name), "http://example.org/healthcare-ontology#"))
    OPTIONAL { ?name rdfs:label ?label }
}
ORDER BY ?type ?name""",

    "11. [DBpedia] Healthcare Diseases": """# Switch endpoint to 'DBpedia Endpoint' above!
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
LIMIT 20""",

    "12. [DBpedia] Medication Details": """# Switch endpoint to 'DBpedia Endpoint' above!
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?resource ?label ?type
WHERE {
    VALUES ?resource {
        dbr:Aspirin
        dbr:Ibuprofen
        dbr:Penicillin
        dbr:Paracetamol
        dbr:Atorvastatin
    }
    ?resource rdfs:label ?label .
    OPTIONAL { ?resource a ?type . FILTER(STRSTARTS(STR(?type), 'http://dbpedia.org/')) }
    FILTER (lang(?label) = 'en')
}
ORDER BY ?resource"""
}


def load_rdf_data():
    """Load the 5-star linked RDF data into memory."""
    global rdf_graph
    rdf_graph = Graph()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    linked_path = os.path.join(base_dir, 'output', 'healthcare_linked.ttl')
    data_path = os.path.join(base_dir, 'output', 'healthcare_data.ttl')
    ontology_path = os.path.join(base_dir, 'ontology', 'healthcare_ontology.ttl')

    if os.path.exists(ontology_path):
        rdf_graph.parse(ontology_path, format="turtle")
        print(f"  [OK] Loaded ontology: {ontology_path}")

    if os.path.exists(linked_path):
        rdf_graph.parse(linked_path, format="turtle")
        print(f"  [OK] Loaded 5-star linked data: {linked_path}")
    elif os.path.exists(data_path):
        rdf_graph.parse(data_path, format="turtle")
        print(f"  [OK] Loaded 4-star data: {data_path}")
    else:
        print("  [!] WARNING: No RDF data found! Run the pipeline first.")

    rdf_graph.bind("hco", HCO)
    rdf_graph.bind("hcd", HCD)

    print(f"  Total triples in graph: {len(rdf_graph)}")


def get_statistics():
    """Get summary statistics from the RDF graph."""
    stats = {}
    stats['total_triples'] = len(rdf_graph)

    q = "PREFIX hco: <http://example.org/healthcare-ontology#> SELECT (COUNT(?p) AS ?c) WHERE { ?p a hco:Patient }"
    for row in rdf_graph.query(q):
        stats['total_patients'] = int(row[0])

    q = "PREFIX hco: <http://example.org/healthcare-ontology#> SELECT (COUNT(?a) AS ?c) WHERE { ?a a hco:Admission }"
    for row in rdf_graph.query(q):
        stats['total_admissions'] = int(row[0])

    q = "PREFIX hco: <http://example.org/healthcare-ontology#> SELECT (COUNT(?d) AS ?c) WHERE { ?d a hco:Doctor }"
    for row in rdf_graph.query(q):
        stats['total_doctors'] = int(row[0])

    q = "PREFIX hco: <http://example.org/healthcare-ontology#> SELECT (COUNT(?h) AS ?c) WHERE { ?h a hco:Hospital }"
    for row in rdf_graph.query(q):
        stats['total_hospitals'] = int(row[0])

    q = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT (COUNT(*) AS ?c) WHERE {
        { ?s owl:sameAs ?o . FILTER(STRSTARTS(STR(?o), "http://dbpedia.org/") || STRSTARTS(STR(?o), "http://www.wikidata.org/")) }
        UNION
        { ?s rdfs:seeAlso ?o . FILTER(STRSTARTS(STR(?o), "http://dbpedia.org/")) }
    }"""
    for row in rdf_graph.query(q):
        stats['external_links'] = int(row[0])

    q = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT (COUNT(?c) AS ?count) WHERE {
        ?c a owl:Class .
        FILTER(STRSTARTS(STR(?c), "http://example.org/healthcare-ontology#"))
    }"""
    for row in rdf_graph.query(q):
        stats['classes_count'] = int(row[0])

    return stats


@app.route('/')
def index():
    stats = get_statistics()
    return render_template('index.html', sample_queries=SAMPLE_QUERIES, stats=stats)


@app.route('/sparql', methods=['GET', 'POST'])
def sparql_endpoint():
    if request.method == 'GET':
        query = request.args.get('query', '')
    else:
        if request.is_json:
            data = request.get_json()
            query = data.get('query', '')
        else:
            query = request.form.get('query', '')

    if not query.strip():
        return jsonify({"error": "No SPARQL query provided"}), 400

    try:
        results = rdf_graph.query(query)

        if results.type == 'SELECT':
            columns = [str(v) for v in results.vars]
            rows = []
            for row in results:
                row_data = {}
                for i, var in enumerate(results.vars):
                    value = row[i]
                    if value is not None:
                        row_data[str(var)] = {
                            "value": str(value),
                            "type": "uri" if hasattr(value, 'n3') and value.n3().startswith('<') else "literal"
                        }
                    else:
                        row_data[str(var)] = {"value": "", "type": "literal"}
                rows.append(row_data)

            return jsonify({
                "type": "SELECT",
                "columns": columns,
                "results": rows,
                "count": len(rows)
            })

        elif results.type == 'ASK':
            return jsonify({"type": "ASK", "result": bool(results.askAnswer)})

        else:
            return Response(results.serialize(format='turtle'), mimetype='text/turtle')

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/dbpedia-query', methods=['POST'])
def dbpedia_query():
    data = request.get_json()
    query = data.get('query', '')

    if not query.strip():
        return jsonify({"error": "No query provided"}), 400

    try:
        sparql = SPARQLWrapper("https://dbpedia.org/sparql")
        sparql.setQuery(query)
        sparql.setReturnFormat(SPARQL_JSON)
        sparql.setTimeout(30)

        results = sparql.query().convert()

        columns = results['head']['vars']
        rows = []
        for binding in results['results']['bindings']:
            row_data = {}
            for col in columns:
                if col in binding:
                    row_data[col] = {"value": binding[col]['value'], "type": binding[col]['type']}
                else:
                    row_data[col] = {"value": "", "type": "literal"}
            rows.append(row_data)

        return jsonify({
            "type": "SELECT",
            "columns": columns,
            "results": rows,
            "count": len(rows),
            "source": "DBpedia"
        })

    except Exception as e:
        return jsonify({"error": f"DBpedia query failed: {str(e)}"}), 400


@app.route('/api/stats')
def api_stats():
    return jsonify(get_statistics())


if __name__ == '__main__':
    print("=" * 60)
    print("  Healthcare LOD - SPARQL Endpoint")
    print("=" * 60)
    print("\nLoading RDF data...")
    load_rdf_data()
    print(f"\nServer starting...")
    print(f"  Web UI:         http://localhost:5000")
    print(f"  SPARQL Endpoint: http://localhost:5000/sparql")
    print(f"  DBpedia Proxy:   http://localhost:5000/api/dbpedia-query")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
