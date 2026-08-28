---
date: 2026-05-06T08:10:21+0000
source: https://pypi.org/project/authlib/
---
[image: Build Status] [image: PyPI version] [image: conda-forge version] [image: PyPI Downloads] [image: Code Coverage] [image: Maintainability Rating]

The ultimate Python library in building OAuth and OpenID Connect servers.
JWS, JWK, JWA, JWT are included.

Authlib is compatible with Python3.10+.

## Migrations

Authlib will deprecate authlib.jose module, please read:

- Migrating from authlib.jose to joserfc

## Sponsors

| | If you want to quickly add secure token-based authentication to Python projects, feel free to check Auth0's Python SDK and free plan at auth0.com/overview. |
| | A blogging and podcast hosting platform with minimal design but powerful features. Host your blog and Podcast with Typlog.com. |

Fund Authlib to access additional features

## Features

Generic, spec-compliant implementation to build clients and providers:

- The OAuth 1.0 Protocol

 - RFC5849: The OAuth 1.0 Protocol
- The OAuth 2.0 Authorization Framework

 - RFC6749: The OAuth 2.0 Authorization Framework
 - RFC6750: The OAuth 2.0 Authorization Framework: Bearer Token Usage
 - RFC7009: OAuth 2.0 Token Revocation
 - RFC7523: JWT Profile for OAuth 2.0 Client Authentication and Authorization Grants
 - RFC7591: OAuth 2.0 Dynamic Client Registration Protocol
 - RFC7592: OAuth 2.0 Dynamic Client Registration Management Protocol
 - RFC7636: Proof Key for Code Exchange by OAuth Public Clients
 - RFC7662: OAuth 2.0 Token Introspection
 - RFC8414: OAuth 2.0 Authorization Server Metadata
 - RFC8628: OAuth 2.0 Device Authorization Grant
 - RFC9068: JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens
 - RFC9101: The OAuth 2.0 Authorization Framework: JWT-Secured Authorization Request (JAR)
 - RFC9207: OAuth 2.0 Authorization Server Issuer Identification
- Javascript Object Signing and Encryption

 - RFC7515: JSON Web Signature
 - RFC7516: JSON Web Encryption
 - RFC7517: JSON Web Key
 - RFC7518: JSON Web Algorithms
 - RFC7519: JSON Web Token
 - RFC7638: JSON Web Key (JWK) Thumbprint
 - RFC7797: JSON Web Signature (JWS) Unencoded Payload Option
 - RFC8037: ECDH in JWS and JWE
 - draft-madden-jose-ecdh-1pu-04: Public Key Authenticated Encryption for JOSE: ECDH-1PU
- OpenID Connect 1.0

 - OpenID Connect Core 1.0
 - OpenID Connect Discovery 1.0
 - OpenID Connect Dynamic Client Registration 1.0
 - OpenID Connect RP-Initiated Logout 1.0

Connect third party OAuth providers with Authlib built-in client integrations:

- Requests

 - OAuth1Session
 - OAuth2Session
 - OpenID Connect
 - AssertionSession
- HTTPX

 - AsyncOAuth1Client
 - AsyncOAuth2Client
 - OpenID Connect
 - AsyncAssertionClient
- Flask OAuth Client
- Django OAuth Client
- Starlette OAuth Client
- FastAPI OAuth Client

Build your own OAuth 1.0, OAuth 2.0, and OpenID Connect providers:

- Flask

 - Flask OAuth 1.0 Provider
 - Flask OAuth 2.0 Provider
 - Flask OpenID Connect 1.0 Provider
- Django

 - Django OAuth 1.0 Provider
 - Django OAuth 2.0 Provider
 - Django OpenID Connect 1.0 Provider

## Useful Links

1. Homepage: https://authlib.org/.
1. Documentation: https://docs.authlib.org/.
1. Purchase Commercial License: https://authlib.org/plans.
1. Blog: https://blog.authlib.org/.
1. Twitter: https://twitter.com/authlib.
1. StackOverflow: https://stackoverflow.com/questions/tagged/authlib.
1. Other Repositories: https://github.com/authlib.
1. Subscribe Tidelift: https://tidelift.com/subscription/pkg/pypi-authlib.

## Security Reporting

If you found security bugs, please do not send a public issue or patch.
You can send me email at me@lepture.com. Attachment with patch is welcome.
My PGP Key fingerprint is:

```
72F8 E895 A70C EBDF 4F2A DFE0 7E55 E3E0 118B 2B4C
```

Or, you can use the Tidelift security contact.
Tidelift will coordinate the fix and disclosure.

## License

Authlib offers two licenses:

1. BSD LICENSE
1. COMMERCIAL-LICENSE

Any project, open or closed source, can use the BSD license.
If your company needs commercial support, you can purchase a commercial license at
Authlib Plans. You can find more information at
https://authlib.org/support.
