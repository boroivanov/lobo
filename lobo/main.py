import sys
import boto3
import click
import click_spinner

from botocore.exceptions import ProfileNotFound, NoRegionError

version = '0.0.1'

PAGE_SIZE = 100


@click.command()
@click.version_option(version=version, message=version)
@click.option('-p', '--profile', help='AWS profile')
@click.option('-r', '--region', help='AWS region')
def cli(region, profile):
    session = create_boto_session(region, profile)
    elb = create_boto_client(session, 'elb')
    elbv2 = create_boto_client(session, 'elbv2')

    with click_spinner.spinner():
        elb_lbs = describe_load_balancers_elb(elb)
        elbv2_lbs = describe_load_balancers_elbv2(elbv2)
        lbs = elb_lbs + elbv2_lbs
        lb_names = [x['LoadBalancerName'] for x in lbs]
        lbs_name_max_len = len(max(lb_names, key=len))

    for lb in sorted(lbs, key=lambda k: k['LoadBalancerName']):
        print('{name:{name_pad}}  {scheme:15}  {type:11}'.format(
            name=lb['LoadBalancerName'],
            name_pad=lbs_name_max_len,
            scheme=lb['Scheme'],
            type=lb.get('Type', 'classic')
        )
        )


def describe_load_balancers_elb(client, names=[], page_size=PAGE_SIZE):
    params = {'LoadBalancerNames': names, 'PageSize': page_size}
    key = 'LoadBalancerDescriptions'
    return loop_load_balancers_pager(client, params, key)


def describe_load_balancers_elbv2(client, names=[], page_size=PAGE_SIZE):
    params = {'Names': names, 'PageSize': page_size}
    key = 'LoadBalancers'
    return loop_load_balancers_pager(client, params, key)


def loop_load_balancers_pager(client, params, key):
    response = None
    lbs = []
    while True:
        if response:
            if 'NextMarker' not in response:
                break
            else:
                params['Marker'] = response['NextMarker']
        response = client.describe_load_balancers(**params)
        lbs += response[key]
    return lbs


def create_boto_session(region, profile):
    try:
        return boto3.session.Session(profile_name=profile, region_name=region)
    except ProfileNotFound as e:
        click.echo(e, err=True)
        sys.exit(1)


def create_boto_client(session, client):
    try:
        return session.client(client)
    except NoRegionError as e:
        click.echo(e, err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
