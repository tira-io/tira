from tira.urls import urlpatterns

from mockito import when, mock, unstub
import inspect
from copy import deepcopy
import os

def route_to_test(url_pattern, params, groups, expected_status_code):
    method_bound_to_url_pattern = None
    mocked_request = mock()
    mocked_request.headers = {
        'X-Disraptor-App-Secret-Key': 'ignored-secret.',
        'X-Disraptor-User': 'ignored-user.',
        'X-Disraptor-Groups': groups,
    }
    mocked_request.path_info = '/' + url_pattern
    mocked_request.META = {
        'CSRF_COOKIE': 'aasa',
    }
    
    for pattern in urlpatterns:
        if str(url_pattern) == str(pattern.pattern):
            method_bound_to_url_pattern = pattern.callback
            

    assert method_bound_to_url_pattern, f'No method is bound to pattern "{url_pattern}".'
    
    params = deepcopy({} if not params else params)
    params['request'] = mocked_request
    
    return (url_pattern, method_bound_to_url_pattern, params, expected_status_code)


def execute_method_behind_url_and_return_status_code(method_bound_to_url_pattern, request):
    #print(os.path.abspath(inspect.getfile(method_bound_to_url_pattern)))
    #print(os.path.abspath(inspect.getfile(method_bound_to_url_pattern)))
    ret = method_bound_to_url_pattern(**request)
    
    if str(type(ret)) == "<class 'django.http.response.Http404'>":
        return 404
    return ret.status_code


def assert_all_url_patterns_are_tested(tested_url_patterns):
    tested_url_patterns = set(tested_url_patterns)
    for url_pattern in urlpatterns:
        assert str(url_pattern.pattern) in tested_url_patterns, f'The pattern "{url_pattern.pattern}" is not tested.'

