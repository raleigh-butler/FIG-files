
#!/usr/bin/env python3
"""
Full Genome 1-Term Test with Feature and Genome Flattening
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


def flatten_result(entry):
    base_fields = {
        "search_term": entry.get("search_term"),
        "genome_id": entry.get("genome_id"),
        "features_found": entry.get("features_found"),
        "success": entry.get("success"),
    }

    flattened_rows = []
    for idx, feature in enumerate(entry.get("features", []), 1):
        row = base_fields.copy()
        row.update({
            f"feature_{idx}_accession": feature.get("accession"),
            f"feature_{idx}_start": feature.get("start"),
            f"feature_{idx}_end": feature.get("end"),
            f"feature_{idx}_feature_type": feature.get("feature_type"),
            f"feature_{idx}_product": feature.get("product"),
        })
        flattened_rows.append(row)

    # If no features, at least preserve one row
    if not flattened_rows:
        flattened_rows.append(base_fields.copy())

    # Add genome_coverage columns
    for row in flattened_rows:
        for genome in entry.get("genome_coverage", []):
            row[f"genome_{genome}"] = True

    return flattened_rows


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

    test_terms = ['copA']
    total_terms = len(test_terms)
    all_raw_results = []

    print(f"\n🎯 Starting search with {total_terms} term across {len(genome_ids)} genomes")
    start_time = time.time()

    for i, term in enumerate(test_terms, 1):
        term_results = search_term_across_genomes(term, genome_ids, i, total_terms)
        all_raw_results.extend(term_results)

    total_time = time.time() - start_time
    print(f"✅ Data collection complete in {total_time:.1f} seconds")

    # Flatten and write to CSV
    flattened = []
    for entry in all_raw_results:
        flattened.extend(flatten_result(entry))

    if flattened:
        output_file = "genome_search_copA_flattened.csv"
        fieldnames = sorted(set().union(*(r.keys() for r in flattened)))
        with open(output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened)
        print(f"📁 Saved flattened result data to {output_file}")
        print(f"📦 Total feature rows: {len(flattened)}")
    else:
        print("⚠️ No results captured!")

    return {
        'execution_time': total_time,
        'total_results': len(flattened),
        'results': flattened
    }


def main():
    print("🧪 RUNNING 1-TERM FLATTENED TEST\n")
    try:
        result = test_1_term_all_genomes()
        print(f"\n✅ Test complete. Total results: {result['total_results']}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
