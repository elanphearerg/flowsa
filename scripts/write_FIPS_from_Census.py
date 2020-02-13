import pandas as pd
from flowsa.common import datapath

#2017 State, County, Minor Civil Division, and Incorporated Place FIPS Codes

url = "https://www2.census.gov/programs-surveys/popest/geographies/2017/all-geocodes-v2017.xlsx"

#Read directly into a pandas df,
raw_df = pd.read_excel(url)

#skip the first few rows
FIPS_df = pd.DataFrame(raw_df.loc[4:]).reindex()
#Assign the column titles
FIPS_df.columns = raw_df.loc[3,]

original_cols = FIPS_df.columns

#Create a dictionary of geographic levels
geocode_levels = {"010":"Country",
                  "040":"State",
                  "050":"County"}
level_codes = geocode_levels.keys()
#filter df for records with the levels of interest
FIPS_df = FIPS_df[FIPS_df["Summary Level"].isin(level_codes)]

#split df by level to return a list of dfs
#use a list comprehension to split it out
FIPS_bylevel = [pd.DataFrame(y) for x,y in FIPS_df.groupby("Summary Level", as_index=False)]

#Assume df order in list is in geolevels keys order

state_and_county_fields = {"Country":["State Code (FIPS)"], #country does not have its own field
                           "State":["State Code (FIPS)"],
                           "County":["State Code (FIPS)","County Code (FIPS)"]}

name_field = "Area Name (including legal/statistical area description)"

new_dfs = {}
for df in FIPS_bylevel:
    df = df.reset_index(drop=True)
    level = geocode_levels[df.loc[0,"Summary Level"]]
    print(level)
    new_df = df[original_cols]
    new_df = new_df.rename(columns={name_field:level})
    fields_to_keep = [str(x) for x in state_and_county_fields[level]]
    fields_to_keep.append(level)
    print(fields_to_keep)
    new_df = new_df[fields_to_keep]
    #Now left merge each with the main df to take on the columns with level names but not removing existing records
    new_dfs[level] = new_df


#New merge the new dfs to add the info
#FIPS_df_new = FIPS_df
for k,v in new_dfs.items():
    fields_to_merge = [str(x) for x in state_and_county_fields[k]]
    #FIPS_df_new = pd.merge(FIPS_df_new,v,on=fields_to_merge,how="left")
    FIPS_df = pd.merge(FIPS_df,v,on=fields_to_merge,how="left")

#combine state and county codes
FIPS_df['FIPS'] = FIPS_df[state_and_county_fields["County"][0]] + FIPS_df[state_and_county_fields["County"][1]]

fields_to_keep = ["State","County","FIPS"]
FIPS_df = FIPS_df[fields_to_keep]

FIPS_df.to_csv(datapath+"FIPS.csv",index=False)


