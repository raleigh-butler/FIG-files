#!/usr/bin/env python3
"""
Shared Utilities for Three-Track BV-BRC Analysis
Common functions used across Track 1 (Amyloids), Track 2 (Copper), and Track 3 (SOD)
"""

import time
import json
import csv
from typing import Dict, List, Optional
from robust_api_handler import RobustBVBRCHandler

# Initialize global API handler
api_handler = RobustBVBRCHandler()

class BVBRCUtils:
    """Utility functions for BV-BRC API interactions across all tracks"""
    
    @staticmethod
    def load_representative_genomes(limit: Optional[int] = None) -> Dict[str, Dict]:
        """Load representative genomes using the robust API handler
        
        Args:
            limit: Optional limit on number of genomes to load
            
        Returns:
            Dictionary of genome_id -> genome_info
        """
        return api_handler.load_representative_genomes(limit=limit)
    
    @staticmethod  
    def search_gene_in_genome_batch(search_term: str, genome_ids: List[str], 
                                   search_type: str = 'gene') -> List[Dict]:
        """Search for a term across a batch of genomes
        
        Args:
            search_term: Gene name or functional term to search
            genome_ids: List of genome IDs to search in
            search_type: 'gene', 'product', or 'keyword'
            
        Returns:
            List of search results for each genome
        """
        results = []
        
        for genome_id in genome_ids:
            result = api_handler.search_gene_in_genome(search_term, genome_id, search_type)
            results.append(result)
            
            # Add delay between requests to be respectful
            time.sleep(0.2)
        
        return results
    
    @staticmethod
    def batch_search_across_genomes(search_terms: List[str], genome_ids: List[str],
                                   search_type: str = 'gene', track_name: str = "Unknown") -> List[Dict]:
        """Execute batch searches for multiple terms across all genomes
        
        Args:
            search_terms: List of terms to search for
            genome_ids: List of genome IDs to search in  
            search_type: 'gene', 'product', or 'keyword'
            track_name: Name of track for logging
            
        Returns:
            List of consolidated search results
        """
        print(f"🔍 {track_name}: Searching {len(search_terms)} terms across {len(genome_ids)} genomes...")
        
        all_results = []
        successful_terms = 0
        total_features = 0
        
        for i, search_term in enumerate(search_terms, 1):
            print(f"   [{i}/{len(search_terms)}] Searching: {search_term}")
            
            # Search this term across all genomes
            term_results = []
            term_features = 0
            genome_coverage = {}  # Track per-genome feature counts for matrix creation
            
            # Process genomes in smaller batches to avoid overwhelming API
            batch_size = 20
            for j in range(0, len(genome_ids), batch_size):
                batch_genome_ids = genome_ids[j:j+batch_size]
                
                batch_results = BVBRCUtils.search_gene_in_genome_batch(
                    search_term, batch_genome_ids, search_type
                )
                
                for result in batch_results:
                    genome_id = result.get('genome_id')
                    feature_count = result.get('count', 0)
                    
                    # Track per-genome coverage for matrix creation
                    genome_coverage[genome_id] = feature_count
                    
                    if result['success'] and feature_count > 0:
                        term_features += feature_count
                        # Add the detailed features to term_results (correct key is 'results')
                        if 'results' in result and result['results']:
                            term_results.extend(result['results'])
                
                # Delay between batches
                time.sleep(0.5)
            
            # Consolidate results for this term
            term_summary = {
                'search_term': search_term,
                'search_type': search_type,
                'track_name': track_name,
                'genomes_searched': len(genome_ids),
                'features_found': term_features,
                'success': term_features > 0,
                'features': term_results,  # Now contains detailed feature data
                'genome_coverage': genome_coverage  # Per-genome feature counts for matrix
            }
            
            all_results.append(term_summary)
            
            if term_features > 0:
                successful_terms += 1
                total_features += term_features
                print(f"      ✅ Found {term_features} features")
            else:
                print(f"      ❌ No features found")
        
        print(f"🎯 {track_name} Batch Summary:")
        print(f"   Terms searched: {len(search_terms)}")
        print(f"   Successful terms: {successful_terms} ({(successful_terms/len(search_terms)*100):.1f}%)")
        print(f"   Total features: {total_features}")
        print(f"   Genomes searched: {len(genome_ids)}")
        
        return all_results
    
    @staticmethod
    def save_track_results(track_results: Dict, output_dir: str = ".") -> List[str]:
        """Save track results to files
        
        Args:
            track_results: Track results dictionary
            output_dir: Directory to save files in
            
        Returns:
            List of saved file paths
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        track_name = track_results.get('track_name', 'unknown_track').lower()
        
        saved_files = []
        
        # 1. Save complete results JSON
        results_file = f"{output_dir}/{track_name}_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(track_results, f, indent=2, default=str)
        saved_files.append(results_file)
        print(f"✅ Saved complete results: {results_file}")
        
        # 2. Save features CSV
        features_file = f"{output_dir}/{track_name}_features_{timestamp}.csv"
        all_features = []
        
        for result in track_results.get('results', []):
            for feature in result.get('features', []):
                feature['search_term'] = result.get('search_term', '')
                feature['search_type'] = result.get('search_type', '')
                all_features.append(feature)
        
        if all_features:
            fieldnames = list(all_features[0].keys())
            with open(features_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_features)
            saved_files.append(features_file)
            print(f"✅ Saved features CSV: {features_file}")
        
        # 3. Save summary stats
        summary_file = f"{output_dir}/{track_name}_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(f"=== {track_results.get('track_name', 'Unknown')} Track Summary ===\n")
            f.write(f"Generated: {timestamp}\n\n")
            f.write(f"Search Statistics:\n")
            f.write(f"  Total searches: {track_results.get('total_searches', 0)}\n")
            f.write(f"  Successful searches: {track_results.get('successful_searches', 0)}\n") 
            f.write(f"  Success rate: {track_results.get('success_rate', 0):.1f}%\n")
            f.write(f"  Features found: {track_results.get('total_features_found', 0)}\n")
            f.write(f"  Genomes searched: {len(track_results.get('genome_ids', []))}\n\n")
            
            f.write(f"Search Terms Used:\n")
            f.write(f"  Gene terms: {len(track_results.get('search_terms_used', {}).get('gene_terms', []))}\n")
            f.write(f"  Functional terms: {len(track_results.get('search_terms_used', {}).get('functional_terms', []))}\n")
            
        saved_files.append(summary_file)
        print(f"✅ Saved summary: {summary_file}")
        
        return saved_files
    
    @staticmethod
    def create_genome_role_matrix(track_results_list: List[Dict], genome_ids: List[str]) -> Dict:
        """Create binary genome-role matrix from multiple track results
        
        Args:
            track_results_list: List of track result dictionaries
            genome_ids: List of all genome IDs analyzed
            
        Returns:
            Dictionary with genome-role binary matrix
        """
        print(f"🧬 Creating genome-role matrix from {len(track_results_list)} tracks...")
        
        # Collect all roles from all tracks
        all_roles = set()
        for track_results in track_results_list:
            for result in track_results.get('results', []):
                all_roles.add(result.get('search_term', ''))
        
        all_roles = sorted(list(all_roles))
        print(f"   Total roles identified: {len(all_roles)}")
        
        # Build binary matrix
        genome_role_matrix = {}
        
        for genome_id in genome_ids:
            genome_role_matrix[genome_id] = {role: 0 for role in all_roles}
        
        # Populate matrix from track results
        total_features = 0
        for track_results in track_results_list:
            track_name = track_results.get('track_name', 'Unknown')
            
            for result in track_results.get('results', []):
                role = result.get('search_term', '')
                
                for feature in result.get('features', []):
                    genome_id = str(feature.get('genome_id', ''))
                    
                    if genome_id in genome_role_matrix:
                        genome_role_matrix[genome_id][role] = 1
                        total_features += 1
        
        print(f"   Matrix populated with {total_features} features")
        print(f"   Matrix dimensions: {len(genome_ids)} genomes × {len(all_roles)} roles")
        
        return {
            'matrix': genome_role_matrix,
            'genomes': genome_ids,
            'roles': all_roles,
            'total_features': total_features,
            'tracks_included': [tr.get('track_name', 'Unknown') for tr in track_results_list]
        }
    
    @staticmethod
    def get_api_stats() -> Dict:
        """Get current API usage statistics"""
        return api_handler.stats.copy()

# Create singleton instance
bvbrc_utils = BVBRCUtils()