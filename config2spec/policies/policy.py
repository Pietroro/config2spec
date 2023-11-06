#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from enum import Enum
import re

class PolicyType(Enum):
    Reachability = 1
    Isolation = 2
    Waypoint = 3
    LoadBalancingSimple = 4
    LoadBalancingEdgeDisjoint = 5
    LoadBalancingNodeDisjoint = 6

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    def __eq__(self, other):
        # Helper method to equate to string
        # Check if 'other' is a string
        if isinstance(other, str):
            try:
                # Split the string into 'enum_name' and 'option_name'
                enum_name, option_name = other.split('.')
                # Check if 'enum_name' matches the name of the enum class, and 'option_name' matches the enum member's name
                if enum_name == self.__class__.__name__ and option_name == self.name:
                    return True
            except ValueError:
                pass  # Ignore exceptions caused by an improperly formatted string
        # If 'other' is not a string or the comparison fails, use the default equality comparison
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)

class PolicySource(object):
    def __init__(self, router):
        self.router = router

    def __str__(self):
        return self.router

    def __repr__(self):
        return str(self)

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.router >= other.router
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.router > other.router
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.router <= other.router
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.router < other.router
        return NotImplemented

    def __eq__(self, other):
        if type(other) == PolicySource:
            return self.router == other.router
        else:
            return False

    def __hash__(self):
        return hash(self.__str__())


class PolicyDestination(object):
    def __init__(self, router, interface, subnet):
        self.router = router
        self.interface = interface
        self.subnet = subnet

    def __str__(self):
        return "{router}:{interface} ({subnet})".format(
            router=self.router, interface=self.interface, subnet=self.subnet)
    
    def __repr__(self):
        return str(self)

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.router >= other.router
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.router > other.router
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.router <= other.router
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.router < other.router
        return NotImplemented

    def __eq__(self, other):
        if type(other) == PolicyDestination:
            return self.router == other.router and self.interface == other.interface and self.subnet == other.subnet
        else:
            return False

    def __hash__(self):
        return hash(self.__str__())
    
    @classmethod
    def from_string(cls, str):
        # Define a regular expression pattern to match the expected format
        pattern = r'^(?P<router>[^:]+):(?P<interface>[^ ]+) \((?P<subnet>[^)]+)\)$'

        # Use re.match to check if the input string matches the pattern
        match = re.match(pattern, str)

        if match:
            # If there is a match, extract the values into variables
            router = match.group('router')
            interface = match.group('interface')
            subnet = match.group('subnet')
        else:
            # If no match is found, return None or raise an exception as needed
            return None
        
        # Create an instance of the class with the extracted data
        instance = cls(router, interface, subnet)
        return instance


class Policy(object):
    def __init__(self, type, sources, destinations, negate=False):
        self.type = type
        self.sources = sources  # list of PolicySource objects
        self.destinations = destinations  # list of PolicyDestination objects
        self.negate = negate

    def __str__(self):
        sources_str = "{{{sources}}}".format(sources=", ".join(str(source) for source in self.sources))
        destinations_str = "{{{destinations}}}".format(
            destinations=", ".join(str(destination) for destination in self.destinations))
        return "{policy_type} policy: {sources}->{destinations}, negate={negated}".format(
            policy_type=self.type, sources=sources_str, destinations=destinations_str, negated=self.negate)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if self.type == other.type and self.sources == other.sources and \
                self.destinations == other.destinations and self.negate == other.negate:
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.__str__())

    def get_coverage(self):
        coverage = len(self.sources) * len(self.destinations)
        return coverage

    @staticmethod
    def get_policy(policy_type, sources, destinations, specifics):
        if policy_type == PolicyType.Reachability:
            policy = ReachabilityPolicy(sources, destinations, negate=False)
        elif policy_type == PolicyType.Isolation:
            policy = ReachabilityPolicy(sources, destinations, negate=True)
        elif policy_type == PolicyType.Waypoint:
            policy = WaypointPolicy(sources, destinations, waypoints=specifics)
        elif policy_type == PolicyType.LoadBalancingSimple:
            policy = LoadBalancingPolicy(sources, destinations, num_paths=specifics)
        else:
            policy = None
        return policy
    
    @classmethod
    def from_df(cls, df):
        # Quick and dirty (maybe TODO: make this less ugly)
        # Extract the type from the DataFrame
        type = df.type
        sources = [df.source]
        # Extract destinations from the string set
        str_destinations = df.Destinations[1:-1].split(', ')
        destinations = [PolicyDestination.from_string(dest) for dest in str_destinations]
        specifics = int(df.specifics) if df.specifics.isdigit() else df.specifics

        policy = Policy.get_policy(type, sources, destinations, specifics)
        
        return policy


class ReachabilityPolicy(Policy):
    def __init__(self, sources, destinations, negate=False):
        super(ReachabilityPolicy, self).__init__("reachability", sources, destinations, negate=negate)


class LoadBalancingPolicy(Policy):
    def __init__(self, sources, destinations, num_paths):
        super(LoadBalancingPolicy, self).__init__("loadbalancing", sources, destinations)
        self.num_paths = num_paths

    def __str__(self):
        output = super(LoadBalancingPolicy, self).__str__()
        return '%s - NumPaths %d' % (output, self.num_paths)

    def __eq__(self, other):
        if super(LoadBalancingPolicy, self).__eq__(other) and self.num_paths == other.num_paths:
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.__str__())


class WaypointPolicy(Policy):
    def __init__(self, sources, destinations, waypoints):
        super(WaypointPolicy, self).__init__("waypoint", sources, destinations)
        self.waypoints = waypoints

    def __str__(self):
        output = super(WaypointPolicy, self).__str__()
        return "{policy_string} - Waypoints {waypoints}".format(policy_string=output, waypoints=self.waypoints)

    def __eq__(self, other):
        if super(WaypointPolicy, self).__eq__(other) and self.waypoints == other.waypoints:
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.__str__())