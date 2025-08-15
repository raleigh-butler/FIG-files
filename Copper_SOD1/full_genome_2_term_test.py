#!/usr/bin/env python3
"""
Full Genome 2-Term Test - Test 2 search terms across ALL 992 genomes for accurate timing
"""

import time
from shared_utilities import bvbrc_utils

def test_2_terms_all_genomes():
    """Test with 2 search terms across ALL representative genomes"""
    
    print("🚀 FULL GENOME 2-TERM TIMING TEST")
    print("="*60)
    
    # Load ALL representative genomes (no limit)
    print("📖 Loading ALL representative genomes...")
    start_load_time = time.time()
    genomes = bvbrc_utils.load_representative_genomes(limit=None)
    genome_ids = list(genomes.keys())
    load_time = time.time() - start_load_time
    
    if not genome_ids:
        print("❌ No genomes loaded")
        return
    
    print(f"✅ Loaded {len(genome_ids)} genomes in {load_time:.1f} seconds")
    print(f"📊 This is the FULL representative genome set")
    print(f"Sample genomes: {genome_ids[:3]}...")
    
    # Select 2 high-value search terms from different tracks
    test_terms = [
        'copA',     # Copper-exporting ATPase (Track 2) - should find many hits
        'sodA'      # Manganese superoxide dismutase (Track 3) - should find many hits
    ]
    
    print(f"\n🎯 Testing with {len(test_terms)} high-value search terms:")
    for i, term in enumerate(test_terms, 1):
        print(f"   {i}. {term}")
    
    print(f"\n⚠️  This will test across ALL {len(genome_ids)} genomes!")
    print(f"Expected API calls: {len(test_terms)} × {len(genome_ids)} = {len(test_terms) * len(genome_ids)}")
    
    # Record start time
    start_time = time.time()
    print(f"🕐 Starting at: {time.strftime('%H:%M:%S')}")
    
    print(f"\n{'='*60}")
    print(f"🔍 STARTING FULL GENOME SEARCH - Watch the Progress!")
    print(f"{'='*60}")
    
    # Execute batch search with progress tracking
    results = bvbrc_utils.batch_search_across_genomes(
        search_terms=test_terms,
        genome_ids=genome_ids,
        search_type='gene',
        track_name="Full_Genome_2_Term_Test"
    )
    
    # Calculate timing
    total_time = time.time() - start_time
    end_time = time.strftime('%H:%M:%S')
    
    # Analyze results
    total_features = sum(r.get('features_found', 0) for r in results)
    successful_terms = sum(1 for r in results if r.get('success', False))
    
    print(f"\n{'='*60}")
    print(f"📊 FULL GENOME 2-TERM TEST RESULTS")
    print(f"{'='*60}")
    print(f"🕐 Started: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
    print(f"🕐 Ended: {end_time}")
    print(f"⏱️  Total execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"🎯 Terms searched: {len(test_terms)}")
    print(f"✅ Successful terms: {successful_terms}/{len(test_terms)} ({(successful_terms/len(test_terms)*100):.1f}%)")
    print(f"📊 Total features found: {total_features}")
    print(f"🧬 Genomes searched: {len(genome_ids)}")
    print(f"⚡ Average time per term: {total_time/len(test_terms):.1f} seconds ({total_time/len(test_terms)/60:.1f} minutes)")
    print(f"⚡ Average time per genome: {total_time/len(genome_ids):.2f} seconds")
    print(f"⚡ Average time per API call: {total_time/(len(test_terms)*len(genome_ids)):.2f} seconds")
    
    # Show term-by-term breakdown
    print(f"\n🔬 TERM-BY-TERM BREAKDOWN:")
    for result in results:
        term = result.get('search_term', 'Unknown')
        features = result.get('features_found', 0)
        status = "✅" if result.get('success', False) else "❌"
        coverage = f"({features/len(genome_ids)*100:.1f}% genome coverage)" if features > 0 else "(no coverage)"
        print(f"   {status} {term}: {features} features {coverage}")
    
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
        print(f"   Average API response time: {total_time/api_stats['total_calls']:.2f} seconds")
    
    # Extrapolate to full 102-term production run
    print(f"\n🔮 FULL 102-TERM PRODUCTION EXTRAPOLATION:")
    full_terms = 102  # Total terms across all three tracks
    
    # Scale up timing based on actual performance
    estimated_time = (total_time / len(test_terms)) * full_terms
    estimated_hours = estimated_time / 3600
    estimated_api_calls = full_terms * len(genome_ids)
    
    print(f"   📊 Actual performance per term: {total_time/len(test_terms):.1f} seconds")
    print(f"   📊 Estimated full run time: {estimated_time:.0f} seconds ({estimated_hours:.1f} hours)")
    print(f"   📊 Total API calls needed: {estimated_api_calls:,}")
    print(f"   📊 Expected total features: {int(total_features * full_terms / len(test_terms)):,}")
    
    # Performance breakdown
    print(f"\n⚡ PERFORMANCE ANALYSIS:")
    if total_time/len(test_terms) < 300:  # Less than 5 minutes per term
        print(f"   ✅ EXCELLENT: {total_time/len(test_terms):.1f} seconds per term")
    elif total_time/len(test_terms) < 600:  # Less than 10 minutes per term
        print(f"   ✅ GOOD: {total_time/len(test_terms):.1f} seconds per term")
    else:
        print(f"   ⚠️  SLOW: {total_time/len(test_terms):.1f} seconds per term")
    
    if api_stats.get('timeout_errors', 0) == 0:
        print(f"   ✅ STABLE: No API timeouts")
    else:
        print(f"   ⚠️  UNSTABLE: {api_stats['timeout_errors']} API timeouts")
    
    if api_success_rate > 95:
        print(f"   ✅ RELIABLE: {api_success_rate:.1f}% API success rate")
    else:
        print(f"   ⚠️  UNRELIABLE: {api_success_rate:.1f}% API success rate")
    
    return {
        'execution_time': total_time,
        'successful_terms': successful_terms,
        'total_features': total_features,
        'results': results,
        'api_stats': api_stats,
        'genomes_tested': len(genome_ids)
    }

def main():
    """Execute the full genome 2-term test"""
    print("🧪 TESTING 2 TERMS ACROSS ALL 992 GENOMES")
    print("This will give us accurate timing for the full production run!")
    print("⚠️  This test will take some time - please be patient...")
    print()
    
    try:
        results = test_2_terms_all_genomes()
        
        print(f"\n✅ Full genome test completed successfully!")
        print(f"📊 Now we have accurate timing data for the complete production run.")
        print(f"🚀 Use this data to plan your full 102-term production execution.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()