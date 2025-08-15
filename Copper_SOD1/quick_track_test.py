#!/usr/bin/env python3
"""
Quick Track Test - Test basic functionality of all three tracks
"""

import sys
import traceback

def test_imports():
    """Test that all track modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from track1_bacterial_amyloids import BacterialAmyloidsTrack
        print("✅ Track 1 (Bacterial Amyloids) - Import successful")
        
        from track2_copper_homeostasis import CopperHomeostasisTrack
        print("✅ Track 2 (Copper Homeostasis) - Import successful") 
        
        from track3_sod_systems import SODSystemsTrack
        print("✅ Track 3 (SOD Systems) - Import successful")
        
        from shared_utilities import bvbrc_utils
        print("✅ Shared Utilities - Import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_initialization():
    """Test that track classes can be initialized"""
    print("\n🏗️  Testing track initialization...")
    
    try:
        from track1_bacterial_amyloids import BacterialAmyloidsTrack
        from track2_copper_homeostasis import CopperHomeostasisTrack
        from track3_sod_systems import SODSystemsTrack
        
        track1 = BacterialAmyloidsTrack()
        print(f"✅ Track 1 initialized - {len(track1.gene_search_terms)} gene terms, {len(track1.functional_search_terms)} functional terms")
        
        track2 = CopperHomeostasisTrack()
        print(f"✅ Track 2 initialized - {len(track2.gene_search_terms)} gene terms, {len(track2.functional_search_terms)} functional terms")
        
        track3 = SODSystemsTrack()
        print(f"✅ Track 3 initialized - {len(track3.gene_search_terms)} gene terms, {len(track3.functional_search_terms)} functional terms")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        traceback.print_exc()
        return False

def test_genome_loading():
    """Test that representative genomes can be loaded"""
    print("\n📖 Testing genome loading...")
    
    try:
        from shared_utilities import bvbrc_utils
        
        # Test loading with small limit
        genomes = bvbrc_utils.load_representative_genomes(limit=5)
        
        if genomes:
            print(f"✅ Genomes loaded successfully - {len(genomes)} genomes")
            # Show first few genome IDs
            genome_ids = list(genomes.keys())[:3]
            for genome_id in genome_ids:
                genome_info = genomes[genome_id]
                print(f"   {genome_id}: {genome_info.get('genome_name', 'Unknown')}")
            return True
        else:
            print("❌ No genomes loaded")
            return False
            
    except Exception as e:
        print(f"❌ Genome loading failed: {e}")
        traceback.print_exc()
        return False

def test_api_handler():
    """Test basic API handler functionality"""
    print("\n📡 Testing API handler...")
    
    try:
        from robust_api_handler import RobustBVBRCHandler
        
        handler = RobustBVBRCHandler()
        print("✅ API handler created successfully")
        
        # Test loading genomes through handler
        genomes = handler.load_representative_genomes(limit=3)
        print(f"✅ API handler loaded {len(genomes)} genomes")
        
        return True
        
    except Exception as e:
        print(f"❌ API handler test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run quick tests"""
    print("🚀 QUICK TRACK FUNCTIONALITY TEST")
    print("="*50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Track Initialization", test_initialization), 
        ("Genome Loading", test_genome_loading),
        ("API Handler", test_api_handler)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 QUICK TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Tracks ready for use!")
    elif passed >= total * 0.75:
        print("⚠️  MOSTLY WORKING - Minor issues to fix")
    else:
        print("❌ SIGNIFICANT ISSUES - Multiple problems detected")

if __name__ == "__main__":
    main()