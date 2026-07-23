"""
Regression test for the Swagger "nowhere to enter my token" issue.

Without an OpenApiAuthenticationExtension registered for JWTAuthentication,
drf-spectacular has no way to know it's a bearer-token scheme, so it never
emits a securitySchemes entry and Swagger UI shows no "Authorize" button
at all.
"""
from rest_framework import status
from rest_framework.test import APITestCase


class SchemaSecuritySchemeTests(APITestCase):
    def test_schema_is_served(self):
        res = self.client.get('/api/schema/?format=json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_jwt_bearer_security_scheme_is_documented(self):
        res = self.client.get('/api/schema/?format=json')
        schema = res.json()

        security_schemes = schema['components']['securitySchemes']
        self.assertIn('jwtAuth', security_schemes)
        self.assertEqual(security_schemes['jwtAuth']['type'], 'http')
        self.assertEqual(security_schemes['jwtAuth']['scheme'], 'bearer')

    def test_an_authenticated_endpoint_requires_the_security_scheme(self):
        """
        Sanity check: an endpoint behind IsAuthenticated should actually
        reference the jwtAuth scheme in its `security` block, not just
        have the scheme sitting unused in components.
        """
        res = self.client.get('/api/schema/?format=json')
        schema = res.json()

        me_get = schema['paths']['/user/me/']['get']
        referenced_schemes = {
            name for requirement in me_get.get('security', []) for name in requirement
        }
        self.assertIn('jwtAuth', referenced_schemes)
