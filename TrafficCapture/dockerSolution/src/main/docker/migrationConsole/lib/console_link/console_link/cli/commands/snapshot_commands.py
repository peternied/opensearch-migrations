"""CLI commands for snapshot operations."""
import click
from typing import Optional

from console_link.services.snapshot_service import SnapshotService
from console_link.domain.exceptions.snapshot_errors import SnapshotError
from console_link.domain.entities.snapshot_entity import SnapshotType
from console_link.cli.formatters.table_formatter import TableFormatter
from console_link.cli.error_handlers import CLIErrorHandler
from console_link.shared.validators import validate_positive_integer


@click.group(name="snapshot")
@click.pass_context
def snapshot_group(ctx):
    """Commands to create and check status of snapshots of the source cluster."""
    # Get required objects from context (will be injected by main CLI)
    required_keys = ['snapshot_service', 'snapshot_config', 'source_cluster']
    for key in required_keys:
        if key not in ctx.obj:
            raise click.ClickException(f"{key} not configured")
    
    # Set up formatter and error handler
    ctx.obj['snapshot_formatter'] = TableFormatter(json_output=ctx.obj.get('json', False))
    ctx.obj['error_handler'] = CLIErrorHandler(json_output=ctx.obj.get('json', False))


@snapshot_group.command(name="create")
@click.option('--wait', is_flag=True, default=False, help='Wait for snapshot completion')
@click.option('--max-snapshot-rate-mb-per-node', type=int, default=None,
              help='Maximum snapshot rate in MB/s per node')
@click.argument('extra_args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def create_snapshot_cmd(ctx, wait: bool, max_snapshot_rate_mb_per_node: Optional[int], extra_args):
    """Create a snapshot of the source cluster."""
    service: SnapshotService = ctx.obj['snapshot_service']
    formatter: TableFormatter = ctx.obj['snapshot_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    snapshot_config = ctx.obj['snapshot_config']
    source_cluster = ctx.obj['source_cluster']
    
    try:
        # Validate rate if provided
        if max_snapshot_rate_mb_per_node is not None:
            validate_positive_integer(max_snapshot_rate_mb_per_node, "max_snapshot_rate_mb_per_node")
        
        # Determine snapshot type and create accordingly
        if 's3_config' in ctx.obj:
            # S3 snapshot
            s3_config = ctx.obj['s3_config']
            snapshot = service.create_s3_snapshot(
                config=snapshot_config,
                s3_config=s3_config,
                source_cluster=source_cluster,
                wait=wait,
                max_snapshot_rate_mb_per_node=max_snapshot_rate_mb_per_node,
                extra_args=list(extra_args)
            )
        elif 'filesystem_repo_path' in ctx.obj:
            # Filesystem snapshot
            repo_path = ctx.obj['filesystem_repo_path']
            snapshot = service.create_filesystem_snapshot(
                config=snapshot_config,
                repo_path=repo_path,
                source_cluster=source_cluster,
                max_snapshot_rate_mb_per_node=max_snapshot_rate_mb_per_node,
                extra_args=list(extra_args)
            )
        else:
            raise click.ClickException("No snapshot storage configuration found (S3 or filesystem)")
        
        # Format and display result
        click.echo(formatter.format_entity(snapshot))
        
        if wait and snapshot.state.value == "SUCCESS":
            click.echo(formatter.format_success("Snapshot created successfully"))
        elif not wait:
            click.echo(formatter.format_info("Snapshot creation initiated"))
            
    except SnapshotError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)


@snapshot_group.command(name="status")
@click.option('--deep-check', is_flag=True, default=False, help='Perform a deep status check of the snapshot')
@click.pass_context
def status_snapshot_cmd(ctx, deep_check: bool):
    """Check the status of the snapshot."""
    service: SnapshotService = ctx.obj['snapshot_service']
    formatter: TableFormatter = ctx.obj['snapshot_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    snapshot_config = ctx.obj['snapshot_config']
    source_cluster = ctx.obj['source_cluster']
    
    try:
        # Get snapshot status
        status = service.get_snapshot_status(
            snapshot_name=snapshot_config.snapshot_name,
            repository_name=snapshot_config.snapshot_repo_name,
            source_cluster=source_cluster,
            deep_check=deep_check
        )
        
        # Format and display status
        click.echo(formatter.format_status(status))
        
    except SnapshotError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)


@snapshot_group.command(name="delete")
@click.option("--acknowledge-risk", is_flag=True, show_default=True, default=False,
              help="Flag to acknowledge risk and skip confirmation")
@click.pass_context
def delete_snapshot_cmd(ctx, acknowledge_risk: bool):
    """Delete the snapshot."""
    service: SnapshotService = ctx.obj['snapshot_service']
    formatter: TableFormatter = ctx.obj['snapshot_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    snapshot_config = ctx.obj['snapshot_config']
    source_cluster = ctx.obj['source_cluster']
    
    try:
        if not acknowledge_risk:
            confirmed = click.confirm(
                'If you proceed with deleting the snapshot, the cluster will delete underlying local '
                'and remote files associated with the snapshot. Are you sure you want to continue?'
            )
            if not confirmed:
                click.echo("Aborting the command to delete snapshot.")
                return
        
        # Delete snapshot
        service.delete_snapshot(
            snapshot_name=snapshot_config.snapshot_name,
            repository_name=snapshot_config.snapshot_repo_name,
            source_cluster=source_cluster
        )
        
        click.echo(formatter.format_success("Snapshot deleted successfully"))
        
    except SnapshotError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)


@snapshot_group.command(name="unregister-repo")
@click.option("--acknowledge-risk", is_flag=True, show_default=True, default=False,
              help="Flag to acknowledge risk and skip confirmation")
@click.pass_context
def unregister_snapshot_repo_cmd(ctx, acknowledge_risk: bool):
    """Remove the snapshot repository."""
    service: SnapshotService = ctx.obj['snapshot_service']
    formatter: TableFormatter = ctx.obj['snapshot_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    snapshot_config = ctx.obj['snapshot_config']
    source_cluster = ctx.obj['source_cluster']
    
    try:
        if not acknowledge_risk:
            confirmed = click.confirm(
                'If you proceed with unregistering the snapshot repository, the cluster will '
                'deregister the existing snapshot repository but will not perform cleanup of '
                'existing snapshot files that may exist. To remove the existing snapshot files '
                '"console snapshot delete" must be used while this repository still exists. '
                'Are you sure you want to continue?'
            )
            if not confirmed:
                click.echo("Aborting the command to remove snapshot repository.")
                return
        
        # Delete repository
        service.delete_snapshot_repository(
            repository_name=snapshot_config.snapshot_repo_name,
            source_cluster=source_cluster
        )
        
        click.echo(formatter.format_success("Snapshot repository unregistered successfully"))
        
    except SnapshotError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)
