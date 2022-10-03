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
    return 0


def usage_point_proportional_allocator(
        proportion: int,
        edith_customers: List[str],
        allow_duplicate_customers: bool = False,
) -> Callable[[LvFeeder, NameType], int]:
    """
    Creates an allocator for the synthetic feeder creator that distributes a `proportion` of NMIs from `edith_customers`
    to an `LvFeeder`

    :param proportion: The percentage of Edith customers to distribute to an `LvFeeder`. Must be between 1 and 100
    :param edith_customers: The Edith NMIs to distribute to the `LvFeeder`
    :param allow_duplicate_customers: Reuse customers from the list to reach the proportion if necessary.
    :return: A function that takes an `LvFeeder` and distributes the `proportion` of NMIs across the UsagePoints on the
    `LvFeeder`.
    """
    if not 1 <= proportion <= 100:
        raise ValueError("Proportion must be between 1 and 100")

    if allow_duplicate_customers:
        nmi_generator = itertools.cycle(edith_customers)
    else:
        nmi_generator = iter(edith_customers)

    def allocator(lv_feeder: LvFeeder, nmi_name_type: NameType) -> int:
        usage_points = []
        for eq in lv_feeder.equipment:
            usage_points.extend(eq.usage_points)
        usage_points.sort(key=lambda up: up.mrid)

        usage_points_to_name = random.sample(usage_points, int(len(usage_points) * proportion / 100))

        usage_points_named = 0
        for usage_point in usage_points_to_name:
            try:
                next_nmi = next(nmi_generator)
            except StopIteration:
                break

            for name in usage_point.names:
                if name.type.name == "NMI":
                    usage_point.remove_name(name)
                    name.type.remove_name(name)
                    break

            usage_point.add_name(nmi_name_type.get_or_add_name(next_nmi, usage_point))
            usage_points_named += 1

        return usage_points_named

    return allocator


async def _create_synthetic_feeder(
        self: NetworkConsumerClient,
        feeder_mrid: str,
        allocator: Callable[[LvFeeder, NameType], int] = do_nothing_allocator,
        seed: Optional[int] = None
) -> Tuple[NetworkService, int]:
    """
    Creates a copy of the given `feeder_mrid` and runs `allocator` across the `LvFeeders` that belong to the `Feeder`.

    :param feeder_mrid: The mRID of the feeder to create a synthetic version.
    :param allocator: The allocator to use to modify the LvFeeders. Default will do nothing to the feeder.
    :return: 2-tuple of (the synthetic version of the NetworkService, the number of added identified objects)
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

    return feeder_network, total_allocated

NetworkConsumerClient.create_synthetic_feeder = _create_synthetic_feeder


def _sync_create_synthetic_feeder(
        self: SyncNetworkConsumerClient,
        feeder_mrid: str,
        allocator: Callable[[LvFeeder, NameType], int] = do_nothing_allocator,
        seed: Optional[int] = None
) -> Tuple[NetworkService, int]:
    return get_event_loop().run_until_complete(_create_synthetic_feeder(self, feeder_mrid, allocator, seed))


SyncNetworkConsumerClient.create_synthetic_feeder = _sync_create_synthetic_feeder
