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
    
    def launch_instance(self, image_id, instance_type, name, dry_run=False):
        """
        Launch an EC2 instance with the specified parameters.
        
        Args:
            image_id: AMI ID (e.g., 'ami-0c55b159cbfafe1f0')
            instance_type: Instance type (e.g., 't2.micro', 't2.small')
            name: Name tag for the instance
            dry_run: If True, validates permissions without creating instance
        
        Returns:
            dict: {'success': bool, 'instance_id': str, 'message': str}
        """
        try:
            # Validate instance type is available in region
            if not self._is_instance_type_available(instance_type):
                return {
                    'success': False,
                    'instance_id': None,
                    'message': f'Instance type {instance_type} not available in region {self.region}'
                }
            
            instances = self.ec2_client.run_instances(
                ImageId=image_id,
                MinCount=1,
                MaxCount=1,
                InstanceType=instance_type,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [{'Key': 'Name', 'Value': name}]
                    }
                ],
                DryRun=dry_run
            )
            
            instance_id = instances['Instances'][0]['InstanceId']
            
            return {
                'success': True,
                'instance_id': instance_id,
                'message': f'Instance {instance_id} launched successfully with name "{name}"'
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'DryRunOperation':
                return {
                    'success': True,
                    'instance_id': None,
                    'message': 'DryRun validation passed - credentials are valid'
                }
            else:
                return {
                    'success': False,
                    'instance_id': None,
                    'message': f'Error launching instance: {e.response["Error"]["Message"]}'
                }
        except Exception as e:
            return {
                'success': False,
                'instance_id': None,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def terminate_instance(self, instance_id):
        """
        Terminate a specific EC2 instance.
        
        Args:
            instance_id: The instance ID to terminate
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            return {
                'success': True,
                'message': f'Instance {instance_id} termination initiated'
            }
        except ClientError as e:
            return {
                'success': False,
                'message': f'Error terminating instance: {e.response["Error"]["Message"]}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
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
    
    def _is_instance_type_available(self, instance_type):
        """
        Check if an instance type is available in the current region.
        
        Args:
            instance_type: Instance type to check (e.g., 't2.micro')
        
        Returns:
            bool: True if available, False otherwise
        """
        try:
            response = self.ec2_client.describe_instance_types(
                Filters=[
                    {
                        'Name': 'instance-type',
                        'Values': [instance_type]
                    }
                ]
            )
            return len(response['InstanceTypes']) > 0
        except ClientError:
            # If we can't verify, assume it's available (let AWS reject it)
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
