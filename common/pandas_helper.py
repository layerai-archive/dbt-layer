import decimal
import pathlib
from typing import Any, List

import agate  # type:ignore
import numpy as np
import pandas as pd  # type:ignore
from dbt.clients import agate_helper  # type:ignore


def from_agate_table(table: agate.Table) -> pd.DataFrame:
    """
    Converts the given agate table to a pandas dataframe
    """
    if len(table.rows) > 0:
        column_types = [_type_from_value(val) for val in table.rows[0]]
        rows = [_from_agate_row(row, column_types) for row in table.rows]
    else:
        rows = []
    return pd.DataFrame.from_records(rows, columns=table.column_names)


def _type_from_value(value: Any) -> Any:
    """
    Returns a function to cast the value to a suitable pandas data type
    """
    if isinstance(value, decimal.Decimal):
        dec_tuple = value.as_tuple()
        if dec_tuple.exponent >= 0:
            return np.int64
        return np.float64
    return None


def _from_agate_row(row: agate.Row, column_types: List[Any]) -> List[Any]:
    """
    Converts a given agate row to a plain python row
    """
    return [column_type(val) if column_type else val for val, column_type in zip(row, column_types)]


def to_agate_table_with_path(dataframe: pd.DataFrame, path: pathlib.Path) -> agate.Table:
    """
    Converts the given pandas dataframe to an agate table
    """
    dataframe.to_csv(path, index=False)
    table = agate_helper.from_csv(path, [])
    table.original_abspath = path
    return table
