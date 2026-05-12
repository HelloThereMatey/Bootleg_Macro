- 'bea' source: "title" field has 'id replicated. Instead, take the "Description" files from the meta and put that as title. 
- 'cryptocompare' source, similar issue: 'title' field should have name of the token rather than the ticker/id replicated from the id field.
- 'tedata' source: "title" field should have 'country' - 'metric' type format, taking more of the data from meta and putting into the title filed concatenated as str.
- 'tradingview' source: GUI searching returned no results, needs investigation, testing and work with tvdatafeed and trasdingview node package.
Has the node packages been implemented in bm? Use node packages for search for tradingview and yfinance. See how it is implemented in bootleg_macro.

