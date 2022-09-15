#  Copyright 2022 Zeppelin Bend Pty Ltd
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from asyncio import get_event_loop
from typing import List
from zepben.evolve import *


def do_nothing_allocator(_):
    pass


def distribution_transformer_proportional_allocator_creator(proportion: int, edith_customers: List[str]) -> Callable[[LvFeeder], None]:
    """
    Creates an allocator for the synthetic feeder creator that distributes a `proportion` of NMIs from `edith_customers` to an `LvFeeder`

    :param proportion: The percentage of Edith customers to distribute to an `LvFeeder`. Must be between 1 and 100
    :param edith_customers: The Edith NMIs to distribute to the `LvFeeder`
    :return: A function that takes an `LvFeeder` and distributes the `proportion` of NMIs across the EnergyConsumers on the `LvFeeder`.
    """
    if not 1 < proportion <= 100:
        raise ValueError("Proportion must be between 1 and 100")

    def allocator(lv_feeder: LvFeeder):
        # Note - given the same LvFeeder and proportion, this function should produce the same result.
        # if we can assume that the equipment on the LvFeeder is always in the same order, this can
        # be something simple where you just modify every X EnergyConsumer on the feeder or something (say where X is derived from the number
        # of EnergyConsumers on the feeder)
        pass

    return allocator


async def _create_synthetic_feeder(self, feeder_mrid: str, allocator: Callable[[LvFeeder], None] = do_nothing_allocator) -> NetworkService:
    """
    Creates a copy of the given `feeder_mrid` and runs `allocator` across the `LvFeeders` that belong to the `Feeder`.

    :param feeder_mrid: The mRID of the feeder to create a synthetic version.
    :param allocator: The allocator to use to modify the LvFeeders. Default will do nothing to the feeder.
    :return: The synthetic version of the NetworkService
    """
    # TODO: fetch the feeder from EWB
    # loop over the LvFeeders and call allocator on it
    # return the service

    return NetworkService()

NetworkConsumerClient.create_synthetic_feeder = _create_synthetic_feeder


def _sync_create_synthetic_feeder(self, feeder_mrid: str, allocator: Callable[[LvFeeder], None] = do_nothing_allocator) -> NetworkService:
    return get_event_loop().run_until_complete(self._create_synthetic_feeder(feeder_mrid, allocator))


SyncNetworkConsumerClient.create_synthetic_feeder = _sync_create_synthetic_feeder
