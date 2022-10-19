#  Copyright 2022 Zeppelin Bend Pty Ltd
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
from dataclasses import dataclass


@dataclass
class LC(object):
    name: str
    phases: int
    norm_amps: float
    emerg_amps: float
    r0: float
    r1: float
    x0: float
    x1: float
    hv: bool = False

LINECODE_CATALOGUE = [
    LC("Flourine_7/3.00_AAAC/1120_3W", phases=3, norm_amps=165.38, emerg_amps=248.07, r1=0.0006016, r0=0.0007516, x1=0.000384, x0=0.001599, hv=True),
    LC("Flourine_7/3.00_AAAC/1120_2W", phases=2, norm_amps=165.38, emerg_amps=248.07, r1=0.0006016, r0=0.0007016, x1=0.0004013, x0=0.0011761, hv=True),
    LC("Flourine_7/3.00_AAAC/1120_1W", phases=1, norm_amps=165.38, emerg_amps=248.07, r1=0.0006516, r0=0.0006516, x1=0.0007887, x0=0.0007887, hv=True),
    LC("Helium_7/3.75_AAAC/1120_3W", phases=3, norm_amps=215.62, emerg_amps=323.43, r1=0.0003853, r0=0.0005353, x1=0.0003712, x0=0.0015862, hv=True),
    LC("Helium_7/3.75_AAAC/1120_2W", phases=2, norm_amps=215.62, emerg_amps=323.43, r1=0.0003853, r0=0.0004853, x1=0.0003885, x0=0.0011633, hv=True),
    LC("Helium_7/3.75_AAAC/1120_1W", phases=1, norm_amps=215.62, emerg_amps=323.43, r1=0.0004353, r0=0.0004353, x1=0.0007759, x0=0.0007759, hv=True),
    LC("Hydrogen_7/4.50_AAAC/1120_3W", phases=3, norm_amps=267.14, emerg_amps=400.71, r1=0.0002676, r0=0.0004176, x1=0.0003586, x0=0.0015736, hv=True),
    LC("Hydrogen_7/4.50_AAAC/1120_2W", phases=2, norm_amps=267.14, emerg_amps=400.71, r1=0.0002676, r0=0.0003676, x1=0.0003759, x0=0.0011507, hv=True),
    LC("Hydrogen_7/4.50_AAAC/1120_1W", phases=1, norm_amps=267.14, emerg_amps=400.71, r1=0.0003176, r0=0.0003176, x1=0.0007633, x0=0.0007633, hv=True),
    LC("Neon_19/3.75_AAAC/1120_3W", phases=3, norm_amps=386.19, emerg_amps=579.285, r1=0.0001433, r0=0.0002933, x1=0.0003353, x0=0.0015503, hv=True),
    LC("Neon_19/3.75_AAAC/1120_2W", phases=2, norm_amps=386.19, emerg_amps=579.285, r1=0.0001433, r0=0.0002433, x1=0.0003527, x0=0.0011274, hv=True),
    LC("Neon_19/3.75_AAAC/1120_1W", phases=1, norm_amps=386.19, emerg_amps=579.285, r1=0.0001933, r0=0.0001933, x1=0.00074, x0=0.00074, hv=True),
    LC("Nitrogen_37/3.00_AAAC/1120_3W", phases=3, norm_amps=438.21, emerg_amps=657.315, r1=0.0001153, r0=0.0002653, x1=0.0003274, x0=0.0015423, hv=True),
    LC("Nitrogen_37/3.00_AAAC/1120_2W", phases=2, norm_amps=438.21, emerg_amps=657.315, r1=0.0001153, r0=0.0002153, x1=0.0003447, x0=0.0011195, hv=True),
    LC("Nitrogen_37/3.00_AAAC/1120_1W", phases=1, norm_amps=438.21, emerg_amps=657.315, r1=0.0001653, r0=0.0001653, x1=0.0007321, x0=0.0007321, hv=True),
    LC("Neptune_19/3.25_AAC/1350_3W", phases=3, norm_amps=333.38, emerg_amps=500.07, r1=0.0001825, r0=0.0003325, x1=0.0003443, x0=0.0015592, hv=True),
    LC("Neptune_19/3.25_AAC/1350_2W", phases=2, norm_amps=333.38, emerg_amps=500.07, r1=0.0001825, r0=0.0002825, x1=0.0003616, x0=0.0011364, hv=True),
    LC("Neptune_19/3.25_AAC/1350_1W", phases=1, norm_amps=333.38, emerg_amps=500.07, r1=0.0002325, r0=0.0002325, x1=0.000749, x0=0.000749, hv=True),
    LC("Pluto_19/3.75_AAC/1350_3W", phases=3, norm_amps=393.27, emerg_amps=589.905, r1=0.0001375, r0=0.0002875, x1=0.0003353, x0=0.0015503, hv=True),
    LC("Pluto_19/3.75_AAC/1350_2W", phases=2, norm_amps=393.27, emerg_amps=589.905, r1=0.0001375, r0=0.0002375, x1=0.0003527, x0=0.0011274, hv=True),
    LC("Pluto_19/3.75_AAC/1350_1W", phases=1, norm_amps=393.27, emerg_amps=589.905, r1=0.0001875, r0=0.0001875, x1=0.00074, x0=0.00074, hv=True),
    LC("Mercury_7/4.50_AAC/1350_3W", phases=3, norm_amps=271.92, emerg_amps=407.88, r1=0.000257, r0=0.000407, x1=0.0003586, x0=0.0015736, hv=True),
    LC("Mercury_7/4.50_AAC/1350_2W", phases=2, norm_amps=271.92, emerg_amps=407.88, r1=0.000257, r0=0.000357, x1=0.0003759, x0=0.0011507, hv=True),
    LC("Mercury_7/4.50_AAC/1350_1W", phases=1, norm_amps=271.92, emerg_amps=407.88, r1=0.000307, r0=0.000307, x1=0.0007633, x0=0.0007633, hv=True),
    LC("Raisin_3/4/2.50_ACSR/GZ_3W", phases=3, norm_amps=96.2, emerg_amps=144.3, r1=0.0016264, r0=0.0017764, x1=0.0004584, x0=0.0016735, hv=True),
    LC("Raisin_3/4/2.50_ACSR/GZ_2W", phases=2, norm_amps=96.2, emerg_amps=144.3, r1=0.0016264, r0=0.0017264, x1=0.0004757, x0=0.0012505, hv=True),
    LC("Raisin_3/4/2.50_ACSR/GZ_1W", phases=1, norm_amps=96.2, emerg_amps=144.3, r1=0.0016764, r0=0.0016764, x1=0.0008631, x0=0.0008631, hv=True),
    LC("Rosella_4/3/0.093_ACSR/GZ_3W", phases=3, norm_amps=94.03, emerg_amps=141.045, r1=0.0016651, r0=0.0018151, x1=0.0003946, x0=0.0016096, hv=True),
    LC("Rosella_4/3/0.093_ACSR/GZ_2W", phases=2, norm_amps=94.03, emerg_amps=141.045, r1=0.0016651, r0=0.0017651, x1=0.000412, x0=0.0011868, hv=True),
    LC("Rosella_4/3/0.093_ACSR/GZ_1W", phases=1, norm_amps=94.03, emerg_amps=141.045, r1=0.0017151, r0=0.0017151, x1=0.0007994, x0=0.0007994, hv=True),
    LC("ACSR/GZ_2/5/3.25_ACSR/GZ_3W", phases=3, norm_amps=108.21, emerg_amps=162.315, r1=0.0014211, r0=0.0015711, x1=0.0003746, x0=0.0015896, hv=True),
    LC("ACSR/GZ_2/5/3.25_ACSR/GZ_2W", phases=2, norm_amps=108.21, emerg_amps=162.315, r1=0.0014211, r0=0.0015211, x1=0.000392, x0=0.0011667, hv=True),
    LC("ACSR/GZ_2/5/3.25_ACSR/GZ_1W", phases=1, norm_amps=108.21, emerg_amps=162.315, r1=0.0014711, r0=0.0014711, x1=0.0007794, x0=0.0007794, hv=True),
    LC("ACSR/GZ_6/1/0.089_ACSR/GZ_3W", phases=3, norm_amps=110.93, emerg_amps=166.395, r1=0.0011755, r0=0.0013255, x1=0.0004034, x0=0.0016184, hv=True),
    LC("ACSR/GZ_6/1/0.089_ACSR/GZ_2W", phases=2, norm_amps=110.93, emerg_amps=166.395, r1=0.0011755, r0=0.0012755, x1=0.0004208, x0=0.0011956, hv=True),
    LC("ACSR/GZ_6/1/0.089_ACSR/GZ_1W", phases=1, norm_amps=110.93, emerg_amps=166.395, r1=0.0012255, r0=0.0012255, x1=0.0008082, x0=0.0008082, hv=True),
    LC("Almond_6/1/2.50_ACSR/GZ_3W", phases=3, norm_amps=121.32, emerg_amps=181.98, r1=0.0010225, r0=0.0011725, x1=0.0004022, x0=0.0016172, hv=True),
    LC("Almond_6/1/2.50_ACSR/GZ_2W", phases=2, norm_amps=121.32, emerg_amps=181.98, r1=0.0010225, r0=0.0011225, x1=0.0004195, x0=0.0011943, hv=True),
    LC("Almond_6/1/2.50_ACSR/GZ_1W", phases=1, norm_amps=121.32, emerg_amps=181.98, r1=0.0010725, r0=0.0010725, x1=0.0008069, x0=0.0008069, hv=True),
    LC("Banana_6/1/3.75_ACSR/GZ_3W", phases=3, norm_amps=190.58, emerg_amps=285.87, r1=0.0004839, r0=0.0006339, x1=0.0003771, x0=0.0015921, hv=True),
    LC("Banana_6/1/3.75_ACSR/GZ_2W", phases=2, norm_amps=190.58, emerg_amps=285.87, r1=0.0004839, r0=0.0005839, x1=0.0003944, x0=0.0011692, hv=True),
    LC("Banana_6/1/3.75_ACSR/GZ_1W", phases=1, norm_amps=190.58, emerg_amps=285.87, r1=0.0005339, r0=0.0005339, x1=0.0007818, x0=0.0007818, hv=True),
    LC("2_Core_Al_LV_XLPE_ABC_OH_2W", phases=2, norm_amps=105, emerg_amps=157.5, r1=0.0014176, r0=0.0014176, x1=0.000089, x0=0.000089),
    LC("4_Core_Al_LV_XLPE_ABC_OH_4W", phases=3, norm_amps=97, emerg_amps=145.5, r1=0.0014176, r0=0.00595151, x1=0.000097, x0=0.000097),
    LC("AAAC:7/4.50", phases=3, norm_amps=383, emerg_amps=574.5, r1=0.000315100014, r0=0.000315100014, x1=0.000305000007, x0=0.000915000021),
    LC("AAAC:19/3.25", phases=3, norm_amps=473, emerg_amps=709.5, r1=0.000225400001, r0=0.000225400001, x1=0.000290600002, x0=0.000871800006),
    LC("AAAC:19/3.75", phases=3, norm_amps=562, emerg_amps=843, r1=0.000171200007, r0=0.000171200007, x1=0.000281699985, x0=0.000845099955),
    LC("AAAC:19/4.75", phases=3, norm_amps=747, emerg_amps=1120.5, r1=0.000110600002, r0=0.000110600002, x1=0.000266799986, x0=0.000800399958),
    LC("AAAC:37/3.00", phases=3, norm_amps=642, emerg_amps=963, r1=0.000138500005, r0=0.000138500005, x1=0.000273900002, x0=0.000821700006),
    LC("ABC2w:25ABC", phases=2, norm_amps=105, emerg_amps=157.5, r1=0.001417600036, r0=0.001417600036, x1=0.000089, x0=0.000267),
    LC("ABC2w:95ABC", phases=2, norm_amps=230, emerg_amps=345, r1=0.000378600001, r0=0.000378600001, x1=0.00008, x0=0.00024),
    LC("ABC4w:25ABC", phases=3, norm_amps=97, emerg_amps=145.5, r1=0.001417600036, r0=0.001417600036, x1=0.000097, x0=0.000291),
    LC("ABC4w:50ABC", phases=3, norm_amps=140, emerg_amps=210, r1=0.000757300019, r0=0.000757300019, x1=0.000093, x0=0.000279),
    LC("ABC4w:70ABC", phases=3, norm_amps=175, emerg_amps=262.5, r1=0.000524200022, r0=0.000524200022, x1=0.000088, x0=0.000264),
    LC("ABC4w:95ABC", phases=3, norm_amps=215, emerg_amps=322.5, r1=0.000378600001, r0=0.000378600001, x1=0.000087, x0=0.000261),
    LC("ABC4w:150ABC", phases=3, norm_amps=280, emerg_amps=420, r1=0.000244499996, r0=0.000244499996, x1=0.000084, x0=0.000252),
    LC("Cu_U/G:16C/4c", phases=3, norm_amps=105, emerg_amps=157.5, r1=0.001399999976, r0=0.001399999976, x1=0.0000805, x0=0.0002415),
    LC("Cu_U/G:25C/4c", phases=3, norm_amps=150, emerg_amps=225, r1=0.000884000003, r0=0.000884000003, x1=0.0000808, x0=0.0002424),
    LC("Cu_U/G:50C/4c", phases=3, norm_amps=215, emerg_amps=322.5, r1=0.000470999986, r0=0.000470999986, x1=0.0000751, x0=0.0002253),
    LC("Cu_U/G:70C/1c", phases=3, norm_amps=260, emerg_amps=390, r1=0.000326999992, r0=0.000326999992, x1=0.000104000002, x0=0.000312000006),
    LC("Cu_U/G:35mm/4C", phases=3, norm_amps=135, emerg_amps=202.5, r1=0.000667999983, r0=0.000667999983, x1=0.000136999995, x0=0.000410999985),
    LC("Cu_U/G:50mm/4C", phases=3, norm_amps=160, emerg_amps=240, r1=0.000493999988, r0=0.000493999988, x1=0.000129999995, x0=0.000389999985),
    LC("Al_UG:120A/4C", phases=3, norm_amps=255, emerg_amps=382.5, r1=0.000310000002, r0=0.000310000002, x1=0.0000685, x0=0.0002055),
    LC("Al_UG:185A/4C", phases=3, norm_amps=325, emerg_amps=487.5, r1=0.000202000007, r0=0.000202000007, x1=0.0000686, x0=0.0002058),
    LC("Al_UG:240A/4C", phases=3, norm_amps=380, emerg_amps=570, r1=0.000153999999, r0=0.000153999999, x1=0.0000678, x0=0.0002034),
    LC("CONSAC:70mm", phases=3, norm_amps=170, emerg_amps=255, r1=0.000541000009, r0=0.000541000009, x1=0.0000646, x0=0.0001938),
    LC("CONSAC:185mm", phases=3, norm_amps=305, emerg_amps=457.5, r1=0.000201000005, r0=0.000201000005, x1=0.0000622, x0=0.0001866),
    LC("CONSAC:300mm", phases=3, norm_amps=395, emerg_amps=592.5, r1=0.000123999998, r0=0.000123999998, x1=0.0000614, x0=0.0001842),
    LC('line-237A-aac-7-3w', phases=3, norm_amps=237, emerg_amps=355.5, r1=0.000684800029, r0=0.000684800029, x1=0.000330500007, x0=0.000330500007),
    LC('line-388A-aac-7-4.5-1w', phases=1, norm_amps=388, emerg_amps=582, r1=0.000307099998, r0=0.000307099998, x1=0.000305, x0=0.000305),
    LC('line-479A-aac-19-3.25-3w', phases=3, norm_amps=479, emerg_amps=582, r1=0.000219400004, r0=0.000219400004, x1=0.000290600002, x0=0.000290600002),
    LC('line-479A-aac-19-3.25-1w', phases=1, norm_amps=479, emerg_amps=582, r1=0.000219400004, r0=0.000219400004, x1=0.000290600002, x0=0.000290600002),
    LC('test-linecode-1w', phases=1, norm_amps=600, emerg_amps=800, r1=0.000219400004, r0=0.000219400004, x1=0.000290600002, x0=0.000290600002),
    LC('test-linecode-3w', phases=3, norm_amps=600, emerg_amps=800, r1=0.000219400004, r0=0.000219400004, x1=0.000290600002, x0=0.000290600002),
]


def get_linecode_to_parameters_catalogue():
    """
    Returns a sorted map between linecode names and linecode parameters including  norm_amps and phases
    :param dss: DSSDLL client with
    :return: sorted dictionary by norm_amps such as {'linecode': [norm_amps, phases]
    """
    sorted_line_codes = sorted(LINECODE_CATALOGUE, key=lambda x: x.norm_amps)
    return sorted_line_codes
