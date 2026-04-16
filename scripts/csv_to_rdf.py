"""
CSV to RDF Converter for Heart Disease Dataset
================================================
Converts 3-star CSV data into 4-star RDF/Turtle format by mapping each row
to the Heart Disease Ontology (hdo:) defined in ontology/heart_disease_ontology.ttl.

Input:  data/heart.csv (3★ - Open format CSV)
Output: output/heart_disease_data.ttl (4★ - RDF with URIs and W3C standards)
"""

import os
import sys
import pandas as pd
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, OWL, XSD, FOAF

# ============================================================================
# Namespace Definitions
# ============================================================================
HDO = Namespace("http://example.org/heart-disease-ontology#")
HDR = Namespace("http://example.org/heart-disease-data/")  # Data instances
SCHEMA = Namespace("http://schema.org/")
DCT = Namespace("http://purl.org/dc/terms/")
DBR = Namespace("http://dbpedia.org/resource/")
DBO = Namespace("http://dbpedia.org/ontology/")

# ============================================================================
# Value Mappings (CSV encoded values → Ontology named individuals)
# ============================================================================
CHEST_PAIN_MAP = {
    0: HDO.TypicalAngina,
    1: HDO.AtypicalAngina,
    2: HDO.NonAnginalPain,
    3: HDO.Asymptomatic
}

ECG_MAP = {
    0: HDO.NormalECG,
    1: HDO.STTWaveAbnormality,
    2: HDO.LeftVentricularHypertrophy
}

SLOPE_MAP = {
    0: HDO.Upsloping,
    1: HDO.FlatSlope,
    2: HDO.Downsloping
}

THAL_MAP = {
    1: HDO.NormalThal,
    2: HDO.FixedDefect,
    3: HDO.ReversibleDefect
}

SEX_MAP = {
    0: "Female",
    1: "Male"
}


def create_rdf_graph():
    """Initialize an RDF graph with namespace bindings."""
    g = Graph()
    g.bind("hdo", HDO)
    g.bind("hdr", HDR)
    g.bind("owl", OWL)
    g.bind("foaf", FOAF)
    g.bind("schema", SCHEMA)
    g.bind("dct", DCT)
    g.bind("dbr", DBR)
    g.bind("dbo", DBO)
    return g


def add_patient_to_graph(g, row, patient_id):
    """
    Map a single CSV row to RDF triples following the Heart Disease Ontology.
    
    Creates three linked resources per patient:
    1. Patient (hdr:patient_{id})
    2. ClinicalMeasurement (hdr:measurement_{id})
    3. Diagnosis (hdr:diagnosis_{id})
    """
    # --- Create URIs ---
    patient_uri = HDR[f"patient_{patient_id}"]
    measurement_uri = HDR[f"measurement_{patient_id}"]
    diagnosis_uri = HDR[f"diagnosis_{patient_id}"]
    
    # --- Patient ---
    g.add((patient_uri, RDF.type, HDO.Patient))
    g.add((patient_uri, RDFS.label, Literal(f"Patient {patient_id}", lang="en")))
    g.add((patient_uri, HDO.patientId, Literal(patient_id, datatype=XSD.integer)))
    g.add((patient_uri, HDO.age, Literal(int(row['age']), datatype=XSD.integer)))
    g.add((patient_uri, HDO.sex, Literal(SEX_MAP.get(int(row['sex']), "Unknown"), datatype=XSD.string)))
    
    # Chest Pain Type (Object Property → Named Individual)
    cp_value = int(row['cp'])
    if cp_value in CHEST_PAIN_MAP:
        g.add((patient_uri, HDO.hasChestPainType, CHEST_PAIN_MAP[cp_value]))
    
    # Thalassemia (Object Property → Named Individual)
    thal_value = int(row['thal'])
    if thal_value in THAL_MAP:
        g.add((patient_uri, HDO.hasThalassemia, THAL_MAP[thal_value]))
    
    # --- Clinical Measurement ---
    g.add((measurement_uri, RDF.type, HDO.ClinicalMeasurement))
    g.add((measurement_uri, RDFS.label, Literal(f"Clinical Measurement for Patient {patient_id}", lang="en")))
    g.add((patient_uri, HDO.hasMeasurement, measurement_uri))
    
    # Datatype Properties
    g.add((measurement_uri, HDO.restingBP, Literal(int(row['trestbps']), datatype=XSD.integer)))
    g.add((measurement_uri, HDO.cholesterol, Literal(int(row['chol']), datatype=XSD.integer)))
    g.add((measurement_uri, HDO.fastingBS, Literal(bool(int(row['fbs'])), datatype=XSD.boolean)))
    g.add((measurement_uri, HDO.maxHR, Literal(int(row['thalach']), datatype=XSD.integer)))
    g.add((measurement_uri, HDO.exerciseAngina, Literal(bool(int(row['exang'])), datatype=XSD.boolean)))
    g.add((measurement_uri, HDO.oldpeak, Literal(float(row['oldpeak']), datatype=XSD.float)))
    g.add((measurement_uri, HDO.numMajorVessels, Literal(int(row['ca']), datatype=XSD.integer)))
    
    # ECG Result (Object Property → Named Individual)
    ecg_value = int(row['restecg'])
    if ecg_value in ECG_MAP:
        g.add((measurement_uri, HDO.hasECGResult, ECG_MAP[ecg_value]))
    
    # ST Slope (Object Property → Named Individual)
    slope_value = int(row['slope'])
    if slope_value in SLOPE_MAP:
        g.add((measurement_uri, HDO.hasSTSlope, SLOPE_MAP[slope_value]))
    
    # --- Diagnosis ---
    g.add((diagnosis_uri, RDF.type, HDO.Diagnosis))
    g.add((diagnosis_uri, RDFS.label, Literal(f"Diagnosis for Patient {patient_id}", lang="en")))
    g.add((patient_uri, HDO.hasDiagnosis, diagnosis_uri))
    g.add((diagnosis_uri, HDO.hasHeartDisease, Literal(bool(int(row['target'])), datatype=XSD.boolean)))


def convert_csv_to_rdf(csv_path, output_path):
    """
    Main conversion function: reads CSV, maps to ontology, outputs RDF/Turtle.
    
    Parameters:
        csv_path (str): Path to input heart.csv
        output_path (str): Path to output .ttl file
    """
    print(f"Reading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} records with columns: {list(df.columns)}")
    
    # Create RDF graph
    g = create_rdf_graph()
    
    # Import ontology reference
    ontology_uri = URIRef("http://example.org/heart-disease-ontology")
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    
    # Add dataset metadata
    dataset_uri = HDR["heart_disease_dataset"]
    g.add((dataset_uri, RDF.type, SCHEMA.Dataset))
    g.add((dataset_uri, RDFS.label, Literal("Heart Disease Prediction Dataset", lang="en")))
    g.add((dataset_uri, DCT.source, Literal("UCI Machine Learning Repository / Kaggle", datatype=XSD.string)))
    g.add((dataset_uri, DCT.description, 
           Literal("Heart disease clinical dataset with 14 attributes per patient, converted to RDF/Turtle format as part of a Linked Open Data application.", lang="en")))
    g.add((dataset_uri, DCT.created, Literal("2026-04-17", datatype=XSD.date)))
    g.add((dataset_uri, SCHEMA.numberOfItems, Literal(len(df), datatype=XSD.integer)))
    
    # Convert each row
    for idx, row in df.iterrows():
        patient_id = idx + 1
        add_patient_to_graph(g, row, patient_id)
    
    # Serialize to Turtle
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    g.serialize(destination=output_path, format="turtle")
    
    # Report statistics
    num_triples = len(g)
    num_patients = len(df)
    num_positive = int(df['target'].sum())
    
    print(f"\n{'='*60}")
    print(f"  CSV -> RDF Conversion Complete (3-star -> 4-star)")
    print(f"{'='*60}")
    print(f"  Total triples generated: {num_triples}")
    print(f"  Total patients: {num_patients}")
    print(f"  Heart disease positive: {num_positive}")
    print(f"  Heart disease negative: {num_patients - num_positive}")
    print(f"  Output: {output_path}")
    print(f"{'='*60}")
    
    return g


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'data', 'heart.csv')
    output_path = os.path.join(base_dir, 'output', 'heart_disease_data.ttl')
    
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        print("  Please run 'python scripts/generate_data.py' first to create the dataset.")
        sys.exit(1)
    
    convert_csv_to_rdf(csv_path, output_path)


if __name__ == '__main__':
    main()
