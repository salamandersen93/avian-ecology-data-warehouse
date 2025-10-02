# Farmland and Grassland Avian Ecology Data Warehouse

> Udacity Data Engineering Capstone Project: AWS Redshift, PostgreSQL, and Python Implementation

---

## Project Overview

This project implements a cloud-based data warehouse that integrates agricultural survey data with avian sighting records for grassland and farmland-dependent bird species. The warehouse combines USDA agricultural census data with Cornell Lab of Ornithology's eBird citizen science observations to enable analysis of relationships between farming practices and bird population dynamics across the United States for the year 2017.

The resulting data warehouse serves as a foundation for ornithological research, conservation policy analysis, and sustainable agriculture decision-making.

---

## Business Context

Grassland bird populations have experienced dramatic declines over the past several decades due to habitat loss from agricultural expansion and changing farming practices. Understanding the relationship between agricultural land use and bird populations is critical for:

- **Conservation Researchers**: Identifying which agricultural practices support or harm specific bird species
- **Policymakers**: Informing legislation such as the Growing Climate Solutions Act (2021) that supports sustainable farming practices
- **Agricultural Organizations**: Understanding the environmental impact of farming decisions
- **Ornithologists**: Tracking population trends and habitat associations for species of conservation concern

This data warehouse enables analysts to explore questions such as: Does increased chemical usage on cropland correlate with decreased bird observations? Do counties with higher conservation program enrollment support larger populations of grassland birds? Which species co-occur in similar agricultural landscapes?

---

## Data Sources

### USDA National Agricultural Statistics Service (NASS) Census

**Source**: 2017 Census of Agriculture (NASS.USDA.gov)  
**Format**: Excel (converted to CSV and JSON)  
**Geographic Scope**: County-level (FIPS codes) across the United States  
**Temporal Scope**: 2017 (census conducted every 5 years)

**Agricultural Metrics Included**:
- Land use composition (farmland, cropland, pastureland, irrigated land)
- Conservation program enrollment (CRP, WRP, Farmable Wetlands, CREP)
- Chemical application rates (insecticides, nematicides, herbicides, growth regulators, fungicides)
- Animal manure treatment practices
- Harvested cropland acreage

**Data Extraction Strategy**:
Two tables were extracted to satisfy project requirements for multiple data source types:
1. **Farms Table**: Agricultural practices and land use metrics (CSV format)
2. **FIPS Table**: Geographic identifiers linking counties to states (JSON format)

### eBird Citizen Science Data

**Source**: Cornell Lab of Ornithology eBird database (eBird.org/science)  
**Acquisition Method**: Data request API  
**Geographic Scope**: Continental United States  
**Temporal Scope**: January 1, 2017 - December 31, 2017  
**Observation Count**: ~3.4 million records

**Species Selection Criteria**:
Seventeen grassland and farmland-dependent songbird species were manually selected based on literature review and conservation status. Species were chosen for their reliance on agricultural and grassland ecosystems for food, shelter, and breeding habitat.

**Target Species**:
- Northern Bobwhite
- Horned Lark
- Upland Sandpiper
- Grasshopper Sparrow
- Baird's Sparrow
- Long-billed Curlew
- American Pipit
- Killdeer
- Sprague's Pipit
- Lapland Longspur
- Vesper Sparrow
- House Sparrow
- Red-winged Blackbird
- Bobolink
- Snow Bunting
- Song Sparrow
- Eastern Meadowlark

**Data Elements Captured**:
- Species identification (common and scientific names)
- Observation counts (exact or estimated)
- Geographic coordinates (latitude/longitude)
- Observation date and time
- Sampling event metadata (duration, distance traveled, observer ID)
- Locality information (eBird "hotspots")

**Data Quality Assurance**:
Quality checks implemented in `eBird_data_acquisition.py`:
- Species name standardization to controlled vocabulary
- Date validation (within 2017 boundaries)
- Geographic validation (within continental US)
- Duplicate detection and removal
- Data type validation

---

## Data Warehouse Architecture

### Schema Design: Star Schema

The warehouse implements a star schema optimized for analytical queries, with one central fact table surrounded by dimension tables.

### Fact Table: `observation_table`

**Purpose**: Central table containing all bird observation events  
**Row Count**: ~3.4 million observations

| Column | Type | Description |
|--------|------|-------------|
| observation_id | INT (PRIMARY KEY) | Unique identifier for each observation record |
| common_name | TEXT | Common name of observed species |
| FIPS_code | INT | Geographic identifier (county level) |
| observation_count | TEXT | Number of individuals observed (see note below) |
| sampling_event_id | TEXT | Links to sampling event metadata |

**Note on observation_count**: This field is stored as TEXT rather than INT to accommodate eBird reporting conventions. When observers cannot determine exact counts due to large flocks or uncertainty, they report 'X'. This preserves data fidelity and allows analysts to apply appropriate imputation strategies based on their analytical requirements.

### Dimension Table: `FIPS_table`

**Purpose**: Geographic reference linking FIPS codes to human-readable locations

| Column | Type | Description |
|--------|------|-------------|
| FIPS_code | INT (PRIMARY KEY) | Federal Information Processing Standard code |
| county | TEXT | County name |
| state | TEXT | State name |

### Dimension Table: `farm_table`

**Purpose**: Agricultural practices and land use metrics by county

| Column | Type | Description |
|--------|------|-------------|
| FIPS_code | INT (PRIMARY KEY) | Geographic identifier |
| y17_M059 | TEXT | Acres of Land in Farms as % of Land Area |
| y17_M061 | TEXT | Acres of Irrigated Land as % of Land in Farms |
| y17_M063 | TEXT | Acres of Total Cropland as % of Land Area |
| y17_M066 | TEXT | Acres of Harvested Cropland as % of Land in Farms |
| y17_M068 | TEXT | Acres of Pastureland as % of Land in Farms |
| y17_M070 | TEXT | Acres Enrolled in Conservation Programs as % of Land in Farms |
| y17_M078 | TEXT | Acres Treated with Animal Manure as % of Total Cropland |
| y17_M079 | TEXT | Acres Treated with Insecticides as % of Total Cropland |
| y17_M080 | TEXT | Acres Treated with Nematicides as % of Total Cropland |
| y17_M081 | TEXT | Acres Treated with Herbicides as % of Total Cropland |
| y17_M082 | TEXT | Acres Treated with Growth Regulators as % of Total Cropland |
| y17_M083 | TEXT | Acres Treated with Fungicides as % of Total Cropland |

**Note**: NASS variable codes (y17_Mxxx) are used as column names due to length constraints. Full descriptions are provided in the data dictionary below.

### Dimension Table: `sampling_event_metadata_table`

**Purpose**: eBird checklist metadata providing observational context

| Column | Type | Description |
|--------|------|-------------|
| sampling_event_id | TEXT (PRIMARY KEY) | Unique identifier for eBird checklist |
| locality | TEXT | eBird "hotspot" (park, trail, farm, etc.) |
| latitude | FLOAT | Geographic coordinate |
| longitude | FLOAT | Geographic coordinate |
| observation_date | TEXT | Date of observation |
| observer_id | TEXT | eBird user identifier |
| duration_minutes | INT | Time spent on sampling event |
| effort_distance_km | INT | Distance traveled during observation |

### Dimension Table: `taxonomy`

**Purpose**: Scientific classification for observed species

| Column | Type | Description |
|--------|------|-------------|
| common_name | TEXT (PRIMARY KEY) | Non-scientific species name |
| scientific_name | TEXT | Latin binomial nomenclature |
| taxonomic_order | TEXT | Biological classification order |

---

## ETL Pipeline Architecture

### Pipeline Components

#### 1. Data Acquisition Scripts

**`NASS_data_acquisition.py`**
- Downloads 2017 Agricultural Census from NASS.USDA.gov
- Extracts farms table with agricultural metrics (CSV output)
- Extracts FIPS geographic reference table (JSON output)
- Performs initial data cleaning and validation
- Outputs: `Farms.csv`, `FIPS.json`

**`eBird_data_acquisition.py`**
- Requests data for 17 target species via eBird API
- Implements quality checks:
  - Species name standardization
  - Date range validation (2017 only)
  - Geographic boundary validation (continental US)
  - Duplicate detection
- Merges individual species files
- Outputs: `merged_cleaned.csv`

**Integration Point**: All acquisition scripts output to local filesystem before upload to S3.

#### 2. Cloud Storage Layer (AWS S3)

**Purpose**: Centralized staging area for raw data files before loading into Redshift

**Bucket Structure**:
```
s3://avian-ecology-warehouse/
├── Farms.csv
├── FIPS.json
└── merged_cleaned.csv
```

**Integration Point**: Serves as source for Redshift COPY commands during ETL execution.

#### 3. Database Setup Script

**`create_tables.py`**
- Establishes connection to AWS Redshift cluster
- Drops existing tables (if any) to ensure clean state
- Creates staging tables for initial data load
- Creates final star schema tables (fact + dimensions)
- Defines primary keys and data types

**Integration Point**: Must execute successfully before ETL script runs.

#### 4. ETL Execution Script

**`etl.py`**
- Orchestrates the complete data loading process
- Implements three-stage pipeline:

**Stage 1: Load Staging Tables**
- Executes COPY commands from S3 to Redshift staging tables
- Staging tables mirror raw data structure
- Enables data validation before transformation

**Stage 2: Data Transformation**
- Cleans and standardizes data types
- Handles special cases (e.g., 'X' values in observation counts)
- Performs data quality checks
- Applies business logic transformations

**Stage 3: Insert into Production Tables**
- Loads transformed data into star schema tables
- Enforces referential integrity
- Creates indexes for query optimization
- Generates unique observation_id values

**Integration Point**: Final step producing the queryable data warehouse.

---

## Complete ETL Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                    DATA ACQUISITION PHASE                        │
│                                                                  │
│  NASS Website → NASS_data_acquisition.py → Farms.csv, FIPS.json │
│  eBird API → eBird_data_acquisition.py → merged_cleaned.csv     │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                      CLOUD STORAGE LAYER                         │
│                                                                  │
│  Local Filesystem → Upload to S3 Bucket                         │
│  (avian-ecology-warehouse/)                                     │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                   DATABASE INITIALIZATION                        │
│                                                                  │
│  create_tables.py:                                              │
│    1. Connect to Redshift cluster                               │
│    2. Drop existing tables (if any)                             │
│    3. Create staging tables                                     │
│    4. Create star schema tables                                 │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                        ETL EXECUTION                             │
│                                                                  │
│  etl.py:                                                        │
│                                                                  │
│  Stage 1: Load Staging Tables                                   │
│    → COPY commands from S3 to Redshift staging                  │
│    → Raw data preserved in staging area                         │
│                                                                  │
│  Stage 2: Data Transformation                                   │
│    → Type conversions and standardization                       │
│    → Business logic application                                 │
│    → Quality validation checks                                  │
│                                                                  │
│  Stage 3: Production Load                                       │
│    → INSERT INTO star schema tables                             │
│    → Generate unique IDs                                        │
│    → Create indexes for performance                             │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
                   QUERYABLE DATA WAREHOUSE
                   (AWS Redshift Cluster)
```

---

## Use Cases and Sample Queries

The data warehouse supports diverse analytical use cases across research, policy, and conservation domains. Sample queries demonstrating these capabilities are documented in `sample_queries.ipynb`.

### Query 1: Species Distribution Analysis

**Use Case**: A researcher wants to understand the geographic distribution of observation reports by species.

**Business Question**: Which counties have the highest observation counts for each species?

**Query Pattern**: 
```sql
SELECT common_name, county, state, COUNT(observation_id) as report_count
FROM observation_table 
JOIN FIPS_table USING (FIPS_code)
GROUP BY common_name, county, state
ORDER BY report_count DESC;
```

**Analytical Value**: Identifies geographic hotspots for conservation prioritization.

### Query 2: Observer Activity Tracking

**Use Case**: An ornithology lab wants to track all species observed by their research team.

**Business Question**: What species has a specific observer recorded?

**Query Pattern**:
```sql
SELECT DISTINCT common_name, scientific_name, observation_date
FROM observation_table
JOIN sampling_event_metadata_table USING (sampling_event_id)
JOIN taxonomy USING (common_name)
WHERE observer_id = 'specific_observer_id'
ORDER BY observation_date;
```

**Analytical Value**: Enables research team coordination and data validation.

### Query 3: Agricultural Impact Assessment

**Use Case**: A policymaker wants to understand how agricultural practices correlate with bird populations.

**Business Question**: Is there a relationship between chemical usage on farmland and bird observation counts?

**Query Pattern**:
```sql
SELECT 
    f.FIPS_code, 
    fips.county, 
    fips.state,
    COUNT(o.observation_id) as total_observations,
    f.y17_M059 as farmland_percent,
    f.y17_M063 as cropland_percent,
    f.y17_M079 as insecticide_percent,
    f.y17_M081 as herbicide_percent
FROM observation_table o
JOIN FIPS_table fips USING (FIPS_code)
JOIN farm_table f USING (FIPS_code)
GROUP BY f.FIPS_code, fips.county, fips.state, f.y17_M059, f.y17_M063, f.y17_M079, f.y17_M081;
```

**Analytical Value**: Informs sustainable agriculture policy and conservation funding allocation.

### Query 4: Conservation Program Efficacy

**Use Case**: A researcher wants to evaluate whether conservation programs support bird populations.

**Business Question**: Do counties with higher conservation enrollment have more bird observations?

**Query Pattern**:
```sql
SELECT 
    fips.state,
    AVG(CAST(f.y17_M070 AS FLOAT)) as avg_conservation_enrollment,
    COUNT(o.observation_id) as total_observations
FROM farm_table f
JOIN FIPS_table fips USING (FIPS_code)
LEFT JOIN observation_table o USING (FIPS_code)
GROUP BY fips.state
ORDER BY avg_conservation_enrollment DESC;
```

**Analytical Value**: Demonstrates return on investment for conservation programs.

### Query 5: Data Warehouse Scale Validation

**Use Case**: Project requirement validation for minimum data scale.

**Business Question**: Does the data warehouse meet the 1+ million row requirement?

**Query Pattern**:
```sql
SELECT 'observation_table' as table_name, COUNT(*) as row_count FROM observation_table
UNION ALL
SELECT 'farm_table', COUNT(*) FROM farm_table
UNION ALL
SELECT 'FIPS_table', COUNT(*) FROM FIPS_table
UNION ALL
SELECT 'sampling_event_metadata_table', COUNT(*) FROM sampling_event_metadata_table
UNION ALL
SELECT 'taxonomy', COUNT(*) FROM taxonomy;
```

**Result**: Observation table contains ~3.4 million rows, exceeding project requirements.

---

## Scaling Considerations and Future Enhancements

### Current Architecture Limitations

**Temporal Scope**: 
- Agricultural census data updates only every 5 years
- eBird data limited to 2017 for this implementation
- No time-series analysis currently possible

**Species Coverage**:
- Only 17 manually selected species included
- Full eBird dataset contains thousands of species
- Expanding coverage would increase data volume by orders of magnitude

**Geographic Resolution**:
- County-level aggregation may obscure local patterns
- Finer geographic resolution would enable precision conservation

### Proposed Production Pipeline (Apache Airflow)

**Annual eBird Data Update DAG**:
```python
# Pseudocode structure
acquire_ebird_data >> 
quality_check_ebird >> 
stage_to_s3 >> 
load_to_redshift >> 
validate_data_quality
```

**Five-Year Agricultural Census Update DAG**:
```python
# Pseudocode structure
acquire_nass_data >> 
clean_and_transform >> 
stage_to_s3 >> 
update_farm_table >> 
validate_changes
```

**Interim Year Handling**:
For years between agricultural censuses, the pipeline would:
1. Load new eBird observations
2. Reference most recent agricultural census data
3. Flag records as "using prior census data"
4. Enable time-series analysis of bird populations with static agricultural context

### Future Enhancement Roadmap

**Phase 1: Temporal Expansion**
- Extend data collection to multiple years (2017-present)
- Implement time-series tables with proper partitioning
- Enable trend analysis and predictive modeling

**Phase 2: Real-Time Integration**
- Integrate eBird API for near-real-time observations
- Implement streaming ingestion (AWS Kinesis)
- Create dashboard for live observation tracking

**Phase 3: Advanced Analytics**
- Build machine learning models for population prediction
- Implement geospatial analysis capabilities (PostGIS extension)
- Create automated anomaly detection for population trends

**Phase 4: Expanded Coverage**
- Include all eBird species (not just grassland birds)
- Integrate additional environmental datasets (climate, land use change)
- Expand geographic scope to North America

---

## Data Dictionary

### Observations Table

| Field | Description |
|-------|-------------|
| observation_id | Unique identifier for each observation record (auto-generated) |
| common_name | Common (non-scientific) name of observed species |
| FIPS_code | Federal Information Processing Standard code for county |
| observation_count | Number of individuals observed ('X' if count uncertain) |
| observation_date | Date of eBird species observation |
| sampling_event_id | Unique identifier for eBird checklist |

### Farm Table

| Field | Description |
|-------|-------------|
| FIPS_code | Federal Information Processing Standard code for county |
| y17_M059 | Acres of Land in Farms as Percent of Land Area in Acres: 2017 |
| y17_M061 | Acres of Irrigated Land as Percent of Land in Farms Acreage: 2017 |
| y17_M063 | Acres of Total Cropland as Percent of Land Area in Acres: 2017 |
| y17_M066 | Acres of Harvested Cropland as Percent of Land in Farms Acreage: 2017 |
| y17_M068 | Acres of All Types of Pastureland as Percent of Land in Farms Acreage: 2017 |
| y17_M070 | Acres Enrolled in Conservation Reserve, Wetlands Reserve, Farmable Wetlands, or Conservation Reserve Enhancement Programs as Percent of Land in Farms Acreage: 2017 |
| y17_M078 | Acres of Cropland and Pastureland Treated with Animal Manure as Percent of Total Cropland Acreage: 2017 |
| y17_M079 | Acres Treated with Chemicals to Control Insects as Percent of Total Cropland Acreage: 2017 |
| y17_M080 | Acres Treated with Chemicals to Control Nematodes as Percent of Total Cropland Acreage: 2017 |
| y17_M081 | Acres of Crops Treated with Chemicals to Control Weeds, Grass, or Brush as Percent of Total Cropland Acreage: 2017 |
| y17_M082 | Acres of Crops Treated with Chemicals to Control Growth, Thin Fruit, Ripen, or Defoliate as Percent of Total Cropland Acreage: 2017 |
| y17_M083 | Acres Treated with Chemicals to Control Disease in Crops and Orchards as Percent of Total Cropland Acreage: 2017 |

### FIPS Table

| Field | Description |
|-------|-------------|
| FIPS_code | Federal Information Processing Standard code (primary geographic identifier) |
| county | County name associated with FIPS code |
| state | State name associated with FIPS code |

### Sampling Event Metadata Table

| Field | Description |
|-------|-------------|
| sampling_event_id | Unique identifier for eBird checklist/sampling event |
| locality | eBird "hotspot" location (park, trail, farm, forest, etc.) |
| latitude | Geographic coordinate (decimal degrees) |
| longitude | Geographic coordinate (decimal degrees) |
| observation_date | Date of observation via eBird |
| observer_id | Identifier of birdwatcher who logged sighting on eBird |
| duration_minutes | Duration of eBird sampling event (time spent observing) |
| effort_distance_km | Distance traveled during eBird sampling event |

### Taxonomy Table

| Field | Description |
|-------|-------------|
| common_name | Common name (non-scientific) of observed species |
| scientific_name | Scientific (Latin binomial) name of observed species |
| taxonomic_order | Biological classification order |

---

## Technical Stack

**Cloud Infrastructure**:
- AWS Redshift (data warehouse)
- AWS S3 (data lake staging)
- AWS IAM (access management)

**Programming Languages**:
- Python 3.x (ETL scripting)
- SQL (PostgreSQL/Redshift dialect)

**Python Libraries**:
- psycopg2 (PostgreSQL/Redshift connectivity)
- pandas (data manipulation)
- boto3 (AWS SDK for S3 operations)

**Data Sources**:
- eBird API (Cornell Lab of Ornithology)
- NASS.USDA.gov (Agricultural Census)

---

## Project Structure

```
├── NASS_data_acquisition.py      # USDA agricultural census data extraction
├── eBird_data_acquisition.py     # eBird API data retrieval and cleaning
├── create_tables.py               # Redshift schema creation script
├── etl.py                         # Main ETL orchestration script
├── sample_queries.ipynb           # Example queries and results
├── data_model.png                 # Visual representation of star schema
├── README.md                      # This file
└── data/                          # Local data directory (not in repo)
    ├── Farms.csv
    ├── FIPS.json
    └── merged_cleaned.csv
```

---

## Getting Started

### Prerequisites

1. AWS account with Redshift cluster provisioned
2. AWS IAM user with S3 and Redshift permissions
3. eBird API access credentials
4. Python 3.7+ with required libraries installed

### Setup Instructions

1. **Configure AWS credentials**:
   ```bash
   aws configure
   ```

2. **Run data acquisition scripts**:
   ```bash
   python NASS_data_acquisition.py
   python eBird_data_acquisition.py
   ```

3. **Upload data to S3**:
   ```bash
   aws s3 cp data/ s3://your-bucket-name/ --recursive
   ```

4. **Create database schema**:
   ```bash
   python create_tables.py
   ```

5. **Execute ETL pipeline**:
   ```bash
   python etl.py
   ```

6. **Validate data load**:
   Open `sample_queries.ipynb` and execute validation queries.

---

## Project Context

This data warehouse was developed as the capstone project for the Udacity Data Engineering Nanodegree. The project demonstrates proficiency in:

- Cloud data warehouse design and implementation
- ETL pipeline development with Python
- Star schema modeling for analytical workloads
- AWS services integration (S3, Redshift, IAM)
- Data quality assurance and validation
- SQL query optimization

The dataset produced by this project serves as the foundation for the companion analytical project: "Grassland Bird Population Analytics: Agricultural Impact Assessment" (Drexel University DSCI 521 Capstone).

---

## References and Acknowledgements

**Data Sources**:
- eBird - Cornell Lab of Ornithology: [eBird.org](https://ebird.org)
- USDA National Agricultural Statistics Service: [NASS.USDA.gov](https://www.nass.usda.gov/)

**Policy Context**:
- Growing Climate Solutions Act (2021) - U.S. legislation supporting sustainable agriculture

**Academic Context**:
- Udacity Data Engineering Nanodegree Program
- Drexel University DSCI 521 (companion analytics project)

---

## License

MIT License

Copyright (c) 2025 Mike Andersen

---

## Contact

For questions about this project or collaboration opportunities:

**Email**: mikeandersen622@gmail.com
**GitHub**: [Your GitHub Profile]  
**LinkedIn**: [Your LinkedIn Profile]

---

**Note**: This README documents the data engineering infrastructure. For statistical analysis and research findings based on this data warehouse, see the companion repository: "Grassland Bird Population Analytics: Agricultural Impact Assessment."
