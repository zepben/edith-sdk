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

__all__ = ["line_weakener", "transformer_weakener",
           "usage_point_proportional_allocator", "NetworkConsumerClient", "SyncNetworkConsumerClient"]

from zepben.edith.transformer_catalogue import TRANSFORMER_CATALOGUE


def line_weakener(
        weakening_percentage: int,
        use_weakest_when_necessary: bool = True,
        callback: Optional[Callable[[Set[str]], Any]] = None
) -> Callable[[NetworkService], None]:
    """
    Returns a mutator function that downgrades lines based on their amp rating. Both the amp rating and impedance is
    updated using an entry in the built-in catalogue of linecodes. The linecode must match the voltage category (HV/LV)
    and phase count (e.g. 2 for AB, 3 for ABCN). If the target amp rating is lower than the amp rating of every
    candidate linecode, the one with the lowest amp rating will be used if `use_weakest_when_necessary` is `True`.

    :param weakening_percentage: Percentage to reduce amp rating of lines by. The linecode chosen for a line with an amp
                                 rating of N should have an amp rating of at most (100 - weakening_percentage)% of N.
    :param use_weakest_when_necessary: Whether to use the linecode with the lowest amp rating if the target amp rating
                                       for a line is too low. Defaults to `True`.
    :param callback: An optional callback that acts on the set of mRIDs of modified lines.

    :return: A mutator function that downgrades lines.
    """
    if not 1 <= weakening_percentage <= 100:
        raise ValueError("Weakening percentage must be between 1 and 100")
    amp_rating_ratio = (100 - weakening_percentage) / 100

    hv_linecodes = [lc for lc in LINECODE_CATALOGUE if lc.hv]
    lv_linecodes = [lc for lc in LINECODE_CATALOGUE if not lc.hv]

    def mutate(feeder_network: NetworkService):
        # Add wire info and plsi for each linecode
        for lc in LINECODE_CATALOGUE:
            feeder_network.add(CableInfo(mrid=f"{lc.name}-ug", rated_current=int(lc.norm_amps)))
            feeder_network.add(OverheadWireInfo(mrid=f"{lc.name}-oh", rated_current=int(lc.norm_amps)))
            feeder_network.add(PerLengthSequenceImpedance(mrid=f"{lc.name}-plsi", r0=lc.r0, x0=lc.x0, r=lc.r1, x=lc.x1))

        lines_modified = set()
        for acls in feeder_network.objects(AcLineSegment):
            try:
                terminal = acls.get_terminal_by_sn(1)
            except IndexError:
                continue

            if acls.wire_info is None or acls.wire_info.rated_current is None:
                continue
            wire_info: WireInfo = acls.wire_info

            if acls.base_voltage_value > 1000:
                correct_voltage_lcs = hv_linecodes
            else:
                correct_voltage_lcs = lv_linecodes

            correct_phases_lcs = [
                lc for lc in correct_voltage_lcs if lc.phases == terminal.phases.without_neutral.num_phases
            ]
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

            acls.per_length_sequence_impedance = feeder_network.get(f"{linecode.name}-plsi", PerLengthSequenceImpedance)
            if isinstance(acls.wire_info, CableInfo):
                acls.wire_info = feeder_network.get(f"{linecode.name}-ug", CableInfo)
            else:
                acls.wire_info = feeder_network.get(f"{linecode.name}-oh", OverheadWireInfo)
            lines_modified.add(acls.mrid)

        if callback is not None:
            callback(lines_modified)

    return mutate


def transformer_weakener(
        weakening_percentage: int,
        use_weakest_when_necessary: bool = True,
        match_voltages: bool = True,
        callback: Optional[Callable[[Set[str]], Any]] = None
) -> Callable[[NetworkService], None]:
    """
    Returns a mutator function that downgrades transformers based on their VA rating. The VA rating of transformer ends
    are updated using an entry in the built-in catalogue of transformer models. The model must match the number of
    windings (usually 2), number of phases on each winding, and the operating voltages of each winding unless
    `match_voltages` is `False`. If the target VA rating is lower than the VA rating of every candidate transformer
    model, the one with the lowest VA rating will be used if `use_weakest_when_necessary` is `True`.

    :param weakening_percentage: Percentage to reduce VA rating of transformer ends by. The transformer model chosen
                                 for a line with an VA rating of N should have a VA rating of at most
                                 (100 - weakening_percentage)% of N.
    :param use_weakest_when_necessary: Whether to use the transformer model with the lowest VA rating if the target
                                       VA rating for a line is too low. Defaults to `True`.
    :param match_voltages: Whether to match the operating voltage of transformer windings when selecting a transformer
                           model. Defaults to `True`.
    :param callback: An optional callback is called on the set of mRIDs of modified transformers.

    :return: A mutator function that downgrades transformers.
    """
    if not 1 <= weakening_percentage <= 100:
        raise ValueError("Weakening percentage must be between 1 and 100")
    amp_rating_ratio = (100 - weakening_percentage) / 100

    def mutate(feeder_network: NetworkService):
        modified_txs = set()
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
                end_voltages = [end.rated_u/1000 for end in ends]
                good_voltage_xfmrs = [xfmr for xfmr in correct_cores_xfmrs if xfmr.kvs == end_voltages]
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

            modified_txs.add(tx.mrid)

        if callback is not None:
            callback(modified_txs)

    return mutate


def usage_point_proportional_allocator(
        proportion: int,
        edith_customers: List[str],
        allow_duplicate_customers: bool = False,
        seed: Optional[int] = None,
        callback: Optional[Callable[[Set[str]], Any]] = None
) -> Callable[[NetworkService], None]:
    """
    Creates a mutator function that distributes a `proportion` of NMIs from `edith_customers`
    to the `UsagePoint`s in the network.

    :param proportion: The percentage of Edith customers to distribute to an `LvFeeder`. Must be between 1 and 100
    :param edith_customers: The Edith NMIs to distribute to the `UsagePoint`s in the network.
    :param allow_duplicate_customers: Reuse customers from the list to reach the proportion if necessary. Defaults to
                                      `False`.
    :param seed: A number to seed the random number generator with. Defaults to not seeding.
    :param callback: An optional function that is called on the set of mRIDs of `UsagePoint`s that are named.

    :return: A mutator function that distributes NMIs across `proportion`% of the `UsagePoint`s, and returns the set
             of mRIDs of modified `UsagePoint`s.
    """
    if not 1 <= proportion <= 100:
        raise ValueError("Proportion must be between 1 and 100")

    if allow_duplicate_customers:
        nmi_generator = itertools.cycle(edith_customers)
    else:
        nmi_generator = iter(edith_customers)

    def mutate(feeder_network: NetworkService):
        random.seed(seed)
        try:
            nmi_name_type = feeder_network.get_name_type("NMI")
        except KeyError:
            # noinspection PyArgumentList
            nmi_name_type = NameType(name="NMI")
            feeder_network.add_name_type(nmi_name_type)

        usage_points_named = set()
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
                usage_points_named.add(usage_point.mrid)
            else:
                continue
            break

        if callback is not None:
            callback(usage_points_named)

    return mutate


async def _create_synthetic_feeder(
        self: NetworkConsumerClient,
        feeder_mrid: str,
        mutators: Iterable[Callable[[NetworkService], None]] = ()
):
    """
    Creates a copy of the given `feeder_mrid` and runs `mutator` to the copied network.

    :param feeder_mrid: The mRID of the feeder to create a synthetic version of.
    :param mutators: The mutator functions to use to modify the feeder network. Defaults to no mutator functions.
    :return: The mRIDs of the mutated objects in the feeder network.
    """

    (await self.get_equipment_container(feeder_mrid, Feeder, include_energized_containers=INCLUDE_ENERGIZED_LV_FEEDERS)).throw_on_error()

    for mutator in mutators:
        mutator(self.service)

NetworkConsumerClient.create_synthetic_feeder = _create_synthetic_feeder


def _sync_create_synthetic_feeder(
        self: SyncNetworkConsumerClient,
        feeder_mrid: str,
        mutators: Iterable[Callable[[NetworkService], None]] = ()
):
    """
    Creates a copy of the given `feeder_mrid` and runs `mutator` to the copied network.

    :param feeder_mrid: The mRID of the feeder to create a synthetic version of.
    :param mutator: The mutator to use to modify the feeder network. Default will do nothing to the feeder.
    :return: The mRIDs of the mutated objects in the feeder network.
    """
    return get_event_loop().run_until_complete(_create_synthetic_feeder(self, feeder_mrid, mutators))


SyncNetworkConsumerClient.create_synthetic_feeder = _sync_create_synthetic_feeder
