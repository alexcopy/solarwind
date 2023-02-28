import json

import jsonschema
from jsonschema import validate


class JsonValidator():
    def __int__(self, test_scheema):
        self.test_scheema = test_scheema




    @property
    def get_schema(self):
        return self.test_scheema

    def validate_json(self, json_data):

        # Describe what kind of json you expect.
        execute_api_schema = self.get_schema()

        try:
            validate(self, instance=json_data, schema=execute_api_schema)
        except jsonschema.exceptions.ValidationError as err:
            print(err)
            err = "Given JSON data is InValid"
            return False, err

        message = "Given JSON data is Valid"
        return True, message


# Convert json to python object.
jsonData = json.loads('{"id" : "10","name": "DonOfDen","contact_number":1234567890}')

# validate it
is_valid, msg = JsonValidator.validate_json(jsonData)
print(msg)
