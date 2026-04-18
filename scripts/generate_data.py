"""
Healthcare Dataset Generator
==============================
Generates a synthetic healthcare dataset matching the Kaggle Healthcare Dataset
schema (prasad22). Creates realistic patient admission records.

Output: data/healthcare.csv
Columns: Name, Age, Gender, Blood Type, Medical Condition, Date of Admission,
         Doctor, Hospital, Insurance Provider, Billing Amount, Room Number,
         Admission Type, Discharge Date, Medication, Test Results
"""

import os
import csv
import random
from datetime import datetime, timedelta

# Seed for reproducibility
random.seed(42)

# ============================================================================
# Data pools
# ============================================================================
FIRST_NAMES_MALE = [
    "James", "Robert", "John", "Michael", "David", "William", "Richard",
    "Joseph", "Thomas", "Christopher", "Daniel", "Matthew", "Anthony",
    "Mark", "Steven", "Andrew", "Paul", "Joshua", "Kenneth", "Kevin",
    "Brian", "George", "Timothy", "Ronald", "Edward", "Jason", "Jeffrey",
    "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen",
    "Larry", "Justin", "Scott", "Brandon", "Benjamin", "Samuel"
]

FIRST_NAMES_FEMALE = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Lisa", "Nancy", "Betty",
    "Margaret", "Sandra", "Ashley", "Dorothy", "Kimberly", "Emily",
    "Donna", "Michelle", "Carol", "Amanda", "Melissa", "Deborah",
    "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia", "Kathleen",
    "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Emma",
    "Nicole", "Helen"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts"
]

DOCTOR_FIRST = [
    "Matthew", "Sarah", "James", "Emily", "Robert", "Jessica", "William",
    "Amanda", "David", "Laura", "Michael", "Jennifer", "Christopher",
    "Elizabeth", "Daniel", "Megan", "Andrew", "Samantha", "Patrick", "Nicole"
]

DOCTOR_LAST = [
    "Smith", "Lee", "Williams", "Brown", "Taylor", "Johnson", "Wilson",
    "Clark", "Anderson", "Thomas", "Garcia", "Martinez", "Robinson",
    "White", "Harris", "Lewis", "Walker", "Young", "King", "Wright"
]

HOSPITALS = [
    "Smith Medical Center", "Johnson Hospital", "Williams General",
    "Brown Healthcare", "Jones Memorial", "Garcia Medical",
    "Miller Children's Hospital", "Davis University Hospital",
    "Rodriguez Medical Center", "Martinez Health System",
    "Wilson Regional Medical", "Anderson Community Hospital",
    "Thomas General Hospital", "Taylor Medical Center",
    "Moore Memorial Hospital", "Jackson Health System",
    "Lee Medical Center", "Harris Hospital", "Clark Medical",
    "Lewis Health Center"
]

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
MEDICAL_CONDITIONS = ["Diabetes", "Hypertension", "Asthma", "Arthritis", "Cancer", "Obesity"]
INSURANCE_PROVIDERS = ["Aetna", "Blue Cross", "Cigna", "UnitedHealthcare", "Medicare"]
ADMISSION_TYPES = ["Emergency", "Elective", "Urgent"]
MEDICATIONS = ["Aspirin", "Ibuprofen", "Penicillin", "Paracetamol", "Lipitor"]
TEST_RESULTS = ["Normal", "Abnormal", "Inconclusive"]

GENDERS = ["Male", "Female"]


def generate_record(record_id):
    """Generate a single patient admission record."""
    gender = random.choice(GENDERS)

    if gender == "Male":
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_FEMALE)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"

    age = random.randint(18, 85)
    blood_type = random.choice(BLOOD_TYPES)
    condition = random.choice(MEDICAL_CONDITIONS)

    # Admission date within the last 3 years
    start_date = datetime(2023, 1, 1)
    random_days = random.randint(0, 1095)
    admission_date = start_date + timedelta(days=random_days)

    # Stay duration: 1-30 days
    stay_days = random.randint(1, 30)
    discharge_date = admission_date + timedelta(days=stay_days)

    doc_first = random.choice(DOCTOR_FIRST)
    doc_last = random.choice(DOCTOR_LAST)
    doctor = f"Dr. {doc_first} {doc_last}"

    hospital = random.choice(HOSPITALS)
    insurance = random.choice(INSURANCE_PROVIDERS)
    billing = round(random.uniform(1000.0, 50000.0), 2)
    room = random.randint(100, 500)
    admission_type = random.choice(ADMISSION_TYPES)
    medication = random.choice(MEDICATIONS)
    test_result = random.choice(TEST_RESULTS)

    return [
        name, age, gender, blood_type, condition,
        admission_date.strftime("%Y-%m-%d"), doctor, hospital,
        insurance, billing, room, admission_type,
        discharge_date.strftime("%Y-%m-%d"), medication, test_result
    ]


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'healthcare.csv')

    headers = [
        "Name", "Age", "Gender", "Blood Type", "Medical Condition",
        "Date of Admission", "Doctor", "Hospital", "Insurance Provider",
        "Billing Amount", "Room Number", "Admission Type",
        "Discharge Date", "Medication", "Test Results"
    ]

    num_records = 500
    records = [generate_record(i) for i in range(num_records)]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)

    # Statistics
    conditions = {}
    for r in records:
        c = r[4]
        conditions[c] = conditions.get(c, 0) + 1

    print(f"Generated {num_records} records -> {output_file}")
    print(f"  Age range: {min(r[1] for r in records)}-{max(r[1] for r in records)}")
    print(f"  Male: {sum(1 for r in records if r[2] == 'Male')}")
    print(f"  Female: {sum(1 for r in records if r[2] == 'Female')}")
    print(f"  Medical conditions:")
    for c, count in sorted(conditions.items()):
        print(f"    {c}: {count}")


if __name__ == '__main__':
    main()
