JSON Web Token (JWT)
====================

.. note:: This feature is not yet implemented

For authorization, TIRA uses a "Bearer Token" (:RFC:`6750`), which can simply be thought of as a string.
The content of this string is dictated by the specific token type that is used. In our case: "JSON Web Token" ("JWT"; :RFC:`7519`). A JWT consists off three parts: A header, payload and signature. The header simply states "this is a JWT"
while the payload presents "claims". This can be, for example "My Username is: ..." (in JSON this could be, for example, ``'username': '...'``) or even "I have access to resource ...". The advantage with JWT is that the API does not need to check with the authorization or authentication server to request this information as seen in the following example:

.. uml::
   :align: center
   :caption: An unauthorized request for user information followed by a login and the same, now authorized, request. If the step ``Verify Signature`` had failed, a 401 would be returned instead of the 200. The 200 contains user information in the response body.

   @startuml
   skinparam monochrome true
   skinparam BackgroundColor #fefefe
   hide footbox

   participant Client
   participant TIRA
   participant "Auth Provider"
   actor User

   Client -> TIRA: /user
   activate TIRA
   TIRA --> Client: 401 Unauthorized
   deactivate TIRA
   Client -> "Auth Provider": Auth. Request
   activate "Auth Provider"
   "Auth Provider" <-> User: Login
   "Auth Provider" --> Client: Auth. Reponse with JWT Token
   deactivate "Auth Provider"
   Client -> TIRA: /user with JWT
   activate TIRA
   TIRA -> TIRA: Verify signature
   TIRA --> Client: 200
   deactivate TIRA

   @enduml

Here, TIRA does not need to fetch the user information (located at ``/user``) from the authentication provider since it is stored within the JWT token already. TIRA only needs to verify the signature of the JWT token to ensure it is genuine.


Example
-------
(1) Request to ``/user`` without a bearer token

    .. code:: http
    
        GET /user HTTP/2
        Host: http://example.org/
        Accept: */*
(2) Response: ``401 Unauthorized``
(3) Authentication request to authentication provider
(4) User authenticates at the authentication provider
(5) Authentication response: ``200 OK`` with a JWT
(6) Request to ``/user`` with the new token

Storing JWT
-----------

Revocation and Expiration
-------------------------
- Access and Refresh Token
- `exp` field

Explicit vs. Implicit Flow
--------------------------






Other Resources
---------------
* https://www.oauth.com/oauth2-servers/server-side-apps/authorization-code/
* https://www.oauth.com/oauth2-servers/single-page-apps/
* https://stackoverflow.blog/2021/10/06/best-practices-for-authentication-and-authorization-for-rest-apis/