import sys
import boto3
import click
import click_spinner
import threading
import queue

from botocore.exceptions import ProfileNotFound, NoRegionError, ClientError

version = '0.0.4'

PAGE_SIZE = 100


@click.command()
@click.version_option(version=version, message=version)
@click.argument('name', required=False)
@click.option('-s', '--scheme', is_flag=True, help='Show scheme')
@click.option('-t', '--lb-type', is_flag=True, help='Show type')
@click.option('-p', '--profile', help='AWS profile')
@click.option('-r', '--region', help='AWS region')
def cli(name, region, profile, scheme, lb_type):
    session = create_boto_session(region, profile)
    elb = create_boto_client(session, 'elb')
    elbv2 = create_boto_client(session, 'elbv2')

    with click_spinner.spinner():
        lbs = describe_all_load_balancers(elb, elbv2, name)

    if len(lbs) == 0:
        click.echo('No matches found.')
        sys.exit(0)
    print_load_balancers_info(lbs, scheme=scheme, lb_type=lb_type)


def print_load_balancers_info(lbs, **kwargs):
    name_pad = max_len_value_in_dict(lbs, 'LoadBalancerName')
    scheme_pad = max_len_value_in_dict(lbs, 'Scheme')
    type_pad = max_len_value_in_dict(lbs, 'Type')

    for lb in sorted(lbs, key=lambda k: k['LoadBalancerName']):
        template = '{name:{name_pad}}'
        params = {
            'name': lb['LoadBalancerName'],
            'name_pad': name_pad,
            'scheme_pad': scheme_pad,
            'type_pad': type_pad,
            'lb': lb,
        }
        template, params = show_toggled_outputs(template, params, **kwargs)

        template += '  {states}'
        params['states'] = lb.get('states', '')
        click.echo(template.format(**params))


def describe_all_load_balancers(elb, elbv2, name):
    '''
    Describe both elb and elbv2 load balancers.

    if `name` is not set.
        - Returns a list of load balancers.

    if `name` is set:
        - Retruns a list of a single load balancer if `name` matches.
        - Otherwise, returns a list of load balancers which contain `name`.
    '''
    lbs = []
    name_filter_set = False
    if name:
        try:
            return describe_load_balancers_elb(elb, [name])
        except ClientError:
            pass
        try:
            return describe_load_balancers_elbv2(elbv2, [name])
        except ClientError:
            pass
        if len(lbs) == 0:
            name_filter_set = True

    names = []
    lbs += describe_load_balancers_elb(elb, names)
    lbs += describe_load_balancers_elbv2(elbv2, names)

    if name_filter_set:
        lbs = list(filter(lambda x: name in x['LoadBalancerName'], lbs))

    return lbs


def describe_load_balancers_elb(client, names, page_size=PAGE_SIZE):
    params = {'LoadBalancerNames': names, 'PageSize': page_size}
    key = 'LoadBalancerDescriptions'
    lbs = loop_load_balancers_pager(client, params, key)

    q = queue.Queue()
    threads = []

    for lb in lbs:
        t = threading.Thread(target=describe_elb, args=(client, lb, q))
        t.start()
        threads.append(t)

    [t.join() for t in threads]

    return [q.get(t) for t in threads]


def describe_load_balancers_elbv2(client, names, page_size=PAGE_SIZE):
    params = {'Names': names}
    if len(names) == 0:
        params['PageSize'] = page_size
    key = 'LoadBalancers'
    lbs = loop_load_balancers_pager(client, params, key)

    q = queue.Queue()
    threads = []

    for lb in lbs:
        t = threading.Thread(target=describe_elbv2, args=(client, lb, q))
        t.start()
        threads.append(t)

    [t.join() for t in threads]
    return [q.get(t) for t in threads]


def describe_elb(client, lb, queue):
    '''Queue adding the elb state of an instance to the elb dict.

    :param client: elb client
    :type client: boto.client
    :param lb: load balancer dict
    :type lb: dict
    :param queue: Queue
    :type queue: queue.Queue
    :return: None
    '''
    instances = describe_instance_health(client, lb['LoadBalancerName'])
    states = aggregate_health_states(instances)
    lb['states'] = dict_to_str(states)
    queue.put(lb)


def describe_elbv2(client, lb, queue):
    '''Queue adding the elbv2 state of a target to the elbv2 dict.

    :param client: elbv2 client
    :type client: boto.client
    :param lb: load balancer v2 dict
    :type lb: dict
    :param queue: Queue
    :type queue: queue.Queue
    :return: Queue
    '''
    target_groups = describe_target_groups(client, lb['LoadBalancerArn'])

    if len(target_groups) >= 1:
        for tg in target_groups:
            states = describe_target_group_states(client, tg['TargetGroupArn'])
            lb['states'] = dict_to_str(states)
    else:
        lb['states'] = ''

    queue.put(lb)


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


def max_len_value_in_dict(l, key):
    v_l = [x.get(key, ' ') for x in l]
    return len(max(v_l, key=len))


def show_toggled_outputs(template, params, **kwargs):
    for key, value in kwargs.items():
        if key == 'scheme' and value:
            template, params = toggle_scheme_output(template, params)
        elif key == 'lb_type' and value:
            template, params = toggle_type_output(template, params)
    return template, params


def toggle_scheme_output(template, params):
    template += '  {scheme:{scheme_pad}}'
    params['scheme'] = params['lb']['Scheme']
    return template, params


def toggle_type_output(template, params):
    template += '  {type:{type_pad}}'
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


def dict_to_str(d):
    return ' '.join(['{}: {}'.format(k, v) for k, v in d.items()])


if __name__ == '__main__':
    cli()
