import requests
import pandas as pd

# Example genome IDs - replace with your actual list
genome_ids = ["1163385.3", "1203605.3", "1401685.3"]

# List of expanded search terms related to SOD1
search_terms = [
    "SOD1",
    "superoxide dismutase",
    "sodA",
    "sodB",
    "sodC"
]

# Initialize dataframe
df = pd.DataFrame(columns=["search_term"] + genome_ids)

# Populate DataFrame with initial False values
for term in search_terms:
    row = {"search_term": term}
    for gid in genome_ids:
        row[gid] = False
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

# Perform API queries
for search_term in search_terms:
    print(f"Searching for: {search_term}")

    # Use gene and product fields for better coverage
    query = f'gene:{search_term} OR product:{search_term}'

    response = requests.get(
        "https://www.bv-brc.org/api/genome_feature/",
        params={
            "http_accept": "application/json",
            "q": query,
            "select": "feature_id,genome_id,accession,annotation,product,gene,start,end,strand,patric_id",
            "limit": 25000
        }
    )

    if response.status_code != 200:
        print(f"API error: {response.status_code} for {search_term}")
        continue

    features = response.json()

    for feature in features:
        genome_id = feature.get("genome_id")
        if genome_id in genome_ids:
            df.loc[df["search_term"] == search_term, genome_id] = True

# Save results
df.to_csv("sod1_extended_search_results.csv", index=False)
print("Results saved to sod1_extended_search_results.csv")
