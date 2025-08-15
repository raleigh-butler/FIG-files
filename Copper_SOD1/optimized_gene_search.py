import csv
import json
import math
import os
import re
import requests
import time
from datetime import datetime
from collections import defaultdict, Counter
from tqdm import tqdm

# ------------------------
# Configuration
# ------------------------
BATCH_SIZE = 20
SLEEP_INTERVAL = 0.5
API_URL = "https://www.bv-brc.org/api/genome_feature/"
HEADERS = {"accept": "application/json"}
timestamp = datetime.now().strftime("%Y%m%d_%H%M")

# Role synonyms dictionary
role_synonyms = {
    "CopA": ["CopA", "copper-exporting ATPase"],
    "SodA": ["SodA", "superoxide dismutase [Mn]", "MnSOD"],
    "CsgA": ["CsgA", "Curli production component"]
    # Add more if needed
}

# Flatten the synonyms for search
all_roles = sorted(set(s for synonyms in role_synonyms.values() for s in synonyms))

# ------------------------
# Load Genomes
# ------------------------
def load_genomes(tsv_path):
    genomes = []
    with open(tsv_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if row.get("genome_id"):
                genomes.append(row["genome_id"])
    return genomes

# ------------------------
# Query BV-BRC API
# ------------------------
def query_bvbrc(genome_ids):
    query = f"in(genome_id,({','.join(genome_ids)}))"
    fields = "genome_id,product,start,end,strand"
    full_url = f"{API_URL}?http_accept=application/json&q={query}&select={fields}&limit=50000"

    try:
        response = requests.get(full_url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API error: {e}")
        return []

# ------------------------
# Match Products to Roles
# ------------------------
def match_role(product):
    for role, synonyms in role_synonyms.items():
        for term in synonyms:
            if re.search(rf"\b{re.escape(term)}\b", product, re.IGNORECASE):
                return role
    return None

# ------------------------
# Process All Genomes
# ------------------------
def process_all(genomes):
    role_hits = defaultdict(lambda: defaultdict(list))
    for i in tqdm(range(0, len(genomes), BATCH_SIZE), desc="Genome Batches"):
        batch = genomes[i:i + BATCH_SIZE]
        features = query_bvbrc(batch)
        for f in features:
            role = match_role(f.get("product", ""))
            if role:
                role_hits[f["genome_id"]][role].append(f)
        time.sleep(SLEEP_INTERVAL)
    return role_hits

# ------------------------
# Write Outputs
# ------------------------
def save_results(role_hits):
    os.makedirs(f"output_{timestamp}", exist_ok=True)

    # Save JSON
    with open(f"output_{timestamp}/detailed_hits.json", "w") as f:
        json.dump(role_hits, f, indent=2)

    # Save matrix
    with open(f"output_{timestamp}/role_matrix.csv", "w") as f:
        writer = csv.writer(f)
        header = ["genome_id"] + list(role_synonyms.keys())
        writer.writerow(header)
        for genome, roles in role_hits.items():
            row = [genome] + [1 if r in roles else 0 for r in role_synonyms.keys()]
            writer.writerow(row)

    # Print simple summary
    print("\nSummary Report")
    print("==============")
    role_counts = Counter(r for genome in role_hits for r in role_hits[genome])
    for role in sorted(role_synonyms):
        print(f"{role}: {role_counts[role]} genomes")

# ------------------------
# Main
# ------------------------
if __name__ == "__main__":
    print("Loading genomes...")
    genomes = load_genomes("reps_converted.tsv")
    print(f"Loaded {len(genomes)} genomes. Starting processing...\n")

    role_hits = process_all(genomes)
    save_results(role_hits)
    print("\nDone.")
