#!/usr/bin/env python3
"""
Quick 10-Term Test - Test with exactly 10 search terms to show progress and timing
"""

import time
from shared_utilities import bvbrc_utils

def test_10_terms():
    """Test with exactly 10 search terms across small genome set"""
    
    print("🚀 QUICK 10-TERM PROGRESS TEST")
    print("="*60)
    
    # Load small set of genomes for quick testing
    print("📖 Loading representative genomes...")
    genomes = bvbrc_utils.load_representative_genomes(limit=15)
    genome_ids = list(genomes.keys())
    
    if not genome_ids:
        print("❌ No genomes loaded")
        return
    
    print(f"✅ Loaded {len(genome_ids)} genomes for testing")
    print(f"Genome sample: {genome_ids[:3]}...")
    
    # Select 10 high-value search terms (mix from all three tracks)
    test_terms = [
        # Track 1: Bacterial Amyloids (3 terms)
        'csgA',     # Major curli subunit
        'csgB',     # Minor curli subunit  
        'tasA',     # Bacillus biofilm matrix
        
        # Track 2: Copper Homeostasis (4 terms)
        'copA',     # Copper-exporting ATPase
        'cusA',     # Copper efflux transporter
        'cueO',     # Copper efflux oxidase
        'cueR',     # Copper efflux regulator
        
        # Track 3: SOD Systems (3 terms)
        'sodA',     # Manganese superoxide dismutase
        'sodB',     # Iron superoxide dismutase
        'sodC'      # Copper-zinc superoxide dismutase
    ]
    
    print(f"\n🎯 Testing with {len(test_terms)} carefully selected search terms:")
    for i, term in enumerate(test_terms, 1):
        print(f"   {i}. {term}")
    
    # Record start time
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"🔍 STARTING SEARCH - Watch the Progress!")
    print(f"{'='*60}")
    
    # Execute batch search with progress tracking
    results = bvbrc_utils.batch_search_across_genomes(
        search_terms=test_terms,
        genome_ids=genome_ids,
        search_type='gene',
        track_name="Quick_10_Term_Test"
    )
    
    # Calculate timing
    total_time = time.time() - start_time
    
    # Analyze results
    total_features = sum(r.get('features_found', 0) for r in results)
    successful_terms = sum(1 for r in results if r.get('success', False))
    
    print(f"\n{'='*60}")
    print(f"📊 10-TERM TEST RESULTS")
    print(f"{'='*60}")
    print(f"⏱️  Total execution time: {total_time:.1f} seconds")
    print(f"🎯 Terms searched: {len(test_terms)}")
    print(f"✅ Successful terms: {successful_terms}/{len(test_terms)} ({(successful_terms/len(test_terms)*100):.1f}%)")
    print(f"📊 Total features found: {total_features}")
    print(f"🧬 Genomes searched: {len(genome_ids)}")
    print(f"⚡ Average time per term: {total_time/len(test_terms):.1f} seconds")
    print(f"⚡ Average time per genome: {total_time/len(genome_ids):.1f} seconds")
    
    # Show term-by-term breakdown
    print(f"\n🔬 TERM-BY-TERM BREAKDOWN:")
    for result in results:
        term = result.get('search_term', 'Unknown')
        features = result.get('features_found', 0)
        status = "✅" if result.get('success', False) else "❌"
        print(f"   {status} {term}: {features} features")
    
    # API statistics
    api_stats = bvbrc_utils.get_api_stats()
    print(f"\n📡 API USAGE STATISTICS:")
    print(f"   Total API calls: {api_stats['total_calls']}")
    print(f"   Successful calls: {api_stats['successful_calls']}")
    print(f"   Timeout errors: {api_stats['timeout_errors']}")
    print(f"   HTTP errors: {api_stats['http_errors']}")
    print(f"   Retry attempts: {api_stats['retry_attempts']}")
    
    if api_stats['total_calls'] > 0:
        api_success_rate = (api_stats['successful_calls'] / api_stats['total_calls']) * 100
        print(f"   API success rate: {api_success_rate:.1f}%")
    
    # Extrapolate to full production run
    print(f"\n🔮 FULL PRODUCTION EXTRAPOLATION:")
    full_terms = 102  # Total terms across all three tracks
    full_genomes = 500  # Approximate full genome set
    
    # Scale up timing (with some overhead factor)
    estimated_time = (total_time / len(test_terms)) * full_terms * (full_genomes / len(genome_ids)) * 1.2
    estimated_hours = estimated_time / 3600
    
    print(f"   Estimated full run time: {estimated_time:.0f} seconds ({estimated_hours:.1f} hours)")
    print(f"   Full terms to search: {full_terms}")
    print(f"   Full genomes to analyze: ~{full_genomes}")
    print(f"   Expected features: {total_features * (full_terms/len(test_terms)) * (full_genomes/len(genome_ids)):.0f}")
    
    return {
        'execution_time': total_time,
        'successful_terms': successful_terms,
        'total_features': total_features,
        'results': results,
        'api_stats': api_stats
    }

def main():
    """Execute the 10-term test"""
    print("🧪 TESTING 10 SEARCH TERMS WITH PROGRESS TRACKING")
    print("This will show you exactly how the progress reporting works!")
    print()
    
    try:
        results = test_10_terms()
        
        print(f"\n✅ Test completed successfully!")
        print(f"You can see the detailed progress reporting above.")
        print(f"The full production run will show similar progress for all 102 terms.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()