"""
DBpedia Linking Script for Healthcare LOD
==========================================
Establishes links between local RDF data and the LOD Cloud (DBpedia/Wikidata)
to achieve 5-star Linked Open Data status.

Input:  output/healthcare_data.ttl (4-star)
Output: output/healthcare_linked.ttl (5-star)
"""

import os
import sys
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, FOAF

# ============================================================================
# Namespace Definitions
# ============================================================================
HCO = Namespace("http://example.org/healthcare-ontology#")
HCD = Namespace("http://example.org/healthcare-data/")
SCHEMA = Namespace("http://schema.org/")
DCT = Namespace("http://purl.org/dc/terms/")
DBR = Namespace("http://dbpedia.org/resource/")
DBO = Namespace("http://dbpedia.org/ontology/")
DBP = Namespace("http://dbpedia.org/property/")
WIKIDATA = Namespace("http://www.wikidata.org/entity/")

# ============================================================================
# Link Definitions
# ============================================================================

# owl:sameAs links - identical concepts
SAME_AS_LINKS = [
    # Medical Conditions
    (HCO.Diabetes, DBR.Diabetes),
    (HCO.Hypertension, DBR.Hypertension),
    (HCO.Asthma, DBR.Asthma),
    (HCO.Arthritis, DBR.Arthritis),
    (HCO.Cancer, DBR.Cancer),
    (HCO.Obesity, DBR.Obesity),

    # Medications
    (HCO.Aspirin, DBR.Aspirin),
    (HCO.Ibuprofen, DBR.Ibuprofen),
    (HCO.Penicillin, DBR.Penicillin),
    (HCO.Paracetamol, DBR.Paracetamol),
    (HCO.Lipitor, DBR.Atorvastatin),  # Lipitor = brand name for Atorvastatin
]

# rdfs:seeAlso links - related concepts
SEE_ALSO_LINKS = [
    # Classes
    (HCO.Patient, DBR.Patient),
    (HCO.Hospital, DBR.Hospital),
    (HCO.Doctor, DBR.Physician),
    (HCO.Admission, DBR.Hospital_admission),
    (HCO.InsuranceProvider, DBR.Health_insurance),
    (HCO.MedicalCondition, DBR.Disease),
    (HCO.Medication, DBR.Medication),
    (HCO.TestResult, DBR.Medical_test),
    (HCO.BloodType, DBR.Blood_type),

    # Admission types
    (HCO.Emergency, DBR.Emergency_department),
    (HCO.Elective, DBR.Elective_surgery),
    (HCO.Urgent, DBR.Urgent_care),

    # Properties
    (HCO.billingAmount, DBR.Medical_billing),
    (HCO.age, DBR.Ageing),
    (HCO.gender, DBR.Gender),
]

# Broader domain links
BROADER_LINKS = [
    (URIRef("http://example.org/healthcare-ontology"), RDFS.seeAlso, DBR.Healthcare),
    (URIRef("http://example.org/healthcare-ontology"), RDFS.seeAlso, DBR.Health_informatics),
    (URIRef("http://example.org/healthcare-ontology"), RDFS.seeAlso, DBR.Electronic_health_record),

    (HCD["healthcare_dataset"], RDFS.seeAlso, DBR.Healthcare),
    (HCD["healthcare_dataset"], DCT.subject, DBR.Health_informatics),
    (HCD["healthcare_dataset"], DCT.subject, DBR.Machine_learning),
    (HCD["healthcare_dataset"], DCT.subject, DBR.Medical_diagnosis),
]

# Wikidata links
WIKIDATA_LINKS = [
    (HCO.Patient, OWL.sameAs, WIKIDATA.Q181600),       # Patient
    (HCO.Hospital, OWL.sameAs, WIKIDATA.Q16917),        # Hospital
    (HCO.Diabetes, OWL.sameAs, WIKIDATA.Q12206),        # Diabetes mellitus
    (HCO.Hypertension, OWL.sameAs, WIKIDATA.Q41861),    # Hypertension
    (HCO.Asthma, OWL.sameAs, WIKIDATA.Q35869),          # Asthma
    (HCO.Aspirin, OWL.sameAs, WIKIDATA.Q18216),         # Aspirin
]


def add_external_links(g):
    """Add all DBpedia and Wikidata links to the graph."""
    link_count = 0

    print("Adding owl:sameAs links...")
    for local, external in SAME_AS_LINKS:
        g.add((local, OWL.sameAs, external))
        link_count += 1
        local_name = local.split('#')[-1] if '#' in local else str(local).split('/')[-1]
        ext_name = external.split('/')[-1]
        print(f"  {local_name} owl:sameAs {ext_name}")

    print("\nAdding rdfs:seeAlso links...")
    for local, external in SEE_ALSO_LINKS:
        g.add((local, RDFS.seeAlso, external))
        link_count += 1
        local_name = local.split('#')[-1] if '#' in local else str(local).split('/')[-1]
        print(f"  {local_name} rdfs:seeAlso {external.split('/')[-1]}")

    print("\nAdding broader domain links...")
    for s, p, o in BROADER_LINKS:
        g.add((s, p, o))
        link_count += 1

    print("\nAdding Wikidata links...")
    for s, p, o in WIKIDATA_LINKS:
        g.add((s, p, o))
        link_count += 1

    return link_count


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'output', 'healthcare_data.ttl')
    output_path = os.path.join(base_dir, 'output', 'healthcare_linked.ttl')

    if not os.path.exists(input_path):
        print(f"ERROR: 4-star RDF file not found at {input_path}")
        print("  Please run 'python scripts/csv_to_rdf.py' first.")
        sys.exit(1)

    print(f"Loading 4-star RDF data from: {input_path}")
    g = Graph()
    g.parse(input_path, format="turtle")
    initial_triples = len(g)
    print(f"  Loaded {initial_triples} triples")

    # Bind namespaces
    g.bind("hco", HCO)
    g.bind("hcd", HCD)
    g.bind("owl", OWL)
    g.bind("foaf", FOAF)
    g.bind("schema", SCHEMA)
    g.bind("dct", DCT)
    g.bind("dbr", DBR)
    g.bind("dbo", DBO)
    g.bind("dbp", DBP)
    g.bind("wikidata", WIKIDATA)

    print(f"\n{'='*60}")
    print("  Linking to LOD Cloud (4-star -> 5-star)")
    print(f"{'='*60}\n")

    link_count = add_external_links(g)

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
