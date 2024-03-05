REST-API Guidelines
===================

1. REST-APIs MUST be stateless
1. 404 SHOULD be used instead of 401
1. REST-APIs MUST be at least maturity level 2
1. Errors MUST be reported using [application/problem+json](https://www.rfc-editor.org/rfc/rfc7807)
1. Filtering SHOULD follow the [JSON:API](https://jsonapi.org/recommendations/#filtering)
1. Underscores SHOULD NOT be used in URIs to avoid problems when the URI is rendered underlined
1. URIs MUST be in lower kebab case
1. Parameters and fields MUST be in lower camel case following the [Google JSON Style Guide](https://google.github.io/styleguide/jsoncstyleguide.xml?showone=Property_Name_Format#Property_Name_Format)