# Census_DP04_1yr.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8
"""
Pulls American Community Survey 1yr Data Profile (DP04): Selected Housing Characteristics
--year = 'year' e.g. 2015
"""
import json
import pandas as pd
import numpy as np
from flowsa.location import US_FIPS
from flowsa.flowbyfunctions import assign_fips_location_system


def DP04_1yr_URL_helper(*, build_url, year, **_):
    """
    This helper function uses the "build_url" input from generateflowbyactivity.py,
    which is a base url for data imports that requires parts of the url text
    string to be replaced with info specific to the data year. This function
    does not parse the data, only modifies the urls from which data
    is obtained.
    :param build_url: string, base url
    :param year: year
    :return: list, urls to call, concat, parse, format into
        Flow-By-Activity format
    """
    urls_DP04 = []
    # This section gets the census data by county instead of by state.
    # This is only for years 2010 and 2011. This is done because the State
    # query that gets all counties returns too many results and errors out.

    url = build_url
    # url = url.replace("%3A%2A", ":*")
    urls_DP04.append(url)

    return urls_DP04


def DP04_1yr_call(*, resp, **_):
    """
    Convert response for calling url to pandas dataframe, begin
        parsing df into FBA format
    :param resp: df, response from url call
    :return: pandas dataframe of original source data
    """
    DP04_json = json.loads(resp.text)
    # convert response to dataframe
    df_DP04 = pd.DataFrame(
        data=DP04_json[1:len(DP04_json)], columns=DP04_json[0])
    return df_DP04


def DP04_1yr_parse(*, df_list, year, **_):
    """
    Combine, parse, and format the provided dataframes
    :param df_list: list of dataframes to concat and format
    :param year: year
    :return: df, parsed and partially formatted to
        flowbyactivity specifications
    """
    # concat dataframes
    df = pd.concat(df_list, sort=False)

    # remove first string of GEO_ID to access the FIPS code
    df['GEO_ID'] = df.GEO_ID.str.replace('0500000US' , '')

    # rename columns to increase readibility
    df = df.rename(columns={'DP04_0046PE':'FlowAmount', #percent of owner-occupied homes (vs renter-occupied homes)
                            'NAME': 'County Name',
                            'GEO_ID':'Location'})
    
    # hard code data for flowsa format
    df['FlowName'] = 'Owner-occupied housing'
    df['Unit'] = '% of homes' # percent of occupied homes
    df['LocationSystem'] = 'FIPS'
    df['FlowType'] = 'TECHNOSPHERE_FLOW'
    df['Class'] ='Other'
    df['Year'] = int(year) - 2
    df['ActivityProducedBy'] = 'Households'
    df['SourceName'] = 'Census_DP04_1yr'
    df['Description'] = 'Housing data from 1yr DP04'
    # Add tmp DQ scores
    df['DataReliability'] = 5
    df['DataCollection'] = 5
    df['Compartment'] = None

    return df