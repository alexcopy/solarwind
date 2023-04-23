#!/usr/bin/env python
import json
import sys
import unittest
import os
from unittest.mock import Mock, patch
import pytest
import jsonschema
from jsonschema import validate

sys.path.append('../')
from malina.LIB.PondPumpAuto import PondPumpAuto


class TestPondPumpAuto(PondPumpAuto):

    def __init__(self, *args, **kwargs):
        pass


class PumpValidatorTestCase(unittest.TestCase):
    def __int__(self):

        self.test_files = {}
        self.origin_schema = []
        self.result_status_schema = []

    def setUp(self) -> None:
        cwd = os.getcwd()
        self.logger = Mock()
        self.pond_pump_auto = TestPondPumpAuto(self.logger)
        files = {}
        self.dir_path = os.path.join(cwd, 'tests', 'pump_resp_json')
        for f in ['valid_pump_responce.json', 'invalid_pump_values.json', 'invalid_structure.json']:
            j_f_p = os.path.join(self.dir_path, f)
            base_name = os.path.basename(j_f_p).replace(".json", "")
            with open(j_f_p, 'r') as file:
                schema = json.load(file)
                files.update({base_name: schema})
        self.test_files = files
        with open(os.path.join(self.dir_path, 'etalon.json'), 'r') as et_file:
            self.origin_schema = json.load(et_file)

    def test_valid_structure_without_values(self):
        """REF: https://json-schema.org/ """
        # Describe what kind of json you expect.
        execute_api_schema = self.origin_schema
        try:
            for i, v in self.test_files.items():
                # checking only valid structured schemas
                if not i == 'invalid_structure':
                    validate(instance=v, schema=execute_api_schema)
                    print("Given JSON data from file %s is Valid" % i)
                # checking if schema's structure isn't valid
                else:
                    print("Given JSON data from file %s is NOT Valid" % i)
                    self.assertRaises(jsonschema.exceptions.ValidationError,
                                      validate(instance=v, schema=execute_api_schema))
        except jsonschema.exceptions.ValidationError as err:
             message = "Given JSON data is Valid"

    def test_valid_structure_with_valid_values(self):
        execute_api_schema = self.origin_schema
        try:
            with open(os.path.join(self.dir_path, 'etalon_values.json'), 'r') as et_file:
                origin_schema = json.load(et_file)
            for i, v in self.test_files.items():
                # checking only valid structured schemas
                if i == 'valid_pump_responce':
                    validate(instance=v, schema=execute_api_schema)
                    print("Given JSON data from file %s is Valid" % i)
                    self.pond_pump_auto._update_pump_status(v)
                    pump_status = self.pond_pump_auto.get_current_status
                    validate(instance=pump_status, schema=origin_schema)
        except jsonschema.exceptions.ValidationError as err:
            pytest.fail("Invalid JSON structure  ..")

    def test_valid_structure_with_invalid_values(self):
        execute_api_schema = self.origin_schema
        try:
            with open(os.path.join(self.dir_path, 'etalon_valid_values.json'), 'r') as et_file:
                origin_schema = json.load(et_file)

            for i, v in self.test_files.items():
                # checking only valid structured schemas
                if i == 'valid_pump_responce':
                    validate(instance=v, schema=execute_api_schema)
                    print("Given JSON data from file %s is Valid" % i)
                    self.pond_pump_auto._update_pump_status(v)
                    pump_status = self.pond_pump_auto.get_current_status
                    validate(instance=pump_status, schema=origin_schema)
        except jsonschema.exceptions.ValidationError as err:
            print(err)
            pytest.fail("Invalid JSON structure  ..")


if __name__ == '__main__':
    unittest.main()
