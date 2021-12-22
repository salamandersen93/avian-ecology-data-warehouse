import configparser
import psycopg2

config = configparser.ConfigParser()
config.read('dwh.cfg')

observation_table_drop = "DROP TABLE IF EXISTS observation_table" # fact table
taxonomy_table_drop = "DROP TABLE IF EXISTS taxonomy_table"
FIPS_table_drop = "DROP TABLE IF EXISTS FIPS_table"
farm_data_table_drop = "DROP TABLE IF EXISTS farm_data_table"
sampling_event_table_drop = "DROP TABLE IF EXISTS sampling_event_metadata_table"
staging_eBird_table_drop = "DROP TABLE IF EXISTS staging_eBird_table"
staging_farms_table_drop = "DROP TABLE IF EXISTS staging_farms_table"
staging_fips_table_drop = "DROP TABLE IF EXISTS staging_FIPS_table"

# staging FIPS
staging_fips_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_FIPS_table (
FIPSTEXT int, CountyName text, Entity text, StateName text
)
""")

# staging eBird
staging_eBird_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_eBird_table (
TAXONOMIC_ORDER text, COMMON_NAME text, SCIENTIFIC_NAME text, OBSERVATION_COUNT text, COUNTRY text, STATE text, COUNTY text,
LOCALITY text, LATITUDE float, LONGITUDE float, OBSERVATION_DATE text, OBSERVER_ID text, SAMPLING_EVENT_IDENTIFIER text,
DURATION_MINUTES FLOAT, EFFORT_DISTANCE_KM FLOAT
)
""")

#staging farms
staging_farms_table_create = ("""
CREATE TABLE IF NOT EXISTS staging_farms_table (
FIPS INT, y17_M059_valueNumeric float, y17_M061_valueNumeric float,
y17_M063_valueNumeric float, y17_M066_valueNumeric float,
y17_M068_valueNumeric float,
y17_M070_valueNumeric float, y17_M078_valueNumeric float,
y17_M079_valueNumeric float, y17_M080_valueNumeric float,
y17_M081_valueNumeric float, y17_M082_valueNumeric float,
y17_M083_valueNumeric float
)
""")

#fact table - observations
observation_table_create = ("""
CREATE TABLE IF NOT EXISTS observation_table (
observation_id INTEGER IDENTITY(1,1) PRIMARY KEY NOT NULL,
common_name text, FIPS_code int, observation_count text, sampling_event_id text
)
""")


# dimension table - farm metadata
farm_data_table_create = ("""
CREATE TABLE IF NOT EXISTS farm_data_table (
FIPS_code text PRIMARY KEY, y17_M059 int, y17_M061 int, y17_M063 int,
y17_M066 int, y17_M068 int, y17_M070 int, y17_M078 int, y17_M079 int,
y17_M080 int, y17_M081 int, y17_M082 int, y17_M083 int
)
""")

# dimension table - taxonomy metadata
taxonomy_table_create = ("""
CREATE TABLE IF NOT EXISTS taxonomy_table (
common_name text PRIMARY KEY, scientific_name text, taxonomic_order text
)
""")

# dimension table - FIPS lookup
FIPS_table_create = ("""
CREATE TABLE IF NOT EXISTS fips_table (
FIPS_code int PRIMARY KEY, county text, state text
)
""")

# dimension table - sampling event metadata
sampling_event_metadata = ("""
CREATE TABLE IF NOT EXISTS sampling_event_metadata_table (
sampling_event_id text PRIMARY KEY, locality text, latitude float, longitude float, observation_date text,
observer_id text, duration_minutes int, effort_distance_km int
)
""")

# STAGING TABLES

staging_eBird_copy = ("""
    copy staging_eBird_table from {}
    iam_role {}
    format as csv
    delimiter '\\t'
    ignoreheader 1
    emptyasnull
    blanksasnull
    truncatecolumns;
""").format(config['S3']['EBIRD_DATA'],config['IAM_ROLE']['ARN'])

staging_farms_copy = ("""   
    copy staging_farms_table from {}
    iam_role {}
    format as csv
    delimiter ','
    ignoreheader 1
    emptyasnull
    blanksasnull
    truncatecolumns
    fillrecord;
""").format(config['S3']['FARMS_DATA'],config['IAM_ROLE']['ARN'])

staging_FIPS_copy = ("""   
    copy staging_FIPS_table from {}
    iam_role {}
    format as csv
    delimiter ','
    ignoreheader 1
    emptyasnull
    blanksasnull
    truncatecolumns;
""").format(config['S3']['FIPS_DATA'],config['IAM_ROLE']['ARN'])

# copying from redshift to s3  -- note: this is post-project
unload_redshift = ("""
unload ('select * from observation_table') 
to 's3://capstone-project-ebird-nass/unload/' iam_role 'arn:aws:iam::166807100329:role/myRedshiftRole'
parallel off
header
delimiter as ','
CSV 
""")

# FINAL TABLES
observation_table_insert = ("""INSERT INTO observation_table (
common_name, FIPS_code, observation_count, sampling_event_id)
SELECT e.COMMON_NAME, f.FIPSTEXT, e.OBSERVATION_COUNT, e.SAMPLING_EVENT_IDENTIFIER
FROM staging_eBird_table e
JOIN staging_FIPS_table f on (e.COUNTY = f.CountyName) AND (e.STATE = f.StateName)
WHERE e.SAMPLING_EVENT_IDENTIFIER IS NOT NULL
""")

farm_data_table_insert = ("""INSERT INTO farm_data_table (
FIPS_code, y17_M059, Y17_M061, y17_M063, y17_M066,
y17_M068,
y17_M070, y17_M078,
y17_M079, y17_M080,
y17_M081, y17_M082,
y17_M083)
SELECT 
FIPS, y17_M059_valueNumeric, y17_M061_valueNumeric,
y17_M063_valueNumeric, y17_M066_valueNumeric,
y17_M068_valueNumeric,
y17_M070_valueNumeric, y17_M078_valueNumeric,
y17_M079_valueNumeric, y17_M080_valueNumeric,
y17_M081_valueNumeric, y17_M082_valueNumeric,
y17_M083_valueNumeric
FROM staging_farms_table
""")

sampling_event_metadata_table_insert = ("""INSERT INTO sampling_event_metadata_table (
sampling_event_id, locality, latitude, longitude, observation_date,
observer_id, duration_minutes, effort_distance_km)
SELECT 
SAMPLING_EVENT_IDENTIFIER, LOCALITY, LATITUDE, LONGITUDE,
OBSERVATION_DATE, OBSERVER_ID, DURATION_MINUTES, EFFORT_DISTANCE_KM
FROM staging_eBird_table
WHERE SAMPLING_EVENT_IDENTIFIER IS NOT NULL
""")

FIPS_table_insert= ("""INSERT INTO fips_table (
FIPS_code, county, state)
SELECT
FIPSTEXT, CountyName, StateName
FROM staging_FIPS_table
""")

taxonomy_table_insert = ("""INSERT INTO taxonomy_table (
common_name, scientific_name, taxonomic_order)
SELECT DISTINCT
(COMMON_NAME), SCIENTIFIC_NAME, TAXONOMIC_ORDER
FROM staging_eBird_table
""")

create_table_queries = [staging_fips_table_create, staging_eBird_table_create, staging_farms_table_create,
                       observation_table_create, farm_data_table_create, taxonomy_table_create,
                       FIPS_table_create, sampling_event_metadata]
drop_table_queries = [staging_eBird_table_drop, staging_farms_table_drop, staging_fips_table_drop, observation_table_drop, 
                      taxonomy_table_drop, FIPS_table_drop, farm_data_table_drop, sampling_event_table_drop]
copy_table_queries = [staging_eBird_copy, staging_farms_copy, staging_FIPS_copy]
insert_table_queries = [observation_table_insert, farm_data_table_insert, sampling_event_metadata_table_insert,
                       FIPS_table_insert, taxonomy_table_insert]
