# coding: utf-8

"""
DeltaStream Dataplane REST API

No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

The version of the OpenAPI document: 2.0.0
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""  # noqa: E501

import unittest

from deltastream.api.dataplane.openapi_client.models.version import Version


class TestVersion(unittest.TestCase):
    """Version unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> Version:
        """Test Version
        include_optional is a boolean, when False only required
        params are included, when True both required and
        optional params are included"""
        # All fields are required, so include_optional doesn't matter
        return Version(major=2, minor=0, patch=1)

    def testVersion(self):
        """Test Version basic functionality"""
        instance = self.make_instance(include_optional=False)
        self.assertEqual(instance.major, 2)
        self.assertEqual(instance.minor, 0)
        self.assertEqual(instance.patch, 1)

    def test_serialization(self):
        """Test Version serialization/deserialization"""
        data = Version(major=1, minor=2, patch=3)
        json_str = data.to_json()
        data_from_json = Version.from_json(json_str)
        self.assertEqual(data.major, data_from_json.major)
        self.assertEqual(data.minor, data_from_json.minor)
        self.assertEqual(data.patch, data_from_json.patch)

    def test_dict_conversion(self):
        """Test Version to/from dict conversion"""
        data = Version(major=2, minor=1, patch=0)
        data_dict = data.to_dict()
        data_from_dict = Version.from_dict(data_dict)
        self.assertEqual(data.major, data_from_dict.major)
        self.assertEqual(data.minor, data_from_dict.minor)
        self.assertEqual(data.patch, data_from_dict.patch)

    def test_validation(self):
        """Test Version validation rules"""
        # Test missing required field
        with self.assertRaises(ValueError):
            Version(
                major=1,
                minor=2,
                # missing patch
            )

        # Test invalid type for major
        with self.assertRaises(ValueError):
            Version(
                major="1",  # string instead of integer
                minor=0,
                patch=0,
            )

        # Test decimal values
        with self.assertRaises(ValueError):
            Version(
                major=1,
                minor=0.5,  # decimal not allowed
                patch=0,
            )

    def test_none_value(self):
        """Test Version with None value"""
        result = Version.from_dict(None)
        self.assertIsNone(result)

    def test_invalid_dict(self):
        """Test Version with invalid dict input"""
        with self.assertRaises(ValueError):
            Version.from_dict({"major": "not_an_integer", "minor": 0, "patch": 0})


if __name__ == "__main__":
    unittest.main()
