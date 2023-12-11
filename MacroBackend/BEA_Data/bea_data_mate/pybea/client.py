from typing import List
from typing import Union

import requests


class BureauEconomicAnalysisClient:

    """
    ### Overview
    ----
    Represents the main BEA Client that
    is used to access the different services.
    """

    def __init__(self, api_key: str) -> None:
        """Initalize the Bureau of Economic Analysis Client.

        ### Arguments:
        ----
        api_key (str):
            Your Bureau of Economic Analysis API
            Key.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)
        """

        # base URL for the SEC EDGAR browser
        self.bea_url = "https://apps.bea.gov/api/data/"
        self.api_key = api_key
        self._format = "JSON"

        if self.api_key:
            self.authstate = True
        else:
            self.authstate = False

    @property
    def format(self) -> str:
        """Used to return the Content format currently set for request.

        ### Returns:
        ----
        str:
            If `JSON`, then data from API request will be sent back
            as JSON data. If `XML` then the data will be returned back
            as XML data.
        """
        return self._format

    @format.setter
    def format(self, value) -> None:
        """Used to return the Content format currently set for request.

        ### Arguments:
        ----
        value (str):
            If `JSON`, then data from API request will be sent back
            as JSON data. If `XML` then the data will be returned back
            as XML data.

        ### Raises:
        ----
        `ValueError`:
            If the format is incorrect will raise a ValueError.
        """

        if value.upper() not in ["JSON", "XML"]:
            raise ValueError("Incorrect format, please set to either `XML` or `JSON`.")

        self._format = value.upper()

    def __repr__(self) -> str:
        """String representation of our BEA Class instance."""

        # define the string representation
        str_representation = (
            f"<BureauEconomicAnalysis Client (authorized={self.authstate})>"
        )

        return str_representation

    def _make_request(self, method: str, params: dict) -> Union[dict, str]:
        """Makes all the request for the BEA Client.

        ### Arguments:
        ----
        method (str):
            The type of request to make. Can be one of the
            following: ['get', 'post', 'put', 'delete', 'put']

        params (dict):
            Any parameters to send along with the request.

        ### Raises:
        ----
        `requests.ConnectionError`:
            If connection error occurs will raise
            an error.

        ### Returns:
        ----
        Union[dict, str]:
            The JSON or XML content.
        """

        # Define a new session.
        request_session = requests.Session()
        request_session.verify = True

        # Define a new request.
        request_request = requests.Request(
            method=method.upper(), url=self.bea_url, params=params
        ).prepare()

        # Send the request.
        response: requests.Response = request_session.send(request=request_request)

        # Close the Session
        request_session.close()

        print(response.url)

        # If the response is OK then return it.
        if response.ok and self._format == "JSON":
            final_response = response.json()
        elif response.ok and self._format == "XML":
            final_response = response.text
        else:
            raise requests.ConnectionError()

        return final_response

    def get_dataset_list(self) -> dict:
        """Returns a list of all the datasets available from the API.

        ### Returns:
        ----
        dict:
            A dictionary with a collection of datasets,
            their corresponding names, and their descriptions.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Grab the Dataset List.
            >>> dataset_list = bea_client.get_dataset_list()
        """

        # Define the parameters.
        params = {
            "UserID": self.api_key,
            "method": "GETDATASETLIST",
            "ResultFormat": self._format,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def get_parameters_list(self, dataset_name: str) -> dict:
        """Retrieves a list of the parameters (required and optional) for
        a particular dataset.

        ### Returns:
        ----
        dict:
            A dictionary with a collection of datasets parameters, their
            corresponding names, and their descriptions

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Grab the Paramters List.
            >>> parameters_set_list = bea_client.get_parameters_list()
        """

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GETPARAMETERLIST",
            "datasetname": dataset_name,
            "resultformat": self._format,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def gdp_by_industry(
        self,
        year: List[str] = "ALL",
        industry: List[str] = "ALL",
        frequency: List[str] = "A,Q,M",
        table_id: List[str] = "ALL",
    ) -> dict:
        """Grabs the estimates of value added, gross output,
        intermediate inputs, KLEMS, and employment statistics by industry.

        ### Arguments:
        ----
        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All). Defaults to 'ALL'.

        industry (List[str], optional, Default='ALL'):
            List of industries to retrieve (ALL for All). Defaults to 'ALL'.

        frequency (str, optional, Default="A,Q,M"):
            `Q` for Quarterly data or `A` for Annual,
            `A,Q` for both.

        table_id (List[str], optional, Default='ALL'):
            The unique GDP by Industry table identifier (ALL for All).

        ### Returns:
        ----
        dict:
            A list of GDP figures for the industry specified.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Grab GDP Data by Industry.
            >>> national_income = bea_client.gdp_by_industry(
                table_name='T10101',
                industry='ALL',
                frequency=['A', 'Q'],
                year=['2011', '2012'],
                table_id=['1']
            )
            >>> national_income
        """
        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(frequency, list):
            frequency = ",".join(frequency)

        if isinstance(table_id, list):
            table_id = ",".join(table_id)

        if isinstance(industry, list):
            industry = ",".join(industry)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "GDPbyIndustry",
            "year": year,
            "resultformat": self._format,
            "industry": industry,
            "frequency": frequency,
            "tableid": table_id,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def underlying_gdp_by_industry(
        self,
        year: List[str] = "ALL",
        industry: List[str] = "ALL",
        frequency: List[str] = "A,Q,M",
        table_id: List[str] = "ALL",
    ) -> dict:
        """The underlying gross domestic product by industry data are
        contained within a dataset called UnderlyingGDPbyIndustry.

        ### Overview:
        ----
        BEA's industry accounts are used extensively by policymakers and
        businesses to understand industry interactions, productivity trends,
        and the changing structure of the U.S. economy. The underlying
        GDP-by-industry dataset includes data in both current and chained (real)
        dollars. The dataset contains estimates for value added, gross output,
        and intermediate input statistics. This dataset is structurally similar to
        the GDPbyIndustry dataset (Appendix F), but contains additional industry detail.

        ### Arguments:
        ----
        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        industry (List[str], optional):
            List of industries to retrieve (ALL for All).

        frequency (str, optional, Default="A,Q,M"):
            `Q` for Quarterly data or `A` for Annual,
            `A,Q` for both.

        table_id (List[str], optional, Default='ALL'):
            The unique GDP by Industry table identifier (ALL for All).

        ### Returns:
        ----
        dict:
            A list of GDP figures for the industry specified.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Quarterly Value Added by Industry data for all industries
            >>> # for years 2012 and 2013.
            >>> underlying_gdp_by_industry = bea_client.underlying_gdp_by_industry(
                industry='ALL',
                frequency=['Q'],
                year=['2012', '2013'],
                table_id='ALL'
            )
            >>> underlying_gdp_by_industry
        """

        if year != "ALL":
            year = ",".join(year)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "underlyingGDPbyIndustry",
            "year": year,
            "resultformat": self._format,
            "industry": industry,
            "frequency": ",".join(frequency),
            "tableid": table_id,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def international_trade_services(
        self,
        type_of_service: str = "ALL",
        trade_direction: List[str] = "ALL",
        affiliation: List[str] = "ALL",
        year: List[str] = "ALL",
        area_or_country: List[str] = "AllCountries",
    ) -> dict:
        """This dataset contains annual data on U.S. international trade in services.

        ### Overview:
        ----
        These data are updated each October to reflect the International Transactions
        Accounts annual update released in June. BEA's statistics on services supplied
        through affiliates by multinational enterprises are not included in this dataset.

        ### Arguments:
        ----
        type_of_service (List[str], optional, Default='ALL'):
            The TypeOfService parameter specifies the type of service being traded (e.g. travel,
            transport, or insurance services). Exactly one TypeOfService parameter value other
            than “All” must be provided in all data requests unless exactly one AreaOrCountry
            parameter value other than “All” is requested. That is, multiple Indicators can
            only be specified if a single AreaOrCountry parameter is specified.

        trade_direction (List[str], optional, Default='ALL'):
            The TradeDirection parameter specifies the trade direction of the services
            transactions. There are four valid parameter values other than “All”:

                1. Exports - Exports
                2. Imports - Imports
                3. Balance - Balance (exports less imports)
                4. SupplementalIns - Supplemental detail on insurance transactions.

        affiliation (str, optional, Default='ALL'):
            The Affiliation parameter specifies the tradedirection for the services
            transactions. There are five valid parameter values other than “All”:

                1. AllAffiliations - The total for all trade, whether affiliated or unaffiliated.
                2. Unaffiliated - Unaffiliated trade.
                3. Affiliated - Affiliated trade.
                4. UsParents - U.S. parents' trade with their foreign affiliates.
                5. UsAffiliates - U.S. affiliates' trade with their foreign parent groups.

        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        area_or_country (List[str], optional, Default='AllCountries'):
            The AreaOrCountry parameter specifies the counterparty area or country
            of the services transactions. The default parameter value (“AllCountries”)
            returns the total for all countries, while “All” returns all data available
            by area and country. Exactly one AreaOrCountry parameter value must be provided
            in all data requests unless exactly one TypeOfService parameter value other
            than “All” is requested.That is, a list of countries can only be specified if a
            single TypeOfService is specified.

        ### Returns:
        ----
        dict:
            A list of international trade services.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Imports of services from Germany for 2014 and 2015.
            >>> international_trade_services = bea_client.international_trade_services(
                type_of_service='AllServiceTypes',
                trade_direction=['Imports'],
                year=['2014', '2015'],
                affiliation=['AllAffiliations'],
                area_or_country=['Germany']
            )
            >>> international_trade_services
        """

        if year != "ALL":
            year = ",".join(year)

        if isinstance(area_or_country, list):
            area_or_country = ",".join(area_or_country)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "IntlServTrade",
            "year": year,
            "resultformat": self._format,
            "typeofservice": type_of_service,
            "tradedirection": trade_direction,
            "affiliation": affiliation,
            "areaorcountry": area_or_country,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def national_income_and_product_accounts(
        self,
        table_name: str,
        year: List[str] = "ALL",
        frequency: List[str] = "A,Q,M",
    ) -> dict:
        """Grabs the data from the National Income and Product Accounts.

        ### Overview:
        ----
        This dataset contains data from the National Income and Product Accounts
        which include measures of the value and composition of U.S.production and
        the incomes generated in producing it. NIPA data is provided on a table basis;
        individual tables contain between fewer than 10 to more than 200 distinct
        data series.

        ### Arguments:
        ----
        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        industry (List[str], optional, Default='ALL'):
            List of industries to retrieve (ALL for All).

        frequency (str, optional, Default="A,Q,M"):
            `Q` for Quarterly data or `A` for Annual, `M` for
            monthly.

        table_id (List[str], optional, Default='ALL'):
            The unique GDP by Industry table identifier (ALL for All).

        ### Returns:
        ----
        dict:
            A list of GDP figures for the industry specified.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Grab National Income & Product Data.
            >>> national_income = bea_client.national_income_and_product_accounts(
                table_name='T10101',
                frequency=['A', 'Q'],
                year=['2011', '2012']
            )
            >>> national_income
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(table_name, list):
            table_name = ",".join(table_name)

        if isinstance(frequency, list):
            frequency = ",".join(frequency)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "NIPA",
            "year": year,
            "resultformat": self._format,
            "frequency": frequency,
            "tablename": table_name,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def national_income_and_product_accounts_detail(
        self,
        table_name: List[str] = "ALL",
        year: List[str] = "ALL",
        frequency: List[str] = "A,Q,M",
    ) -> dict:
        """This dataset contains underlying detail data from the
        National Income and Product Accounts.

        ### Overview:
        ----
        This dataset contains data from the National Income and Product Accounts
        which include measures of the value and composition of U.S.production and
        the incomes generated in producing it. NIPA data is provided on a table basis;
        individual tables contain between fewer than 10 to more than 200 distinct data series.

        ### Arguments:
        ----
        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        industry (List[str], optional, Default='ALL'):
            List of industries to retrieve (ALL for All).

        frequency (str, optional, Default="A,Q,M"):
            `Q` for Quarterly data or `A` for Annual, "M" for monthly.

        table_id (List[str], optional, Default='ALL'):
            The unique GDP by Industry table identifier (ALL for All).

        ### Returns:
        ----
        dict:
            A list of GDP figures for the industry specified.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Grab Personal Conumption Expenditures, Current Dollars,
            >>> # Annually, Quarterly and Monthly for all years.
            >>> national_income = bea_client.national_income_and_product_accounts_detail(
                table_name='U20305',
                frequency=['A', 'Q'],
                year=['2011', '2012']
            )
            >>> national_income
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(table_name, list):
            table_name = ",".join(table_name)

        if isinstance(frequency, list):
            frequency = ",".join(frequency)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "NIUnderlyingDetail",
            "year": year,
            "resultformat": self._format,
            "frequency": frequency,
            "tablename": table_name,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def fixed_assets(
        self, table_name: List[str] = "ALL", year: List[str] = "ALL"
    ) -> dict:
        """This dataset contains data from the standard set of Fixed Assets
        tables as published online.

        ### Arguments:
        ----
        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        table_name (List[str], optional, Default='ALL'):
            The standard NIPA table identifier.

        ### Returns:
        ----
        dict:
            A list of GDP figures for the industry specified.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Grab Current-Cost Net Stock of Private Fixed Assets, Equipment, Structures,
            >>> # and Intellectual Property Products by Type, for all years.
            >>> fixed_assets = bea_client.fixed_assets(
                table_name='FAAt201',
                year=['2011', '2012']
            )
            >>> fixed_assets
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(table_name, list):
            table_name = ",".join(table_name)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "FixedAssets",
            "year": year,
            "resultformat": self._format,
            "tablename": table_name,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def direct_investments_and_multinational_enterprises(
        self,
        direction_of_investment: str,
        classification: str,
        series_id: int = "ALL",
        year: List[str] = "ALL",
        country: List[str] = "ALL",
        industry: List[str] = "ALL",
        footnotes: bool = True,
    ) -> dict:
        """Grabs one of two datasets from the Direct Investment
        and Multinational Enterprises dataset.

        ### Overview:
        ----
        This dataset contains the following statistics:

        Direct Investment (DI)—income and financial transactions in direct
        investment that underlie the U.S. balance of payments statistics,
        and direct investment positions that underlie the U. S. international
        investment positions

        ### Arguments:
        ----
        direction_of_investment (str):
            `outward` for US direct investment abroad, `inward` for
            foreign investment in the US.

        classification (str):
            Results by `country` or `industry`.

        series_id (int, optional, Default='ALL'):
            Data Series Identifier (ALL for All).

        year (List[str], optiona, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        country (List[str], optional, Default='ALL'):
            List of country(s) of data to retrieve (ALL for All).

        industry (List[str], optional, Default='ALL'):
            List of industries to retrieve (ALL for All).

        footnotes (bool, optional, Default=True):
            `True` to include footnotes, `False` to not include.

        ### Returns:
        ----
        dict:
            A list of investment data.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # U. S. direct investment position in China and Asia for 2011 and 2012
            >>> investments = bea_client.direct_investments_and_multinational_enterprises(
                direction_of_investment='outward',
                classification='country',
                series_id=['30'],
                year=['2011', '2012'],
                country=['650', '699']
            )
            >>> investments
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(series_id, list):
            series_id = ",".join(series_id)

        if isinstance(country, list):
            country = ",".join(country)

        if isinstance(industry, list):
            industry = ",".join(industry)

        if footnotes:
            footnotes = "Yes"
        else:
            footnotes = "No"

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "MNE",
            "year": year,
            "country": country,
            "industry": industry,
            "seriesid": series_id,
            "classification": classification,
            "directionofinvestment": direction_of_investment,
            "resultformat": self._format,
            "getfootnotes": footnotes,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def activities_investments_and_multinational_enterprises(
        self,
        direction_of_investment: str,
        classification: str,
        ownership_level: bool,
        non_bank_affilates_only: bool,
        series_id: int = "ALL",
        states: List[str] = "ALL",
        year: List[str] = "ALL",
        country: List[str] = "ALL",
        industry: List[str] = "ALL",
        footnotes: bool = True,
    ) -> dict:
        """Grabs one of two datasets from the Direct Investment and
        Multinational Enterprises dataset.

        ### Overview:
        ----
        This dataset contains the following statistics:

        Activities of Multinational Enterprises (AMNE)—operations and finances
        of U.S. parent enterprises and their foreign affiliates and U.S.
        affiliates of foreign MNEs.

        ### Arguments:
        ----
        direction_of_investment (str):
            `outward` for US direct investment abroad, `inward` for foreign investment
            in the US, `state` provides data on U. S. affiliates of foreign multinational
            enterprises at the state level and `parent` provides data on U.S. parent
            enterprises.

        classification (str]):
            Results by `country` or `industry`.

        ownership_level (bool):
            `True` for majority-owned affiliates, `False` for all affiliates.

        non_bank_affilates_only (bool):
            `True` Both Bank and NonBank Affiliates, `False` for all Nonbank
            Affiliates.

        series_id (int, optional, Default='ALL'):
            Data Series Identifier (ALL for All).

        states (List[str], optional, Default='ALL'):
            List of state(s) of data to retrieve (ALL for All).

        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        country (List[str], optional, Default='ALL'):
            List of country(s) of data to retrieve (ALL for All)

        industry (List[str], optional, Default='ALL'):
            List of industries to retrieve (ALL for All).

        footnotes (bool, optional, Default=True):
            `True` to include footnotes, `False` to not include.

        ### Returns:
        ----
        dict:
            A list of investment data.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Net income and sales for Brazilian affiliates of U.S.
            >>> # parent enterprises, all industries, 2011 and 2012.
            >>> investments = bea_client.direct_investments_and_multinational_enterprises(
                direction_of_investment='outward',
                classification='CountryByIndustry',
                series_id=['4','5'],
                year=['2011', '2012'],
                country=['202'],
                ownership_level=False,
                industry='ALL',
                non_bank_affilates_only=False,
            )
            >>> investments
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(series_id, list):
            series_id = ",".join(series_id)

        if isinstance(states, list):
            states = ",".join(states)

        if isinstance(country, list):
            country = ",".join(country)

        if isinstance(industry, list):
            industry = ",".join(industry)

        if footnotes:
            footnotes = "Yes"
        else:
            footnotes = "No"

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "MNE",
            "year": year,
            "nonbankaffiliatesonly": int(non_bank_affilates_only),
            "ownershiplevel": int(ownership_level),
            "state": states,
            "country": country,
            "industry": industry,
            "seriesid": series_id,
            "classification": classification,
            "directionofinvestment": direction_of_investment,
            "resultformat": self._format,
            "getfootnotes": footnotes,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def international_transactions(
        self,
        indicator: str = "ALL",
        area_or_country: str = "AllCountries",
        year: List[str] = "ALL",
        frequency: str = "ALL",
    ) -> dict:
        """This dataset contains data on U. S. international transactions.

        ### Overview:
        ----
        The DataSetName is ITA. This dataset contains data on U. S. international transactions.
        BEA's international transactions (balance of payments) accounts include all transactions
        between U. S. and foreign residents.

        ### Arguments:
        ----
        indicator (str, optional, Default='ALL'):
            The indicator code for the type of transaction requested.

        area_or_country (str, optional, Default='AllCountries'):
            The area or country requested.

        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        frequency (List[str], optional, Default='ALL'):
            A - Annual, QSA - Quarterly seasonally adjusted,
            QNSA -Quarterly not seasonally adjusted.

        ### Returns:
        ----
        dict:
            A list of transaction data.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Balance on goods with China for 2011 and 2012.
            >>> balance_on_goods = bea_client.international_transactions(
                indicator=['BalGds'],
                area_or_country=['China'],
                year=['2011', '2012'],
                frequency=['A']
            )
            >>> balance_on_goods
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(area_or_country, list):
            area_or_country = ",".join(area_or_country)

        if isinstance(frequency, list):
            frequency = ",".join(frequency)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "ITA",
            "indicator": indicator,
            "year": year,
            "frequency": frequency,
            "areaorcountry": area_or_country,
            "resultformat": self._format,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def international_investments_positions(
        self,
        type_of_investment: str = "ALL",
        component: str = "ALL",
        year: List[str] = "ALL",
        frequency: str = "ALL",
    ) -> dict:
        """This dataset contains data on the U. S. international investment position.

        ### Overview:
        ----
        The DataSetName is IIP. This dataset contains data on the U.S. international investment
        position. BEA's international investment position accounts include the end of period
        value of accumulated stocks of U.S. financial assets and liabilities.

        ### Arguments:
        ----
        type_of_investment (str, optional, Default='ALL'):
            The type of investment.

        component (str, optional, Default='ALL'):
            Component of changes in position.

        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        frequency (List[str], optional, Default='ALL'):
            A - Annual, QNSA -Quarterly not seasonally adjusted.

        ### Returns:
        ----
        dict:
            A list of transaction data.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # U. S. assets excluding financial derivatives; change in
            >>> # position attributable to price changes for all available
            >>> # years.
            >>> us_assets = bea_client.international_investments_positions(
                type_of_investment=['FinAssetsExclFinDeriv'],
                component=['ChgPosPrice'],
                year='ALL',
                frequency=['A']
            )
            >>> us_assets
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(component, list):
            component = ",".join(component)

        if isinstance(frequency, list):
            frequency = ",".join(frequency)

        if isinstance(type_of_investment, list):
            type_of_investment = ",".join(type_of_investment)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "IIP",
            "year": year,
            "frequency": frequency,
            "component": component,
            "typeofinvestment": type_of_investment,
            "resultformat": self._format,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def input_output_statstics(
        self, table_id: List[str], year: List[str] = "ALL"
    ) -> dict:
        """The Input‐Output Statistics are contained within a dataset
        called InputOutput.

        ### Overview:
        ----
        The Input‐Output Statistics are contained within a dataset called
        InputOutput. BEA's industry accounts are used extensively by policymakers
        and businesses to understand industry interactions, productivity trends,
        and the changing structure of the U.S. economy. The input-output accounts
        provide a detailed view of the interrelationships between U.S. producers and
        users. The Input‐Output dataset contains Make Tables, Use Tables, and Direct
        and Total Requirements tables.

        ### Arguments:
        ----
        table_id (List[str], optional,  Default='ALL'):
            The unique GDP by Industry table identifier (ALL for All).

        year (List[str], optional, Default='ALL'):
            List of year(s) of data to retrieve (ALL for All).

        ### Returns:
        ----
        dict:
            A list of input and output statistics.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Data from Industry‐by‐Commodity Total Requirements,
            >>> # After Redefinitions (Sector Level) table
            >>> # for years 2010, 2011, and 2012.
            >>> input_output_data = bea_client.input_output_statstics(
                table_id=['56'],
                year=['2010', '2011', '2012', '2013']
            )
            >>> input_output_data
        """

        if isinstance(year, list):
            year = ",".join(year)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "InputOutput",
            "year": year,
            "tableid": ",".join(table_id),
            "resultformat": self._format,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response

    def regional(
        self,
        table_name: str,
        line_code: Union[int, str],
        geo_fips: List[str] = "ALL",
        year: List[str] = "ALL",
    ) -> dict:
        """The Input‐Output Statistics are contained within a dataset
        called InputOutput.

        ### Overview:
        ----
        The Regional dataset contains income and employment estimates from the Regional
        Economic Accounts by state, county, and metropolitan area. All data accessible
        through the Regional InteractiveTables on bea.gov are available through this
        dataset. The Regional dataset replaces the RegionalIncome and RegionalProduct
        datasets. Additional information may be found at:
        http://apps.bea.gov/regional/pdf/RegionalApi.pd

        ### Arguments:
        ----
        table_name (str):
            TableName specifies a published table fromthe regional accounts.
            Exactly one TableName must be provided.

        line_code (Union[int, str]):
            LineCode corresponds to the statistic in a table. It can either be
            one value(ie.1,10,11), or 'ALL' to retrieve all the statistics for
            one GeoFips.

        geo_fips (List[str], optional, Default='ALL')
            GeoFips specifies geography. It can be all states (STATE), all counties
            (COUNTY), all Metropolitan Statistical Areas (MSA), all Micropolitan
            Statistical Areas (MIC), all Metropolitan Divisions (DIV), all Combined
            Statistical Areas (CSA), all metropolitan/nonmetropolitan portions
            (PORT), or state post office abbreviation for all counties in one
            state (e.g. NY).

        year (List[str], optional, Default='ALL'):
            Year is either a list of comma delimited years, LAST5, LAST10, or
            ALL. Year will default to LAST5 years if the parameter is not
            specified.

        ### Returns:
        ----
        dict:
            A list of input and output statistics.

        ### Usage:
        ----
            >>> # Initalize the new Client.
            >>> bea_client = BureauEconomicAnalysisClient(api_key=API_KEY)

            >>> # Personal income for 2012 and 2013 for all counties.
            >>> regional_data = bea_client.regional(
                table_name=['CAINC1'],
                line_code=1,
                geo_fips=['COUNTY'],
                year=['2012', '2013']
            )
            >>> regional_data
        """

        if isinstance(year, list):
            year = ",".join(year)

        if isinstance(geo_fips, list):
            geo_fips = ",".join(geo_fips)

        # Define the parameters.
        params = {
            "userid": self.api_key,
            "method": "GetData",
            "datasetname": "Regional",
            "year": year,
            "TableName": ",".join(table_name),
            "GeoFips": geo_fips,
            "LineCode": line_code,
            "resultformat": self._format,
        }

        # Make the request.
        response = self._make_request(method="get", params=params)

        return response
