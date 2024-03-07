REST-API Guidelines
===================

1. REST-APIs MUST be stateless
1. 404 SHOULD be used instead of 401 if a 401 would disclose to an unauthorized party that the resource exists
1. If a URL points at an existing resource, all parent URLs MUST NOT return a 404.
   For example, if `/users/1234` returns a 200, then `/users/` must exist and cannot return 404. If it cannot be
   accessed by anyone, 403 should be returned or, if the user could access it by logging in, 401.
1. Endpoints MUST respond with appropriate HTTP codes. Errors MUST NOT be conveyed using a 2xx HTTP code.
1. REST-APIs MUST be at least maturity level 2
1. When generating unique identifiers for resources, [ULID](https://github.com/ulid/spec) SHOULD be used
1. Resources MUST be plural names except if it is a single resource.
   For example, `/users/` for all users and `/users/1234` for a single user with ID `1234` but the resource "avatar" is
   singular in `/users/1234/avatar` since a user has exactly one avatar.
1. Resources MUST NOT be verbs
1. Errors MUST be reported using [application/problem+json](https://www.rfc-editor.org/rfc/rfc7807)
1. Filtering SHOULD follow the [JSON:API](https://jsonapi.org/recommendations/#filtering)
1. Underscores SHOULD NOT be used in URIs to avoid problems when the URI is rendered underlined
1. URIs MUST be in lower kebab case
1. Parameters and fields MUST be in lower camel case following the [Google JSON Style Guide](https://google.github.io/styleguide/jsoncstyleguide.xml?showone=Property_Name_Format#Property_Name_Format)
1. Big collections MUST be filterable and paginated
1. GET requests MUST NOT change any resource
1. GET requests SHOULD NOT contain payload (https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/GET)
1. The query parameter `fields` MAY be used with GET requests to only retrieve certain fields. For example, the
   hypothetical GET request `/users?fields=lastName,age` returns only the last name and age of all users.
1. PUT requests MUST update the entire resource. Especially if a resource is a collection, PUT MUST set the entire
   colleciton. To update only part of a resource, PATCH MUST be used ([RFC 5789](https://www.rfc-editor.org/rfc/rfc5789)).
1. To update (parts of) a resource, JSON Patch ([RFC 6902](https://www.rfc-editor.org/rfc/rfc6902)) MAY be used.