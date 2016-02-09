1. Download DevStack

2. Add this repo as an external repository:

    cat >local.conf <<END
   [[local|localrc]] enable_plugin baremetal-network-provisioning https://github.com/hp-networking/baremetal-network-provisioning
    enable_service bnp-plugin

    #add hp to Q_ML2_PLUGIN_MECHANISM_DRIVERS

    Q_ML2_PLUGIN_MECHANISM_DRIVERS=openvswitch,l2population,hp
    
    #append the below lines

    Q_ML2_PLUGIN_EXT_DRIVERS=port_security,bnp_ext_driver
    Q_PLUGIN_EXTRA_CONF_PATH=etc/neutron/plugins/ml2
    Q_PLUGIN_EXTRA_CONF_FILES=(ml2_conf_hp.ini)
	
	END


3. run stack.sh
