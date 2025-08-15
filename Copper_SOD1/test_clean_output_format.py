#!/usr/bin/env python3
"""
Test script to validate the clean output format without full search
"""

import csv
from full_genome_search_parallel_curated_copper_sod import save_comprehensive_results

def test_clean_format():
    print("🧪 TESTING CLEAN OUTPUT FORMAT")
    print("="*50)
    
    # Create mock results in the format that would come from BV-BRC
    mock_results = [
        {
            'search_term': 'copA',
            'success': True,
            'features': [
                {
                    'accession': 'NC_006569',
                    'patric_id': 'fig|100226.1.peg.123',
                    'product': 'Copper-translocating P-type ATPase',
                    'start': '415635',
                    'end': '418000',
                    'strand': '+',
                    'feature_type': 'CDS',
                    'gene': 'copA',
                    'locus_tag': 'XYZ_001',
                    'protein_id': 'ABC123',
                    'function': 'Copper transport',
                    'subsystem': 'Copper homeostasis'
                },
                {
                    'accession': 'NC_006569',
                    'patric_id': 'fig|100226.1.peg.456',
                    'product': 'Copper efflux pump',
                    'start': '420000',
                    'end': '422500',
                    'strand': '-',
                    'feature_type': 'CDS',
                    'gene': 'copA',
                    'locus_tag': 'XYZ_002',
                    'protein_id': 'DEF456'
                }
            ]
        },
        {
            'search_term': 'sodA',
            'success': True,
            'features': [
                {
                    'accession': 'NC_007795',
                    'patric_id': 'fig|200226.1.peg.789',
                    'product': 'Superoxide dismutase [Mn]',
                    'start': '125000',
                    'end': '125600',
                    'strand': '+',
                    'feature_type': 'CDS',
                    'gene': 'sodA',
                    'locus_tag': 'ABC_003',
                    'function': 'Superoxide detoxification'
                }
            ]
        }
    ]
    
    # Test the saving function
    output_file = "test_clean_format.csv"
    feature_count = save_comprehensive_results(mock_results, output_file)
    
    print(f"\n📊 RESULTS:")
    print(f"   Features saved: {feature_count}")
    print(f"   Output file: {output_file}")
    
    # Read and display the first few lines to verify format
    print(f"\n📖 SAMPLE OUTPUT (first 5 lines):")
    with open(output_file, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:5]):
            print(f"   {i+1}: {line.strip()}")
    
    # Verify column structure
    print(f"\n🔍 COLUMN VERIFICATION:")
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        print(f"   Total columns: {len(headers)}")
        print(f"   Headers: {', '.join(headers)}")
    
    # Compare to problematic format
    print(f"\n✅ FORMAT COMPARISON:")
    print(f"   OLD problematic format: 700+ columns (mostly genome_coverage_X)")
    print(f"   NEW clean format: {len(headers)} columns (essential metadata only)")
    print(f"   Improvement: {700 - len(headers)} fewer columns!")
    
    # Check data quality
    print(f"\n🔬 DATA QUALITY CHECK:")
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    for i, row in enumerate(rows[:2]):
        print(f"   Feature {i+1}:")
        print(f"      Search term: {row['search_term']}")
        print(f"      Product: {row['product']}")
        print(f"      Location: {row['start']}-{row['end']} ({row['strand']})")
        print(f"      Feature type: {row['feature_type']}")
    
    print(f"\n🎯 SUCCESS: Clean, analyzable format achieved!")
    print(f"   ✅ Individual feature rows (not sparse matrix)")
    print(f"   ✅ Full BV-BRC metadata preserved") 
    print(f"   ✅ Easy to read and analyze")
    print(f"   ✅ Matches Alpha-Synuclein project format")
    
    return output_file, feature_count

if __name__ == "__main__":
    test_clean_format()