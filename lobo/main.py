import sys
import boto3
import click
import click_spinner

from botocore.exceptions import ProfileNotFound, NoRegionError

version = '0.0.1'

PAGE_SIZE = 100


@click.command()
@click.version_option(version=version, message=version)
@click.option('-s', '--scheme', is_flag=True, help='Show scheme')
@click.option('-t', '--lb-type', is_flag=True, help='Show type')
@click.option('-p', '--profile', help='AWS profile')
@click.option('-r', '--region', help='AWS region')
def cli(region, profile, scheme, lb_type):
    session = create_boto_session(region, profile)
    elb = create_boto_client(session, 'elb')
    elbv2 = create_boto_client(session, 'elbv2')

    with click_spinner.spinner():
        lbs = describe_all_load_balancers(elb, elbv2)

    print_load_balancers_info(lbs, scheme=scheme, lb_type=lb_type)


def print_load_balancers_info(lbs, **kwargs):
    name_pad = lb_name_max_len(lbs)
    for lb in sorted(lbs, key=lambda k: k['LoadBalancerName']):
        template = '{name:{name_pad}}'
        params = {
            'name': lb['LoadBalancerName'],
            'name_pad': name_pad,
            'lb': lb,
        }
        template, params = show_toggled_outputs(template, params, **kwargs)

        template += '  {states}'
        params['states'] = lb.get('states', '')
        click.echo(template.format(**params))


def describe_all_load_balancers(elb, elbv2):
    elb_lbs = describe_load_balancers_elb(elb)
    elbv2_lbs = describe_load_balancers_elbv2(elbv2)
    return elb_lbs + elbv2_lbs


def describe_load_balancers_elb(client, names=[], page_size=PAGE_SIZE):
    params = {'LoadBalancerNames': names, 'PageSize': page_size}
    key = 'LoadBalancerDescriptions'
    lbs = loop_load_balancers_pager(client, params, key)
    for lb in lbs:
        instances = describe_instance_health(client, lb['LoadBalancerName'])
        states = aggregate_health_states(instances)
        lb['states'] = states
    return lbs


def describe_load_balancers_elbv2(client, names=[], page_size=PAGE_SIZE):
    params = {'Names': names, 'PageSize': page_size}
    key = 'LoadBalancers'
    lbs = loop_load_balancers_pager(client, params, key)
    for lb in lbs:
        for tg in describe_target_groups(client, lb['LoadBalancerArn']):
            states = describe_target_group_states(client, tg['TargetGroupArn'])
            lb['states'] = states
    return lbs


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


def describe_instance_health(client, lb_name):
    '''Describe elb health states'''
    response = client.describe_instance_health(LoadBalancerName=lb_name)
    return response['InstanceStates']


def describe_target_groups(client, lb_arn):
    '''Describe elbv2 health states'''
    response = client.describe_target_groups(LoadBalancerArn=lb_arn)
    return response['TargetGroups']


def describe_target_group_states(elbv2, tg_arn):
    targets = elbv2.describe_target_health(TargetGroupArn=tg_arn)
    return aggregate_health_states(targets['TargetHealthDescriptions'])


def aggregate_health_states(targets):
    '''Aggregate elb or elbv2 health stats'''
    states = {}
    for t in targets:
        if 'TargetHealth' in t:
            state = t['TargetHealth']['State']
        else:
            state = t['State']
        if state in states:
            states[state] += 1
        else:
            states[state] = 1
    return states


def lb_name_max_len(lbs):
    lb_names = [x['LoadBalancerName'] for x in lbs]
    return len(max(lb_names, key=len))


def show_toggled_outputs(template, params, **kwargs):
    for key, value in kwargs.items():
        if key == 'scheme' and value:
            template, params = toggle_scheme_output(template, params)
        elif key == 'lb_type' and value:
            template, params = toggle_type_output(template, params)
    return template, params


def toggle_scheme_output(template, params):
    template += '  {scheme:15}'
    params['scheme'] = params['lb']['Scheme']
    return template, params


def toggle_type_output(template, params):
    template += '  {type:11}'
    params['type'] = params['lb'].get('Type', 'classic')
    return template, params


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
