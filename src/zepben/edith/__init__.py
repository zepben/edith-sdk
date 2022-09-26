#  Copyright 2022 Zeppelin Bend Pty Ltd
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
import itertools
import logging
import random
from asyncio import get_event_loop
from zepben.evolve import *
from zepben.protobuf.nc.nc_requests_pb2 import INCLUDE_ENERGIZED_LV_FEEDERS

logger = logging.getLogger("zepben.edith")


def do_nothing_allocator(_1, _2):
    return 0


def distribution_transformer_proportional_allocator_creator(
        proportion: int,
        edith_customers: List[str]
) -> Callable[[LvFeeder, NameType], int]:
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
    num_nmis_used = 0

    def allocator(lv_feeder: LvFeeder, nmi_name_type: NameType) -> int:
        nonlocal num_nmis_used

        usage_points = []
        for eq in lv_feeder.equipment:
            usage_points.extend(eq.usage_points)
        usage_points.sort(key=lambda up: up.mrid)

        usage_points_to_name = random.sample(usage_points, int(len(usage_points) * proportion / 100))
        if num_nmis_used <= len(edith_customers) < num_nmis_used + len(usage_points_to_name):
            logger.warning(
                "Insufficient NMIs to allocate to the requested percentage of usage points without repetition."
            )
        num_nmis_used += len(usage_points_to_name)

        for up in usage_points_to_name:
            # noinspection PyArgumentList
            up.add_name(nmi_name_type.get_or_add_name(next(nmi_generator), up))

        return len(usage_points_to_name)

    return allocator


async def _create_synthetic_feeder(
        self: NetworkConsumerClient,
        feeder_mrid: str,
        allocator: Callable[[LvFeeder, NameType], int] = do_nothing_allocator,
        seed: Optional[int] = None
) -> NetworkService:
    """
    Creates a copy of the given `feeder_mrid` and runs `allocator` across the `LvFeeders` that belong to the `Feeder`.

    :param feeder_mrid: The mRID of the feeder to create a synthetic version.
    :param allocator: The allocator to use to modify the LvFeeders. Default will do nothing to the feeder.
    :return: The synthetic version of the NetworkService
    """

    await self.get_equipment_container(feeder_mrid, Feeder, include_energized_containers=INCLUDE_ENERGIZED_LV_FEEDERS)
    feeder_network = self.service
    try:
        nmi_name_type = feeder_network.get_name_type("NMI")
    except KeyError:
        # noinspection PyArgumentList
        nmi_name_type = NameType(name="NMI")
        feeder_network.add_name_type(nmi_name_type)

    if seed:
        random.seed(seed)

    total_allocated = 0
    for lv_feeder in sorted(feeder_network.objects(LvFeeder), key=lambda lvf: lvf.mrid):
        total_allocated += allocator(lv_feeder, nmi_name_type)

    logger.info(f"NMI names have been added to {total_allocated} usage points.")

    return feeder_network

NetworkConsumerClient.create_synthetic_feeder = _create_synthetic_feeder


def _sync_create_synthetic_feeder(
        self: SyncNetworkConsumerClient,
        feeder_mrid: str,
        allocator: Callable[[LvFeeder, NameType], int] = do_nothing_allocator,
        seed: Optional[int] = None
) -> NetworkService:
    return get_event_loop().run_until_complete(_create_synthetic_feeder(self, feeder_mrid, allocator, seed))


SyncNetworkConsumerClient.create_synthetic_feeder = _sync_create_synthetic_feeder
