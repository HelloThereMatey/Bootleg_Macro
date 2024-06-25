import pandas as pd


def get_data(userid: str, datasetname: str, do_checks: bool = False,
             throttle: bool = True, **kwargs) -> pd.DataFrame:
    """
    Returns a data table.

    Parameters
    ----------
    userid :
        Your API key
    datasetname :
        Name of BEA dataset
    **kwargs:
        Other named parameters as key-value pairs

    Returns
    -------
    pd.DataFrame
        A table with data.
        The 'DataValue' col will try to be converted to a numeric using
        ``pd.to_numeric()``.
        '', '(NA)', and '(NM)'/'(D)' (when accompanied by the same in the NoteRef col)
        will be converted to ``np.nan``.

        Attribute (``.attr``) dictionary keys:

        * **params** (*dict*) -- The user-defined query parameters.
        * **response_size** (*int*) --  The length of the API response.
        * **index_cols** (*list[str]*) -- The columns that uniquely define the
          key (depending on query, might include unnecessary cols). There may be other
          columns that 1:1 map to some of the index key (e.g. "rowCode" and
          "rowDescription"). Also, for ITA, IIP, IntlServTrade, 'TimeSeriesId' unique
          identifies the time_invariant_keys. For IIP  ['TimePeriod'] = ['Frequency',
          'Year'].
        * **time_invariant_keys**, **time_invariant_vars**, **time_variant_keys**,
          **time_variant_vars**, **time_variant_only_vars** (*list[str]*) -- These
          partition the columns into whether they are keys or other variables and how
          they interact with the time variable
        * **detail** (*dict*) -- Has extended info depending on the dataset. It
          contains a 'Dimensions' table with columns 'Name', 'DataType', 'IsValue'
          describing the columns of the main data. It may contain a 'Notes' table with
          extra info referenced from the main data.

    Examples
    --------
    >>> import beaapi_cus
    >>> beaapi_cus.get_dataset('yourAPIkey', 'NIPA', TableName='T20305', Frequency='Q',
    >>>                    Year='X')
    """
    from beaapi_cus import api_request, BEAAPIPkgException

    bea_spec = {k.lower(): v for k, v in kwargs.items()}
    bea_spec.update({
        'UserID': userid ,
        'method': 'GetData',
        'datasetname': datasetname.lower(),
        'ResultFormat': 'json'
    })

    # Columns can be either {key, var} and either {time-invariant, time-variant,
    # time-variant-only}.
    # For keys prefer disaggregated interpreatble over others.

    time_invariant_keys = {
        'nipa' : ['LineNumber'],
        'niunderlyingdetail' : ['LineNumber'],
        # ColumnGParentCode somtimes differs by ColumnCode (when 000)
        # RowCode=' ' for several rows when different Row. Also Row!=RowCode.
        # ('StatebyCountryofUBO', 'Outward', 'All', 'DI') requires TableRowDisplayOrder
        # ('StatebyCountryofUBO', 'Inward', 'All', 'DI') req. TableColumnDisplayOrder
        'mne' : ['SeriesID', 'RowCode', 'Row', 'ColumnCode', 'Column',
                 'ColumnGParentCode'],
        'fixedassets' : ['SeriesCode', 'LineNumber'],
        'ita' : ['Indicator', 'AreaOrCountry', 'Frequency'],
        'iip' : ['Frequency', 'TypeOfInvestment', 'Component'],
        "inputoutput" : ['TableID', 'RowCode', 'ColCode'],
        "intlservtrade" : ['TypeOfService', 'TradeDirection', 'Affiliation',
                           "AreaOrCountry"],
        "gdpbyindustry" : ['TableID', 'Industry', 'IndustrYDescription'],
        "underlyinggdpbyindustry" : ['TableID', 'Industry'],
        "regional" : ['Code', 'GeoFips']
    }

    # If there's a completely constant col list separately (maybe later we expose)
    # underlyinggdpbyindustry: All tables currently Annual
    time_invariant_vars = {
        'nipa' : ['TableName'] + ['SeriesCode', 'LineDescription', 'METRIC_NAME',
                                  'CL_UNIT', 'UNIT_MULT', 'NoteRef'],
        'niunderlyingdetail' : ['TableName'] + ['SeriesCode', 'LineDescription',
                                                'METRIC_NAME', 'CL_UNIT', 'UNIT_MULT',
                                                'NoteRef'],
        'mne' : ['SeriesName', 'ColumnGParent', 'ColumnParent',
                 'ColumnParentCode', 'TableScale'],
        'fixedassets' : ['TableName'] + ['LineDescription', 'METRIC_NAME',
                                         'CL_UNIT', 'UNIT_MULT', 'NoteRef'],
        'ita' : ['TimeSeriesId', 'TimeSeriesDescription', 'CL_UNIT', 'UNIT_MULT'],
        'iip' : ['TimeSeriesId', 'TimeSeriesDescription', 'CL_UNIT', 'UNIT_MULT'],
        "inputoutput" : ['RowDescr', 'RowType', 'ColType', 'ColDescr', 'NoteRef'],
        "intlservtrade" : ['TimeSeriesId', 'TimeSeriesDescription', 'CL_UNIT',
                           'UNIT_MULT'],
        "gdpbyindustry" : ['NoteRef'],
        "underlyinggdpbyindustry" : ['Frequency'] + ['IndustrYDescription', 'NoteRef'],
        "regional" : ['GeoName', 'CL_UNIT', 'UNIT_MULT']
    }

    time_invariant_opt_vars = {
        'regional': ['Description']
    }

    # gdpbyindustry: when frequency is A then Quarter==Year, otherwise I-IV
    # ita: Note that we need frequency because we've have a time val column with 2 rows
    #      (one for QSA and one for QNSA). We also have Yearly and quarterly val cols
    time_variant_keys = {
        'nipa' : ['TimePeriod'],
        'niunderlyingdetail' : ['TimePeriod'],
        'mne' : ['Year', 'TableRowDisplayOrder', 'TableColumnDisplayOrder'],
        'fixedassets' : ['TimePeriod'],
        'ita' : ['TimePeriod'],
        'iip' : ['TimePeriod'],
        "inputoutput" : ['Year'],
        "intlservtrade" : ['TimePeriod'],
        "gdpbyindustry" : ['Frequency', 'Year', 'Quarter'],
        "underlyinggdpbyindustry" : ['Year'],
        "regional" : ['TimePeriod']
    }

    time_variant_vars = {
        'nipa' : ['DataValue'],
        'niunderlyingdetail' : ['DataValue'],
        'mne' : ['DataValueUnformatted', 'DataValue'],
        'fixedassets' : ['DataValue'],
        'ita' : ['DataValue', 'NoteRef'],
        'iip' : ['DataValue', 'NoteRef'],
        "inputoutput" : ['DataValue'],
        "intlservtrade" : ['DataValue', 'NoteRef'],
        "gdpbyindustry" : ['DataValue'],
        "underlyinggdpbyindustry" : ['DataValue'],
        "regional" : ['DataValue']
    }

    time_variant_opt_vars = {
        'regional': ['NoteRef']
    }

    # Note Year!=TimePeriod
    time_variant_only_vars = {
        'ita': ['Year'],
        'iip': ['Year'],
        "intlservtrade": ['Year']
    }

    index_cols = {ds: time_invariant_keys[ds] + tv_keys
                  for ds, tv_keys in time_variant_keys.items()}

    # Check for API error (API team is looking into this)
    if (bea_spec['datasetname'] == "inputoutput"
       and "," in bea_spec.get("tableid", "")):
        raise Exception("There is some concern about the data returned from InputOutput"
                        ' when asking for multiple tables at once. Retry with separate'
                        " requests.")
    if (bea_spec['datasetname'] == "underlyinggdpbyindustry"
       and "," in bea_spec.get("frequency", "")):
        print("underlyinggdpbyindustry currenty only returns Annual results (even if"
              " you ask for additional frequencies).")

    # Warn about dropped extra parameters
    # List of allowable paratmers (generated from metadata.ipynb)
    allowable_params = {'nipa': ['frequency', 'showmillions', 'tableid', 'tablename', 'year'],
                        'niunderlyingdetail': ['frequency', 'tableid', 'tablename', 'year'],
                        'mne': ['directionofinvestment', 'ownershiplevel', 'nonbankaffiliatesonly', 'classification ', 'country', 'industry', 'year', 'state', 'seriesid', 'getfootnotes', 'investment', 'parentinvestment'],
                        'fixedassets': ['tablename', 'year'],
                        'ita': ['indicator', 'areaorcountry', 'frequency', 'year'],
                        'iip': ['typeofinvestment', 'component', 'frequency', 'year'],
                        'inputoutput': ['tableid', 'year'],
                        'intlservtrade': ['typeofservice', 'tradedirection', 'affiliation', 'areaorcountry', 'year'],
                        'gdpbyindustry': ['frequency', 'industry', 'tableid', 'year'],
                        'regional': ['geofips', 'linecode', 'tablename', 'year'],
                        'underlyinggdpbyindustry': ['frequency', 'industry', 'tableid', 'year'],
                        }
    if (bea_spec['datasetname'] in allowable_params.keys()):
        for param in bea_spec.keys():
            if param not in ['UserID', 'method', 'GetData', 'datasetname','ResultFormat'] and param not in allowable_params[bea_spec['datasetname']]:
                print("Parameter " + param + " not allowed in current query and will be dropped by API.")

    

    tbl = api_request(bea_spec, as_dict=False, as_table=True, is_meta=False,
                      throttle=throttle)
    assert isinstance(tbl, pd.DataFrame)

    tbl.attrs['time_invariant_keys'] = time_invariant_keys[datasetname.lower()]
    tbl.attrs['time_invariant_vars'] = time_invariant_vars[datasetname.lower()]
    for col in time_invariant_opt_vars.get(datasetname.lower(), []):
        if col in tbl.columns:
            tbl.attrs['time_invariant_vars'] = tbl.attrs['time_invariant_vars'] + [col]
    tbl.attrs['time_variant_keys'] = time_variant_keys[datasetname.lower()]
    tbl.attrs['time_variant_vars'] = time_variant_vars[datasetname.lower()]
    for col in time_variant_opt_vars.get(datasetname.lower(), []):
        if col in tbl.columns:
            tbl.attrs['time_variant_vars'] = tbl.attrs['time_variant_vars'] + [col]
    tbl.attrs['time_variant_only_vars'] = \
        time_variant_only_vars.get(datasetname.lower(), [])
    tbl.attrs['index_cols'] = index_cols[datasetname.lower()]

    if do_checks:
        expected_cols = tbl.attrs['time_invariant_keys'] \
            + tbl.attrs['time_invariant_vars'] \
            + tbl.attrs['time_variant_keys'] \
            + tbl.attrs['time_variant_vars'] \
            + tbl.attrs['time_variant_only_vars']
        if set(list(tbl.columns)) != set(expected_cols):
            raise BEAAPIPkgException("Col mis-match. Expected: " + str(expected_cols)
                                     + ". Received: " + str(list(tbl.columns)),
                                     tbl.attrs['response_size'])

        tbl.set_index(tbl.attrs['index_cols'], verify_integrity=True)

        (tbl[tbl.attrs['time_invariant_keys'] + tbl.attrs['time_invariant_vars']]
         .drop_duplicates()
         .set_index(tbl.attrs['time_invariant_keys'], verify_integrity=True))

        # TODO: check for completely invariant columns and refactor

    return(tbl)


def to_wide_vars_in_cols(bea_tbl):
    """
    Returns a wide-format data frame with variables as columns (and time dimension as
    rows). This is the typical format for DataFrames in analysis.
    Utilizes the column info in ``bea_tbl.attrs``.

    Parameters
    ----------
    bea_tbl :
        Long-format table (e.g., from the API)

    Returns
    -------
    pd.DataFrame
        A table in a wide format.
    Examples
    --------
    >>> import beaapi_cus
    >>> tbl = beaapi_cus.get_dataset(...)
    >>> wide_tbl = beaapi_cus.to_wide_vars_in_cols(tbl)
    """
    if 'wide_format' in bea_tbl.attrs:
        raise Exception("bea_tbl must be in long-format (e.g., from the API).")
    time_varying_data = (bea_tbl[bea_tbl.attrs['index_cols']
                                 + bea_tbl.attrs['time_variant_vars']]
                         .set_index(bea_tbl.attrs['index_cols'], verify_integrity=True))
    wide_data = time_varying_data.unstack(bea_tbl.attrs['time_invariant_keys'])
    # remove redundant level (we only had 1 data col that we unstacked)
    if len(bea_tbl.attrs['time_variant_vars']) == 1:
        wide_data.columns = wide_data.columns.droplevel(0)
    wide_data.attrs['wide_format'] = 'vars_in_cols'
    return(wide_data)


def to_wide_vars_in_rows(bea_tbl):
    """
    Returns a wide-format data frame with variables as rows (and time dimension as
    columns). This is the way iTables presents data.
    Utilizes the column info in ``bea_tbl.attrs``.

    Parameters
    ----------
    bea_tbl :
        Long-format table (e.g., from the API)

    Returns
    -------
    pd.DataFrame
        A table in a wide format.
    Examples
    --------
    >>> import beaapi_cus
    >>> tbl = beaapi_cus.get_dataset(...)
    >>> wide_tbl = beaapi_cus.to_wide_vars_in_rows(tbl)
    """
    if 'wide_format' in bea_tbl.attrs:
        raise Exception("bea_tbl must be in long-format (e.g., from the API).")
    time_invariant_data = (bea_tbl[bea_tbl.attrs['time_invariant_vars']
                                   + bea_tbl.attrs['time_invariant_keys']]
                           .drop_duplicates()
                           .set_index(bea_tbl.attrs['time_invariant_keys'],
                                      verify_integrity=True))
    time_varying_data = (bea_tbl[bea_tbl.attrs['index_cols']
                                 + bea_tbl.attrs['time_variant_vars']]
                         .set_index(bea_tbl.attrs['index_cols'], verify_integrity=True))

    itables_data = time_varying_data.unstack(bea_tbl.attrs['time_variant_keys'])
    # remove redundant level (we only had 1 data col that we unstacked)
    if len(bea_tbl.attrs['time_variant_vars']) == 1:
        itables_data.columns = itables_data.columns.droplevel(0)

    # merge with time-invariant
    if itables_data.columns.nlevels > 1:
        itables_data.columns = itables_data.columns.to_flat_index()
    itables_data.columns.name = None
    wide_data2 = time_invariant_data.merge(itables_data,
                                           on=bea_tbl.attrs['time_invariant_keys'])
    wide_data2.attrs['wide_format'] = 'vars_in_rows'
    return(wide_data2)
