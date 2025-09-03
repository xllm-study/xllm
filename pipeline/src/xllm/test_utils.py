# test_date_parser.py


import unittest
from src.xllm.utils import normalize_date

class TestParseDate(unittest.TestCase):
    """
    Test suite for the parse_date function.
    """

    def test_full_iso_format(self):
        """Tests a standard, complete YYYY-MM-DD date."""
        self.assertEqual(normalize_date('2023-10-26'), '2023-10-26')
        self.assertEqual(normalize_date('1999-01-01'), '1999-01-01')

    def test_partial_iso_formats(self):
        """Tests partial ISO formats like YYYY and YYYY-MM."""
        self.assertEqual(normalize_date('2020'), '2020-01-01', "Should default year-only to Jan 1st")
        self.assertEqual(normalize_date('2021-05'), '2021-05-01', "Should default year-month to the 1st day")

    def test_american_format(self):
        """Tests standard mm/dd/yyyy format."""
        self.assertEqual(normalize_date('10/26/2023'), '2023-10-26')
        self.assertEqual(normalize_date('05/01/2022'), '2022-05-01')
        # Test with single-digit month and day, which strptime handles
        self.assertEqual(normalize_date('5/1/2022'), '2022-05-01')

    def test_invalid_formats(self):
        """Tests strings that do not match any known format."""
        self.assertIsNone(normalize_date('gibberish'), "Should return None for non-date strings")
        self.assertIsNone(normalize_date('26-10-2023'), "Should return None for unsupported DD-MM-YYYY")
        self.assertIsNone(normalize_date('October 26, 2023'), "Should return None for verbose date formats")
        self.assertIsNone(normalize_date('2023/10/26'), "Should return None for YYYY/MM/DD")
        
    def test_logically_invalid_dates(self):
        """Tests dates that are syntactically valid but logically impossible."""
        self.assertIsNone(normalize_date('2023-13-01'), "Should return None for an invalid month (13)")
        self.assertIsNone(normalize_date('2023-02-30'), "Should return None for an invalid day (Feb 30)")
        self.assertIsNone(normalize_date('04/31/2023'), "Should return None for an invalid day (Apr 31)")
        self.assertIsNone(normalize_date('02/29/2023'), "Should return None for a leap day in a non-leap year")

    def test_valid_leap_year(self):
        """Tests a valid leap day in a leap year."""
        self.assertEqual(normalize_date('2024-02-29'), '2024-02-29')
        self.assertEqual(normalize_date('02/29/2020'), '2020-02-29')

    def test_empty_and_none_input(self):
        """Tests handling of empty strings and None as input."""
        self.assertIsNone(normalize_date(''), "Should return None for an empty string")
        # The function signature expects a string, but we can test for robustness
        # The 'if not date_str:' check correctly handles None input.
        self.assertIsNone(normalize_date(None), "Should return None for None input") # type: ignore


# This allows the test to be run from the command line
if __name__ == '__main__':
    unittest.main(verbosity=2)