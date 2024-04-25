import unittest
from main import Repository

class TestExtractFieldFromReadme(unittest.TestCase):
    def setUp(self):
        self.repo = Repository('C:\\Users\\Pau\\Documents\\abpresclin\\')

    def test_Status(self):
        expected_output = 'Pendent validacions finals'
        actual_output = self.repo.extract_field_from_readme('### Status')
        self.assertEqual(expected_output, actual_output)

    def test_Correu(self):
        expected_output = 'fcsdfc@fdf.cs'
        actual_output = self.repo.extract_field_from_readme('- Correu:')
        self.assertEqual(expected_output, actual_output)
    def test_extract_nonexistent_field(self):
        expected_output = None
        actual_output = self.repo.extract_field_from_readme('Nonexistent field')
        self.assertEqual(expected_output, actual_output)

    def test_Nom(self):
        expected_output = 'JavierArranz'
        actual_output = self.repo.extract_field_from_readme('- Nom:')
        self.assertEqual(expected_output, actual_output)

    def test_Solicitud(self):
        expected_output = 'SSPT_20240206B_PRISIB_Alfonso Leiva - còpia.pdf'
        actual_output = self.repo.extract_field_from_readme('- Sol·licitud:')
        self.assertEqual(expected_output, actual_output)

    def test_Pressupost(self):
        expected_output = None
        actual_output = self.repo.extract_field_from_readme('- Pressupost:')
        self.assertEqual(expected_output, actual_output)

    def test_Codi(self):
        expected_output = '22011'
        actual_output = self.repo.extract_field_from_readme('- Codi:')
        self.assertEqual(expected_output, actual_output)

    def test_Data(self):
        expected_output = '01/12/2022'
        actual_output = self.repo.extract_field_from_readme('- Data inici:')
        self.assertEqual(expected_output, actual_output)

if __name__ == '__main__':
    unittest.main()