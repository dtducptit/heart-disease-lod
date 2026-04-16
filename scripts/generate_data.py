"""
Generate a realistic Heart Disease dataset based on the UCI Heart Disease schema.
This creates a CSV file with 303 records matching the Kaggle dataset format.

Columns: age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, target
"""

import csv
import random
import os

random.seed(42)

def generate_heart_data(n=303):
    """Generate realistic heart disease data."""
    records = []
    
    for i in range(n):
        # Determine if this patient has heart disease (roughly 45% positive)
        target = 1 if random.random() < 0.45 else 0
        
        # Age: 29-77, heart disease patients tend to be older
        if target == 1:
            age = random.randint(45, 77)
        else:
            age = random.randint(29, 70)
        
        # Sex: 1=male, 0=female (dataset is ~68% male)
        sex = 1 if random.random() < 0.68 else 0
        
        # Chest pain type: 0=typical angina, 1=atypical, 2=non-anginal, 3=asymptomatic
        if target == 1:
            cp = random.choices([0, 1, 2, 3], weights=[0.05, 0.10, 0.15, 0.70])[0]
        else:
            cp = random.choices([0, 1, 2, 3], weights=[0.30, 0.25, 0.30, 0.15])[0]
        
        # Resting blood pressure: 94-200 mm Hg
        if target == 1:
            trestbps = random.randint(110, 200)
        else:
            trestbps = random.randint(94, 170)
        
        # Serum cholesterol: 126-564 mg/dl
        if target == 1:
            chol = random.randint(175, 564)
        else:
            chol = random.randint(126, 400)
        
        # Fasting blood sugar > 120 mg/dl: 0=false, 1=true
        fbs = 1 if random.random() < 0.15 else 0
        
        # Resting ECG: 0=normal, 1=ST-T wave abnormality, 2=LVH
        if target == 1:
            restecg = random.choices([0, 1, 2], weights=[0.40, 0.45, 0.15])[0]
        else:
            restecg = random.choices([0, 1, 2], weights=[0.60, 0.30, 0.10])[0]
        
        # Maximum heart rate: 71-202
        if target == 1:
            thalach = random.randint(71, 165)
        else:
            thalach = random.randint(100, 202)
        
        # Exercise-induced angina: 0=no, 1=yes
        if target == 1:
            exang = 1 if random.random() < 0.55 else 0
        else:
            exang = 1 if random.random() < 0.15 else 0
        
        # Oldpeak (ST depression): 0.0-6.2
        if target == 1:
            oldpeak = round(random.uniform(0.5, 6.2), 1)
        else:
            oldpeak = round(random.uniform(0.0, 3.0), 1)
        
        # Slope: 0=upsloping, 1=flat, 2=downsloping
        if target == 1:
            slope = random.choices([0, 1, 2], weights=[0.10, 0.55, 0.35])[0]
        else:
            slope = random.choices([0, 1, 2], weights=[0.50, 0.35, 0.15])[0]
        
        # Number of major vessels colored by fluoroscopy: 0-3
        if target == 1:
            ca = random.choices([0, 1, 2, 3], weights=[0.25, 0.30, 0.25, 0.20])[0]
        else:
            ca = random.choices([0, 1, 2, 3], weights=[0.65, 0.20, 0.10, 0.05])[0]
        
        # Thalassemia: 1=normal, 2=fixed defect, 3=reversible defect
        if target == 1:
            thal = random.choices([1, 2, 3], weights=[0.15, 0.20, 0.65])[0]
        else:
            thal = random.choices([1, 2, 3], weights=[0.55, 0.10, 0.35])[0]
        
        records.append([age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, target])
    
    return records

def main():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'heart.csv')
    
    headers = ['age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal', 'target']
    records = generate_heart_data(303)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)
    
    # Print statistics
    total = len(records)
    positive = sum(1 for r in records if r[-1] == 1)
    print(f"Generated {total} records -> {output_file}")
    print(f"  Heart disease positive: {positive} ({positive/total*100:.1f}%)")
    print(f"  Heart disease negative: {total - positive} ({(total-positive)/total*100:.1f}%)")
    print(f"  Age range: {min(r[0] for r in records)}-{max(r[0] for r in records)}")
    print(f"  Male: {sum(1 for r in records if r[1]==1)}, Female: {sum(1 for r in records if r[1]==0)}")

if __name__ == '__main__':
    main()
