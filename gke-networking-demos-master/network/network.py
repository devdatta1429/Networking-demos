import re
import logging

logger = logging.getLogger(__name__)

NETWORK_TYPE = 'compute.v1.network'
SUBNETWORK_TYPE = 'compute.v1.subnetwork'

def is_valid_cidr(cidr):
    pattern = r'^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$'
    return bool(re.match(pattern, cidr))


def GenerateConfig(context):
    """
    Generates the YAML resource configuration for a GCP network.
    """
    network_name = context.env.get('name')

    if not network_name:
        logger.error("Network name not provided.")
        raise ValueError("Network name cannot be empty.")

    resources = [{
        'name': network_name,
        'type': NETWORK_TYPE,
        'properties': {
            'name': network_name,
            'autoCreateSubnetworks': False,
        }
    }]

    subnetworks = context.properties.get('subnetworks')
    if not subnetworks:
        logger.error("No subnetworks provided.")
        raise ValueError("No subnetworks provided in the configuration.")

    subnetwork_names = set()

    for subnetwork in subnetworks:
        # Validate subnetwork parameters
        if not all(k in subnetwork for k in ('name', 'region', 'cidr')):
            logger.error(f"Missing required subnetwork properties: {subnetwork}")
            raise ValueError("Subnetwork missing 'name', 'region', or 'cidr'.")

        if not is_valid_cidr(subnetwork['cidr']):
            logger.error(f"Invalid CIDR format for subnetwork: {subnetwork['name']}")
            raise ValueError(f"Invalid CIDR format for subnetwork: {subnetwork['name']}")

        subnetwork_name = f"{subnetwork['name']}-{subnetwork['region']}"
        if subnetwork_name in subnetwork_names:
            logger.error(f"Duplicate subnetwork name detected: {subnetwork_name}")
            raise ValueError(f"Duplicate subnetwork name detected: {subnetwork_name}")

        subnetwork_names.add(subnetwork_name)

        description = subnetwork.get('description', f"Subnetwork of {network_name} in {subnetwork['region']}")

        resources.append({
            'name': subnetwork_name,
            'type': SUBNETWORK_TYPE,
            'properties': {
                'name': subnetwork_name,
                'description': description,
                'ipCidrRange': subnetwork['cidr'],
                'region': subnetwork['region'],
                'network': f"$(ref.{network_name}.selfLink)",
            },
            'metadata': {
                'dependsOn': [network_name]
            }
        })

    return {'resources': resources}
