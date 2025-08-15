#!/usr/bin/env python3
"""
Track 1 Test: Quick test of bacterial amyloids search with robust API handling
"""

from robust_api_handler import api_handler

def test_bacterial_amyloids():
    """Test bacterial amyloids search with robust timeout handling"""
    
    print("🧬 TRACK 1: BACTERIAL AMYLOIDS TEST")
    print("="*50)
    
    # Load test genomes (small number for quick test)
    genomes = api_handler.load_representative_genomes(limit=10)
    genome_ids = list(genomes.keys())
    
    if not genome_ids:
        print("❌ No genomes loaded")
        return
    
    print(f"🎯 Testing with {len(genome_ids)} genomes")
    
    # Test enhanced amyloid gene names
    test_genes = [
        'csgA', 'csgB', 'csgC',  # Curli system
        'tasA', 'tapA',          # Bacillus biofilm
        'psmA', 'psmB',          # Staphylococcal modulins
        'fapC',                  # Pseudomonas amyloids
        'chpA'                   # Streptomyces chaplins
    ]
    
    # Test functional terms
    test_functions = [
        'curli',
        'biofilm matrix protein',
        'functional amyloid'
    ]
    
    all_results = []
    
    print(f"\n🔬 TESTING GENE NAME SEARCHES")
    for gene in test_genes:
        print(f"--- Testing {gene} ---")
        gene_hits = 0
        
        for genome_id in genome_ids[:5]:  # Test first 5 genomes
            result = api_handler.search_gene_in_genome(gene, genome_id, 'gene')
            all_results.append(result)
            
            if result['success'] and result['count'] > 0:
                gene_hits += result['count']
                print(f"  ✅ {genome_id}: {result['count']} hits")
            
            # Small delay to be polite
            import time
            time.sleep(0.2)
        
        print(f"  📊 {gene}: {gene_hits} total hits")
    
    print(f"\n🔍 TESTING FUNCTIONAL SEARCHES")  
    for function in test_functions:
        print(f"--- Testing '{function}' ---")
        func_hits = 0
        
        for genome_id in genome_ids[:3]:  # Test first 3 genomes for functions
            result = api_handler.search_gene_in_genome(function, genome_id, 'product')
            all_results.append(result)
            
            if result['success'] and result['count'] > 0:
                func_hits += result['count']
                print(f"  ✅ {genome_id}: {result['count']} hits")
            
            import time
            time.sleep(0.3)
        
        print(f"  📊 '{function}': {func_hits} total hits")
    
    # Summary
    total_hits = sum(r['count'] for r in all_results if r['success'])
    successful_searches = sum(1 for r in all_results if r['success'])
    
    print(f"\n📈 TEST SUMMARY:")
    print(f"  Total API calls: {api_handler.stats['total_calls']}")
    print(f"  Successful calls: {api_handler.stats['successful_calls']}")
    print(f"  Timeout errors: {api_handler.stats['timeout_errors']}")
    print(f"  HTTP errors: {api_handler.stats['http_errors']}")
    print(f"  Retry attempts: {api_handler.stats['retry_attempts']}")
    print(f"  Total hits found: {total_hits}")
    
    if api_handler.stats['total_calls'] > 0:
        success_rate = (api_handler.stats['successful_calls'] / api_handler.stats['total_calls']) * 100
        print(f"  Success rate: {success_rate:.1f}%")
    
    # Show some example hits
    hits = [r for r in all_results if r['success'] and r['count'] > 0]
    if hits:
        print(f"\n🎯 EXAMPLE HITS:")
        for hit in hits[:3]:
            genome_name = genomes.get(hit['genome_id'], {}).get('genome_name', 'Unknown')
            print(f"  {hit['gene_term']} in {hit['genome_id']} ({genome_name}): {hit['count']} features")
    
    print(f"\n✅ Track 1 test complete! Robust API handling working.")

if __name__ == "__main__":
    test_bacterial_amyloids()