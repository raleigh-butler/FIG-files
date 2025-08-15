#!/usr/bin/env python3
"""
Integrated Copper-Amyloid-SOD1 Data Extractor for BV-BRC

This script implements the integrated search strategy combining:
1. Bacterial amyloid systems (CsgA/CsgB focus)
2. Copper homeostasis pathways  
3. Superoxide dismutase systems

Based on the proven methodology from Histidine/Alpha-synuclein projects.
Targets gut microbiome relevance for Parkinson's disease research.
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

class CopperAmyloidExtractor:
    def __init__(self):
        """Initialize the integrated BV-BRC extractor"""
        
        self.base_url = "https://www.bv-brc.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # TRACK 1: Bacterial amyloid systems (your high-priority targets)
        self.amyloid_genes = {
            'CsgA': 'Major curlin subunit',
            'CsgB': 'Minor curlin subunit', 
            'AgfA': 'Salmonella curli major subunit',
            'AgfB': 'Salmonella curli minor subunit',
            'TasA': 'Bacillus biofilm matrix protein',
            'FapC': 'Pseudomonas functional amyloid',
            'PSM': 'Staphylococcal phenol-soluble modulin',
            'ChpD': 'Streptomyces chaplin'
        }
        
        # TRACK 2: Copper homeostasis systems
        self.copper_genes = {
            'CtrA': 'Copper transporter A',
            'CopA': 'Copper-exporting ATPase',
            'CusA': 'Copper efflux transporter', 
            'CueO': 'Copper efflux oxidase',
            'CopZ': 'Copper chaperone',
            'CueR': 'Copper efflux regulator',
            'CusR': 'Copper-sensing regulator',
            'CopY': 'Copper operon repressor'
        }
        
        # TRACK 3: SOD systems
        self.sod_genes = {
            'SodA': 'Manganese superoxide dismutase',
            'SodB': 'Iron superoxide dismutase', 
            'SodC': 'Copper-zinc superoxide dismutase',
            'CAT': 'Catalase'
        }
        
        # Combined target roles (20 total)
        self.target_roles = {**self.amyloid_genes, **self.copper_genes, **self.sod_genes}
        
        # Load representative genomes
        self.representative_genomes = self.load_representative_genomes()
        
        print(f"Initialized Copper-Amyloid-SOD1 extractor")
        print(f"Target roles: {len(self.target_roles)} ({len(self.amyloid_genes)} amyloid + {len(self.copper_genes)} copper + {len(self.sod_genes)} SOD)")
        print(f"Representative genomes loaded: {len(self.representative_genomes)}")
    
    def load_representative_genomes(self):
        """Load representative genomes from reps_converted.tsv"""
        
        reps_file = '../reps_converted.tsv'
        representative_genomes = {}
        
        try:
            with open(reps_file, 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip header
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
            
            print(f"✅ Loaded {len(representative_genomes)} representative genomes from {reps_file}")
            return representative_genomes
            
        except FileNotFoundError:
            print(f"❌ Representative genomes file not found: {reps_file}")
            print("❌ Falling back to broad search approach")
            return {}
        except Exception as e:
            print(f"❌ Error loading representative genomes: {e}")
            return {}
    
    def search_gene_in_genomes(self, gene_term, search_type='gene'):
        """Search for a specific gene/product across all representative genomes"""
        
        if not self.representative_genomes:
            print("⚠️  No representative genomes loaded, using broad search")
            return self.execute_bvbrc_search(gene_term, search_type)
        
        print(f"\n🔍 Searching for {gene_term} across {len(self.representative_genomes)} representative genomes...")
        
        all_results = []
        success_count = 0
        
        # Search in batches to avoid overwhelming the API
        genome_ids = list(self.representative_genomes.keys())
        batch_size = 50  # Process 50 genomes at a time
        
        for i in range(0, len(genome_ids), batch_size):
            batch_ids = genome_ids[i:i+batch_size]
            
            try:
                batch_results = self.search_gene_in_genome_batch(gene_term, batch_ids, search_type)
                if batch_results:
                    all_results.extend(batch_results)
                    success_count += len(batch_results)
                
                # Be respectful to API
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error in batch {i//batch_size + 1}: {e}")
                continue
        
        print(f"✅ Found {success_count} results for {gene_term} across representative genomes")
        return all_results
    
    def search_gene_in_genome_batch(self, gene_term, genome_ids, search_type='gene'):
        """Search for a gene across a batch of specific genomes"""
        
        url = f"{self.base_url}/genome_feature/"
        
        # Create OR query for multiple genome IDs
        genome_query = ','.join(genome_ids)
        
        if search_type == 'gene':
            # Search for gene name within specific genomes
            query = f'and(in(genome_id,({genome_query})),eq(gene,"{gene_term}"))'
        elif search_type == 'product':
            # Search for product description within specific genomes  
            query = f'and(in(genome_id,({genome_query})),keyword("{gene_term}"))'
        else:
            # General search within specific genomes
            query = f'and(in(genome_id,({genome_query})),keyword("{gene_term}"))'
        
        params = {
            'q': query,
            'rows': 10000,  # Large enough to capture all results from batch
            'fl': 'genome_id,genome_name,patric_id,gene,product,feature_type,organism_name,taxon_id,start,end'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                else:
                    return []
            else:
                print(f"❌ API error {response.status_code} for {gene_term}")
                return []
                
        except Exception as e:
            print(f"❌ Request error for {gene_term}: {e}")
            return []

    def search_amyloid_systems(self):
        """Search for bacterial amyloid systems (Track 1) - Targeted Approach"""
        
        print("=" * 60)
        print("TRACK 1: BACTERIAL AMYLOID SYSTEMS (TARGETED)")
        print("=" * 60)
        
        # High priority gene searches using targeted genome approach
        high_priority_genes = [
            'CsgA',   # Major curlin subunit
            'CsgB',   # Minor curlin subunit
            'TasA',   # Bacillus biofilm matrix
            'AgfA',   # Salmonella curli major
            'AgfB',   # Salmonella curli minor
            'FapC'    # Pseudomonas functional amyloid
        ]
        
        amyloid_results = []
        
        for gene_name in high_priority_genes:
            print(f"\n🧬 Searching for {gene_name} in representative genomes...")
            
            try:
                results = self.search_gene_in_genomes(gene_name, 'gene')
                if results:
                    amyloid_results.extend(results)
                else:
                    print(f"❌ No results for {gene_name}")
                    
            except Exception as e:
                print(f"❌ Error searching {gene_name}: {e}")
        
        # Medium priority product searches (more selective)
        product_searches = [
            '"phenol soluble modulin"',
            '"curli"',
            '"biofilm matrix"'
        ]
        
        for product_term in product_searches:
            print(f"\n🔍 Product search: {product_term}...")
            
            try:
                results = self.search_gene_in_genomes(product_term, 'product')
                if results:
                    amyloid_results.extend(results)
                    
            except Exception as e:
                print(f"❌ Error in product search {product_term}: {e}")
        
        print(f"\n📊 TRACK 1 SUMMARY: {len(amyloid_results)} total amyloid system results")
        return amyloid_results
    
    def search_copper_systems(self):
        """Search for copper homeostasis systems (Track 2) - Targeted Approach"""
        
        print("\n" + "=" * 60)
        print("TRACK 2: COPPER HOMEOSTASIS SYSTEMS (TARGETED)")
        print("=" * 60)
        
        # Core copper genes using targeted genome approach
        copper_genes = [
            'copA',   # Copper-exporting ATPase
            'cusA',   # Copper efflux transporter
            'cueO',   # Copper efflux oxidase
            'cueR',   # Copper efflux regulator
            'copZ',   # Copper chaperone
            'cusR',   # Copper-sensing regulator
            'copY',   # Copper operon repressor
            'ctrA'    # Copper transporter
        ]
        
        copper_results = []
        
        for gene_name in copper_genes:
            print(f"\n🧬 Searching for {gene_name} in representative genomes...")
            
            try:
                results = self.search_gene_in_genomes(gene_name, 'gene')
                if results:
                    copper_results.extend(results)
                else:
                    print(f"❌ No results for {gene_name}")
                    
            except Exception as e:
                print(f"❌ Error searching {gene_name}: {e}")
        
        # Targeted functional copper searches
        copper_product_searches = [
            '"copper transporter"',
            '"copper resistance"',
            '"copper efflux"'
        ]
        
        for product_term in copper_product_searches:
            print(f"\n🔍 Copper product search: {product_term}...")
            
            try:
                results = self.search_gene_in_genomes(product_term, 'product')
                if results:
                    copper_results.extend(results)
                    
            except Exception as e:
                print(f"❌ Error in copper product search {product_term}: {e}")
        
        print(f"\n📊 TRACK 2 SUMMARY: {len(copper_results)} total copper system results")
        return copper_results
    
    def search_sod_systems(self):
        """Search for superoxide dismutase systems (Track 3) - Targeted Approach"""
        
        print("\n" + "=" * 60)
        print("TRACK 3: SUPEROXIDE DISMUTASE SYSTEMS (TARGETED)")
        print("=" * 60)
        
        # SOD and antioxidant genes using targeted genome approach
        sod_genes = [
            'sodA',   # Manganese superoxide dismutase
            'sodB',   # Iron superoxide dismutase  
            'sodC',   # Copper-zinc superoxide dismutase
            'katA',   # Catalase A
            'katB',   # Catalase B
            'katE'    # Catalase E
        ]
        
        sod_results = []
        
        for gene_name in sod_genes:
            print(f"\n🧬 Searching for {gene_name} in representative genomes...")
            
            try:
                results = self.search_gene_in_genomes(gene_name, 'gene')
                if results:
                    sod_results.extend(results)
                else:
                    print(f"❌ No results for {gene_name}")
                    
            except Exception as e:
                print(f"❌ Error searching {gene_name}: {e}")
        
        # Targeted SOD functional searches
        sod_product_searches = [
            '"superoxide dismutase"',
            '"catalase"'
        ]
        
        for product_term in sod_product_searches:
            print(f"\n🔍 SOD product search: {product_term}...")
            
            try:
                results = self.search_gene_in_genomes(product_term, 'product')
                if results:
                    sod_results.extend(results)
                    
            except Exception as e:
                print(f"❌ Error in SOD product search {product_term}: {e}")
        
        print(f"\n📊 TRACK 3 SUMMARY: {len(sod_results)} total SOD system results")
        return sod_results
    
    def execute_bvbrc_search(self, search_term, search_type='gene', limit=5000):
        """Execute a single BV-BRC API search"""
        
        url = f"{self.base_url}/genome_feature/"
        
        # Different query strategies based on search type
        if search_type == 'gene':
            query_params = {
                'q': f'gene:{search_term}',
                'rows': limit,
                'fl': 'genome_id,genome_name,patric_id,gene,product,feature_type,organism_name,taxon_id'
            }
        elif search_type == 'product':
            query_params = {
                'q': f'product:{search_term}',
                'rows': limit,
                'fl': 'genome_id,genome_name,patric_id,gene,product,feature_type,organism_name,taxon_id'
            }
        else:
            query_params = {
                'q': search_term,
                'rows': limit,
                'fl': 'genome_id,genome_name,patric_id,gene,product,feature_type,organism_name,taxon_id'
            }
        
        try:
            response = self.session.get(url, params=query_params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                else:
                    print(f"Unexpected response format for {search_term}")
                    return []
            else:
                print(f"API error {response.status_code} for {search_term}")
                return []
                
        except Exception as e:
            print(f"Request error for {search_term}: {e}")
            return []
    
    def build_integrated_dataset(self):
        """Build the integrated copper-amyloid-SOD dataset"""
        
        print("\n" + "=" * 80)
        print("INTEGRATED COPPER-AMYLOID-SOD1 DATASET CONSTRUCTION")
        print("=" * 80)
        
        # Execute all three search tracks
        amyloid_results = self.search_amyloid_systems()
        copper_results = self.search_copper_systems()  
        sod_results = self.search_sod_systems()
        
        # Combine all results
        all_results = amyloid_results + copper_results + sod_results
        print(f"\n📊 COMBINED RESULTS: {len(all_results)} total features")
        
        # Build genome-role matrix (results are already from representative genomes)
        genome_roles, genome_info = self.build_genome_role_matrix(all_results)
        
        # Determine subsystem states
        genome_states = self.determine_integrated_states(genome_roles)
        
        # Build final dataset
        dataset_rows = self.build_final_dataset(genome_roles, genome_info, genome_states)
        
        return dataset_rows, genome_roles
    
    def build_genome_role_matrix(self, results):
        """Build genome-role binary matrix from integrated results"""
        
        print("\n🧬 Building integrated genome-role matrix...")
        
        genome_roles = defaultdict(lambda: {role: 0 for role in self.target_roles.keys()})
        genome_info = {}
        role_matches = defaultdict(list)
        
        for result in results:
            try:
                genome_id = str(result.get('genome_id', ''))
                if not genome_id:
                    continue
                
                # Store genome metadata (use representative genome info when available)
                rep_info = self.representative_genomes.get(genome_id, {})
                genome_info[genome_id] = {
                    'genome_name': result.get('genome_name', rep_info.get('genome_name', f'Genome {genome_id}')),
                    'organism_name': result.get('organism_name', ''),
                    'taxon_id': result.get('taxon_id', ''),
                    'gene': result.get('gene', ''),
                    'product': result.get('product', ''),
                    'rep100': rep_info.get('rep100', genome_id),
                    'rep200': rep_info.get('rep200', genome_id)
                }
                
                # Match against target roles
                gene_name = str(result.get('gene', '')).lower()
                product = str(result.get('product', '')).lower()
                
                # Role matching logic
                for role_id, role_desc in self.target_roles.items():
                    role_id_lower = role_id.lower()
                    role_desc_lower = role_desc.lower()
                    
                    # Direct gene name match
                    if role_id_lower in gene_name:
                        genome_roles[genome_id][role_id] = 1
                        role_matches[role_id].append(genome_id)
                        continue
                    
                    # Product description match
                    if any(keyword in product for keyword in [role_id_lower, role_desc_lower]):
                        genome_roles[genome_id][role_id] = 1
                        role_matches[role_id].append(genome_id)
                        continue
                    
                    # Specific matching rules
                    if self.match_specific_role(role_id, gene_name, product):
                        genome_roles[genome_id][role_id] = 1
                        role_matches[role_id].append(genome_id)
                        
            except Exception as e:
                print(f"Error processing result: {e}")
                continue
        
        # Print statistics
        print(f"📊 Matrix statistics:")
        print(f"   Total genomes: {len(genome_roles)}")
        
        role_counts = {}
        for role_id in self.target_roles.keys():
            count = len(set(role_matches[role_id]))
            role_counts[role_id] = count
            coverage = (count / len(genome_roles)) * 100 if genome_roles else 0
            print(f"   {role_id}: {count} genomes ({coverage:.1f}%)")
        
        return dict(genome_roles), genome_info
    
    def match_specific_role(self, role_id, gene_name, product):
        """Apply specific matching rules for different role types"""
        
        # Amyloid-specific matching
        if role_id in self.amyloid_genes:
            if role_id == 'CsgA' and any(term in product for term in ['curli', 'major subunit', 'biofilm']):
                return True
            if role_id == 'CsgB' and any(term in product for term in ['curli', 'minor subunit', 'nucleation']):
                return True
            if role_id == 'TasA' and any(term in product for term in ['biofilm matrix', 'tas']):
                return True
            if role_id == 'PSM' and any(term in product for term in ['phenol', 'modulin', 'psm']):
                return True
        
        # Copper-specific matching  
        if role_id in self.copper_genes:
            if 'copper' in product and any(term in product for term in ['transport', 'efflux', 'resistance']):
                return True
            if role_id == 'CopA' and any(term in product for term in ['p-type atpase', 'copper export']):
                return True
            if role_id == 'CueR' and any(term in product for term in ['regulator', 'transcriptional']):
                return True
        
        # SOD-specific matching
        if role_id in self.sod_genes:
            if role_id == 'SodA' and any(term in product for term in ['manganese', 'superoxide']):
                return True
            if role_id == 'SodC' and any(term in product for term in ['copper', 'zinc', 'superoxide']):
                return True
            if role_id == 'CAT' and 'catalase' in product:
                return True
        
        return False
    
    def determine_integrated_states(self, genome_roles):
        """Determine integrated subsystem states based on amyloid-copper-SOD patterns"""
        
        print("\n🎯 Determining integrated subsystem states...")
        
        genome_states = {}
        state_counts = defaultdict(int)
        
        for genome_id, roles in genome_roles.items():
            
            # Count systems present
            amyloid_count = sum(roles[role] for role in self.amyloid_genes.keys())
            copper_count = sum(roles[role] for role in self.copper_genes.keys())
            sod_count = sum(roles[role] for role in self.sod_genes.keys())
            
            total_systems = amyloid_count + copper_count + sod_count
            
            # Integrated state logic
            if amyloid_count >= 2 and copper_count >= 2 and sod_count >= 1:
                state = 'active'  # Complete amyloid-copper-SOD system
            elif (amyloid_count >= 1 and copper_count >= 2) or (copper_count >= 3 and sod_count >= 1):
                state = 'likely'  # Strong partial system
            elif total_systems >= 3:
                state = 'unknown'  # Mixed patterns
            elif total_systems >= 1:
                state = 'unknown'  # Single system components
            else:
                state = 'inactive'  # No relevant systems
            
            genome_states[genome_id] = state
            state_counts[state] += 1
        
        print("📊 State distribution:")
        for state, count in state_counts.items():
            percentage = (count / len(genome_roles)) * 100 if genome_roles else 0
            print(f"   {state}: {count} genomes ({percentage:.1f}%)")
        
        return genome_states
    
    def build_final_dataset(self, genome_roles, genome_info, genome_states):
        """Build final dataset in Histidine-compatible format"""
        
        print("\n📋 Building final integrated dataset...")
        
        dataset_rows = []
        
        for genome_id, roles in genome_roles.items():
            info = genome_info.get(genome_id, {})
            state = genome_states.get(genome_id, 'unknown')
            
            # Get representative genome info
            rep100 = info.get('rep100', genome_id)
            rep200 = info.get('rep200', genome_id)
            
            # Create row matching Histidine format  
            row = {
                'genome_id': genome_id,
                'State': state,
                'rep100': rep100,
                'genome_name': info.get('genome_name', f'Genome {genome_id}'),
                'organism_name': info.get('organism_name', ''),
                'RepGen.100': rep100,
                'RepGen.200': rep200,
            }
            
            # Add all role columns (binary)
            for role_id in self.target_roles.keys():
                row[role_id] = roles[role_id]
            
            # Add placeholder taxonomy (to be filled by NCBI validation)
            row.update({
                'kingdom': 'Unknown',
                'phylum': 'Unknown', 
                'class': 'Unknown',
                'order': 'Unknown',
                'family': 'Unknown',
                'genus': 'Unknown',
                'species': 'Unknown'
            })
            
            # Add system summary features
            row.update({
                'amyloid_systems': sum(roles[role] for role in self.amyloid_genes.keys()),
                'copper_systems': sum(roles[role] for role in self.copper_genes.keys()),
                'sod_systems': sum(roles[role] for role in self.sod_genes.keys()),
                'total_systems': sum(roles.values())
            })
            
            dataset_rows.append(row)
        
        print(f"✅ Built final dataset with {len(dataset_rows)} genomes")
        return dataset_rows
    
    def save_integrated_dataset(self, dataset_rows):
        """Save the integrated dataset in standardized format"""
        
        if not dataset_rows:
            print("❌ No dataset to save")
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Main dataset file
        dataset_file = f"copper_amyloid_sod_dataset_{timestamp}.tsv"
        fieldnames = list(dataset_rows[0].keys())
        
        with open(dataset_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            writer.writerows(dataset_rows)
        
        print(f"✅ Main dataset saved: {dataset_file}")
        
        # Roles definition file
        roles_file = f"copper_amyloid_sod_roles_{timestamp}.tsv"
        with open(roles_file, 'w', encoding='utf-8') as f:
            for role_id, role_desc in self.target_roles.items():
                f.write(f"{role_id}\t{role_desc}\n")
        
        print(f"✅ Roles file saved: {roles_file}")
        
        # Binary matrix for neural network
        binary_file = f"copper_amyloid_sod_binary_{timestamp}.tsv"
        binary_fields = ['genome_id', 'State', 'rep100'] + list(self.target_roles.keys())
        
        with open(binary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=binary_fields, delimiter='\t')
            writer.writeheader()
            for row in dataset_rows:
                binary_row = {field: row[field] for field in binary_fields if field in row}
                writer.writerow(binary_row)
        
        print(f"✅ Binary matrix saved: {binary_file}")
        
        # Summary statistics
        summary = {
            'dataset_info': {
                'total_genomes': len(dataset_rows),
                'total_roles': len(self.target_roles),
                'amyloid_roles': len(self.amyloid_genes),
                'copper_roles': len(self.copper_genes),
                'sod_roles': len(self.sod_genes),
                'extraction_method': 'BV-BRC_integrated_amyloid_copper_sod',
                'gut_relevance_filter': True
            },
            'role_statistics': {
                'amyloid_coverage': {role: sum(1 for r in dataset_rows if r.get(role, 0) == 1) 
                                   for role in self.amyloid_genes.keys()},
                'copper_coverage': {role: sum(1 for r in dataset_rows if r.get(role, 0) == 1) 
                                  for role in self.copper_genes.keys()},
                'sod_coverage': {role: sum(1 for r in dataset_rows if r.get(role, 0) == 1) 
                               for role in self.sod_genes.keys()}
            },
            'state_distribution': {
                state: len([r for r in dataset_rows if r['State'] == state])
                for state in set(r['State'] for r in dataset_rows)
            },
            'system_statistics': {
                'avg_amyloid_systems': sum(r.get('amyloid_systems', 0) for r in dataset_rows) / len(dataset_rows),
                'avg_copper_systems': sum(r.get('copper_systems', 0) for r in dataset_rows) / len(dataset_rows),
                'avg_sod_systems': sum(r.get('sod_systems', 0) for r in dataset_rows) / len(dataset_rows)
            },
            'created': timestamp
        }
        
        summary_file = f"copper_amyloid_sod_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Summary saved: {summary_file}")
        
        # Generate visualizations
        self.create_visualizations(dataset_rows, summary, timestamp)
        
        return dataset_file, roles_file, binary_file, summary_file
    
    def create_visualizations(self, dataset_rows, summary, timestamp):
        """Create comprehensive visualizations of the dataset"""
        
        print("\n📊 Generating visualizations...")
        
        # Set style for professional plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(dataset_rows)
        
        # Create visualization directory
        viz_dir = f"copper_amyloid_visualizations_{timestamp}"
        os.makedirs(viz_dir, exist_ok=True)
        
        # 1. System Distribution Overview
        self.plot_system_distribution(df, viz_dir)
        
        # 2. Role Coverage Analysis
        self.plot_role_coverage(df, viz_dir)
        
        # 3. State Distribution
        self.plot_state_distribution(df, viz_dir)
        
        # 4. System Integration Heatmap
        self.plot_system_integration(df, viz_dir)
        
        # 5. Track-specific Analysis
        self.plot_track_analysis(df, viz_dir)
        
        # 6. Co-occurrence Matrix
        self.plot_cooccurrence_matrix(df, viz_dir)
        
        # 7. Taxonomic Distribution (if available)
        self.plot_taxonomic_distribution(df, viz_dir)
        
        print(f"✅ Visualizations saved in: {viz_dir}/")
    
    def plot_system_distribution(self, df, viz_dir):
        """Plot distribution of amyloid, copper, and SOD systems"""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Copper-Amyloid-SOD System Distribution', fontsize=16, fontweight='bold')
        
        # System counts
        system_counts = {
            'Amyloid Systems': df['amyloid_systems'].value_counts().sort_index(),
            'Copper Systems': df['copper_systems'].value_counts().sort_index(),
            'SOD Systems': df['sod_systems'].value_counts().sort_index(),
            'Total Systems': df['total_systems'].value_counts().sort_index()
        }
        
        for idx, (system_name, counts) in enumerate(system_counts.items()):
            ax = axes[idx // 2, idx % 2]
            counts.plot(kind='bar', ax=ax, color=sns.color_palette("husl", len(counts)))
            ax.set_title(f'{system_name} per Genome')
            ax.set_xlabel('Number of Systems')
            ax.set_ylabel('Number of Genomes')
            ax.tick_params(axis='x', rotation=0)
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/system_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_role_coverage(self, df, viz_dir):
        """Plot coverage of individual roles across genomes"""
        
        # Calculate role frequencies
        role_frequencies = {}
        for role in self.target_roles.keys():
            if role in df.columns:
                role_frequencies[role] = df[role].sum()
        
        # Create grouped bar plot by track
        fig, ax = plt.subplots(figsize=(15, 8))
        
        tracks = {
            'Amyloid': list(self.amyloid_genes.keys()),
            'Copper': list(self.copper_genes.keys()), 
            'SOD': list(self.sod_genes.keys())
        }
        
        x_pos = []
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        track_positions = []
        
        current_pos = 0
        for track_idx, (track_name, roles) in enumerate(tracks.items()):
            track_pos = []
            for role in roles:
                if role in role_frequencies:
                    frequency = role_frequencies[role]
                    percentage = (frequency / len(df)) * 100
                    
                    ax.bar(current_pos, percentage, color=colors[track_idx], alpha=0.8)
                    ax.text(current_pos, percentage + 1, f'{frequency}', 
                           ha='center', va='bottom', fontsize=8)
                    track_pos.append(current_pos)
                    current_pos += 1
            
            if track_pos:
                track_positions.append((track_name, np.mean(track_pos)))
        
        # Customize plot
        ax.set_xlabel('Roles')
        ax.set_ylabel('Coverage Percentage')
        ax.set_title('Role Coverage Across Representative Genomes', fontsize=14, fontweight='bold')
        
        # Add track labels
        role_names = []
        role_positions = []
        current_pos = 0
        for track_name, roles in tracks.items():
            for role in roles:
                if role in role_frequencies:
                    role_names.append(role)
                    role_positions.append(current_pos)
                    current_pos += 1
        
        ax.set_xticks(role_positions)
        ax.set_xticklabels(role_names, rotation=45, ha='right')
        
        # Add track dividers and labels
        for i, (track_name, center_pos) in enumerate(track_positions):
            ax.text(center_pos, ax.get_ylim()[1] * 0.95, track_name, 
                   ha='center', va='top', fontweight='bold', 
                   color=colors[i], fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/role_coverage.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_state_distribution(self, df, viz_dir):
        """Plot distribution of subsystem states"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # State counts
        state_counts = df['State'].value_counts()
        colors = ['#2ECC71', '#F39C12', '#E74C3C', '#95A5A6']
        
        # Bar plot
        state_counts.plot(kind='bar', ax=ax1, color=colors[:len(state_counts)])
        ax1.set_title('Subsystem State Distribution')
        ax1.set_xlabel('State')
        ax1.set_ylabel('Number of Genomes')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add percentages on bars
        total = len(df)
        for i, (state, count) in enumerate(state_counts.items()):
            percentage = (count / total) * 100
            ax1.text(i, count + total * 0.01, f'{percentage:.1f}%', 
                    ha='center', va='bottom', fontweight='bold')
        
        # Pie chart
        ax2.pie(state_counts.values, labels=state_counts.index, autopct='%1.1f%%',
                colors=colors[:len(state_counts)], startangle=90)
        ax2.set_title('Subsystem State Proportions')
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/state_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_system_integration(self, df, viz_dir):
        """Plot system integration patterns"""
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create integration matrix
        integration_data = []
        for _, row in df.iterrows():
            integration_data.append([
                row['amyloid_systems'],
                row['copper_systems'], 
                row['sod_systems']
            ])
        
        integration_df = pd.DataFrame(integration_data, 
                                    columns=['Amyloid Systems', 'Copper Systems', 'SOD Systems'])
        
        # Create correlation heatmap
        correlation_matrix = integration_df.corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='RdYlBu_r', center=0,
                   square=True, ax=ax, cbar_kws={'label': 'Correlation Coefficient'})
        ax.set_title('System Integration Correlation Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/system_integration.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_track_analysis(self, df, viz_dir):
        """Plot detailed analysis for each track"""
        
        fig, axes = plt.subplots(3, 1, figsize=(15, 18))
        
        tracks = [
            ('Amyloid', self.amyloid_genes, '#FF6B6B'),
            ('Copper', self.copper_genes, '#4ECDC4'),
            ('SOD', self.sod_genes, '#45B7D1')
        ]
        
        for idx, (track_name, genes, color) in enumerate(tracks):
            ax = axes[idx]
            
            # Calculate presence/absence for each gene in this track
            gene_presence = {}
            for gene in genes.keys():
                if gene in df.columns:
                    gene_presence[gene] = df[gene].sum()
            
            if gene_presence:
                genes_list = list(gene_presence.keys())
                counts = list(gene_presence.values())
                
                bars = ax.bar(genes_list, counts, color=color, alpha=0.8)
                ax.set_title(f'{track_name} Systems: Gene Presence Across Genomes', 
                           fontsize=12, fontweight='bold')
                ax.set_xlabel('Genes')
                ax.set_ylabel('Number of Genomes')
                
                # Add value labels on bars
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + len(df) * 0.01,
                           f'{count}', ha='center', va='bottom', fontweight='bold')
                           
                # Add percentage labels
                for i, count in enumerate(counts):
                    percentage = (count / len(df)) * 100
                    ax.text(i, count/2, f'{percentage:.1f}%', 
                           ha='center', va='center', color='white', fontweight='bold')
                
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/track_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_cooccurrence_matrix(self, df, viz_dir):
        """Plot co-occurrence matrix of roles"""
        
        # Create binary matrix for roles
        role_columns = [col for col in df.columns if col in self.target_roles.keys()]
        if not role_columns:
            return
        
        role_matrix = df[role_columns].astype(int)
        
        # Calculate co-occurrence
        cooccurrence = role_matrix.T.dot(role_matrix)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(14, 12))
        
        # Mask for upper triangle
        mask = np.triu(np.ones_like(cooccurrence, dtype=bool))
        
        sns.heatmap(cooccurrence, mask=mask, annot=True, fmt='d', cmap='YlOrRd',
                   square=True, ax=ax, cbar_kws={'label': 'Co-occurrence Count'})
        ax.set_title('Role Co-occurrence Matrix', fontsize=14, fontweight='bold')
        ax.set_xlabel('Roles')
        ax.set_ylabel('Roles')
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/cooccurrence_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_taxonomic_distribution(self, df, viz_dir):
        """Plot taxonomic distribution if taxonomy data available"""
        
        if 'genus' not in df.columns or df['genus'].isna().all():
            # Create placeholder plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Taxonomic data not yet available\n(Run NCBI taxonomy validation)', 
                   ha='center', va='center', fontsize=14, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            ax.set_title('Taxonomic Distribution (Pending NCBI Validation)', 
                        fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(f'{viz_dir}/taxonomic_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            return
        
        # If taxonomy data is available, create distribution plots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Taxonomic Distribution', fontsize=16, fontweight='bold')
        
        taxonomic_levels = ['kingdom', 'phylum', 'class', 'order']
        
        for idx, level in enumerate(taxonomic_levels):
            if level in df.columns:
                ax = axes[idx // 2, idx % 2]
                
                level_counts = df[level].value_counts().head(10)  # Top 10
                level_counts.plot(kind='bar', ax=ax)
                ax.set_title(f'Top {level.capitalize()} Distribution')
                ax.set_xlabel(level.capitalize())
                ax.set_ylabel('Number of Genomes')
                ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(f'{viz_dir}/taxonomic_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()


def main():
    """Main execution function"""
    
    # Change to Copper_SOD1 directory
    os.chdir('/Users/raleigh/Desktop/FIG/Copper_SOD1')
    
    print("🧬 INTEGRATED COPPER-AMYLOID-SOD1 DATASET EXTRACTOR")
    print("=" * 80)
    print("Combining bacterial amyloids + copper homeostasis + superoxide dismutase")
    print("Focus: Gut microbiome relevance for Parkinson's disease research")
    print("=" * 80)
    
    # Build integrated dataset
    extractor = CopperAmyloidExtractor()
    dataset_rows, genome_roles = extractor.build_integrated_dataset()
    
    if dataset_rows:
        files = extractor.save_integrated_dataset(dataset_rows)
        
        print("\n" + "=" * 80)
        print("🎉 INTEGRATED DATASET CONSTRUCTION COMPLETE!")
        print("=" * 80)
        print(f"✅ Successfully created dataset with {len(dataset_rows)} genomes")
        
        # Analyze system integration
        complete_systems = sum(1 for r in dataset_rows if r.get('State') == 'active')
        gut_relevant = sum(1 for r in dataset_rows if r.get('gut_relevance') == 'high')
        
        print(f"📊 Integration Analysis:")
        print(f"   Complete amyloid-copper-SOD systems: {complete_systems}")
        print(f"   Gut-relevant genomes: {gut_relevant}")
        print(f"   Average systems per genome: {sum(r.get('total_systems', 0) for r in dataset_rows) / len(dataset_rows):.1f}")
        
        # System distribution
        amyloid_genomes = sum(1 for r in dataset_rows if r.get('amyloid_systems', 0) > 0)
        copper_genomes = sum(1 for r in dataset_rows if r.get('copper_systems', 0) > 0)
        sod_genomes = sum(1 for r in dataset_rows if r.get('sod_systems', 0) > 0)
        
        print(f"📊 System Distribution:")
        print(f"   Genomes with amyloid systems: {amyloid_genomes}")
        print(f"   Genomes with copper systems: {copper_genomes}")
        print(f"   Genomes with SOD systems: {sod_genomes}")
        
        if len(dataset_rows) >= 100:
            print(f"✅ Dataset scale: EXCELLENT for neural network training")
        elif len(dataset_rows) >= 50:
            print(f"✅ Dataset scale: ADEQUATE for neural network training")
        else:
            print(f"⚠️  Dataset scale: May need expansion for robust training")
        
        print(f"\n🔄 Next steps:")
        print(f"   1. NCBI taxonomy verification")
        print(f"   2. Representative genome mapping")
        print(f"   3. Neural network training with integrated features")
        print(f"   4. Validation in SOCK mouse model")
        
    else:
        print("❌ Failed to create integrated dataset")


if __name__ == "__main__":
    main()