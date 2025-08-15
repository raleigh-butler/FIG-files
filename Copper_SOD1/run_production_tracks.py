#!/usr/bin/env python3
"""
Production Runner for Three-Track BV-BRC Analysis
Executes Track 1 (Amyloids), Track 2 (Copper), Track 3 (SOD) with full representative genome set
"""

import time
import json
import os
from datetime import datetime
from track1_bacterial_amyloids import BacterialAmyloidsTrack
from track2_copper_homeostasis import CopperHomeostasisTrack
from track3_sod_systems import SODSystemsTrack
from shared_utilities import bvbrc_utils

class ProductionTrackRunner:
    """Production runner for executing all three tracks with full datasets"""
    
    def __init__(self, genome_limit: int = None):
        """Initialize production runner
        
        Args:
            genome_limit: Optional limit on number of genomes (None = all genomes)
        """
        self.genome_limit = genome_limit
        self.start_time = time.time()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory
        self.output_dir = f"production_results_{self.timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"🚀 PRODUCTION TRACK RUNNER INITIALIZED")
        print(f"Timestamp: {self.timestamp}")
        print(f"Output directory: {self.output_dir}")
        print(f"Genome limit: {genome_limit if genome_limit else 'All available genomes'}")
    
    def load_genomes(self):
        """Load representative genomes for analysis"""
        print(f"\n📖 Loading representative genomes...")
        
        genomes = bvbrc_utils.load_representative_genomes(limit=self.genome_limit)
        genome_ids = list(genomes.keys())
        
        if not genome_ids:
            raise ValueError("No genomes loaded - cannot proceed")
        
        print(f"✅ Loaded {len(genome_ids)} representative genomes")
        
        # Save genome list for reference
        genome_list_file = f"{self.output_dir}/genome_list_{self.timestamp}.json"
        with open(genome_list_file, 'w') as f:
            json.dump(genomes, f, indent=2, default=str)
        
        print(f"📄 Genome list saved: {genome_list_file}")
        
        return genomes, genome_ids
    
    def run_track1(self, genome_ids):
        """Execute Track 1: Bacterial Amyloids"""
        print(f"\n{'='*80}")
        print(f"🧬 EXECUTING TRACK 1: BACTERIAL AMYLOIDS")
        print(f"{'='*80}")
        
        try:
            track1 = BacterialAmyloidsTrack()
            start_time = time.time()
            
            results = track1.run_complete_track(genome_ids)
            execution_time = time.time() - start_time
            
            # Save results
            files_saved = bvbrc_utils.save_track_results(results, self.output_dir)
            
            track1_summary = {
                'track_name': 'Track1_Bacterial_Amyloids',
                'execution_time': execution_time,
                'status': 'success',
                'results': results,
                'files_saved': files_saved
            }
            
            print(f"✅ Track 1 completed successfully in {execution_time:.1f} seconds")
            print(f"📁 Files saved: {len(files_saved)}")
            
            return track1_summary
            
        except Exception as e:
            print(f"❌ Track 1 failed: {e}")
            return {
                'track_name': 'Track1_Bacterial_Amyloids',
                'status': 'failed',
                'error': str(e)
            }
    
    def run_track2(self, genome_ids):
        """Execute Track 2: Copper Homeostasis"""
        print(f"\n{'='*80}")
        print(f"🟠 EXECUTING TRACK 2: COPPER HOMEOSTASIS")
        print(f"{'='*80}")
        
        try:
            track2 = CopperHomeostasisTrack()
            start_time = time.time()
            
            results = track2.run_complete_track(genome_ids)
            execution_time = time.time() - start_time
            
            # Save results
            files_saved = bvbrc_utils.save_track_results(results, self.output_dir)
            
            track2_summary = {
                'track_name': 'Track2_Copper_Homeostasis', 
                'execution_time': execution_time,
                'status': 'success',
                'results': results,
                'files_saved': files_saved
            }
            
            print(f"✅ Track 2 completed successfully in {execution_time:.1f} seconds")
            print(f"📁 Files saved: {len(files_saved)}")
            
            return track2_summary
            
        except Exception as e:
            print(f"❌ Track 2 failed: {e}")
            return {
                'track_name': 'Track2_Copper_Homeostasis',
                'status': 'failed', 
                'error': str(e)
            }
    
    def run_track3(self, genome_ids):
        """Execute Track 3: SOD Systems"""
        print(f"\n{'='*80}")
        print(f"🔵 EXECUTING TRACK 3: SOD SYSTEMS")
        print(f"{'='*80}")
        
        try:
            track3 = SODSystemsTrack()
            start_time = time.time()
            
            results = track3.run_complete_track(genome_ids)
            execution_time = time.time() - start_time
            
            # Save results
            files_saved = bvbrc_utils.save_track_results(results, self.output_dir)
            
            track3_summary = {
                'track_name': 'Track3_SOD_Systems',
                'execution_time': execution_time,
                'status': 'success',
                'results': results,
                'files_saved': files_saved
            }
            
            print(f"✅ Track 3 completed successfully in {execution_time:.1f} seconds")
            print(f"📁 Files saved: {len(files_saved)}")
            
            return track3_summary
            
        except Exception as e:
            print(f"❌ Track 3 failed: {e}")
            return {
                'track_name': 'Track3_SOD_Systems',
                'status': 'failed',
                'error': str(e)
            }
    
    def create_integrated_matrix(self, track_summaries, genome_ids):
        """Create integrated genome-role matrix from all successful tracks"""
        print(f"\n{'='*80}")
        print(f"🧬 CREATING INTEGRATED GENOME-ROLE MATRIX")
        print(f"{'='*80}")
        
        # Collect successful track results
        successful_results = []
        for summary in track_summaries:
            if summary.get('status') == 'success':
                successful_results.append(summary['results'])
        
        if not successful_results:
            print("❌ No successful tracks to integrate")
            return None
        
        try:
            matrix_data = bvbrc_utils.create_genome_role_matrix(successful_results, genome_ids)
            
            # Save integrated matrix
            matrix_file = f"{self.output_dir}/integrated_genome_role_matrix_{self.timestamp}.json"
            with open(matrix_file, 'w') as f:
                json.dump(matrix_data, f, indent=2, default=str)
            
            # Save as CSV for easy analysis
            import csv
            csv_file = f"{self.output_dir}/integrated_genome_role_matrix_{self.timestamp}.csv"
            
            with open(csv_file, 'w', newline='') as f:
                roles = matrix_data['roles']
                writer = csv.writer(f)
                
                # Write header
                header = ['genome_id'] + roles
                writer.writerow(header)
                
                # Write data rows
                for genome_id in matrix_data['genomes']:
                    row = [genome_id]
                    for role in roles:
                        row.append(matrix_data['matrix'][genome_id][role])
                    writer.writerow(row)
            
            print(f"✅ Integrated matrix created successfully")
            print(f"📊 Matrix dimensions: {len(matrix_data['genomes'])} genomes × {len(matrix_data['roles'])} roles")
            print(f"📊 Total features: {matrix_data['total_features']}")
            print(f"📁 Matrix saved: {matrix_file}")
            print(f"📁 CSV saved: {csv_file}")
            
            return matrix_data
            
        except Exception as e:
            print(f"❌ Matrix creation failed: {e}")
            return None
    
    def generate_final_report(self, track_summaries, matrix_data, genome_ids):
        """Generate comprehensive final report"""
        print(f"\n{'='*80}")
        print(f"📋 GENERATING FINAL REPORT")
        print(f"{'='*80}")
        
        total_time = time.time() - self.start_time
        
        # Calculate statistics
        successful_tracks = sum(1 for t in track_summaries if t.get('status') == 'success')
        total_features = sum(t['results'].get('total_features_found', 0) 
                           for t in track_summaries if t.get('status') == 'success')
        
        api_stats = bvbrc_utils.get_api_stats()
        
        report = {
            'production_run_info': {
                'timestamp': self.timestamp,
                'total_execution_time': total_time,
                'genomes_analyzed': len(genome_ids),
                'genome_limit_used': self.genome_limit,
                'output_directory': self.output_dir
            },
            'track_results': {
                'total_tracks': len(track_summaries),
                'successful_tracks': successful_tracks,
                'track_success_rate': (successful_tracks / len(track_summaries)) * 100,
                'total_features_found': total_features,
                'track_summaries': track_summaries
            },
            'integrated_analysis': {
                'matrix_created': matrix_data is not None,
                'matrix_dimensions': f"{len(matrix_data['genomes'])} × {len(matrix_data['roles'])}" if matrix_data else "N/A",
                'integrated_features': matrix_data['total_features'] if matrix_data else 0,
                'tracks_integrated': matrix_data['tracks_included'] if matrix_data else []
            },
            'api_usage': api_stats,
            'recommendations': self.generate_recommendations(track_summaries, matrix_data)
        }
        
        # Save report
        report_file = f"{self.output_dir}/production_run_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Final report saved: {report_file}")
        
        return report
    
    def generate_recommendations(self, track_summaries, matrix_data):
        """Generate recommendations based on results"""
        recommendations = []
        
        successful_tracks = sum(1 for t in track_summaries if t.get('status') == 'success')
        
        if successful_tracks == 3:
            recommendations.append("✅ All tracks completed successfully - Dataset ready for neural network training")
            
        if matrix_data and matrix_data['total_features'] > 100:
            recommendations.append("✅ Rich feature set obtained - Good foundation for machine learning")
            
        if matrix_data and len(matrix_data['genomes']) > 50:
            recommendations.append("✅ Sufficient genome coverage - Dataset suitable for robust analysis")
            
        # Add specific recommendations based on track performance
        for summary in track_summaries:
            if summary.get('status') == 'success':
                features = summary['results'].get('total_features_found', 0)
                track_name = summary['track_name']
                
                if features > 50:
                    recommendations.append(f"✅ {track_name}: High feature count ({features}) - Excellent coverage")
                elif features > 20:
                    recommendations.append(f"⚠️  {track_name}: Moderate feature count ({features}) - Consider expanding search terms")
                else:
                    recommendations.append(f"⚠️  {track_name}: Low feature count ({features}) - Review search strategy")
        
        return recommendations
    
    def run_complete_production(self):
        """Execute complete production run of all three tracks"""
        print(f"🚀 STARTING COMPLETE PRODUCTION RUN")
        print(f"="*80)
        
        try:
            # Load genomes
            genomes, genome_ids = self.load_genomes()
            
            # Execute all tracks with delays between them
            track_summaries = []
            
            # Track 1: Bacterial Amyloids
            track1_summary = self.run_track1(genome_ids)
            track_summaries.append(track1_summary)
            time.sleep(5)  # Delay between tracks
            
            # Track 2: Copper Homeostasis  
            track2_summary = self.run_track2(genome_ids)
            track_summaries.append(track2_summary)
            time.sleep(5)  # Delay between tracks
            
            # Track 3: SOD Systems
            track3_summary = self.run_track3(genome_ids)
            track_summaries.append(track3_summary)
            
            # Create integrated matrix
            matrix_data = self.create_integrated_matrix(track_summaries, genome_ids)
            
            # Generate final report
            final_report = self.generate_final_report(track_summaries, matrix_data, genome_ids)
            
            # Print summary
            self.print_final_summary(final_report)
            
            return final_report
            
        except Exception as e:
            print(f"❌ Production run failed: {e}")
            raise
    
    def print_final_summary(self, report):
        """Print final summary of production run"""
        print(f"\n{'='*80}")
        print(f"🎉 PRODUCTION RUN COMPLETE!")
        print(f"{'='*80}")
        
        info = report['production_run_info']
        results = report['track_results']
        integration = report['integrated_analysis']
        
        print(f"⏱️  Total execution time: {info['total_execution_time']:.1f} seconds")
        print(f"🧬 Genomes analyzed: {info['genomes_analyzed']}")
        print(f"🎯 Successful tracks: {results['successful_tracks']}/{results['total_tracks']}")
        print(f"📊 Total features found: {results['total_features_found']}")
        
        if integration['matrix_created']:
            print(f"🧬 Integrated matrix: {integration['matrix_dimensions']}")
            print(f"📊 Integrated features: {integration['integrated_features']}")
        
        print(f"📁 Output directory: {info['output_directory']}")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   {rec}")

def main():
    """Main production execution"""
    print("🚀 THREE-TRACK PRODUCTION RUNNER")
    print("="*80)
    print("Executing Track 1 (Amyloids) + Track 2 (Copper) + Track 3 (SOD)")
    print("="*80)
    
    # Option to limit genomes for testing (set to None for full run)
    genome_limit = 25  # Use for testing
    # genome_limit = None  # Use for full production run
    
    try:
        runner = ProductionTrackRunner(genome_limit=genome_limit)
        final_report = runner.run_complete_production()
        
        print(f"\n✅ Production run completed successfully!")
        print(f"📁 All results saved in: {runner.output_dir}")
        
    except Exception as e:
        print(f"❌ Production run failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()