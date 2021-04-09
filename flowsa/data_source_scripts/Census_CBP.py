# Census_CBP.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8
"""
Pulls County Business Patterns data in NAICS from the Census Bureau
Writes out to various FlowBySector class files for these data items
EMP = Number of employees, Class = Employment
PAYANN = Annual payroll ($1,000), Class = Money
ESTAB = Number of establishments, Class = Other
This script is designed to run with a configuration parameter
--year = 'year' e.g. 2015
"""
import json
import pandas as pd
import numpy as np
from flowsa.common import get_all_state_FIPS_2
from flowsa.flowbyfunctions import assign_fips_location_system


def Census_CBP_URL_helper(build_url, config, args):
    """
    This helper function uses the "build_url" input from flowbyactivity.py, which
    is a base url for blm pls data that requires parts of the url text string
    to be replaced with info specific to the data year.
    This function does not parse the data, only modifies the urls from which data is obtained.
    :param build_url: string, base url
    :param config: dictionary of method yaml
    :param args: dictionary, arguments specified when running
    flowbyactivity.py ('year' and 'source')
    :return: list of urls to call, concat, parse
    """
    urls_census = []
    FIPS_2 = get_all_state_FIPS_2()['FIPS_2']
    for c in FIPS_2:
        url = build_url
        url = url.replace("__stateFIPS__", c)
        # specified NAICS code year depends on year of data
        if args["year"] in ['2017']:
            url = url.replace("__NAICS__", "NAICS2017")
        if args["year"] in ['2012', '2013', '2014', '2015', '2016']:
            url = url.replace("__NAICS__", "NAICS2012")
        if args["year"] in ['2010', '2011']:
            url = url.replace("__NAICS__", "NAICS2007")
        urls_census.append(url)
    return urls_census


def census_cbp_call(url, cbp_response, args):
    """
    Convert response for calling url to pandas dataframe, transform to pandas df
    :param url: string, url
    :param response_load: df, response from url call
    :param args: dictionary, arguments specified when running
    flowbyactivity.py ('year' and 'source')
    :return: pandas dataframe of original source data
    """
    cbp_json = json.loads(cbp_response.text)
    # convert response to dataframe
    df_census = pd.DataFrame(data=cbp_json[1:len(cbp_json)], columns=cbp_json[0])
    return df_census


def census_cbp_parse(dataframe_list, args):
    """
    Functions to being parsing and formatting data into flowbyactivity format
    :param dataframe_list: list of dataframes to concat and format
    :param args: arguments as specified in flowbyactivity.py ('year' and 'source')
    :return: dataframe parsed and partially formatted to flowbyactivity specifications
    """
    # concat dataframes
    df = pd.concat(dataframe_list, sort=False)
    # Add year
    df['Year'] = args["year"]
    # convert county='999' to line for full state
    df.loc[df['county'] == '999', 'county'] = '000'
    # Make FIPS as a combo of state and county codes
    df['Location'] = df['state'] + df['county']
    # now drop them
    df = df.drop(columns=['state', 'county'])
    # rename NAICS column and add NAICS year as description
    if 'NAICS2007' in df.columns:
        df = df.rename(columns={"NAICS2007": "ActivityProducedBy"})
        df['Description'] = 'NAICS2007'
    if 'NAICS2012' in df.columns:
        df = df.rename(columns={"NAICS2012": "ActivityProducedBy"})
        df['Description'] = 'NAICS2012'
    if 'NAICS2017' in df.columns:
        df = df.rename(columns={"NAICS2017": "ActivityProducedBy"})
        df['Description'] = 'NAICS2017'
    # drop all sectors record
    df = df[df['ActivityProducedBy'] != "00"]
    # rename columns
    df = df.rename(columns={'ESTAB': 'Number of establishments',
                            'EMP': 'Number of employees',
                            'PAYANN': 'Annual payroll'})
    # use "melt" fxn to convert colummns into rows
    df = df.melt(id_vars=["Location", "ActivityProducedBy", "Year", "Description"],
                 var_name="FlowName",
                 value_name="FlowAmount")
    # specify unit based on flowname
    df['Unit'] = np.where(df["FlowName"] == 'Annual payroll', "USD", "p")
    # specify class
    df.loc[df['FlowName'] == 'Number of employees', 'Class'] = 'Employment'
    df.loc[df['FlowName'] == 'Number of establishments', 'Class'] = 'Other'
    df.loc[df['FlowName'] == 'Annual payroll', 'Class'] = 'Money'
    # add location system based on year of data
    df = assign_fips_location_system(df, args['year'])
    # hard code data
    df['SourceName'] = 'Census_CBP'
    # Add tmp DQ scores
    df['DataReliability'] = 5
    df['DataCollection'] = 5
    df['Compartment'] = None
    return df
