from django.test import TestCase
from api_access_matrix import ORGANIZER
from utils_for_testing import method_for_url_pattern, mock_request, set_up_tira_environment


organizer_function = method_for_url_pattern('api/organizer-list')


class TestOrganizerList(TestCase):
    @classmethod
    def setUpClass(cls):
        set_up_tira_environment()

    def test_api_organizer_list_is_empty_for_non_existing_organizer(self):
        # Arrange
        request = mock_request('tira_org_non-existing-organizer', 'api/organizer-list')
        
        # Act
        actual = organizer_function(request)
        
        # Assert
        self.verify_as_json(actual, 'organizer_api_integration_tests/test_api_organizer_list_is_empty_for_non_existing_organizer.json')

    def test_api_organizer_list_is_non_empty_for_existing_organizer(self):
        # Arrange
        request = mock_request(ORGANIZER, 'api/organizer-list')
        
        # Act
        actual = organizer_function(request)
        
        # Assert
        self.verify_as_json(actual, 'organizer_api_integration_tests/test_api_organizer_list_is_non_empty_for_existing_organizer.json')

    def test_api_organizer_list_is_complete_for_admin(self):
        # Arrange
        request = mock_request('tira_reviewer', 'api/organizer-list')
        
        # Act
        actual = organizer_function(request)
        
        # Assert
        self.verify_as_json(actual, 'organizer_api_integration_tests/test_api_organizer_list_is_complete_for_admin.json')

    def verify_as_json(self, actual, test_name):
        from approvaltests import verify_as_json
        from approvaltests.core.options import Options
        from approvaltests.namer.cli_namer import CliNamer
        import json
        
        self.assertEqual(200, actual.status_code)
        verify_as_json(json.loads(actual.content), options=Options().with_namer(CliNamer(test_name)))

    @classmethod
    def tearDownClass(cls):
        pass

