import pandas as pd
from os import listdir
from os.path import isfile, join
import datetime as dt
pd.set_option('display.max_columns', None) 
pd.set_option('max_colwidth', 100)
pd.set_option("max_rows", None)

eBirdFiles = [f for f in listdir('eBird_Data/') if isfile(join('eBird_Data/', f))]
eBirdFiles = ['eBird_Data/' + e for e in eBirdFiles]

eBird_df = pd.read_csv(eBirdFiles[0], delimiter='\t')
  
for i in range(1,len(eBirdFiles)):
    if eBirdFiles[i].endswith('.csv'):
        #print('starting extraction:' + eBirdFiles[i])
        data = pd.read_csv(eBirdFiles[i], delimiter='\t', low_memory=False)
        df = pd.DataFrame(data)
        eBird_df = eBird_df.append(df)
        #print('finished appending:' + eBirdFiles[i])

# data type conversions for date field OBSERVATION DATE
eBird_df['OBSERVATION DATE'] =  pd.to_datetime(eBird_df['OBSERVATION DATE'], format='%Y-%m-%d')

# dropping irrelevant columns
eBird_df = eBird_df.drop(['GLOBAL UNIQUE IDENTIFIER', 'LAST EDITED DATE','CATEGORY', 'SUBSPECIES COMMON NAME',
               'SUBSPECIES SCIENTIFIC NAME', 'BREEDING CODE',
               'BREEDING CATEGORY', 'BEHAVIOR CODE', 'AGE/SEX',
               'COUNTRY CODE', 'STATE CODE', 'COUNTY CODE', 'IBA CODE',
               'BCR CODE', 'USFWS CODE', 'ATLAS BLOCK', 'LOCALITY ID',
               'LOCALITY TYPE', 'TIME OBSERVATIONS STARTED', 'PROTOCOL TYPE',
               'PROTOCOL CODE', 'PROJECT CODE', 'EFFORT AREA HA',
               'NUMBER OBSERVERS', 'ALL SPECIES REPORTED', 'GROUP IDENTIFIER',
               'HAS MEDIA', 'APPROVED', 'REVIEWED', 'REASON', 'TRIP COMMENTS',
               'SPECIES COMMENTS', 'Unnamed: 47'], axis=1)

# quality check 1: ensuring species in table are the ones required for the research question
species_in_df = eBird_df['COMMON NAME'].unique()


acceptable_species = ['Northern Bobwhite' 'Horned Lark' 'Upland Sandpiper'
 'Grasshopper Sparrow' "Baird's Sparrow" 'Long-billed Curlew'
 'American Pipit' 'Killdeer' "Sprague's Pipit" 'Lapland Longspur'
 'Vesper Sparrow' 'House Sparrow' 'Red-winged Blackbird' 'Bobolink'
 'Snow Bunting' 'Song Sparrow' 'Eastern Meadowlark']

try:
    acceptable_species == species_in_df
except:
    print("Error - invalid species in data.")
    
# quality check # 2: ensuring dates are only present for the dates in scope

min_date = min(eBird_df['OBSERVATION DATE'])
max_date = max(eBird_df['OBSERVATION DATE'])

try:
    min_date.year > 2016
    max_date.year < 2018
except:
    raise ValueError("Data must only contain data for year 2017.")

eBird_df.columns = eBird_df.columns.str.replace(' ', '_')
eBird_df = eBird_df.replace('"','', regex=True)
eBird_df.to_csv('processed_input_data/merged_all_species_eBird.csv', sep='\t', index=False)