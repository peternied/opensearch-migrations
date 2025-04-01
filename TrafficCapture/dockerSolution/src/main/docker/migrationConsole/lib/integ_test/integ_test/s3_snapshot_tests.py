import logging
import pytest
import unittest
from http import HTTPStatus
from console_link.middleware.clusters import connection_check, clear_cluster, ConnectionResult
from console_link.models.cluster import Cluster
from console_link.models.backfill_base import Backfill
from console_link.models.command_result import CommandResult
from console_link.models.metadata import Metadata
from console_link.cli import Context
from .common_utils import EXPECTED_BENCHMARK_DOCS
from .default_operations import DefaultOperationsLibrary

logger = logging.getLogger(__name__)
ops = DefaultOperationsLibrary()


@pytest.fixture(scope="class")
def setup_external_snapshot_backfill(request):
    config_path = request.config.getoption("--config_file_path")
    unique_id = request.config.getoption("--unique_id")
    pytest.console_env = Context(config_path).env
    pytest.unique_id = unique_id
    
    # Only need to verify target cluster connection since we're using an external snapshot
    target_cluster: Cluster = pytest.console_env.target_cluster
    target_con_result: ConnectionResult = connection_check(target_cluster)
    assert target_con_result.connection_established is True
    
    # Clear target cluster to ensure clean state
    clear_cluster(target_cluster)
    
    backfill: Backfill = pytest.console_env.backfill
    assert backfill is not None
    metadata: Metadata = pytest.console_env.metadata
    assert metadata is not None

    # Start the backfill process using the external snapshot
    backfill.create()
    metadata_result: CommandResult = metadata.migrate()
    assert metadata_result.success
    backfill_start_result: CommandResult = backfill.start()
    assert backfill_start_result.success
    # Scale to 2 units for better performance
    backfill_scale_result: CommandResult = backfill.scale(units=2)
    assert backfill_scale_result.success


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    # Setup code
    logger.info("Starting external snapshot backfill tests...")

    yield

    # Teardown code
    logger.info("Stopping backfill...")
    backfill: Backfill = pytest.console_env.backfill
    backfill.stop()


@pytest.mark.usefixtures("setup_external_snapshot_backfill")
class ExternalSnapshotBackfillTests(unittest.TestCase):

    def test_external_snapshot_backfill_indices(self):
        """Test that indices from the external snapshot are properly migrated to the target cluster"""
        target_cluster: Cluster = pytest.console_env.target_cluster
        
        # Wait for indices to appear in the target cluster
        # This assumes the external snapshot contains at least one index
        # The test will pass if any indices are found in the target cluster
        indices = ops.get_indices(cluster=target_cluster, max_attempts=30, delay=30.0)
        self.assertTrue(len(indices) > 0, "No indices found in target cluster after backfill")
        logger.info(f"Found {len(indices)} indices in target cluster: {', '.join(indices)}")
        
        # Check that each index has documents
        for index in indices:
            doc_count = ops.get_doc_count(cluster=target_cluster, index_name=index)
            logger.info(f"Index {index} has {doc_count} documents")
            self.assertTrue(doc_count > 0, f"No documents found in index {index}")
