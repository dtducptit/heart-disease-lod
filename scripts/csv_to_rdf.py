"""
CSV to RDF Converter for Healthcare Dataset
=============================================
Converts 3-star CSV data into 4-star RDF/Turtle format by mapping each row
to the Healthcare Ontology (hco:).

Input:  data/healthcare.csv (3-star)
Output: output/healthcare_data.ttl (4-star)
"""

import os
import sys
import re
import pandas as pd
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

# ============================================================================
# Value Mappings
# ============================================================================
BLOOD_TYPE_MAP = {
    "A+": HCO.BloodType_Apos, "A-": HCO.BloodType_Aneg,
    "B+": HCO.BloodType_Bpos, "B-": HCO.BloodType_Bneg,
    "AB+": HCO.BloodType_ABpos, "AB-": HCO.BloodType_ABneg,
    "O+": HCO.BloodType_Opos, "O-": HCO.BloodType_Oneg,
}

CONDITION_MAP = {
    "Diabetes": HCO.Diabetes, "Hypertension": HCO.Hypertension,
    "Asthma": HCO.Asthma, "Arthritis": HCO.Arthritis,
    "Cancer": HCO.Cancer, "Obesity": HCO.Obesity,
}

ADMISSION_TYPE_MAP = {
    "Emergency": HCO.Emergency, "Elective": HCO.Elective, "Urgent": HCO.Urgent,
}

MEDICATION_MAP = {
    "Aspirin": HCO.Aspirin, "Ibuprofen": HCO.Ibuprofen,
    "Penicillin": HCO.Penicillin, "Paracetamol": HCO.Paracetamol,
    "Lipitor": HCO.Lipitor,
}

TEST_RESULT_MAP = {
    "Normal": HCO.NormalResult, "Abnormal": HCO.AbnormalResult,
    "Inconclusive": HCO.InconclusiveResult,
}


def sanitize_uri(name):
    """Convert a name string to a valid URI fragment."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name.strip()).strip('_')


def create_rdf_graph():
    """Initialize an RDF graph with namespace bindings."""
    g = Graph()
    g.bind("hco", HCO)
    g.bind("hcd", HCD)
    g.bind("owl", OWL)
    g.bind("foaf", FOAF)
    g.bind("schema", SCHEMA)
    g.bind("dct", DCT)
    g.bind("dbr", DBR)
    g.bind("dbo", DBO)
    return g


def add_record_to_graph(g, row, record_id, doctors_added, hospitals_added, insurers_added):
    """Map a single CSV row to RDF triples."""
    patient_uri = HCD[f"patient_{record_id}"]
    admission_uri = HCD[f"admission_{record_id}"]

    # --- Patient ---
    g.add((patient_uri, RDF.type, HCO.Patient))
    g.add((patient_uri, RDFS.label, Literal(f"Patient {record_id}: {row['Name']}", lang="en")))
    g.add((patient_uri, HCO.patientName, Literal(str(row['Name']), datatype=XSD.string)))
    g.add((patient_uri, HCO.age, Literal(int(row['Age']), datatype=XSD.integer)))
    g.add((patient_uri, HCO.gender, Literal(str(row['Gender']), datatype=XSD.string)))

    # Blood Type
    bt = str(row['Blood Type'])
    if bt in BLOOD_TYPE_MAP:
        g.add((patient_uri, HCO.hasBloodType, BLOOD_TYPE_MAP[bt]))

    # --- Doctor (reuse URI if same name) ---
    doctor_name = str(row['Doctor'])
    doctor_key = sanitize_uri(doctor_name)
    doctor_uri = HCD[f"doctor_{doctor_key}"]
    if doctor_key not in doctors_added:
        g.add((doctor_uri, RDF.type, HCO.Doctor))
        g.add((doctor_uri, RDFS.label, Literal(doctor_name, lang="en")))
        g.add((doctor_uri, HCO.doctorName, Literal(doctor_name, datatype=XSD.string)))
        doctors_added.add(doctor_key)

    # --- Hospital (reuse URI if same name) ---
    hospital_name = str(row['Hospital'])
    hospital_key = sanitize_uri(hospital_name)
    hospital_uri = HCD[f"hospital_{hospital_key}"]
    if hospital_key not in hospitals_added:
        g.add((hospital_uri, RDF.type, HCO.Hospital))
        g.add((hospital_uri, RDFS.label, Literal(hospital_name, lang="en")))
        g.add((hospital_uri, HCO.hospitalName, Literal(hospital_name, datatype=XSD.string)))
        hospitals_added.add(hospital_key)

    # --- Insurance Provider (reuse URI) ---
    insurance_name = str(row['Insurance Provider'])
    insurance_key = sanitize_uri(insurance_name)
    insurance_uri = HCD[f"insurance_{insurance_key}"]
    if insurance_key not in insurers_added:
        g.add((insurance_uri, RDF.type, HCO.InsuranceProvider))
        g.add((insurance_uri, RDFS.label, Literal(insurance_name, lang="en")))
        insurers_added.add(insurance_key)
    g.add((patient_uri, HCO.hasInsurance, insurance_uri))

    # --- Admission ---
    g.add((admission_uri, RDF.type, HCO.Admission))
    g.add((admission_uri, RDFS.label, Literal(f"Admission {record_id}", lang="en")))
    g.add((patient_uri, HCO.hasAdmission, admission_uri))
    g.add((admission_uri, HCO.attendedBy, doctor_uri))
    g.add((admission_uri, HCO.admittedTo, hospital_uri))

    # Dates
    g.add((admission_uri, HCO.dateOfAdmission, Literal(str(row['Date of Admission']), datatype=XSD.date)))
    g.add((admission_uri, HCO.dischargeDate, Literal(str(row['Discharge Date']), datatype=XSD.date)))

    # Billing
    g.add((admission_uri, HCO.billingAmount, Literal(float(row['Billing Amount']), datatype=XSD.float)))
    g.add((admission_uri, HCO.roomNumber, Literal(int(row['Room Number']), datatype=XSD.integer)))

    # Medical Condition
    condition = str(row['Medical Condition'])
    if condition in CONDITION_MAP:
        g.add((admission_uri, HCO.hasMedicalCondition, CONDITION_MAP[condition]))

    # Admission Type
    adm_type = str(row['Admission Type'])
    if adm_type in ADMISSION_TYPE_MAP:
        g.add((admission_uri, HCO.hasAdmissionType, ADMISSION_TYPE_MAP[adm_type]))

    # Medication
    med = str(row['Medication'])
    if med in MEDICATION_MAP:
        g.add((admission_uri, HCO.prescribedMedication, MEDICATION_MAP[med]))

    # Test Result
    result = str(row['Test Results'])
    if result in TEST_RESULT_MAP:
        g.add((admission_uri, HCO.hasTestResult, TEST_RESULT_MAP[result]))


def convert_csv_to_rdf(csv_path, output_path):
    """Main conversion function."""
    print(f"Reading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} records with columns: {list(df.columns)}")

    g = create_rdf_graph()

    # Ontology reference
    ontology_uri = URIRef("http://example.org/healthcare-ontology")
    g.add((ontology_uri, RDF.type, OWL.Ontology))

    # Dataset metadata
    dataset_uri = HCD["healthcare_dataset"]
    g.add((dataset_uri, RDF.type, SCHEMA.Dataset))
    g.add((dataset_uri, RDFS.label, Literal("Healthcare Dataset", lang="en")))
    g.add((dataset_uri, DCT.source, Literal("Kaggle - prasad22/healthcare-dataset", datatype=XSD.string)))
    g.add((dataset_uri, DCT.description,
           Literal("Synthetic healthcare dataset with patient admissions, medical conditions, medications, and test results, converted to RDF/Turtle as 5-star Linked Open Data.", lang="en")))
    g.add((dataset_uri, DCT.created, Literal("2026-04-17", datatype=XSD.date)))
    g.add((dataset_uri, SCHEMA.numberOfItems, Literal(len(df), datatype=XSD.integer)))

    # Track unique entities
    doctors_added = set()
    hospitals_added = set()
    insurers_added = set()

    for idx, row in df.iterrows():
        record_id = idx + 1
        add_record_to_graph(g, row, record_id, doctors_added, hospitals_added, insurers_added)

    # Serialize
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")

    num_triples = len(g)
    print(f"\n{'='*60}")
    print(f"  CSV -> RDF Conversion Complete (3-star -> 4-star)")
    print(f"{'='*60}")
    print(f"  Total triples generated: {num_triples}")
    print(f"  Total patients: {len(df)}")
    print(f"  Unique doctors: {len(doctors_added)}")
    print(f"  Unique hospitals: {len(hospitals_added)}")
    print(f"  Output: {output_path}")
    print(f"{'='*60}")

    return g


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'data', 'healthcare_dataset.csv')
    if len(sys.argv) > 1:
        csv_path = os.path.abspath(sys.argv[1])
    output_path = os.path.join(base_dir, 'output', 'healthcare_data.ttl')

    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        print("  Please run 'python scripts/generate_data.py' first.")
        sys.exit(1)

    convert_csv_to_rdf(csv_path, output_path)


if __name__ == '__main__':
    main()
