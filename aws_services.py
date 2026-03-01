import boto3
from botocore.exceptions import ClientError


class AWSManager:
    """Manages AWS EC2 operations using Boto3."""
    
    def __init__(self, access_key, secret_key, region):
        """
        Initialize AWS manager with user credentials.
        
        Args:
            access_key: AWS Access Key ID
            secret_key: AWS Secret Access Key
            region: AWS Region
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.ec2_client = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        self.ec2_resource = boto3.resource(
            'ec2',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
    
    
    def get_all_instances(self):
        """
        Retrieve all instances for the user (across all states except terminated).
        
        Returns:
            list: List of instance dictionaries with key info
        """
        try:
            instances = []
            
            # Get all reservations (non-terminated instances)
            response = self.ec2_client.describe_instances(
                Filters=[
                    {
                        'Name': 'instance-state-name',
                        'Values': ['pending', 'running', 'stopping', 'stopped']
                    }
                ]
            )
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Extract the Name tag if it exists
                    name = instance['InstanceId']
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'Name':
                            name = tag['Value']
                            break
                    
                    instances.append({
                        'instance_id': instance['InstanceId'],
                        'name': name,
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'public_ip': instance.get('PublicIpAddress', 'N/A'),
                        'private_ip': instance.get('PrivateIpAddress', 'N/A')
                    })
            
            return instances
        except ClientError as e:
            print(f'Error retrieving instances: {e}')
            return []
    
    def get_key_pairs(self):
        """
        Get all available EC2 Key Pairs in the region.
        
        Returns:
            list: List of key pair names
        """
        try:
            response = self.ec2_client.describe_key_pairs()
            return [kp['KeyName'] for kp in response['KeyPairs']]
        except ClientError:
            return []
    
    def get_security_groups(self):
        """
        Get all available security groups in the region.
        
        Returns:
            list: List of dicts with 'GroupId' and 'GroupName'
        """
        try:
            response = self.ec2_client.describe_security_groups()
            return [
                {
                    'GroupId': sg['GroupId'],
                    'GroupName': sg['GroupName'],
                    'Description': sg.get('Description', '')
                }
                for sg in response['SecurityGroups']
            ]
        except ClientError:
            return []
    
    def get_subnets(self):
        """
        Get all available subnets in the region.
        
        Returns:
            list: List of dicts with 'SubnetId', 'VpcId', 'CidrBlock', 'AvailabilityZone'
        """
        try:
            response = self.ec2_client.describe_subnets()
            return [
                {
                    'SubnetId': subnet['SubnetId'],
                    'VpcId': subnet['VpcId'],
                    'CidrBlock': subnet['CidrBlock'],
                    'AvailabilityZone': subnet['AvailabilityZone'],
                    'AvailableIpAddressCount': subnet['AvailableIpAddressCount']
                }
                for subnet in response['Subnets']
            ]
        except ClientError:
            return []
    
    def get_iam_roles(self):
        """
        Get all available IAM roles that can be used with EC2 instances.
        
        Returns:
            list: List of role names
        """
        try:
            iam_client = boto3.client('iam')
            response = iam_client.list_roles()
            return [role['RoleName'] for role in response['Roles']]
        except ClientError:
            return []
    
    def get_available_instance_types(self, instance_family='t'):
        """
        Get all available instance types in the current region.
        Optionally filter by instance family (e.g., 't' for t2/t3, 'm' for m5, etc.)
        
        Returns:
            list: List of instance type strings (e.g., ['t2.micro', 't2.small', 't3.micro'])
        """
        try:
            # Use InstanceTypeFilter to get available types for a family
            response = self.ec2_client.describe_instance_types(
                Filters=[
                    {
                        'Name': 'instance-type',
                        'Values': [f'{instance_family}*.micro', f'{instance_family}*.small', f'{instance_family}*.medium', f'{instance_family}*.large', f'{instance_family}*.xlarge', f'{instance_family}*.2xlarge']
                    }
                ]
            )
            instance_types = sorted([it['InstanceType'] for it in response['InstanceTypes']])
            return instance_types
        except ClientError:
            # If filtering fails, try a broader approach - describe all and filter locally
            try:
                response = self.ec2_client.describe_instance_types()
                instance_types = sorted([
                    it['InstanceType'] 
                    for it in response['InstanceTypes'] 
                    if it['InstanceType'].startswith(instance_family)
                ])
                return instance_types
            except ClientError:
                # Fallback to common instance types
                return ['t2.micro', 't2.small', 't2.medium', 't3.micro', 't3.small']
    
    def _is_instance_type_available(self, instance_type):
        """
        Check if an instance type is available in the current region.
        
        Args:
            instance_type: Instance type to check (e.g., 't2.micro')
        
        Returns:
            bool: True if available, False otherwise
        """
        try:
            # Use InstanceTypes parameter instead of Filters for more reliable checking
            response = self.ec2_client.describe_instance_types(
                InstanceTypes=[instance_type]
            )
            # If we got a response with the instance type, it's available
            return len(response['InstanceTypes']) > 0
        except ClientError as e:
            # If there's an error, it could be invalid instance type or permission issue
            # In either case, return False and let the user know
            error_code = e.response['Error']['Code']
            if error_code == 'InvalidParameterValue':
                # Instance type doesn't exist in this region
                return False
            # For other errors, allow it to proceed (permission issues, etc)
            return True


def validate_aws_credentials(access_key, secret_key, region):
    """
    Validate AWS credentials before storing them.
    
    Args:
        access_key: AWS Access Key ID
        secret_key: AWS Secret Access Key
        region: AWS Region
    
    Returns:
        dict: {'valid': bool, 'message': str}
    """
    try:
        manager = AWSManager(access_key, secret_key, region)
        # Try a dry-run describe to validate credentials
        manager.ec2_client.describe_instances(DryRun=True)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'DryRunOperation':
            return {'valid': True, 'message': 'Credentials are valid'}
        elif error_code == 'AuthFailure':
            return {'valid': False, 'message': 'Invalid AWS credentials'}
        else:
            return {'valid': False, 'message': f'Error: {e.response["Error"]["Message"]}'}
    except Exception as e:
        return {'valid': False, 'message': f'Error validating credentials: {str(e)}'}
    
    return {'valid': True, 'message': 'Credentials are valid'}
