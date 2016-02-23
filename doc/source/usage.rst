
========
Overview
========
.. _whatisbnp:

1. What is Bare Metal Network Provisioning (BNP)
================================================

Openstack Ironic project deals with provisioning BM servers. However, plumbing BM servers into tenant networks has been a manual procedure by the Cloud Admin.
	Within the timeframe of Liberty Release of Openstack, we are attempting to spruce-up Ironic to automate plumbing BM servers into tenant networks. Since Openstack Neutron project deals with plumbing ports on tenant-network in the cloud, Ironic has requested the Neutron team to provide enhancement to enable plumb the BM server ports into Cloud infrastructure (part of solution).
	Initially, Openstack Neutron will be extended to allow plumbing of BM server ports into only VLAN-based networks.  
These networks could either be a boot up network (ie., PXE booting network for BM servers) , or tenant network (for cloud to BM server communication) or cleaning-network (for recovering BM server used IP namespaces).


.. _model:
2. BNP models
=============
BNP introduces a various models to describe the relationship between neutron ports and the physical ports.

.. _cli:
3. BNP CLI's
============

Create Switch:
neutron-bnp switch-create --help (This command will provide help for giving parameters)
Example:
neutron-bnp switch-create xxx.xxx.xxx.xxx hpe snmpv2c --access_parameters write_community=public

Show Switch:
neutron-bnp switch-show --help (Help related to switch-show command)
Example:
neutron-bnp switch-show <switch_id>

List Switch
neutron-bnp switch-list --help (Help related to switch-list command)
Example:
neutron-bnp switch-list

Delete switch: This happens in 2 steps:
a.	Disable the switch:  neutron-bnp switch-update <switch_id> --enable=False
b.	Delete the switch: neutron-bnp switch-delete <switch_id>

Update Switch
a.	neutron-bnp switch-update –help

Example:
neutron-bnp switch-update $switch_id  --enable False --rediscover True
neutron-bnp switch-update $switch_id   --rediscover True

.. _deployment:
4. Deployment Components
========================
.. image:: images/bnp.png
           :height: 225px
           :width:  450px
           :align: center

.. _enablement:
5. Enable BNP code in devstack
===============================
Refer the below link 
https://github.com/hp-networking/baremetal-network-provisioning/blob/master/devstack/README.rst

.. _mechanism_driver:
6. Mechanism Driver Actions
===========================

Mechanism driver is listening for PortContext events from the ML2 Plugin . 
Implemented create_port_precommit(), update_port_precommit(), delete_port_precommit() & bind_port()
only bind_port() calls make the SNMP request to the switch.

when ironic invokes the neutron port-create calls to the neutron then mechanism driver takes the action accordingly.
The mechanism driver acts based on VNIC_TYPE =='baremetal' and process the neutron ports.

The physical information like switch_id and port_id is fetched from the 'local_link_information' list from portbindings.PROFILE


