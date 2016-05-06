#!/usr/bin/env python3

import argparse
import boto3

parser = argparse.ArgumentParser(description='AMI Builder')
parser.add_argument('--instance-id', required=True, help='Instance ID to create AMI from')
parser.add_argument('--name', required=True, help='Name for the AMI')
args = parser.parse_args()

print("Instance ID: {}".format(args.instance_id))
ec2 = boto3.resource('ec2', region_name='us-east-1')

print("Stopping instance...")
inst = list(ec2.instances.filter(InstanceIds=[instance_id]))[0]
inst.stop()
inst.wait_until_stopped()
print("Instance stopped")

print("Creating snapshot...")
vol = list(inst.volumes.all())[0]
snap = vol.create_snapshot()
snap.wait_until_completed()
print("Snapshot ID: {}".format(snap.id))

# deregister existing ami if any
for ex in list(ec2.images.filter(Owners=['self'], Filters=[{'Name':'name','Values':[args.name]}])):
  print("Deregistering existing AMI {}".format(ex.id))
  ex.deregister()
  snap_id = ex.block_device_mappings[0]['Ebs']['SnapshotId']
  snap = list(ec2.snapshots.filter(SnapshotIds=[snap_id]))[0]
  snap.delete()

print("Registering AMI Name={}...".format(args.name))
img = ec2.register_image(
   Name=args.name, Architecture='x86_64', VirtualizationType='hvm',
   RootDeviceName='/dev/sda1',
   BlockDeviceMappings=[{
    'DeviceName': '/dev/sda1',
    'Ebs': {'SnapshotId': snap.id}
   }])
print("AMI ID: {}".format(img.id))
