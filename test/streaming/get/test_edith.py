#  Copyright 2022 Zeppelin Bend Pty Ltd
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Optional, Iterable, Generator, Callable, Dict, Set, Tuple

import pytest

import grpc_testing
from zepben.evolve import NetworkService, IdentifiedObject, CableInfo, AcLineSegment, Breaker, EnergySource, \
    EnergySourcePhase, Junction, PowerTransformer, PowerTransformerEnd, ConnectivityNode, Feeder, Location, \
    OverheadWireInfo, PerLengthSequenceImpedance, \
    Substation, Terminal, EquipmentContainer, TransformerStarImpedance, GeographicalRegion, \
    SubGeographicalRegion, Circuit, Loop, LvFeeder, UsagePoint, BaseVoltage, TestNetworkBuilder, PhaseCode, CustomerService, CustomerConsumerClient
from zepben.protobuf.cc import cc_pb2
from zepben.protobuf.nc import nc_pb2
from zepben.protobuf.nc.nc_data_pb2 import NetworkIdentifiedObject
from zepben.protobuf.nc.nc_requests_pb2 import GetIdentifiedObjectsRequest, GetEquipmentForContainersRequest
from zepben.protobuf.nc.nc_responses_pb2 import GetIdentifiedObjectsResponse, GetEquipmentForContainersResponse, \
    GetNetworkHierarchyResponse
from zepben.protobuf.cc.cc_data_pb2 import CustomerIdentifiedObject
from zepben.protobuf.cc.cc_requests_pb2 import GetCustomersForContainerRequest
from zepben.protobuf.cc.cc_responses_pb2 import GetCustomersForContainerResponse
from zepben.edith import NetworkConsumerClient, usage_point_proportional_allocator, line_weakener, transformer_weakener
from streaming.get.grpcio_aio_testing.mock_async_channel import async_testing_channel
from streaming.get.mock_server import MockServer, StreamGrpc, UnaryGrpc, unary_from_fixed


class TestNetworkConsumer:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.channel = async_testing_channel(cc_pb2.DESCRIPTOR.services_by_name.values(),
                                             grpc_testing.strict_real_time())
        self.mock_server = MockServer(self.channel, [nc_pb2.DESCRIPTOR.services_by_name['NetworkConsumer'], cc_pb2.DESCRIPTOR.services_by_name['CustomerConsumer']])
        self.client = NetworkConsumerClient(channel=self.channel)
        self.customer_client = CustomerConsumerClient(channel=self.channel)
        self.customer_service = self.customer_client.service
        self.service = self.client.service

    @pytest.mark.asyncio
    @pytest.mark.parametrize("feeder_network", [5], indirect=True)
    async def test_nmi_allocator_does_not_reuse_nmis_by_default(self, feeder_network: NetworkService):
        feeder_mrid = "f001"

        def verify_usage_points(modified_usage_points: Set[str]):
            assert len(modified_usage_points) == 3

            added_names = list(self.service.get_name_type("NMI").names)
            assert set(n.name for n in added_names) == {"A", "B", "C"}
            assert len(set(n.identified_object for n in added_names)) == 3

        async def client_test():
            await self.client.create_synthetic_feeder(
                feeder_mrid,
                [usage_point_proportional_allocator(80, ["A", "B", "C"], callback=verify_usage_points)]
            )

        object_responses = _create_object_responses(feeder_network)

        await self.mock_server.validate(
            client_test,
            [
                UnaryGrpc('getNetworkHierarchy', unary_from_fixed(None, _create_hierarchy_response(feeder_network))),
                StreamGrpc('getEquipmentForContainers', [_create_container_responses(feeder_network)]),
                StreamGrpc('getIdentifiedObjects', [object_responses, object_responses])
            ])

    @pytest.mark.asyncio
    @pytest.mark.parametrize("feeder_network", [5], indirect=True)
    async def test_nmi_allocator_can_reuse_nmis(self, feeder_network: NetworkService):
        feeder_mrid = "f001"

        def verify_usage_points(modified_usage_points: Set[str]):
            assert len(modified_usage_points) == 4

            added_names = list(self.service.get_name_type("NMI").names)
            assert set(n.name for n in added_names) == {"A", "B", "C"}
            assert len(set(n.identified_object for n in added_names)) == 4

        async def client_test():
            await self.client.create_synthetic_feeder(
                feeder_mrid,
                [
                    usage_point_proportional_allocator(80, ["A", "B", "C"], allow_duplicate_customers=True,
                                                       callback=verify_usage_points)
                ]
            )

        object_responses = _create_object_responses(feeder_network)

        await self.mock_server.validate(
            client_test,
            [
                UnaryGrpc('getNetworkHierarchy', unary_from_fixed(None, _create_hierarchy_response(feeder_network))),
                StreamGrpc('getEquipmentForContainers', [_create_container_responses(feeder_network)]),
                StreamGrpc('getIdentifiedObjects', [object_responses, object_responses])
            ])

    @pytest.mark.asyncio
    @pytest.mark.parametrize("network_with_nmis", [5], indirect=True)
    async def test_nmi_allocator_replaces_existing_nmis(self, network_with_nmis: Tuple[NetworkService, CustomerService]):
        feeder_mrid = "fdr2"
        network_service, customer_service = network_with_nmis

        def verify_usage_points(modified_usage_points: Set[str]):
            assert len(modified_usage_points) == 3

            nmi_names = list(self.service.get_name_type("NMI").names)
            assert len(nmi_names) == 5
            assert {"A", "B", "C"} <= set(n.name for n in nmi_names)
            assert len(set(n.identified_object for n in nmi_names)) == 5

        async def client_test():
            await self.client.create_synthetic_feeder(
                feeder_mrid,
                [usage_point_proportional_allocator(60, ["A", "B", "C"], callback=verify_usage_points)],
                self.customer_client
            )

        object_responses = _create_object_responses(network_service)
        customer_object_responses = _create_customer_responses(network_service, customer_service)

        await self.mock_server.validate(
            client_test,
            [
                UnaryGrpc('getNetworkHierarchy', unary_from_fixed(None, _create_hierarchy_response(network_service))),
                StreamGrpc('getEquipmentForContainers', [_create_container_responses(network_service)]),
                StreamGrpc('getIdentifiedObjects', [object_responses, object_responses]),
                StreamGrpc('getCustomersForContainer', [customer_object_responses, customer_object_responses])
            ]
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("network_with_nmis", [5], indirect=True)
    async def test_nmi_allocator_skips_non_residential_custumers(self, network_with_nmis: NetworkService, customer_service: CustomerService):
        feeder_mrid = "fdr2"

        def verify_usage_points(modified_usage_points: Set[str]):
            assert len(modified_usage_points) == 3

            nmi_names = list(self.service.get_name_type("NMI").names)
            assert len(nmi_names) == 5
            assert {"A", "B", "C"} <= set(n.name for n in nmi_names)
            assert len(set(n.identified_object for n in nmi_names)) == 5

        async def client_test():
            await self.client.create_synthetic_feeder(
                feeder_mrid,
                [usage_point_proportional_allocator(60, ["A", "B", "C"], callback=verify_usage_points)]
            )

        object_responses = _create_object_responses(network_with_nmis)

        await self.mock_server.validate(
            client_test,
            [
                UnaryGrpc('getNetworkHierarchy', unary_from_fixed(None, _create_hierarchy_response(network_with_nmis))),
                StreamGrpc('getEquipmentForContainers', [_create_container_responses(network_with_nmis)]),
                StreamGrpc('getIdentifiedObjects', [object_responses, object_responses])
            ]
        )

    @pytest.mark.asyncio
    async def test_line_weakener(self):
        cable_info = CableInfo(mrid="cable-500A", rated_current=500)
        base_voltage = BaseVoltage(mrid="hv-bv", nominal_voltage=11000)
        network_with_line = await (
            TestNetworkBuilder()
            .from_acls(
                nominal_phases=PhaseCode.BCN,
                action=lambda acls: setattr(acls, "wire_info", cable_info) or
                                    setattr(acls, "base_voltage", base_voltage)
            )
            .add_feeder("c0")
            .build()
        )
        network_with_line.add(cable_info)
        network_with_line.add(base_voltage)

        feeder_mrid = "fdr1"

        def verify_lines(modified_lines: Set[str]):
            assert modified_lines == {"c0"}
            acls = self.service.get("c0", AcLineSegment)
            assert acls.wire_info.mrid == "Neptune_19/3.25_AAC/1350_2W-ug"
            assert acls.wire_info.rated_current == 333
            assert acls.per_length_sequence_impedance.mrid == "Neptune_19/3.25_AAC/1350_2W-plsi"
            assert acls.per_length_sequence_impedance.r == 0.0001825
            assert acls.per_length_sequence_impedance.x == 0.0003616
            assert acls.per_length_sequence_impedance.r0 == 0.0002825
            assert acls.per_length_sequence_impedance.x0 == 0.0011364

        async def client_test():
            await self.client.create_synthetic_feeder(
                feeder_mrid,
                [line_weakener(30, callback=verify_lines)]
            )

        object_responses = _create_object_responses(network_with_line)

        await self.mock_server.validate(
            client_test,
            [
                UnaryGrpc('getNetworkHierarchy', unary_from_fixed(None, _create_hierarchy_response(network_with_line))),
                StreamGrpc('getEquipmentForContainers', [_create_container_responses(network_with_line)]),
                StreamGrpc('getIdentifiedObjects', [object_responses])
            ]
        )

    @pytest.mark.asyncio
    async def test_transformer_weakener(self):
        network_with_tx = await (
            TestNetworkBuilder()
            .from_power_transformer(
                nominal_phases=[PhaseCode.ABCN, PhaseCode.ABC],
                end_actions=[
                    lambda end: setattr(end, "rated_u", 11000) or setattr(end, "rated_s", 300000),
                    lambda end: setattr(end, "rated_u", 433) or setattr(end, "rated_s", 300000)
                ]
            )
            .add_feeder("tx0")
            .build()
        )

        feeder_mrid = "fdr1"

        def verify_transformers(modified_txs: Set[str]):
            assert modified_txs == {"tx0"}
            primary_end, secondary_end = self.service.get("tx0", PowerTransformer).ends
            assert primary_end.rated_s == secondary_end.rated_s == 200000

        async def client_test():
            await self.client.create_synthetic_feeder(
                feeder_mrid,
                [transformer_weakener(30, callback=verify_transformers)]
            )

        object_responses = _create_object_responses(network_with_tx)

        await self.mock_server.validate(
            client_test,
            [
                UnaryGrpc('getNetworkHierarchy', unary_from_fixed(None, _create_hierarchy_response(network_with_tx))),
                StreamGrpc('getEquipmentForContainers', [_create_container_responses(network_with_tx)]),
                StreamGrpc('getIdentifiedObjects', [object_responses])
            ]
        )


# noinspection PyUnresolvedReferences
def _to_network_identified_object(obj) -> NetworkIdentifiedObject:
    if isinstance(obj, AcLineSegment):
        nio = NetworkIdentifiedObject(acLineSegment=obj.to_pb())
    elif isinstance(obj, Breaker):
        nio = NetworkIdentifiedObject(breaker=obj.to_pb())
    elif isinstance(obj, EnergySource):
        nio = NetworkIdentifiedObject(energySource=obj.to_pb())
    elif isinstance(obj, EnergySourcePhase):
        nio = NetworkIdentifiedObject(energySourcePhase=obj.to_pb())
    elif isinstance(obj, Junction):
        nio = NetworkIdentifiedObject(junction=obj.to_pb())
    elif isinstance(obj, PowerTransformer):
        nio = NetworkIdentifiedObject(powerTransformer=obj.to_pb())
    elif isinstance(obj, Terminal):
        nio = NetworkIdentifiedObject(terminal=obj.to_pb())
    elif isinstance(obj, ConnectivityNode):
        nio = NetworkIdentifiedObject(connectivityNode=obj.to_pb())
    elif isinstance(obj, CableInfo):
        nio = NetworkIdentifiedObject(cableInfo=obj.to_pb())
    elif isinstance(obj, TransformerStarImpedance):
        nio = NetworkIdentifiedObject(transformerStarImpedance=obj.to_pb())
    elif isinstance(obj, EnergySourcePhase):
        nio = NetworkIdentifiedObject(energySourcePhase=obj.to_pb())
    elif isinstance(obj, Feeder):
        nio = NetworkIdentifiedObject(feeder=obj.to_pb())
    elif isinstance(obj, Location):
        nio = NetworkIdentifiedObject(location=obj.to_pb())
    elif isinstance(obj, OverheadWireInfo):
        nio = NetworkIdentifiedObject(overheadWireInfo=obj.to_pb())
    elif isinstance(obj, PerLengthSequenceImpedance):
        nio = NetworkIdentifiedObject(perLengthSequenceImpedance=obj.to_pb())
    elif isinstance(obj, PowerTransformerEnd):
        nio = NetworkIdentifiedObject(powerTransformerEnd=obj.to_pb())
    elif isinstance(obj, Substation):
        nio = NetworkIdentifiedObject(substation=obj.to_pb())
    elif isinstance(obj, Loop):
        nio = NetworkIdentifiedObject(loop=obj.to_pb())
    elif isinstance(obj, Circuit):
        nio = NetworkIdentifiedObject(circuit=obj.to_pb())
    elif isinstance(obj, LvFeeder):
        nio = NetworkIdentifiedObject(lvFeeder=obj.to_pb())
    elif isinstance(obj, UsagePoint):
        nio = NetworkIdentifiedObject(usagePoint=obj.to_pb())
    elif isinstance(obj, BaseVoltage):
        nio = NetworkIdentifiedObject(baseVoltage=obj.to_pb())
    else:
        raise Exception(f"Missing class in create response - you should implement it: {str(obj)}")
    return nio


# noinspection PyUnresolvedReferences
def _to_customer_identified_object(obj) -> CustomerIdentifiedObject:
    if isinstance(obj, Customer):
        cio = CustomerIdentifiedObject(customer=obj.to_pb())
    elif isinstance(obj, CustomerAgreement):
        cio = CustomerIdentifiedObject(customerAgreement=obj.to_pb())
    elif isinstance(obj, Organisation):
        cio = CustomerIdentifiedObject(organisation=obj.to_pb())
    elif isinstance(obj, PricingStructure):
        cio = CustomerIdentifiedObject(pricingStructure=obj.to_pb())
    elif isinstance(obj, Tariff):
        cio = CustomerIdentifiedObject(tariff=obj.to_pb())
    else:
        raise Exception(f"Missing class in create response - you should implement it: {str(obj)}")
    return cio


def _response_of(io: IdentifiedObject, response_type):
    return response_type(identifiedObjects=[_to_network_identified_object(io)])


def _customer_response_of(io: IdentifiedObject, response_type):
    return response_type(identifiedObjects=[_to_customer_identified_object(io)])


def _create_object_responses(ns: NetworkService, mrids: Optional[Iterable[str]] = None) \
        -> Callable[[GetIdentifiedObjectsRequest], Generator[GetIdentifiedObjectsResponse, None, None]]:
    valid: Dict[str, IdentifiedObject] = {mrid: ns[mrid] for mrid in mrids} if mrids else ns

    def responses(request: GetIdentifiedObjectsRequest) -> Generator[GetIdentifiedObjectsResponse, None, None]:
        for mrid in request.mrids:
            obj = valid[mrid]
            if obj:
                yield _response_of(obj, GetIdentifiedObjectsResponse)
            else:
                raise AssertionError(f"Requested unexpected object {mrid}.")

    return responses


def _create_customer_responses(ns: NetworkService, cs: CustomerService) -> \
        Callable[[GetCustomersForContainerRequest], Generator[GetCustomersForContainerResponse, None, None]]:

    def responses(request: GetCustomersForContainerRequest) -> Generator[GetCustomersForContainerResponse, None, None]:
        for mrid in request.mrids:
            container = ns[mrid]
            if container:
                for eq in container.equipment:
                    for up in eq.usage_points:
                        for ed in up.end_devices:
                            if ed.customer_mrid:
                                customer = cs.get(ed.customer_mrid)
                                yield _customer_response_of(customer, GetCustomersForContainerResponse)
            else:
                raise AssertionError(f"Requested unexpected object {mrid}.")

    return responses


# noinspection PyUnresolvedReferences
def _create_hierarchy_response(service: NetworkService) -> GetNetworkHierarchyResponse:
    return GetNetworkHierarchyResponse(
        geographicalRegions=list(map(lambda it: it.to_pb(), service.objects(GeographicalRegion))),
        subGeographicalRegions=list(map(lambda it: it.to_pb(), service.objects(SubGeographicalRegion))),
        substations=list(map(lambda it: it.to_pb(), service.objects(Substation))),
        feeders=list(map(lambda it: it.to_pb(), service.objects(Feeder))),
        circuits=list(map(lambda it: it.to_pb(), service.objects(Circuit))),
        loops=list(map(lambda it: it.to_pb(), service.objects(Loop)))
    )


def _create_container_responses(ns: NetworkService, mrids: Optional[Iterable[str]] = None) \
        -> Callable[[GetEquipmentForContainersRequest], Generator[GetEquipmentForContainersResponse, None, None]]:
    valid: Dict[str, EquipmentContainer] = {mrid: ns[mrid] for mrid in mrids} if mrids else ns

    def responses(request: GetEquipmentForContainersRequest) -> Generator[GetEquipmentForContainersResponse, None, None]:
        for mrid in request.mrids:
            container = valid[mrid]
            if container:
                for equipment in container.equipment:
                    yield _response_of(equipment, GetEquipmentForContainersResponse)
            else:
                raise AssertionError(f"Requested unexpected container {mrid}.")

    return responses
