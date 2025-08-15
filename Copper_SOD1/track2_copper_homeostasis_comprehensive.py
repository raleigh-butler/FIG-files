#!/usr/bin/env python3
"""
TRACK 2: Copper Homeostasis Comprehensive Search
Searches ALL representative genomes for 54 copper homeostasis-related terms.

Focus: Bacterial copper sequestration mechanisms affecting bioavailability.
Terms: 36 gene terms + 18 functional terms = 54 total
Expected runtime: 45-90 minutes
"""

import time
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from shared_utilities import bvbrc_utils


def print_progress_bar(current, total, start_time, prefix="Progress"):
    """Print a progress bar with timing estimates"""
    percent = (current / total) * 100
    elapsed = time.time() - start_time
    
    if current > 0:
        avg_time_per_item = elapsed / current
        eta = (total - current) * avg_time_per_item
        eta_str = f", ETA: {eta/60:.1f}m"
    else:
        eta_str = ""
    
    # Create visual progress bar
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\\r{prefix}: |{bar}| {current}/{total} ({percent:.1f}%) [{elapsed/60:.1f}m elapsed{eta_str}]", end='', flush=True)
    
    if current == total:
        print()  # New line when complete


def save_comprehensive_results(all_results, output_filename):
    """Save results in Alpha-Synuclein format with full BV-BRC metadata"""
    all_detailed_features = []
    
    # Process all results to extract individual features
    for result in all_results:
        search_term = result.get('search_term', 'Unknown')
        success = result.get('success', False)
        
        if success and result.get('features'):
            # Extract each individual feature with full metadata
            for feature in result['features']:
                # Extract genome_id from accession if available
                accession = feature.get('accession', '')
                genome_id = accession.split('_')[0] if '_' in accession else result.get('genome_id', 'Unknown')
                
                feature_row = {
                    'search_term': search_term,
                    'genome_id': genome_id,
                    'success': 'TRUE',
                    'count': 1,  # Each row represents one feature
                    'error': '',
                    'accession': feature.get('accession', ''),
                    'patric_id': feature.get('patric_id', ''),  # Include if available
                    'product': feature.get('product', ''),
                    'start': feature.get('start', ''),
                    'end': feature.get('end', ''),
                    'strand': feature.get('strand', ''),
                    'feature_type': feature.get('feature_type', ''),
                    'gene': feature.get('gene', ''),
                    'locus_tag': feature.get('locus_tag', ''),
                    'protein_id': feature.get('protein_id', ''),
                    'function': feature.get('function', ''),
                    'subsystem': feature.get('subsystem', '')
                }
                all_detailed_features.append(feature_row)
    
    # Save to CSV with comprehensive format
    if all_detailed_features:
        with open(output_filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'search_term', 'genome_id', 'success', 'count', 'error',
                'accession', 'patric_id', 'product', 'start', 'end', 'strand', 
                'feature_type', 'gene', 'locus_tag', 'protein_id', 'function', 'subsystem'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_detailed_features)
        
        print(f"📁 Track 2 results saved: {output_filename}")
        print(f"📊 Format: Alpha-Synuclein style with full BV-BRC metadata")
        print(f"📊 Features saved: {len(all_detailed_features)} individual features")
        return len(all_detailed_features)
    else:
        print(f"⚠️  No features found to save")
        return 0


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
            track_name="Track2_Copper_Homeostasis"
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_batch, i, batch) for i, batch in enumerate(batches)]
        for future in as_completed(futures):
            results.extend(future.result())

    return results


def run_track2_copper_homeostasis():
    print("🔥 TRACK 2: COPPER HOMEOSTASIS COMPREHENSIVE SEARCH")
    print("="*65)

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

    # TRACK 2: Copper Homeostasis (54 terms total)
    track2_gene_terms = [
        # Major Copper Efflux Systems
        'copA', 'copB', 'copC', 'copD', 'copE', 'copF',  # cop operon
        'cusA', 'cusB', 'cusC', 'cusF', 'cusR', 'cusS',  # cus system
        'cueO', 'cueR', 'cueP',                          # cue system
        'ctrA', 'ctrB', 'ctrC', 'ctrD',                  # ctr transporters
        # Copper Chaperones and Binding
        'copZ', 'copY', 'copG', 'copH',                  # cop chaperones/regulators
        'cutC', 'cutE', 'cutF',                          # copper tolerance
        'scoA', 'scoB',                                  # copper chaperones
        # Additional Copper Systems
        'pcoA', 'pcoB', 'pcoC', 'pcoD', 'pcoE',         # pco operon
        'copL', 'copM', 'copN'                           # additional cop genes
    ]
    
    track2_functional_terms = [
        'copper transporter', 'copper efflux', 'copper resistance', 'copper export',
        'copper oxidase', 'copper chaperone', 'copper binding', 'copper homeostasis',
        'copper tolerance', 'cuprous oxidase', 'multicopper oxidase', 'copper sensor',
        'copper regulator', 'copper detoxification', 'heavy metal efflux', 'metal transport',
        'P-type ATPase copper', 'copper-translocating'
    ]
    
    # Combine all Track 2 terms
    all_track2_terms = track2_gene_terms + track2_functional_terms
    total_terms = len(all_track2_terms)
    all_raw_results = []
    
    print(f"\\n🎯 TRACK 2 SEARCH TERMS:")
    print(f"   🧬 Gene terms: {len(track2_gene_terms)}")
    print(f"   📋 Functional terms: {len(track2_functional_terms)}")
    print(f"   📊 TOTAL TERMS: {total_terms}")
    print(f"   🔬 GENOMES: {len(genome_ids)}")
    print(f"   ⏱️  Expected runtime: 45-90 minutes")
    print(f"\\n🚀 Starting Track 2 search...")
    
    start_time = time.time()

    for i, term in enumerate(all_track2_terms, 1):
        term_results = search_term_across_genomes(term, genome_ids, i, total_terms)
        all_raw_results.extend(term_results)
        
        # Update progress bar
        print_progress_bar(i, total_terms, start_time, "Track 2 Progress")

    total_time = time.time() - start_time
    print(f"✅ Track 2 data collection complete in {total_time:.1f} seconds")

    # Save results in Alpha-Synuclein comprehensive format
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"track2_copper_homeostasis_results_{timestamp}.csv"
    feature_count = save_comprehensive_results(all_raw_results, output_file)
    
    if feature_count > 0:
        print(f"\\n✅ TRACK 2 COMPLETE!")
        print(f"📊 Features found: {feature_count}")
        print(f"📁 Output file: {output_file}")
        print(f"⏱️  Execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"🎯 Focus: Bacterial copper sequestration mechanisms")
    else:
        print("⚠️ No results captured!")

    return {
        'execution_time': total_time,
        'total_results': feature_count,
        'output_file': output_file,
        'track': 'Track2_Copper_Homeostasis',
        'terms_searched': total_terms
    }


def main():
    print("🧪 RUNNING TRACK 2: COPPER HOMEOSTASIS COMPREHENSIVE SEARCH\\n")
    try:
        result = run_track2_copper_homeostasis()
        print(f"\\n✅ Track 2 complete. Features saved: {result['total_results']}")
        print(f"📁 Output file: {result['output_file']}")
        print(f"🔥 Track: {result['track']}")
        print(f"📊 Terms searched: {result['terms_searched']}")
        print(f"⏱️  Runtime: {result['execution_time']/60:.1f} minutes")
    except Exception as e:
        print(f"❌ Track 2 failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()