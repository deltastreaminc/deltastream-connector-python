# coding: utf-8

"""
DeltaStream REST API

No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

The version of the OpenAPI document: 2.0.0
Generated by OpenAPI Generator (https://openapi-generator.tech)

Do not edit the class manually.
"""  # noqa: E501

import unittest

from deltastream.api.controlplane.openapi_client.models.version import Version


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
        return Version(major=1, minor=2, patch=3)

    def test_version_required(self):
        instance = self.make_instance(include_optional=False)
        self.assertIsInstance(instance, Version)
        self.assertEqual(instance.major, 1)
        self.assertEqual(instance.minor, 2)
        self.assertEqual(instance.patch, 3)

    def test_to_from_json(self):
        instance = self.make_instance(include_optional=True)
        json_str = instance.to_json()
        new_instance = Version.from_json(json_str)
        self.assertEqual(instance, new_instance)

    def testVersion(self):
        """Test Version"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)


if __name__ == "__main__":
    unittest.main()
