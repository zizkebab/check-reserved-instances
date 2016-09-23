"""'Unit' tests.

Unfortunately, moto doesn't support creation of reserved instances (yet).

https://github.com/spulec/moto/blob/master/moto/ec2/responses/reserved_instances.py
"""
from collections import namedtuple
import datetime

from click.testing import CliRunner
from dateutil.tz import tzutc
import mock

from check_reserved_instances import cli


ec2_instance = namedtuple(
    'ec2_instance',
    'state spot_instance_request_id placement instance_type tags id')

ec2_reservation = namedtuple(
    'ec2_reservations',
    'instances')

ec2_ri = namedtuple(
    'ec2_ri',
    'state availability_zone instance_type instance_count end')

rds_instance = namedtuple(
    'rds_instance',
    'status multi_az instance_class id')


def get_ec2_instances():
    """Return a mocked list of EC2 instances."""
    return [
        ec2_reservation(
            instances=[
                ec2_instance(
                    'running', None, 'us-east-1b', 'm4.large',
                    {'Name': 'test'}, 'i-456sdf4g'),
                ec2_instance(
                    'running', None, 'us-east-1b', 'm4.large', {},
                    'i-sdf3f4d6'),
                ec2_instance(
                    'stopped', None, 'us-east-1c', 't1.micro', {},
                    'i-dfgeqa53')
            ]
        )
    ]


def get_ec2_reserved_instances():
    """Return a mocked list of EC2 RIs."""
    return [
        ec2_ri('active', 'us-east-1b', 'c4.xlarge', 1,
               '2016-11-22T18:32:12.000Z'),
        ec2_ri('expired', 'us-east-1c', 'm4.large', 1,
               '2015-11-22T18:32:12.000Z'),
        ec2_ri('active', 'us-east-1b', 'm4.large', 1,
               '2016-11-22T18:32:12.000Z'),
    ]


def get_elc_instances():
    """Return a mocked list of ElastiCache instances."""
    return {
        'DescribeCacheClustersResponse': {
            'DescribeCacheClustersResult': {
                'CacheClusters': [
                    {
                        'CacheClusterStatus': 'available',
                        'Engine': 'redis',
                        'CacheNodeType': 'cache.t2.small',
                        'CacheClusterId': 'test1',
                    },
                    {
                        'CacheClusterStatus': 'stopped',
                        'Engine': 'redis',
                        'CacheNodeType': 'cache.m3.medium',
                        'CacheClusterId': 'test2',
                    }
                ]
            }
        }
    }


def get_elc_reserved_instances():
    """Return a mocked list of ElastiCache RIs."""
    return {
        'DescribeReservedCacheNodesResponse': {
            'DescribeReservedCacheNodesResult': {
                'ReservedCacheNodes': [
                    {
                        'State': 'active',
                        'ProductDescription': 'redis',
                        'CacheNodeType': 'cache.m1.medium',
                        'CacheNodeCount': 1,
                        'StartTime': 1473804560.474,
                        'Duration': 31536000,
                    },
                    {
                        'State': 'expired',
                        'ProductDescription': 'redis',
                        'CacheNodeType': 'cache.t2.small',
                        'CacheNodeCount': 1,
                        'StartTime': 1473798124.580,
                        'Duration': 31536000,
                    }
                ]
            }
        }
    }


def get_rds_instances():
    """Return a mocked list of RDS instances."""
    return [
        rds_instance('available', True, 'db.t2.medium', 'test1'),
        rds_instance('stopped', False, 'db.m3.medium', 'test2')
    ]


def get_rds_reserved_instances():
    """Return a mocked list of RDS RIs."""
    return {
        'ReservedDBInstances': [
            {
                'State': 'active',
                'MultiAZ': True,
                'DBInstanceClass': 'db.m4.xlarge',
                'DBInstanceCount': 1,
                'StartTime': datetime.datetime(
                    2016, 8, 24, 20, 23, 4, 753000, tzinfo=tzutc()),
                'Duration': 31536000,
            },
            {
                'State': 'expired',
                'MultiAZ': False,
                'DBInstanceClass': 'db.m4.large',
                'DBInstanceCount': 1,
                'StartTime': datetime.datetime(
                    2015, 8, 24, 20, 23, 4, 753000, tzinfo=tzutc()),
                'Duration': 31536000,
            }
        ]
    }


def test_bad_aws_config():
    """Test loading a bad config file with missing AWS options."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.bad_aws'])

    assert ('Required configuration option for an AWS account '
            '(aws_secret_access_key)' in result.output)


def test_bad_email_config():
    """Test loading a bad config file with missing email options."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.bad_email'])

    assert ('Required configuration option for email '
            '(smtp_host)' in result.output)


def test_config_empty():
    """Test loading an empty config file."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.empty'])

    assert ('Please specify at least one [AWS ] section in the configuration '
            'file!' in result.output)


def test_not_aws_config():
    """Test loading a non-blank config with no AWS sections."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.no_aws'])

    assert ('Please specify at least one [AWS ] section in the configuration '
            'file!' in result.output)


@mock.patch('check_reserved_instances.calculate.boto.ec2.connect_to_region')
def test_success_no_email(mocked_ec2):
    """Test a successful run without email."""
    mocked_ec2.return_value.get_all_instances.return_value = (
        get_ec2_instances())

    mocked_ec2.return_value.get_all_reserved_instances.return_value = (
        get_ec2_reserved_instances())

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.no_email'])

    assert 'Not sending email for this report' in result.output


@mock.patch('check_reserved_instances.calculate.boto.ec2.connect_to_region')
@mock.patch('check_reserved_instances.report.smtplib')
def test_success_no_email_tls(mocked_smtplib, mocked_ec2):
    """Test a successful run with email but without TLS or SMTP auth."""
    mocked_ec2.return_value.get_all_instances.return_value = (
        get_ec2_instances())

    mocked_ec2.return_value.get_all_reserved_instances.return_value = (
        get_ec2_reserved_instances())

    mocked_smtplib.return_value.sendmail.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.email_no_tls'])

    assert 'Sending emails to test@example.com' in result.output


@mock.patch('check_reserved_instances.calculate.boto.ec2.connect_to_region')
@mock.patch('check_reserved_instances.calculate.boto.elasticache.'
            'connect_to_region')
@mock.patch('check_reserved_instances.calculate.boto.rds.connect_to_region')
@mock.patch('check_reserved_instances.calculate.boto3.client')
@mock.patch('check_reserved_instances.report.smtplib')
def test_success_run(mocked_smtplib, mocked_boto3, mocked_rds, mocked_elc,
                     mocked_ec2):
    """Test a successful run for all services with email."""
    mocked_boto3.return_value.describe_reserved_db_instances.return_value = (
        get_rds_reserved_instances())

    mocked_rds.return_value.get_all_dbinstances.return_value = (
        get_rds_instances())

    mocked_elc.return_value.describe_cache_clusters.return_value = (
        get_elc_instances())

    mocked_elc.return_value.describe_reserved_cache_nodes.return_value = (
        get_elc_reserved_instances())

    mocked_ec2.return_value.get_all_instances.return_value = (
        get_ec2_instances())

    mocked_ec2.return_value.get_all_reserved_instances.return_value = (
        get_ec2_reserved_instances())

    mocked_smtplib.return_value.starttls.return_value = True
    mocked_smtplib.return_value.login.return_value = True
    mocked_smtplib.return_value.sendmail.return_value = True

    runner = CliRunner()
    result = runner.invoke(
        cli, ['--config', 'tests/fixtures/config.ini.testing'])

    assert 'AWS account1 Reserved Instances Report' in result.output
    assert 'AWS account2 Reserved Instances Report' in result.output
    assert 'Sending emails to test@example.com' in result.output
