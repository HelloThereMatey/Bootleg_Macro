"""
Pydantic models for standardized time series metadata.

All time series returned by bm sources follow a common metadata format
defined by these models.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


class SeriesMetadata(BaseModel):
    """Standard metadata for all time series returned by bm sources."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    # Identification
    id: str = Field(description="Unique identifier for the series (e.g., ticker, series code)")
    title: Optional[str] = Field(default=None, description="Human-readable title/name of the series")

    # Source information
    source: str = Field(description="Data source name (e.g., 'yfinance', 'fred', 'bea')")
    original_source: Optional[str] = Field(default=None, description="Original source name if aggregated")

    # Temporal information
    start_date: Optional[date] = Field(default=None, description="First observation date")
    end_date: Optional[date] = Field(default=None, description="Last observation date")
    frequency: Optional[str] = Field(default=None, description="Data frequency (e.g., 'D', 'W', 'M', 'Q', 'A')")

    # Units and currency
    units: Optional[str] = Field(default=None, description="Full units description")
    units_short: Optional[str] = Field(default=None, description="Short units notation")

    # Data quality
    length: int = Field(default=0, description="Number of non-null observations")
    min_value: Optional[float] = Field(default=None, description="Minimum value in series")
    max_value: Optional[float] = Field(default=None, description="Maximum value in series")

    # Description
    description: Optional[str] = Field(default=None, description="Full description of the series")

    # Last updated
    last_updated: Optional[datetime] = Field(default=None, description="When the data was last fetched")

    def to_pandas(self) -> "pandas.Series":
        """Convert metadata to a pandas Series.

        Each field becomes a named value in the series.

        Returns:
            pandas Series with metadata fields as values
        """
        import pandas as pd

        data = {
            'id': self.id,
            'title': self.title,
            'source': self.source,
            'original_source': self.original_source,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'frequency': self.frequency,
            'units': self.units,
            'units_short': self.units_short,
            'length': self.length,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'description': self.description,
            'last_updated': self.last_updated,
        }

        return pd.Series(data, name='metadata')


class StandardSeries(BaseModel):
    """A standardized time series with data and metadata.

    All bm sources return data in this format.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    data: dict = Field(description="Dictionary mapping date to values (for JSON serialization)")
    metadata: SeriesMetadata = Field(description="Metadata for this series")

    @classmethod
    def from_pandas(
        cls,
        series: "pandas.Series",
        metadata: Optional[SeriesMetadata] = None,
        **overrides
    ) -> "StandardSeries":
        """Create a StandardSeries from a pandas Series.

        Args:
            series: pandas Series with DatetimeIndex
            metadata: Optional pre-built metadata
            **overrides: Fields to override in the metadata
        """
        import pandas as pd

        if metadata is None:
            metadata = SeriesMetadata(id=series.name or "unknown")

        # Auto-fill metadata from pandas Series
        if isinstance(series.index, pd.DatetimeIndex):
            if metadata.start_date is None:
                metadata.start_date = series.index.min().date()
            if metadata.end_date is None:
                metadata.end_date = series.index.max().date()

        if metadata.length == 0:
            metadata.length = int(series.dropna().shape[0])

        if metadata.min_value is None:
            vals = series.dropna()
            if len(vals) > 0:
                metadata.min_value = float(vals.min())

        if metadata.max_value is None:
            vals = series.dropna()
            if len(vals) > 0:
                metadata.max_value = float(vals.max())

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)

        # Convert to dict for JSON serialization
        data_dict = {
            str(k): float(v) if pd.notna(v) else None
            for k, v in series.items()
        }

        return cls(data=data_dict, metadata=metadata)

    def to_pandas(self) -> "pandas.Series":
        """Convert back to a pandas Series."""
        import pandas as pd

        series = pd.Series(self.data, name=self.metadata.id)
        series.index = pd.to_datetime(series.index)
        return series
