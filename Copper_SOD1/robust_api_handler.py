#!/usr/bin/env python3
"""
Robust API Handler for BV-BRC with timeout management and retry logic
Handles API timeout issues with exponential backoff and adaptive rate limiting
"""

import requests
import json
import csv
import time
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime
import random

class RobustBVBRCHandler:
    """Robust BV-BRC API handler with comprehensive timeout and retry management"""
    
    def __init__(self):
        self.base_url = "https://www.bv-brc.org/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'CopperAmyloidResearch/1.0'
        })
        
        # Timeout and retry configuration
        self.base_timeout = 30  # Base timeout in seconds
        self.max_timeout = 120  # Maximum timeout for retries
        self.max_retries = 3
        self.base_delay = 1.0   # Base delay between requests
        self.max_delay = 5.0    # Maximum delay for backoff
        
        # Track API call statistics
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'timeout_errors': 0,
            'http_errors': 0,
            'retry_attempts': 0
        }
    
    def load_representative_genomes(self, limit: Optional[int] = None) -> Dict[str, Dict]:
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
    
    def robust_api_call(self, url: str, params: str, search_context: str = "") -> Tuple[bool, List[Dict]]:
        """Make API call with robust timeout handling and exponential backoff"""
        
        full_url = f"{url}?{params}"
        
        for attempt in range(self.max_retries + 1):
            # Calculate timeout and delay for this attempt
            timeout = min(self.base_timeout * (2 ** attempt), self.max_timeout)
            
            if attempt > 0:
                # Exponential backoff with jitter
                delay = min(self.base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1), self.max_delay)
                print(f"    ⏳ Retry {attempt}/{self.max_retries} after {delay:.1f}s delay...")
                time.sleep(delay)
                self.stats['retry_attempts'] += 1
            
            try:
                self.stats['total_calls'] += 1
                
                response = self.session.get(full_url, timeout=timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    self.stats['successful_calls'] += 1
                    return True, data
                    
                elif response.status_code == 400:
                    # Bad request - don't retry
                    print(f"    ✗ Bad request (400) for {search_context}")
                    self.stats['http_errors'] += 1
                    return False, []
                    
                elif response.status_code in [429, 503, 504]:
                    # Rate limited or server error - retry
                    print(f"    ⚠️  Server error {response.status_code} for {search_context}")
                    self.stats['http_errors'] += 1
                    continue  # Retry
                    
                else:
                    print(f"    ✗ HTTP {response.status_code} for {search_context}")
                    self.stats['http_errors'] += 1
                    continue  # Retry
                    
            except requests.exceptions.Timeout:
                print(f"    ⏱️  Timeout ({timeout}s) for {search_context}")
                self.stats['timeout_errors'] += 1
                if attempt == self.max_retries:
                    return False, []
                continue  # Retry with longer timeout
                
            except requests.exceptions.ConnectionError:
                print(f"    🔌 Connection error for {search_context}")
                if attempt == self.max_retries:
                    return False, []
                continue  # Retry
                
            except Exception as e:
                print(f"    ❌ Unexpected error for {search_context}: {e}")
                if attempt == self.max_retries:
                    return False, []
                continue  # Retry
        
        return False, []
    
    def search_gene_in_genome(self, gene_term: str, genome_id: str, search_type: str = 'gene') -> Dict:
        """Search for a specific gene/product in a specific genome"""
        
        url = f"{self.base_url}/genome_feature/"
        
        if search_type == 'gene':
            # Gene name search
            query = f'and(eq(genome_id,{genome_id}),eq(gene,"{gene_term}"))'
        elif search_type == 'product':
            # Product description search
            query = f'and(eq(genome_id,{genome_id}),keyword({gene_term}))'
        else:
            raise ValueError(f"Invalid search_type: {search_type}")
        
        # Request comprehensive BV-BRC feature information
        params = f"{query}&select(genome_id,genome_name,accession,feature_type,patric_id,refseq_locus_tag,start,end,strand,na_length,gene,product,organism_name,taxon_id)&limit(200)"
        
        search_context = f"{gene_term} in {genome_id}"
        success, data = self.robust_api_call(url, params, search_context)
        
        if success:
            return {
                "success": True,
                "genome_id": genome_id,
                "gene_term": gene_term,
                "search_type": search_type,
                "results": data,
                "count": len(data)
            }
        else:
            return {
                "success": False,
                "genome_id": genome_id,
                "gene_term": gene_term,
                "search_type": search_type,
                "results": [],
                "count": 0,
                "error": "API call failed after retries"
            }

# Create global instance
api_handler = RobustBVBRCHandler()