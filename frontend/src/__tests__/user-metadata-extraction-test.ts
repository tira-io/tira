import { extractCsrf } from '../utils'


function doc(html: string) {
    return new DOMParser().parseFromString(html, 'text/html')
}

test('Csrf Token can be extracted.', () => {
    let d = doc('<div><input type="hidden" name="csrfmiddlewaretoken" value="xyz"></div>')

    expect(extractCsrf(d)).toBe('xyz')
})

test('Csrf Token can be extracted and is string.', () => {
    let d = doc('<div><input type="hidden" name="csrfmiddlewaretoken" value="1234"></div>')

    expect(extractCsrf(d)).toBe('1234')
})

test('Csrf Token is empty string if not available.', () => {
    let d = doc('<div></div>')

    expect(extractCsrf(d)).toBe('')
})
