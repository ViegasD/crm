"""Construct the configured transport without connecting to an external Redis."""
import unittest
from types import SimpleNamespace

from app.workers.celery_app import celery_app


class WorkerTransportTests(unittest.TestCase):
    def test_redis_transport_constructs_with_installed_dependencies(self):
        with celery_app.connection_for_write() as connection:
            transport = connection.transport
            redis_client = transport.Channel._get_client(SimpleNamespace(global_keyprefix=""))
            self.assertTrue(callable(redis_client))
