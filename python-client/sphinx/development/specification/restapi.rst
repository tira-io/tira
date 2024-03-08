REST-API
===================

Guidelines
----------

General
^^^^^^^

#.  **REST-APIs MUST be stateless**
#.  **REST-APIs MUST be at least** `maturity level 2 <https://en.wikipedia.org/wiki/Richardson_Maturity_Model#Level_2:_HTTP_verbs>`_,

    i.e., URIs point to resources and proper HTTP verbs are used.
#.  **GET requests MUST NOT change any resource**
#.  `ULID <https://github.com/ulid/spec>`_ **SHOULD be used**
    
    when generating random unique identifiers for resources to combine the advantages of UUIDs with those of
    autoincremented primary keys (especially performance through sortability).
#.  **Resources MUST be plural names except if it is a single resource.**

    For example, ``/users/`` for all users and ``/users/1234`` for a single user with ID ``1234`` but the resource
    ``avatar`` is singular in ``/users/1234/avatar`` since a user has exactly one avatar.
#.  **Resources MUST NOT be verbs**
#.  **URIs MUST be in lower kebab case**
    
    This means especially that underscores MUST NOT be used in URIs to avoid problems when the URI underlined.
#.  **Parameters and fields MUST be in lower camel case**

    following the `Google JSON Style Guide <https://google.github.io/styleguide/jsoncstyleguide.xml?showone=Property_Name_Format#Property_Name_Format>`_

#.  **GET requests SHOULD NOT contain payload**

    This is recommended by `Mozilla <https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods/GET>`_.

#.  **The query parameter** ``fields`` **MAY be used with GET requests to only retrieve certain fields.**

    For example, the hypothetical GET request ``/users?fields=lastName,age`` returns only the last name and age of all
    users.



Errors
^^^^^^

#.  **404 SHOULD be used instead of 401**
    
    if a 401 would disclose to an unauthorized party that the resource exists
#.  **If a URL points at an existing resource, all parent URLs MUST NOT return a 404.**

    For example, if ``/users/1234`` returns a 200, then ``/users/`` must exist and cannot return 404. If it cannot be
    accessed by anyone, 403 should be returned or, if the user could access it by logging in, 401.
#.  **Endpoints MUST respond with appropriate HTTP status codes.**
#.  **Errors MUST NOT be conveyed using a 2xx HTTP status codes.**
#.  **Errors MUST be reported using** `application/problem+json <https://www.rfc-editor.org/rfc/rfc7807>`_.



Filtering and Pagination
^^^^^^^^^^^^^^^^^^^^^^^^

#.  **Big collections MUST be paginated and SHOULD be filterable**
#.  **Filtering SHOULD follow the** `JSON:API <https://jsonapi.org/recommendations/#filtering>`_
#.  **Pagination SHOULD use cursors instead of offsets if able**

    (e.g. cursor based pagination does not work with sorting)
#.  **If pagination returns no elements (possible for offset-based pagination if the offset is too large), a 204 MUST be
    returned.**
#.  **If the pagination parameters a malformed, a 400 MUST be returned.**

    This is the case for example if the cursor points to a resource that does not exist or the user does not have access
    to it or if the limit is less than or equal to 0.
#.  **PUT requests MUST update the entire resource.**

    Especially if a resource is a collection, PUT MUST set the entire colleciton.
#.  **To update only part of a resource, PATCH SHOULD be used** (`RFC 5789 <https://www.rfc-editor.org/rfc/rfc5789>`_).
#.  **To update (parts of) a resource, JSON Patch** (`RFC 6902 <https://www.rfc-editor.org/rfc/rfc6902>`_) **MAY be used.**
