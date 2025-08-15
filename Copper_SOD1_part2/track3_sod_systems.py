#!/usr/bin/env python3
"""
Track 3: SOD (Superoxide Dismutase) Systems
Systematic search for bacterial antioxidant defense systems, particularly SOD and catalase
"""

from shared_utilities import bvbrc_utils
from typing import List, Dict

class SODSystemsTrack:
    """Track 3: SOD and antioxidant systems search and analysis"""
    
    def __init__(self):
        """Initialize Track 3 with comprehensive SOD and antioxidant search terms"""
        self.track_name = "SOD_Systems"
        
        # SOD and antioxidant enzyme genes (28 total)
        self.gene_search_terms = [
            # Superoxide Dismutases
            'sodA', 'sodB', 'sodC', 'sodM', 'sodF',          # Main SOD enzymes
            'sod1', 'sod2', 'sod3',                          # Alternative naming
            
            # Catalases
            'katA', 'katB', 'katC', 'katE', 'katG', 'katN',  # Catalase variants
            'hpxO', 'hpxQ',                                  # Manganese catalases
            
            # Peroxidases and Related
            'ahpC', 'ahpF',                                  # Alkyl hydroperoxide reductase
            'tpx', 'bcp',                                    # Thiol peroxidases
            'ohr', 'osmC',                                   # Organic hydroperoxide resistance
            'dps',                                           # DNA protection during starvation
            
            # Glutathione System
            'gor', 'grx', 'gshA', 'gshB',                    # Glutathione metabolism
            'trxA', 'trxB', 'trxC'                           # Thioredoxin system
        ]
        
        # Functional keyword searches (20 total)
        self.functional_search_terms = [
            'superoxide dismutase',
            'catalase',
            'peroxidase',
            'antioxidant',
            'oxidative stress',
            'superoxide radical',
            'hydrogen peroxide',
            'reactive oxygen',
            'ROS detoxification',
            'alkyl hydroperoxide reductase',
            'thiol peroxidase',
            'manganese superoxide dismutase',
            'iron superoxide dismutase',  
            'copper zinc superoxide dismutase',
            'catalase peroxidase',
            'glutathione peroxidase',
            'thioredoxin',
            'glutaredoxin',
            'DNA protection protein',
            'oxidative damage'
        ]
        
        self.all_search_terms = self.gene_search_terms + self.functional_search_terms
        
        print(f"🔵 Track 3 initialized: {len(self.gene_search_terms)} gene terms + {len(self.functional_search_terms)} functional terms")
    
    def run_gene_searches(self, genome_ids: List[str]) -> List[Dict]:
        """Execute gene name searches across all representative genomes
        
        Args:
            genome_ids: List of genome IDs to search
            
        Returns:
            List of batch search results for gene searches
        """
        print(f"\n=== TRACK 3A: SOD GENE SEARCHES ===")
        
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
        print(f"\n=== TRACK 3B: SOD FUNCTIONAL SEARCHES ===")
        
        functional_results = bvbrc_utils.batch_search_across_genomes(
            search_terms=self.functional_search_terms,
            genome_ids=genome_ids,
            search_type='keyword',
            track_name=f"{self.track_name}_Functional"
        )
        
        return functional_results
    
    def run_complete_track(self, genome_ids: List[str]) -> Dict:
        """Execute complete Track 3 search (genes + functional)
        
        Args:
            genome_ids: List of genome IDs to search
            
        Returns:
            Combined results dictionary with track summary
        """
        print(f"\n{'='*60}")
        print(f"🔵 TRACK 3: SOD & ANTIOXIDANT SYSTEMS")
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
            'track_number': 3,
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
        
        print(f"\n🔵 TRACK 3 SUMMARY:")
        print(f"   Total searches: {total_searches}")
        print(f"   Successful: {successful_searches} ({track_summary['success_rate']:.1f}%)")
        print(f"   Features found: {total_features}")
        print(f"   Genomes searched: {len(genome_ids)}")
        
        return track_summary
    
    def get_sod_system_classification(self, features: List[Dict]) -> Dict:
        """Classify SOD/antioxidant systems found in features
        
        Args:
            features: List of feature dictionaries
            
        Returns:
            Classification summary of antioxidant systems
        """
        systems = {
            'superoxide_dismutases': [],    # sodA, sodB, sodC
            'catalases': [],               # katA, katB, katE, etc.
            'peroxidases': [],            # ahpC, tpx, bcp, etc.
            'glutathione_system': [],     # gor, grx, gshA, gshB
            'thioredoxin_system': [],     # trxA, trxB, trxC
            'dna_protection': [],         # dps, osmC
            'other_antioxidants': []      # ohr, etc.
        }
        
        for feature in features:
            gene = feature.get('gene', '').lower()
            product = feature.get('product', '').lower()
            
            # Classify by gene name patterns
            if any(term in gene for term in ['soda', 'sodb', 'sodc', 'sodm', 'sodf', 'sod1', 'sod2', 'sod3']):
                systems['superoxide_dismutases'].append(feature)
                # Add metal cofactor info if available
                if 'manganese' in product or 'mn' in product or 'soda' in gene:
                    feature['metal_cofactor'] = 'Manganese'
                elif 'iron' in product or 'fe' in product or 'sodb' in gene:
                    feature['metal_cofactor'] = 'Iron'
                elif 'copper' in product or 'zinc' in product or 'cu' in product or 'zn' in product or 'sodc' in gene:
                    feature['metal_cofactor'] = 'Copper-Zinc'
                else:
                    feature['metal_cofactor'] = 'Unknown'
                    
            elif any(term in gene for term in ['kata', 'katb', 'katc', 'kate', 'katg', 'katn', 'hpxo', 'hpxq']):
                systems['catalases'].append(feature)
                
            elif any(term in gene for term in ['ahpc', 'ahpf', 'tpx', 'bcp', 'ohr']):
                systems['peroxidases'].append(feature)
                
            elif any(term in gene for term in ['gor', 'grx', 'gsha', 'gshb']):
                systems['glutathione_system'].append(feature)
                
            elif any(term in gene for term in ['trxa', 'trxb', 'trxc']):
                systems['thioredoxin_system'].append(feature)
                
            elif any(term in gene for term in ['dps', 'osmc']):
                systems['dna_protection'].append(feature)
                
            # Classify by product description  
            elif 'superoxide dismutase' in product:
                systems['superoxide_dismutases'].append(feature)
                # Infer metal cofactor from product description
                if 'manganese' in product or 'mn' in product:
                    feature['metal_cofactor'] = 'Manganese'
                elif 'iron' in product or 'fe' in product:
                    feature['metal_cofactor'] = 'Iron'  
                elif 'copper' in product or 'zinc' in product:
                    feature['metal_cofactor'] = 'Copper-Zinc'
                else:
                    feature['metal_cofactor'] = 'Inferred from gene'
                    
            elif 'catalase' in product:
                systems['catalases'].append(feature)
                
            elif any(term in product for term in ['peroxidase', 'hydroperoxide']):
                systems['peroxidases'].append(feature)
                
            elif any(term in product for term in ['glutathione', 'glutaredoxin']):
                systems['glutathione_system'].append(feature)
                
            elif 'thioredoxin' in product:
                systems['thioredoxin_system'].append(feature)
                
            elif any(term in product for term in ['dna protection', 'starvation']):
                systems['dna_protection'].append(feature)
                
            else:
                systems['other_antioxidants'].append(feature)
        
        return systems
    
    def analyze_metal_cofactor_distribution(self, sod_features: List[Dict]) -> Dict:
        """Analyze distribution of SOD metal cofactors
        
        Args:
            sod_features: List of SOD feature dictionaries
            
        Returns:
            Metal cofactor distribution summary
        """
        cofactor_counts = {
            'Manganese': 0,
            'Iron': 0, 
            'Copper-Zinc': 0,
            'Unknown': 0
        }
        
        for feature in sod_features:
            cofactor = feature.get('metal_cofactor', 'Unknown')
            cofactor_counts[cofactor] += 1
        
        return {
            'total_sods': len(sod_features),
            'cofactor_distribution': cofactor_counts,
            'copper_dependent_sods': cofactor_counts['Copper-Zinc'],
            'copper_independent_sods': cofactor_counts['Manganese'] + cofactor_counts['Iron']
        }

def main():
    """Test Track 3 implementation"""
    print("🔵 Testing Track 3: SOD & Antioxidant Systems")
    
    # Test with small genome set
    track3 = SODSystemsTrack()
    
    # Load representative genomes (limit for testing)
    genomes = bvbrc_utils.load_representative_genomes(limit=10)
    genome_ids = list(genomes.keys())
    
    if genome_ids:
        print(f"Testing with {len(genome_ids)} genomes...")
        results = track3.run_complete_track(genome_ids)
        
        print(f"\n✅ Track 3 test complete!")
        print(f"Found {results['total_features_found']} SOD/antioxidant features")
    else:
        print("❌ No genomes loaded for testing")

if __name__ == "__main__":
    main()