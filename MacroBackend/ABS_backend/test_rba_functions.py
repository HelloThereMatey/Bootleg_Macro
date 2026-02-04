"""
Quick test script to verify RBA functions work with Python readabs package.
"""

import sys
import os

# Add parent directories to path properly
wd = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(wd)  # MacroBackend
grandparent = os.path.dirname(parent)  # Bootleg_Macro

# Add grandparent so we can import MacroBackend module
sys.path.insert(0, grandparent)

import readabs_py

print("=" * 70)
print("Testing RBA Functions with Python readabs")
print("=" * 70)

# Test 1: Get RBA catalogue
print("\n[Test 1] Get RBA Catalogue:")
try:
    catalogue = readabs_py.get_rba_catalogue(verbose=True)
    if catalogue is not None:
        print(f"✓ Success! Found {len(catalogue)} RBA tables")
        print(f"Columns: {catalogue.columns.tolist()}")
        print(f"First few tables:\n{catalogue.head()}")
    else:
        print("✗ No catalogue returned")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 2: Browse RBA tables
print("\n[Test 2] Browse RBA Tables for 'interest':")
try:
    tables = readabs_py.browse_rba_tables(searchterm="interest", verbose=True)
    if tables is not None:
        print(f"✓ Success! Found {len(tables)} matching tables")
        print(tables[['id', 'title']].head() if 'id' in tables.columns else tables.head())
    else:
        print("✗ No tables found")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Browse RBA series
print("\n[Test 3] Browse RBA Series for 'Cash Rate' in interest tables:")
try:
    # Filter to only search interest-related tables for efficiency
    series = readabs_py.browse_rba_series(
        searchterm="Cash Rate",
        table_filter="interest",
        max_tables=10,
        verbose=True
    )
    if series is not None:
        print(f"✓ Success! Found {len(series)} matching series")
        print(series.head())
    else:
        print("✗ No series found")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 4: Get specific RBA series (if we found one)
print("\n[Test 4] Get RBA Series Data:")
try:
    # First, let's find what's actually in the F1 table (interest rates)
    print("Attempting to read F1 table to see available series...")
    import readabs as ra
    f1_data, f1_meta = ra.read_rba_table(table="F1")
    print(f"F1 table has {len(f1_data.columns)} series")
    print(f"First few column names: {f1_data.columns.tolist()[:5]}")
    
    # Now try to get one of those series
    if len(f1_data.columns) > 0:
        first_series_id = f1_data.columns[0]
        print(f"\nTrying to get series: {first_series_id}")
        
        data_series, metadata = readabs_py.get_rba_series(
            series_id=first_series_id,
            table_no="F1",
            verbose=True
        )
        
        if data_series is not None:
            print(f"✓ Success! Retrieved series")
            print(f"Data shape: {data_series.shape}")
            print(f"Metadata:\n{metadata}")
            print(f"\nLast 5 values:\n{data_series.tail()}")
        else:
            print("✗ No data returned")
    else:
        print("✗ No columns found in F1 table")
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Testing Complete")
print("=" * 70)
