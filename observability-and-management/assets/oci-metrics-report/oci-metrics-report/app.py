"""
OCI Monitoring Metrics Report Generator

This Flask application provides a web interface for querying and visualizing
OCI Monitoring metrics using the OCI SDK and MQL (Monitoring Query Language).

Supports multiple authentication methods:
- OCI Config File (default)
- Instance Principal (for CloudShell, OCI Compute instances)
- Resource Principal (for OCI Functions)
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

import oci
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dateutil import parser as date_parser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app)


class AuthType(Enum):
    """Supported OCI authentication types."""
    CONFIG_FILE = "config_file"
    INSTANCE_PRINCIPAL = "instance_principal"
    RESOURCE_PRINCIPAL = "resource_principal"
    SECURITY_TOKEN = "security_token"  # For CloudShell with delegation token


def detect_auth_type() -> AuthType:
    """
    Automatically detect the best authentication method based on environment.

    Detection order:
    1. OCI_CLI_AUTH=instance_principal -> Instance Principal
    2. OCI_RESOURCE_PRINCIPAL_VERSION set -> Resource Principal
    3. OCI_CLI_AUTH=security_token -> Security Token (CloudShell)
    4. Default -> Config File
    """
    oci_cli_auth = os.environ.get("OCI_CLI_AUTH", "").lower()

    if oci_cli_auth == "instance_principal":
        return AuthType.INSTANCE_PRINCIPAL

    if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        return AuthType.RESOURCE_PRINCIPAL

    if oci_cli_auth == "security_token":
        return AuthType.SECURITY_TOKEN

    # Check if running in CloudShell by looking for delegation token
    if os.environ.get("OCI_CLI_CLOUD_SHELL"):
        return AuthType.SECURITY_TOKEN

    return AuthType.CONFIG_FILE


def get_signer(auth_type: AuthType, config_file: str = "~/.oci/config",
               profile: str = "DEFAULT") -> tuple:
    """
    Get the appropriate signer and config based on authentication type.

    Returns:
        Tuple of (config_dict, signer) for use with OCI clients
    """
    if auth_type == AuthType.INSTANCE_PRINCIPAL:
        logger.info("Using Instance Principal authentication")
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        config = {"region": signer.region}
        return config, signer

    elif auth_type == AuthType.RESOURCE_PRINCIPAL:
        logger.info("Using Resource Principal authentication")
        signer = oci.auth.signers.get_resource_principals_signer()
        config = {"region": signer.region}
        return config, signer

    elif auth_type == AuthType.SECURITY_TOKEN:
        logger.info("Using Security Token authentication (CloudShell)")
        config = oci.config.from_file(config_file, profile)
        token_file = config.get("security_token_file")
        key_file = config.get("key_file")

        if token_file and os.path.exists(os.path.expanduser(token_file)):
            with open(os.path.expanduser(token_file), 'r') as f:
                token = f.read().strip()

            private_key = oci.signer.load_private_key_from_file(
                os.path.expanduser(key_file)
            )
            signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
            return config, signer
        else:
            # Fall back to config file auth
            logger.warning("Security token not found, falling back to config file auth")
            return oci.config.from_file(config_file, profile), None

    else:  # CONFIG_FILE
        logger.info("Using Config File authentication")
        config = oci.config.from_file(config_file, profile)
        return config, None


class OCIMonitoringClient:
    """
    Client for interacting with OCI Monitoring service.

    Handles authentication and provides methods for:
    - Listing compartments
    - Listing metric namespaces
    - Listing metrics within a namespace
    - Querying metric data using MQL

    Supports multiple authentication methods:
    - OCI Config File
    - Instance Principal (for compute instances, CloudShell)
    - Resource Principal (for OCI Functions)
    - Security Token (for CloudShell delegation)
    """

    def __init__(self, config_file: str = "~/.oci/config", profile: str = "DEFAULT",
                 auth_type: AuthType = None, region: str = None):
        """
        Initialize the OCI Monitoring client.

        Args:
            config_file: Path to OCI config file (for config file auth)
            profile: OCI config profile name (for config file auth)
            auth_type: Authentication type (auto-detected if None)
            region: OCI region (required for instance/resource principal)
        """
        # Auto-detect auth type if not specified
        if auth_type is None:
            auth_type = detect_auth_type()

        self.auth_type = auth_type
        logger.info(f"Initializing OCI client with auth type: {auth_type.value}")

        # Get config and signer
        self.config, self.signer = get_signer(auth_type, config_file, profile)

        # Override region if specified
        if region:
            self.config["region"] = region

        # Create clients with appropriate authentication
        if self.signer:
            self.monitoring_client = oci.monitoring.MonitoringClient(
                self.config, signer=self.signer
            )
            self.identity_client = oci.identity.IdentityClient(
                self.config, signer=self.signer
            )
        else:
            self.monitoring_client = oci.monitoring.MonitoringClient(self.config)
            self.identity_client = oci.identity.IdentityClient(self.config)

        # Get tenancy ID
        self.tenancy_id = self._get_tenancy_id()

    def _get_tenancy_id(self) -> str:
        """
        Get the tenancy OCID based on authentication type.

        For config file auth, reads from config.
        For instance/resource principal, extracts from the signer.
        """
        # Try to get from config first
        if "tenancy" in self.config:
            return self.config["tenancy"]

        # For instance principal, get tenancy from claims
        if self.auth_type == AuthType.INSTANCE_PRINCIPAL:
            # The signer has the tenancy in its security token
            if hasattr(self.signer, 'tenancy_id'):
                return self.signer.tenancy_id
            # Try to get from environment or instance metadata
            tenancy_id = os.environ.get("OCI_TENANCY")
            if tenancy_id:
                return tenancy_id

        # For resource principal
        if self.auth_type == AuthType.RESOURCE_PRINCIPAL:
            # Resource principal signer contains compartment/tenancy info
            rp_compartment = os.environ.get("OCI_RESOURCE_PRINCIPAL_COMPARTMENT_OCID")
            if rp_compartment:
                # Extract tenancy from compartment (root compartment = tenancy)
                # or use API to get tenancy
                pass

        # Fallback: try to get tenancy from environment
        tenancy_id = os.environ.get("OCI_TENANCY") or os.environ.get("OCI_CLI_TENANCY")
        if tenancy_id:
            return tenancy_id

        raise ValueError(
            "Could not determine tenancy ID. Please set OCI_TENANCY environment variable "
            "or ensure your authentication method provides tenancy information."
        )

    def list_compartments(self, parent_compartment_id: Optional[str] = None) -> List[Dict]:
        """
        List all compartments accessible to the user.

        Returns compartments in a hierarchical structure with full path names.
        """
        compartment_id = parent_compartment_id or self.tenancy_id
        compartments = []

        try:
            # Get root compartment (tenancy)
            tenancy = self.identity_client.get_tenancy(self.tenancy_id).data
            compartments.append({
                "id": self.tenancy_id,
                "name": tenancy.name,
                "path": f"{tenancy.name} (root)"
            })

            # List all sub-compartments recursively
            all_compartments = oci.pagination.list_call_get_all_results(
                self.identity_client.list_compartments,
                compartment_id=self.tenancy_id,
                compartment_id_in_subtree=True,
                access_level="ACCESSIBLE",
                lifecycle_state="ACTIVE"
            ).data

            # Build compartment path map
            compartment_map = {self.tenancy_id: tenancy.name}
            for comp in all_compartments:
                compartment_map[comp.id] = comp.name

            # Build full paths
            def get_path(comp_id, visited=None):
                if visited is None:
                    visited = set()
                if comp_id in visited:
                    return compartment_map.get(comp_id, "Unknown")
                visited.add(comp_id)

                comp = next((c for c in all_compartments if c.id == comp_id), None)
                if comp is None or comp.compartment_id == self.tenancy_id:
                    return f"{tenancy.name}/{compartment_map.get(comp_id, 'Unknown')}"
                return f"{get_path(comp.compartment_id, visited)}/{comp.name}"

            for comp in all_compartments:
                compartments.append({
                    "id": comp.id,
                    "name": comp.name,
                    "path": get_path(comp.id)
                })

        except Exception as e:
            logger.error(f"Error listing compartments: {e}")
            raise

        return sorted(compartments, key=lambda x: x["path"])

    def list_metric_namespaces(self, compartment_id: str) -> List[str]:
        """
        List all metric namespaces available in a compartment.

        Args:
            compartment_id: The OCID of the compartment

        Returns:
            List of namespace names
        """
        try:
            namespaces = set()
            response = oci.pagination.list_call_get_all_results(
                self.monitoring_client.list_metrics,
                compartment_id=compartment_id,
                list_metrics_details=oci.monitoring.models.ListMetricsDetails()
            ).data

            for metric in response:
                namespaces.add(metric.namespace)

            return sorted(list(namespaces))

        except Exception as e:
            logger.error(f"Error listing namespaces: {e}")
            raise

    def list_metrics(self, compartment_id: str, namespace: str,
                     resource_group: Optional[str] = None) -> List[Dict]:
        """
        List all metrics within a namespace.

        Args:
            compartment_id: The OCID of the compartment
            namespace: The metric namespace
            resource_group: Optional resource group filter

        Returns:
            List of metric definitions with name and dimensions
        """
        try:
            details = oci.monitoring.models.ListMetricsDetails(
                namespace=namespace,
                resource_group=resource_group
            )

            response = oci.pagination.list_call_get_all_results(
                self.monitoring_client.list_metrics,
                compartment_id=compartment_id,
                list_metrics_details=details
            ).data

            metrics = {}
            for metric in response:
                if metric.name not in metrics:
                    metrics[metric.name] = {
                        "name": metric.name,
                        "namespace": metric.namespace,
                        "dimensions": set(),
                        "resource_group": metric.resource_group
                    }
                # Collect all dimension keys
                if metric.dimensions:
                    metrics[metric.name]["dimensions"].update(metric.dimensions.keys())

            # Convert sets to lists for JSON serialization
            result = []
            for name, data in metrics.items():
                result.append({
                    "name": data["name"],
                    "namespace": data["namespace"],
                    "dimensions": sorted(list(data["dimensions"])),
                    "resource_group": data["resource_group"]
                })

            return sorted(result, key=lambda x: x["name"])

        except Exception as e:
            logger.error(f"Error listing metrics: {e}")
            raise

    def list_resource_groups(self, compartment_id: str, namespace: str) -> List[str]:
        """
        List all resource groups within a namespace.

        Args:
            compartment_id: The OCID of the compartment
            namespace: The metric namespace

        Returns:
            List of resource group names
        """
        try:
            details = oci.monitoring.models.ListMetricsDetails(
                namespace=namespace,
                group_by=["resourceGroup"]
            )

            response = oci.pagination.list_call_get_all_results(
                self.monitoring_client.list_metrics,
                compartment_id=compartment_id,
                list_metrics_details=details
            ).data

            groups = set()
            for metric in response:
                if metric.resource_group:
                    groups.add(metric.resource_group)

            return sorted(list(groups))

        except Exception as e:
            logger.error(f"Error listing resource groups: {e}")
            raise

    def list_dimensions(self, compartment_id: str, namespace: str,
                        metric_name: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List all dimensions and their values for metrics in a namespace.

        Args:
            compartment_id: The OCID of the compartment
            namespace: The metric namespace
            metric_name: Optional metric name to filter by

        Returns:
            Dict mapping dimension names to lists of their values
        """
        try:
            details = oci.monitoring.models.ListMetricsDetails(
                namespace=namespace,
                name=metric_name
            )

            response = oci.pagination.list_call_get_all_results(
                self.monitoring_client.list_metrics,
                compartment_id=compartment_id,
                list_metrics_details=details
            ).data

            dimensions: Dict[str, set] = {}
            for metric in response:
                if metric.dimensions:
                    for key, value in metric.dimensions.items():
                        if key not in dimensions:
                            dimensions[key] = set()
                        dimensions[key].add(value)

            # Convert sets to sorted lists
            return {k: sorted(list(v)) for k, v in sorted(dimensions.items())}

        except Exception as e:
            logger.error(f"Error listing dimensions: {e}")
            raise

    def list_dimension_values(self, compartment_id: str, namespace: str,
                              dimension_name: str, metric_name: Optional[str] = None,
                              filters: Optional[Dict[str, str]] = None) -> List[str]:
        """
        List values for a specific dimension.

        Args:
            compartment_id: The OCID of the compartment
            namespace: The metric namespace
            dimension_name: The dimension to get values for
            metric_name: Optional metric name filter
            filters: Optional dict of other dimension filters

        Returns:
            List of dimension values
        """
        try:
            dimension_filters = filters or {}

            details = oci.monitoring.models.ListMetricsDetails(
                namespace=namespace,
                name=metric_name,
                dimension_filters=dimension_filters if dimension_filters else None
            )

            response = oci.pagination.list_call_get_all_results(
                self.monitoring_client.list_metrics,
                compartment_id=compartment_id,
                list_metrics_details=details
            ).data

            values = set()
            for metric in response:
                if metric.dimensions and dimension_name in metric.dimensions:
                    values.add(metric.dimensions[dimension_name])

            return sorted(list(values))

        except Exception as e:
            logger.error(f"Error listing dimension values: {e}")
            raise

    def query_metrics(self, compartment_id: str, namespace: str, query: str,
                      start_time: datetime, end_time: datetime,
                      resolution: Optional[str] = None) -> Dict[str, Any]:
        """
        Query metric data using MQL.

        Args:
            compartment_id: The OCID of the compartment
            namespace: The metric namespace
            query: MQL query string
            start_time: Query start time
            end_time: Query end time
            resolution: Optional resolution for data points

        Returns:
            Dict containing metric data with timestamps and values
        """
        try:
            details = oci.monitoring.models.SummarizeMetricsDataDetails(
                namespace=namespace,
                query=query,
                start_time=start_time.isoformat() + "Z" if start_time.tzinfo is None else start_time.isoformat(),
                end_time=end_time.isoformat() + "Z" if end_time.tzinfo is None else end_time.isoformat(),
                resolution=resolution
            )

            response = self.monitoring_client.summarize_metrics_data(
                compartment_id=compartment_id,
                summarize_metrics_data_details=details
            ).data

            result = {
                "query": query,
                "namespace": namespace,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "metric_data": []
            }

            for metric_data in response:
                # Build a label from dimensions
                label_parts = [metric_data.name]
                if metric_data.dimensions:
                    dim_str = ", ".join([f"{k}={v}" for k, v in sorted(metric_data.dimensions.items())])
                    label_parts.append(f"({dim_str})")

                series = {
                    "name": metric_data.name,
                    "namespace": metric_data.namespace,
                    "dimensions": metric_data.dimensions or {},
                    "label": " ".join(label_parts),
                    "unit": metric_data.metadata.get("unit", "") if metric_data.metadata else "",
                    "data_points": []
                }

                for point in metric_data.aggregated_datapoints:
                    series["data_points"].append({
                        "timestamp": point.timestamp.isoformat(),
                        "value": point.value
                    })

                result["metric_data"].append(series)

            return result

        except Exception as e:
            logger.error(f"Error querying metrics: {e}")
            raise


# Global OCI client instance (kept for backward compatibility)
oci_client = None

# Compartment name cache for result labeling
_compartment_cache: Dict[str, Dict] = {}


def get_compartment_name(compartment_id: str) -> str:
    """Get compartment name from cache."""
    if compartment_id in _compartment_cache:
        return _compartment_cache[compartment_id].get('name', compartment_id)
    return compartment_id


def populate_compartment_cache(compartments: List[Dict]):
    """Populate compartment cache from API response."""
    global _compartment_cache
    for comp in compartments:
        _compartment_cache[comp['id']] = comp


class OCIRegionClientManager:
    """
    Manages OCI monitoring clients across multiple regions.

    Creates and caches clients per region to enable cross-region queries.
    """

    def __init__(self, config_file: str = "~/.oci/config", profile: str = "DEFAULT",
                 auth_type: AuthType = None):
        self.config_file = config_file
        self.profile = profile
        self.auth_type = auth_type or detect_auth_type()
        self._clients: Dict[str, OCIMonitoringClient] = {}
        self._base_config, self._signer = get_signer(self.auth_type, config_file, profile)
        self._default_region = self._base_config.get("region", "us-ashburn-1")
        self._tenancy_id = self._base_config.get("tenancy")

    def get_client(self, region: str = None) -> OCIMonitoringClient:
        """Get or create a client for a specific region."""
        region = region or self._default_region
        if region not in self._clients:
            self._clients[region] = OCIMonitoringClient(
                config_file=self.config_file,
                profile=self.profile,
                auth_type=self.auth_type,
                region=region
            )
        return self._clients[region]

    def get_default_region(self) -> str:
        """Get the default region from config."""
        return self._default_region

    def get_available_regions(self) -> List[str]:
        """Get list of subscribed OCI regions."""
        try:
            # Use identity client to list subscribed regions
            if self._signer:
                identity_client = oci.identity.IdentityClient(
                    self._base_config, signer=self._signer
                )
            else:
                identity_client = oci.identity.IdentityClient(self._base_config)

            regions = identity_client.list_region_subscriptions(
                tenancy_id=self._tenancy_id
            ).data

            return sorted([r.region_name for r in regions if r.status == "READY"])
        except Exception as e:
            logger.error(f"Error listing regions: {e}")
            # Return default region as fallback
            return [self._default_region]


# Global region client manager
_region_manager = None


def get_region_manager() -> OCIRegionClientManager:
    """Get or create the region client manager."""
    global _region_manager
    if _region_manager is None:
        config_file = os.environ.get("OCI_CONFIG_FILE", "~/.oci/config")
        profile = os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT")

        auth_type_str = os.environ.get("OCI_AUTH_TYPE", "").lower()
        auth_type = None
        if auth_type_str == "instance_principal":
            auth_type = AuthType.INSTANCE_PRINCIPAL
        elif auth_type_str == "resource_principal":
            auth_type = AuthType.RESOURCE_PRINCIPAL
        elif auth_type_str == "security_token":
            auth_type = AuthType.SECURITY_TOKEN
        elif auth_type_str == "config_file":
            auth_type = AuthType.CONFIG_FILE

        _region_manager = OCIRegionClientManager(
            config_file=config_file,
            profile=profile,
            auth_type=auth_type
        )
    return _region_manager


def get_oci_client() -> OCIMonitoringClient:
    """Get or create the OCI client instance."""
    global oci_client
    if oci_client is None:
        config_file = os.environ.get("OCI_CONFIG_FILE", "~/.oci/config")
        profile = os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT")
        region = os.environ.get("OCI_REGION")

        # Check for explicit auth type override
        auth_type_str = os.environ.get("OCI_AUTH_TYPE", "").lower()
        auth_type = None
        if auth_type_str == "instance_principal":
            auth_type = AuthType.INSTANCE_PRINCIPAL
        elif auth_type_str == "resource_principal":
            auth_type = AuthType.RESOURCE_PRINCIPAL
        elif auth_type_str == "security_token":
            auth_type = AuthType.SECURITY_TOKEN
        elif auth_type_str == "config_file":
            auth_type = AuthType.CONFIG_FILE
        # Otherwise auto-detect

        oci_client = OCIMonitoringClient(
            config_file=config_file,
            profile=profile,
            auth_type=auth_type,
            region=region
        )
    return oci_client


# API Routes

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/auth-info', methods=['GET'])
def api_auth_info():
    """Get current authentication information."""
    try:
        client = get_oci_client()
        return jsonify({
            "auth_type": client.auth_type.value,
            "tenancy_id": client.tenancy_id,
            "region": client.config.get("region", "unknown")
        })
    except Exception as e:
        logger.error(f"API error getting auth info: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/compartments', methods=['GET'])
def api_list_compartments():
    """List all accessible compartments."""
    try:
        client = get_oci_client()
        compartments = client.list_compartments()
        # Populate compartment cache for result labeling
        populate_compartment_cache(compartments)
        return jsonify({"compartments": compartments})
    except Exception as e:
        logger.error(f"API error listing compartments: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/regions', methods=['GET'])
def api_list_regions():
    """List all subscribed OCI regions."""
    try:
        manager = get_region_manager()
        regions = manager.get_available_regions()
        return jsonify({
            "regions": regions,
            "current_region": manager.get_default_region()
        })
    except Exception as e:
        logger.error(f"API error listing regions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/namespaces', methods=['GET'])
def api_list_namespaces():
    """List metric namespaces in a compartment."""
    compartment_id = request.args.get('compartment_id')
    if not compartment_id:
        return jsonify({"error": "compartment_id is required"}), 400

    try:
        client = get_oci_client()
        namespaces = client.list_metric_namespaces(compartment_id)
        return jsonify({"namespaces": namespaces})
    except Exception as e:
        logger.error(f"API error listing namespaces: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/resource-groups', methods=['GET'])
def api_list_resource_groups():
    """List resource groups in a namespace."""
    compartment_id = request.args.get('compartment_id')
    namespace = request.args.get('namespace')

    if not compartment_id or not namespace:
        return jsonify({"error": "compartment_id and namespace are required"}), 400

    try:
        client = get_oci_client()
        groups = client.list_resource_groups(compartment_id, namespace)
        return jsonify({"resource_groups": groups})
    except Exception as e:
        logger.error(f"API error listing resource groups: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/metrics', methods=['GET'])
def api_list_metrics():
    """List metrics in a namespace."""
    compartment_id = request.args.get('compartment_id')
    namespace = request.args.get('namespace')
    resource_group = request.args.get('resource_group')

    if not compartment_id or not namespace:
        return jsonify({"error": "compartment_id and namespace are required"}), 400

    try:
        client = get_oci_client()
        metrics = client.list_metrics(compartment_id, namespace, resource_group)
        return jsonify({"metrics": metrics})
    except Exception as e:
        logger.error(f"API error listing metrics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/dimensions', methods=['GET'])
def api_list_dimensions():
    """List all dimensions and their values for a namespace/metric."""
    compartment_id = request.args.get('compartment_id')
    namespace = request.args.get('namespace')
    metric_name = request.args.get('metric_name')

    if not compartment_id or not namespace:
        return jsonify({"error": "compartment_id and namespace are required"}), 400

    try:
        client = get_oci_client()
        dimensions = client.list_dimensions(compartment_id, namespace, metric_name)
        return jsonify({"dimensions": dimensions})
    except Exception as e:
        logger.error(f"API error listing dimensions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/dimension-values', methods=['GET'])
def api_list_dimension_values():
    """List values for a specific dimension."""
    compartment_id = request.args.get('compartment_id')
    namespace = request.args.get('namespace')
    dimension_name = request.args.get('dimension_name')
    metric_name = request.args.get('metric_name')

    if not compartment_id or not namespace or not dimension_name:
        return jsonify({"error": "compartment_id, namespace, and dimension_name are required"}), 400

    # Parse any filter parameters (dimension_filter_xxx=value)
    filters = {}
    for key, value in request.args.items():
        if key.startswith('filter_'):
            dim_name = key[7:]  # Remove 'filter_' prefix
            filters[dim_name] = value

    try:
        client = get_oci_client()
        values = client.list_dimension_values(
            compartment_id, namespace, dimension_name,
            metric_name=metric_name, filters=filters if filters else None
        )
        return jsonify({"values": values})
    except Exception as e:
        logger.error(f"API error listing dimension values: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/query', methods=['POST'])
def api_query_metrics():
    """Execute a metric query."""
    data = request.json

    required_fields = ['compartment_id', 'namespace', 'query', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    try:
        start_time = date_parser.parse(data['start_time'])
        end_time = date_parser.parse(data['end_time'])
    except Exception as e:
        return jsonify({"error": f"Invalid date format: {e}"}), 400

    try:
        client = get_oci_client()
        result = client.query_metrics(
            compartment_id=data['compartment_id'],
            namespace=data['namespace'],
            query=data['query'],
            start_time=start_time,
            end_time=end_time,
            resolution=data.get('resolution')
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"API error querying metrics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/query-multiple', methods=['POST'])
def api_query_multiple():
    """Execute multiple metric queries."""
    data = request.json
    queries = data.get('queries', [])

    if not queries:
        return jsonify({"error": "queries array is required"}), 400

    results = []
    errors = []

    client = get_oci_client()

    for idx, query_def in enumerate(queries):
        required_fields = ['compartment_id', 'namespace', 'query', 'start_time', 'end_time']
        missing = [f for f in required_fields if f not in query_def]

        if missing:
            errors.append({
                "query_index": idx,
                "error": f"Missing fields: {', '.join(missing)}"
            })
            continue

        try:
            start_time = date_parser.parse(query_def['start_time'])
            end_time = date_parser.parse(query_def['end_time'])

            result = client.query_metrics(
                compartment_id=query_def['compartment_id'],
                namespace=query_def['namespace'],
                query=query_def['query'],
                start_time=start_time,
                end_time=end_time,
                resolution=query_def.get('resolution')
            )
            result['query_id'] = query_def.get('id', idx)
            result['query_name'] = query_def.get('name', f"Query {idx + 1}")
            results.append(result)

        except Exception as e:
            errors.append({
                "query_index": idx,
                "query_id": query_def.get('id', idx),
                "error": str(e)
            })

    return jsonify({
        "results": results,
        "errors": errors
    })


@app.route('/api/query-unified', methods=['POST'])
def api_query_unified():
    """
    Execute queries across multiple regions and compartments.

    This endpoint enables unified monitoring dashboards by querying the same
    metric across multiple regions and compartments simultaneously.

    Request body:
    {
        "regions": ["us-ashburn-1", "us-phoenix-1"],  // Optional, defaults to current region
        "compartment_ids": ["ocid1...", "ocid2..."],  // Required, at least one
        "namespace": "oci_computeagent",
        "query": "CpuUtilization[1h].mean()",
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-02T00:00:00Z",
        "resolution": "1h"  // Optional
    }
    """
    data = request.json

    # Validate required fields
    required_fields = ['compartment_ids', 'namespace', 'query', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    compartment_ids = data.get('compartment_ids', [])
    if not compartment_ids:
        return jsonify({"error": "At least one compartment_id is required"}), 400

    # Get regions - default to current region if not specified
    manager = get_region_manager()
    regions = data.get('regions', [])
    # Filter out empty/None values and fallback to default if no valid regions
    regions = [r for r in regions if r]
    if not regions:
        regions = [manager.get_default_region()]

    namespace = data['namespace']
    query = data['query']
    resolution = data.get('resolution')

    try:
        start_time = date_parser.parse(data['start_time'])
        end_time = date_parser.parse(data['end_time'])
    except Exception as e:
        return jsonify({"error": f"Invalid date format: {e}"}), 400

    results = []
    errors = []

    logger.info(f"Unified query: {len(regions)} regions x {len(compartment_ids)} compartments = {len(regions) * len(compartment_ids)} queries")
    logger.info(f"Regions: {regions}")

    # Query each region/compartment combination
    for region in regions:
        try:
            client = manager.get_client(region)
        except Exception as e:
            # Region not available
            for comp_id in compartment_ids:
                errors.append({
                    "region": region,
                    "compartment_id": comp_id,
                    "error": f"Failed to connect to region {region}: {str(e)}"
                })
            continue

        for compartment_id in compartment_ids:
            try:
                result = client.query_metrics(
                    compartment_id=compartment_id,
                    namespace=namespace,
                    query=query,
                    start_time=start_time,
                    end_time=end_time,
                    resolution=resolution
                )

                # Get compartment name for labeling
                compartment_name = get_compartment_name(compartment_id)

                # Add source metadata to each metric series
                for metric in result.get('metric_data', []):
                    metric['_source'] = {
                        'region': region,
                        'compartment_id': compartment_id,
                        'compartment_name': compartment_name
                    }
                    # Enhance label with source info
                    original_label = metric.get('label', metric.get('name', 'Unknown'))
                    metric['label'] = f"{original_label} [{region}] ({compartment_name})"
                    metric['short_label'] = original_label

                metric_count = len(result.get('metric_data', []))
                logger.info(f"Region {region}, compartment {compartment_name}: {metric_count} metric series")

                results.append({
                    'region': region,
                    'compartment_id': compartment_id,
                    'compartment_name': compartment_name,
                    **result
                })

            except Exception as e:
                logger.error(f"Error querying {region}/{compartment_id}: {e}")
                errors.append({
                    "region": region,
                    "compartment_id": compartment_id,
                    "compartment_name": get_compartment_name(compartment_id),
                    "error": str(e)
                })

    return jsonify({
        "results": results,
        "errors": errors,
        "metadata": {
            "total_regions": len(regions),
            "total_compartments": len(compartment_ids),
            "total_queries": len(regions) * len(compartment_ids),
            "successful_queries": len(results),
            "failed_queries": len(errors)
        }
    })


# Common metric namespaces and their typical metrics for reference
COMMON_NAMESPACES = {
    "oci_computeagent": {
        "description": "Compute Instance Metrics",
        "metrics": ["CpuUtilization", "MemoryUtilization", "DiskBytesRead", "DiskBytesWritten",
                    "DiskIopsRead", "DiskIopsWritten", "NetworkBytesIn", "NetworkBytesOut"]
    },
    "oci_blockvolume": {
        "description": "Block Volume Metrics",
        "metrics": ["VolumeReadThroughput", "VolumeWriteThroughput", "VolumeReadOps", "VolumeWriteOps"]
    },
    "oci_vcn": {
        "description": "Virtual Cloud Network Metrics",
        "metrics": ["VnicToNetworkBytes", "VnicFromNetworkBytes", "VnicToNetworkPackets", "VnicFromNetworkPackets"]
    },
    "oci_lbaas": {
        "description": "Load Balancer Metrics",
        "metrics": ["HttpRequests", "HttpResponses", "ActiveConnections", "BytesReceived", "BytesSent"]
    },
    "oci_autonomous_database": {
        "description": "Autonomous Database Metrics",
        "metrics": ["CpuUtilization", "StorageUtilization", "Sessions", "ExecuteCount"]
    },
    "oci_database": {
        "description": "Database Service Metrics",
        "metrics": ["CpuUtilization", "StorageSpaceUsed", "Sessions"]
    },
    "oci_objectstorage": {
        "description": "Object Storage Metrics",
        "metrics": ["ObjectCount", "StoredBytes", "AllRequests"]
    },
    "oci_filestorage": {
        "description": "File Storage Metrics",
        "metrics": ["ReadThroughput", "WriteThroughput", "ReadRequests", "WriteRequests"]
    }
}


@app.route('/api/common-namespaces', methods=['GET'])
def api_common_namespaces():
    """Get common metric namespaces with descriptions."""
    return jsonify({"namespaces": COMMON_NAMESPACES})


# Supported statistics and intervals
SUPPORTED_STATISTICS = ["mean", "max", "min", "sum", "count", "rate", "percentile(0.5)",
                        "percentile(0.9)", "percentile(0.95)", "percentile(0.99)"]

SUPPORTED_INTERVALS = [
    {"value": "1m", "label": "1 minute"},
    {"value": "5m", "label": "5 minutes"},
    {"value": "15m", "label": "15 minutes"},
    {"value": "1h", "label": "1 hour"},
    {"value": "6h", "label": "6 hours"},
    {"value": "1d", "label": "1 day"}
]


@app.route('/api/query-options', methods=['GET'])
def api_query_options():
    """Get available statistics and intervals."""
    return jsonify({
        "statistics": SUPPORTED_STATISTICS,
        "intervals": SUPPORTED_INTERVALS
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
