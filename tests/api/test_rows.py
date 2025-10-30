"""
Tests for rows.py module - specifically the castRowData function
"""

from unittest.mock import MagicMock
from datetime import datetime
from decimal import Decimal
from deltastream.api.rows import castRowData, Column
from deltastream.api.controlplane.openapi_client.models.result_set_data_inner_inner import (
    ResultSetDataInnerInner,
)


class TestCastRowDataWithResultSetDataInnerInner:
    """Test castRowData with ResultSetDataInnerInner objects (original behavior)"""

    def test_cast_varchar_with_result_set_object(self):
        """Test casting VARCHAR with ResultSetDataInnerInner object"""
        columns = [Column(name="name", type="VARCHAR", nullable=True)]

        # Create mock ResultSetDataInnerInner object
        mock_data = MagicMock(spec=ResultSetDataInnerInner)
        mock_data.actual_instance = "John Doe"

        result = castRowData([mock_data], columns)

        assert len(result) == 1
        assert result[0] == "John Doe"

    def test_cast_integer_with_result_set_object(self):
        """Test casting INTEGER with ResultSetDataInnerInner object"""
        columns = [Column(name="age", type="INTEGER", nullable=True)]

        mock_data = MagicMock(spec=ResultSetDataInnerInner)
        mock_data.actual_instance = "42"

        result = castRowData([mock_data], columns)

        assert len(result) == 1
        assert result[0] == 42
        assert isinstance(result[0], int)

    def test_cast_bigint_with_result_set_object(self):
        """Test casting BIGINT with ResultSetDataInnerInner object"""
        columns = [Column(name="big_number", type="BIGINT", nullable=True)]

        mock_data = MagicMock(spec=ResultSetDataInnerInner)
        mock_data.actual_instance = "9223372036854775807"

        result = castRowData([mock_data], columns)

        assert len(result) == 1
        assert result[0] == Decimal("9223372036854775807")
        assert isinstance(result[0], Decimal)

    def test_cast_float_with_result_set_object(self):
        """Test casting FLOAT with ResultSetDataInnerInner object"""
        columns = [Column(name="price", type="FLOAT", nullable=True)]

        mock_data = MagicMock(spec=ResultSetDataInnerInner)
        mock_data.actual_instance = "3.14159"

        result = castRowData([mock_data], columns)

        assert len(result) == 1
        assert abs(result[0] - 3.14159) < 0.00001
        assert isinstance(result[0], float)

    def test_cast_boolean_with_result_set_object(self):
        """Test casting BOOLEAN with ResultSetDataInnerInner object"""
        columns = [
            Column(name="is_active", type="BOOLEAN", nullable=True),
            Column(name="is_deleted", type="BOOLEAN", nullable=True),
        ]

        mock_data_true = MagicMock(spec=ResultSetDataInnerInner)
        mock_data_true.actual_instance = "true"

        mock_data_false = MagicMock(spec=ResultSetDataInnerInner)
        mock_data_false.actual_instance = "false"

        result = castRowData([mock_data_true, mock_data_false], columns)

        assert len(result) == 2
        assert result[0] is True
        assert result[1] is False

    def test_cast_null_with_result_set_object(self):
        """Test casting NULL values with ResultSetDataInnerInner object"""
        columns = [Column(name="optional_field", type="VARCHAR", nullable=True)]

        mock_data = MagicMock(spec=ResultSetDataInnerInner)
        mock_data.actual_instance = None

        result = castRowData([mock_data], columns)

        assert len(result) == 1
        assert result[0] is None


class TestCastRowDataWithPlainValues:
    """Test castRowData with plain values from WebSocket (new behavior)"""

    def test_cast_varchar_with_plain_string(self):
        """Test casting VARCHAR with plain string value"""
        columns = [Column(name="name", type="VARCHAR", nullable=True)]

        result = castRowData(["John Doe"], columns)

        assert len(result) == 1
        assert result[0] == "John Doe"

    def test_cast_integer_with_plain_string(self):
        """Test casting INTEGER with plain string value"""
        columns = [Column(name="age", type="INTEGER", nullable=True)]

        result = castRowData(["42"], columns)

        assert len(result) == 1
        assert result[0] == 42
        assert isinstance(result[0], int)

    def test_cast_bigint_with_plain_string(self):
        """Test casting BIGINT with plain string value"""
        columns = [Column(name="big_number", type="BIGINT", nullable=True)]

        result = castRowData(["9223372036854775807"], columns)

        assert len(result) == 1
        assert result[0] == Decimal("9223372036854775807")
        assert isinstance(result[0], Decimal)

    def test_cast_float_with_plain_string(self):
        """Test casting FLOAT with plain string value"""
        columns = [Column(name="price", type="FLOAT", nullable=True)]

        result = castRowData(["3.14159"], columns)

        assert len(result) == 1
        assert abs(result[0] - 3.14159) < 0.00001
        assert isinstance(result[0], float)

    def test_cast_double_with_plain_string(self):
        """Test casting DOUBLE with plain string value"""
        columns = [Column(name="measurement", type="DOUBLE", nullable=True)]

        result = castRowData(["123.456789"], columns)

        assert len(result) == 1
        assert abs(result[0] - 123.456789) < 0.000001
        assert isinstance(result[0], float)

    def test_cast_decimal_with_plain_string(self):
        """Test casting DECIMAL with plain string value"""
        columns = [Column(name="amount", type="DECIMAL", nullable=True)]

        result = castRowData(["99.99"], columns)

        assert len(result) == 1
        assert abs(result[0] - 99.99) < 0.01
        assert isinstance(result[0], float)

    def test_cast_boolean_true_with_plain_string(self):
        """Test casting BOOLEAN true with plain string value"""
        columns = [Column(name="is_active", type="BOOLEAN", nullable=True)]

        result = castRowData(["true"], columns)

        assert len(result) == 1
        assert result[0] is True

    def test_cast_boolean_false_with_plain_string(self):
        """Test casting BOOLEAN false with plain string value"""
        columns = [Column(name="is_deleted", type="BOOLEAN", nullable=True)]

        result = castRowData(["false"], columns)

        assert len(result) == 1
        assert result[0] is False

    def test_cast_null_with_plain_value(self):
        """Test casting NULL values with plain None value"""
        columns = [Column(name="optional_field", type="VARCHAR", nullable=True)]

        result = castRowData([None], columns)

        assert len(result) == 1
        assert result[0] is None

    def test_cast_tinyint_with_plain_string(self):
        """Test casting TINYINT with plain string value"""
        columns = [Column(name="small_number", type="TINYINT", nullable=True)]

        result = castRowData(["127"], columns)

        assert len(result) == 1
        assert result[0] == 127
        assert isinstance(result[0], int)

    def test_cast_smallint_with_plain_string(self):
        """Test casting SMALLINT with plain string value"""
        columns = [Column(name="medium_number", type="SMALLINT", nullable=True)]

        result = castRowData(["32767"], columns)

        assert len(result) == 1
        assert result[0] == 32767
        assert isinstance(result[0], int)


class TestCastRowDataMixedTypes:
    """Test castRowData with mixed ResultSetDataInnerInner objects and plain values"""

    def test_cast_multiple_columns_with_result_set_objects(self):
        """Test casting multiple columns with ResultSetDataInnerInner objects"""
        columns = [
            Column(name="id", type="INTEGER", nullable=False),
            Column(name="name", type="VARCHAR", nullable=True),
            Column(name="price", type="FLOAT", nullable=True),
            Column(name="is_active", type="BOOLEAN", nullable=True),
        ]

        mock_data = [
            MagicMock(spec=ResultSetDataInnerInner),
            MagicMock(spec=ResultSetDataInnerInner),
            MagicMock(spec=ResultSetDataInnerInner),
            MagicMock(spec=ResultSetDataInnerInner),
        ]

        mock_data[0].actual_instance = "123"
        mock_data[1].actual_instance = "Product A"
        mock_data[2].actual_instance = "19.99"
        mock_data[3].actual_instance = "true"

        result = castRowData(mock_data, columns)

        assert len(result) == 4
        assert result[0] == 123
        assert result[1] == "Product A"
        assert abs(result[2] - 19.99) < 0.01
        assert result[3] is True

    def test_cast_multiple_columns_with_plain_values(self):
        """Test casting multiple columns with plain values (WebSocket scenario)"""
        columns = [
            Column(name="id", type="INTEGER", nullable=False),
            Column(name="name", type="VARCHAR", nullable=True),
            Column(name="price", type="FLOAT", nullable=True),
            Column(name="is_active", type="BOOLEAN", nullable=True),
        ]

        plain_data = ["123", "Product A", "19.99", "true"]

        result = castRowData(plain_data, columns)

        assert len(result) == 4
        assert result[0] == 123
        assert result[1] == "Product A"
        assert abs(result[2] - 19.99) < 0.01
        assert result[3] is True

    def test_cast_with_null_values_mixed(self):
        """Test casting with NULL values in mixed data"""
        columns = [
            Column(name="id", type="INTEGER", nullable=False),
            Column(name="optional_name", type="VARCHAR", nullable=True),
            Column(name="optional_price", type="FLOAT", nullable=True),
        ]

        # Test with ResultSetDataInnerInner objects
        mock_data = [
            MagicMock(spec=ResultSetDataInnerInner),
            MagicMock(spec=ResultSetDataInnerInner),
            MagicMock(spec=ResultSetDataInnerInner),
        ]

        mock_data[0].actual_instance = "123"
        mock_data[1].actual_instance = None
        mock_data[2].actual_instance = "19.99"

        result = castRowData(mock_data, columns)

        assert len(result) == 3
        assert result[0] == 123
        assert result[1] is None
        assert abs(result[2] - 19.99) < 0.01

        # Test with plain values
        plain_data = ["456", None, "29.99"]

        result2 = castRowData(plain_data, columns)

        assert len(result2) == 3
        assert result2[0] == 456
        assert result2[1] is None
        assert abs(result2[2] - 29.99) < 0.01


class TestCastRowDataTimestamps:
    """Test timestamp handling with both object types"""

    def test_cast_timestamp_with_result_set_object(self):
        """Test casting TIMESTAMP with ResultSetDataInnerInner object"""
        columns = [Column(name="created_at", type="TIMESTAMP", nullable=True)]

        mock_data = MagicMock(spec=ResultSetDataInnerInner)
        mock_data.actual_instance = "2023-01-15T10:30:00"

        result = castRowData([mock_data], columns)

        assert len(result) == 1
        assert isinstance(result[0], datetime)
        assert result[0].year == 2023
        assert result[0].month == 1
        assert result[0].day == 15

    def test_cast_timestamp_with_plain_string(self):
        """Test casting TIMESTAMP with plain string value"""
        columns = [Column(name="created_at", type="TIMESTAMP", nullable=True)]

        result = castRowData(["2023-01-15T10:30:00"], columns)

        assert len(result) == 1
        assert isinstance(result[0], datetime)
        assert result[0].year == 2023
        assert result[0].month == 1
        assert result[0].day == 15

    def test_cast_timestamp_tz_with_plain_string(self):
        """Test casting TIMESTAMP_TZ with plain string value"""
        columns = [Column(name="event_time", type="TIMESTAMP_TZ", nullable=True)]

        result = castRowData(["2023-01-15T10:30:00Z"], columns)

        assert len(result) == 1
        assert isinstance(result[0], datetime)

    def test_cast_date_with_plain_string(self):
        """Test casting DATE with plain string value"""
        columns = [Column(name="birth_date", type="DATE", nullable=True)]

        result = castRowData(["2023-01-15"], columns)

        assert len(result) == 1
        assert isinstance(result[0], datetime)


class TestCastRowDataComplexTypes:
    """Test complex types (ARRAY, MAP, STRUCT) handling"""

    def test_cast_array_with_plain_value(self):
        """Test casting ARRAY type with plain value"""
        columns = [Column(name="tags", type="ARRAY<VARCHAR>", nullable=True)]

        # Arrays come as JSON strings from WebSocket
        result = castRowData(['["tag1", "tag2", "tag3"]'], columns)

        assert len(result) == 1
        # Complex types are returned as-is (string)
        assert result[0] == '["tag1", "tag2", "tag3"]'

    def test_cast_map_with_plain_value(self):
        """Test casting MAP type with plain value"""
        columns = [Column(name="metadata", type="MAP<VARCHAR, VARCHAR>", nullable=True)]

        result = castRowData(['{"key1": "value1", "key2": "value2"}'], columns)

        assert len(result) == 1
        # Complex types are returned as-is (string)
        assert result[0] == '{"key1": "value1", "key2": "value2"}'

    def test_cast_struct_with_plain_value(self):
        """Test casting STRUCT type with plain value"""
        columns = [
            Column(
                name="address",
                type="STRUCT<street VARCHAR, city VARCHAR>",
                nullable=True,
            )
        ]

        result = castRowData(['{"street": "123 Main St", "city": "New York"}'], columns)

        assert len(result) == 1
        # Complex types are returned as-is (string)
        assert result[0] == '{"street": "123 Main St", "city": "New York"}'


class TestCastRowDataBinaryTypes:
    """Test binary types (VARBINARY, BYTES) handling"""

    def test_cast_varbinary_with_plain_value(self):
        """Test casting VARBINARY with plain value"""
        columns = [Column(name="binary_data", type="VARBINARY", nullable=True)]

        result = castRowData(["binary_content"], columns)

        assert len(result) == 1
        assert result[0] == "binary_content"

    def test_cast_bytes_with_plain_value(self):
        """Test casting BYTES with plain value"""
        columns = [Column(name="file_content", type="BYTES", nullable=True)]

        result = castRowData(["file_bytes"], columns)

        assert len(result) == 1
        assert result[0] == "file_bytes"


class TestCastRowDataEdgeCases:
    """Test edge cases and error handling"""

    def test_cast_unknown_type_with_plain_value(self, capsys):
        """Test casting unknown type returns raw value with warning"""
        columns = [Column(name="unknown_field", type="UNKNOWN_TYPE", nullable=True)]

        result = castRowData(["some_value"], columns)

        assert len(result) == 1
        assert result[0] == "some_value"

        # Check that warning was printed
        captured = capsys.readouterr()
        assert "Unknown type: UNKNOWN_TYPE" in captured.out

    def test_cast_invalid_integer_falls_back_to_string(self, capsys):
        """Test that invalid integer value falls back to raw string"""
        columns = [Column(name="age", type="INTEGER", nullable=True)]

        result = castRowData(["not_a_number"], columns)

        assert len(result) == 1
        assert result[0] == "not_a_number"

        # Check that error was printed
        captured = capsys.readouterr()
        assert "Error casting value" in captured.out

    def test_cast_invalid_float_falls_back_to_string(self, capsys):
        """Test that invalid float value falls back to raw string"""
        columns = [Column(name="price", type="FLOAT", nullable=True)]

        result = castRowData(["invalid_float"], columns)

        assert len(result) == 1
        assert result[0] == "invalid_float"

        # Check that error was printed
        captured = capsys.readouterr()
        assert "Error casting value" in captured.out

    def test_cast_empty_column_list(self):
        """Test casting with empty column list"""
        columns = []

        result = castRowData([], columns)

        assert len(result) == 0

    def test_hasattr_check_with_object_without_actual_instance(self):
        """Test that objects without actual_instance are treated as plain values"""
        columns = [Column(name="value", type="VARCHAR", nullable=True)]

        # Object without actual_instance attribute
        plain_obj = "plain_string"

        result = castRowData([plain_obj], columns)

        assert len(result) == 1
        assert result[0] == "plain_string"
