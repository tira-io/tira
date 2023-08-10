import { changeCurrentUrlToDataset } from '../utils'

Object.defineProperty((window as Window), 'location', {
    value: {
      href: ''
    },
    writable: true // possibility to override
  });

test('No history entry is added if we are not an a url without a selectable dataset (using external url).', () => {
    (window as Window).location.href = "http://dummy.com";
    changeCurrentUrlToDataset('asa')
    
    expect(history.length).toBe(1)
});

test('No history entry is added if we are not an a url without a selectable dataset (using internal url).', () => {
    (window as Window).location.href = "http://tira.io";
    changeCurrentUrlToDataset('dataset-01')
    
    expect(history.length).toBe(1)
});

test('History entry is added if we are on a url with a selectable dataset (using task 1234).', () => {
    (window as Window).location.href = "task-overview/1234/dataset-02/";
    changeCurrentUrlToDataset('dataset-01')
    expect(history.state.url).toBe("task-overview/1234/dataset-01")
});

test('History entry is added if we are on a url with a selectable dataset (using task abc).', () => {
    (window as Window).location.href = "task-overview/abc/dataset-02/";
    changeCurrentUrlToDataset('ds')
    expect(history.state.url).toBe("task-overview/abc/ds")
});

test('History entry is added if we are on a url with a selectable dataset (using task abc) and noise is removed.', () => {
    (window as Window).location.href = "task-overview/1234/dataset-02/this-is-some-noise";
    changeCurrentUrlToDataset('a')
    expect(history.state.url).toBe("task-overview/1234/a")
});
