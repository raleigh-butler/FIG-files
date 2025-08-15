
#!/usr/bin/env python3
"""
Full Genome 1-Term Test - Normalized Feature Rows and Genome Coverage Columns
"""

import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from shared_utilities import bvbrc_utils


def search_term_across_genomes(term, genome_ids, term_index, total_terms, batch_size=25):
    results = []
    batches = [genome_ids[i:i + batch_size] for i in range(0, len(genome_ids), batch_size)]

    print(f"🔍 Term {term_index}/{total_terms}: {term} — {len(batches)} genome batches")

    def search_batch(i, batch):
        start = i * batch_size
        end = min(start + batch_size, len(genome_ids))
        print(f"   🔄 Batch {i+1}/{len(batches)} — Genomes {start+1}-{end}")
        return bvbrc_utils.batch_search_across_genomes(
            search_terms=[term],
            genome_ids=batch,
            search_type='gene',
            track_name="Full_Genome_1_Term_Test"
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_batch, i, batch) for i, batch in enumerate(batches)]
        for future in as_completed(futures):
            results.extend(future.result())

    return results


def normalize_results(results):
    normalized = []
    all_coverage_genomes = set()

    # First pass to collect all genome_coverage keys
    for entry in results:
        all_coverage_genomes.update(entry.get("genome_coverage", []))

    for entry in results:
        base = {
            "search_term": entry.get("search_term"),
            "genome_id": entry.get("genome_id"),
        }

        features = entry.get("features", [])
        if features:
            for i, feat in enumerate(features):
                row = base.copy()
                row.update({
                    "accession": feat.get("accession"),
                    "start": feat.get("start"),
                    "end": feat.get("end"),
                    "feature_type": feat.get("feature_type"),
                    "product": feat.get("product"),
                })
                # Add genome_coverage flags
                for genome in all_coverage_genomes:
                    row[f"genome_coverage_{genome}"] = genome in entry.get("genome_coverage", [])
                normalized.append(row)
        else:
            row = base.copy()
            row.update({
                "accession": None,
                "start": None,
                "end": None,
                "feature_type": None,
                "product": None,
            })
            for genome in all_coverage_genomes:
                row[f"genome_coverage_{genome}"] = genome in entry.get("genome_coverage", [])
            normalized.append(row)

    return normalized


def test_1_term_all_genomes():
    print("🚀 FULL GENOME 1-TERM DATA COLLECTION")
    print("="*60)

    print("📖 Loading ALL representative genomes...")
    start_load_time = time.time()
    genomes = bvbrc_utils.load_representative_genomes(limit=None)
    genome_ids = list(genomes.keys())
    load_time = time.time() - start_load_time

    if not genome_ids:
        print("❌ No genomes loaded")
        return

    print(f"✅ Loaded {len(genome_ids)} genomes in {load_time:.1f} seconds")
    print(f"📊 Sample genomes: {genome_ids[:3]}...")

    test_terms = ['sod1']
    total_terms = len(test_terms)
    all_raw_results = []

    print(f"\n🎯 Starting search with {total_terms} term across {len(genome_ids)} genomes")
    start_time = time.time()

    for i, term in enumerate(test_terms, 1):
        term_results = search_term_across_genomes(term, genome_ids, i, total_terms)
        all_raw_results.extend(term_results)

    total_time = time.time() - start_time
    print(f"✅ Data collection complete in {total_time:.1f} seconds")

    normalized = normalize_results(all_raw_results)

    if normalized:
        output_file = "genome_search_sod1_normalized.csv"
        
        # Reorder fieldnames: search_term first, then metadata, then genomes
        first_column = ["search_term"]
        genome_columns = [k for k in normalized[0].keys() if k.startswith("genome_coverage_")]
        renamed_genome_columns = {g: g.replace("genome_coverage_", "") for g in genome_columns}
        metadata_columns = [k for k in normalized[0].keys() if k not in first_column + genome_columns]
        fieldnames = first_column + metadata_columns + list(renamed_genome_columns.values())

        # Rename genome coverage keys in each row
        for row in normalized:
            for old_key, new_key in renamed_genome_columns.items():
                row[new_key] = row.pop(old_key)
    
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized)
        print(f"📁 Saved normalized result data to {output_file}")
        print(f"📦 Total feature rows: {len(normalized)}")
    else:
        print("⚠️ No results captured!")

    return {
        'execution_time': total_time,
        'total_results': len(normalized),
        'results': normalized
    }


def main():
    print("🧪 RUNNING 1-TERM NORMALIZED TEST\n")
    try:
        result = test_1_term_all_genomes()
        print(f"\n✅ Test complete. Total results: {result['total_results']}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
