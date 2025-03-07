# coding: utf-8

"""
    DeltaStream Dataplane REST API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 2.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from deltastream.api.dataplane.openapi_client.models.statement_status import StatementStatus

class TestStatementStatus(unittest.TestCase):
    """StatementStatus unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> StatementStatus:
        """Test StatementStatus
            include_optional is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        if include_optional:
            return StatementStatus(
                sql_state="00000",
                message="Query completed successfully",
                statement_id="stmt_123",
                created_on=1234567890
            )
        else:
            return StatementStatus(
                sql_state="00000",
                statement_id="stmt_123",
                created_on=1234567890
            )

    def testStatementStatus(self):
        """Test StatementStatus basic functionality"""
        inst_req_only = self.make_instance(include_optional=False)
        self.assertEqual(inst_req_only.sql_state, "00000")
        self.assertIsNone(inst_req_only.message)
        
        inst_with_optional = self.make_instance(include_optional=True)
        self.assertEqual(inst_with_optional.message, "Query completed successfully")

    def test_serialization(self):
        """Test StatementStatus serialization/deserialization"""
        data = self.make_instance(include_optional=True)
        json_str = data.to_json()
        data_from_json = StatementStatus.from_json(json_str)
        self.assertEqual(data.sql_state, data_from_json.sql_state)
        self.assertEqual(data.statement_id, data_from_json.statement_id)
        self.assertEqual(data.created_on, data_from_json.created_on)
        self.assertEqual(data.message, data_from_json.message)

    def test_dict_conversion(self):
        """Test StatementStatus to/from dict conversion"""
        data = self.make_instance(include_optional=True)
        data_dict = data.to_dict()
        data_from_dict = StatementStatus.from_dict(data_dict)
        self.assertEqual(data.sql_state, data_from_dict.sql_state)
        self.assertEqual(data_dict["sqlState"], "00000")
        self.assertEqual(data_dict["statementID"], "stmt_123")

    def test_validation(self):
        """Test StatementStatus validation rules"""
        # Test missing required field
        with self.assertRaises(ValueError):
            StatementStatus(
                statement_id="stmt_123",
                created_on=1234567890
                # missing sql_state
            )

        # Test invalid created_on type
        with self.assertRaises(ValueError):
            StatementStatus(
                sql_state="00000",
                statement_id="stmt_123",
                created_on="not_a_timestamp"
            )

    def test_none_value(self):
        """Test StatementStatus with None value"""
        result = StatementStatus.from_dict(None)
        self.assertIsNone(result)

    def test_optional_message(self):
        """Test StatementStatus with optional message field"""
        # Test with message
        status_with_msg = StatementStatus(
            sql_state="00000",
            message="test message",
            statement_id="stmt_123",
            created_on=1234567890
        )
        self.assertEqual(status_with_msg.message, "test message")

        # Test without message
        status_without_msg = StatementStatus(
            sql_state="00000",
            statement_id="stmt_123",
            created_on=1234567890
        )
        self.assertIsNone(status_without_msg.message)

if __name__ == '__main__':
    unittest.main()
