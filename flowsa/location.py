# location.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8
"""
Functions related to accessing and modifying location codes
"""

import pandas as pd
import numpy as np
import pycountry
import urllib.error
from flowsa.settings import datapath, log
from flowsa.common import clean_str_and_capitalize


US_FIPS = "00000"

fips_number_key = {"national": 0,
                   "state": 2,
                   "county": 5}


def read_stored_FIPS(year='2015'):
    """
    Read fips based on year specified, year defaults to 2015
    :param year: str, '2010', '2013', or '2015', default year is 2015
        because most recent year of FIPS available
    :return: df, FIPS for specified year
    """

    FIPS_df = pd.read_csv(datapath + "FIPS_Crosswalk.csv", header=0, dtype=str)
    # subset columns by specified year
    df = FIPS_df[["State", "FIPS_" + year, "County_" + year]]
    # rename columns to drop data year
    df.columns = ['State', 'FIPS', 'County']
    # sort df
    df = df.sort_values(['FIPS']).reset_index(drop=True)

    return df


def getFIPS(state=None, county=None, year='2015'):
    """
    Pass a state or state and county name to get the FIPS.

    :param state: str. A US State Name or Puerto Rico, any case accepted
    :param county: str. A US county
    :param year: str. '2010', '2013', '2015', default year is 2015
    :return: str. A five digit FIPS code
    """
    FIPS_df = read_stored_FIPS(year)

    # default code
    code = None

    if county is None:
        if state is not None:
            state = clean_str_and_capitalize(state)
            code = FIPS_df.loc[(FIPS_df["State"] == state)
                               & (FIPS_df["County"].isna()), "FIPS"]
        else:
            log.error("To get state FIPS, state name must be passed in "
                      "'state' param")
    else:
        if state is None:
            log.error("To get county FIPS, state name must be passed in "
                      "'state' param")
        else:
            state = clean_str_and_capitalize(state)
            county = clean_str_and_capitalize(county)
            code = FIPS_df.loc[(FIPS_df["State"] == state)
                               & (FIPS_df["County"] == county), "FIPS"]
    if code.empty:
        log.error("No FIPS code found")
    else:
        code = code.values[0]

    return code


def apply_county_FIPS(df, year='2015', source_state_abbrev=True):
    """
    Applies FIPS codes by county to dataframe containing columns with State
    and County
    :param df: dataframe must contain columns with 'State' and 'County', but
        not 'Location'
    :param year: str, FIPS year, defaults to 2015
    :param source_state_abbrev: True or False, the state column uses
        abbreviations
    :return dataframe with new column 'FIPS', blanks not removed
    """
    # If using 2 letter abbrevations, map to state names
    if source_state_abbrev:
        df['State'] = df['State'].map(abbrev_us_state)
    df['State'] = df.apply(lambda x: clean_str_and_capitalize(x.State),
                           axis=1)
    df['County'] = df.apply(lambda x: clean_str_and_capitalize(x.County),
                            axis=1)

    # Pull and merge FIPS on state and county
    mapping_FIPS = get_county_FIPS(year)
    df = df.merge(mapping_FIPS, how='left')

    # Where no county match occurs, assign state FIPS instead
    mapping_FIPS = get_state_FIPS()
    mapping_FIPS.drop(columns=['County'], inplace=True)
    df = df.merge(mapping_FIPS, left_on='State', right_on='State', how='left')
    df['Location'] = df['FIPS_x'].where(df['FIPS_x'].notnull(), df['FIPS_y'])
    df.drop(columns=['FIPS_x', 'FIPS_y'], inplace=True)

    return df


def update_geoscale(df, to_scale):
    """
    Updates df['Location'] based on specified to_scale
    :param df: df, requires Location column
    :param to_scale: str, target geoscale
    :return: df, with 5 digit fips
    """
    # code for when the "Location" is a FIPS based system
    if to_scale == 'state':
        df.loc[:, 'Location'] = df['Location'].apply(lambda x: str(x[0:2]))
        # pad zeros
        df.loc[:, 'Location'] = df['Location'].apply(lambda x:
                                                     x.ljust(3 + len(x), '0')
                                                     if len(x) < 5 else x)
    elif to_scale == 'national':
        df.loc[:, 'Location'] = US_FIPS
    return df

def get_state_FIPS(year='2015'):
    """
    Filters FIPS df for state codes only
    :param year: str, year of FIPS, defaults to 2015
    :return: FIPS df with only state level records
    """

    fips = read_stored_FIPS(year)
    fips = fips.drop_duplicates(subset='State')
    fips = fips[fips['State'].notnull()]
    return fips


def get_county_FIPS(year='2015'):
    """
    Filters FIPS df for county codes only
    :param year: str, year of FIPS, defaults to 2015
    :return: FIPS df with only county level records
    """
    fips = read_stored_FIPS(year)
    fips = fips.drop_duplicates(subset='FIPS')
    fips = fips[fips['County'].notnull()]
    return fips


def get_all_state_FIPS_2(year='2015'):
    """
    Gets a subset of all FIPS 2 digit codes for states
    :param year: str, year of FIPS, defaults to 2015
    :return: df with 'State' and 'FIPS_2' cols
    """

    state_fips = get_state_FIPS(year)
    state_fips.loc[:, 'FIPS_2'] = state_fips['FIPS'].apply(lambda x: x[0:2])
    state_fips = state_fips[['State', 'FIPS_2']]
    return state_fips


# From https://gist.github.com/rogerallen/1583593
# removed non US states, PR, MP, VI
us_state_abbrev = {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
}

# thank you to @kinghelix and @trevormarburger for this idea
abbrev_us_state = {abbr: state for state, abbr in us_state_abbrev.items()}


def get_region_and_division_codes():
    """
    Load the Census Regions csv
    :return: pandas df of census regions
    """
    df = pd.read_csv(f"{datapath}Census_Regions_and_Divisions.csv",
                     dtype="str")
    return df


def assign_census_regions(df_load):
    """
    Assign census regions as a LocationSystem
    :param df_load: fba or fbs
    :return: df with census regions as LocationSystem
    """
    # load census codes
    census_codes_load = get_region_and_division_codes()
    census_codes = census_codes_load[
        census_codes_load['LocationSystem'] == 'Census_Region']

    # merge df with census codes
    df = df_load.merge(census_codes[['Name', 'Region']],
                       left_on=['Location'], right_on=['Name'], how='left')
    # replace Location value
    df['Location'] = np.where(~df['Region'].isnull(),
                              df['Region'], df['Location'])

    # modify LocationSystem
    # merge df with census codes
    df = df.merge(census_codes[['Region', 'LocationSystem']],
                  left_on=['Region'], right_on=['Region'], how='left')
    # replace Location value
    df['LocationSystem_x'] = np.where(~df['LocationSystem_y'].isnull(),
                                      df['LocationSystem_y'],
                                      df['LocationSystem_x'])

    # drop census columns
    df = df.drop(columns=['Name', 'Region', 'LocationSystem_y'])
    df = df.rename(columns={'LocationSystem_x': 'LocationSystem'})

    return df


def call_country_code(country):
    """
    use pycountry to call on 3 digit iso country code
    :param country: str, name of country
    :return: str, ISO code
    """
    return pycountry.countries.get(name=country).numeric


def merge_urb_cnty_pct(df):
    """
    Merge a %-urban-population column onto a df with existing LocationSystem 
    and Location columns, where the latter contains FIPS county codes. 
    Note: post-merge 0% values are valid and not equal to nan's.
    :param df: pandas dataframe
    :return: pandas dataframe with new column of urban population percentages
    """
    if any(i is None for i in df['LocationSystem']):
        print('LocationSystem column contains one or more None values')
        return None
    elif any('FIPS' not in i for i in set(df['LocationSystem'])):
        print('LocationSystem column contains non-FIPS labels')
        return None  # check derived from flowsa FBA format specs
    elif any(df['Location'].str.len() != 5):
        print('One or more FIPS codes are not expressed as 5-digits; review data')
        return None
    
    # expects uniform LocationSystem values (i.e., single FIPS_yyyy year code)
    years = extract_fips_years(df['LocationSystem'])
    try: 
        year = years.item()  # extract year element from length-1 array
    except ValueError:
        print('LocationSystem contains >1 "FIPS_yyyy" code')
        return None
    
    years_xwalk = extract_fips_years(  # from xwalk headers
        pd.read_csv(datapath + 'FIPS_Crosswalk.csv', nrows=0).columns)

    if not {year} <= set(years_xwalk):  # compare data years as sets
        print('LocationSystem incompatible with FIPS_Crosswalk.csv')
        return None

    pct_urb = get_census_cnty_tbl(year)
    df = pd.merge(df, pct_urb, how='left', on='Location')

    # find unmerged nan pct_pop_urb values
    pct_na = sum(df['pct_pop_urb'].isna())
    if pct_na != 0: 
        print(f'WARNING {pct_na} FIPS codes did not merge successfully.\n'
              'In pct_pop_urb, the resulting "nan" values are not equal to 0%.')
    return df


def extract_fips_years(pd_series):
    """
    Extract np.array of unique year ints from pd.series of 'FIPS_yyyy' strings
    :param series: pandas series
    :return: numpy array of year integers
    """
    years = (pd_series.str.extract(r'FIPS_(\d{4})')
             .dropna().squeeze().unique().astype(int))
    return years


def get_census_cnty_tbl(year):
    """
    Read table of Census county-equivalent-level (FIPS) urban and rural
    population counts (detail in esupy/data_census/README.md), and 
    calculate each area's urban population percentage.
    :param year: integer data year from a LocationSystem column (FIPS_yyyy)
    """
    cnty_url = 'https://www2.census.gov/geo/docs/reference/ua/PctUrbanRural_County.txt'
    
    # screen for data availability; limited to 2010-2019 for now
    if (year - (year%10)) != 2010:
        print('County-level data year not yet available')
        return None
    
    try:
        df = pd.read_csv(cnty_url, encoding='iso-8859-1',
                          usecols = ['STATE','COUNTY','POP_COU','POP_URBAN'])
    except urllib.error.HTTPError:
        print(f'File unavailable, check Census domain status: \n{cnty_url}')
        return None
    
    df['STATE'] = df['STATE'].apply(lambda x: '{0:0>2}'.format(x))
    df['COUNTY'] = df['COUNTY'].apply(lambda x: '{0:0>3}'.format(x))
    df['FIPS_2010'] = df['STATE'] + df['COUNTY']  # 5-digit county codes
    # Note: {total = urban + rural} population, for all FIPS areas
    df['pct_pop_urb'] = df['POP_URBAN'] / df['POP_COU']    
    
    df = shift_census_cnty_tbl(df, year)  # adjust to match data year
    return df


def shift_census_cnty_tbl(df, year):
    """
    Transform a table of Census pct_pop_urb values (by FIPS area code) 
    to a specified data year via FIPS_Crosswalk.csv.                                  
    FIPS area splits are assumed to inherit their parent's pct_pop_urb value.
    FIPS area merges assume the child inherits the sum of its parents' 
    total and urban population values (both assumed constant over time), 
    requiring a recalculation of pct_pop_urb.
    :param df: pandas df from get_census_cnty_tbl
    :param year: integer data year from a LocationSystem column (FIPS_yyyy)
    """
    decade = (year - year%10)  # previous decennial census year
    if year == decade: # if already a decennial census year
        df['Location'] = df[f'FIPS_{decade}']
        df = df[['Location','pct_pop_urb']]  # keep only necessary cols
        return df
    # splits identified by duplicated 'FIPS_{decade}' codes (A-->B, A-->C)
        # i.e., join by ['FIPS_{decade}'] field ensures pct_pop_urb inheritance
    # merges identified by duplicated 'FIPS_{year}' codes (A-->C, B-->C)
        # e.g., 51019 & 51515 --> 51019
    fips_xwalk = pd.read_csv(datapath + 'FIPS_Crosswalk.csv', dtype=str,
                             usecols = [f'FIPS_{decade}',f'FIPS_{year}'])
    df = pd.merge(df, fips_xwalk, how='left', on=f'FIPS_{decade}')
    
    # sums population counts where code-year values are duplicated
    df[f'POP_COU_{year}'] = (df.groupby(f'FIPS_{year}')['POP_COU']
                             .transform('sum')) 
    df[f'POP_URBAN_{year}'] = (df.groupby(f'FIPS_{year}')['POP_URBAN']
                               .transform('sum'))
    df['pct_pop_urb'] = df[f'POP_URBAN_{year}'] / df[f'POP_COU_{year}']
    df['Location'] = df[f'FIPS_{year}']
    df = df[['Location','pct_pop_urb']].drop_duplicates()
    return df 
