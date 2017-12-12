"""Results calculation functions."""

import datetime
from check_reserved_instances.normalized_units import normalized_units_per_hour

def calc_expiry_time(expiry):
    """Calculate the number of days until the reserved instance expires.

    Args:
        expiry (DateTime): A timezone-aware DateTime object of the date when
            the reserved instance will expire.

    Returns:
        The number of days between the expiration date and now.

    """
    return (expiry.replace(tzinfo=None) - datetime.datetime.utcnow()).days



def report_diffs(running_instances, reserved_instances):
    """Calculate differences between reserved instances and running instances.

    Prints a message string containg unused reservations, unreserved instances,
    and counts of running and reserved instances.

    Args:
        running_instances (dict): Dictionary object of running instances. Key
            is the unique identifier for RI's (instance type and availability
            zone). Value is the count of instances with those properties.
        reserved_instances (dict): Dictionary of reserved instances in the same
            format as running_instances.

    Returns:
        A dict of the unused reservations, unreserved instances and counts of
        each.

    """
    instance_diff = {}
    regional_benefit_ris = {}
    # loop through the reserved instances
    for placement_key in reserved_instances:
        # if the AZ from an RI is 'All' (regional benefit RI)
        if placement_key[1] == 'All':
            # put into another dict for these RIs for processing later
            regional_benefit_ris[placement_key[0]] = reserved_instances[
                placement_key]
        else:
            instance_diff[placement_key] = reserved_instances[
                placement_key] - running_instances.get(placement_key, 0)

    # add unreserved instances to instance_diff
    for placement_key in running_instances:
        if placement_key not in reserved_instances:
            instance_diff[placement_key] = -running_instances[
                placement_key]

    # loop through regional benefit RI's
    for ri in regional_benefit_ris:
        # loop through the entire instace diff
        for placement_key in instance_diff:
            # find unreserved instances with the same type as the regional
            # benefit RI
            if (placement_key[0] == ri and placement_key[1] != 'All' and
                    instance_diff[placement_key] < 0):
                # loop while incrementing unreserved instances (less than 0)
                # and decrementing count of regional benefit RI's
                while True:
                    if (instance_diff[placement_key] == 0 or
                            regional_benefit_ris[ri] == 0):
                        break
                    instance_diff[placement_key] += 1
                    regional_benefit_ris[ri] -= 1

        instance_diff[(ri, 'All')] = regional_benefit_ris[ri]

    unused_reservations = dict((key, value) for key, value in
                               instance_diff.items() if value > 0)
    unreserved_instances = dict((key, -value) for key, value in
                                instance_diff.items() if value < 0)

    qty_running_instances = 0
    for instance_count in running_instances.values():
        qty_running_instances += instance_count

    qty_reserved_instances = 0
    for instance_count in reserved_instances.values():
        qty_reserved_instances += instance_count

    return {
        'unused_reservations': unused_reservations,
        'unreserved_instances': unreserved_instances,
        'qty_running_instances': qty_running_instances,
        'qty_reserved_instances': qty_reserved_instances
    }





def report_normlaized_unit_diffs(running_instances, reserved_instances, total_normalized_units_per_hour):

    """Calculate differences between reserved instances and running instances.

    Prints a message string containg unused reservations, unreserved instances,
    and counts of running and reserved instances.

    Args:
        running_instances (dict): Dictionary object of running instances. Key
            is the unique identifier for RI's (instance type and availability
            zone). Value is the count of instances with those properties.
        reserved_instances (dict): Dictionary of reserved instances in the same
            format as running_instances.
        total_normalized_units_per_hour (dict): Dictionary object of instance families and corresponding
            reserved units.

    Returns:
        A dict of the unused reservations, unreserved instances and counts of
        each.

    """
    instance_diff = {}
    regional_benefit_ris = {}
    # loop through the reserved instances
    for placement_key in reserved_instances:
        # if the AZ from an RI is 'All' (regional benefit RI)
        if placement_key[1] == 'All':
            # put into another dict for these RIs for processing later
            regional_benefit_ris[placement_key[0]] = reserved_instances[
                placement_key]
        else:
            instance_diff[placement_key] = reserved_instances[
                                               placement_key] - running_instances.get(placement_key, 0)

    # add unreserved instances to instance_diff
    for placement_key in running_instances:
        if placement_key not in reserved_instances:
            instance_diff[placement_key] = -running_instances[
                placement_key]

    # loop through regional benefit RI's
    normalized_units_diff = total_normalized_units_per_hour.copy()
    for placement_key in instance_diff:
        placement_family, placement_size = placement_key[0].split('.')
        if instance_diff[placement_key] <= 0:
            normalized_units_diff[placement_family] =  normalized_units_diff.get(placement_family, 0) + normalized_units_per_hour[placement_size] * instance_diff[placement_key]
            instance_diff[placement_key] += 1

    unused_reservations = dict((key, value) for key, value in
                               instance_diff.items() if value > 0)
    unreserved_instances = dict((key, -value) for key, value in
                                normalized_units_diff.items() if value < 0)

    qty_running_instances = 0
    for instance_count in running_instances.values():
        qty_running_instances += instance_count

    qty_reserved_instances = 0
    for instance_count in reserved_instances.values():
        qty_reserved_instances += instance_count


    return {
            'unused_reservations': unused_reservations,
            'unreserved_instances': unreserved_instances,
            'qty_running_instances': qty_running_instances,
            'qty_reserved_instances': qty_reserved_instances
        }
