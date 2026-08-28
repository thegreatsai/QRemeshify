import json

from app.services.cli_export import (
    SwitchPortConfig,
    export_switch_config,
    generate_ios_config,
    generate_meraki_port_list,
)


def test_ios_config_access_port_with_vlan():
    ports = [SwitchPortConfig(port_number=1, mode="access", vlan_number=10, description="Room 101")]
    text = generate_ios_config("Cisco 2960-48", ports)
    assert "interface GigabitEthernet1/0/1" in text
    assert " description Room 101" in text
    assert " switchport mode access" in text
    assert " switchport access vlan 10" in text


def test_ios_config_trunk_port_has_no_vlan_line():
    ports = [SwitchPortConfig(port_number=48, mode="trunk", vlan_number=None, description="Uplink")]
    text = generate_ios_config("Cisco 9300-48", ports)
    assert "interface GigabitEthernet1/0/48" in text
    assert " switchport mode trunk" in text
    assert "switchport access vlan" not in text


def test_ios_config_ports_sorted_by_number_regardless_of_input_order():
    ports = [
        SwitchPortConfig(port_number=3, mode="access", vlan_number=10, description=None),
        SwitchPortConfig(port_number=1, mode="access", vlan_number=10, description=None),
        SwitchPortConfig(port_number=2, mode="access", vlan_number=10, description=None),
    ]
    text = generate_ios_config("Cisco 2960-48", ports)
    idx1 = text.index("1/0/1")
    idx2 = text.index("1/0/2")
    idx3 = text.index("1/0/3")
    assert idx1 < idx2 < idx3


def test_ios_config_custom_interface_prefix():
    ports = [SwitchPortConfig(port_number=1, mode="trunk", vlan_number=None, description=None)]
    text = generate_ios_config("Cisco 9300-48", ports, interface_prefix="TenGigabitEthernet1/1/")
    assert "interface TenGigabitEthernet1/1/1" in text


def test_meraki_port_list_shape():
    ports = [SwitchPortConfig(port_number=5, mode="access", vlan_number=20, description="Classroom")]
    result = generate_meraki_port_list(ports)
    assert result == [{"portId": "5", "name": "Classroom", "type": "access", "vlan": 20}]


def test_export_switch_config_routes_ios_models_to_cli():
    ports = [SwitchPortConfig(port_number=1, mode="access", vlan_number=10, description=None)]
    content, content_type = export_switch_config("Cisco 2960-48", ports)
    assert content_type == "text/plain"
    assert "interface GigabitEthernet1/0/1" in content


def test_export_switch_config_routes_meraki_models_to_json():
    ports = [SwitchPortConfig(port_number=1, mode="access", vlan_number=10, description=None)]
    content, content_type = export_switch_config("MS390-24", ports)
    assert content_type == "application/json"
    parsed = json.loads(content)
    assert parsed[0]["portId"] == "1"


def test_export_switch_config_case_insensitive_meraki_detection():
    ports = []
    _, content_type = export_switch_config("ms225-48lp", ports)
    assert content_type == "application/json"


def test_export_switch_config_does_not_false_positive_on_ms_substring():
    """'ms' appearing incidentally in a model name shouldn't route to
    Meraki JSON -- only an actual MS<digits> model number should."""
    ports = [SwitchPortConfig(port_number=1, mode="access", vlan_number=10, description=None)]
    content, content_type = export_switch_config("Systems-2960", ports)
    assert content_type == "text/plain"
