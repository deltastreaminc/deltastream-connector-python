# coding: utf-8

"""
    DeltaStream REST API

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 2.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from deltastream.api.controlplane.openapi_client.api.deltastream_api import DeltastreamApi


class TestDeltastreamApi(unittest.TestCase):
    """DeltastreamApi unit test stubs"""

    def setUp(self) -> None:
        self.api = DeltastreamApi()

    def tearDown(self) -> None:
        pass

    def test_get_statement_status(self) -> None:
        """Test case for get_statement_status

        """
        pass

    def test_get_version(self) -> None:
        """Test case for get_version

        """
        pass

    def test_submit_statement(self) -> None:
        """Test case for submit_statement

        """
        pass


if __name__ == '__main__':
    unittest.main()
