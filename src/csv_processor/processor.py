import codecs
import csv
from typing import IO
from ..errors import CSVValidationError


class CSVProcessor:
    def __init__(self, file: IO) -> None:
        self.file = file
        sample_string = file.read(5000)
        sample_string = sample_string.decode()
        file.seek(0)
        self.reader = csv.DictReader(codecs.iterdecode(file, "utf-8"), dialect=self.get_dialect(sample_string))

    def get_dialect(self, sample_string):
        try:
            dialect = csv.Sniffer().sniff(sample_string, delimiters=";,")
        except csv.Error as e:
            if str(e) == "Could not determine delimiter":
                raise CSVValidationError
        return dialect

    @property
    def column_names(self):
        return self.reader.fieldnames
    
    def __iter__(self):
        return self
    
    def __next__(self):
        row = next(self.reader)
        return row
