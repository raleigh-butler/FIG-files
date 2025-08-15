#!/usr/bin/env python3
"""
Test version of the copper-amyloid extractor
Tests with limited genomes and genes to verify functionality
"""

import requests
import json
import csv
import time
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import os

class CopperAmyloidTest:
    def __init__(self):
        """Initialize test extractor"""
        
        self.base_url = "https://www.bv-brc.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Test with just 3 key roles
        self.test_roles = {
            'CsgA': 'Major curlin subunit',
            'CopA': 'Copper-exporting ATPase',
            'SodA': 'Manganese superoxide dismutase'
        }
        
        self.search_results = {}
        self.genome_metadata = {}
    
    def load_representative_genomes(self, limit=10):
        """Load limited representative genomes for testing"""
        
        reps_file = '../reps_converted.tsv'
        representative_genomes = {}
        
        try:
            with open(reps_file, 'r') as f:
                lines = f.readlines()
                count = 0
                for line in lines[1:]:  # Skip header
                    if count >= limit:
                        break
                    parts = line.strip().split('\t')
                    if len(parts) >= 4 and parts[0] and parts[1]:  # Valid data row
                        genome_id = parts[0].strip()
                        genome_name = parts[1].strip()
                        rep100 = parts[2].strip() if len(parts) > 2 else ''
                        rep200 = parts[3].strip() if len(parts) > 3 else ''
                        
                        representative_genomes[genome_id] = {
                            'genome_name': genome_name,
                            'rep100': rep100,
                            'rep200': rep200
                        }
                        count += 1
            
            print(f"✅ Loaded {len(representative_genomes)} test genomes")
            return representative_genomes
            
        except Exception as e:
            print(f"❌ Error loading genomes: {e}")
            return {}
    
    def search_gene_in_genome_batch(self, gene_term, genome_batch):
        """Search for gene across a batch of genomes"""
        
        if not genome_batch:
            return []
        
        # Create batch query
        genome_query = ','.join(genome_batch)
        query = f'and(in(genome_id,({genome_query})),eq(gene,"{gene_term}"))'
        
        url = f"{self.base_url}/genome_feature/"
        params = f"{query}&select(genome_id,patric_id,gene,product,start,end)&limit(100)"
        full_url = f"{url}?{params}"
        
        print(f"  Searching {gene_term} in batch of {len(genome_batch)} genomes...")
        
        try:
            response = self.session.get(full_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"    ✓ Found {len(data)} {gene_term} features")
                return data
            else:
                print(f"    ✗ HTTP {response.status_code} error")
                return []
                
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return []
    
    def run_test_search(self):
        """Run the test search"""
        
        print("=== COPPER-AMYLOID EXTRACTION TEST ===")
        
        # Load test genomes
        representative_genomes = self.load_representative_genomes(limit=20)
        
        if not representative_genomes:
            print("❌ No genomes loaded!")
            return
        
        genome_ids = list(representative_genomes.keys())
        self.genome_metadata = representative_genomes
        
        # Search each role
        for role, description in self.test_roles.items():
            print(f"\n--- Searching {role} ({description}) ---")
            results = self.search_gene_in_genome_batch(role, genome_ids)
            self.search_results[role] = results
            time.sleep(1)  # Be polite to API
        
        # Create summary
        self.create_test_summary()
    
    def create_test_summary(self):
        """Create summary of test results"""
        
        print(f"\n=== TEST RESULTS SUMMARY ===")
        
        total_hits = 0
        genome_hit_count = defaultdict(int)
        
        for role, results in self.search_results.items():
            role_hits = len(results)
            total_hits += role_hits
            print(f"{role}: {role_hits} hits")
            
            # Count genomes with hits
            for result in results:
                genome_id = result.get('genome_id')
                if genome_id:
                    genome_hit_count[genome_id] += 1
        
        print(f"\nTotal hits: {total_hits}")
        print(f"Genomes with hits: {len(genome_hit_count)}")
        
        # Show top genomes
        if genome_hit_count:
            print(f"\nTop genomes by hit count:")
            sorted_genomes = sorted(genome_hit_count.items(), key=lambda x: x[1], reverse=True)
            for genome_id, hits in sorted_genomes[:5]:
                genome_name = self.genome_metadata.get(genome_id, {}).get('genome_name', 'Unknown')
                print(f"  {genome_id}: {hits} hits - {genome_name}")
        
        # Save results
        timestamp = int(time.time())
        with open(f'copper_test_results_{timestamp}.json', 'w') as f:
            json.dump({
                'search_results': self.search_results,
                'genome_metadata': self.genome_metadata,
                'summary': {
                    'total_hits': total_hits,
                    'genomes_tested': len(self.genome_metadata),
                    'roles_tested': list(self.test_roles.keys())
                }
            }, f, indent=2)
        
        print(f"\n✅ Test results saved to copper_test_results_{timestamp}.json")

if __name__ == "__main__":
    tester = CopperAmyloidTest()
    tester.run_test_search()