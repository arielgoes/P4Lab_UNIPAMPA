"""A central controller computing and installing shortest paths.
"""

import os
import sys
#from cli import CLI
from re import search
from random import random
from networkx.algorithms import all_pairs_dijkstra

from p4utils.utils.helper import load_topo
from p4utils.utils.topology import *
from p4utils.utils.sswitch_thrift_API import SimpleSwitchThriftAPI
from collections import defaultdict

from time import sleep

from scapy.all import Packet
from scapy.all import sniff, sendp, hexdump, get_if_list, get_if_hwaddr, bind_layers
from scapy.all import Packet, IPOption
from scapy.all import IP, UDP, Raw, Ether
from scapy.layers.inet import _IPOption_HDR
from scapy.fields import *

# this function will be held by the CLI later...
import subprocess


class RerouteController(object):
    """Controller for the fast rerouting exercise."""

    def __init__(self):
        """Initializes the topology and data structures."""

        if not os.path.exists('topology.json'):
            print("Could not find topology object!\n")
            raise Exception

        self.topo = load_topo('topology.json')
        self.controllers = {}
        self.connect_to_switches()
        self.reset_states()
        
    
    def install_rules(self):
    	#TO-DO

    	#the line below gives me access to switch 's1'
    	control = self.controllers=['s1'] 

    	#now, install a table rule at 's1' to forward packets to 's2'

    	#the line below ... 's2'
    	control = self.controllers=['s2']

    	#now, ... to forward packets from 's2' to 'h2'


    	#AFTER installing the table rules to forward from 'h1' to 'h2', do the opposite way: 'h2' to 'h1'.




    #def do_reset(self, line=""):  # pylint: disable=unused-argument
    def do_reset(self, line):
        """Set all interfaces back up."""
        failed_links = self.check_all_links()
        for link in failed_links:
            print("Resetting failure for link %s-%s." % link)
            self.update_interfaces(link, "up")
            #self.update_linkstate(link, "up")


    def connect_to_switches(self):
        """Connects to all the switches in the topology."""
        for p4switch in self.topo.get_p4switches():
            thrift_port = self.topo.get_thrift_port(p4switch)
            self.controllers[p4switch] = SimpleSwitchThriftAPI(thrift_port)


    def reset_states(self):
        """Resets registers, tables, etc."""
        for control in self.controllers.values():
            control.reset_state()


    def get_host_net(self, host):
        """Return ip and subnet of a host.

        Args:
            host (str): The host for which the net will be returned.

        Returns:
            str: IP and subnet in the format "address/mask".
        """
        gateway = self.topo.get_host_gateway_name(host)
        return self.topo.get_intfs()[host][gateway]['ip']


    # this function will be held by the CLI later... For it is a static entry: "fail s2 s3"
    #def do_fail(self, line=""):
    def do_fail(self, line): 
        """Fail a link between two nodes.

        Usage: fail_link node1 node2
        """
        try:
            node1, node2 = line.split()
            link = (node1, node2)
        except ValueError:
            print("Provide exactly two arguments: node1 node2")
            return

        for node in (node1, node2):
            if node not in self.controllers:
                print("%s is not a valid node!" % node, \
                    "You can only fail links between switches")
                return

        if node2 not in self.topo.get_intfs()[node1]:
            print("The link %s-%s does not exist." % link)
            return

        failed_links = self.check_all_links()
        for failed_link in failed_links:
            if failed_link in [(node1, node2), (node2, node1)]:
                print("The link %s-%s is already down!" % (node1, node2))
                return

        print("Failing link %s-%s." % link)

        self.update_interfaces(link, "down")
        #self.update_linkstate(link, "down")


    # this function will be held by the CLI later...
    def update_interfaces(self, link, state):
        """Set both interfaces on link to state (up or down)."""
        if1, if2 = self.get_interfaces(link)
        self.update_if(if1, state)
        self.update_if(if2, state)
        #print('link: ' + str(link))
        #print('if1: ' + str(if1) + ' if2: ' + str(if2))


    # this function will be held by the CLI later...
    def check_all_links(self):
        """Check the state for all link interfaces."""
        failed_links = []
        switchgraph = self.topo.subgraph(
            list(self.controllers.keys())
        )
        for link in switchgraph.edges:
            if1, if2 = self.get_interfaces(link)
            if not (self.if_up(if1) and self.if_up(if2)):
                failed_links.append(link)
        return failed_links


    # this function will be held by the CLI later...
    def get_interfaces(self, link):
        """Return tuple of interfaces on both sides of the link."""
        node1, node2 = link
        if_12 = self.topo.get_intfs()[node1][node2]['intfName']
        if_21 = self.topo.get_intfs()[node2][node1]['intfName']
        return if_12, if_21


    # this function will be held by the CLI later...
    @staticmethod
    def if_up(interface):
        """Return True if interface is up, else False."""
        cmd = ["ip", "link", "show", "dev", interface]
        return b"state UP" in subprocess.check_output(cmd)


    # this function will be held by the CLI later...
    @staticmethod
    def update_if(interface, state):
        """Set interface to state (up or down)."""
        print("Set interface '%s' to '%s'." % (interface, state))
        cmd = ["sudo", "ip", "link", "set", "dev", interface, state]
        subprocess.check_call(cmd)

if __name__ == "__main__":
    controller = RerouteController()  # pylint: disable=invalid-name
    #CLI(controller)
