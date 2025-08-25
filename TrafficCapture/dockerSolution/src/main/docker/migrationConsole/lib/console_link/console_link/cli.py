import json
import logging
from datetime import datetime, timezone
from typing import Optional

import click
from click import ClickException

from console_link.cli_options import (
    backfill_options,
    clusters_options,
    kafka_options,
    metadata_options,
    metrics_source_options,
    metrics_target_options,
    replay_options,
    snapshot_options,
)
from console_link.environment import Environment, init_logging
from console_link.infrastructure.resource_injector import ServiceLoaderService

# Import service interfaces
from console_link.services.cluster_service import ClusterService
from console_link.services.snapshot_service import SnapshotService
from console_link.services.backfill_service import BackfillService
from console_link.services.replay_service import ReplayService
from console_link.services.metadata_service import MetadataService
from console_link.services.kafka_service import KafkaService
from console_link.services.metrics_service import MetricsService

# Import domain exceptions
from console_link.domain.exceptions.backfill_errors import BackfillError
from console_link.domain.exceptions.replay_errors import ReplayError
from console_link.domain.exceptions.metadata_errors import MetadataError
from console_link.domain.exceptions.common_errors import ServiceNotFoundError, ValidationError

logger = logging.getLogger(__name__)

# Create a single instance of the service loader
service_loader_service = ServiceLoaderService()

def _create_env(config_file: str) -> Environment:
    """Helper to create an Environment instance"""
    ctx = click.get_current_context()
    # We'll use the existing environment if it exists
    if not hasattr(ctx, 'env'):
        ctx.env = Environment(config_file)
    return ctx.env

@click.group()
@click.option("--config-file", default="/etc/migration_services.yaml", 
              help="Path to config file")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output as JSON")
@click.option("--debug", is_flag=True, default=False)
@click.pass_context
def cli(ctx, config_file, as_json, debug):
    """Migration assistant CLI"""
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    
    # Initialize environment
    environment = _create_env(config_file)
    init_logging(environment)
    
    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj['as_json'] = as_json
    ctx.obj['config_file'] = config_file
    ctx.obj['debug'] = debug
    ctx.obj['env'] = environment

# Cluster commands
@cli.group(name="clusters")
def cluster_group():
    """Cluster management commands"""
    pass

@cluster_group.command(name="cat-indices")
@click.pass_context
@clusters_options
def cat_indices_cmd(ctx, **kwargs):
    """Cat indices on a cluster"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        cluster_service = service_loader_service.load_service(
            ClusterService, environment
        )
        
        cluster_name = kwargs['cluster']
        response = cluster_service.cat_indices(cluster_name)
        
        if as_json:
            click.echo(json.dumps(response))
        else:
            click.echo(response)
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to cat indices: {e}")
        raise ClickException(f"Failed to cat indices: {str(e)}")

# Snapshot commands
@cli.group(name="snapshot")
def snapshot_group():
    """Snapshot management commands"""
    pass

@snapshot_group.command(name="create")
@click.pass_context
@snapshot_options
def create_snapshot_cmd(ctx, **kwargs):
    """Create a snapshot"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        snapshot_service = service_loader_service.load_service(
            SnapshotService, environment
        )
        
        result = snapshot_service.create_snapshot(
            snapshot_name=kwargs.get('snapshot_name'),
            source_cluster=kwargs.get('source_cluster'),
            wait=kwargs.get('wait', False)
        )
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to create snapshot: {e}")
        raise ClickException(f"Failed to create snapshot: {str(e)}")

@snapshot_group.command(name="status")
@click.pass_context
@snapshot_options
def status_snapshot_cmd(ctx, **kwargs):
    """Check the status of a snapshot"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        snapshot_service = service_loader_service.load_service(
            SnapshotService, environment
        )
        
        status = snapshot_service.get_snapshot_status(
            snapshot_name=kwargs.get('snapshot_name'),
            source_cluster=kwargs.get('source_cluster')
        )
        
        if as_json:
            click.echo(json.dumps(status))
        else:
            click.echo(json.dumps(status, indent=2))
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to get snapshot status: {e}")
        raise ClickException(f"Failed to get snapshot status: {str(e)}")

# Metadata commands
@cli.group(name="metadata")
def metadata_group():
    """Metadata migration commands"""
    pass

@metadata_group.command(name="evaluate")
@click.pass_context
@metadata_options
def evaluate_metadata_cmd(ctx, **kwargs):
    """Evaluate metadata migration"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        metadata_service = service_loader_service.load_service(
            MetadataService, environment
        )
        
        request = metadata_service.create_migrate_request(
            index_allowlist=kwargs.get('index_allowlist'),
            index_template_allowlist=kwargs.get('index_template_allowlist'),
            component_template_allowlist=kwargs.get('component_template_allowlist'),
            dry_run=True
        )
        
        status = metadata_service.evaluate(request)
        
        if as_json:
            click.echo(json.dumps(status.dict()))
        else:
            click.echo(json.dumps(status.dict(), indent=2))
    except (ServiceNotFoundError, ValidationError, MetadataError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to evaluate metadata: {e}")
        raise ClickException(f"Failed to evaluate metadata: {str(e)}")

@metadata_group.command(name="migrate")
@click.pass_context
@metadata_options
def migrate_metadata_cmd(ctx, **kwargs):
    """Migrate metadata to target cluster"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        metadata_service = service_loader_service.load_service(
            MetadataService, environment
        )
        
        request = metadata_service.create_migrate_request(
            index_allowlist=kwargs.get('index_allowlist'),
            index_template_allowlist=kwargs.get('index_template_allowlist'),
            component_template_allowlist=kwargs.get('component_template_allowlist'),
            dry_run=False
        )
        
        status = metadata_service.migrate(request)
        
        if as_json:
            click.echo(json.dumps(status.dict()))
        else:
            click.echo(json.dumps(status.dict(), indent=2))
    except (ServiceNotFoundError, ValidationError, MetadataError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to migrate metadata: {e}")
        raise ClickException(f"Failed to migrate metadata: {str(e)}")

# Backfill commands
@cli.group(name="backfill")
def backfill_group():
    """Backfill migration commands"""
    pass

@backfill_group.command(name="create")
@click.pass_context
def create_backfill_cmd(ctx):
    """Create a backfill migration"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        backfill_service = service_loader_service.load_service(
            BackfillService, environment
        )
        
        result = backfill_service.create()
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError, BackfillError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to create backfill: {e}")
        raise ClickException(f"Failed to create backfill: {str(e)}")

@backfill_group.command(name="start")
@click.pass_context
@backfill_options
def start_backfill_cmd(ctx, **kwargs):
    """Start backfill"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        backfill_service = service_loader_service.load_service(
            BackfillService, environment
        )
        
        result = backfill_service.start()
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError, BackfillError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to start backfill: {e}")
        raise ClickException(f"Failed to start backfill: {str(e)}")

@backfill_group.command(name="stop")
@click.pass_context
def stop_backfill_cmd(ctx):
    """Stop backfill"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        backfill_service = service_loader_service.load_service(
            BackfillService, environment
        )
        
        result = backfill_service.stop()
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError, BackfillError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to stop backfill: {e}")
        raise ClickException(f"Failed to stop backfill: {str(e)}")

@backfill_group.command(name="status")
@click.pass_context
@backfill_options
def status_backfill_cmd(ctx, **kwargs):
    """Get backfill status"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        backfill_service = service_loader_service.load_service(
            BackfillService, environment
        )
        
        deep_check = kwargs.get('deep_check', False)
        status, details = backfill_service.get_status(deep_check=deep_check)
        
        output = {
            "status": status.name,
            "details": details
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(f"Status: {status.name}")
            click.echo(f"Details: {details}")
    except (ServiceNotFoundError, ValidationError, BackfillError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to get backfill status: {e}")
        raise ClickException(f"Failed to get backfill status: {str(e)}")

@backfill_group.command(name="scale")
@click.argument("units", type=int)
@click.pass_context
def scale_backfill_cmd(ctx, units):
    """Scale backfill workers"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        backfill_service = service_loader_service.load_service(
            BackfillService, environment
        )
        
        result = backfill_service.scale(units)
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError, BackfillError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to scale backfill: {e}")
        raise ClickException(f"Failed to scale backfill: {str(e)}")

# Replayer commands
@cli.group(name="replay")
def replay_group():
    """Replay traffic commands"""
    pass

@replay_group.command(name="start")
@click.pass_context
@replay_options
def start_replay_cmd(ctx, **kwargs):
    """Start replaying traffic"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        replay_service = service_loader_service.load_service(
            ReplayService, environment
        )
        
        result = replay_service.start()
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError, ReplayError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to start replay: {e}")
        raise ClickException(f"Failed to start replay: {str(e)}")

@replay_group.command(name="stop")
@click.pass_context
def stop_replay_cmd(ctx):
    """Stop replaying traffic"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        replay_service = service_loader_service.load_service(
            ReplayService, environment
        )
        
        result = replay_service.stop()
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError, ReplayError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to stop replay: {e}")
        raise ClickException(f"Failed to stop replay: {str(e)}")

@replay_group.command(name="status")
@click.pass_context
def status_replay_cmd(ctx):
    """Get replayer status"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        replay_service = service_loader_service.load_service(
            ReplayService, environment
        )
        
        status, details = replay_service.get_status()
        
        output = {
            "status": status.name,
            "details": details
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(f"Status: {status.name}")
            click.echo(f"Details: {details}")
    except (ServiceNotFoundError, ValidationError, ReplayError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to get replay status: {e}")
        raise ClickException(f"Failed to get replay status: {str(e)}")

@replay_group.command(name="scale")
@click.argument("units", type=int)
@click.pass_context
def scale_replay_cmd(ctx, units):
    """Scale replay workers"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        replay_service = service_loader_service.load_service(
            ReplayService, environment
        )
        
        result = replay_service.scale(units)
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError, ReplayError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to scale replay: {e}")
        raise ClickException(f"Failed to scale replay: {str(e)}")

# Kafka commands
@cli.group(name="kafka")
def kafka_group():
    """Kafka operations"""
    pass

@kafka_group.command(name="create-topic")
@click.argument("topic_name")
@click.pass_context
def create_kafka_topic_cmd(ctx, topic_name):
    """Create a Kafka topic"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        kafka_service = service_loader_service.load_service(
            KafkaService, environment
        )
        
        result = kafka_service.create_topic(topic_name)
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to create Kafka topic: {e}")
        raise ClickException(f"Failed to create Kafka topic: {str(e)}")

@kafka_group.command(name="delete-records")
@click.argument("topic_name")
@click.pass_context
def delete_kafka_records_cmd(ctx, topic_name):
    """Delete all records from a Kafka topic"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        kafka_service = service_loader_service.load_service(
            KafkaService, environment
        )
        
        result = kafka_service.delete_records(topic_name)
        
        output = {
            "success": True,
            "message": result
        }
        
        if as_json:
            click.echo(json.dumps(output))
        else:
            click.echo(result)
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to delete Kafka records: {e}")
        raise ClickException(f"Failed to delete Kafka records: {str(e)}")

@kafka_group.command(name="describe-topic")
@click.argument("topic_name")
@click.pass_context
@kafka_options
def describe_kafka_topic_cmd(ctx, topic_name, as_yaml):
    """Describe a Kafka topic"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        kafka_service = service_loader_service.load_service(
            KafkaService, environment
        )
        
        result = kafka_service.describe_topic(topic_name, as_yaml=as_yaml)
        
        # Output is already formatted by the service
        click.echo(result)
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to describe Kafka topic: {e}")
        raise ClickException(f"Failed to describe Kafka topic: {str(e)}")

@kafka_group.command(name="describe-consumer-group")
@click.argument("group_id")
@click.pass_context
def describe_consumer_group_cmd(ctx, group_id):
    """Describe a Kafka consumer group"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        kafka_service = service_loader_service.load_service(
            KafkaService, environment
        )
        
        result = kafka_service.describe_consumer_group(group_id)
        
        # Output is already formatted by the service
        click.echo(result)
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to describe consumer group: {e}")
        raise ClickException(f"Failed to describe consumer group: {str(e)}")

# Metrics commands
@cli.group(name="metrics")
def metrics_group():
    """Metrics operations"""
    pass

@metrics_group.command(name="list")
@click.pass_context
@metrics_source_options
def list_metrics_cmd(ctx, **kwargs):
    """List available metrics"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        metrics_service = service_loader_service.load_service(
            MetricsService, environment
        )
        
        source = kwargs.get('source', 'all')
        metrics_list = metrics_service.list_metrics(source)
        
        if as_json:
            output = {
                "metrics": metrics_list,
                "source": source
            }
            click.echo(json.dumps(output))
        else:
            if source != 'all':
                click.echo(f"Metrics for {source}:")
            for metric in metrics_list:
                click.echo(f"  - {metric}")
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise ClickException(f"Failed to list metrics: {str(e)}")

@metrics_group.command(name="get")
@click.argument("metric_name")
@click.pass_context
@metrics_target_options
def get_metric_cmd(ctx, metric_name, **kwargs):
    """Get metric data"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        metrics_service = service_loader_service.load_service(
            MetricsService, environment
        )
        
        target = kwargs.get('target')
        data = metrics_service.get_metric_data(metric_name, target)
        
        if as_json:
            output = {
                "metric": metric_name,
                "target": target,
                "data": data
            }
            click.echo(json.dumps(output))
        else:
            click.echo(f"Metric: {metric_name}")
            if target:
                click.echo(f"Target: {target}")
            click.echo(json.dumps(data, indent=2))
    except (ServiceNotFoundError, ValidationError) as e:
        raise ClickException(str(e))
    except Exception as e:
        logger.error(f"Failed to get metric: {e}")
        raise ClickException(f"Failed to get metric: {str(e)}")

# Utility command for status
@cli.command()
@click.pass_context
def status(ctx):
    """Check migration status"""
    as_json = ctx.obj.get('as_json', False)
    config_file = ctx.obj.get('config_file')
    
    try:
        environment = _create_env(config_file)
        status_info = {}
        
        # Check backfill status
        try:
            backfill_service = service_loader_service.load_service(
                BackfillService, environment
            )
            backfill_status, backfill_details = backfill_service.get_status()
            status_info['backfill'] = {
                'status': backfill_status.name,
                'details': backfill_details
            }
        except ServiceNotFoundError:
            status_info['backfill'] = 'Not configured'
        except Exception as e:
            status_info['backfill'] = f'Error: {str(e)}'
        
        # Check replay status
        try:
            replay_service = service_loader_service.load_service(
                ReplayService, environment
            )
            replay_status, replay_details = replay_service.get_status()
            status_info['replay'] = {
                'status': replay_status.name,
                'details': replay_details
            }
        except ServiceNotFoundError:
            status_info['replay'] = 'Not configured'
        except Exception as e:
            status_info['replay'] = f'Error: {str(e)}'
        
        if as_json:
            click.echo(json.dumps(status_info))
        else:
            click.echo("Migration Status:")
            for component, info in status_info.items():
                click.echo(f"\n{component.capitalize()}:")
                if isinstance(info, dict):
                    click.echo(f"  Status: {info['status']}")
                    click.echo(f"  Details: {info['details']}")
                else:
                    click.echo(f"  {info}")
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise ClickException(f"Failed to get status: {str(e)}")

if __name__ == "__main__":
    cli()
