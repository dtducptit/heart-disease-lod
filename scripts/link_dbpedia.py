"""
DBpedia Linking Script for Heart Disease LOD
==============================================
Establishes links between local RDF data and the LOD Cloud (DBpedia)
to achieve 5-star Linked Open Data status.

Links are created using:
- owl:sameAs     → for equivalent concepts
- rdfs:seeAlso   → for related resources
- dbo:*          → for DBpedia ontology properties

Input:  output/heart_disease_data.ttl (4★)
Output: output/heart_disease_linked.ttl (5★)
"""

import os
import sys
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, FOAF

# ============================================================================
# Namespace Definitions
# ============================================================================
HDO = Namespace("http://example.org/heart-disease-ontology#")
HDR = Namespace("http://example.org/heart-disease-data/")
SCHEMA = Namespace("http://schema.org/")
DCT = Namespace("http://purl.org/dc/terms/")
DBR = Namespace("http://dbpedia.org/resource/")
DBO = Namespace("http://dbpedia.org/ontology/")
DBP = Namespace("http://dbpedia.org/property/")
WIKIDATA = Namespace("http://www.wikidata.org/entity/")

# ============================================================================
# DBpedia Link Definitions
# ============================================================================

# owl:sameAs links — these concepts are identical to DBpedia resources
SAME_AS_LINKS = [
    # Ontology class links
    (HDO.ThalassemiaType, DBR.Thalassemia),
    (HDO.TypicalAngina, DBR.Angina_pectoris),
    (HDO.AtypicalAngina, DBR.Angina_pectoris),  # subtype
    
    # Named individual links
    (HDO.NormalECG, DBR.Electrocardiography),
    (HDO.STTWaveAbnormality, DBR.ST_segment),
    (HDO.LeftVentricularHypertrophy, DBR.Left_ventricular_hypertrophy),
]

# rdfs:seeAlso links — related but not identical concepts  
SEE_ALSO_LINKS = [
    # Classes to related DBpedia articles
    (HDO.Patient, DBR.Patient),
    (HDO.Diagnosis, DBR.Medical_diagnosis),
    (HDO.ClinicalMeasurement, DBR.Clinical_trial),
    (HDO.ChestPainType, DBR.Chest_pain),
    (HDO.ECGResult, DBR.Electrocardiography),
    (HDO.STSlope, DBR.ST_segment),
    
    # Datatype property concepts to related DBpedia articles
    (HDO.restingBP, DBR.Blood_pressure),
    (HDO.cholesterol, DBR.Cholesterol),
    (HDO.fastingBS, DBR.Blood_sugar_level),
    (HDO.maxHR, DBR.Heart_rate),
    (HDO.exerciseAngina, DBR.Angina_pectoris),
    (HDO.oldpeak, DBR.ST_segment),
    (HDO.age, DBR.Ageing),
    
    # Disease-specific links
    (HDO.hasHeartDisease, DBR.Cardiovascular_disease),
    (HDO.FixedDefect, DBR.Thalassemia),
    (HDO.ReversibleDefect, DBR.Thalassemia),
    (HDO.Upsloping, DBR.ST_segment),
    (HDO.FlatSlope, DBR.ST_segment),
    (HDO.Downsloping, DBR.ST_segment),
    (HDO.NonAnginalPain, DBR.Chest_pain),
    (HDO.Asymptomatic, DBR.Asymptomatic),
]

# Additional domain-specific links to enrich the knowledge graph
BROADER_LINKS = [
    # Link the ontology itself to the broader medical domain
    (URIRef("http://example.org/heart-disease-ontology"), RDFS.seeAlso, DBR.Cardiovascular_disease),
    (URIRef("http://example.org/heart-disease-ontology"), RDFS.seeAlso, DBR.Heart_disease),
    (URIRef("http://example.org/heart-disease-ontology"), RDFS.seeAlso, DBR.Cardiology),
    
    # Link dataset to source concepts
    (HDR["heart_disease_dataset"], RDFS.seeAlso, DBR.Heart_disease),
    (HDR["heart_disease_dataset"], DCT.subject, DBR.Cardiovascular_disease),
    (HDR["heart_disease_dataset"], DCT.subject, DBR.Machine_learning),
    (HDR["heart_disease_dataset"], DCT.subject, DBR.Medical_diagnosis),
]

# Wikidata links for broader interoperability
WIKIDATA_LINKS = [
    (HDO.Patient, OWL.sameAs, WIKIDATA.Q181600),         # Patient
    (HDO.ThalassemiaType, OWL.sameAs, WIKIDATA.Q192627), # Thalassemia
]


def add_dbpedia_links(g):
    """Add all DBpedia and external links to the graph."""
    link_count = 0
    
    # --- owl:sameAs links ---
    print("Adding owl:sameAs links...")
    for local_resource, dbpedia_resource in SAME_AS_LINKS:
        g.add((local_resource, OWL.sameAs, dbpedia_resource))
        link_count += 1
        print(f"  {local_resource.split('#')[-1] if '#' in local_resource else local_resource} "
              f"owl:sameAs {dbpedia_resource.split('/')[-1]}")
    
    # --- rdfs:seeAlso links ---
    print("\nAdding rdfs:seeAlso links...")
    for local_resource, dbpedia_resource in SEE_ALSO_LINKS:
        g.add((local_resource, RDFS.seeAlso, dbpedia_resource))
        link_count += 1
        local_name = local_resource.split('#')[-1] if '#' in local_resource else str(local_resource).split('/')[-1]
        print(f"  {local_name} rdfs:seeAlso {dbpedia_resource.split('/')[-1]}")
    
    # --- Broader/domain links ---
    print("\nAdding broader domain links...")
    for s, p, o in BROADER_LINKS:
        g.add((s, p, o))
        link_count += 1
    
    # --- Wikidata links ---
    print("\nAdding Wikidata links...")
    for s, p, o in WIKIDATA_LINKS:
        g.add((s, p, o))
        link_count += 1
    
    return link_count


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'output', 'heart_disease_data.ttl')
    output_path = os.path.join(base_dir, 'output', 'heart_disease_linked.ttl')
    
    if not os.path.exists(input_path):
        print(f"ERROR: 4-star RDF file not found at {input_path}")
        print("  Please run 'python scripts/csv_to_rdf.py' first.")
        sys.exit(1)
    
    # Load existing 4★ RDF data
    print(f"Loading 4-star RDF data from: {input_path}")
    g = Graph()
    g.parse(input_path, format="turtle")
    initial_triples = len(g)
    print(f"  Loaded {initial_triples} triples")
    
    # Bind namespaces
    g.bind("hdo", HDO)
    g.bind("hdr", HDR)
    g.bind("owl", OWL)
    g.bind("foaf", FOAF)
    g.bind("schema", SCHEMA)
    g.bind("dct", DCT)
    g.bind("dbr", DBR)
    g.bind("dbo", DBO)
    g.bind("dbp", DBP)
    g.bind("wikidata", WIKIDATA)
    
    # Add DBpedia links
    print(f"\n{'='*60}")
    print("  Linking to LOD Cloud (4-star -> 5-star)")
    print(f"{'='*60}\n")
    
    link_count = add_dbpedia_links(g)
    
    # Serialize to Turtle
    g.serialize(destination=output_path, format="turtle")
    
    final_triples = len(g)
    new_triples = final_triples - initial_triples
    
    print(f"\n{'='*60}")
    print(f"  DBpedia Linking Complete (4-star -> 5-star)")
    print(f"{'='*60}")
    print(f"  Original triples: {initial_triples}")
    print(f"  New link triples: {new_triples}")
    print(f"  Total triples: {final_triples}")
    print(f"  External links added: {link_count}")
    print(f"  Linked datasets: DBpedia, Wikidata")
    print(f"  Output: {output_path}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
