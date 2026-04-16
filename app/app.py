"""
Heart Disease LOD - SPARQL Endpoint & Web Interface
=====================================================
A Flask web application that provides:
1. A SPARQL endpoint (/sparql) for programmatic queries
2. A beautiful web UI (/) for interactive SPARQL querying
3. Statistics dashboard
4. Pre-loaded sample queries
5. Federated query support to DBpedia

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

# Namespaces
HDO = Namespace("http://example.org/heart-disease-ontology#")
HDR = Namespace("http://example.org/heart-disease-data/")

# Global RDF graph
rdf_graph = None

# ============================================================================
# Sample SPARQL Queries
# ============================================================================
SAMPLE_QUERIES = {
    "1. All Patients (LIMIT 20)": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX hdr: <http://example.org/heart-disease-data/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?patient ?label ?age ?sex
WHERE {
    ?patient a hdo:Patient ;
             rdfs:label ?label ;
             hdo:age ?age ;
             hdo:sex ?sex .
}
ORDER BY ?age
LIMIT 20""",

    "2. Patients with Heart Disease": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX hdr: <http://example.org/heart-disease-data/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?patient ?age ?sex ?chestPainLabel
WHERE {
    ?patient a hdo:Patient ;
             hdo:age ?age ;
             hdo:sex ?sex ;
             hdo:hasDiagnosis ?diagnosis ;
             hdo:hasChestPainType ?cpType .
    ?diagnosis hdo:hasHeartDisease "true"^^xsd:boolean .
    ?cpType rdfs:label ?chestPainLabel .
}
ORDER BY DESC(?age)
LIMIT 20""",

    "3. Patients Over 60 with High Cholesterol": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX hdr: <http://example.org/heart-disease-data/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?patient ?age ?sex ?cholesterol ?hasDisease
WHERE {
    ?patient a hdo:Patient ;
             hdo:age ?age ;
             hdo:sex ?sex ;
             hdo:hasMeasurement ?measurement ;
             hdo:hasDiagnosis ?diagnosis .
    ?measurement hdo:cholesterol ?cholesterol .
    ?diagnosis hdo:hasHeartDisease ?hasDisease .
    FILTER (?age > 60 && ?cholesterol > 300)
}
ORDER BY DESC(?cholesterol)""",

    "4. Average Cholesterol by Chest Pain Type": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?cpLabel (AVG(?chol) AS ?avgCholesterol) (COUNT(?patient) AS ?patientCount)
WHERE {
    ?patient a hdo:Patient ;
             hdo:hasChestPainType ?cpType ;
             hdo:hasMeasurement ?m .
    ?m hdo:cholesterol ?chol .
    ?cpType rdfs:label ?cpLabel .
}
GROUP BY ?cpLabel
ORDER BY DESC(?avgCholesterol)""",

    "5. Disease Statistics by Age Group": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?ageGroup (COUNT(?patient) AS ?total)
       (SUM(IF(?hasDisease = "true"^^xsd:boolean, 1, 0)) AS ?withDisease)
       (SUM(IF(?hasDisease = "false"^^xsd:boolean, 1, 0)) AS ?withoutDisease)
WHERE {
    ?patient a hdo:Patient ;
             hdo:age ?age ;
             hdo:hasDiagnosis ?diagnosis .
    ?diagnosis hdo:hasHeartDisease ?hasDisease .
    BIND(
        IF(?age < 40, "Under 40",
        IF(?age < 50, "40-49",
        IF(?age < 60, "50-59",
        IF(?age < 70, "60-69", "70+")))) AS ?ageGroup
    )
}
GROUP BY ?ageGroup
ORDER BY ?ageGroup""",

    "6. Linked Data - DBpedia Connections": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
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
    FILTER(STRSTARTS(STR(?externalResource), "http://dbpedia.org/"))
}
ORDER BY ?linkType ?localResource""",

    "7. Full Patient Clinical Profile": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?patient ?age ?sex ?cpLabel ?bp ?chol ?maxHR ?oldpeak ?ecgLabel ?slopeLabel ?hasDisease
WHERE {
    ?patient a hdo:Patient ;
             hdo:age ?age ;
             hdo:sex ?sex ;
             hdo:hasChestPainType ?cpType ;
             hdo:hasMeasurement ?m ;
             hdo:hasDiagnosis ?diag .
    ?cpType rdfs:label ?cpLabel .
    ?m hdo:restingBP ?bp ;
       hdo:cholesterol ?chol ;
       hdo:maxHR ?maxHR ;
       hdo:oldpeak ?oldpeak ;
       hdo:hasECGResult ?ecg ;
       hdo:hasSTSlope ?slope .
    ?ecg rdfs:label ?ecgLabel .
    ?slope rdfs:label ?slopeLabel .
    ?diag hdo:hasHeartDisease ?hasDisease .
}
ORDER BY ?patient
LIMIT 15""",

    "8. Heart Disease Rate by Sex": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?sex (COUNT(?patient) AS ?total)
       (SUM(IF(?hasDisease = "true"^^xsd:boolean, 1, 0)) AS ?diseaseCount)
       (ROUND(SUM(IF(?hasDisease = "true"^^xsd:boolean, 1, 0)) * 100.0 / COUNT(?patient)) AS ?diseaseRate)
WHERE {
    ?patient a hdo:Patient ;
             hdo:sex ?sex ;
             hdo:hasDiagnosis ?diag .
    ?diag hdo:hasHeartDisease ?hasDisease .
}
GROUP BY ?sex""",

    "9. Ontology Classes & Properties": """PREFIX hdo: <http://example.org/heart-disease-ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?type ?name ?label ?comment
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
    FILTER(STRSTARTS(STR(?name), "http://example.org/heart-disease-ontology#"))
    OPTIONAL { ?name rdfs:label ?label }
    OPTIONAL { ?name rdfs:comment ?comment }
}
ORDER BY ?type ?name""",

    "10. [DBpedia] Heart-Related Diseases": """# Switch endpoint to 'DBpedia Endpoint' above before running!
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
        CONTAINS(LCASE(?label), 'angina') ||
        CONTAINS(LCASE(?label), 'myocardial')
    )
}
ORDER BY ?label
LIMIT 20""",

    "11. [DBpedia] Cardiovascular Disease Info": """# Switch endpoint to 'DBpedia Endpoint' above before running!
PREFIX dbr: <http://dbpedia.org/resource/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?name ?label ?type
WHERE {
    dbr:Cardiovascular_disease rdfs:label ?label ;
                               a ?type .
    OPTIONAL { dbr:Cardiovascular_disease foaf:name ?name }
    FILTER (lang(?label) = 'en')
    FILTER (STRSTARTS(STR(?type), 'http://dbpedia.org/'))
}
LIMIT 10""",

    "12. [DBpedia] Thalassemia & Angina Details": """# Switch endpoint to 'DBpedia Endpoint' above before running!
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
ORDER BY ?resource"""
}


def load_rdf_data():
    """Load the 5-star linked RDF data into memory."""
    global rdf_graph
    rdf_graph = Graph()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Try to load 5-star linked data first, fall back to 4-star
    linked_path = os.path.join(base_dir, 'output', 'heart_disease_linked.ttl')
    data_path = os.path.join(base_dir, 'output', 'heart_disease_data.ttl')
    ontology_path = os.path.join(base_dir, 'ontology', 'heart_disease_ontology.ttl')
    
    # Load ontology
    if os.path.exists(ontology_path):
        rdf_graph.parse(ontology_path, format="turtle")
        print(f"  [OK] Loaded ontology: {ontology_path}")
    
    # Load data (prefer linked version)
    if os.path.exists(linked_path):
        rdf_graph.parse(linked_path, format="turtle")
        print(f"  [OK] Loaded 5-star linked data: {linked_path}")
    elif os.path.exists(data_path):
        rdf_graph.parse(data_path, format="turtle")
        print(f"  [OK] Loaded 4-star data: {data_path}")
    else:
        print("  [!] WARNING: No RDF data found! Run the pipeline first.")
    
    # Bind namespaces
    rdf_graph.bind("hdo", HDO)
    rdf_graph.bind("hdr", HDR)
    
    print(f"  Total triples in graph: {len(rdf_graph)}")


def get_statistics():
    """Get summary statistics from the RDF graph."""
    stats = {}
    
    # Total triples
    stats['total_triples'] = len(rdf_graph)
    
    # Total patients
    q = """
    PREFIX hdo: <http://example.org/heart-disease-ontology#>
    SELECT (COUNT(?p) AS ?count) WHERE { ?p a hdo:Patient }
    """
    for row in rdf_graph.query(q):
        stats['total_patients'] = int(row[0])
    
    # Heart disease positive
    q = """
    PREFIX hdo: <http://example.org/heart-disease-ontology#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT (COUNT(?d) AS ?count) WHERE { 
        ?d hdo:hasHeartDisease "true"^^xsd:boolean 
    }
    """
    for row in rdf_graph.query(q):
        stats['disease_positive'] = int(row[0])
    
    # Heart disease negative
    stats['disease_negative'] = stats.get('total_patients', 0) - stats.get('disease_positive', 0)
    
    # External links count
    q = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT (COUNT(*) AS ?count) WHERE {
        {
            ?s owl:sameAs ?o .
            FILTER(STRSTARTS(STR(?o), "http://dbpedia.org/") || STRSTARTS(STR(?o), "http://www.wikidata.org/"))
        }
        UNION
        {
            ?s rdfs:seeAlso ?o .
            FILTER(STRSTARTS(STR(?o), "http://dbpedia.org/"))
        }
    }
    """
    for row in rdf_graph.query(q):
        stats['external_links'] = int(row[0])
    
    # Classes count
    q = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT (COUNT(?c) AS ?count) WHERE { 
        ?c a owl:Class .
        FILTER(STRSTARTS(STR(?c), "http://example.org/heart-disease-ontology#"))
    }
    """
    for row in rdf_graph.query(q):
        stats['classes_count'] = int(row[0])
    
    # Properties count
    q = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT (COUNT(?p) AS ?count) WHERE { 
        { ?p a owl:ObjectProperty } UNION { ?p a owl:DatatypeProperty }
        FILTER(STRSTARTS(STR(?p), "http://example.org/heart-disease-ontology#"))
    }
    """
    for row in rdf_graph.query(q):
        stats['properties_count'] = int(row[0])
    
    return stats


@app.route('/')
def index():
    """Render the SPARQL query web interface."""
    stats = get_statistics()
    return render_template('index.html', 
                         sample_queries=SAMPLE_QUERIES,
                         stats=stats)


@app.route('/sparql', methods=['GET', 'POST'])
def sparql_endpoint():
    """
    SPARQL endpoint supporting both GET and POST requests.
    
    Parameters:
        query (str): SPARQL query string
        format (str): Response format (json, turtle, xml) - default: json
    
    Returns:
        JSON results for SELECT/ASK queries
        Turtle/XML for CONSTRUCT/DESCRIBE queries
    """
    if request.method == 'GET':
        query = request.args.get('query', '')
        output_format = request.args.get('format', 'json')
    else:
        # Accept both form data and JSON body
        if request.is_json:
            data = request.get_json()
            query = data.get('query', '')
            output_format = data.get('format', 'json')
        else:
            query = request.form.get('query', '')
            output_format = request.form.get('format', 'json')
    
    if not query.strip():
        return jsonify({"error": "No SPARQL query provided"}), 400
    
    try:
        results = rdf_graph.query(query)
        
        # Handle SELECT queries
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
        
        # Handle ASK queries
        elif results.type == 'ASK':
            return jsonify({
                "type": "ASK",
                "result": bool(results.askAnswer)
            })
        
        # Handle CONSTRUCT/DESCRIBE queries
        else:
            if output_format == 'turtle':
                return Response(
                    results.serialize(format='turtle'),
                    mimetype='text/turtle'
                )
            else:
                return Response(
                    results.serialize(format='xml'),
                    mimetype='application/rdf+xml'
                )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/dbpedia-query', methods=['POST'])
def dbpedia_query():
    """
    Proxy endpoint to query DBpedia's public SPARQL endpoint.
    This enables federated queries from the web UI.
    """
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
                    row_data[col] = {
                        "value": binding[col]['value'],
                        "type": binding[col]['type']
                    }
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
    """Return dataset statistics as JSON."""
    return jsonify(get_statistics())


# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  Heart Disease LOD - SPARQL Endpoint")
    print("=" * 60)
    print("\nLoading RDF data...")
    load_rdf_data()
    print(f"\nServer starting...")
    print(f"  Web UI:         http://localhost:5000")
    print(f"  SPARQL Endpoint: http://localhost:5000/sparql")
    print(f"  DBpedia Proxy:   http://localhost:5000/api/dbpedia-query")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
