#!/bin/bash
# devstack/plugin.sh
# Functions to control the configuration and operation of the baremetal-network-provisioning(bnp)
# Dependencies:
#
# ``functions`` file
# ``DEST`` must be defined
# ``STACK_USER`` must be defined
# ``stack.sh`` calls the entry points in this order:
# Save trace setting

XTRACE=$(set +o | grep xtrace)
set +o xtrace

function install_bnp {
   setup_develop $BNP_DIR
}

function run_bnp_alembic_migration {
   $NEUTRON_BIN_DIR/neutron-db-manage --config-file /etc/neutron/neutron.conf  --config-file /etc/neutron/plugins/ml2/ml2_conf.ini  upgrade head
}

function configure_bnp_plugin { 
    if [ ! -d $NEUTRON_CONF_DIR ]; then
       sudo mkdir -p $NEUTRON_CONF_DIR
       sudo chown -R $STACK_USER:root /etc/neutron
    fi
    cp $BNP_DIR/etc/ml2_conf_hp.ini $BNP_ML2_CONF_HP_FILE
    iniset $BNP_ML2_CONF_HP_FILE default snmp_timeout $SNMP_TIMEOUT
    iniset $BNP_ML2_CONF_HP_FILE default snmp_retries $SNMP_RETRIES
    iniadd $BNP_ML2_CONF_HP_FILE ml2_hp net_provisioning_driver $NET_PROVISIONING_DRIVER
    iniset $BNP_ENTRY_POINT_FILE neutron.ml2.mechanism_drivers hp $HP_MECHANISM_DRIVER
    iniset $BNP_ENTRY_POINT_FILE neutron.ml2.extension_drivers bnp_ext_driver $BNP_EXTENSION_DRIVER
}


# main loop
if is_service_enabled bnp-plugin; then
    if [[ "$1" == "source" ]]; then
        # no-op
        :
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
        install_bnp
        configure_bnp_plugin
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        run_bnp_alembic_migration
    elif [[ "$1" == "stack" && "$2" == "post-extra" ]]; then
        # no-op
        :
    fi

    if [[ "$1" == "unstack" ]]; then
        # no-op
        :
    fi

    if [[ "$1" == "clean" ]]; then
        # no-op
        :
    fi
fi

# Restore xtrace
$XTRACE
