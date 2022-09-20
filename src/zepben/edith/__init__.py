#  Copyright 2022 Zeppelin Bend Pty Ltd
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
import itertools
import random
from asyncio import get_event_loop
from zepben.evolve import *
from zepben.protobuf.nc.nc_requests_pb2 import INCLUDE_ENERGIZED_LV_FEEDERS


def do_nothing_allocator(_1, _2):
    pass


def distribution_transformer_proportional_allocator_creator(
        proportion: int,
        edith_customers: List[str]
) -> Callable[[LvFeeder], None]:
    """
    Creates an allocator for the synthetic feeder creator that distributes a `proportion` of NMIs from `edith_customers`
    to an `LvFeeder`

    :param proportion: The percentage of Edith customers to distribute to an `LvFeeder`. Must be between 1 and 100
    :param edith_customers: The Edith NMIs to distribute to the `LvFeeder`
    :return: A function that takes an `LvFeeder` and distributes the `proportion` of NMIs across the UsagePoints on the
    `LvFeeder`.
    """
    if not 1 <= proportion <= 100:
        raise ValueError("Proportion must be between 1 and 100")

    nmi_generator = itertools.cycle(edith_customers)

    def allocator(lv_feeder: LvFeeder, nmi_name_type: NameType):
        usage_points = set()
        for eq in lv_feeder.equipment:
            usage_points.update(eq.usage_points)

        for up in random.sample(usage_points, int(len(usage_points) * 1/proportion)):
            # noinspection PyArgumentList
            up.add_name(Name(name=next(nmi_generator), type=nmi_name_type))

    return allocator


async def _create_synthetic_feeder(
        self: SyncNetworkConsumerClient,
        feeder_mrid: str,
        allocator: Callable[[LvFeeder, NameType], None] = do_nothing_allocator,
        seed: Optional[int] = None
) -> NetworkService:
    """
    Creates a copy of the given `feeder_mrid` and runs `allocator` across the `LvFeeders` that belong to the `Feeder`.

    :param feeder_mrid: The mRID of the feeder to create a synthetic version.
    :param allocator: The allocator to use to modify the LvFeeders. Default will do nothing to the feeder.
    :return: The synthetic version of the NetworkService
    """

    self.get_equipment_container(feeder_mrid, Feeder, include_energized_containers=INCLUDE_ENERGIZED_LV_FEEDERS)
    feeder_network = self.service
    try:
        nmi_name_type = feeder_network.get_name_type("NMI")
    except KeyError:
        # noinspection PyArgumentList
        nmi_name_type = NameType(name="NMI")
        feeder_network.add_name_type(nmi_name_type)

    if seed:
        random.seed(seed)
    for lv_feeder in feeder_network.objects(LvFeeder):
        allocator(lv_feeder, nmi_name_type)

    return feeder_network

NetworkConsumerClient.create_synthetic_feeder = _create_synthetic_feeder


def _sync_create_synthetic_feeder(
        self: SyncNetworkConsumerClient,
        feeder_mrid: str,
        allocator: Callable[[LvFeeder, NameType], None] = do_nothing_allocator,
        seed: Optional[int] = None
) -> NetworkService:
    return get_event_loop().run_until_complete(_create_synthetic_feeder(self, feeder_mrid, allocator, seed))


SyncNetworkConsumerClient.create_synthetic_feeder = _sync_create_synthetic_feeder
