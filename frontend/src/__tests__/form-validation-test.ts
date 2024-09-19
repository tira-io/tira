import { validateEmail, validateTeamName, validateNotEmpty } from '../utils'

test('Empty string is not a valid email.', () => {
    expect(validateEmail('')).toEqual('E-mail is required.');
});

test('String without @ is no valid email.', () => {
    expect(validateEmail('test.test')).toEqual('E-mail must be valid.');
});

test('String with @ and domain is valid email.', () => {
    expect(validateEmail('test@test.test')).toBeTruthy();
});

test('Empty string is not a valid team name.', () => {
    expect(validateTeamName('')).toEqual('Team name is required.');
});

test('Single character is not a valid team name.', () => {
    expect(validateTeamName('a')).toEqual('Team name must have 3 or more characters.');
});

test('35 characters are not a valid team name.', () => {
    expect(validateTeamName('123456789123456789123451234567891234567')).toEqual('Team name must be less than 30 characters.');
});

test('4 characters are a valid team name.', () => {
    expect(validateTeamName('test')).toBeTruthy();
});

test('Empty string is not valid.', () => {
    expect(validateNotEmpty('')).toEqual('This field is required.');
});

test('Non-Empty string is valid.', () => {
    expect(validateNotEmpty('a')).toBeTruthy();
});
