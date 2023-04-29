#  Copyright 2021 Zeppelin Bend Pty Ltd
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
from typing import Dict, List, Optional

from pytest import fixture
from zepben.evolve import AssignToLvFeeders, LvFeeder, BaseVoltage, NameType, TestNetworkBuilder, Customer, CustomerKind

from zepben.edith import NetworkService, Feeder, PhaseCode, EnergySource, EnergySourcePhase, Junction, ConductingEquipment, Breaker, PowerTransformer, \
    UsagePoint, Terminal, PowerTransformerEnd, Meter, AssetOwner, CustomerService, Organisation, AcLineSegment, \
    PerLengthSequenceImpedance, WireInfo, EnergyConsumer, GeographicalRegion, SubGeographicalRegion, Substation, PowerSystemResource, Location, PositionPoint, \
    SetPhases, OverheadWireInfo, OperationalRestriction, Equipment, ConnectivityNode
from zepben.evolve.services.network.tracing.feeder.assign_to_feeders import AssignToFeeders
from zepben.evolve.util import CopyableUUID

__all__ = ["create_terminals", "create_junction_for_connecting", "create_source_for_connecting", "create_switch_for_connecting", "create_acls_for_connecting",
           "create_energy_consumer_for_connecting", "create_feeder", "create_substation", "create_power_transformer_for_connecting", "create_terminals",
           "create_geographical_region", "create_subgeographical_region", "create_asset_owner", "create_meter", "create_power_transformer_end",
           "feeder_network", "network_with_nmis", "create_connectivitynode_with_terminals", "create_terminal"]


def create_terminals(network: NetworkService, ce: ConductingEquipment, num_terms: int, phases: PhaseCode = PhaseCode.ABCN) -> List[Terminal]:
    terms = []
    for i in range(1, num_terms + 1):
        term = Terminal(mrid=f"{ce.mrid}_t{i}", conducting_equipment=ce, phases=phases, sequence_number=i)
        ce.add_terminal(term)
        assert network.add(term)
        terms.append(term)

    return terms


def create_terminal(network: NetworkService, ce: Optional[ConductingEquipment], phases: PhaseCode = PhaseCode.ABCN, sequence_number: int = 1) -> Terminal:
    terminal = None
    try:
        terminal = ce.get_terminal_by_sn(sequence_number) if ce is not None else None
    except IndexError:
        pass

    if terminal is None:
        if ce:
            terminal = Terminal(mrid=f"{ce.mrid}_t{len(list(ce.terminals)) + 1}", conducting_equipment=ce, phases=phases, sequence_number=sequence_number)
            ce.add_terminal(terminal)
        else:
            terminal = Terminal(phases=phases, sequence_number=sequence_number)
        network.add(terminal)
    return terminal


def create_connectivitynode_with_terminals(ns: NetworkService, mrid: str, *terminal_phases: PhaseCode):
    cn = ConnectivityNode(mrid=mrid)
    ns.add(cn)
    # noinspection PyTypeChecker
    for i, phase in enumerate(terminal_phases, start=1):
        t = create_terminal(ns, None, phase, i)
        ns.connect_by_mrid(t, mrid)


def create_junction_for_connecting(network: NetworkService, mrid: str = "", num_terms: int = 0, phases: PhaseCode = PhaseCode.ABCN) -> Junction:
    if not mrid:
        mrid = str(CopyableUUID())

    junction = Junction(mrid=mrid, name="test junction")
    create_terminals(network, junction, num_terms, phases)
    network.add(junction)
    return junction


def create_source_for_connecting(network: NetworkService, mrid: str = "", num_terms: int = 0, phases: PhaseCode = PhaseCode.ABCN) -> EnergySource:
    if not mrid:
        mrid = str(CopyableUUID())

    source = EnergySource(mrid=mrid)
    for phase in phases.single_phases:
        esp = EnergySourcePhase(energy_source=source, phase=phase)

        source.add_phase(esp)
        network.add(esp)

    create_terminals(network, source, num_terms, phases)
    network.add(source)
    return source


def create_switch_for_connecting(network: NetworkService, mrid: str = "", num_terms: int = 0, phases: PhaseCode = PhaseCode.ABC,
                                 normal_phase_states: List[bool] = None, current_phase_states: List[bool] = None) -> Breaker:
    if not mrid:
        mrid = str(CopyableUUID())

    cb = Breaker(mrid=mrid, name="test breaker")
    create_terminals(network, cb, num_terms, phases)

    cb.set_open(False)
    cb.set_normally_open(False)
    if normal_phase_states:
        for i, state in enumerate(normal_phase_states):
            cb.set_normally_open(state, phases.single_phases[i])
    if current_phase_states:
        for i, state in enumerate(current_phase_states):
            cb.set_open(state, phases.single_phases[i])

    network.add(cb)
    return cb


def create_power_transformer_end(network: NetworkService, pt: PowerTransformer, t: Terminal, end_number: int = 0, **kwargs) -> PowerTransformerEnd:
    en = end_number if end_number > 0 else t.sequence_number
    te = PowerTransformerEnd(mrid=f"{pt.mrid}_e{en}", power_transformer=pt, terminal=t, end_number=en,
                             **kwargs)
    pt.add_end(te)
    network.add(te)
    return te


def create_asset_owner(network: NetworkService, company: str, customer_service: Optional[CustomerService] = None) -> AssetOwner:
    # noinspection PyArgumentList
    ao = AssetOwner(mrid=f"{company}-owner-role")
    # noinspection PyArgumentList
    org = Organisation(mrid=company, name=company)
    ao.organisation = org
    network.add(org)
    network.add(ao)

    if customer_service is not None:
        customer_service.add(org)

    return ao


def create_meter(network: NetworkService, mrid: str = "") -> Meter:
    if not mrid:
        mrid = str(CopyableUUID())

    meter = Meter(mrid=mrid, name=f"companyMeterId{mrid}")
    meter.add_organisation_role(create_asset_owner(network, f"company{mrid}"))
    network.add(meter)
    return meter


def create_power_transformer_for_connecting(network: NetworkService, mrid: str = "", num_terms: int = 0, phases: PhaseCode = PhaseCode.ABCN,
                                            num_usagepoints: int = 0, num_meters: int = 0, end_args: List[Dict] = None) -> PowerTransformer:
    """
    `end_args` A list of dictionaries, each of which is passed to `create_power_transformer_end` for every terminal created. Possible kwargs are anything that
               can be passed to the `PowerTransformerEnd` constructor. Keep in mind CIM recommends the HV end is first in the list.
    """
    if not mrid:
        mrid = str(CopyableUUID())

    pt = PowerTransformer(mrid=mrid, name="test powertransformer")
    terminals = create_terminals(network, pt, num_terms, phases)

    for eargs, t in zip(end_args, terminals):
        create_power_transformer_end(network, pt, t, **eargs)

    for i in range(num_usagepoints):
        up = UsagePoint(mrid=f"{mrid}-up{i}")
        pt.add_usage_point(up)
        up.add_equipment(pt)
        for j in range(num_meters):
            meter = create_meter(network, f"{mrid}-up{i}-m{j}")
            up.add_end_device(meter)
            meter.add_usage_point(up)
        network.add(up)

    network.add(pt)
    return pt


def create_acls_for_connecting(network: NetworkService, mrid: str = "", phases: PhaseCode = PhaseCode.ABCN, length: float = 0.0,
                               plsi_mrid: str = "perLengthSequenceImepedance",
                               wi_mrid: str = "wireInfo") -> AcLineSegment:
    if not mrid:
        mrid = str(CopyableUUID())

    try:
        plsi = network.get(plsi_mrid, PerLengthSequenceImpedance)
    except KeyError:
        # noinspection PyArgumentList
        plsi = PerLengthSequenceImpedance(mrid=plsi_mrid)
        network.add(plsi)

    try:
        wi = network.get(wi_mrid, WireInfo)
    except KeyError:
        # noinspection PyArgumentList
        wi = OverheadWireInfo(mrid=wi_mrid)
        network.add(wi)

    acls = AcLineSegment(mrid=mrid, name=f"{mrid} name", per_length_sequence_impedance=plsi, asset_info=wi, length=length)
    create_terminals(network, acls, 2, phases)
    network.add(acls)
    return acls


def create_energy_consumer_for_connecting(network: NetworkService, mrid: str = "", num_terms: int = 0, phases: PhaseCode = PhaseCode.ABCN) -> EnergyConsumer:
    if not mrid:
        mrid = str(CopyableUUID())

    ec = EnergyConsumer(mrid=mrid, name=f"{mrid}-name")
    create_terminals(network, ec, num_terms, phases)
    network.add(ec)
    return ec


def create_geographical_region(network: NetworkService, mrid: str = "", name: str = "") -> GeographicalRegion:
    if not mrid:
        mrid = str(CopyableUUID())

    gr = GeographicalRegion(mrid=mrid, name=name)
    network.add(gr)
    return gr


def create_subgeographical_region(network: NetworkService, mrid: str = "", name: str = "", gr: GeographicalRegion = None) -> SubGeographicalRegion:
    if not mrid:
        mrid = str(CopyableUUID())

    sgr = SubGeographicalRegion(mrid=mrid, name=name)
    if gr is not None:
        sgr.geographical_region = gr
        gr.add_sub_geographical_region(sgr)

    network.add(sgr)
    return sgr


def create_substation(network: NetworkService, mrid: str = "", name: str = "", sgr: SubGeographicalRegion = None) -> Substation:
    if not mrid:
        mrid = str(CopyableUUID())

    sub = Substation(mrid=mrid, name=name, sub_geographical_region=sgr)
    if sgr is not None:
        sgr.add_substation(sub)

    network.add(sub)
    return sub


def create_feeder(network: NetworkService, mrid: str = "", name: str = "", sub: Substation = None, head_terminal: Terminal = None,
                  *equipment_mrids: str) -> Feeder:
    """
    `equipment_mrids` Equipment to fetch from the network and add to this feeder.
    """
    if not mrid:
        mrid = str(CopyableUUID())
    feeder = Feeder(mrid=mrid, name=name, normal_head_terminal=head_terminal, normal_energizing_substation=sub)
    if sub:
        sub.add_feeder(feeder)
    network.add(feeder)

    for mrid in equipment_mrids:
        ce = network.get(mrid, ConductingEquipment)
        ce.add_container(feeder)
        feeder.add_equipment(ce)

    return feeder


def create_operational_restriction(network: NetworkService, mrid: str = "", name: str = "", *equipment_mrids: str, **document_kwargs):
    if not mrid:
        mrid = str(CopyableUUID())
    restriction = OperationalRestriction(mrid=mrid, name=name, **document_kwargs)
    network.add(restriction)

    for mrid in equipment_mrids:
        eq = network.get(mrid, Equipment)
        restriction.add_equipment(eq)
        eq.add_operational_restriction(restriction)

    return restriction


def add_location(network: NetworkService, psr: PowerSystemResource, *coords: float):
    """
    `coords` XY/longlats to use for the PositionPoint for this location. Must be an even number of coords.
    :return:
    """
    loc = Location()
    # noinspection PyTypeChecker
    for i in range(0, len(coords), 2):
        # noinspection PyArgumentList, PyUnresolvedReferences
        loc.add_point(PositionPoint(coords[i], coords[i + 1]))
    psr.location = loc
    network.add(loc)


@fixture()
async def feeder_network(request):
    """
                c1       c2
    source-fcb------fsp------tx
    """
    num_usagepoints = request.param

    network_service = NetworkService()

    hv = BaseVoltage(mrid="hv")
    hv.nominal_voltage = 22000
    network_service.add(hv)

    source = create_source_for_connecting(network_service, "source", 1, PhaseCode.AB)
    fcb = create_switch_for_connecting(network_service, "fcb", 2, PhaseCode.AB)
    fsp = create_junction_for_connecting(network_service, "fsp", 2, PhaseCode.AB)
    tx = create_power_transformer_for_connecting(network_service, "tx", 2, PhaseCode.AB,
                                                 num_usagepoints=num_usagepoints,
                                                 end_args=[{"rated_u": 22000}, {"rated_u": 415}])

    c1 = create_acls_for_connecting(network_service, "c1", PhaseCode.AB)
    c2 = create_acls_for_connecting(network_service, "c2", PhaseCode.AB)

    fcb.base_voltage = fsp.base_voltage = c1.base_voltage = c2.base_voltage = hv

    sub = create_substation(network_service, "f", "f")
    fdr = create_feeder(network_service, "f001", "f001", sub, fsp.get_terminal_by_sn(2))
    lvf = LvFeeder(mrid="lvf001", normal_head_terminal=tx.get_terminal_by_sn(2), normal_energizing_feeders=[fdr])
    fdr.add_normal_energized_lv_feeder(lvf)
    network_service.add(lvf)

    add_location(network_service, source, 1.0, 1.0)
    add_location(network_service, fcb, 1.0, 1.0)
    add_location(network_service, fsp, 5.0, 1.0)
    add_location(network_service, tx, 10.0, 2.0)
    add_location(network_service, c1, 1.0, 1.0, 5.0, 1.0)
    add_location(network_service, c2, 5.0, 1.0, 10.0, 2.0)

    network_service.connect_terminals(source.get_terminal_by_sn(1), fcb.get_terminal_by_sn(1))
    network_service.connect_terminals(fcb.get_terminal_by_sn(2), c1.get_terminal_by_sn(1))
    network_service.connect_terminals(c1.get_terminal_by_sn(2), fsp.get_terminal_by_sn(1))
    network_service.connect_terminals(fsp.get_terminal_by_sn(2), c2.get_terminal_by_sn(1))
    network_service.connect_terminals(c2.get_terminal_by_sn(2), tx.get_terminal_by_sn(1))

    await SetPhases().run(network_service)
    await AssignToFeeders().run(network_service)
    await AssignToLvFeeders().run(network_service)
    return network_service


@fixture()
async def network_with_nmis(request):
    num_usagepoints = request.param

    hv = BaseVoltage(mrid="hv")
    hv.nominal_voltage = 22000
    lv = BaseVoltage(mrid="lv")
    lv.nominal_voltage = 415

    network_service = await (
        TestNetworkBuilder()
        .from_breaker(action=lambda ce: setattr(ce, "base_voltage", hv))
        .to_power_transformer(end_actions=[
            lambda pte: setattr(pte, "base_voltage", hv),
            lambda pte: setattr(pte, "base_voltage", lv)
        ])
        .add_feeder("b0")
        .add_lv_feeder("tx1")
        .build()
    )

    network_service.add(hv)
    network_service.add(lv)
    fdr = network_service.get("fdr2", Feeder)
    lvf = network_service.get("lvf3", LvFeeder)
    fdr.add_normal_energized_lv_feeder(lvf)
    lvf.add_normal_energizing_feeder(fdr)

    # noinspection PyArgumentList
    nmi_name_type = NameType(name="NMI")
    network_service.add_name_type(nmi_name_type)

    customer_service = CustomerService()

    tx = network_service.get("tx1", PowerTransformer)
    for i in range(num_usagepoints):
        usage_point = UsagePoint(mrid=f"up{i}")
        usage_point.add_name(nmi_name_type.get_or_add_name(f"NMI{i}", usage_point))

        customer = Customer(mrid=f"customer{i}")
        customer.kind = CustomerKind.residential
        customer_service.add(customer)

        meter = Meter(mrid=f"meter{i}")
        usage_point.add_end_device(meter)
        meter.add_usage_point(usage_point)
        meter.customer_mrid = customer.mrid
        network_service.add(meter)

        tx.add_usage_point(usage_point)
        usage_point.add_equipment(tx)
        network_service.add(usage_point)

    return network_service, customer_service
