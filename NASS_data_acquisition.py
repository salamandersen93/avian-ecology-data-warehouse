import pandas as pd
pd.set_option('display.max_columns', None) 
pd.set_option('max_colwidth', None)
pd.set_option('max_rows', None)

NASS_farm = pd.read_csv('NASS_Data/farms.csv')
NASS_dict = pd.read_csv('NASS_Data/variable_lookup.csv')
NASS_counties = pd.read_json('NASS_Data/fips_lookup.json') # 2 types of data source captured (json and csv)

# only interested in a few of these columns for this exercise
relevant_farm_codes = ['y17_M059_classRange', 'y17_M061_classRange', 
                       'y17_M063_classRange', 'y17_M066_classRange',
                       'y17_M068_classRange', 'y17_M070_classRange',
                       'y17_M078_classRange', 'y17_M079_classRange',
                       'y17_M080_classRange', 'y17_M081_classRange',
                       'y17_M082_classRange', 'y17_M083_classRange']

boolean_series = NASS_dict.MapID.isin(relevant_farm_codes)
filtered_NASS_dict = NASS_dict[boolean_series]

# can remove irrelevant headers from NASS_farm
final_NASS_farm_columns = ['FIPS', 'y17_M059_classRange', 'y17_M061_classRange', 
                       'y17_M063_classRange', 'y17_M066_classRange',
                       'y17_M068_classRange', 'y17_M070_classRange',
                       'y17_M078_classRange', 'y17_M079_classRange',
                       'y17_M080_classRange', 'y17_M081_classRange',
                       'y17_M082_classRange', 'y17_M083_classRange']

NASS_farm_filtered = NASS_farm.drop(columns=[col for col in NASS_farm if col not in final_NASS_farm_columns])
#NASS_farm_filtered = NASS_farm_filtered.rename(columns = lambda x : str(x)[:-13])
NASS_farm_filtered = NASS_farm_filtered.rename(columns={NASS_farm_filtered.columns[0]: 'FIPS'})

NASS_farm_filtered.to_csv('processed_input_data/NASS_farm.csv')
NASS_counties.to_csv('processed_input_data/FIPS_lookup.csv')
filtered_NASS_dict.to_csv('processed_input_data/NASS_header_lookup.csv')