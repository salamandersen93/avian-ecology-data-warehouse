<h1> Udacity Data Engineering Capstone Project: Data Warehouse </h1>

<h2> Farmland and Grassland Avian Ecology Data Warehouse Implementation in AWS Redshift, PostGreSQL, and Python </h2>

<h3> Background </h3>
<p>The objective of this project is to compile a dataset comprised of agricultural survey data and avian sighting records for species which rely heavily on grassland and farmland ecosystems for survival. The scope of this dataset is for the year 2017 within the United States. Species included in this dataset were manually selected based on literature searches for songbirds which rely on these habitats for food, shelter, and overall survival.</p>
  
<h3> Data Selection </h3>

<h4> NASS/NASS Census of Agriculture Data</h4>
<p>2017 USDA/NASS Census of Agriculture Data was acquired from NASS.USDA.gov in an Excel format. Two tables were extracted from this Excel file. The first describes various parameters of land use and chemical use on farms, and was extracted locally as a .csv file. The second was a table containing FIPS data for each county surveyed, and was extracted locally as a .json file to satisfy project requirement of two types of data sources for ingestion.

The farms table contains metadata including Acres of Land in Farms, Acres of Irrigated Land as Percent of Land in Farms, Acres of Total Cropland as Percent of Land in Farms, Acres of Harvested Cropland as Percent of Land in Farms, Acres of Pastureland as Percent of Land in Farms, Acres Enrolled in Conservation Reserve, Acres Treated with Chemicals to Control Insects, Acres Treated with Chemicals to Control Nematodes, Acres Treated with Chemicals to Contorl Weeds, Acres Treated with Chemicals to Control Growth, Acres Treated with Chemicals to Control Disease. Each of these was encoded with a value provided by NASS in the foramt y17_Mxxx. Mapping is described in the data dicitonary.
</p>

<h4> eBird Data</h4>
<p>eBird data was acquired by request at https://ebird.org/science/use-ebird-data. Requests were made for 17 species of songbird, with parameters of Country = 'United States' and date between Jan 2017 and Dec 2017. Data was acquired for the below species:

'Northern Bobwhite', 'Horned Lark', 'Upland Sandpiper', 'Grasshopper Sparrow' "Baird's Sparrow" 'Long-billed Curlew', 'American Pipit' 'Killdeer' "Sprague's Pipit" 'Lapland Longspur', 'Vesper Sparrow', 'House Sparrow', 'Red-winged Blackbird', 'Bobolink', 'Snow Bunting', 'Song Sparrow', 'Eastern Meadowlark'

Quality checks were run on the data to ensure that the species list in the raw dataset was curated into a proper controlled vocabulary, and that the dates were within the designated dates for the project. These quality checks can be found in the eBird_data_acquisition.py script.</p>

<h4> Data Model </h4>
An image of the data model is provided in this repository. It follows the format below:

Fact Table: Observation_table
- observation_id PRIMARY KEY INT
- common_name TEXT
- FIPS_code INT
- observation_count TEXT
- sampling_event_id TEXT
note about observation_count - while in an analysis this would be ideal as an integer,
there are cases where the reporter of the sighting could not define ane exact count of a species
due to a large flock or uncertainty if the same bird was seen multiple times. These are reported as 'X'.
Rather than attempt to impute during this dataset construction, I would leave this imputation up to
the data scientist or analyst executing the downstream analytics in this case.

Dimension Table: FIPS_table
- FIPS_code PRIMARY KEY INT
- county TEXT
- state TEXT

Dimension Table: Farm_table
-FIPS_code PRIMARY KEY INT
-y17_M059 TEXT
-y17_M061 TEXT
-y17_M063 TEXT
-y17_M066 TEXT
-y17_M068 TEXT
-y17_M070 TEXT
-y17_M078 TEXT
-y17_M079 TEXT
-y17_M080 TEXT
-y17_M081 TEXT
-y17_M082 TEXT
note - variable meaning described in data dictionary, too long for column headers

Dimension Table: Sampling_event_metadata_table
sampling_event_id TEXT PRIMARY KEY
locality TEXT
latitude FLOAT
longitude FLOAT
observation_date TEXT
observer_id TEXT
duration_minutes INT
effort_distance_km INT

The model was constructed by executing the following steps:
1. NASS/USDA data acquistion script execution to output two files: Farms.csv and FIPS.json (input for ETL - two data source types).
2. A .csv file for each of the 17 species listed above. An eBird data acquisition script was run to append, clean, and output a merged_cleaned.csv file.
3. All three of the output files were inserted into an S3 bucket, which is the input source for the ETL project dataset.
4. A create_tables script was run to execute SQL queries in PostgreSQL to create the tables in Redshift.
5. The ETL.py script was run to execute staging table creation, copying into staging tables, and execution of data insert into the Redshift tables.

<h4> Use-cases and Sample Queries </h4>

<p>This data preparation exercise resulted in a table which could be used as either an analytics table or an application back-end. This is a static dataset from a temporal perspective since the Agricultural Census only occurs every 5 years. In theory this could be curated every 5 years to assess change.

With respect to use-cases, this dataset could be used by ornithology researchers, policymakers, or farmers to understand the potential impact of farmland acreage, chemical use, and geography on avian populations and ecosystem dynamics. This past June, the United States passed the <b> Growing Climate Solutions Act </b>, which support farmers in implementing sustainable and environmentally-friendly practices, ultimately benefiting avian populations rebound from their current status. This area of sustainable agriculture is a topic of interest and this dataset could serve as a conceptual model to build upon with future census data and eBird checklists. Some sample queries have been executed in Redshift and images were pasted into a Jupyter Notebook report attached in this repository.
  
To summarize scenarios which are outlined in the query report (sample_queries.pynb) attached to this repository:
  <b> Query 1 Justification: </b> A reasearcher wants to get the count of species observation reports (not SUM) grouped by county and state by species.
  <b> Query 2 Justification: </b> An ornithologist wants to track their labs sightings by seeing a list of all species observed by observer_id
  <b> Query 3 Justification: </b> A policymaker wants to understand how Acreage of Farmland, Cropland, and Chemical usage on farmland impacts bird populations by county and state. This could be leveraged to strengthen positions of sustainable agriculture and conservation.
  <b> Query 4 Justification: </b> A policymaker or researcher wants to get an idea of the amount of farmland which is part of conservation efforts or sustainable farming efforts in a given county or state to inform policy decisions or research hypotheses on species population dynamics.
  <b> Query 5 Justification: </b> Getting counts on all 5 tables. Project requirement: at least 1 million rows. Rows in fact table: 3.4 million.

<h4> Data Updates, Future Scenarios, and Pipelines </h4>

Agricultural census data is only updated every 5 years, while eBird data is constantly available. There is an eBird API which could be leveraged to access real-time data, but there are limitations to amount of data which can be extracted. If an agreement was reached with Cornell Lab of Ornithology, the export files could be provided on a yearly basis to feed a data pipeline. I would propose the following pipeline for a productionized version of this dataset, leveraging Apache Airflow:
1. Acquire all 17 species eBird files on a yearly basis and run the eBird_data_acquisition.py to clean, append, and quality check the data.
2. Acquire NASS/USDA Agricultural Census summary data every 5 years as it becomes available and run the NASS_data_acquisition.py to clean and sort the data.
3. Modify ETL to handle cases of interim years where Agricultural Summary data is not available, in order to handle only eBird data.

If the data size was increased by 100x (as proposed in project write-up scenario): leverage Spark instead of Pandas for data acquisition and writing to Redshift.

If the pipelines were run on a daily basis at 7AM (as proposed in the project write-up scenario): This is not relevant for this scenario, however if eBird API data were theoretically to be acquired daily at 7AM, an Airflow DAG could be set up to run the API calls separately and feed the data into the eBird_data_acquisition script.

If the database needed to be acessed by 100+ people (as proposed in project write-up scenario): Launch on RA3.16xlarge, RA3.4xlarge, or RA3.xlplus nodes in Redshift

<h2> Data Dictionary </h2>

<h3> Observations </h3
observation_id:  automatically incremented primary key value <br>
common_name common: (non-scientific) name of species observed <br>
FIPS_code: FIPS code (geopgraphic information data) <br>
observation_date: date of eBird species observation <br>
sampling_event_id: unique identifier for sampling event (aka eBird checklist - can include multiple spcies, at a given location and date/time) <br>
  
<h3> Farms </h3>
FIPS_code: FIPS code (geographic information data)<br>
y17_M059:	Acres of Land in Farms as Percent of Land Area in Acres: 2017<br>
y17_M061:	Acres of Irrigated Land as Percent of Land in Farms Acreage: 2017<br>
y17_M063:	Acres of Total Cropland as Percent of Land Area in Acres: 2017<br>
y17_M066:	Acres of Harvested Cropland as Percent of Land in Farms Acreage: 2017<br>
y17_M068:	Acres of All Types of Pastureland as Percent of Land in Farms Acreage: 2017<br>
y17_M070:	Acres Enrolled in the Conservation Reserve, Wetlands Reserve, Farmable Wetlands, or Conservation Reserve Enhancement Programs as Percent of Land in Farms Acreage: 2017<br>
y17_M078:	Acres of Cropland and Pastureland Treated with Animal Manure as Percent of Total Cropland Acreage: 2017<br>
y17_M079:	Acres Treated with Chemicals to Control Insects as Percent of Total Cropland Acreage: 2017<br>
y17_M080:	Acres Treated with Chemicals to Control Nematodes as Percent of Total Cropland Acreage: 2017<br>
y17_M081:	Acres of Crops Treated with Chemicals to Control Weeds, Grass, or Brush as Percent of Total Cropland Acreage: 2017<br>
y17_M082:	Acres of Crops Treated with Chemicals to Control Growth, Thin Fruit, Ripen, or Defoliate as Percent of Total Cropland Acreage: 2017<br>
y17_M083:	Acres Treated with Chemicals to Control Disease in Crops and Orchards as Percent of Total Cropland Acreage: 2017<br>

<h3> FIPS </h3>
FIPS_code: FIPS code (geographic information data)<br>
county: county associated with FIPS code<br>
state: state associated with FIPS code<br>
  
<h3> Sampling Event Metadata </h3>
sampling_event_id: value from eBird, unique identifier for checklist/sampling event
locality: value from eBird, aka a 'hotspot', is a location defined in eBird. can be a park, hiking trail, farm, forest, roadside area, beach, etc.
latitude: latitude
longitude: longitude
observation_date: date of observation via eBird
observer_id: identifier of the birdwatcher who logged the sighting on eBird
duration_minutes: duration of the eBird sampling event (hours spent by the birdwatcher/observer on that sampling event)
effort_distance_km: distance traveled during the eBird sampling event by the birdwatcher/observer
  
<h3> References and Acknowledgements </h3>
  eBird - cornell lab of ornithology: eBird.org
  NASS/USDA: NASS.usda.gov
  
