"""CLI commands for cluster operations."""
import click
import json
from typing import Dict

from console_link.services.cluster_service import ClusterService
from console_link.domain.exceptions.cluster_errors import ClusterError
from console_link.cli.formatters.table_formatter import TableFormatter
from console_link.cli.error_handlers import CLIErrorHandler


@click.group(name="clusters")
@click.pass_context
def cluster_group(ctx):
    """Commands to interact with source and target clusters."""
    # Get cluster service from context (will be injected by main CLI)
    if 'cluster_service' not in ctx.obj:
        raise click.ClickException("Cluster service not configured")
    
    # Set up formatter and error handler
    ctx.obj['cluster_formatter'] = TableFormatter(json_output=ctx.obj.get('json', False))
    ctx.obj['error_handler'] = CLIErrorHandler(json_output=ctx.obj.get('json', False))


@cluster_group.command(name="cat-indices")
@click.option("--refresh", is_flag=True, default=False, help="Refresh cluster information")
@click.pass_context
def cat_indices_cmd(ctx, refresh: bool):
    """List indices on both source and target clusters."""
    service: ClusterService = ctx.obj['cluster_service']
    formatter: TableFormatter = ctx.obj['cluster_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    
    try:
        # Get indices from both clusters
        result = service.get_indices(refresh=refresh)
        
        if ctx.obj.get('json', False):
            # JSON output
            click.echo(json.dumps(result, indent=2))
        else:
            # Table output
            if not refresh:
                click.echo(formatter.format_warning("Cluster information may be stale. Use --refresh to update."))
                click.echo()
            
            # Source cluster indices
            click.echo("SOURCE CLUSTER")
            if result.get('source_cluster'):
                indices = result['source_cluster']
                if indices:
                    click.echo(formatter.format_list(
                        indices,
                        headers=['Index', 'Health', 'Status', 'Docs', 'Size']
                    ))
                else:
                    click.echo(formatter.format_info("No indices found"))
            else:
                click.echo(formatter.format_info("No source cluster defined"))
            
            click.echo("\nTARGET CLUSTER")
            if result.get('target_cluster'):
                indices = result['target_cluster']
                if indices:
                    click.echo(formatter.format_list(
                        indices,
                        headers=['Index', 'Health', 'Status', 'Docs', 'Size']
                    ))
                else:
                    click.echo(formatter.format_info("No indices found"))
            else:
                click.echo(formatter.format_info("No target cluster defined"))
                
    except ClusterError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)


@cluster_group.command(name="connection-check")
@click.pass_context
def connection_check_cmd(ctx):
    """Check connections to source and target clusters."""
    service: ClusterService = ctx.obj['cluster_service']
    formatter: TableFormatter = ctx.obj['cluster_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    
    try:
        # Check connections
        result = service.check_connections()
        
        if ctx.obj.get('json', False):
            # JSON output
            click.echo(json.dumps(result, indent=2))
        else:
            # Table output
            click.echo("SOURCE CLUSTER")
            source_status = result.get('source_cluster', {})
            if source_status:
                click.echo(formatter.format_entity(source_status))
            else:
                click.echo(formatter.format_info("No source cluster defined"))
            
            click.echo("\nTARGET CLUSTER")
            target_status = result.get('target_cluster', {})
            if target_status:
                click.echo(formatter.format_entity(target_status))
            else:
                click.echo(formatter.format_info("No target cluster defined"))
                
    except ClusterError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)


@cluster_group.command(name="clear-indices")
@click.option("--acknowledge-risk", is_flag=True, show_default=True, default=False,
              help="Flag to acknowledge risk and skip confirmation")
@click.option('--cluster',
              type=click.Choice(['source', 'target'], case_sensitive=False),
              help="Cluster to perform clear indices action on",
              required=True)
@click.pass_context
def clear_indices_cmd(ctx, acknowledge_risk: bool, cluster: str):
    """[Caution] Clear indices on a source or target cluster."""
    service: ClusterService = ctx.obj['cluster_service']
    formatter: TableFormatter = ctx.obj['cluster_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    
    try:
        # Validate cluster exists
        if cluster.lower() == 'source' and 'source_cluster' not in ctx.obj:
            raise click.ClickException("No source cluster defined")
        elif cluster.lower() == 'target' and 'target_cluster' not in ctx.obj:
            raise click.ClickException("No target cluster defined")
        
        if not acknowledge_risk:
            confirmed = click.confirm(
                f'Clearing indices WILL result in the loss of all data on the {cluster.lower()} cluster. '
                f'Are you sure you want to continue?'
            )
            if not confirmed:
                click.echo("Aborting command.")
                return
        
        click.echo(f"Clearing indices on {cluster.lower()} cluster...")
        
        # Clear indices
        service.clear_indices(cluster_type=cluster.lower())
        
        click.echo(formatter.format_success(f"Successfully cleared indices on {cluster.lower()} cluster"))
        
    except ClusterError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)


def parse_headers(header: str) -> Dict:
    """Parse header string into dictionary."""
    headers = {}
    for h in header:
        try:
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()
        except ValueError:
            raise click.BadParameter(f"Invalid header format: {h}. Expected format: 'Header: Value'.")
    return headers


@cluster_group.command(name="curl")
@click.option('-X', '--request', default='GET', help="HTTP method to use",
              type=click.Choice(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH']))
@click.option('-H', '--header', multiple=True, help='Pass custom header(s) to the server.')
@click.option('-d', '--data', help='Send specified data in a POST request.')
@click.option('--json', 'json_data', help='Send data as JSON.')
@click.argument('cluster', required=True, type=click.Choice(['target', 'source'], case_sensitive=False))
@click.argument('path', required=True)
@click.pass_context
def cluster_curl_cmd(ctx, cluster, path, request, header, data, json_data):
    """Execute HTTP requests against configured clusters.
    
    This implements a subset of curl commands, formatted for use against 
    configured source or target clusters.
    """
    service: ClusterService = ctx.obj['cluster_service']
    formatter: TableFormatter = ctx.obj['cluster_formatter']
    error_handler: CLIErrorHandler = ctx.obj['error_handler']
    
    try:
        headers = parse_headers(header) if header else {}
        
        if json_data:
            try:
                data = json.dumps(json.loads(json_data))
                headers['Content-Type'] = 'application/json'
            except json.JSONDecodeError:
                raise click.BadParameter("Invalid JSON format.")
        
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        # Call API
        result = service.call_cluster_api(
            cluster_type=cluster.lower(),
            path=path,
            method=request,
            headers=headers,
            data=data
        )
        
        # Display result
        if result.get('error'):
            click.echo(formatter.format_error(result['error']))
        else:
            response = result.get('response', {})
            if not response.get('ok', True):
                click.echo(f"Error: {response.get('status_code', 'Unknown')}")
            
            click.echo(response.get('text', ''))
            
    except ClusterError as e:
        error_handler.handle_error(e)
    except Exception as e:
        error_handler.handle_error(e)
