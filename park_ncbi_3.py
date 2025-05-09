import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import time
import sys
import xml.etree.ElementTree as ET
import urllib.parse
import re
import csv
from io import StringIO
import subprocess
import os
import platform
import traceback # Added import for traceback

class NCBISRAScraper:
    """
    A class to scrape and analyze Parkinson's Disease research data from NCBI's SRA.
    Uses the NCBI E-utilities API to search and retrieve SRA records.
    Can also download and convert SRA data using the SRA Toolkit.
    """

    def __init__(self):
        """Initialize the scraper with base URL and current date."""
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.today = datetime.now()
        # Set default search period to last 6 months
        self.start_date = (self.today - timedelta(days=180)).strftime("%Y-%m-%d")
        self.end_date = self.today.strftime("%Y-%m-%d")
        # Store records during counting to avoid redundant API calls
        self.sra_cache = []
        # API rate limiting (3 requests per second without API key)
        self.request_delay = 0.34  # slightly more than 1/3 second
        # NCBI API key (if you have one - increases rate limit to 10 per second)
        self.api_key = None  # Set your API key here if you have one
        # Output directory for downloads
        self.output_dir = os.path.join(os.getcwd(), "sra_downloads")
        # Check for SRA Toolkit availability
        self.check_sra_toolkit_availability()

    def check_sra_toolkit_availability(self):
        """
        Check if SRA Toolkit commands are available in the system path.
        Sets self.sra_toolkit_available based on the check.
        """
        self.sra_toolkit_available = False
        self.prefetch_path = "prefetch" # Default to command name
        self.fasterq_dump_path = "fasterq-dump" # Default to command name
        self.fastq_dump_path = "fastq-dump" # Default to command name

        print("\nChecking for SRA Toolkit availability...")

        # Try to find prefetch using 'which' or 'where'
        try:
            if platform.system() == "Windows":
                 # Use 'where' on Windows
                result = subprocess.run(["where", "prefetch"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True) # check=True raises CalledProcessError if not found
                self.prefetch_path = result.stdout.strip().splitlines()[0] # Take the first path found

                result = subprocess.run(["where", "fasterq-dump"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                self.fasterq_dump_path = result.stdout.strip().splitlines()[0]

                result = subprocess.run(["where", "fastq-dump"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                self.fastq_dump_path = result.stdout.strip().splitlines()[0]

            else: # Linux/macOS
                # Use 'which'
                result = subprocess.run(["which", "prefetch"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                self.prefetch_path = result.stdout.strip()

                result = subprocess.run(["which", "fasterq-dump"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                self.fasterq_dump_path = result.stdout.strip()

                result = subprocess.run(["which", "fastq-dump"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        check=True)
                self.fastq_dump_path = result.stdout.strip()

            self.sra_toolkit_available = True
            print(f"SRA Toolkit detected.")
            print(f"  prefetch: {self.prefetch_path}")
            print(f"  fasterq-dump: {self.fasterq_dump_path}")
            print(f"  fastq-dump: {self.fastq_dump_path}")

            # Verify it works by running a simple version command
            try:
                result = subprocess.run([self.prefetch_path, "--version"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        timeout=5,
                                        text=True,
                                        env=os.environ.copy())  # Use current environment
                if result.returncode == 0:
                    version_output = result.stdout.strip() or result.stderr.strip()
                    print(f"SRA Toolkit version: {version_output}")
                else:
                    print("SRA Toolkit found but returned an error when testing version.")
                    print(f"Error: {result.stderr.strip()}")
                    print("Will attempt to use it anyway.")
            except Exception as e:
                print(f"Warning: Found SRA Toolkit but encountered an error when testing version: {e}")
                print("Will attempt to use it anyway.")

        except (subprocess.CalledProcessError, FileNotFoundError):
            print("SRA Toolkit not detected in system path.")
            print("Download/conversion features will be disabled.")
            print("Download SRA Toolkit from: https://github.com/ncbi/sra-tools")
            print("\nIf you have already installed SRA Toolkit, make sure its 'bin' directory is in your system's PATH.")
        except Exception as e:
            print(f"An unexpected error occurred while checking for SRA Toolkit: {type(e).__name__}: {e}")
            print("Download/conversion features will be disabled.")


    def ensure_output_directory(self):
        """
        Ensure the output directory for downloads exists.

        Returns:
            str: Path to the output directory
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"Created output directory: {self.output_dir}")
        return self.output_dir

    def set_api_key(self, api_key):
        """
        Set an NCBI API key to increase request rate limits.

        Args:
            api_key (str): Your NCBI API key
        """
        self.api_key = api_key
        if api_key:
            # With API key, you can make up to 10 requests per second
            self.request_delay = 0.11  # slightly more than 1/10 second
            print(f"API key set. Request delay reduced to {self.request_delay} seconds.")
        else:
            # Without API key, limit is 3 requests per second
            self.request_delay = 0.34
            print(f"No API key. Request delay set to {self.request_delay} seconds.")

    def set_date_range(self, days_back):
        """
        Set the date range for the search.

        Args:
            days_back (int): Number of days to look back from today
        """
        self.start_date = (self.today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        self.end_date = self.today.strftime("%Y-%m-%d")
        print(f"Date range set to: {self.start_date} to {self.end_date}")

    def search_sra_with_term(self, search_term, max_results=100):
        """
        Search SRA directly with a specific term using a format that works better with SRA.
        Uses runinfo format which is specifically designed for SRA data.

        Args:
            search_term (str): Search term to use
            max_results (int): Maximum number of results to retrieve

        Returns:
            list: List of dictionaries containing SRA record details
        """
        # Clear any previous results
        self.sra_cache = []

        print(f"\nSearching SRA for: {search_term}")
        print(f"Maximum results set to: {max_results}")

        # Build the API URL - using a different approach that works better for SRA
        # This uses the same API but with a format specifically for SRA
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

        # Parameters for the initial search
        search_params = {
            'db': 'sra',
            'term': search_term,
            'usehistory': 'y',
            'retmax': 0,  # Just get the count first
            'retmode': 'json',
            'sort': 'relevance'  # Sort by relevance to get better results
        }

        if self.api_key:
            search_params['api_key'] = self.api_key

        try:
            # Make the initial search to get the count and WebEnv
            time.sleep(self.request_delay) # Add delay before request
            response = requests.get(base_url, params=search_params, timeout=30)
            response.raise_for_status()
            results = response.json()

            count = int(results['esearchresult']['count'])
            web_env = results['esearchresult']['webenv']
            query_key = results['esearchresult']['querykey']

            print(f"Found {count} matching SRA records")

            if count == 0:
                return []

            # Now fetch the results using runinfo format
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

            # Fetch records in batches
            batch_size = 100
            fetch_count = min(count, max_results)
            records = []

            for start in range(0, fetch_count, batch_size):
                fetch_params = {
                    'db': 'sra',
                    'query_key': query_key,
                    'WebEnv': web_env,
                    'retstart': start,
                    'retmax': min(batch_size, fetch_count - start),
                    'rettype': 'runinfo',
                    'retmode': 'text'
                }

                if self.api_key:
                    fetch_params['api_key'] = self.api_key

                # Pause to respect API rate limits
                time.sleep(self.request_delay)

                fetch_response = requests.get(fetch_url, params=fetch_params, timeout=60)
                fetch_response.raise_for_status()

                # Parse the CSV data
                if fetch_response.text:
                    # Skip empty responses
                    csv_data = fetch_response.text

                    # Try to determine the delimiter by examining the first line
                    first_line = fetch_response.text.splitlines()[0] if fetch_response.text.splitlines() else ""
                    delimiter = '\t' if '\t' in first_line else ','

                    # Use the detected delimiter for runinfo format
                    reader = csv.DictReader(csv_data.splitlines(), delimiter=delimiter)
                    batch_records = list(reader)
                    records.extend(batch_records)
                    print(f"Retrieved {len(batch_records)} records (batch {start//batch_size + 1})")

            print(f"Successfully retrieved {len(records)} SRA records in total")

            # Format the records for our use
            formatted_records = []
            for i, record in enumerate(records):
                try:
                    # Create a more flexible mapping that tries multiple possible field names
                    formatted_record = {
                        'experiment_accession': record.get('Experiment', '') or record.get('experiment_accession', ''),
                        'run_accessions': [record.get('Run', '') or record.get('run_accession', '')],
                        'study_accession': record.get('SRAStudy', '') or record.get('study_accession', '') or record.get('SRA_Study', ''),
                        'sample_accession': record.get('Sample', '') or record.get('sample_accession', ''),
                        'submission_accession': record.get('Submission', '') or record.get('submission_accession', ''),
                        'experiment_title': record.get('LibraryName', '') or record.get('experiment_title', '') or record.get('Library_Name', ''),
                        'study_title': record.get('SRAStudy_title', '') or record.get('study_title', '') or record.get('SampleName', '') or record.get('Sample_Name', ''),
                        'organism': record.get('ScientificName', '') or record.get('organism', '') or record.get('Organism', ''),
                        'library_strategy': record.get('LibraryStrategy', '') or record.get('library_strategy', '') or record.get('Library_Strategy', ''),
                        'library_source': record.get('LibrarySource', '') or record.get('library_source', '') or record.get('Library_Source', ''),
                        'library_selection': record.get('LibrarySelection', '') or record.get('library_selection', '') or record.get('Library_Selection', ''),
                        'total_bases': record.get('Bases', '') or record.get('total_bases', '') or record.get('bases', ''),
                        'total_reads': record.get('TotalSpots', '') or record.get('total_spots', '') or record.get('spots', '')
                    }

                    # Add any additional fields available
                    for key, value in record.items():
                        if key not in formatted_record and value:
                            formatted_record[key] = value

                    formatted_records.append(formatted_record)
                except Exception as e:
                    print(f"Error formatting record {i+1}: {e}")
                    print(f"Problematic record data: {record}")
                    # Skip this record and continue with the next
                    continue

            # Update the cache
            self.sra_cache = formatted_records

            # If we got empty records, try an alternative approach
            if all(not record.get('study_title') for record in formatted_records):
                print("WARNING: Retrieved records appear to be empty. Trying alternative approach...")
                return self.search_sra_alternative(search_term, max_results)

            return formatted_records

        except requests.exceptions.RequestException as e:
            print(f"Error accessing NCBI API: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            try:
                print(f"Response content: {response.text[:200]}...")  # Show first 200 chars
            except:
                pass
            return []
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            return []

    def search_sra_alternative(self, search_term, max_results=100):
        """
        Alternative method to search SRA when the primary method returns empty records.
        Uses esummary instead of runinfo format.

        Args:
            search_term (str): Search term to use
            max_results (int): Maximum number of results to retrieve

        Returns:
            list: List of dictionaries containing SRA record details
        """
        print("\nUsing alternative SRA search method...")

        try:
            # First search to get IDs
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                'db': 'sra',
                'term': search_term,
                'retmax': max_results,
                'retmode': 'json',
                'sort': 'relevance'
            }

            if self.api_key:
                search_params['api_key'] = self.api_key

            time.sleep(self.request_delay) # Add delay before request
            response = requests.get(search_url, params=search_params, timeout=30)
            response.raise_for_status()
            search_results = response.json()

            id_list = search_results['esearchresult'].get('idlist', [])
            if not id_list:
                print("No SRA records found with alternative method.")
                return []

            print(f"Found {len(id_list)} SRA IDs with alternative method.")

            # Now fetch summaries for these IDs
            summary_url = f"{self.base_url}/esummary.fcgi"
            summary_params = {
                'db': 'sra',
                'id': ','.join(id_list),
                'retmode': 'json'
            }

            if self.api_key:
                summary_params['api_key'] = self.api_key

            time.sleep(self.request_delay) # Add delay before request
            summary_response = requests.get(summary_url, params=summary_params, timeout=60)
            summary_response.raise_for_status()
            summary_data = summary_response.json()

            # Process the summary data
            formatted_records = []

            if 'result' in summary_data:
                result = summary_data['result']

                for uid in result.get('uids', []):
                    if uid in result:
                        record_data = result[uid]

                        # Extract experiment info
                        expxml = record_data.get('expxml', '')
                        run_set = record_data.get('runs', {}).get('run', [])
                        if not isinstance(run_set, list):
                            run_set = [run_set]

                        # Get run accessions
                        run_accessions = []
                        for run in run_set:
                            if isinstance(run, dict) and 'acc' in run:
                                run_accessions.append(run['acc'])

                        # Create formatted record
                        formatted_record = {
                            'experiment_accession': record_data.get('Experiment', ''),
                            'run_accessions': run_accessions,
                            'study_accession': record_data.get('Study', ''),
                            'sample_accession': record_data.get('Sample', ''),
                            'submission_accession': record_data.get('Submission', ''),
                            'experiment_title': record_data.get('Title', ''),
                            'study_title': record_data.get('ExpXml', {}).get('Summary', {}).get('Title', '') or record_data.get('Title', ''),
                            'organism': record_data.get('ExpXml', {}).get('Organism', {}).get('ScientificName', ''),
                            'library_strategy': record_data.get('LibraryStrategy', ''),
                            'library_source': record_data.get('LibrarySource', ''),
                            'library_selection': record_data.get('LibrarySelection', ''),
                            'total_bases': record_data.get('Statistics', {}).get('total_bases', ''),
                            'total_reads': record_data.get('Statistics', {}).get('total_spots', '')
                        }

                        # Add any additional useful fields
                        for key, value in record_data.items():
                            if key not in formatted_record and value and not isinstance(value, dict) and not isinstance(value, list):
                                formatted_record[key] = value

                        formatted_records.append(formatted_record)

            # Update the cache with these records
            self.sra_cache = formatted_records
            print(f"Retrieved {len(formatted_records)} records with alternative method")
            return formatted_records

        except Exception as e:
            print(f"Error in alternative SRA search: {type(e).__name__}: {e}")
            return []

    def get_recent_records(self, count=10):
        """
        Get the most recent SRA records related to Parkinson's Disease from the cached results.

        Args:
            count (int): Number of records to retrieve

        Returns:
            list: List of SRA record dictionaries
        """
        print(f"\nRetrieving {count} recent SRA records from cached results...")

        if not self.sra_cache:
            print("Warning: No records in cache. Try running a search option (1 or 9) first.")
            return []

        # We don't have reliable date info in all records, so use cache order (most recent first)
        # (The E-utility search typically returns results with most recent first)

        # Return the requested number (or all if fewer)
        result_count = min(count, len(self.sra_cache))
        print(f"Returning {result_count} records from the {len(self.sra_cache)} cached records")

        return self.sra_cache[:count]

    def keyword_search(self, keywords, case_sensitive=False, search_mode='OR', search_fields=None):
        """
        Search the cached SRA records for specific keywords.

        Args:
            keywords (list): List of keywords to search for
            case_sensitive (bool): Whether the search should be case sensitive
            search_mode (str): 'AND' or 'OR' for Boolean operations
            search_fields (list): List of fields to search in (e.g., ['study_title', 'experiment_title'])

        Returns:
            list: Records matching the keyword criteria
        """
        if not self.sra_cache:
            print("Warning: No records in cache. Run a search option (1 or 9) first.")
            return []

        # Default fields to search in if none provided
        if search_fields is None:
            search_fields = ['study_title', 'experiment_title', 'sample_attributes']

        # Print search parameters
        print(f"\nPerforming keyword search on {len(self.sra_cache)} cached SRA records:")
        print(f"  Keywords: {', '.join(keywords)}")
        print(f"  Case sensitive: {case_sensitive}")
        print(f"  Search mode: {search_mode}")
        print(f"  Search fields: {', '.join(search_fields)}")

        # Define the text_contains function within this method to access case_sensitive
        def text_contains(text, keyword):
            if not isinstance(text, str):
                return False

            # Compare based on case sensitivity setting
            if case_sensitive:
                return keyword in text
            else:
                return keyword.lower() in text.lower()

        # Define dict_contains function to check for keywords in dictionary values
        def dict_contains(d, keyword):
            if not isinstance(d, dict):
                return False

            # Check dictionary keys
            for key in d:
                if text_contains(key, keyword):
                    return True

                # Check dictionary values
                value = d[key]
                if isinstance(value, str) and text_contains(value, keyword):
                    return True
                elif isinstance(value, dict) and dict_contains(value, keyword):
                    return True

            return False

        # Filter records by keywords using the specified Boolean logic
        matching_records = []
        for record in self.sra_cache:
            # Check if record matches the keywords based on search mode
            matches = []

            for keyword in keywords:
                # Check each requested field
                keyword_match = False

                for field in search_fields:
                    if field in record:
                        # Handle dictionary fields (like sample_attributes) differently
                        if field == 'sample_attributes' and isinstance(record[field], dict):
                            if dict_contains(record[field], keyword):
                                keyword_match = True
                                break
                        # Handle regular text fields
                        elif text_contains(record[field], keyword):
                            keyword_match = True
                            break

                matches.append(keyword_match)

            # Determine overall match based on search mode
            record_matches = False
            if search_mode == 'AND':
                record_matches = all(matches)
            else:  # 'OR' is the default
                record_matches = any(matches)

            if record_matches:
                matching_records.append(record)

        print(f"Found {len(matching_records)} records matching the keyword criteria")
        return matching_records

    def _format_large_number(self, num):
        """
        Format a large number into a readable format (KB, MB, GB, etc.)
        """
        for unit in ['', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if abs(num) < 1024.0:
                return f"{num:.1f} {unit}"
            num /= 1024.0
        return f"{num:.1f} EB"

    def analyze_trends(self):
        """
        Analyze trends in the SRA records related to Parkinson's Disease.
        This examines library strategies, sources, organisms, etc.
        """
        if not self.sra_cache:
            print("No records to analyze. Run a search option (1 or 9) first.")
            return

        print(f"\nAnalyzing trends in {len(self.sra_cache)} SRA records...")

        # 1. Analyze library strategies
        strategies = {}
        for record in self.sra_cache:
            if 'library_strategy' in record and record['library_strategy']:
                strategy = record['library_strategy']
                strategies[strategy] = strategies.get(strategy, 0) + 1

        if strategies:
            print("\nLibrary Strategies:")
            for strategy, count in sorted(strategies.items(), key=lambda x: x[1], reverse=True):
                print(f"  {strategy}: {count} records ({count/len(self.sra_cache)*100:.1f}%)")

        # 2. Analyze library sources
        sources = {}
        for record in self.sra_cache:
            if 'library_source' in record and record['library_source']:
                source = record['library_source']
                sources[source] = sources.get(source, 0) + 1

        if sources:
            print("\nLibrary Sources:")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                print(f"  {source}: {count} records ({count/len(self.sra_cache)*100:.1f}%)")

        # 3. Analyze organisms
        organisms = {}
        for record in self.sra_cache:
            if 'organism' in record and record['organism']:
                organism = record['organism']
                organisms[organism] = organisms.get(organism, 0) + 1

        if organisms:
            print("\nOrganisms:")
            for organism, count in sorted(organisms.items(), key=lambda x: x[1], reverse=True):
                print(f"  {organism}: {count} records ({count/len(self.sra_cache)*100:.1f}%)")

    def find_related_pmids(self, record):
        """
        Find PMIDs (PubMed IDs) related to an SRA record.

        Args:
            record (dict): SRA record

        Returns:
            list: List of PMIDs as strings
        """
        # Check if we already have a PMID in the record
        if 'pubmed_id' in record and record['pubmed_id']:
            return [record['pubmed_id']]

        # Otherwise, search PubMed using the study accession
        if 'study_accession' in record and record['study_accession']:
            try:
                search_url = f"{self.base_url}/esearch.fcgi"
                params = {
                    'db': 'pubmed',
                    'term': record['study_accession'],
                    'retmode': 'json',
                    'retmax': 5
                }

                if self.api_key:
                    params['api_key'] = self.api_key

                time.sleep(self.request_delay) # Add delay before request
                response = requests.get(search_url, params=params, timeout=30)
                response.raise_for_status()
                results = response.json()

                id_list = results['esearchresult'].get('idlist', [])
                return id_list

            except Exception as e:
                print(f"Error finding related PMIDs: {e}")
                return []

        return []

    def get_paper_abstract(self, pmid):
        """
        Get paper details including abstract for a given PubMed ID.

        Args:
            pmid (str): PubMed ID

        Returns:
            dict: Paper details including title, authors, journal, date, and abstract
        """
        try:
            # Use E-utilities to fetch the paper abstract
            fetch_url = f"{self.base_url}/efetch.fcgi"
            params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'xml'
            }

            if self.api_key:
                params['api_key'] = self.api_key

            time.sleep(self.request_delay) # Add delay before request
            response = requests.get(fetch_url, params=params, timeout=30)
            response.raise_for_status()

            # Parse the XML response
            root = ET.fromstring(response.text)

            # Extract paper details
            article = root.find('.//Article')
            if article is None:
                return None

            # Extract title
            title_elem = article.find('./ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title available"

            # Extract authors
            authors = []
            author_list = article.findall('.//AuthorList/Author')
            for author in author_list:
                last_name = author.find('./LastName')
                first_name = author.find('./ForeName')
                if last_name is not None and first_name is not None:
                    authors.append(f"{last_name.text} {first_name.text}")
                elif last_name is not None:
                    authors.append(last_name.text)

            # Extract journal
            journal_elem = article.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else "Unknown journal"

            # Extract publication date
            year_elem = article.find('.//Journal/JournalIssue/PubDate/Year')
            month_elem = article.find('.//Journal/JournalIssue/PubDate/Month')
            day_elem = article.find('.//Journal/JournalIssue/PubDate/Day')

            pub_date_parts = []
            if year_elem is not None:
                pub_date_parts.append(year_elem.text)
            if month_elem is not None:
                pub_date_parts.append(month_elem.text)
            if day_elem is not None:
                pub_date_parts.append(day_elem.text)

            publication_date = " ".join(pub_date_parts) if pub_date_parts else "Unknown date"

            # Extract abstract
            abstract_parts = []
            abstract_elems = article.findall('.//Abstract/AbstractText')

            for elem in abstract_elems:
                label = elem.get('Label')
                if label:
                    abstract_parts.append(f"{label}: {elem.text}")
                else:
                    abstract_parts.append(elem.text)

            abstract = "\n".join(abstract_parts) if abstract_parts else "No abstract available"

            return {
                'title': title,
                'authors': authors,
                'journal': journal,
                'publication_date': publication_date,
                'abstract': abstract
            }

        except Exception as e:
            print(f"Error fetching paper abstract: {e}")
            return None

    def export_data(self, filepath, format_type='csv'):
        """
        Export cached SRA records to a file in CSV or JSON format.

        Args:
            filepath (str): Path to the output file
            format_type (str): Format type ('csv' or 'json')

        Returns:
            bool: True if export was successful, False otherwise
        """
        if not self.sra_cache:
            print("No records to export. Run a search option (1 or 9) first.")
            return False

        try:
            if format_type.lower() == 'csv':
                # Determine all possible fields across all records
                all_fields = set()
                for record in self.sra_cache:
                    all_fields.update(record.keys())

                # Sort fields for better readability
                sorted_fields = sorted(all_fields)

                # Write to CSV
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=sorted_fields)
                    writer.writeheader()

                    for record in self.sra_cache:
                        # Handle special cases like lists before writing
                        row = {}
                        for key, value in record.items():
                            if isinstance(value, list):
                                row[key] = ','.join(str(v) for v in value)
                            elif isinstance(value, dict):
                                # Convert dict to JSON string
                                row[key] = json.dumps(value)
                            else:
                                row[key] = value

                        writer.writerow(row)

                print(f"Exported {len(self.sra_cache)} records to CSV: {filepath}")
                return True

            elif format_type.lower() == 'json':
                # Write to JSON
                with open(filepath, 'w', encoding='utf-8') as jsonfile:
                    json.dump(self.sra_cache, jsonfile, indent=2)

                print(f"Exported {len(self.sra_cache)} records to JSON: {filepath}")
                return True

            else:
                print(f"Unsupported format: {format_type}")
                return False

        except Exception as e:
            print(f"Error exporting data: {e}")
            return False

    def get_sra_toolkit_commands(self, run_accessions):
        """
        Generate SRA Toolkit commands for downloading and converting SRA data.

        Args:
            run_accessions (list): List of SRA run accessions

        Returns:
            dict: Dictionary with prefetch and fastq-dump commands
        """
        if not run_accessions:
            return {'prefetch': [], 'fasterq_dump': [], 'fastq_dump': []}

        # Ensure output directory exists
        output_dir = self.ensure_output_directory()

        # Generate commands for each accession
        prefetch_cmds = []
        fasterq_dump_cmds = []
        fastq_dump_cmds = []

        # Use the stored paths if available, otherwise use command names
        prefetch_cmd_name = getattr(self, 'prefetch_path', "prefetch")
        fasterq_dump_cmd_name = getattr(self, 'fasterq_dump_path', "fasterq-dump")
        fastq_dump_cmd_name = getattr(self, 'fastq_dump_path', "fastq-dump")

        for acc in run_accessions:
            # Prefetch command (download SRA)
            prefetch_cmd = f"{prefetch_cmd_name} {acc} -O {output_dir}"
            prefetch_cmds.append(prefetch_cmd)

            # fasterq-dump command (convert to FASTQ - faster method)
            fasterq_cmd = f"{fasterq_dump_cmd_name} {acc} -O {output_dir} -e 8 -p"
            fasterq_dump_cmds.append(fasterq_cmd)

            # fastq-dump command (convert to FASTQ - older method)
            fastq_cmd = f"{fastq_dump_cmd_name} {acc} -O {output_dir} --split-3"
            fastq_dump_cmds.append(fastq_cmd)

        return {
            'prefetch': prefetch_cmds,
            'fasterq_dump': fasterq_dump_cmds,
            'fastq_dump': fastq_dump_cmds
        }

    def download_sra(self, accession, output_dir=None):
        """
        Download SRA data using prefetch.

        Args:
            accession (str): SRA run accession
            output_dir (str): Output directory

        Returns:
            bool: True if download was successful, False otherwise
        """
        if not self.sra_toolkit_available:
            print("SRA Toolkit not installed or not detected. Cannot download SRA data.")
            print("If you know it's installed, try running the prefetch command directly:")
            print(f"prefetch {accession} -O <output_directory>")
            return False

        if output_dir is None:
            output_dir = self.ensure_output_directory()

        try:
            # Use the specific path if available, otherwise use the command name
            prefetch_cmd = getattr(self, 'prefetch_path', "prefetch")

            # Build the prefetch command
            cmd = [prefetch_cmd, accession, "-O", output_dir]

            print(f"Running command: {' '.join(cmd)}")

            # Create a copy of the current environment
            env = os.environ.copy()

            result = subprocess.run(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    env=env)

            if result.returncode == 0:
                print(f"Download of {accession} completed successfully")
                return True
            else:
                print(f"Download of {accession} failed with error: {result.stderr}")
                # Provide more helpful error information
                if "command not found" in result.stderr or "is not recognized" in result.stderr:
                    print("\nThe prefetch command was not found. Possible solutions:")
                    print("1. Make sure SRA Toolkit is installed")
                    print("2. Add the SRA Toolkit bin directory to your PATH")
                    print("3. Restart your terminal/command prompt after installation")
                elif "permission denied" in result.stderr.lower():
                    print("\nPermission denied. Try running with administrator/sudo privileges")
                return False

        except Exception as e:
            print(f"Error downloading SRA data for {accession}: {e}")
            print("\nTroubleshooting tips:")
            print("1. Verify SRA Toolkit is installed correctly")
            print("2. Check if you can run 'prefetch --help' directly in your terminal")
            print("3. Make sure you have internet connectivity")
            return False

    def convert_to_fastq(self, accession, method='fasterq', output_dir=None):
        """
        Convert SRA data to FASTQ format.

        Args:
            accession (str): SRA run accession
            method (str): Conversion method ('fasterq' or 'fastq')
            output_dir (str): Output directory

        Returns:
            bool: True if conversion was successful, False otherwise
        """
        if not self.sra_toolkit_available:
            print("SRA Toolkit not installed or not detected. Cannot convert SRA data.")
            cmd_name = "fasterq-dump" if method == 'fasterq' else "fastq-dump"
            print(f"If you know it's installed, try running the {cmd_name} command directly:")
            if method == 'fasterq':
                print(f"{cmd_name} {accession} -O <output_directory> -e 8 -p")
            else:
                print(f"{cmd_name} {accession} -O <output_directory> --split-3")
            return False

        if output_dir is None:
            output_dir = self.ensure_output_directory()

        try:
            # Use the specific path if available, otherwise use the command name
            if method == 'fasterq':
                cmd_path = getattr(self, 'fasterq_dump_path', "fasterq-dump")
                cmd = [cmd_path, accession, "-O", output_dir, "-e", "8", "-p"]
            else:
                cmd_path = getattr(self, 'fastq_dump_path', "fastq-dump")
                cmd = [cmd_path, accession, "-O", output_dir, "--split-3"]

            print(f"Running command: {' '.join(cmd)}")

            # Create a copy of the current environment
            env = os.environ.copy()

            result = subprocess.run(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    env=env)

            if result.returncode == 0:
                print(f"Conversion of {accession} completed successfully")
                return True
            else:
                print(f"Conversion of {accession} failed with error: {result.stderr}")
                # Provide more helpful error information
                cmd_name = cmd[0]
                if "command not found" in result.stderr or "is not recognized" in result.stderr:
                    print(f"\nThe {cmd_name} command was not found. Possible solutions:")
                    print("1. Make sure SRA Toolkit is installed")
                    print("2. Add the SRA Toolkit bin directory to your PATH")
                    print("3. Restart your terminal/command prompt after installation")
                elif "permission denied" in result.stderr.lower():
                    print("\nPermission denied. Try running with administrator/sudo privileges")
                return False

        except Exception as e:
            print(f"Error converting SRA data for {accession}: {e}")
            print("\nTroubleshooting tips:")
            print("1. Verify SRA Toolkit is installed correctly")
            print(f"2. Check if you can run '{cmd[0]} --help' directly in your terminal")
            print("3. Make sure the SRA file exists and is accessible")
            return False

    def run(self):
        """Execute the main functionality of the scraper."""
        print("NCBI SRA Parkinson's Disease Research Scraper")
        print("=============================================")

        # Use a shorter time window for faster testing
        print("Setting default date range to last 30 days")
        self.set_date_range(30)

        # Try simple API check first
        try:
            print("\nTesting API connectivity...")
            test_url = f"{self.base_url}/info.fcgi"
            test_params = {'db': 'sra', 'retmode': 'json'}
            if self.api_key:
                test_params['api_key'] = self.api_key

            response = requests.get(test_url, params=test_params, timeout=5)
            if response.status_code == 200:
                print("API connection successful!")
            else:
                print(f"Warning: API returned status code {response.status_code}")
        except Exception as e:
            print(f"Error testing API connection: {type(e).__name__}: {e}")

        # Main menu
        while True:
            try:
                print("\n=============================================")
                print("MAIN MENU")
                print("=============================================")
                print("1. Search for Parkinson's Disease SRA records")
                print("2. Display recent SRA records")
                print("3. Advanced keyword search (within cached records)")
                print("4. Analyze SRA trends")
                print("5. Export data to file")
                print("6. Change date range")
                print("7. Set API key")
                print("8. Generate SRA Toolkit commands")
                print("9. Direct search with NCBI API (e.g., 'metagenomic AND Parkinson')")
                print("10. Download SRA data (by accession or from cache)")
                print("11. Convert SRA to FASTQ (by accession or from cache)")
                print("0. Exit")

                choice = input("\nEnter your choice (0-11): ")
            except Exception as e:
                print(f"Error displaying menu: {type(e).__name__}: {e}")
                choice = None

            if choice == '0':
                print("Exiting program...")
                break

            elif choice == '1':
                try:
                    print("\n--- Retrieving Parkinson's Disease SRA Records ---")
                    # Build the search query for Parkinson's Disease
                    search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"

                    # Ask if user wants to include metagenomic/metagenome terms
                    include_metagenomic = input("Include metagenomic data? (y/n, default: n): ").lower() == 'y'
                    if include_metagenomic:
                        search_query = f"({search_query}) AND (metagenomic OR metagenome OR metagenomics OR \"meta genomic\" OR \"meta-genomic\")"
                        print("Added metagenomic terms to search query")

                    # Add the date range if specified
                    if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                        # Use proper NCBI date format
                        date_range = f" AND \"{self.start_date}\":\"{self.end_date}\"[PDAT]"
                        search_query += date_range
                    else:
                         print("Warning: Date range not set. Searching all dates.")


                    # Ask for maximum results
                    max_results_input = input("Maximum number of results to retrieve (default: 100, X to return to main menu): ") or "100"
                    if max_results_input.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    try:
                        max_results = int(max_results_input)
                        if max_results <= 0:
                            print("Invalid number. Using default of 100.")
                            max_results = 100
                    except ValueError:
                        print("Invalid input. Using default of 100.")
                        max_results = 100

                    records = self.search_sra_with_term(search_query, max_results=max_results)
                    print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '2':
                try:
                    if not self.sra_cache:
                        print("No records in cache. Running option 1 to retrieve records first...")
                        search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"

                        # Ask if user wants to include metagenomic data
                        include_metagenomic = input("Include metagenomic data? (y/n, default: n): ").lower() == 'y'
                        if include_metagenomic:
                            search_query = f"({search_query}) AND (metagenomic OR metagenome OR metagenomics OR \"meta genomic\" OR \"meta-genomic\")"
                            print("Added metagenomic terms to search query")

                        # Add date range if enabled
                        include_date_input = input("Include date range filter? (y/n, default: n): ")
                        include_date = include_date_input.lower() == 'y'
                        if include_date and hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                            date_range = f" AND \"{self.start_date}\":\"{self.end_date}\"[PDAT]"
                            search_query += date_range
                            print(f"Added date range filter: {date_range}")
                        else:
                             print("Warning: Date range not included in search.")


                        # Ask for maximum results for the initial search if cache is empty
                        max_results_input = input("Maximum number of results to retrieve for initial search (default: 100): ") or "100"
                        try:
                            max_results = int(max_results_input)
                            if max_results <= 0:
                                print("Invalid number. Using default of 100.")
                                max_results = 100
                        except ValueError:
                            print("Invalid input. Using default of 100.")
                            max_results = 100

                        records = self.search_sra_with_term(search_query, max_results=max_results)
                        print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")

                    print("\n--- Recent SRA Records ---")
                    # Ask how many records to display
                    display_count = 10  # Default
                    if self.sra_cache:
                        count_input = input(f"How many records to display? (1-{len(self.sra_cache)}, default: 10, X to return to main menu): ")
                        if count_input.upper() == 'X':
                            print("Returning to main menu...")
                            continue

                        if count_input.strip():
                            try:
                                input_count = int(count_input)
                                # Ensure the count is within valid range
                                if 1 <= input_count <= len(self.sra_cache):
                                    display_count = input_count
                                else:
                                    print(f"Invalid number. Using default of 10 records.")
                            except ValueError:
                                print(f"Invalid input. Using default of 10 records.")
                    else:
                         print("No records in cache to display.")
                         continue # Go back to main menu

                    recent_records = self.get_recent_records(count=display_count)
                    if recent_records:
                        print(f"\nShowing {len(recent_records)} Parkinson's Disease related SRA records:")

                        # Store PMIDs for each record to use later for abstracts
                        record_pmids = {}

                        # Display all records with full details
                        for i, record in enumerate(recent_records, 1):
                            print("\n" + "="*80)
                            print(f"RECORD #{i}")
                            print("="*80)
                            print(f"Study Title: {record.get('study_title', 'N/A')}")
                            if 'experiment_title' in record:
                                print(f"Experiment Title: {record.get('experiment_title', 'N/A')}")
                            print(f"Study Accession: {record.get('study_accession', 'N/A')}")
                            print(f"Experiment Accession: {record.get('experiment_accession', 'N/A')}")

                            if 'run_accessions' in record and record['run_accessions']:
                                print(f"Run Accession(s): {', '.join(record['run_accessions'])}")

                            if 'library_strategy' in record:
                                print(f"Library Strategy: {record.get('library_strategy', 'N/A')}")
                            if 'library_source' in record:
                                print(f"Library Source: {record.get('library_source', 'N/A')}")
                            if 'library_selection' in record:
                                print(f"Library Selection: {record.get('library_selection', 'N/A')}")

                            if 'total_bases' in record and record['total_bases']:
                                try:
                                    bases = int(record['total_bases'])
                                    print(f"Total Bases: {bases:,} ({self._format_large_number(bases)})")
                                except:
                                    print(f"Total Bases: {record['total_bases']}")

                            if 'total_reads' in record and record['total_reads']:
                                try:
                                    reads = int(record['total_reads'])
                                    print(f"Total Reads: {reads:,}")
                                except:
                                    print(f"Total Reads: {record['total_reads']}")

                            if 'organism' in record:
                                print(f"Organism: {record.get('organism', 'N/A')}")

                            # Print sample attributes in a readable format
                            if 'sample_attributes' in record and record['sample_attributes']:
                                print("\nSample Attributes:")
                                # Ensure sample_attributes is a dictionary before iterating
                                if isinstance(record['sample_attributes'], dict):
                                    for key, value in record['sample_attributes'].items():
                                        print(f"  {key}: {value}")
                                else:
                                     print(f"  {record['sample_attributes']}") # Print as is if not a dict

                            # Check for related publications
                            print("\nRelated Publications:")
                            if 'pubmed_id' in record and record['pubmed_id']:
                                pmid = record['pubmed_id']
                                print(f"PubMed ID: {pmid}")
                                print(f"PubMed URL: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
                                record_pmids[i] = [pmid]
                            else:
                                pmids = self.find_related_pmids(record)
                                if pmids:
                                    print(f"PubMed ID(s): {', '.join(pmids)}")
                                    print(f"PubMed URL: https://pubmed.ncbi.nlm.nih.gov/{pmids[0]}/")
                                    record_pmids[i] = pmids
                                else:
                                    print("No related publications found.")
                                    record_pmids[i] = []

                        # After displaying all records, offer options
                        while True:
                            print("\n" + "="*80)
                            print("OPTIONS:")
                            print("1. View paper abstract")
                            print("2. Download SRA format")
                            print("3. Convert to FASTQ")
                            print("0. Return to main menu")

                            option = input("\nEnter your choice (0-3, X to return to main menu): ")
                            if option.upper() == 'X':
                                print("Returning to main menu...")
                                break # Exit inner loop and go back to main menu loop

                            if option == '0':
                                break # Exit inner loop and go back to main menu loop

                            elif option == '1':
                                # View paper abstract
                                print("\nRecords with available papers:")
                                available_papers = []

                                for record_num, pmids in record_pmids.items():
                                    if pmids:
                                        record = recent_records[record_num - 1]
                                        title = record.get('study_title', 'No title available')
                                        print(f"{record_num}. {title} (PubMed ID: {pmids[0]})")
                                        available_papers.append(record_num)

                                if not available_papers:
                                    print("No papers available for any of the displayed records.")
                                    continue

                                # Ask which paper to view
                                paper_choice = input("\nEnter record number to view paper abstract, 0 to cancel, or X to return to main menu: ")
                                if paper_choice.upper() == 'X':
                                    print("Returning to main menu...")
                                    break # Exit inner loop
                                if paper_choice == '0':
                                    continue

                                if paper_choice.isdigit() and 1 <= int(paper_choice) <= len(recent_records) and int(paper_choice) in available_papers:
                                    record_num = int(paper_choice)
                                    pmid = record_pmids[record_num][0]  # Use the first PMID

                                    print(f"\nFetching abstract for PubMed ID: {pmid}...")
                                    paper_details = self.get_paper_abstract(pmid)

                                    if paper_details:
                                        print("\n" + "="*80)
                                        print("PAPER DETAILS")
                                        print("="*80)
                                        print(f"Title: {paper_details['title']}")
                                        print(f"Authors: {', '.join(paper_details['authors'])}")
                                        print(f"Journal: {paper_details['journal']}")
                                        print(f"Publication Date: {paper_details['publication_date']}")
                                        print("\nAbstract:")
                                        print("-"*40)
                                        print(paper_details['abstract'])
                                        print("-"*40)
                                        print(f"PubMed URL: https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
                                        print("="*80)
                                    else:
                                        print("Could not retrieve paper abstract.")
                                else:
                                    print("Invalid record number or no paper available for that record.")

                            elif option == '2':
                                # Download SRA format
                                if not self.sra_toolkit_available:
                                    print("\nSRA Toolkit not detected. Cannot download SRA data.")
                                    print("Please install SRA Toolkit: https://github.com/ncbi/sra-tools")
                                    continue

                                record_choice = input(f"\nEnter record number (1-{len(recent_records)}) to download SRA, 0 to cancel, or X to return to main menu: ")
                                if record_choice.upper() == 'X':
                                    print("Returning to main menu...")
                                    break # Exit inner loop
                                if record_choice == '0':
                                    continue

                                if record_choice.isdigit() and 1 <= int(record_choice) <= len(recent_records):
                                    record_num = int(record_choice)
                                    record = recent_records[record_num - 1]

                                    if 'run_accessions' not in record or not record['run_accessions']:
                                        print("No run accessions found for this record. Cannot download.")
                                        continue

                                    print(f"\nSelected record for download: {record.get('study_title', 'Unknown study')}")
                                    print(f"Run accession(s): {', '.join(record['run_accessions'])}")

                                    # Confirm the output directory
                                    default_output_dir = self.ensure_output_directory()
                                    custom_output_dir = input(f"Enter output directory (default: {default_output_dir}): ").strip()
                                    output_dir = custom_output_dir if custom_output_dir else default_output_dir

                                    # Ensure output directory exists
                                    if not os.path.exists(output_dir):
                                        os.makedirs(output_dir)
                                        print(f"Created output directory: {output_dir}")

                                    all_downloads_successful = True
                                    # Download each run accession
                                    for run_acc in record['run_accessions']:
                                        print(f"\nAttempting to download run accession: {run_acc}")
                                        success = self.download_sra(run_acc, output_dir)

                                        if not success:
                                            all_downloads_successful = False
                                            print(f"Download failed for {run_acc}.")
                                            # Decide if we should continue with other accessions or stop
                                            continue_downloads = input("Continue with remaining downloads for this record? (y/n, default: y): ").lower()
                                            if continue_downloads == 'n':
                                                break # Stop processing accessions for this record

                                    if all_downloads_successful:
                                        print("\nAll selected SRA files downloaded successfully.")
                                        print(f"Output files are in: {output_dir}")
                                    else:
                                        print("\nSome downloads failed.")

                                else:
                                    print(f"Invalid record number. Please enter a number between 1 and {len(recent_records)}.")

                            elif option == '3':
                                # Convert to FASTQ
                                if not self.sra_toolkit_available:
                                    print("\nSRA Toolkit not detected. Cannot convert SRA data.")
                                    print("Please install SRA Toolkit: https://github.com/ncbi/sra-tools")
                                    continue

                                record_choice = input(f"\nEnter record number (1-{len(recent_records)}) to convert SRA to FASTQ, 0 to cancel, or X to return to main menu: ")
                                if record_choice.upper() == 'X':
                                    print("Returning to main menu...")
                                    break # Exit inner loop
                                if record_choice == '0':
                                    continue

                                if record_choice.isdigit() and 1 <= int(record_choice) <= len(recent_records):
                                    record_num = int(record_choice)
                                    record = recent_records[record_num - 1]

                                    if 'run_accessions' not in record or not record['run_accessions']:
                                        print("No run accessions found for this record. Cannot convert.")
                                        continue

                                    run_acc_list = record['run_accessions']
                                    print(f"\nSelected record for conversion: {record.get('study_title', 'Unknown study')}")
                                    print(f"Will process run accession(s): {', '.join(run_acc_list)}")

                                    # Choose conversion method
                                    print("\nSelect conversion method:")
                                    print("1. fasterq-dump (recommended, faster)")
                                    print("2. fastq-dump (older method)")

                                    method_choice = input("Enter choice (1-2, default: 1, X to return to main menu): ") or "1"
                                    if method_choice.upper() == 'X':
                                        print("Returning to main menu...")
                                        break # Exit inner loop

                                    method = 'fasterq' if method_choice == '1' else 'fastq'

                                    # Specify output directory
                                    default_output_dir = self.ensure_output_directory()
                                    custom_output_dir = input(f"Enter output directory (default: {default_output_dir}): ").strip()
                                    output_dir = custom_output_dir if custom_output_dir else default_output_dir

                                    # Ensure output directory exists
                                    if not os.path.exists(output_dir):
                                        os.makedirs(output_dir)
                                        print(f"Created output directory: {output_dir}")

                                    all_conversions_successful = True
                                    for run_acc in run_acc_list:
                                        print(f"\nAttempting to convert run accession: {run_acc} using {method}...")
                                        conversion_success = self.convert_to_fastq(run_acc, method, output_dir)

                                        if not conversion_success:
                                            all_conversions_successful = False
                                            print(f"Conversion failed for {run_acc}.")
                                            # Decide if we should continue with other accessions or stop
                                            continue_processing = input("Continue with remaining accessions for this record? (y/n, default: y): ").lower()
                                            if continue_processing == 'n':
                                                break # Stop processing accessions for this record
                                            else:
                                                continue # Continue loop

                                    if all_conversions_successful:
                                        print("\nAll selected SRA files converted to FASTQ successfully.")
                                        print(f"Output files are in: {output_dir}")
                                    else:
                                        print("\nSome conversions failed.")

                                else:
                                    print(f"Invalid record number. Please enter a number between 1 and {len(recent_records)}.")

                            else:
                                print("Invalid option. Please try again.")

                    else:
                        print("No records retrieved.")
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '3':
                try:
                    if not self.sra_cache:
                        print("No records in cache. Running option 1 to retrieve records first...")
                        search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"

                        # Ask if user wants to include metagenomic data
                        include_metagenomic = input("Include metagenomic data? (y/n, default: n): ").lower() == 'y'
                        if include_metagenomic:
                            search_query = f"({search_query}) AND (metagenomic OR metagenome OR metagenomics OR \"meta genomic\" OR \"meta-genomic\")"
                            print("Added metagenomic terms to search query")

                        # Add date range if enabled
                        include_date_input = input("Include date range filter? (y/n, default: n): ")
                        include_date = include_date_input.lower() == 'y'
                        if include_date and hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                            date_range = f" AND \"{self.start_date}\":\"{self.end_date}\"[PDAT]"
                            search_query += date_range
                            print(f"Added date range filter: {date_range}")
                        else:
                             print("Warning: Date range not included in search.")


                        # Ask for maximum results for the initial search if cache is empty
                        max_results_input = input("Maximum number of results to retrieve for initial search (default: 100): ") or "100"
                        try:
                            max_results = int(max_results_input)
                            if max_results <= 0:
                                print("Invalid number. Using default of 100.")
                                max_results = 100
                        except ValueError:
                            print("Invalid input. Using default of 100.")
                            max_results = 100

                        records = self.search_sra_with_term(search_query, max_results=max_results)
                        print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")

                    if not self.sra_cache:
                         print("No records in cache to search.")
                         continue # Go back to main menu

                    print("\n--- Advanced Keyword Search (within cached records) ---")
                    print("This option searches within already retrieved records.")
                    keywords_input = input("Enter keywords separated by commas (X to return to main menu): ")
                    if keywords_input.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    keywords = [k.strip() for k in keywords_input.split(',')]
                    if not keywords or all(not k for k in keywords):
                        print("No keywords provided. Returning to main menu.")
                        continue


                    case_sensitive_input = input("Case sensitive search? (y/n, default: n, X to return to main menu): ")
                    if case_sensitive_input.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    case_sensitive = case_sensitive_input.lower() == 'y'

                    print("\nSelect search mode:")
                    print("1. OR - Match any keyword")
                    print("2. AND - Match all keywords")
                    search_mode_choice = input("Enter choice (1-2, default: 1, X to return to main menu): ") or "1"
                    if search_mode_choice.upper() == 'X':
                        print("Returning to main menu...")
                        continue

                    search_mode = "OR"
                    if search_mode_choice == "2":
                        search_mode = "AND"

                    print("\nSelect search fields:")
                    print("1. All default fields (study_title, experiment_title, sample_attributes)")
                    print("2. Study title only")
                    print("3. Sample attributes only")
                    print("4. Custom field selection")
                    fields_choice = input("Enter choice (1-4, default: 1, X to return to main menu): ") or "1"
                    if fields_choice.upper() == 'X':
                        print("Returning to main menu...")
                        continue

                    search_fields = None  # Default will be used
                    if fields_choice == "2":
                        search_fields = ['study_title']
                    elif fields_choice == "3":
                        search_fields = ['sample_attributes']
                    elif fields_choice == "4":
                        print("\nAvailable fields:")
                        # Dynamically list fields from the first record if cache is not empty
                        if self.sra_cache:
                            print("Fields in cached records:")
                            for field in sorted(self.sra_cache[0].keys()):
                                print(f"- {field}")
                        else:
                             print("- study_title")
                             print("- experiment_title")
                             print("- sample_attributes")
                             print("- organism")
                             print("(Cache is empty, showing common fields)")

                        fields_input = input("Enter fields separated by commas: ")
                        search_fields = [f.strip() for f in fields_input.split(',')]
                        if not search_fields or all(not f for f in search_fields):
                            print("No fields provided. Using default fields.")
                            search_fields = None # Revert to default

                    results = self.keyword_search(keywords, case_sensitive, search_mode, search_fields)

                    if results:
                        print(f"\nFound {len(results)} records matching the criteria:")
                        for i, record in enumerate(results, 1):
                            print(f"{i}. {record.get('study_title', 'No title available')}")

                        # Option to view details
                        while True:
                            view_details = input("\nView record details? Enter record number, 0 to return to menu, or X to return to main menu: ")
                            if view_details.upper() == 'X':
                                print("Returning to main menu...")
                                break
                            if view_details == '0':
                                break

                            if view_details.isdigit() and 1 <= int(view_details) <= len(results):
                                record = results[int(view_details) - 1]
                                print("\n" + "="*80)
                                # Display as many fields as possible for direct search results
                                title_shown = False
                                for key, value in record.items():
                                    # Handle special cases first
                                    if key == 'study_title' and value:
                                        print(f"Study Title: {value}")
                                        title_shown = True
                                    elif key == 'run_accessions' in key and value: # Check if key contains 'run_accessions'
                                        print(f"Run Accession(s): {', '.join(value)}")
                                    elif key == 'sample_attributes' in key and value: # Check if key contains 'sample_attributes'
                                         print("\nSample Attributes:")
                                         if isinstance(value, dict):
                                             for attr_key, attr_value in value.items():
                                                 print(f"  {attr_key}: {attr_value}")
                                         else:
                                             print(f"  {value}")
                                    # Skip empty values and already shown fields
                                    elif value and key not in ['study_title', 'run_accessions', 'sample_attributes']:
                                        # Format the field name for display
                                        display_name = ' '.join(word.capitalize() for word in key.split('_'))
                                        print(f"{display_name}: {value}")

                                # If no title was shown but we have a sample name, use that
                                if not title_shown and 'SampleName' in record:
                                    print(f"Sample Name: {record['SampleName']}")

                                print("="*80)

                                # Ask if user wants to view another record
                                continue_viewing = input("\nView another record? (y/n, default: n, X to return to main menu): ").lower()
                                if continue_viewing.upper() == 'X':
                                    print("Returning to main menu...")
                                    break
                                if continue_viewing != 'y':
                                    break
                            else:
                                print(f"Invalid record number. Please enter a number between 1 and {len(results)}.")
                    else:
                        print("No records found matching those keywords.")
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '4':
                try:
                    if not self.sra_cache:
                        print("No records in cache. Running option 1 to retrieve records first...")
                        search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"

                        # Ask if user wants to include metagenomic data
                        include_metagenomic = input("Include metagenomic data? (y/n, default: n): ").lower() == 'y'
                        if include_metagenomic:
                            search_query = f"({search_query}) AND (metagenomic OR metagenome OR metagenomics OR \"meta genomic\" OR \"meta-genomic\")"
                            print("Added metagenomic terms to search query")

                        # Add date range if enabled
                        include_date_input = input("Include date range filter? (y/n, default: n): ")
                        include_date = include_date_input.lower() == 'y'
                        if include_date and hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                            date_range = f" AND \"{self.start_date}\":\"{self.end_date}\"[PDAT]"
                            search_query += date_range
                            print(f"Added date range filter: {date_range}")
                        else:
                             print("Warning: Date range not included in search.")

                        # Ask for maximum results for the initial search if cache is empty
                        max_results_input = input("Maximum number of results to retrieve for initial search (default: 100): ") or "100"
                        try:
                            max_results = int(max_results_input)
                            if max_results <= 0:
                                print("Invalid number. Using default of 100.")
                                max_results = 100
                        except ValueError:
                            print("Invalid input. Using default of 100.")
                            max_results = 100

                        records = self.search_sra_with_term(search_query, max_results=max_results)
                        print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")

                    print("\n--- SRA Trend Analysis ---")
                    self.analyze_trends()
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '5':
                try:
                    if not self.sra_cache:
                        print("No records in cache. Running option 1 to retrieve records first...")
                        search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"
                        records = self.search_sra_with_term(search_query)
                        print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")

                    if not self.sra_cache:
                         print("No records in cache to export.")
                         continue # Go back to main menu

                    print("\n--- Export Data ---")
                    filename = input("Enter filename (default: parkinsons_sra_records): ") or "parkinsons_sra_records"
                    format_choice = input("Enter format (csv/json, default: csv): ").lower() or "csv"

                    if format_choice not in ['csv', 'json']:
                        print(f"Unsupported format: {format_choice}. Using csv instead.")
                        format_choice = 'csv'

                    filepath = f"{filename}.{format_choice}"
                    success = self.export_data(filepath, format_choice)

                    if success:
                        print(f"Data successfully exported to {filepath}")
                    else:
                        print("Data export failed.")
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '6':
                try:
                    print("\n--- Change Date Range ---")
                    days_input = input("Enter number of days to look back (default: 30, X to return to main menu): ")
                    if days_input.upper() == 'X':
                        print("Returning to main menu...")
                        continue

                    if days_input.isdigit():
                        days = int(days_input)
                        self.set_date_range(days)
                        print(f"Date range set to last {days} days")
                        # Clear cache since date range changed
                        self.sra_cache = []
                        print("Record cache cleared. Please run a search option (1 or 9) to retrieve records with the new date range.")
                    else:
                        print("Invalid input. Using default (30 days).")
                        self.set_date_range(30)
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '7':
                try:
                    print("\n--- Set NCBI API Key ---")
                    print("An API key allows higher request rates (10/second vs 3/second).")
                    print("You can obtain an API key from: https://www.ncbi.nlm.nih.gov/account/settings/")

                    api_key = input("Enter your NCBI API key (leave blank to clear, X to return to main menu): ").strip()
                    if api_key.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    self.set_api_key(api_key)
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '8':
                try:
                    if not self.sra_cache:
                        print("No records in cache. Running option 1 to retrieve records first...")
                        search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"
                        records = self.search_sra_with_term(search_query)
                        print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")

                    if not self.sra_cache:
                         print("No records in cache to generate commands for.")
                         continue # Go back to main menu

                    print("\n--- Generate SRA Toolkit Commands ---")
                    # List records first
                    recent_records = self.get_recent_records(count=20)  # Show more records for this option

                    if recent_records:
                        print("\nSelect a record to generate download commands:")
                        for i, record in enumerate(recent_records, 1):
                            print(f"{i}. {record.get('study_title', 'No title available')}")

                        record_choice = input("\nEnter record number, 0 to return, or X to return to main menu: ")
                        if record_choice.upper() == 'X':
                            print("Returning to main menu...")
                            continue
                        if record_choice == '0':
                            continue

                        if record_choice.isdigit() and 1 <= int(record_choice) <= len(recent_records):
                            record = recent_records[int(record_choice) - 1]

                            if 'run_accessions' not in record or not record['run_accessions']:
                                print("No run accessions found for this record. Cannot generate download commands.")
                                continue

                            print(f"\nGenerating download commands for: {record.get('study_title')}")
                            print(f"Run accession(s): {', '.join(record['run_accessions'])}")

                            commands = self.get_sra_toolkit_commands(record['run_accessions'])

                            print("\nSRA Toolkit must be installed to use these commands.")
                            print("Download from: https://github.com/ncbi/sra-tools\n")

                            print("1. Download SRA format files:")
                            for cmd in commands['prefetch']:
                                print(f"   {cmd}")

                            print("\n2. Convert SRA to FASTQ (split files):")
                            for cmd in commands['fasterq_dump']:
                                print(f"   {cmd}")

                            print("\nTip: For multiple files, you can create a batch script with these commands.")

                            # Option to save commands to a file
                            save_option = input("\nSave commands to a shell script? (y/n, default: n, X to return to main menu): ").lower()
                            if save_option.upper() == 'X':
                                print("Returning to main menu...")
                                continue
                            if save_option == 'y':
                                script_name = input("Enter script filename (default: download_commands.sh): ") or "download_commands.sh"

                                try:
                                    with open(script_name, 'w') as f:
                                        f.write("#!/bin/bash\n\n")
                                        f.write("# SRA download commands for Parkinson's research data\n")
                                        f.write(f"# Study: {record.get('study_title')}\n")
                                        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                                        f.write("# 1. Download SRA format files\n")
                                        for cmd in commands['prefetch']:
                                            f.write(f"{cmd}\n")

                                        f.write("\n# 2. Convert SRA to FASTQ (split files)\n")
                                        for cmd in commands['fasterq_dump']:
                                            f.write(f"{cmd}\n")

                                    print(f"Commands saved to {script_name}")
                                    print("You may need to make the script executable with: chmod +x " + script_name)
                                except Exception as e:
                                    print(f"Error saving script file: {e}")

                        else:
                            print("Invalid record number.")
                    else:
                        print("No records available to generate commands for.")

                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '9':
                try:
                    print("\n--- Direct SRA Search with NCBI API ---")
                    print("This option makes a new API call to NCBI to retrieve fresh records.")
                    print("Enter a search term using NCBI's search syntax:")
                    print("Examples:")
                    print("  metagenomic AND Parkinson")
                    print("  metagenome AND human gut")
                    print("  \"16S rRNA\" AND metagenome")

                    search_term = input("\nEnter search term (X to return to main menu): ")
                    if search_term.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    if not search_term.strip():
                        print("No search term provided. Please try again.")
                        continue

                    # Ask for maximum results
                    max_results_input = input("Maximum number of results to retrieve (default: 100, X to return to main menu): ") or "100"
                    if max_results_input.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    try:
                        max_results = int(max_results_input)
                        if max_results <= 0:
                            print("Invalid number. Using default of 100.")
                            max_results = 100
                    except ValueError:
                        print("Invalid input. Using default of 100.")
                        max_results = 100

                    # Add date range if enabled
                    include_date_input = input("Include date range filter? (y/n, default: n, X to return to main menu): ")
                    if include_date_input.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    include_date = include_date_input.lower() == 'y'
                    if include_date and hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                        # Use proper NCBI date format
                        date_range = f" AND \"{self.start_date}\":\"{self.end_date}\"[PDAT]"
                        search_term += date_range
                        print(f"Added date range filter: {date_range}")
                    else:
                         print("Warning: Date range not included in search.")


                    # Perform the search
                    records = self.search_sra_with_term(search_term, max_results=max_results)

                    if records:
                        print(f"\nRetrieved {len(records)} records. Showing first 20:")
                        display_count = min(20, len(records))

                        for i, record in enumerate(records[:display_count], 1):
                            print(f"{i}. {record.get('study_title', 'No title available')}")

                        # Ask if user wants to see record details
                        while True:
                            view_details = input("\nView record details? Enter record number, 0 to return to menu, or X to return to main menu: ")
                            if view_details.upper() == 'X':
                                print("Returning to main menu...")
                                break
                            if view_details == '0':
                                break

                            if view_details.isdigit() and 1 <= int(view_details) <= display_count:
                                record_num = int(view_details)
                                record = records[record_num - 1]

                                print("\n" + "="*80)
                                # Display as many fields as possible for direct search results
                                title_shown = False
                                for key, value in record.items():
                                    # Handle special cases first
                                    if key == 'study_title' and value:
                                        print(f"Study Title: {value}")
                                        title_shown = True
                                    elif key == 'run_accessions' in key and value: # Check if key contains 'run_accessions'
                                        print(f"Run Accession(s): {', '.join(value)}")
                                    elif key == 'sample_attributes' in key and value: # Check if key contains 'sample_attributes'
                                         print("\nSample Attributes:")
                                         if isinstance(value, dict):
                                             for attr_key, attr_value in value.items():
                                                 print(f"  {attr_key}: {attr_value}")
                                         else:
                                             print(f"  {value}")
                                    # Skip empty values and already shown fields
                                    elif value and key not in ['study_title', 'run_accessions', 'sample_attributes']:
                                        # Format the field name for display
                                        display_name = ' '.join(word.capitalize() for word in key.split('_'))
                                        print(f"{display_name}: {value}")

                                # If no title was shown but we have a sample name, use that
                                if not title_shown and 'SampleName' in record:
                                    print(f"Sample Name: {record['SampleName']}")

                                print("="*80)

                                # Ask if user wants to view another record
                                continue_viewing = input("\nView another record? (y/n, default: n, X to return to main menu): ").lower()
                                if continue_viewing.upper() == 'X':
                                    print("Returning to main menu...")
                                    break
                                if continue_viewing != 'y':
                                    break
                            else:
                                print(f"Invalid record number. Please enter a number between 1 and {display_count}.")
                    else:
                        print("No records found matching your search term.")

                    # Ask if user wants to save these records to the cache
                    if records:
                        save_to_cache_input = input("\nSave these records to the cache for further analysis? (y/n, default: y, X to return to main menu): ")
                        if save_to_cache_input.upper() == 'X':
                            print("Returning to main menu...")
                            continue
                        save_to_cache = save_to_cache_input.lower() != 'n'
                        if save_to_cache:
                            self.sra_cache = records
                            print(f"Saved {len(records)} records to the cache.")
                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '10':
                try:
                    print("\n--- Download SRA Data (by accession or from cache) ---")

                    if not self.sra_toolkit_available:
                        print("SRA Toolkit not detected in your system path.")
                        print("Please install SRA Toolkit to use this feature:")
                        print("https://github.com/ncbi/sra-tools")
                        continue

                    # Option to download directly from accession or from cached records
                    print("\nSelect download source:")
                    print("1. Download by SRA run accession (requires manual input)")
                    print("2. Select from cached records")
                    print("0. Return to main menu")

                    download_source_choice = input("Enter choice (0-2, default: 1, X to return to main menu): ") or "1"
                    if download_source_choice.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    if download_source_choice == '0':
                        continue

                    run_acc_list = [] # Use a list to handle multiple accessions

                    if download_source_choice == "1":
                        # Download by manual accession input
                        acc_input = input("Enter SRA run accession(s) to download (comma-separated for multiple): ").strip()
                        if not acc_input:
                            print("No accession provided.")
                            continue
                        run_acc_list = [acc.strip() for acc in acc_input.split(',') if acc.strip()]

                    elif download_source_choice == "2":
                        # Select from cached records
                        if not self.sra_cache:
                            print("No records in cache. Running option 1 to retrieve records first...")
                            search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"
                            records = self.search_sra_with_term(search_query)
                            print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")

                        if not self.sra_cache:
                             print("No records in cache to select from.")
                             continue # Go back to main menu

                        # Display available records
                        recent_records = self.get_recent_records(count=20) # Show up to 20 records

                        if recent_records:
                            print("\nSelect a record to download:")
                            for i, record in enumerate(recent_records, 1):
                                print(f"{i}. {record.get('study_title', 'No title available')}")

                            record_choice = input("\nEnter record number, 0 to return, or X to return to main menu: ")
                            if record_choice.upper() == 'X':
                                print("Returning to main menu...")
                                continue
                            if record_choice == '0':
                                continue

                            if record_choice.isdigit() and 1 <= int(record_choice) <= len(recent_records):
                                record = recent_records[int(record_choice) - 1]

                                if 'run_accessions' not in record or not record['run_accessions']:
                                    print("No run accessions found for this record. Cannot download.")
                                    continue

                                run_acc_list = record['run_accessions']
                                print(f"\nSelected record: {record.get('study_title', 'Unknown study')}")
                                print(f"Will download run accession(s): {', '.join(run_acc_list)}")

                            else:
                                print("Invalid record number.")
                                continue # Go back to the start of option 10

                        else:
                            print("No records available to select from.")
                            continue # Go back to main menu

                    else:
                        print("Invalid option.")
                        continue # Go back to the start of option 10

                    # If we have run_acc_list, proceed with download
                    if run_acc_list:
                        # Confirm the output directory
                        default_output_dir = self.ensure_output_directory()
                        custom_output_dir = input(f"Enter output directory (default: {default_output_dir}): ").strip()
                        output_dir = custom_output_dir if custom_output_dir else default_output_dir

                        # Ensure output directory exists
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                            print(f"Created output directory: {output_dir}")

                        all_downloads_successful = True
                        # Download each run accession
                        for run_acc in run_acc_list:
                            print(f"\nAttempting to download run accession: {run_acc}")
                            success = self.download_sra(run_acc, output_dir)

                            if not success:
                                all_downloads_successful = False
                                print(f"Download failed for {run_acc}.")
                                # Decide if we should continue with other accessions or stop
                                continue_downloads = input("Continue with remaining downloads? (y/n, default: y): ").lower()
                                if continue_downloads == 'n':
                                    break # Stop processing accessions

                        if all_downloads_successful:
                            print("\nAll selected SRA files downloaded successfully.")
                            print(f"Output files are in: {output_dir}")
                        else:
                            print("\nSome downloads failed.")


                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            elif choice == '11':
                try:
                    print("\n--- Convert SRA to FASTQ (by accession or from cache) ---")

                    if not self.sra_toolkit_available:
                        print("SRA Toolkit not detected in your system path.")
                        print("Please install SRA Toolkit to use this feature:")
                        print("https://github.com/ncbi/sra-tools")
                        continue

                    # Option to convert directly from accession or from previously downloaded SRA
                    print("\nSelect conversion source:")
                    print("1. Convert a previously downloaded SRA file (requires accession)")
                    print("2. Select from cached records (download and convert in one step)")
                    print("0. Return to main menu")

                    convert_option = input("Enter choice (0-2, default: 1, X to return to main menu): ") or "1"
                    if convert_option.upper() == 'X':
                        print("Returning to main menu...")
                        continue
                    if convert_option == '0':
                        continue

                    run_acc_list = [] # Use a list to handle multiple accessions from a record

                    if convert_option == "1":
                        # Convert existing SRA file
                        run_acc = input("Enter SRA run accession to convert: ").strip()
                        if not run_acc:
                            print("No accession provided.")
                            continue
                        run_acc_list = [run_acc] # Put single accession in a list

                    elif convert_option == "2":
                        # Select from available records
                        if not self.sra_cache:
                            print("No records in cache. Running option 1 to retrieve records first...")
                            search_query = "(Parkinson OR Parkinson's OR Parkinsons OR \"Parkinson's Disease\" OR \"Parkinsons Disease\" OR Parkinsonism)"
                            records = self.search_sra_with_term(search_query)
                            print(f"\n>>> Total Parkinson's Disease related SRA records found: {len(records)} <<<\n")

                        if not self.sra_cache:
                             print("No records in cache to select from.")
                             continue # Go back to main menu

                        # Display available records
                        recent_records = self.get_recent_records(count=20) # Show up to 20 records

                        if recent_records:
                            print("\nSelect a record to download and convert:")
                            for i, record in enumerate(recent_records, 1):
                                print(f"{i}. {record.get('study_title', 'No title available')}")

                            record_choice = input("\nEnter record number, 0 to return, or X to return to main menu: ")
                            if record_choice.upper() == 'X':
                                print("Returning to main menu...")
                                continue
                            if record_choice == '0':
                                continue

                            if record_choice.isdigit() and 1 <= int(record_choice) <= len(recent_records):
                                record = recent_records[int(record_choice) - 1]

                                if 'run_accessions' not in record or not record['run_accessions']:
                                    print("No run accessions found for this record. Cannot download/convert.")
                                    continue

                                run_acc_list = record['run_accessions']
                                print(f"\nSelected record: {record.get('study_title', 'Unknown study')}")
                                print(f"Will process run accession(s): {', '.join(run_acc_list)}")

                            else:
                                print("Invalid record number.")
                                continue # Go back to the start of option 11

                        else:
                            print("No records available to select from.")
                            continue # Go back to main menu

                    else:
                        print("Invalid option.")
                        continue # Go back to the start of option 11

                    # If we have run_acc_list, proceed with conversion options
                    if run_acc_list:
                        # Choose conversion method
                        print("\nSelect conversion method:")
                        print("1. fasterq-dump (recommended, faster)")
                        print("2. fastq-dump (older method)")

                        method_choice = input("Enter choice (1-2, default: 1, X to return to main menu): ") or "1"
                        if method_choice.upper() == 'X':
                            print("Returning to main menu...")
                            continue

                        method = 'fasterq' if method_choice == '1' else 'fastq'

                        # Specify output directory
                        default_output_dir = self.ensure_output_directory()
                        custom_output_dir = input(f"Enter output directory (default: {default_output_dir}): ").strip()
                        output_dir = custom_output_dir if custom_output_dir else default_output_dir

                        # Ensure output directory exists
                        if not os.path.exists(output_dir):
                            os.makedirs(output_dir)
                            print(f"Created output directory: {output_dir}")

                        all_processes_successful = True
                        for run_acc in run_acc_list:
                            if convert_option == "2": # If selecting from cached records, download first
                                print(f"\nAttempting to download run accession: {run_acc}")
                                download_success = self.download_sra(run_acc, output_dir)
                                if not download_success:
                                    print(f"Download failed for {run_acc}. Cannot proceed with conversion for this run.")
                                    all_processes_successful = False
                                    # Decide if we should continue with other accessions or stop
                                    continue_processing = input("Continue with remaining accessions for this record? (y/n, default: y): ").lower()
                                    if continue_processing == 'n':
                                        break # Stop processing accessions for this record
                                    else:
                                        continue # Skip conversion for this failed download but continue loop

                            # Convert to FASTQ (either from existing or just downloaded)
                            print(f"\nAttempting to convert {run_acc} to FASTQ format using {method}...")
                            conversion_success = self.convert_to_fastq(run_acc, method, output_dir)

                            if not conversion_success:
                                all_processes_successful = False
                                print(f"Conversion failed for {run_acc}.")
                                # Decide if we should continue with other accessions or stop
                                continue_processing = input("Continue with remaining accessions for this record? (y/n, default: y): ").lower()
                                if continue_processing == 'n':
                                    break # Stop processing accessions for this record
                                else:
                                    continue # Continue loop

                        if all_processes_successful:
                            print("\nAll selected SRA files processed successfully (downloaded and/or converted).")
                            print(f"Output files are in: {output_dir}")
                        else:
                            print("\nSome processes failed.")


                except Exception as e:
                    print(f"Error: {type(e).__name__}: {e}")
                    traceback.print_exc() # Print traceback for debugging

            else:
                print("Invalid choice. Please try again.")

        print("\nProgram completed successfully.")

if __name__ == "__main__":
    print("Starting NCBI SRA scraper for Parkinson's Disease research...\n")
    try:
        scraper = NCBISRAScraper()
        scraper.run()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Unhandled exception: {type(e).__name__}: {e}")
        traceback.print_exc()
