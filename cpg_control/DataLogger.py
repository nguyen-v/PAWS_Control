import csv
from datetime import datetime

class DataLogger:
    def __init__(self, prefix=""):
        self.fields = []
        self.data = {}
        self.decimals = {}
        self.file_name = None
        self.prefix = prefix

    def create_file(self, file_name=None):
        if file_name is None:
            if self.prefix != "":
                self.prefix = self.prefix + "_"
            self.file_name = self.prefix + datetime.now().strftime('%Y%m%d_%H%M%S') + '.csv'
        else:
            self.file_name = file_name
        with open(self.file_name, 'w', newline='') as csvfile:
            self.writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            self.writer.writeheader()

    def add_field(self, field_name, decimals=None):
        self.fields.append(field_name)
        self.data[field_name] = None
        self.decimals[field_name] = decimals

    def set_field(self, field_name, value):
        if field_name in self.fields:
            decimals = self.decimals.get(field_name)
            if decimals is not None and isinstance(value, (int, float)):
                self.data[field_name] = round(value, decimals)
            else:
                self.data[field_name] = value
        else:
            raise KeyError(f"Field '{field_name}' not found in the logger.")

    def write_line(self):
        # Ensure all fields have a value before writing
        for field in self.fields:
            if self.data[field] is None:
                raise ValueError(f"Field '{field}' has not been set.")
        try:
            with open(self.file_name, 'a', newline='') as csvfile:
                self.writer = csv.DictWriter(csvfile, fieldnames=self.fields)
                self.writer.writerow(self.data)
        except Exception as e:
            print(f"Error writing line: {e}")
            raise

    def get_file_name(self):
        return self.file_name
    
    def delete_file(self):
        import os
        try:
            os.remove(self.file_name)
        except Exception as e:
            print(f"Error deleting file: {e}")
            raise