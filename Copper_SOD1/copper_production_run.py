#!/usr/bin/env python3
"""
Production Copper-Amyloid Extraction Program
Efficient implementation with progress tracking and comprehensive results
"""

import requests
import json
import csv
import time
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime

class CopperAmyloidProductionExtractor:
    def __init__(self):
        """Initialize the production extractor"""
        
        self.base_url = "https://www.bv-brc.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Full 20-role target system
        self.target_roles = {
            # TRACK 1: Bacterial Amyloids (8 roles)
            'CsgA': 'Major curlin subunit',
            'CsgB': 'Minor curlin subunit', 
            'AgfA': 'Salmonella curli major subunit',
            'TasA': 'Bacillus biofilm matrix protein',
            'FapC': 'Pseudomonas functional amyloid',
            'PSM': 'Staphylococcal phenol-soluble modulin',
            'ChpD': 'Streptomyces chaplin',
            'AmyA': 'Generic bacterial amyloid protein',
            
            # TRACK 2: Copper Systems (8 roles)
            'CtrA': 'Copper transporter A',
            'CopA': 'Copper-exporting ATPase',
            'CusA': 'Copper efflux transporter', 
            'CueO': 'Copper efflux oxidase',
            'CopZ': 'Copper chaperone',
            'CueR': 'Copper efflux regulator',
            'CusR': 'Copper-sensing regulator',
            'CopY': 'Copper operon repressor',
            
            # TRACK 3: SOD Systems (4 roles)
            'SodA': 'Manganese superoxide dismutase',
            'SodB': 'Iron superoxide dismutase', 
            'SodC': 'Copper-zinc superoxide dismutase',
            'KatA': 'Catalase'
        }
        
        self.search_results = {}
        self.genome_metadata = {}
        self.batch_size = 50  # Process 50 genomes per batch
    
    def load_representative_genomes(self, limit=None):
        """Load representative genomes with optional limit"""
        
        reps_file = 'reps_converted.tsv'
        representative_genomes = {}
        
        try:
            with open(reps_file, 'r') as f:
                lines = f.readlines()
                count = 0
                for line in lines[1:]:  # Skip header
                    if limit and count >= limit:
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
            
            print(f"✅ Loaded {len(representative_genomes)} representative genomes")
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
        params = f"{query}&select(genome_id,patric_id,gene,product,start,end)&limit(200)"
        full_url = f"{url}?{params}"
        
        try:
            response = self.session.get(full_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"    ✗ HTTP {response.status_code} error for {gene_term}")
                return []
                
        except Exception as e:
            print(f"    ✗ Error searching {gene_term}: {e}")
            return []
    
    def run_comprehensive_search(self, max_genomes=500):
        """Run comprehensive search across multiple genomes"""
        
        print("🧬 COMPREHENSIVE COPPER-AMYLOID-SOD1 EXTRACTION")
        print("=" * 80)
        
        # Load genomes
        representative_genomes = self.load_representative_genomes(limit=max_genomes)
        
        if not representative_genomes:
            print("❌ No genomes loaded!")
            return
        
        genome_ids = list(representative_genomes.keys())
        self.genome_metadata = representative_genomes
        
        print(f"🎯 Processing {len(genome_ids)} genomes across {len(self.target_roles)} roles")
        print(f"📊 Expected total searches: {len(genome_ids) * len(self.target_roles)}")
        
        # Process each role
        total_hits = 0
        genome_hit_count = defaultdict(int)
        role_progress = 0
        
        for role, description in self.target_roles.items():
            role_progress += 1
            print(f"\\n--- ROLE {role_progress}/{len(self.target_roles)}: {role} ({description}) ---")
            
            # Process genomes in batches
            all_results = []
            
            for i in range(0, len(genome_ids), self.batch_size):
                batch = genome_ids[i:i+self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(genome_ids) + self.batch_size - 1) // self.batch_size
                
                print(f"  Batch {batch_num}/{total_batches}: {len(batch)} genomes...", end=" ")
                
                batch_results = self.search_gene_in_genome_batch(role, batch)
                all_results.extend(batch_results)
                
                print(f"Found {len(batch_results)} hits")
                time.sleep(0.5)  # Rate limiting
            
            # Store results for this role
            self.search_results[role] = all_results
            role_hits = len(all_results)
            total_hits += role_hits
            
            print(f"  ✅ {role} complete: {role_hits} total hits")
            
            # Count genome hits
            for result in all_results:
                genome_id = result.get('genome_id')
                if genome_id:
                    genome_hit_count[genome_id] += 1
        
        # Generate comprehensive results
        self.create_comprehensive_output(total_hits, genome_hit_count)
        
        # Create visualizations
        self.create_visualizations()
        
        return self.search_results
    
    def create_comprehensive_output(self, total_hits, genome_hit_count):
        """Create comprehensive output files"""
        
        timestamp = int(time.time())
        
        print(f"\\n=== COMPREHENSIVE RESULTS SUMMARY ===")
        print(f"📊 Total hits across all roles: {total_hits}")
        print(f"🧬 Genomes with hits: {len(genome_hit_count)}")
        print(f"📋 Roles searched: {len(self.target_roles)}")
        
        # 1. Save raw search results
        with open(f'copper_comprehensive_results_{timestamp}.json', 'w') as f:
            json.dump({
                'search_results': self.search_results,
                'genome_metadata': self.genome_metadata,
                'summary': {
                    'total_hits': total_hits,
                    'genomes_tested': len(self.genome_metadata),
                    'genomes_with_hits': len(genome_hit_count),
                    'roles_tested': list(self.target_roles.keys()),
                    'timestamp': timestamp
                }
            }, f, indent=2)
        print(f"✅ Raw results: copper_comprehensive_results_{timestamp}.json")
        
        # 2. Create genome-role matrix
        self.create_genome_role_matrix(timestamp)
        
        # 3. Create detailed CSV
        self.create_detailed_csv(timestamp)
        
        # 4. Show top genomes
        print(f"\\n🎯 TOP GENOMES BY ROLE COUNT:")
        sorted_genomes = sorted(genome_hit_count.items(), key=lambda x: x[1], reverse=True)
        for i, (genome_id, hits) in enumerate(sorted_genomes[:10]):
            genome_name = self.genome_metadata.get(genome_id, {}).get('genome_name', 'Unknown')
            print(f"  {i+1:2d}. {genome_id}: {hits:2d} roles - {genome_name}")
    
    def create_genome_role_matrix(self, timestamp):
        """Create binary genome-role matrix similar to histidine project"""
        
        print("\\n🧬 Creating genome-role binary matrix...")
        
        # Build matrix
        all_genomes = list(self.genome_metadata.keys())
        matrix_data = []
        
        for genome_id in all_genomes:
            row = {'genome_id': genome_id}
            row['genome_name'] = self.genome_metadata[genome_id]['genome_name']
            
            # Add binary role columns
            for role in self.target_roles:
                role_results = self.search_results.get(role, [])
                has_role = any(r['genome_id'] == genome_id for r in role_results)
                row[role] = 1 if has_role else 0
            
            matrix_data.append(row)
        
        # Save as CSV
        csv_filename = f'copper_genome_role_matrix_{timestamp}.csv'
        with open(csv_filename, 'w', newline='') as f:
            fieldnames = ['genome_id', 'genome_name'] + list(self.target_roles.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matrix_data)
        
        print(f"✅ Genome-role matrix: {csv_filename}")
    
    def create_detailed_csv(self, timestamp):
        """Create detailed feature-level CSV"""
        
        print("\\n📋 Creating detailed feature CSV...")
        
        csv_filename = f'copper_detailed_features_{timestamp}.csv'
        with open(csv_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'genome_id', 'genome_name', 'role', 'gene', 'product', 
                'patric_id', 'start', 'end', 'track'
            ])
            
            # Determine track for each role
            track_map = {}
            amyloid_roles = ['CsgA', 'CsgB', 'AgfA', 'TasA', 'FapC', 'PSM', 'ChpD', 'AmyA']
            copper_roles = ['CtrA', 'CopA', 'CusA', 'CueO', 'CopZ', 'CueR', 'CusR', 'CopY']
            sod_roles = ['SodA', 'SodB', 'SodC', 'KatA']
            
            for role in self.target_roles:
                if role in amyloid_roles:
                    track_map[role] = 'AMYLOID'
                elif role in copper_roles:
                    track_map[role] = 'COPPER'
                elif role in sod_roles:
                    track_map[role] = 'SOD'
                else:
                    track_map[role] = 'OTHER'
            
            # Write all features
            for role, results in self.search_results.items():
                for result in results:
                    genome_id = result.get('genome_id', '')
                    genome_name = self.genome_metadata.get(genome_id, {}).get('genome_name', '')
                    
                    writer.writerow([
                        genome_id,
                        genome_name,
                        role,
                        result.get('gene', ''),
                        result.get('product', ''),
                        result.get('patric_id', ''),
                        result.get('start', ''),
                        result.get('end', ''),
                        track_map.get(role, 'OTHER')
                    ])
        
        print(f"✅ Detailed features: {csv_filename}")
    
    def create_visualizations(self):
        """Create comprehensive visualizations"""
        
        print("\\n📊 Creating visualizations...")
        
        try:
            # 1. Role distribution plot
            role_counts = {role: len(results) for role, results in self.search_results.items()}
            
            plt.figure(figsize=(15, 8))
            
            # Separate by track
            amyloid_roles = ['CsgA', 'CsgB', 'AgfA', 'TasA', 'FapC', 'PSM', 'ChpD', 'AmyA']
            copper_roles = ['CtrA', 'CopA', 'CusA', 'CueO', 'CopZ', 'CueR', 'CusR', 'CopY']
            sod_roles = ['SodA', 'SodB', 'SodC', 'KatA']
            
            colors = []
            for role in role_counts.keys():
                if role in amyloid_roles:
                    colors.append('#FF6B6B')  # Red for amyloids
                elif role in copper_roles:
                    colors.append('#4ECDC4')  # Teal for copper
                elif role in sod_roles:
                    colors.append('#45B7D1')  # Blue for SOD
                else:
                    colors.append('#96CEB4')  # Green for other
            
            bars = plt.bar(range(len(role_counts)), list(role_counts.values()), color=colors)
            plt.xlabel('Copper-Amyloid-SOD Roles')
            plt.ylabel('Number of Features Found')
            plt.title('Copper-Amyloid-SOD1 System Distribution Across Representative Genomes')
            plt.xticks(range(len(role_counts)), list(role_counts.keys()), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom', fontsize=9)
            
            # Add legend
            legend_elements = [
                plt.Rectangle((0,0),1,1, color='#FF6B6B', label='Bacterial Amyloids'),
                plt.Rectangle((0,0),1,1, color='#4ECDC4', label='Copper Homeostasis'),
                plt.Rectangle((0,0),1,1, color='#45B7D1', label='SOD Systems'),
            ]
            plt.legend(handles=legend_elements, loc='upper right')
            
            plt.tight_layout()
            plt.savefig('copper_role_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print("✅ Role distribution plot: copper_role_distribution.png")
            
            # 2. Track summary plot
            track_totals = {
                'Bacterial Amyloids': sum(role_counts.get(role, 0) for role in amyloid_roles),
                'Copper Homeostasis': sum(role_counts.get(role, 0) for role in copper_roles),
                'SOD Systems': sum(role_counts.get(role, 0) for role in sod_roles)
            }
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(track_totals.keys(), track_totals.values(), 
                          color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
            plt.ylabel('Total Features Found')
            plt.title('Three-Track System Summary: Amyloids + Copper + SOD')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig('copper_track_summary.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print("✅ Track summary plot: copper_track_summary.png")
            
        except Exception as e:
            print(f"⚠️  Visualization error: {e}")

if __name__ == "__main__":
    # Run comprehensive extraction
    extractor = CopperAmyloidProductionExtractor()
    
    # Process 500 genomes for comprehensive coverage
    results = extractor.run_comprehensive_search(max_genomes=500)
    
    print("\\n🎯 EXTRACTION COMPLETE!")
    print("📁 Output files generated with comprehensive copper-amyloid-SOD data")
    print("🧬 Ready for neural network training and biological analysis")