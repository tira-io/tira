import { inject_response } from '../utils'

test('Object without keys gets nothing injected.', () => {
    let obj = Object()
    obj.$data = {}
    let default_values = {}
    let message = {'context': {'a': 1, 'b': 2}}
    
    let expected = JSON.stringify({})
    inject_response(obj, default_values)(message)

    expect(JSON.stringify(obj.$data)).toBe(expected)
});


test('Object without keys gets default values injected.', () => {
    let obj = Object()
    obj.$data = {}
    let default_values = {'c': 3, 'd': 4}
    let message = {'context': {'a': 1, 'b': 2}}
    
    let expected = JSON.stringify({'c': 3, 'd': 4})
    inject_response(obj, default_values)(message)

    expect(JSON.stringify(obj.$data)).toBe(expected)
});


test('Object with keys in response gets value injected.', () => {
    let obj = Object()
    obj.$data = {'b': 4}
    let default_values = {}
    let message = {'context': {'a': 1, 'b': 2}}
    
    let expected = JSON.stringify({'b': 2})
    inject_response(obj, default_values)(message)

    expect(JSON.stringify(obj.$data)).toBe(expected)
});

test('Object with keys in response gets value injected and default_values as well.', () => {
    let obj = Object()
    obj.$data = {'b': 4}
    let default_values = {'f': 1}
    let message = {'context': {'a': 1, 'b': 2}}
    
    let expected = JSON.stringify({'b': 2, 'f': 1})
    inject_response(obj, default_values)(message)

    expect(JSON.stringify(obj.$data)).toBe(expected)
});
