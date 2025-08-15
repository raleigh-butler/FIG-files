# Integrated Copper-Amyloid-SOD1 Research Project

## Overview

This project implements a systematic data-gathering approach to investigate the hypothesis that bacterial amyloids in the gut microbiome sequester copper and cross-seed SOD1 misfolding, contributing to Parkinson's disease neurodegeneration.

## Biological Hypothesis

**Primary Mechanism:**
1. Gut bacterial amyloids bind available copper
2. Reduced copper bioavailability affects host SOD1 function  
3. Copper-deficient SOD1 misfolds into pathological forms
4. Cross-seeding between bacterial and host amyloids accelerates pathology

## Project Structure

```
Copper_SOD1/
├── summary_copper_article.rtf          # Original research summary
├── bvbrc_copper_search_plan.rtf        # Your initial search strategy
├── copper_research_implementation_plan.txt  # Detailed implementation
├── integrated_copper_amyloid_search_strategy.txt  # Combined approach
├── copper_amyloid_extractor.py         # Main extraction script
└── README_COPPER_PROJECT.md           # This file
```

## Research Tracks

### Track 1: Bacterial Amyloid Systems
- **Primary targets**: CsgA (220K+ results), CsgB (225K+ results), TasA (66K+ results)
- **Secondary targets**: AgfA/AgfB (Salmonella), FapC (Pseudomonas), PSM (Staphylococcus)
- **Focus**: Gut microbiome-relevant amyloid producers

### Track 2: Copper Homeostasis Systems  
- **Transport**: CtrA, CopA, CusA, CueO
- **Chaperones**: CopZ, CCS, ScoA
- **Regulation**: CueR, CopY, CusR, CopS
- **Focus**: Copper sequestration and resistance mechanisms

### Track 3: Superoxide Dismutase Systems
- **Core enzymes**: SodA (Mn-SOD), SodB (Fe-SOD), SodC (Cu/Zn-SOD)
- **Related**: Catalase, glutathione systems
- **Focus**: Copper-dependent antioxidant systems

## Target Roles (20 total)

### Bacterial Amyloids (8 roles)
- `CsgA`: Major curlin subunit
- `CsgB`: Minor curlin subunit  
- `AgfA`: Salmonella curli major subunit
- `TasA`: Bacillus biofilm matrix protein
- `FapC`: Pseudomonas functional amyloid
- `PSM`: Staphylococcal phenol-soluble modulin
- `ChpD`: Streptomyces chaplin
- `AmyA`: Generic bacterial amyloid protein

### Copper Systems (8 roles)
- `CtrA`: Copper transporter A
- `CopA`: Copper-exporting ATPase
- `CusA`: Copper efflux transporter
- `CueO`: Copper efflux oxidase
- `CopZ`: Copper chaperone
- `CueR`: Copper efflux regulator
- `CusR`: Copper-sensing regulator
- `CopY`: Copper operon repressor

### SOD Systems (4 roles)
- `SodA`: Manganese superoxide dismutase
- `SodB`: Iron superoxide dismutase
- `SodC`: Copper-zinc superoxide dismutase
- `CAT`: Catalase

## Subsystem State Logic

### Active (Complete Systems)
- Amyloid + Copper transport + SOD system present
- OR High copper resistance + amyloid production
- OR Complete curli system (CsgA + CsgB + regulation)

### Likely (Partial Systems)  
- Major amyloid component + some copper handling
- OR SOD + partial copper system
- OR Biofilm matrix + metal tolerance

### Unknown (Mixed Patterns)
- Single amyloid gene without context
- Copper transport without regulation
- SOD without copper handling

### Inactive (Minimal Systems)
- No amyloid, minimal copper systems
- No oxidative stress response
- Obligate intracellular organisms

## Expected Dataset Characteristics

### Scale Predictions
- **CsgA searches**: 220,618 features → ~10,000-50,000 genomes
- **Target dataset**: 1,000-5,000 representative genomes
- **Deep analysis**: 200-500 high-quality genomes
- **Comparison**: Exceeds Histidine (989), far exceeds Alpha-synuclein (6)

### Taxonomic Distribution
- **High representation**: Enterobacteriaceae, Bacillaceae, Pseudomonadaceae
- **Focus**: Gut microbiome taxa for clinical relevance
- **Comparative**: Environmental bacteria for copper resistance context

## Implementation Workflow

### Phase 1: Data Collection (Week 1)
1. Execute BV-BRC searches using `copper_amyloid_extractor.py`
2. Track 1: Amyloid systems (CsgA, CsgB priority)
3. Track 2: Copper homeostasis systems
4. Track 3: SOD systems
5. Filter for gut microbiome relevance

### Phase 2: Integration (Week 2)
1. Build genome-role binary matrix
2. Apply integrated state determination logic
3. Cross-reference amyloid-copper co-occurrence
4. Identify high-value intersection genomes

### Phase 3: Validation (Week 3)
1. NCBI taxonomic verification
2. Representative genome mapping
3. Quality control and filtering
4. Gut microbiome relevance validation

### Phase 4: Analysis Preparation (Week 4)
1. Generate standardized output files
2. Neural network training dataset
3. Statistical analysis of patterns
4. Target prioritization for experimental validation

## Usage Instructions

### Three-Track Approach (RECOMMENDED)

The project now implements a **three-track approach** for more comprehensive and specialized data extraction:

#### Quick Testing
```bash
cd /Users/raleigh/Desktop/FIG/Copper_SOD1
python3 quick_track_test.py
```

#### Individual Track Testing  
```bash
python3 track1_bacterial_amyloids.py    # Bacterial amyloids
python3 track2_copper_homeostasis.py    # Copper systems  
python3 track3_sod_systems.py           # SOD systems
```

#### Full Production Run (All Three Tracks)
```bash
python3 run_production_tracks.py
```

### Legacy Integrated Approach
```bash
python3 copper_amyloid_extractor.py
```

### Expected Outputs

#### Three-Track Approach Outputs
```
production_results_YYYYMMDD_HHMMSS/
├── bacterial_amyloids_results_YYYYMMDD_HHMMSS.json       # Track 1 complete results
├── bacterial_amyloids_features_YYYYMMDD_HHMMSS.csv       # Track 1 features  
├── copper_homeostasis_results_YYYYMMDD_HHMMSS.json       # Track 2 complete results
├── copper_homeostasis_features_YYYYMMDD_HHMMSS.csv       # Track 2 features
├── sod_systems_results_YYYYMMDD_HHMMSS.json              # Track 3 complete results
├── sod_systems_features_YYYYMMDD_HHMMSS.csv              # Track 3 features
├── integrated_genome_role_matrix_YYYYMMDD_HHMMSS.json    # Combined binary matrix
├── integrated_genome_role_matrix_YYYYMMDD_HHMMSS.csv     # ML-ready format
└── production_run_report_YYYYMMDD_HHMMSS.json            # Comprehensive analysis
```

#### Legacy Integrated Approach Outputs  
1. **Main Dataset**: `copper_amyloid_sod_dataset_YYYYMMDD_HHMMSS.tsv`
2. **Roles File**: `copper_amyloid_sod_roles_YYYYMMDD_HHMMSS.tsv`  
3. **Binary Matrix**: `copper_amyloid_sod_binary_YYYYMMDD_HHMMSS.tsv`
4. **Summary Statistics**: `copper_amyloid_sod_summary_YYYYMMDD_HHMMSS.json`

### Next Steps After Data Collection

1. **Taxonomic Validation** (use Histidine methodology):
   ```python
   # Adapt create_correct_taxonomic_dataset.py for copper data
   # NCBI taxonomy verification
   # Representative genome mapping
   ```

2. **Neural Network Training** (use Histidine template):
   ```python
   # Adapt corrected_taxonomy_model.py for 20 roles
   # Hierarchical taxonomy embeddings  
   # Anti-overfitting validation
   ```

3. **Biological Analysis**:
   - Amyloid-copper co-occurrence patterns
   - Gut microbiome correlation analysis
   - Target prioritization for SOCK mouse validation

## Success Metrics

### Quantitative Targets
- ✅ 500+ genomes with integrated amyloid-copper-SOD data
- ✅ 15+ roles represented in ≥5% of genomes  
- ✅ >90% gut microbiome clinical relevance
- ✅ Clear correlation between amyloid and copper systems

### Biological Validation
- Expected co-occurrence: CsgA with CsgB, CopA with CueR
- Taxonomic clustering matches known biology
- Environmental associations (copper-rich vs copper-poor)
- Metal-binding predictions align with experimental data

### Clinical Translation
- Prioritized targets for SOCK mouse validation
- Testable hypotheses for copper sequestration
- Biomarker candidates for gut-brain axis
- Therapeutic intervention points identified

## Integration with Previous Projects

This project leverages the proven methodology from:

- **Histidine Degradation**: Systematic data collection, NCBI validation, neural network architecture
- **Alpha-Synuclein**: Protein aggregation focus, chaperone system analysis
- **Bacterial Amyloids**: Cross-seeding mechanisms, gut-brain axis connections

Key advantages:
1. **Scale**: Expected 10x larger than Histidine dataset
2. **Integration**: Multi-system analysis (amyloids + copper + SOD)
3. **Clinical relevance**: Direct gut microbiome-Parkinson's connection
4. **Experimental validation**: SOCK mouse model ready for testing

## File Dependencies

Ensure the following files are available for full workflow:
- `../Histidine/reps.tsv` (representative genome mappings)
- `../Histidine/create_correct_taxonomic_dataset.py` (taxonomy validation)
- `../Histidine/corrected_taxonomy_model.py` (neural network template)

## Contact & Support

This project implements the systematic methodology developed for Histidine and Alpha-synuclein research, adapted for the specific biological context of copper-amyloid interactions in Parkinson's disease.