#!/usr/bin/env python3
"""
Quick test of copper-amyloid extraction with proper API query format
Tests the corrected BV-BRC query syntax on a small subset
"""

import requests
import json
import time

def test_bvbrc_query():
    """Test the corrected BV-BRC API query format"""
    
    # Load a few representative genomes
    with open('../reps_converted.tsv', 'r') as f:
        lines = f.readlines()
    
    # Get first 3 valid genome IDs for testing
    test_genomes = []
    for line in lines[1:]:  # Skip header
        parts = line.strip().split('\t')
        if len(parts) > 0 and parts[0]:  # Only non-empty genome IDs
            test_genomes.append(parts[0])
            if len(test_genomes) >= 3:
                break
    
    print(f"Testing with genomes: {test_genomes}")
    
    # Test with CsgA gene
    test_gene = "CsgA"
    
    # Create the query string properly quoted
    genome_query = ','.join(test_genomes)
    query = f'and(in(genome_id,({genome_query})),eq(gene,"{test_gene}"))'
    
    print(f"Query: {query}")
    
    # Make the API request
    url = f"https://www.bv-brc.org/api/genome_feature/"
    params = f"{query}&select(genome_id,patric_id,gene,product)&limit(10)"
    full_url = f"{url}?{params}"
    
    print(f"Full URL: {full_url}")
    
    try:
        response = requests.get(full_url, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Results found: {len(data)}")
            
            for item in data[:3]:  # Show first 3 results
                print(f"  - Genome: {item.get('genome_id')}")
                print(f"    Gene: {item.get('gene')}")  
                print(f"    Product: {item.get('product')}")
                print()
            
            return True
            
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    print("=== BV-BRC API Query Test ===")
    success = test_bvbrc_query()
    print(f"Test {'PASSED' if success else 'FAILED'}")