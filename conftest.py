"""
Root pytest conftest.

Defaults the test run to an in-memory SQLite database (see
freelancercrib/settings.py) so `pytest` works without a Postgres/
docker-compose stack running. This must be set before Django settings
are imported, which is why it lives at the very top of the rootdir
conftest rather than in a fixture.

Set DJANGO_TEST_SQLITE=false explicitly (e.g. in CI) to run the suite
against a real Postgres instance instead.
"""
import os

os.environ.setdefault('DJANGO_TEST_SQLITE', 'true')
