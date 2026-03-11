import os
import sys
import argparse
from typing import Iterable

import pandas as pd

# Ensure repo root is importable when run from examples/
wd = os.path.dirname(__file__)
repo_root = os.path.dirname(wd)
if repo_root not in sys.path:
    sys.path.append(repo_root)

from MacroBackend import Utilities
from MacroBackend.BEA_Data import bea_data_mate


def search_bea_index(
    index_df: pd.DataFrame,
    query: str,
    search_cols: Iterable[str] | None = None,
    max_results: int = 25,
) -> pd.DataFrame:
    """Search BEA index table for a query across metadata columns.

    Args:
        index_df: BEA master index DataFrame.
        query: Text query to search for.
        search_cols: Optional list of columns to search. Defaults to common metadata fields.
        max_results: Max rows to return.

    Returns:
        Filtered DataFrame with relevant metadata columns.
    """
    if index_df is None or index_df.empty:
        return pd.DataFrame()

    q = str(query).strip()
    if not q:
        return pd.DataFrame()

    if search_cols is None:
        search_cols = [
            "title",
            "LineDescription",
            "SeriesCode",
            "TableId",
            "TableName",
            "DatasetName",
            "id",
            "CL_UNIT",
            "METRIC_NAME",
        ]

    cols = [c for c in search_cols if c in index_df.columns]
    if not cols:
        return pd.DataFrame()

    mask = pd.Series(False, index=index_df.index)
    for col in cols:
        ser = index_df[col].astype(str)
        mask = mask | ser.str.contains(q, case=False, regex=True, na=False)

    out_cols = [
        c for c in [
            "id",
            "title",
            "DatasetName",
            "TableId",
            "SeriesCode",
            "LineDescription",
            "TableName",
            "CL_UNIT",
            "METRIC_NAME",
            "Frequency",
            "source",
        ] if c in index_df.columns
    ]

    return index_df.loc[mask, out_cols].head(max_results).copy()


def main():
    parser = argparse.ArgumentParser(description="Build and test BEA local series index search.")
    parser.add_argument(
        "--index-path",
        default=os.path.join(repo_root, "User_Data", "BEA", "BEA_Series_Index.h5s"),
        help="Path to output/read BEA .h5s index file.",
    )
    parser.add_argument(
        "--frequency",
        default="Q",
        help="Frequency used while building index (A, Q, M).",
    )
    parser.add_argument(
        "--max-tables-per-dataset",
        type=int,
        default=None,
        help="Optional cap per dataset for faster test builds.",
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        default=["gross domestic product", "personal consumption", "price index", "employment"],
        help="Search query list.",
    )
    args = parser.parse_args()

    keyz = Utilities.api_keys().keys
    bea_key = keyz.get("bea")
    if not bea_key:
        raise RuntimeError("No BEA API key found. Add key 'bea' in SystemInfo/API_Keys.json.")

    print("Step 1/3: Building BEA series index...")
    index_df = bea_data_mate.BEA_API_backend.build_bea_series_index(
        bea_key=bea_key,
        save_path=args.index_path,
        frequency=args.frequency,
        max_tables_per_dataset=args.max_tables_per_dataset,
    )

    print(f"Step 2/3: Index saved to {args.index_path}")
    print(f"Rows indexed: {len(index_df)}")

    print("Step 3/3: Running search tests...")
    loaded_df = pd.read_hdf(args.index_path, key="data")

    for query in args.queries:
        print("\n" + "=" * 100)
        print(f"Query: {query}")
        matches = search_bea_index(loaded_df, query=query, max_results=20)
        if matches.empty:
            print("No matches found.")
        else:
            print(f"Matches found: {len(matches)}")
            print(matches.to_string(index=False))


if __name__ == "__main__":
    main()
