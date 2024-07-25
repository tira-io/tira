import { get_link_to_organizer, get_contact_link_to_organizer } from '../utils'

test('Task organizer link.', () => {
    expect(get_link_to_organizer('pan')).toBe('https://www.tira.io/g/tira_org_pan');
});

test('Task organizer contact.', () => {
    expect(get_contact_link_to_organizer('pan')).toBe('https://www.tira.io/new-message?username=tira_org_pan&title=Request%20&body=message%20body');
});

