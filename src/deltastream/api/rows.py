from dataclasses import dataclass
from typing import List, Optional, Any
import re
import json
from decimal import Decimal
from dateutil import parser as date_parser
from deltastream.api.controlplane.openapi_client.models.result_set_data_inner_inner import (
    ResultSetDataInnerInner,
)


@dataclass
class Column:
    """Represents a database column with its metadata."""

    name: str
    type: str
    nullable: bool
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None


def castRowData(
    row_data_strings: List[ResultSetDataInnerInner], columns: List[Column]
) -> List[Any]:
    """
    Cast row data strings to their appropriate Python types based on column definitions.

    Args:
        row_data_strings: List of string values or None from the database
        columns: List of Column objects defining the data types

    Returns:
        List of values cast to their appropriate Python types
    """
    row_data: List[Any] = []

    for i, column in enumerate(columns):
        row_data_string = row_data_strings[i]
        value = row_data_string.actual_instance
        if value is None:
            row_data.append(None)
            continue

        # Split type string on <>() to handle parameterized types
        cols_type_parts = re.split(r"[<>()]", column.type)
        base_type = cols_type_parts[0]

        try:
            if base_type == "VARCHAR":
                row_data.append(value)

            elif base_type in ("TINYINT", "SMALLINT", "INTEGER"):
                row_data.append(int(value))

            elif base_type == "BIGINT":
                row_data.append(Decimal(value))

            elif base_type in ("FLOAT", "DOUBLE", "DECIMAL"):
                row_data.append(float(value))

            elif base_type in (
                "TIMESTAMP",
                "TIMESTAMP_TZ",
                "DATE",
                "TIME",
                "TIMESTAMP_LTZ",
            ):
                row_data.append(date_parser.parse(value))

            elif base_type in ("VARBINARY", "BYTES"):
                row_data.append(value)

            elif base_type in ("ARRAY", "MAP", "STRUCT"):
                row_data.append(value)

            elif base_type == "BOOLEAN":
                row_data.append(value == "true")

            else:
                print(f"Unknown type: {column.type}")
                row_data.append(value)  # Fallback to raw string

        except (ValueError, json.JSONDecodeError) as e:
            print(f'Error casting value "{value}" to type {base_type}: {str(e)}')
            row_data.append(value)  # Fallback to raw string on error

    return row_data
