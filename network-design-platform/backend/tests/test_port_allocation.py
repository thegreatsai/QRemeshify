import pytest

from app.services.port_allocation import SwitchAllocationInput, calculate_switch_allocation


def test_zero_drops_needs_no_switches():
    result = calculate_switch_allocation(SwitchAllocationInput(data_drops=0))
    assert result.switches_needed == 0
    assert result.per_switch == []


def test_single_switch_fits_exactly():
    # 46 usable ports (48 - 2 uplink), 46 drops -> exactly one switch, fully used
    result = calculate_switch_allocation(SwitchAllocationInput(data_drops=46, ports_per_switch=48))
    assert result.switches_needed == 1
    assert result.usable_data_ports_per_switch == 46
    assert result.per_switch[0].data_ports == 46


def test_one_over_capacity_needs_second_switch():
    result = calculate_switch_allocation(SwitchAllocationInput(data_drops=47, ports_per_switch=48))
    assert result.switches_needed == 2
    # evenly split: 24 + 23
    totals = sorted(p.data_ports for p in result.per_switch)
    assert totals == [23, 24]
    assert sum(totals) == 47


def test_even_distribution_across_switches():
    result = calculate_switch_allocation(
        SwitchAllocationInput(data_drops=90, ports_per_switch=48, uplink_ports_per_switch=2)
    )
    # usable = 46/switch; 90 drops needs ceil(90/46) = 2 switches
    assert result.switches_needed == 2
    totals = sorted(p.data_ports for p in result.per_switch)
    assert totals == [45, 45]


def test_no_switch_exceeds_usable_capacity_across_a_range():
    """The load-bearing correctness property: however many drops, no
    single switch in the plan ever gets more than usable_data_ports."""
    for data_drops in range(0, 300, 7):
        result = calculate_switch_allocation(SwitchAllocationInput(data_drops=data_drops, ports_per_switch=48))
        for plan in result.per_switch:
            assert plan.data_ports <= result.usable_data_ports_per_switch
        assert sum(p.data_ports for p in result.per_switch) == data_drops


def test_ap_reserved_ports_separate_from_data_pool():
    result = calculate_switch_allocation(
        SwitchAllocationInput(
            data_drops=40, ap_drops=10, ports_per_switch=48, ap_reserved_ports_per_switch=18, uplink_ports_per_switch=2
        )
    )
    # usable data = 48 - 18 - 2 = 28; 40 data drops -> ceil(40/28) = 2 switches for data
    # 10 ap drops -> ceil(10/18) = 1 switch for AP
    # switches_needed = max(2, 1) = 2
    assert result.usable_data_ports_per_switch == 28
    assert result.switches_needed == 2
    assert sum(p.data_ports for p in result.per_switch) == 40
    assert sum(p.ap_ports for p in result.per_switch) == 10
    for plan in result.per_switch:
        assert plan.ap_ports <= 18


def test_ap_drops_can_force_more_switches_than_data_alone_would():
    result = calculate_switch_allocation(
        SwitchAllocationInput(
            data_drops=5, ap_drops=40, ports_per_switch=48, ap_reserved_ports_per_switch=18, uplink_ports_per_switch=2
        )
    )
    # data alone needs 1 switch; AP needs ceil(40/18) = 3 switches
    assert result.switches_needed == 3
    assert sum(p.ap_ports for p in result.per_switch) == 40
    assert sum(p.data_ports for p in result.per_switch) == 5


def test_ap_drops_without_reserved_ports_rejected():
    with pytest.raises(ValueError, match="ap_reserved_ports_per_switch"):
        calculate_switch_allocation(SwitchAllocationInput(data_drops=0, ap_drops=5, ap_reserved_ports_per_switch=0))


def test_reserved_ports_exceeding_switch_size_rejected():
    with pytest.raises(ValueError, match="usable data ports"):
        calculate_switch_allocation(
            SwitchAllocationInput(
                data_drops=1, ports_per_switch=48, ap_reserved_ports_per_switch=40, uplink_ports_per_switch=10
            )
        )


def test_negative_drops_rejected():
    with pytest.raises(ValueError, match=">= 0"):
        calculate_switch_allocation(SwitchAllocationInput(data_drops=-1))


def test_zero_ports_per_switch_rejected():
    with pytest.raises(ValueError, match="ports_per_switch"):
        calculate_switch_allocation(SwitchAllocationInput(data_drops=1, ports_per_switch=0))


def test_large_realistic_school_scenario():
    # A mid-size school: ~180 data drops, 24 AP drops, standard 48-port
    # switches with 2 uplink ports and 4 reserved for APs per switch.
    result = calculate_switch_allocation(
        SwitchAllocationInput(
            data_drops=180, ap_drops=24, ports_per_switch=48, ap_reserved_ports_per_switch=4, uplink_ports_per_switch=2
        )
    )
    assert result.total_ports_needed == 204
    assert sum(p.data_ports for p in result.per_switch) == 180
    assert sum(p.ap_ports for p in result.per_switch) == 24
    for plan in result.per_switch:
        assert plan.total_ports <= result.usable_data_ports_per_switch + 4
