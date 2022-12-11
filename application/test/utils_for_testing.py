from tira.urls import urlpatterns

from mockito import when, mock, unstub
import inspect
from copy import deepcopy
import os
import io
from contextlib import redirect_stdout, redirect_stderr

def __mock_request(groups, url_pattern, method):
    if 'DISRAPTOR_APP_SECRET_KEY' not in os.environ:
        os.environ['DISRAPTOR_APP_SECRET_KEY'] = 'my-disraptor-key'
    ret = mock()
    ret.headers = {
        'X-Disraptor-App-Secret-Key': 'my-disraptor-key',
        'X-Disraptor-User': 'ignored-user.',
        'X-Disraptor-Groups': groups,
    }
    ret.path_info = '/' + url_pattern
    ret.META = {
        'CSRF_COOKIE': 'aasa',
    }
    ret.current_app = 'tira'
    if method:
        ret.method = method
    
    return ret


def __find_method(url_pattern):
    method_bound_to_url_pattern = None
    
    for pattern in urlpatterns:
        if str(url_pattern) == str(pattern.pattern):
            method_bound_to_url_pattern = pattern.callback

    assert method_bound_to_url_pattern, f'No method is bound to pattern "{url_pattern}".'
    
    return method_bound_to_url_pattern


def route_to_test(url_pattern, params, groups, expected_status_code, method='GET', hide_stdout=False):
    params = deepcopy({} if not params else params)
    params['request'] = __mock_request(groups, url_pattern, method=method)
    
    return (url_pattern, __find_method(url_pattern), params, expected_status_code, hide_stdout)


def execute_method_behind_url_and_return_status_code(method_bound_to_url_pattern, request, hide_stdout):
    #print(os.path.abspath(inspect.getfile(method_bound_to_url_pattern)))
    #print(os.path.abspath(inspect.getfile(method_bound_to_url_pattern)))
    if hide_stdout:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            ret = method_bound_to_url_pattern(**request)
    else:
        ret = method_bound_to_url_pattern(**request)
    
    if str(type(ret)) == "<class 'django.http.response.Http404'>":
        return 404
    return ret.status_code


def assert_all_url_patterns_are_tested(tested_url_patterns):
    tested_url_patterns = set(tested_url_patterns)
    for url_pattern in urlpatterns:
        assert str(url_pattern.pattern) in tested_url_patterns, f'The pattern "{url_pattern.pattern}" is not tested.'

