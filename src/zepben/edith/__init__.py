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

from zepben.edith.linecode_catalogue import LINECODE_CATALOGUE

__all__ = ["do_nothing_mutator", "composite_mutator", "line_weakener", "transformer_weakener",
           "usage_point_proportional_allocator", "NetworkConsumerClient", "SyncNetworkConsumerClient"]

from zepben.edith.transformer_catalogue import TRANSFORMER_CATALOGUE


def do_nothing_mutator(_):
    return 0


def composite_mutator(mutators: Iterable[Callable[[NetworkService], int]]) -> Callable[[NetworkService], int]:
    def mutate(feeder_network):
        total_changed = 0
        for mut in mutators:
            mut(feeder_network)
        return total_changed
    return mutate


def line_weakener(
        weakening_percentage: int,
        use_weakest_when_necessary: bool = True
) -> Callable[[NetworkService], int]:
    if not 1 <= weakening_percentage <= 100:
        raise ValueError("Weakening percentage must be between 1 and 100")
    amp_rating_ratio = (100 - weakening_percentage) / 100

    hv_linecodes = list(filter(lambda lc: lc.hv, LINECODE_CATALOGUE))
    lv_linecodes = list(filter(lambda lc: not lc.hv, LINECODE_CATALOGUE))

    def mutate(feeder_network: NetworkService):
        # Add wire info and plsi for each linecode
        for lc in LINECODE_CATALOGUE:
            feeder_network.add(CableInfo(mrid=f"{lc.name} underground cable", rated_current=int(lc.norm_amps)))
            feeder_network.add(OverheadWireInfo(mrid=f"{lc.name} overhead line", rated_current=int(lc.norm_amps)))
            feeder_network.add(PerLengthSequenceImpedance(mrid=f"{lc.name} plsi", r0=lc.r0, x0=lc.x0, r=lc.r1, x=lc.x1))

        num_lines_modified = 0
        for acls in feeder_network.objects(AcLineSegment):
            try:
                terminal = acls.get_terminal_by_sn(1)
            except IndexError:
                continue

            if acls.wire_info is None:
                continue
            wire_info: WireInfo = acls.wire_info

            if acls.base_voltage_value > 1000:
                correct_voltage_lcs = hv_linecodes
            else:
                correct_voltage_lcs = lv_linecodes

            correct_phases_lcs = list(filter(
                lambda lc: lc.phases == terminal.phases.without_neutral.num_phases,
                correct_voltage_lcs
            ))
            viable_lcs = filter(
                lambda lc: lc.norm_amps <= wire_info.rated_current * amp_rating_ratio,
                correct_phases_lcs
            )
            if use_weakest_when_necessary:
                fallback_lc = min(correct_phases_lcs, key=lambda lc: lc.norm_amps, default=None)
            else:
                fallback_lc = None
            linecode = max(viable_lcs, key=lambda lc: lc.norm_amps, default=fallback_lc)
            if linecode is None:
                continue

            acls.per_length_sequence_impedance = feeder_network.get(f"{linecode.name} plsi", PerLengthSequenceImpedance)
            if isinstance(acls.wire_info, CableInfo):
                acls.wire_info = feeder_network.get(f"{linecode.name} underground cable", CableInfo)
            else:
                acls.wire_info = feeder_network.get(f"{linecode.name} overhead line", OverheadWireInfo)
            num_lines_modified += 1

        return num_lines_modified

    return mutate


def transformer_weakener(
        weakening_percentage: int,
        use_weakest_when_necessary: bool = True,
        match_voltages: bool = True
) -> Callable[[NetworkService], int]:
    if not 1 <= weakening_percentage <= 100:
        raise ValueError("Weakening percentage must be between 1 and 100")
    amp_rating_ratio = (100 - weakening_percentage) / 100

    def mutate(feeder_network: NetworkService):
        num_ends_modified = 0
        for tx in feeder_network.objects(PowerTransformer):
            ends = list(tx.ends)
            if len(ends) == 0:
                continue
            for end in ends:
                if end.rated_s is not None:
                    target_rated_va = end.rated_s * amp_rating_ratio
                    break
            else:
                continue

            correct_num_windings = filter(lambda xfmr: xfmr.windings == len(ends), TRANSFORMER_CATALOGUE)
            num_cores = ends[0].terminal.phases.without_neutral.num_phases
            correct_cores_xfmrs = filter(lambda xfmr: xfmr.phases == num_cores, correct_num_windings)
            if match_voltages:
                end_voltages = list(map(lambda end: end.rated_u/1000, ends))
                good_voltage_xfmrs = list(filter(lambda xfmr: xfmr.kvs == end_voltages, correct_cores_xfmrs))
            else:
                good_voltage_xfmrs = list(correct_cores_xfmrs)
            viable_xfmrs = filter(lambda xfmr: max(xfmr.kvas) * 1000 <= target_rated_va, good_voltage_xfmrs)

            if use_weakest_when_necessary:
                fallback_xfmr = min(good_voltage_xfmrs, key=lambda xfmr: max(xfmr.kvas), default=None)
            else:
                fallback_xfmr = None
            xfmr = max(viable_xfmrs, key=lambda xfmr: max(xfmr.kvas), default=fallback_xfmr)
            if xfmr is None:
                continue

            for end, new_kva_rating in zip(ends, xfmr.kvas):
                end.rated_s = new_kva_rating * 1000
                num_ends_modified += 1

        return num_ends_modified

    return mutate


def usage_point_proportional_allocator(
        proportion: int,
        edith_customers: List[str],
        allow_duplicate_customers: bool = False,
        seed: Optional[int] = None
) -> Callable[[NetworkService], int]:
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

    def mutate(feeder_network: NetworkService) -> int:
        random.seed(seed)
        try:
            nmi_name_type = feeder_network.get_name_type("NMI")
        except KeyError:
            # noinspection PyArgumentList
            nmi_name_type = NameType(name="NMI")
            feeder_network.add_name_type(nmi_name_type)

        usage_points_named = 0
        for lv_feeder in feeder_network.objects(LvFeeder):
            usage_points = []
            for eq in lv_feeder.equipment:
                usage_points.extend(eq.usage_points)
            usage_points.sort(key=lambda up: up.mrid)

            usage_points_to_name = random.sample(usage_points, int(len(usage_points) * proportion / 100))
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
            else:
                continue
            break

        return usage_points_named

    return mutate


async def _create_synthetic_feeder(
        self: NetworkConsumerClient,
        feeder_mrid: str,
        mutator: Callable[[NetworkService], int] = do_nothing_mutator
) -> int:
    """
    Creates a copy of the given `feeder_mrid` and runs `allocator` across the `LvFeeders` that belong to the `Feeder`.

    :param feeder_mrid: The mRID of the feeder to create a synthetic version.
    :param mutator: The mutator to use to modify the feeder network. Default will do nothing to the feeder.
    :return: The number of mutations performed on the feeder network.
    """

    await self.get_equipment_container(feeder_mrid, Feeder, include_energized_containers=INCLUDE_ENERGIZED_LV_FEEDERS)
    feeder_network = self.service

    total_allocated = mutator(feeder_network)

    return total_allocated

NetworkConsumerClient.create_synthetic_feeder = _create_synthetic_feeder


def _sync_create_synthetic_feeder(
        self: SyncNetworkConsumerClient,
        feeder_mrid: str,
        mutator: Callable[[NetworkService], int] = do_nothing_mutator
) -> int:
    return get_event_loop().run_until_complete(_create_synthetic_feeder(self, feeder_mrid, mutator))


SyncNetworkConsumerClient.create_synthetic_feeder = _sync_create_synthetic_feeder
