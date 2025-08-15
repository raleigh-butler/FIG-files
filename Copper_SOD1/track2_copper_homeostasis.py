#!/usr/bin/env python3
"""
Track 2: Copper Homeostasis Systems
Systematic search for bacterial copper transport, resistance, and regulatory systems
"""

from shared_utilities import bvbrc_utils
from typing import List, Dict

class CopperHomeostasisTrack:
    """Track 2: Copper homeostasis systems search and analysis"""
    
    def __init__(self):
        """Initialize Track 2 with comprehensive copper system search terms"""
        self.track_name = "Copper_Homeostasis"
        
        # Copper transport and efflux genes (32 total)
        self.gene_search_terms = [
            # Major Copper Efflux Systems
            'copA', 'copB', 'copC', 'copD', 'copE', 'copF',  # cop operon
            'cusA', 'cusB', 'cusC', 'cusF', 'cusR', 'cusS',  # cus system
            'cueO', 'cueR', 'cueP',                          # cue system
            'ctrA', 'ctrB', 'ctrC', 'ctrD',                  # ctr transporters
            
            # Copper Chaperones and Binding
            'copZ', 'copY', 'copG', 'copH',                  # cop chaperones/regulators
            'cutC', 'cutE', 'cutF',                          # copper tolerance
            'scoA', 'scoB',                                  # copper chaperones
            'ccs',                                           # copper chaperone for SOD
            
            # Copper Sensing and Regulation
            'merR', 'copS', 'copT',                          # regulatory systems
            'tcuA', 'tcuB', 'tcuC', 'tcuR'                   # tricarballylate Cu regulation
        ]
        
        # Functional keyword searches (18 total)
        self.functional_search_terms = [
            'copper transporter',
            'copper efflux',
            'copper resistance',
            'copper export',
            'copper oxidase',
            'copper chaperone',
            'copper binding',
            'copper homeostasis',
            'copper tolerance',
            'cuprous oxidase',
            'copper ATPase',
            'copper sensing',
            'copper regulator',
            'copper responsive',
            'heavy metal efflux',
            'metal tolerance',
            'P-type ATPase copper',
            'RND copper efflux'
        ]
        
        self.all_search_terms = self.gene_search_terms + self.functional_search_terms
        
        print(f"🟠 Track 2 initialized: {len(self.gene_search_terms)} gene terms + {len(self.functional_search_terms)} functional terms")
    
    def run_gene_searches(self, genome_ids: List[str]) -> List[Dict]:
        """Execute gene name searches across all representative genomes
        
        Args:
            genome_ids: List of genome IDs to search
            
        Returns:
            List of batch search results for gene searches
        """
        print(f"\n=== TRACK 2A: COPPER GENE SEARCHES ===")
        
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
        print(f"\n=== TRACK 2B: COPPER FUNCTIONAL SEARCHES ===")
        
        functional_results = bvbrc_utils.batch_search_across_genomes(
            search_terms=self.functional_search_terms,
            genome_ids=genome_ids,
            search_type='keyword',
            track_name=f"{self.track_name}_Functional"
        )
        
        return functional_results
    
    def run_complete_track(self, genome_ids: List[str]) -> Dict:
        """Execute complete Track 2 search (genes + functional)
        
        Args:
            genome_ids: List of genome IDs to search
            
        Returns:
            Combined results dictionary with track summary
        """
        print(f"\n{'='*60}")
        print(f"🟠 TRACK 2: COPPER HOMEOSTASIS SYSTEMS")
        print(f"{'='*60}")
        print(f"Searching {len(genome_ids)} representative genomes...")
        print(f"Gene terms: {len(self.gene_search_terms)}")
        print(f"Functional terms: {len(self.functional_search_terms)}")
        
        # Run both search types
        gene_results = self.run_gene_searches(genome_ids)
        functional_results = self.run_functional_searches(genome_ids)
        
        # Combine results
        all_results = gene_results + functional_results
        
        # Track statistics
        total_features = sum(len(r.get('features', [])) for r in all_results)
        successful_searches = sum(1 for r in all_results if r.get('success', False))
        total_searches = len(all_results)
        
        track_summary = {
            'track_name': self.track_name,
            'track_number': 2,
            'gene_searches': len(gene_results),
            'functional_searches': len(functional_results),
            'total_searches': total_searches,
            'successful_searches': successful_searches,
            'success_rate': (successful_searches / total_searches * 100) if total_searches > 0 else 0,
            'total_features_found': total_features,
            'search_terms_used': {
                'gene_terms': self.gene_search_terms,
                'functional_terms': self.functional_search_terms
            },
            'results': all_results
        }
        
        print(f"\n🟠 TRACK 2 SUMMARY:")
        print(f"   Total searches: {total_searches}")
        print(f"   Successful: {successful_searches} ({track_summary['success_rate']:.1f}%)")
        print(f"   Features found: {total_features}")
        print(f"   Genomes searched: {len(genome_ids)}")
        
        return track_summary
    
    def get_copper_system_classification(self, features: List[Dict]) -> Dict:
        """Classify copper systems found in features
        
        Args:
            features: List of feature dictionaries
            
        Returns:
            Classification summary of copper systems
        """
        systems = {
            'efflux_systems': [],      # copA, cusA, etc.
            'chaperones': [],          # copZ, ccs, etc.  
            'regulators': [],          # cueR, copY, etc.
            'transporters': [],        # ctrA, etc.
            'oxidases': [],            # cueO, etc.
            'resistance': []           # cutC, etc.
        }
        
        for feature in features:
            gene = feature.get('gene', '').lower()
            product = feature.get('product', '').lower()
            
            # Classify by gene name patterns
            if any(term in gene for term in ['copa', 'cusa', 'efflux']):
                systems['efflux_systems'].append(feature)
            elif any(term in gene for term in ['copz', 'ccs', 'scoa', 'scob']):
                systems['chaperones'].append(feature)  
            elif any(term in gene for term in ['cuer', 'copy', 'cusr', 'cops', 'merr']):
                systems['regulators'].append(feature)
            elif any(term in gene for term in ['ctra', 'ctrb', 'ctrch']):
                systems['transporters'].append(feature)
            elif any(term in gene for term in ['cueo', 'oxidase']):
                systems['oxidases'].append(feature)
            elif any(term in gene for term in ['cutc', 'cute', 'cutf', 'tolerance']):
                systems['resistance'].append(feature)
            
            # Classify by product description
            elif any(term in product for term in ['efflux', 'export']):
                systems['efflux_systems'].append(feature)
            elif any(term in product for term in ['chaperone', 'binding']):
                systems['chaperones'].append(feature)
            elif any(term in product for term in ['regulator', 'transcriptional']):
                systems['regulators'].append(feature)
            elif any(term in product for term in ['transporter', 'transport']):
                systems['transporters'].append(feature)
            elif any(term in product for term in ['oxidase', 'cuprous']):
                systems['oxidases'].append(feature)
            elif any(term in product for term in ['resistance', 'tolerance']):
                systems['resistance'].append(feature)
        
        return systems

def main():
    """Test Track 2 implementation"""
    print("🟠 Testing Track 2: Copper Homeostasis Systems")
    
    # Test with small genome set
    track2 = CopperHomeostasisTrack()
    
    # Load representative genomes (limit for testing)
    genomes = bvbrc_utils.load_representative_genomes(limit=10)
    genome_ids = list(genomes.keys())
    
    if genome_ids:
        print(f"Testing with {len(genome_ids)} genomes...")
        results = track2.run_complete_track(genome_ids)
        
        print(f"\n✅ Track 2 test complete!")
        print(f"Found {results['total_features_found']} copper system features")
    else:
        print("❌ No genomes loaded for testing")

if __name__ == "__main__":
    main()