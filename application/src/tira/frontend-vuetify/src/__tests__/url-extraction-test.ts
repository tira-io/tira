import { extractTaskFromCurrentUrl, extractDatasetFromCurrentUrl, extractSubView, extractSubSubView } from '../utils'

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

test('Task from Url without Subpath Should be correct with question mark.', () => {
  (window as Window).location.href = 'task-overview/abc?sada'
  expect(extractTaskFromCurrentUrl()).toStrictEqual('abc');
});

test('Task from Url without Subpath Should be correct with # symbol.', () => {
  (window as Window).location.href = 'task-overview/abc#sa'
  expect(extractTaskFromCurrentUrl()).toStrictEqual('abc');
});

test('Task from Url with Subpath Should be correct.', () => {
    (window as Window).location.href = 'task-overview/1234/'
    expect(extractTaskFromCurrentUrl()).toStrictEqual('1234');
});

test('Dataset from Url without dataset should be the empty string.', () => {
  (window as Window).location.href = 'task-overview/abc/'
  expect(extractDatasetFromCurrentUrl()).toStrictEqual('');
});

test('Dataset from current Url should be Null.', () => {
  (window as Window).location.href = "http://dummy.com";
  expect(extractDatasetFromCurrentUrl()).toStrictEqual('');
});

test('Dataset from Url without dataset should be the empty string even when not exists.', () => {
  (window as Window).location.href = 'task-overview/1234'
  expect(extractDatasetFromCurrentUrl()).toStrictEqual('');
});

test('Dataset from Url without Subpath Should be correct.', () => {
  (window as Window).location.href = 'task-overview/abc/ds'
  expect(extractDatasetFromCurrentUrl()).toStrictEqual('ds');
});

test('Dataset from Url without Subpath Should be correct with question mark.', () => {
  (window as Window).location.href = 'task-overview/abc/ds?xy=1'
  expect(extractDatasetFromCurrentUrl()).toStrictEqual('ds');
});

test('Dataset from Url without Subpath Should be correct with # symbol.', () => {
  (window as Window).location.href = 'task-overview/abc/ds#asdad'
  expect(extractDatasetFromCurrentUrl()).toStrictEqual('ds');
});

test('Dataset from Url with Subpath Should be correct.', () => {
  (window as Window).location.href = 'task-overview/1234/dataset-01/'
  expect(extractDatasetFromCurrentUrl()).toStrictEqual('dataset-01');
});

test('Dataset is extracted with precedence from the default_choice if available.', () => {
  (window as Window).location.href = 'task-overview/abc/ds'

  let options = [{'dataset_id': 'ds'}, {'dataset_id': 'something-is-selected'}, {'dataset_id': 'ds2'}]
  let selectedDataset = 'something-is-selected'

  expect(extractDatasetFromCurrentUrl(options, selectedDataset)).toStrictEqual('something-is-selected');
});

test('First Dataset is extracted if the default_choice is not available.', () => {
  (window as Window).location.href = 'task-overview/abc'

  let options = [{'dataset_id': 'ds'}, {'dataset_id': 'something-is-selected'}, {'dataset_id': 'ds2'}]
  let selectedDataset = 'does-not-exist'

  expect(extractDatasetFromCurrentUrl(options, selectedDataset)).toStrictEqual('ds');
});


test('Dataset from URL is extracted if default_choice is wrong.', () => {
  (window as Window).location.href = 'task-overview/abc/ds2'

  let options = [{'dataset_id': 'ds'}, {'dataset_id': 'something-is-selected'}, {'dataset_id': 'ds2'}]
  let selectedDataset = 'does-not-exist'

  expect(extractDatasetFromCurrentUrl(options, selectedDataset)).toStrictEqual('ds2');
});

test('Dataset from URL is extracted if no default_choice is available.', () => {
  (window as Window).location.href = 'task-overview/abc/ds2'

  let options = [{'dataset_id': 'ds'}, {'dataset_id': 'something-is-selected'}, {'dataset_id': 'ds2'}]
  let selectedDataset = ''

  expect(extractDatasetFromCurrentUrl(options, selectedDataset)).toStrictEqual('ds2');
});


test('First dataset is used if dataset from URL does not exist.', () => {
  (window as Window).location.href = 'task-overview/abc/ds2'

  let options = [{'dataset_id': 'ds'}, {'dataset_id': 'something-is-selected'}, {'dataset_id': 'ds22'}]
  let selectedDataset = ''

  expect(extractDatasetFromCurrentUrl(options, selectedDataset)).toStrictEqual('ds');
});

test('First dataset is used if dataset from URL does not exist and default_choise is wrong.', () => {
  (window as Window).location.href = 'task-overview/abc/ds2'

  let options = [{'dataset_id': 'ds'}, {'dataset_id': 'something-is-selected'}, {'dataset_id': 'ds3'}]
  let selectedDataset = 'does-not-exist'

  expect(extractDatasetFromCurrentUrl(options, selectedDataset)).toStrictEqual('ds');
});

test('No sub-view and sub-sub-view exist 1.', () => {
  (window as Window).location.href = 'task-overview/1234/'
  expect(extractSubView()).toBeNull;
  expect(extractSubSubView()).toBeNull;
});

test('No sub-view and sub-sub-view exist 2.', () => {
  (window as Window).location.href = 'task-overview/1234/23'
  expect(extractSubView()).toBeNull;
  expect(extractSubSubView()).toBeNull;
});

test('No sub-view and sub-sub-view exist 2.', () => {
  (window as Window).location.href = 'dummy/1234/23/hello/world/how'
  expect(extractSubView()).toBeNull;
  expect(extractSubSubView()).toBeNull;
});

test('Sub-view exists but no sub-sub-view 1.', () => {
  (window as Window).location.href = 'task-overview/1234/23/sub-view-1'
  expect(extractSubView()).toStrictEqual('sub-view-1');
  expect(extractSubSubView()).toBeNull;
});

test('Sub-view exists but no sub-sub-view 2.', () => {
  (window as Window).location.href = 'task-overview/1234/23/1234'
  expect(extractSubView()).toStrictEqual('1234');
  expect(extractSubSubView()).toBeNull;
});

test('Sub-view exists and sub-sub-view 1.', () => {
  (window as Window).location.href = 'task-overview/1234/23/1234/sub-sub-view'
  expect(extractSubView()).toStrictEqual('1234');
  expect(extractSubSubView()).toStrictEqual('sub-sub-view');
});

test('Sub-view exists and sub-sub-view 1.', () => {
  (window as Window).location.href = 'task-overview/1234/23/1234/sub-sub-view'
  expect(extractSubView()).toStrictEqual('1234');
  expect(extractSubSubView()).toStrictEqual('sub-sub-view');
});