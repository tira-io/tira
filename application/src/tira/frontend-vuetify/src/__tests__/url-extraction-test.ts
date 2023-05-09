import { extractTaskFromCurrentUrl } from '../utils'

Object.defineProperty((window as Window), 'location', {
    value: {
      href: ''
    },
    writable: true // possibility to override
  });

test('Task from current Url should be Null.', () => {
    (window as Window).location.href = "http://dummy.com";
    expect(extractTaskFromCurrentUrl()).toBeNull();
});

test('Task from Url without Subpath Should be correct.', () => {
    (window as Window).location.href = 'task-overview/abc'
    expect(extractTaskFromCurrentUrl()).toStrictEqual('abc');
});

test('Task from Url with Subpath Should be correct.', () => {
    (window as Window).location.href = 'task-overview/1234/'
    expect(extractTaskFromCurrentUrl()).toStrictEqual('1234');
});