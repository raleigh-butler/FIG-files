#!/usr/bin/env python3
"""
Track 1: Bacterial Amyloids Search
Systematic search for bacterial amyloid systems using expanded gene names and functional terms
"""

from shared_utilities import bvbrc_utils
from typing import List, Dict

class BacterialAmyloidsTrack:
    """Track 1: Bacterial amyloid systems search and analysis"""
    
    def __init__(self):
        """Initialize Track 1 with expanded amyloid search terms"""
        self.track_name = "Bacterial_Amyloids"
        
        # Limited gene name searches (10 total for testing)
        self.gene_search_terms = [
            # Primary Curli System (E. coli)
            'csgA', 'csgB', 'csgC', 'csgD', 'csgE',
            
            # Salmonella Curli Equivalents
            'agfA', 'agfB',
            
            # Bacillus Biofilm Matrix
            'tasA', 'tapA',
            
            # Pseudomonas Functional Amyloids
            'fapA'
        ]
        
        # No functional searches for this test
        self.functional_search_terms = []
        
        self.all_search_terms = self.gene_search_terms + self.functional_search_terms
        
        print(f"🧬 Track 1 initialized: {len(self.gene_search_terms)} gene terms + {len(self.functional_search_terms)} functional terms")
    
    def run_gene_searches(self, genome_ids: List[str]) -> List[Dict]:
        """Execute gene name searches across all representative genomes
        
        Args:
            genome_ids: List of genome IDs to search
            
        Returns:
            List of batch search results for gene searches
        """
        print(f"\n=== TRACK 1A: GENE NAME SEARCHES ===")
        
        gene_results = bvbrc_utils.batch_search_across_genomes(
            search_terms=self.gene_search_terms,
            genome_ids=genome_ids,
            search_type='gene',
            track_name=f"{self.track_name}_Genes"
        )
        
        return gene_results
    
    def run_functional_searches(self, genome_ids: List[str]) -> List[Dict]:
        """Execute functional keyword searches across all representative genomes
        
        Args:
            genome_ids: List of genome IDs to search
            
        Returns:
            List of batch search results for functional searches
        """
        print(f"\n=== TRACK 1B: FUNCTIONAL KEYWORD SEARCHES ===")
        
        functional_results = bvbrc_utils.batch_search_across_genomes(
            search_terms=self.functional_search_terms,
            genome_ids=genome_ids,
            search_type='keyword',
            track_name=f"{self.track_name}_Functional"
        )
        
        return functional_results
    
    def analyze_amyloid_results(self, gene_results: List[Dict], functional_results: List[Dict]) -> Dict:
        """Analyze combined amyloid search results for biological insights
        
        Args:
            gene_results: Results from gene name searches
            functional_results: Results from functional searches
            
        Returns:
            Dictionary with analysis results
        """
        print(f"\n=== TRACK 1 BIOLOGICAL ANALYSIS ===")
        
        # Extract individual features
        gene_features = bvbrc_utils.extract_individual_features(gene_results)
        functional_features = bvbrc_utils.extract_individual_features(functional_results)
        
        analysis = {
            'gene_features_count': len(gene_features),
            'functional_features_count': len(functional_features),
            'total_features': len(gene_features) + len(functional_features)
        }
        
        # Analyze curli system completeness
        curli_genes = ['csgA', 'csgB', 'csgC', 'csgD', 'csgE', 'csgF', 'csgG']
        curli_hits = {}
        
        for feature in gene_features:
            gene = feature['gene'].lower()
            if gene in curli_genes:
                if gene not in curli_hits:
                    curli_hits[gene] = []
                curli_hits[gene].append(feature['genome_id'])
        
        analysis['curli_system_analysis'] = {
            'genes_found': list(curli_hits.keys()),
            'complete_operons': self._find_complete_curli_operons(curli_hits)
        }
        
        # Analyze secretion potential
        secretion_indicators = ['signal', 'secreted', 'extracellular', 'exported']
        secreted_amyloids = []
        
        for feature in gene_features + functional_features:
            product = feature['product'].lower()
            if any(indicator in product for indicator in secretion_indicators):
                secreted_amyloids.append(feature)
        
        analysis['secretion_analysis'] = {
            'secreted_amyloid_count': len(secreted_amyloids),
            'secretion_percentage': len(secreted_amyloids) / analysis['total_features'] * 100 if analysis['total_features'] > 0 else 0
        }
        
        # Genome distribution analysis
        gene_genomes = set(f['genome_id'] for f in gene_features)
        functional_genomes = set(f['genome_id'] for f in functional_features)
        all_genomes = gene_genomes.union(functional_genomes)
        
        analysis['genome_distribution'] = {
            'genomes_with_gene_hits': len(gene_genomes),
            'genomes_with_functional_hits': len(functional_genomes),
            'total_genomes_with_amyloids': len(all_genomes),
            'overlap_genomes': len(gene_genomes.intersection(functional_genomes))
        }
        
        print(f"📊 Amyloid Analysis Complete:")
        print(f"  Total features: {analysis['total_features']}")
        print(f"  Genomes with amyloids: {analysis['genome_distribution']['total_genomes_with_amyloids']}")
        print(f"  Secreted amyloids: {analysis['secretion_analysis']['secreted_amyloid_count']}")
        print(f"  Curli genes found: {len(analysis['curli_system_analysis']['genes_found'])}")
        
        return analysis
    
    def _find_complete_curli_operons(self, curli_hits: Dict[str, List[str]]) -> List[str]:
        """Find genomes with complete or near-complete curli operons
        
        Args:
            curli_hits: Dictionary mapping curli genes to genome lists
            
        Returns:
            List of genome IDs with complete operons
        """
        # Require at least csgA (major subunit) + 2 other curli genes for "complete"
        complete_operons = []
        
        if 'csga' not in curli_hits:
            return complete_operons
        
        csga_genomes = set(curli_hits['csga'])
        
        for genome_id in csga_genomes:
            curli_gene_count = sum(1 for gene_genomes in curli_hits.values() if genome_id in gene_genomes)
            
            if curli_gene_count >= 3:  # csgA + at least 2 others
                complete_operons.append(genome_id)
        
        return complete_operons
    
    def run_complete_track(self, genome_ids: List[str] = None, genome_limit: int = 500) -> Dict:
        """Execute complete Track 1 search and analysis
        
        Args:
            genome_ids: Optional list of genome IDs (will load if not provided)
            genome_limit: Limit on number of genomes to process
            
        Returns:
            Dictionary with all Track 1 results and analysis
        """
        print(f"🧬 STARTING TRACK 1: BACTERIAL AMYLOIDS")
        print("=" * 60)
        
        # Load genomes if not provided
        if genome_ids is None:
            genome_metadata = bvbrc_utils.load_representative_genomes(limit=genome_limit)
            genome_ids = list(genome_metadata.keys())
        
        if not genome_ids:
            print("❌ No genomes available for search!")
            return {}
        
        print(f"🎯 Processing {len(genome_ids)} genomes with {len(self.all_search_terms)} search terms")
        
        # Execute searches
        gene_results = self.run_gene_searches(genome_ids)
        functional_results = self.run_functional_searches(genome_ids)
        
        # Combine and save results
        all_results = gene_results + functional_results
        
        # Save track results
        batch_file, features_file = bvbrc_utils.save_track_results(
            batch_results=all_results,
            track_name=self.track_name,
            search_terms=self.all_search_terms
        )
        
        # Create visualizations
        bvbrc_utils.create_track_visualization(all_results, self.track_name)
        
        # Perform biological analysis
        analysis = self.analyze_amyloid_results(gene_results, functional_results)
        
        # Compile final results
        track_results = {
            'track_name': self.track_name,
            'gene_search_terms': self.gene_search_terms,
            'functional_search_terms': self.functional_search_terms,
            'total_search_terms': len(self.all_search_terms),
            'genomes_processed': len(genome_ids),
            'gene_results': gene_results,
            'functional_results': functional_results,
            'biological_analysis': analysis,
            'output_files': {
                'batch_results': batch_file,
                'features_csv': features_file
            }
        }
        
        print(f"\n✅ TRACK 1 COMPLETE: {analysis['total_features']} amyloid features found")
        
        return track_results

def main():
    """Main execution function for Track 1"""
    import sys
    
    # Initialize Track 1
    track1 = BacterialAmyloidsTrack()
    
    # Handle command line arguments
    genome_limit = 50  # Test with 50 genomes
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "full":
            genome_limit = None  # No limit
        elif sys.argv[1].isdigit():
            genome_limit = int(sys.argv[1])
    
    print(f"Running Track 1 with {'all' if genome_limit is None else genome_limit} genomes")
    
    # Execute Track 1
    results = track1.run_complete_track(genome_limit=genome_limit)
    
    if results:
        print("\n🎯 Track 1 Results Summary:")
        analysis = results['biological_analysis']
        print(f"  Gene features: {analysis['gene_features_count']}")
        print(f"  Functional features: {analysis['functional_features_count']}")
        print(f"  Total amyloid features: {analysis['total_features']}")
        print(f"  Genomes with hits: {analysis['genome_distribution']['total_genomes_with_amyloids']}")

if __name__ == "__main__":
    main()