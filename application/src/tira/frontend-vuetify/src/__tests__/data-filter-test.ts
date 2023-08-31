import {filterByDisplayName} from '../utils'

test('empty filter, returns all', () => {
    let images = [{"id": 1, "display_name": 'test-1'}, {"id": 2, "display_name": 'test-2'}, {
        "id": 3,
        "display_name": 'test-3'
    }];
    let expected = [{"id": 1, "display_name": 'test-1'}, {"id": 2, "display_name": 'test-2'}, {
        "id": 3,
        "display_name": 'test-3'
    }];
    expect(filterByDisplayName(images, '')).toEqual(expected);
});

test('test-1 filter, returns only the first image', () => {
    let images = [{"id": 1, "display_name": 'test-1'}, {"id": 2, "display_name": 'test-2'}, {
        "id": 3,
        "display_name": 'test-3'
    }]
    let expected = [{"id": 1, "display_name": 'test-1'}]
    expect(filterByDisplayName(images, 'test-1')).toEqual(expected);
});