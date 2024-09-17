import boto3 # type: ignore
from botocore.exceptions import ClientError # type: ignore
import argparse
from datetime import datetime

# ----------------Parser Initialization-------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='platformtool',
        description='This program can manage resources in the AWS from the command line')
    
    parser.add_argument('--resource', type=str,
                        help='Enter the AWS resource you want to manage')
    parser.add_argument('--username', type=str,
                        help='The name of the user creating the instance.')
    parser.add_argument('--instance_type', type=str,
                        help="The type of instance you want to create, only t3.nano or t4g.nano")
    parser.add_argument('--ami_choice', type=str,
                        help='Selects between Ubuntu or Amazon Linux AMIs')
    parser.add_argument('--amount', type=int,
                        help='Specifies an amount of EC2 instances to create')
    parser.add_argument('--action', type=str,
                        help='Allows user to manage the resources. \
                            Accepted parameters: create, start, stop, list, update/upsert, upload, create-zone')
    parser.add_argument('--ec2_id', type=str,
                        help='The ID of an ec2 instance you want to start/stop.')
    parser.add_argument('--bucket_access', type=str,
                        help='Choose between private or public access to the bucket.')
    parser.add_argument('--access_confirmation', type=str,
                        help='Confirm whether you want to create a public bucket.')
    parser.add_argument('--bucket_name', type=str,
                        help='Bucket name to which you want to upload a file.')
    parser.add_argument('--file_path', type=str,
                        help='Path to a file which you want to upload to a bucket.')
    parser.add_argument('--file_name', type=str,
                        help='Name of the file you want to upload.')
    parser.add_argument('--zone_id', type=str,
                        help='Hosted zone ID for DNS management.')
    parser.add_argument('--record_type', type=str,
                        help='DNS record type to create/update.')
    parser.add_argument('--dns_target', type=str,
                        help='Where to point the DNS record at.')
    parser.add_argument('--record_name', type=str,
                        help='A name for the record.')
    parser.add_argument('--zone_type', type=str,
                        help='Select between a public or a private hosted zone.')
    return parser.parse_args()

# --------------Sending parameters to correct resources------------------------------

def select_resources(resources, session):
    restype = resources.resource
        
    if restype.lower() == "ec2":
        select_ec2(resources, session)
    elif restype.lower() == "s3":
        select_s3(resources, session)
    elif restype.lower() == "route53":
        select_route53(resources, session)
    else: 
        raise argparse.ArgumentTypeError("Not a valid resource. Valid resources are: ec2, s3 and route53.")
    
# --------------------------EC2 Management-------------------------------    
    
def check_for_cli_ec2(resources, ec2, custom_filter):
     instance_check = ec2.describe_instances(
                Filters = custom_filter,
                InstanceIds=[
                    resources.ec2_id
                ],
            )    
     return instance_check
 
def ec2_list(resources, ec2, custom_filter):
    instances = ec2.describe_instances(Filters=custom_filter)
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    print(instance_id)
    print("Listed all EC2 instances for this user.")
    
def ec2_create(resources, ec2, imageID, allowed_instance_types):
    if resources.amount:
        if 0 < resources.amount <= 2:
            if resources.instance_type in allowed_instance_types:
                for i in range(resources.amount):
                    instance = ec2.run_instances(
                        ImageId = imageID,
                        InstanceType=resources.instance_type,
                        MinCount=1,
                        MaxCount=1,
                        TagSpecifications=[
                            {
                                'ResourceType': 'instance',
                                'Tags': [
                                    {
                                        'Key': 'Name',
                                        'Value': resources.username + '-' + resources.ami_choice + str(i + 1),
                                    },
                                    {
                                        'Key': 'Created with CLI',
                                        'Value': 'True'
                                    },
                                    {
                                        'Key': 'Creator',
                                        'Value': resources.username
                                    },
                                ]
                            }
                        ],
                        Placement={
                            'AvailabilityZone': 'us-east-1a'
                        },
                        SubnetId='subnet-0992c1cd4b004598c'
                            
                    )
                    print("Instance created:", instance['Instances'][0]['InstanceId'])
            else:
                raise argparse.ArgumentTypeError('Either no --instance_type provided, or the instance type is not valid. \
                    The allowed instance types are: t3.nano, t4g.nano, t2.micro')
        else:
            raise argparse.ArgumentTypeError('Invalid amount of instances. You can only create up to 2 instances.')
    else:
        raise argparse.ArgumentTypeError('No amount provided. Please use --amount <amount of instances to create>.\
            You can only create up to 2 instances.')        

def ec2_start(resources, ec2, custom_filter):
    instance_check = check_for_cli_ec2(resources, ec2, custom_filter)
    if not instance_check['Reservations']:
        print("Instance wasn't created with CLI.")
    else:
        instances = ec2.start_instances(
            InstanceIds=[
                resources.ec2_id,
            ],
        )
        print("Successfully started instance:", resources.ec2_id)

def ec2_stop(resources, ec2, custom_filter):
    instance_check = check_for_cli_ec2(resources, ec2, custom_filter)
    if not instance_check['Reservations']:
        print("Instance wasn't created with CLI.")
    else:
        instances = ec2.stop_instances(
            InstanceIds=[
                resources.ec2_id,
            ],
        )    
        print('Successfully stopped instance:', resources.ec2_id)

def select_ec2(resources, session):
    if resources.username:
        ec2 = session.client('ec2') # initializing the ec2 module
        
        # Adding a custom filter for easy tag checking.
        custom_filter = [
            {
            'Name':'tag:Created with CLI',
            'Values': ['True']
            },
            {
             'Name':'tag:Creator',
             'Values': [resources.username]
            }
            ]
        if resources.action == "list":
            instances = ec2_list(resources, ec2, custom_filter)
        elif resources.action == "start":
                instance_start = ec2_start(resources, ec2, custom_filter)
        elif resources.action == "stop":
                instance_stop = ec2_stop(resources, ec2, custom_filter)
                        
        else:
            # Adding an AMI choice & an allowed instance list
            allowed_instance_types = ['t2.micro']
            image = resources.ami_choice
            if image.lower() == "ubuntu":
                imageID = 'ami-0e86e20dae9224db8'
            elif image.lower() == "amazon linux":
                imageID = 'ami-0182f373e66f89c85'
            else: 
                raise argparse.ArgumentTypeError("Invalid AMI selected. Only valid options are Ubuntu and Amazon Linux.")

            if resources.action == "create":
                instance = ec2_create(resources, ec2, imageID, allowed_instance_types)   
            else:
                argparse.ArgumentTypeError("A valid action wasn't provided.")
    else:
        raise argparse.ArgumentTypeError('No username provided. Please enter --username <username>.')

# --------------------S3 Management---------------------------------------

def s3_create_bucket(resources, s3):
    if resources.bucket_access == "private" or resources.bucket_access == "public" and resources.access_confirmation.lower() == "true":
        bucket = s3.create_bucket(
                        ACL='private',
                        Bucket=resources.username + '-bucket',
        )
        created_bucket = bucket['Location'].replace("/", "")
        return s3_tag_bucket(resources, s3, created_bucket)

    else:
        raise argparse.ArgumentTypeError("Please pass --access_confirmation true if you want to make a public bucket.")

        
def s3_tag_bucket(resources, s3, bucket,):
    bucket_tagged = s3.put_bucket_tagging(
                    Bucket=bucket,
                    Tagging={
                        'TagSet':[
                            {
                                'Key': 'Created with CLI',
                                'Value': 'True'
                            },
                            {
                                'Key': 'Owner',
                                'Value': resources.username
                            },
                        ]
                    },
                )
    if resources.bucket_access == "private":
        return bucket
    elif resources.bucket_access == "public":
        return s3_public_bucket(resources, s3, bucket)

def s3_public_bucket(resources, s3, bucket):
    if resources.access_confirmation.lower() == "true":
        public_bucket = s3.put_public_access_block(
                            Bucket=bucket,
                            PublicAccessBlockConfiguration={
                                'BlockPublicAcls': False,
                                'IgnorePublicAcls': False,
                                'BlockPublicPolicy': False,
                                'RestrictPublicBuckets': False
                            },
                        )
        return bucket
    else:
        raise argparse.ArgumentTypeError("Please pass --access_confirmation true if you want to make a public bucket.")

    
def s3_list_bucket(resources, s3):
    bucket = s3.list_buckets()
    btag = [] # list to append valid buckets to
    for i in bucket['Buckets']:
        bucket_name = i['Name']
        
        try:
            tags = s3.get_bucket_tagging(
                Bucket= bucket_name
            )
            for tag in tags.get('TagSet', []):
                if tag['Key'] == 'Created with CLI':
                    btag.append(bucket_name)
        except ClientError:
            continue
    return btag

def s3_upload_file(resources, s3):
    upload = s3.upload_file(resources.file_path, resources.bucket_name, resources.file_name)
    print("File successfully uploaded.")
    return upload
    

def select_s3(resources, session):
    s3 = session.client('s3')
    if resources.action == "create":
        bucket = s3_create_bucket(resources, s3)
        print("Bucket successfully created.", bucket)

    elif resources.action == "list":
        bucket = print(s3_list_bucket(resources, s3))

    elif resources.action == "upload":
        if not resources.file_name:
            raise argparse.ArgumentTypeError("No file name provided. Please use --file_name to provide a name for the file.")
        check_cli = s3_list_bucket(resources, s3)
        if resources.bucket_name in check_cli:
            s3_upload = s3_upload_file(resources, s3)

        else:
            raise argparse.ArgumentTypeError("Bucket wasn't created with CLI.")
    else:
        raise argparse.ArgumentTypeError("No valid action was provided.")

# ---------------Route53 Management-----------------------------------

def route53_create_public(resources, r53):
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    route53 = r53.create_hosted_zone(
        Name=resources.username + '-zone.com',
        CallerReference=current_time,
        HostedZoneConfig={
            'Comment': 'Zone created with CLI',
            'PrivateZone': False
        },
    )
    created_zone_id = route53['HostedZone']['Id']
    cleaned_up_id = created_zone_id.replace("/hostedzone/", "")
    print("Route53 zone successfully created:", cleaned_up_id)
    return route53_tag(resources, r53, cleaned_up_id)
    

def route53_create(resources, r53):
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    route53 = r53.create_hosted_zone(
        Name=resources.username + '-zone.com',
        VPC={
            'VPCRegion': 'us-east-1',
            'VPCId': 'vpc-058154e6ed31674ee',    
        },
        CallerReference=current_time,
        HostedZoneConfig={
            'Comment': 'Zone created with CLI',
            'PrivateZone': True
        },
    )
    created_zone_id = route53['HostedZone']['Id']
    cleaned_up_id = created_zone_id.replace("/hostedzone/", "")
    print("Route53 zone successfully created:", cleaned_up_id)
    return route53_tag(resources, r53, cleaned_up_id)


def route53_tag(resources, r53, r53_zone):
    route53_tagged = r53.change_tags_for_resource(
            ResourceType='hostedzone',
            ResourceId=r53_zone,
            AddTags=[
                {
                    'Key': 'Created with CLI',
                    'Value': 'True'
                },
                {
                    'Key': 'Owner',
                    'Value': resources.username
                },
            ],
        )
    print("tags succesfully added")
    return route53_tagged

def route53_add_record(resources, r53):
    # Only use the part of the record name before the -username.zone
    if resources.action.lower() == "update":
        resources.action = "upsert"
    if resources.record_name == None:
        raise argparse.ArgumentTypeError("No record name provided. Please use --record_name to provide a name.")
    elif resources.record_type == None:
        raise argparse.ArgumentTypeError("No record type provided. Please use --record_type to provide one.")
    elif resources.dns_target == None:
        raise argparse.ArgumentTypeError("No DNS target provided. Please provide one with --dns_target")
    elif resources.zone_id == None:
        raise argparse.ArgumentTypeError("No hosted zone id provided. Use --zone_id to provide one.")
    else:
        checking_for_tags = route53_check_tags(resources, r53)
        if checking_for_tags == '1':
            route53_record = r53.change_resource_record_sets(
                    HostedZoneId=resources.zone_id,
                    ChangeBatch={
                        'Changes': [
                            {
                                'Action': resources.action.upper(),
                                'ResourceRecordSet': {
                                    'Name': resources.record_name + '.' + resources.username + '-zone.com',
                                    'Type': resources.record_type,
                                    'TTL': 300,
                                    'ResourceRecords': [
                                        {
                                        'Value': resources.dns_target
                                        }, 
                                    ],
                                },
                            },
                        ]
                    },
                )
            print("Record edited successfully.")
            return route53_record
        else:
            raise argparse.ArgumentTypeError("Hosted Zone wasn't created with CLI.")
    

def route53_check_tags(resources, r53):
    r53_check = r53.list_tags_for_resource(
        ResourceType='hostedzone',
        ResourceId=resources.zone_id,
    )
    for tag in r53_check['ResourceTagSet']['Tags']:
        if tag['Key'] == 'Created with CLI':
            return "1"

def select_route53(resources, session):
    allowed_action = ['update', 'upsert', 'create-zone', 'create', 'delete']
    r53 = session.client('route53')
    if resources.username == None:
        raise argparse.ArgumentTypeError("No username provided. Please provide username with --username.")
    elif resources.action == None:
        raise argparse.ArgumentTypeError("No action provided. Please use --action to provide an action.")
    elif resources.action.lower() not in allowed_action:
        raise argparse.ArgumentTypeError("Invalid action. Valid actions are:", allowed_action)


    if resources.action == "create-zone":
        if resources.zone_type == None:
            raise argparse.ArgumentTypeError("No --zone_type provided. Please use --zone_type public/private.")
        elif resources.zone_type.lower() == "public":
            route53 = route53_create_public(resources, r53)
        elif resources.zone_type.lower() == "private":
            route53 = route53_create(resources, r53)
        else:
            raise argparse.ArgumentTypeError("Invalid zone_type. --zone_type only accepts: public, private.")
            
    elif resources.action.lower() == "create" or "delete" or "update" or "upsert":
        route53_record = route53_add_record(resources, r53)
    
    else:
        raise argparse.ArgumentTypeError("Unexpected exception occurred.")

    
    


def main():
    session = boto3.Session()
    args = parse_arguments()
    if args.resource:
        select_resources(args, session) # sends all args further down the line
        
    
main()
