# coding: utf-8

"""
    DeltaStream Dataplane REST API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 2.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from deltastream.api.dataplane.openapi_client.models.result_set_data_inner_inner import ResultSetDataInnerInner

class TestResultSetDataInnerInner(unittest.TestCase):
    """ResultSetDataInnerInner unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> ResultSetDataInnerInner:
        """Test ResultSetDataInnerInner"""
        if include_optional:
            return ResultSetDataInnerInner("sample_data")
        else:
            return ResultSetDataInnerInner("sample_data")

    def testResultSetDataInnerInner(self):
        """Test ResultSetDataInnerInner basic functionality"""
        inst_req = self.make_instance(include_optional=False)
        self.assertEqual(inst_req.actual_instance, "sample_data")

    def test_data_inner_inner_serialization(self):
        """Test ResultSetDataInnerInner serialization/deserialization"""
        data = ResultSetDataInnerInner("test_value")
        json_str = data.to_json()
        data_from_json = ResultSetDataInnerInner.from_json(json_str)
        self.assertEqual(data.actual_instance, data_from_json.actual_instance)

    def test_data_inner_inner_dict_conversion(self):
        """Test ResultSetDataInnerInner to/from dict conversion"""
        data = ResultSetDataInnerInner("dict_test")
        data_dict = data.to_dict()
        data_from_dict = ResultSetDataInnerInner.from_dict(data_dict)
        self.assertEqual(data.actual_instance, data_from_dict.actual_instance)
        self.assertIsInstance(data_dict, str)

    def test_data_inner_inner_none_value(self):
        """Test ResultSetDataInnerInner with None value"""
        data = ResultSetDataInnerInner(None)
        self.assertIsNone(data.actual_instance)
        self.assertEqual(data.to_json(), "null")

    def test_empty_string_value(self):
        """Test ResultSetDataInnerInner with empty string"""
        data = ResultSetDataInnerInner("")
        self.assertEqual(data.actual_instance, "")
        
    def test_invalid_type(self):
        """Test ResultSetDataInnerInner with invalid type"""
        with self.assertRaises(ValueError):
            ResultSetDataInnerInner(123)  # Should only accept strings

if __name__ == '__main__':
    unittest.main()
