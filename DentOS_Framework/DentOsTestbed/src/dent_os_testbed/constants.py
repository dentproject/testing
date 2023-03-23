""" Constants used in the Testbed application
"""
TESTBED_CONFIG_FILE_NAME = 'testbed_config.json'
PLATFORMS_CONSTANTS = '/DENT/DentOsTestbed/src/dent_os_testbed/utils/test_utils/data/platforms.json'
TEST_OUTPUT_FOLDER = 'test_output'
TESTBED_ARGS_FILE = 'testbed_args'
TESTBED_CONFIG_FILE = 'testbed_config.json'
TEST_DEFAULT_LOG_LEVEL = 4
OS_IMAGE_DOWNLOAD_URL = (
    'http://204.99.132.251/.dentos/testing/'
    'DENTOS-master_ONL-OS9_2020-09-01.2242-c800338_ARM64_INSTALLED_INSTALLER'
)
LOGDIR = 'logs'
DEFAULT_LOGGER = 'DENT'

# First define the suite in PYTEST_SUITES and map the suite to a suite group in
# PYTEST_SUITE_GROUPS. And every test should belong to a test suite either
# defined with scope of test-case, class or module level.
#
# options:
# ------------------------------
# 1. @pytest.mark.suite_test : decorator can be added to testcase or a class to
# add to suite
# 2. pytestmark = [pytest.mark.suite_test] : can be added to a modele test.py
# at the top the file to add the whole module to a test suite.
# 3. pytestmark = pytest.mark.suite_test : can be added inside a class to mark
# the class to particular test_suite
#
# Note: Markers are strictly enforced,
# 1. a test case which does not belong to any suite will not be run during
# framework execution
# 2. marking with a invalid "suite_" marker will also result in pytest failing
# to run
#
# Please use prefixes "suite_group_" and "suite_" to keep markers unique and
# consistent

PYTEST_SUITES = {
    'suite_test': 'Test marker',
    'suite_clean_config': 'Bringup the switch in clean state',
    'suite_unittest': 'Example suite for writing unit testcases which are run during bb',
    'suite_feature_f1': 'Test marker for feature f1',
    'suite_feature_f2': 'Test marker for feature f1',
    'suite_iproute2': 'Test marker for feature IpRoute2 Utility',
    'suite_arp': 'Test ARP feature',
    'suite_basic_trigger': 'Test marker for basic Triggres tests',
    'suite_traffic': 'Test marker for Traffic Generator Tests',
    'suite_tc_flower': 'Test marker for traffic class flow-er Tests',
    'suite_bgp_routes': 'Test bgp route flaps',
    'suite_stress': 'Test system for stress too many requests for memory, CPU, network',
    'suite_system_wide_testing': 'Test system wide restart and reloads',
    'suite_system_health': 'Test system wide health',
    'suite_connection': 'Marker for suite related to connection APIs like ssh, serial',
    'suite_onlpdump': 'Marker for suite related to sfp tests',
    'suite_poe': 'Marker for suite related to poe tests',
    'suite_lldp': 'Marker for suite related to lldp tests',
    'suite_system_verify': 'Marker for suite related to verification using batfish',
    'suite_system_bootstrap': 'Bootstrap the store setup',
    'suite_routing': 'routing related tets',
    'suite_bonding': 'bonding related tets',
    'suite_switching': 'Switching related tets',
    'suite_provisioning': 'Provisioning related tests',
    'suite_bgp_routing': 'BGP Routing related tests',
    'suite_filtering': 'filtering related tests',
    'suite_alpha_poe': 'Alpha Poe Related tests',
    'suite_services': 'Services related tests',
    'suite_vlan_port_isolation': 'VLAN Port Isolation related tests',
    'suite_acl_scale': 'ACL Scale related tests',
    'suite_acl_performance': 'ACL Performance related tests',
    'suite_poe_cli': 'POE related tests with the cli tool',
    'suite_cleanup': 'Test marker for test cleanup',
    'suite_functional_ipv4': 'Functional IPv4 tests',
    'suite_functional_ipv6': 'Functional IPv6 tests',
    'suite_functional_bridging': 'Functional bridging tests',
    'suite_functional_vlan': 'VLAN functional tests',
    'suite_functional_acl': 'Functional ACL tests',
    'suite_functional_qos': 'Functional QoS tests',
    'suite_functional_l1': 'Functional L1 tests',
    'suite_functional_port_isolation': 'Functional Port Isolation tests',
    'suite_functional_igmp': 'IGMP snooping functional tests',
}

PYTEST_SUITE_GROUPS = {
    'suite_group_test': ['suite_test', 'suite_feature_f1', 'suite_feature_f2'],
    'suite_group_clean_config': ['suite_clean_config'],
    'suite_group_l3_tests': ['suite_iproute2', 'suite_arp'],
    'suite_group_basic_trigger_tests': ['suite_basic_trigger'],
    'suite_group_traffic_tests': ['suite_traffic'],
    'suite_group_tc_tests': ['suite_tc_flower'],
    'suite_group_bgp_tests': ['suite_bgp_routes'],
    'suite_group_stress_tests': ['suite_stress'],
    'suite_group_system_wide_testing': ['suite_system_wide_testing'],
    'suite_group_system_health': ['suite_system_health'],
    'suite_group_store_bringup': ['suite_system_bootstrap', 'suite_system_verify'],
    'suite_group_alpha_lab_testing': [
        'suite_routing',
        # "suite_bonding",
        'suite_switching',
        'suite_provisioning',
        'suite_bgp_routing',
        'suite_filtering',
        'suite_alpha_poe',
        'suite_services',
    ],
    'suite_group_dentv2_testing': [
        'suite_vlan_port_isolation',
        'suite_acl_scale',
        'suite_acl_performance',
        'suite_poe_cli',
    ],
    'suite_group_connection': ['suite_connection'],
    'suite_group_platform': ['suite_poe', 'suite_onlpdump', 'suite_lldp'],
    'suite_group_cleanup': ['suite_cleanup'],
    'suite_group_functional': [
        'suite_functional_vlan',
        'suite_functional_bridging',
        'suite_functional_acl',
        'suite_functional_qos',
        'suite_functional_ipv4',
        'suite_functional_ipv6',
        'suite_functional_l1',
        'suite_functional_port_isolation',
        'suite_functional_igmp',
    ]
}
