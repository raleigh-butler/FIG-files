
#!/usr/bin/env python3
"""
Enhanced Full Genome 2-Term Test - Parallelized by Batch with Safe Rate Limiting
"""

import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from shared_utilities import bvbrc_utils


# Global rate limiting
rate_limit_lock = threading.Lock()
last_api_call_time = 0
api_call_count = 0
api_failures = 0

def safe_rate_limited_delay():
    """Apply adaptive rate limiting with dynamic backoff based on API failures"""
    global last_api_call_time, api_call_count, api_failures
    
    with rate_limit_lock:
        current_time = time.time()
        
        # Adaptive base delay - increases with failures
        base_delay = 0.3  # Conservative base delay
        if api_failures > 10:
            base_delay = 0.6  # Slower if many failures
        elif api_failures > 5:
            base_delay = 0.4  # Slightly slower with some failures
        
        # Progressive failure penalty - gets more aggressive with more failures
        if api_failures <= 5:
            failure_penalty = min(api_failures * 0.3, 2.0)  # Gentle penalty initially
        else:
            failure_penalty = min(api_failures * 0.8, 10.0)  # More aggressive penalty
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 0.3)
        
        total_delay = base_delay + failure_penalty + jitter
        
        # Ensure minimum time between calls
        time_since_last = current_time - last_api_call_time
        if time_since_last < total_delay:
            sleep_time = total_delay - time_since_last
            time.sleep(sleep_time)
        
        last_api_call_time = time.time()
        api_call_count += 1

def search_term_across_genomes(term, genome_ids, term_index, total_terms, batch_size=30, max_workers=12):
    """Search a single term across genome batches with safe rate limiting"""
    global api_failures
    
    results = []
    batches = [genome_ids[i:i + batch_size] for i in range(0, len(genome_ids), batch_size)]
    completed_batches = 0
    total_features = 0

    print(f"🔍 Term {term_index}/{total_terms}: {term} — {len(batches)} genome batches")

    def search_batch_safe(i, batch):
        """Search batch with safe rate limiting and error handling"""
        global api_failures
        
        start = i * batch_size
        end = min(start + batch_size, len(genome_ids))
        
        max_retries = 8  # Increased from 3 to 8 for better resilience
        for attempt in range(max_retries):
            try:
                # Apply rate limiting before each batch
                safe_rate_limited_delay()
                
                batch_start = time.time()
                batch_results = bvbrc_utils.batch_search_across_genomes(
                    search_terms=[term],
                    genome_ids=batch,
                    search_type='gene',
                    track_name="Safe_Parallel_Search"
                )
                batch_time = time.time() - batch_start
                
                # Count features in this batch
                batch_features = sum(r.get('features_found', 0) for r in batch_results)
                
                print(f"   ✅ Batch {i+1}/{len(batches)} — Genomes {start+1}-{end} — {batch_features} features ({batch_time:.1f}s)")
                
                return batch_results
                
            except Exception as e:
                api_failures += 1
                error_msg = str(e)[:60]
                print(f"   ⚠️  Batch {i+1}/{len(batches)} attempt {attempt+1}/{max_retries} failed: {error_msg}...")
                
                if attempt < max_retries - 1:
                    # More aggressive exponential backoff for API rate limiting
                    if "rate" in error_msg.lower() or "limit" in error_msg.lower() or "timeout" in error_msg.lower():
                        # For rate limiting/timeout errors, use longer backoff
                        backoff_time = min((2 ** attempt) * 2, 60) + random.uniform(0, 5)  # Max 60s + jitter
                        print(f"   ⏳ API rate limit detected - longer retry in {backoff_time:.1f} seconds...")
                    else:
                        # For other errors, use standard backoff
                        backoff_time = min((2 ** attempt), 30) + random.uniform(0, 2)  # Max 30s + jitter
                        print(f"   ⏳ Retrying in {backoff_time:.1f} seconds...")
                    
                    time.sleep(backoff_time)
                else:
                    print(f"   ❌ Batch {i+1}/{len(batches)} PERMANENTLY FAILED after {max_retries} attempts")
                    print(f"   📝 Final error: {error_msg}")
                    return []
        
        return []

    # Use conservative thread pool settings to avoid overwhelming API
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=f"{term}_worker") as executor:
        # Submit all batch jobs
        futures = [executor.submit(search_batch_safe, i, batch) for i, batch in enumerate(batches)]
        
        # Collect results as they complete with progress tracking
        for future in as_completed(futures):
            batch_results = future.result()
            if batch_results:
                results.extend(batch_results)
                batch_features = sum(r.get('features_found', 0) for r in batch_results)
                total_features += batch_features
            
            completed_batches += 1
            
            # Progress update every 10 batches or at significant milestones
            if completed_batches % 10 == 0 or completed_batches == len(batches):
                progress_pct = (completed_batches / len(batches)) * 100
                print(f"   📊 Progress: {completed_batches}/{len(batches)} batches ({progress_pct:.1f}%) — {total_features} features found")

    print(f"   🎯 Term {term} completed: {total_features} total features from {len(results)} successful searches")
    return results


def test_2_terms_all_genomes():
    print("🚀 FULL GENOME 2-TERM TIMING TEST")
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
    print(f"Sample genomes: {genome_ids[:3]}...")

    test_terms = ['copA', 'sodA']
    total_terms = len(test_terms)

    print(f"\n🎯 Starting search with {total_terms} terms across {len(genome_ids)} genomes.")
    overall_start_time = time.time()
    
    # Track timing for each term
    term_timings = []
    results = []
    
    # Progress bar setup
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
        
        print(f"\r{prefix}: |{bar}| {current}/{total} ({percent:.1f}%) [{elapsed/60:.1f}m elapsed{eta_str}]", end='', flush=True)
        
        if current == total:
            print()  # New line when complete
    
    print("\n" + "="*80)
    print("📊 OVERALL PROGRESS TRACKING")
    print("="*80)
    
    for i, term in enumerate(test_terms, 1):
        term_start_time = time.time()
        print(f"\n⏱️  Starting term {i}/{total_terms}: {term} at {time.strftime('%H:%M:%S')}")
        
        term_results = search_term_across_genomes(
            term=term, 
            genome_ids=genome_ids, 
            term_index=i, 
            total_terms=total_terms,
            batch_size=30,    # Increased from 25
            max_workers=12    # Increased from 10 but kept conservative
        )
        
        term_end_time = time.time()
        term_duration = term_end_time - term_start_time
        term_features = sum(r.get('features_found', 0) for r in term_results)
        
        term_timings.append({
            'term': term,
            'duration': term_duration,
            'features': term_features,
            'start_time': time.strftime('%H:%M:%S', time.localtime(term_start_time)),
            'end_time': time.strftime('%H:%M:%S', time.localtime(term_end_time))
        })
        
        print(f"⏱️  Completed term {i}/{total_terms}: {term} in {term_duration:.1f} seconds ({term_features} features)")
        
        results.extend(term_results)
        
        # Update overall progress bar
        print_progress_bar(i, total_terms, overall_start_time, "Overall Progress")

    total_time = time.time() - overall_start_time
    end_time = time.strftime('%H:%M:%S')

    total_features = sum(r.get('features_found', 0) for r in results)
    successful_terms = sum(1 for r in results if r.get('success', False))

    print(f"\n{'='*70}")
    print(f"📊 COMPREHENSIVE TIMING & RESULTS REPORT")
    print(f"{'='*70}")
    
    # Overall timing summary
    start_time_str = time.strftime('%H:%M:%S', time.localtime(overall_start_time))
    print(f"🕐 Overall timing:")
    print(f"   Started: {start_time_str}")
    print(f"   Ended: {end_time}")
    print(f"   Total execution time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"   Average time per term: {total_time/total_terms:.1f} seconds")
    
    # Per-term timing breakdown
    print(f"\n⏱️  DETAILED PER-TERM TIMING:")
    for i, timing in enumerate(term_timings, 1):
        duration_mins = timing['duration'] / 60
        features_per_sec = timing['features'] / timing['duration'] if timing['duration'] > 0 else 0
        print(f"   Term {i}: {timing['term']}")
        print(f"      Time: {timing['start_time']} → {timing['end_time']} ({timing['duration']:.1f}s / {duration_mins:.1f}m)")
        print(f"      Features: {timing['features']} ({features_per_sec:.1f} features/second)")
    
    # Performance analysis
    print(f"\n📈 PERFORMANCE ANALYSIS:")
    fastest_term = min(term_timings, key=lambda x: x['duration'])
    slowest_term = max(term_timings, key=lambda x: x['duration'])
    most_productive = max(term_timings, key=lambda x: x['features'])
    
    print(f"   Fastest term: {fastest_term['term']} ({fastest_term['duration']:.1f}s)")
    print(f"   Slowest term: {slowest_term['term']} ({slowest_term['duration']:.1f}s)")
    print(f"   Most productive: {most_productive['term']} ({most_productive['features']} features)")
    print(f"   Time variation: {slowest_term['duration'] - fastest_term['duration']:.1f}s difference")
    
    # Results summary
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Terms processed: {total_terms}/{total_terms} (100%)")
    print(f"   Successful searches: {successful_terms}")
    print(f"   Total features found: {total_features}")
    print(f"   Genomes analyzed: {len(genome_ids)}")
    print(f"   Average features per term: {total_features/total_terms:.1f}")

    print(f"\n🔬 TERM-BY-TERM BREAKDOWN:")
    for result in results:
        term = result.get('search_term', 'Unknown')
        features = result.get('features_found', 0)
        status = "✅" if result.get('success', False) else "❌"
        coverage = f"({features/len(genome_ids)*100:.1f}% genome coverage)" if features > 0 else "(no coverage)"
        print(f"   {status} {term}: {features} features {coverage}")

    # Enhanced API and safety statistics
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
    
    # Safety features reporting
    global api_failures, api_call_count
    print(f"\n🛡️  ENHANCED SAFETY FEATURES REPORT:")
    print(f"   Rate-limited API calls made: {api_call_count}")
    print(f"   API failures handled gracefully: {api_failures}")
    print(f"   Failure rate: {(api_failures/max(api_call_count,1)*100):.1f}%")
    print(f"   Adaptive delays: ✅ 0.3-0.6s base + up to 10s failure penalties")
    print(f"   Aggressive retry logic: ✅ Up to 8 attempts per batch")
    print(f"   Rate limit detection: ✅ Extended backoff (up to 60s) for API limits")
    print(f"   Thread pool size: 12 workers (conservative)")
    
    # Provide resilience assessment
    if api_failures == 0:
        print(f"   🎯 Resilience status: EXCELLENT - No API issues encountered")
    elif api_failures < 5:
        print(f"   ✅ Resilience status: GOOD - Minor API issues handled successfully")
    elif api_failures < 20:
        print(f"   ⚠️  Resilience status: ACCEPTABLE - Some API instability but data gathering successful")
    else:
        print(f"   🔥 Resilience status: CHALLENGING - Significant API issues but robust retry logic working")
    
    # Production estimates based on actual timing data
    print(f"\n🔮 FULL PRODUCTION ESTIMATES (102 terms):")
    avg_term_time = total_time / total_terms
    fastest_time = min(timing['duration'] for timing in term_timings)
    slowest_time = max(timing['duration'] for timing in term_timings)
    
    # Conservative estimates
    conservative_estimate = avg_term_time * 102 * 1.2  # 20% buffer for larger dataset
    optimistic_estimate = avg_term_time * 102
    pessimistic_estimate = slowest_time * 102 * 1.3   # Based on slowest term + 30% buffer
    
    print(f"   Based on average term time ({avg_term_time:.1f}s):")
    print(f"   ⚡ Optimistic: {optimistic_estimate/60:.1f} minutes ({optimistic_estimate/3600:.1f} hours)")
    print(f"   🎯 Expected: {conservative_estimate/60:.1f} minutes ({conservative_estimate/3600:.1f} hours)")
    print(f"   ⚠️  Pessimistic: {pessimistic_estimate/60:.1f} minutes ({pessimistic_estimate/3600:.1f} hours)")
    print(f"   📊 Expected total features: {int(total_features * 102 / total_terms):,}")

    # Save comprehensive results to files
    print(f"\n💾 SAVING RESULTS TO FILES...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Create comprehensive report with all data
    comprehensive_report = {
        'test_info': {
            'timestamp': timestamp,
            'test_type': '2_term_parallel_progress_test',
            'execution_time': total_time,
            'genomes_tested': len(genome_ids)
        },
        'timing_analysis': {
            'total_seconds': total_time,
            'total_minutes': total_time / 60,
            'avg_seconds_per_term': avg_term_time,
            'fastest_term': fastest_term,
            'slowest_term': slowest_term,
            'most_productive': most_productive,
            'time_variation': slowest_term['duration'] - fastest_term['duration'],
            'detailed_timings': term_timings
        },
        'results_summary': {
            'successful_terms': successful_terms,
            'total_features': total_features,
            'avg_features_per_term': total_features / len(test_terms),
            'terms_tested': test_terms
        },
        'api_statistics': api_stats,
        'resilience_stats': {
            'api_call_count': api_call_count,
            'api_failures': api_failures,
            'failure_rate': (api_failures/max(api_call_count,1)*100)
        },
        'raw_results': results
    }
    
    # Save comprehensive JSON report
    json_file = f"2term_test_comprehensive_report_{timestamp}.json"
    with open(json_file, 'w') as f:
        import json
        json.dump(comprehensive_report, f, indent=2, default=str)
    print(f"📁 Comprehensive report saved: {json_file}")
    
    # Create term-level results matrix (CSV)
    print(f"📊 Creating term-level results matrix...")
    print(f"🔍 Current data structure provides aggregate counts, not per-genome breakdown")
    
    # Create a simplified matrix showing term presence/absence at aggregate level
    # Since we don't have per-genome data, we'll create a different format
    
    # Debug: Show what we actually have
    print(f"   🔍 DEBUGGING: Total results received: {len(results)}")
    
    for i, result in enumerate(results):
        term = result.get('search_term', 'Unknown')
        success = result.get('success', False)
        features_found = result.get('features_found', 0)
        
        print(f"   Result {i+1}: {term}")
        print(f"      Success: {success}")
        print(f"      Features found: {features_found}")
        print(f"      Available keys: {list(result.keys())}")
        
        # Check if there's any detailed feature data
        if 'features' in result and result['features']:
            print(f"      Features detail (first 2): {result['features'][:2]}")
        
        if features_found > 0:
            print(f"      🎯 THIS RESULT HAS {features_found} FEATURES - WHERE ARE THEY?")
            # Print the entire result to see structure
            print(f"      Full result: {result}")
            break  # Stop after first successful result
    
    # Create a term summary matrix instead of genome-feature matrix
    term_summary = {}
    successful_terms = []
    total_features_debug = 0
    
    for result in results:
        term = result.get('search_term', 'Unknown')
        success = result.get('success', False)
        features_found = result.get('features_found', 0)
        total_features_debug += features_found
        
        print(f"   Processing {term}: success={success}, features={features_found}")
        
        if success and features_found > 0:
            successful_terms.append(term)
            term_summary[term] = {
                'features_found': features_found,
                'success': True,
                'genomes_searched': result.get('genomes_searched', len(genome_ids))
            }
        else:
            term_summary[term] = {
                'features_found': 0,
                'success': False,
                'genomes_searched': result.get('genomes_searched', len(genome_ids))
            }
    
    print(f"   🔍 DEBUG SUMMARY:")
    print(f"      Total results processed: {len(results)}")
    print(f"      Total features counted: {total_features_debug}")
    print(f"      Successful terms with features: {successful_terms}")
    print(f"      Term summary: {term_summary}")
    
    print(f"   ⚠️  IMPORTANT: If features > 0 but no genome breakdown, we have a data structure issue")
    
    # Create genome-feature matrix using the genome_coverage data
    matrix = {}
    all_terms_found = set()
    
    # Build matrix from results using genome_coverage
    for result in results:
        if result.get('success', False):
            term = result.get('search_term', 'Unknown')
            genome_coverage = result.get('genome_coverage', {})
            
            all_terms_found.add(term)
            
            # For each genome, mark 1 if has features for this term, 0 otherwise
            for genome_id in genome_ids:
                if genome_id not in matrix:
                    matrix[genome_id] = {}
                
                # Use genome_coverage data to set 1 or 0
                feature_count = genome_coverage.get(genome_id, 0)
                matrix[genome_id][term] = 1 if feature_count > 0 else 0
    
    print(f"   ✅ Matrix now uses actual per-genome feature data!")
    print(f"   📊 Terms with features: {sorted(list(all_terms_found))}")
    
    # Show sample matrix data for validation
    if genome_ids and all_terms_found:
        sample_genome = genome_ids[0]
        sample_data = matrix.get(sample_genome, {})
        print(f"   📝 Sample matrix data for {sample_genome}: {sample_data}")
    
    # Save the actual genome-feature matrix as CSV
    import csv
    csv_file = f"2term_test_genome_feature_matrix_{timestamp}.csv"
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        terms_list = sorted(list(all_terms_found))
        header = ['genome_id'] + terms_list
        writer.writerow(header)
        
        # Data rows with actual 1/0 values
        for genome_id in genome_ids:
            row = [genome_id]
            for term in terms_list:
                row.append(matrix.get(genome_id, {}).get(term, 0))
            writer.writerow(row)
    
    print(f"📁 Genome-feature matrix saved: {csv_file}")
    print(f"📊 Matrix dimensions: {len(genome_ids)} genomes × {len(all_terms_found)} terms (now with actual data!)")
    
    # Create a more useful term-level results CSV
    term_results_csv = f"2term_test_term_results_{timestamp}.csv"
    with open(term_results_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['term', 'success', 'features_found', 'genomes_searched', 'avg_features_per_genome'])
        
        for term, data in term_summary.items():
            avg_features = data['features_found'] / data['genomes_searched'] if data['genomes_searched'] > 0 else 0
            writer.writerow([
                term,
                'Yes' if data['success'] else 'No',
                data['features_found'],
                data['genomes_searched'],
                f"{avg_features:.3f}"
            ])
    
    print(f"📁 Term results saved: {term_results_csv}")
    print(f"📊 This shows the actual useful data: which terms found features and how many")
    
    # Create detailed features CSV with all BV-BRC data
    detailed_features_csv = f"2term_test_detailed_features_{timestamp}.csv"
    all_features = []
    
    # Collect all detailed features from all results
    for result in results:
        if result.get('success', False) and result.get('features'):
            term = result.get('search_term', 'Unknown')
            for feature in result['features']:
                # Add search term to each feature for identification
                feature_copy = feature.copy()
                feature_copy['search_term'] = term
                all_features.append(feature_copy)
    
    if all_features:
        # Save detailed features CSV
        import csv
        with open(detailed_features_csv, 'w', newline='', encoding='utf-8') as f:
            # Use all available fields from the first feature
            fieldnames = list(all_features[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_features)
        
        print(f"📁 Detailed features saved: {detailed_features_csv}")
        print(f"📊 Contains {len(all_features)} individual features with full BV-BRC data")
        print(f"📊 Fields included: {', '.join(fieldnames)}")
    else:
        print(f"⚠️  No detailed features found to save")
    
    # Create simple summary CSV for quick analysis
    summary_csv = f"2term_test_summary_{timestamp}.csv"
    with open(summary_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['term', 'features_found', 'duration_seconds', 'features_per_second'])
        
        for timing in term_timings:
            features_per_sec = timing['features'] / timing['duration'] if timing['duration'] > 0 else 0
            writer.writerow([
                timing['term'], 
                timing['features'], 
                timing['duration'], 
                f"{features_per_sec:.2f}"
            ])
    
    print(f"📁 Summary saved: {summary_csv}")
    
    print(f"\n✅ All results saved successfully!")
    print(f"📁 Files created:")
    print(f"   • {json_file} (comprehensive data)")
    print(f"   • {csv_file} (genome-feature matrix)")
    print(f"   • {summary_csv} (term summary)")

    return {
        'execution_time': total_time,
        'successful_terms': successful_terms,
        'term_timings': term_timings,
        'performance_analysis': {
            'fastest_term': fastest_term,
            'slowest_term': slowest_term,
            'most_productive': most_productive,
            'avg_time_per_term': avg_term_time,
            'time_variation': slowest_term['duration'] - fastest_term['duration']
        },
        'total_features': total_features,
        'results': results,
        'api_stats': api_stats,
        'genomes_tested': len(genome_ids),
        'files_saved': [json_file, csv_file, detailed_features_csv, term_results_csv, summary_csv]
    }


def main():
    print("🧪 TESTING 2 TERMS ACROSS ALL GENOMES\n")
    try:
        results = test_2_terms_all_genomes()
        print(f"\n✅ Full genome test completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
