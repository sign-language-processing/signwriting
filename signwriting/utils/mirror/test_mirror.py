# pylint: disable=too-many-lines  # dominated by the _PAIRS_RAW data table
import unittest
import warnings

import numpy as np
from PIL import ImageOps

from signwriting.formats.swu_to_fsw import swu2fsw
from signwriting.utils.mirror import mirror_sign, mirror_symbol
from signwriting.utils.mirror.mirror import _symbol_exists
from signwriting.visualizer.visualize import signwriting_to_image

# User-confirmed (src, mirror) pairs. The authoritative list of symbol
# pairs that have been reviewed and signed off on - encoded once in each
# direction, then expanded into a set covering both directions.
_PAIRS_RAW = [
    # Contact: fill stays, rotation reflects (4-k)%4.
    ("S20600", "S20600"),

    # Movement 16-rotation: +8, fill stays (no fill swap).
    ("S2e95c", "S2e954"),
    ("S2e95e", "S2e956"),

    # Movement 4-rotation (n-k)%n: S219/S218/S21d.
    ("S21900", "S21900"),
    ("S21901", "S21903"),
    ("S21902", "S21902"),
    ("S21813", "S21811"),
    ("S21d03", "S21d01"),

    # Movement XOR arrows: fill 0<->1 swap + rotation XOR 1 (fill 2 stays).
    ("S2ae00", "S2ae11"),
    ("S2ae02", "S2ae13"),
    ("S2ae20", "S2ae21"),
    # Rotation Alternating (S2ac/S2b3): fill 0<->1 + rotation 3 - r.
    ("S2ac00", "S2ac13"),
    ("S2ac01", "S2ac12"),
    ("S2b300", "S2b313"),
    # 16-rotation arrows swap fill 0<->1 + rotation +8 (S2e7 Arm Circle).
    ("S2e700", "S2e718"),
    ("S2e710", "S2e708"),
    # Contact-style bases that DO swap fill 0<->1 (S22a/S22f).
    ("S22a02", "S22a16"),
    ("S22f02", "S22f16"),
    # Contact-style base that keeps fill (S226).
    ("S22602", "S22606"),
    ("S22600", "S22600"),
    # Bases below S22a keep fill (the general movement-fill rule starts at
    # S22a): S21a/S21f Sequential (+8), S223/S224 Hinge Sequential (+8).
    ("S21a08", "S21a00"),
    ("S21f00", "S21f08"),
    ("S22300", "S22308"),

    # S255-S26b Diagonal & Floor-plane Straight: fill 0<->1, fills 2/3/4
    # stay, face-style rotation.
    ("S25d00", "S25d10"),
    ("S25d04", "S25d14"),
    ("S25d01", "S25d17"),
    ("S25d05", "S25d13"),
    ("S25d24", "S25d24"),
    ("S26500", "S26510"),
    ("S26502", "S26516"),

    # S2c0 XOR-1 within fill 3.
    ("S2c030", "S2c031"),
    ("S2c034", "S2c035"),

    # S2ef / S2f0: fills 0<->1 (rotation preserved), fill 2 uses XOR-1.
    ("S2ef00", "S2ef10"),
    ("S2ef20", "S2ef21"),
    ("S2ef22", "S2ef23"),
    ("S2f010", "S2f000"),
    # S2ef / S2f0 fill 2 rotations 4/5 have no representable horizontal
    # mirror in ISWA, so they pass through unchanged (with a warning).
    ("S2ef24", "S2ef24"),
    ("S2ef25", "S2ef25"),
    ("S2f024", "S2f024"),
    ("S2f025", "S2f025"),

    # S2f3 / S2f4 Finger Circles Hits Wall: fill stays; rotation 0<->2,
    # 1<->3, 4<->5, 6<->7.
    ("S2f300", "S2f302"),
    ("S2f301", "S2f303"),
    ("S2f304", "S2f305"),
    ("S2f306", "S2f307"),
    ("S2f310", "S2f312"),
    ("S2f311", "S2f313"),
    ("S2f314", "S2f315"),
    ("S2f316", "S2f317"),
    ("S2f400", "S2f402"),
    ("S2f401", "S2f403"),
    ("S2f404", "S2f405"),
    ("S2f410", "S2f412"),

    # Cross-mirror inside the movement range.
    ("S22632", "S22636"),
    ("S2cf30", "S2cf31"),
    ("S22612", "S22616"),
    ("S22622", "S22626"),
    ("S22712", "S22716"),
    ("S22722", "S22726"),
    ("S22732", "S22736"),
    ("S22a23", "S22a25"),
    ("S22600", "S22600"),
    ("S22604", "S22604"),
    ("S2f023", "S2f022"),

    # Hump/Loop/Wave Hits Floor (S2c8-S2d1).
    ("S2c800", "S2c811"),
    ("S2c801", "S2c810"),
    ("S2c803", "S2c816"),
    ("S2c820", "S2c821"),
    ("S2c832", "S2c837"),
    ("S2cf30", "S2cf31"),
    ("S2d000", "S2d011"),
    ("S2d002", "S2d017"),
    ("S2d104", "S2d115"),

    # Curve Hits Ceiling (S2b7-S2b8).
    ("S2b700", "S2b711"),
    ("S2b720", "S2b721"),
    ("S2b730", "S2b741"),
    ("S2b750", "S2b751"),
    ("S2b803", "S2b816"),
    ("S2b837", "S2b842"),

    # Rotation Alternating Hits Floor (S2d4).
    ("S2d400", "S2d414"),
    ("S2d402", "S2d417"),
    ("S2d420", "S2d424"),
    ("S2d432", "S2d447"),

    # Various "Hits Ceiling/Floor" bases (dual-axis pair rule).
    ("S2c300", "S2c311"),
    ("S2c302", "S2c317"),
    ("S2c322", "S2c327"),
    ("S2c600", "S2c611"),
    ("S2c606", "S2c613"),
    ("S2c620", "S2c621"),
    ("S2c400", "S2c411"),
    ("S2c420", "S2c421"),
    ("S2c500", "S2c511"),
    ("S2c520", "S2c521"),
    ("S2c700", "S2c711"),
    ("S2c706", "S2c713"),
    ("S2c720", "S2c721"),
    ("S2c730", "S2c741"),
    ("S2d200", "S2d211"),
    ("S2d217", "S2d202"),

    # S2f2 Finger Circles Wall Double - rotation XOR 4, fill stays.
    ("S2f200", "S2f204"),
    ("S2f211", "S2f215"),

    # S326 fill 3 rotations 0 and 4 are special self-mirrors.
    ("S32630", "S32630"),
    ("S32634", "S32634"),

    # S2b9 / S2bb Hump Hits Ceiling 2/3 Humps Small.
    ("S2b900", "S2b911"),
    ("S2b903", "S2b916"),
    ("S2b920", "S2b921"),
    ("S2b930", "S2b931"),
    ("S2bb00", "S2bb11"),
    ("S2bb20", "S2bb21"),

    # S231 Double Alternating Movement, Wall Plane.
    ("S23100", "S23118"),
    ("S23120", "S23128"),
    ("S23105", "S2311d"),

    # S22e Single Wrist Flex, Wall Plane.
    ("S22e32", "S22e36"),

    # S226 / S228 - default contact-style rotation.
    ("S22602", "S22606"),
    ("S22803", "S22805"),

    # S269 Single Wrist Flex, Floor Plane.
    ("S26932", "S26936"),

    # S265-S268 Floor Plane bases - fills 2/3 stay; rotation 0 / 4 self.
    ("S26530", "S26530"),
    ("S26534", "S26534"),
    ("S26630", "S26630"),
    ("S26634", "S26634"),
    ("S26730", "S26730"),
    ("S26734", "S26734"),
    ("S26830", "S26830"),
    ("S26834", "S26834"),

    # Other confirmed pairs.
    ("S35c11", "S35c17"),
    ("S32913", "S32917"),
    ("S37d11", "S37d19"),
    ("S37330", "S37332"),
    ("S33817", "S33811"),

    # Known font issues: codepoint mapping is correct, but the rendered
    # glyph isn't the visual horizontal mirror. See README.md.
    ("S22822", "S22826"),
    ("S2311b", "S23103"),
    ("S23104", "S2311c"),
    ("S22922", "S22926"),

    # Newly confirmed pairs.
    ("S32911", "S32915"),
    ("S37c01", "S37c09"),
    ("S29824", "S2982c"),
    ("S2f542", "S2f546"),
    ("S2f512", "S2f516"),

    # S36f Shoulder Hip Move Wall Plane - fill 5 pairs.
    ("S36f50", "S36f58"),
    ("S36f54", "S36f5c"),

    # Confirmed self-mirrors.
    ("S36520", "S36520"),
    ("S32510", "S32510"),
    ("S31e30", "S31e30"),
    ("S30150", "S30150"),
    ("S30154", "S30154"),
    ("S36650", "S36650"),
    ("S32514", "S32514"),
    ("S31830", "S31830"),
    ("S35910", "S35910"),
    ("S32130", "S32130"),
    ("S32230", "S32230"),
    ("S32330", "S32330"),
    ("S36820", "S36820"),
    ("S36640", "S36640"),
    ("S32114", "S32114"),

    # S321 fill 1 face-style.
    ("S32111", "S32117"),
    ("S32113", "S32115"),

    # S35c Tongue Inside Mouth Relaxed - face-style at fill 1.
    ("S35c12", "S35c16"),

    # S35d Tongue Center Sticks Out - face-style at fill 1.
    ("S35d11", "S35d17"),
    ("S35d13", "S35d15"),

    # Additional confirmed self-mirrors.
    ("S36340", "S36340"),
    ("S32434", "S32434"),
    ("S32534", "S32534"),
    ("S36924", "S36924"),
    ("S31f30", "S31f30"),
    ("S32310", "S32310"),
    ("S32314", "S32314"),
    ("S32110", "S32110"),
    ("S36140", "S36140"),
    ("S34810", "S34810"),

    # Limb (S377-S37d) axis-aligned self-mirrors.
    ("S37700", "S37700"),
    ("S37708", "S37708"),
    ("S37800", "S37800"),
    ("S37808", "S37808"),
    ("S37900", "S37900"),
    ("S37908", "S37908"),
    ("S37a00", "S37a00"),
    ("S37a08", "S37a08"),
    ("S37b00", "S37b00"),
    ("S37b08", "S37b08"),
    ("S37c00", "S37c00"),
    ("S37c08", "S37c08"),
    ("S37d00", "S37d00"),
    ("S37d08", "S37d08"),
    ("S35f40", "S35f40"),

    # Confirmed self-mirrors.
    ("S32030", "S32030"),
    ("S32210", "S32210"),
    ("S32214", "S32214"),
    ("S32220", "S32220"),
    ("S32224", "S32224"),
    ("S33410", "S33410"),
    ("S35914", "S35914"),

    # S37e Fingers - no fill swap; rotation +8.
    ("S37e00", "S37e08"),
    ("S37e10", "S37e18"),
    ("S37e20", "S37e28"),
    ("S37e40", "S37e48"),
    ("S37e42", "S37e4a"),

    # Limb bases (S377-S37d): rotation 0/8 self-mirror, others +8.
    ("S37c0d", "S37c05"),

    # Other face fill overrides.
    ("S36110", "S36110"),
    ("S35850", "S35840"),
    ("S35750", "S35740"),
    ("S32c40", "S32c30"),
    ("S32c10", "S32c20"),
    ("S33000", "S33000"),
    ("S33010", "S33020"),
    ("S33040", "S33030"),

    # S368 / S369: no fill swap, face-style rotation.
    ("S36810", "S36810"),
    ("S36811", "S36817"),
    ("S36813", "S36815"),
    ("S36821", "S36827"),
    ("S36814", "S36814"),
    ("S36911", "S36917"),
    ("S36912", "S36916"),

    # S329: fill stays, rotation XOR 4 (8-rotation).
    ("S32900", "S32904"),
    ("S32901", "S32905"),
    ("S32902", "S32906"),
    ("S32903", "S32907"),
    ("S32921", "S32925"),
    ("S32923", "S32927"),

    # S387 Comma: fill stays, rotation 0<->4, 1<->7, 2<->6, 3<->5.
    ("S38700", "S38704"),
    ("S38701", "S38707"),
    ("S38702", "S38706"),
    ("S38703", "S38705"),
    ("S38732", "S38736"),

    # S369 confirmed at fill 2.
    ("S36921", "S36927"),

    # S372 / S373 / S374 Torso bases - rotation XOR 2.
    ("S37200", "S37202"),
    ("S37201", "S37203"),
    ("S37220", "S37220"),
    ("S37222", "S37222"),
    ("S37300", "S37302"),
    ("S37301", "S37303"),
    ("S37320", "S37322"),
    ("S37400", "S37402"),
    ("S37401", "S37403"),

    # S30a-S310 Eyebrows: fills 1<->2 and 4<->5.
    ("S30a10", "S30a20"),
    ("S30a40", "S30a50"),
    ("S30b10", "S30b20"),
    ("S30c10", "S30c20"),
    ("S30d10", "S30d20"),

    # S314-S320 Eyes: default 1<->2 fill swap; fills 0/3/4 stay.
    ("S31400", "S31400"),
    ("S31410", "S31420"),
    ("S31430", "S31430"),
    ("S31440", "S31440"),

    # S317 Eye Blink Single - also pairs fills 3<->4.
    ("S31730", "S31740"),

    # S328 Eyegaze Curved Floor Plane - no fill swap; rotation XOR 4.
    ("S32800", "S32804"),
    ("S32810", "S32814"),

    # Special one-off override: S32320 mirrors to S32324.
    ("S32320", "S32324"),

    # Confirmed self-mirrors with high pixel diff.
    ("S32134", "S32134"),
    ("S32234", "S32234"),
    ("S32334", "S32334"),
    ("S36824", "S36824"),

    # S308 / S309 Face Direction (16 rotations).
    ("S30800", "S30808"),
    ("S30802", "S3080a"),
    ("S30900", "S30908"),

    # S302 Head Movement Tilts Wall Plane - XOR-1.
    ("S30200", "S30201"),
    ("S30210", "S30211"),

    # S304/S305 Head Movement Curves Wall/Floor Plane - XOR-2.
    ("S30400", "S30402"),
    ("S30401", "S30403"),
    ("S30500", "S30502"),

    # S306 Head Movement Circles - XOR-1.
    ("S30600", "S30601"),
    ("S30602", "S30603"),

    # Confirmed self/cross.
    ("S34910", "S34910"),
    ("S32912", "S32916"),
    ("S37d01", "S37d09"),
    ("S32714", "S3271c"),
    ("S35e31", "S35e37"),
    ("S22702", "S22706"),
    ("S37d07", "S37d0f"),
    ("S37d0d", "S37d05"),
    ("S32223", "S32225"),
    ("S30353", "S30355"),

    # S307 Face Direction Positions, Nose Forward Tilting - XOR-1.
    ("S30700", "S30701"),
    ("S30710", "S30711"),

    # S326 Eyegaze Straight Floor Alternate - face-style with 0/4 swapped.
    ("S32600", "S32604"),
    ("S32601", "S32607"),
    ("S32602", "S32606"),

    # Confirmed self-mirrors.
    ("S35c10", "S35c10"),
    ("S35c14", "S35c14"),
    ("S36150", "S36150"),
    ("S36530", "S36530"),
    ("S36030", "S36030"),

    # Eyegaze fill-2 diagonals.
    ("S32221", "S32227"),
    ("S32321", "S32327"),
    ("S32621", "S32627"),

    # Tongue Inside Mouth Relaxed.
    ("S35c13", "S35c15"),

    # Loop Wall Plane Small Double (S298) - fill 0<->1, rotation +8.
    ("S29800", "S29818"),
    ("S29804", "S2981c"),
    ("S29806", "S2981e"),
    ("S29808", "S29810"),
    ("S2980a", "S29812"),
    ("S2980e", "S29816"),
    ("S29814", "S2980c"),
    ("S29834", "S2983c"),
    ("S29820", "S29828"),
    ("S29830", "S29838"),

    # S335 Air Blowing Out / S336 Air Sucking In / S356 Mouth Corners.
    ("S33500", "S33500"),
    ("S33510", "S33520"),
    ("S33530", "S33530"),
    ("S33540", "S33550"),
    ("S33610", "S33620"),
    ("S33640", "S33650"),
    ("S35610", "S35620"),
    ("S35640", "S35650"),

    # S32b Cheeks Neutral.
    ("S32b00", "S32b00"),
    ("S32b10", "S32b20"),
    ("S32b30", "S32b40"),

    # S365 Teeth on Lips - only fills 4<->5 swap.
    ("S36500", "S36500"),
    ("S36510", "S36510"),
    ("S36530", "S36530"),
    ("S36540", "S36550"),

    ("S31530", "S31530"),
    ("S31b30", "S31b30"),

    # S329 confirmed at fill 1.
    ("S32910", "S32914"),

    # S327 Eyegaze Curved Wall Plane.
    ("S32700", "S32708"),
    ("S32710", "S32718"),
    ("S32722", "S3272a"),
    ("S32726", "S3272e"),

    # S35e Tongue Moves Against Cheek.
    ("S35e33", "S35e35"),

    # S36d Shoulder Hip Spine.
    ("S36d00", "S36d00"),
    ("S36d01", "S36d03"),
    ("S36d02", "S36d02"),

    # S383 Location Depth - all symbols are self-mirror.
    ("S38300", "S38300"),
    ("S38312", "S38312"),
    ("S38340", "S38340"),

    # S376 Limb Combinations - custom rotation map.
    ("S37600", "S37600"),
    ("S37601", "S37609"),
    ("S37604", "S3760c"),
    ("S37605", "S3760e"),
    ("S37606", "S3760f"),
    ("S37607", "S3760d"),
    ("S37608", "S37608"),

    # S382 Location Width - custom rotation map.
    ("S38200", "S38200"),
    ("S38201", "S38202"),
    ("S38203", "S38204"),
    ("S38205", "S38206"),
    ("S38207", "S38208"),

    # S369 Jaw Movement Floor Plane.
    ("S36923", "S36925"),

    # S321-S326 Eyegaze Straight.
    ("S32100", "S32100"),
    ("S32101", "S32107"),
    ("S32102", "S32106"),
    ("S32103", "S32105"),
    ("S32104", "S32104"),
    ("S32200", "S32200"),
    ("S32201", "S32207"),
    ("S32203", "S32205"),
    ("S32204", "S32204"),
    ("S32431", "S32437"),
    ("S32433", "S32435"),
    ("S32531", "S32537"),
    ("S32533", "S32535"),
    ("S32631", "S32637"),
    ("S32633", "S32635"),

    # S339 Breath Exhale / S33a Breath Inhale.
    ("S33900", "S33910"),
    ("S33920", "S33930"),
    ("S33940", "S33950"),
    ("S33a00", "S33a10"),
    ("S33a20", "S33a30"),
    ("S33a40", "S33a50"),

    # S36f, S370, S371: fill stays, rotation +8.
    ("S36f10", "S36f18"),
    ("S36f20", "S36f28"),
    ("S37011", "S37019"),
    ("S37125", "S3712d"),

    # S386: fill stays, rotation XOR 4.
    ("S38600", "S38604"),
    ("S38601", "S38605"),
    ("S38602", "S38606"),
    ("S38603", "S38607"),
    ("S38608", "S3860c"),
    ("S38609", "S3860d"),
    ("S3860a", "S3860e"),
    ("S3860b", "S3860f"),

    # User-confirmed self-mirrors in the "other" range.
    ("S21e00", "S21e00"),
    ("S21e10", "S21e10"),
    ("S32f30", "S32f30"),
    ("S36130", "S36130"),
    ("S36350", "S36350"),
    ("S32e30", "S32e30"),
    ("S32d30", "S32d30"),
    ("S35010", "S35010"),
    ("S33110", "S33110"),

    # S36b Hair / S36c Excitement.
    ("S36b00", "S36b00"),
    ("S36b10", "S36b10"),
    ("S36b20", "S36b30"),
    ("S36c00", "S36c00"),
    ("S36c10", "S36c10"),
    ("S36c20", "S36c30"),

    # S2f7 Fast / S2f9 Tense / S2fa Relaxed.
    ("S2f700", "S2f710"),
    ("S2f720", "S2f730"),
    ("S2f900", "S2f910"),
    ("S2f920", "S2f930"),
    ("S2fa00", "S2fa10"),
    ("S2fa20", "S2fa30"),

    # S36e Shoulder Hip Positions.
    ("S36e00", "S36e00"),
    ("S36e01", "S36e05"),
    ("S36e02", "S36e04"),
    ("S36e03", "S36e03"),
    ("S36e10", "S36e13"),
    ("S36e11", "S36e15"),
    ("S36e12", "S36e14"),
    ("S36e20", "S36e23"),
    ("S36e21", "S36e25"),
    ("S36e30", "S36e33"),
    ("S36e40", "S36e41"),
    ("S36e42", "S36e42"),
    ("S36e43", "S36e43"),
    ("S36e44", "S36e45"),
]
CONFIRMED_PAIRS = {(a, b) for pair in _PAIRS_RAW for a, b in (pair, pair[::-1])}

# Canonical SWU examples sourced from real signs. Converted to FSW once at
# load time so the test cases live in their original notation but exercise
# the FSW-only API.
RENDER_MIRROR_CASES_SWU = [
    '𝠀񀀒񀀚񋚥񋛩𝠃𝤟𝤩񋛩𝣵𝤐񀀒𝤇𝣤񋚥𝤐𝤆񀀚𝣮𝣭',
    '𝠀񂇢񂇈񆙡񋎥񋎵𝠃𝤛𝤬񂇈𝤀𝣺񂇢𝤄𝣻񋎥𝤄𝤗񋎵𝤃𝣟񆙡𝣱𝣸',
    '𝠀񅨑񀀙񆉁𝠃𝤙𝤞񀀙𝣷𝤀񅨑𝣼𝤀񆉁𝣳𝣮',
    '𝠀񀕁𝠃𝤍𝤕񀕁𝣾𝣷',
    '𝠀񂌢񂇷񆙡񈗦𝠃𝤩𝤛񂌢𝣢𝣱񂇷𝣬𝤉񆙡𝤍𝣽񈗦𝤜𝤎',
    '𝠀񀀡𝠃𝤎𝤕񀀡𝣿𝣷',
    '𝠀񀀒񉁩񌏁𝠃𝤮𝤙񌏁𝣴𝣴񀀒𝤙𝣻񉁩𝤙𝣟',
    '𝠀񀂁񂇻񈟃񆕁𝠃𝤣𝤘񂇻𝤈𝤌񆕁𝣹𝤁񀂁𝤍𝣵񈟃𝣩𝣽',
    '𝠀񀀡񋎥񀀁𝠃𝤡𝤖񀀁𝤒𝣸񀀡𝣫𝣸񋎥𝣻𝣷',
    '𝠀񀀓񃛆񆿅񆕁𝠃𝤣𝤟񀀓𝤅𝣯񆕁𝤅𝣽񃛆𝣪𝣮񆿅𝤅𝤐',
    '𝠀񂇢񉳍񂇂񂇈𝠃𝤬𝤘񂇢𝤕𝣵񂇈𝣡𝣴񂇂𝣤𝣵񉳍𝣿𝣼',
    '𝠀񀀒񀀚񋠥񋡩𝠃𝤝𝤪񋡩𝣷𝤊񀀒𝤈𝣡񋠥𝤍𝤃񀀚𝣯𝣪',
    '𝠀񃧁񃧉񆿅񆿕񋸥𝠃𝤨𝤛񆿕𝣭𝤉񃧁𝤌𝣱񃧉𝣥𝣱񆿅𝤔𝤊񋸥𝣿𝤕',
    '𝠀񄹸񈗦񄾘𝠃𝤭𝤥񄹸𝣞𝣦񄾘𝤔𝤌񈗦𝣽𝣾',
    '𝠃𝤗𝤜񀀋𝣹𝤍񀁂𝣵𝣱',
    '𝠀񆅁񇅅𝠃𝤏𝤙񆅁𝣿𝣳񇅅𝣾𝤇',
    '𝠃𝤦𝤖񄵡𝣧𝣷񆅁𝤁𝤆񃉡𝤔𝣸',
    '𝠃𝤧𝤬񅩱𝤊𝤝񍳡𝣴𝣴',
    '𝠃𝤼𝤘񃛋𝣳𝣶񃛃𝤇𝣶񈙇𝤞𝣵񈙓𝣐𝣵񆇡𝤂𝤍',
    '𝠀񂋣񂋫񆕁񇆡𝠃𝤜𝤞񇆡𝣹𝣯񂋣𝤁𝤆񂋫𝣱𝤋񆕁𝣿𝣿',
    '𝠀񀟡񆄩񆕁񈟃񍩁𝠃𝤟𝥄񆄩𝤉𝤵񀟡𝤐𝤕񆕁𝤁𝤥񈟃𝣰𝤟񍩁𝣴𝣴',
    '𝠀񃁁񃁉񋠩񋡭񋸡𝠃𝤦𝤬񃁁𝤇𝤝񃁉𝣥𝤑񋡭𝣯𝣨񋠩𝤌𝣵񋸡𝤀𝣠',
    '𝠀񅡁񂇇񉨬𝠃𝤖𝤥񂇇𝣶𝣦񅡁𝣾𝣵񉨬𝣶𝤂',
    '𝠀񆅱񆅹񇆥񇆵񌁵𝠃𝤢𝥇񆅱𝤎𝤤񆅹𝣯𝤤񇆥𝤉𝤹񇆵𝣩𝤹񌁵𝣴𝣯',
    '𝠃𝤛𝤵񍉡𝣴𝣵񆄱𝤌𝤆񈠣𝤉𝤚',
]
RENDER_MIRROR_CASES = [swu2fsw(sw) for sw in RENDER_MIRROR_CASES_SWU]


def _render(fsw: str):
    return signwriting_to_image(fsw, antialiasing=False, trust_box=True)


def _pixel_diff_ratio(a, b):
    arr_a = np.array(a)
    arr_b = np.array(b)
    if arr_a.shape != arr_b.shape:
        return 1.0
    diff = (arr_a != arr_b).any(axis=-1).sum()
    return diff / (arr_a.shape[0] * arr_a.shape[1])


class MirrorHandCase(unittest.TestCase):
    """S100-S204: rotation 0-7 / 8-15 are mirror halves."""

    def test_swaps_halves(self):
        self.assertEqual('S10008', mirror_symbol('S10000'))
        self.assertEqual('S10000', mirror_symbol('S10008'))

    def test_preserves_orientation_offset(self):
        self.assertEqual('S1000d', mirror_symbol('S10005'))
        self.assertEqual('S10004', mirror_symbol('S1000c'))

    def test_fill_unchanged(self):
        self.assertEqual('S15028', mirror_symbol('S15020'))


class MirrorContactCase(unittest.TestCase):
    """S205-S216: fills encode visual variants, not handedness, so they
    are preserved. Rotations flip with (n - rotation) % n."""

    def test_single_rotation_contact_is_self_mirror(self):
        # S205 (contact) and S208 (grasp) each ship only fill 0 rotation 0.
        self.assertEqual('S20500', mirror_symbol('S20500'))
        self.assertEqual('S20800', mirror_symbol('S20800'))

    def test_touch_multiple_fill_preserved(self):
        # S20600 is the user-reported case: rotation 0 is horizontally
        # symmetric and fill 0 must NOT swap to fill 1.
        self.assertEqual('S20600', mirror_symbol('S20600'))
        self.assertEqual('S20610', mirror_symbol('S20610'))

    def test_touch_multiple_diagonal_rotations_swap(self):
        # S206 has 4 rotations covering 4 evenly-spaced angles; the two
        # diagonals (1 and 3) are mirror partners.
        self.assertEqual('S20603', mirror_symbol('S20601'))
        self.assertEqual('S20601', mirror_symbol('S20603'))
        self.assertEqual('S20602', mirror_symbol('S20602'))

    def test_surface_uses_eight_rotations(self):
        # S214 (surface) ships 8 rotations - mirror is (8 - k) % 8.
        self.assertEqual('S21407', mirror_symbol('S21401'))
        self.assertEqual('S21405', mirror_symbol('S21403'))
        self.assertEqual('S21404', mirror_symbol('S21404'))


class MirrorMovementCase(unittest.TestCase):
    """S217-S2f6: 16-rotation arrows use ``rotation + 8`` and swap fill
    0<->1 (handedness); fewer-rotation bases use ``(n - rotation) % n``
    (contact convention). Fills other than 0/1 are preserved."""

    def test_16_rotation_base_uses_plus_8(self):
        # S2e7 ships all 16 rotations; rotation 0 mirrors to rotation 8 and
        # fill 0 swaps to 1.
        self.assertEqual('S2e718', mirror_symbol('S2e700'))
        self.assertEqual('S2e708', mirror_symbol('S2e710'))
        # Fills other than 0/1 are preserved.
        self.assertEqual('S2e958', mirror_symbol('S2e950'))
        self.assertEqual('S2e954', mirror_symbol('S2e95c'))

    def test_16_rotation_diagonals(self):
        # S2e7 ships 6 fills, so fill 3<->4 also swap; rotation 4 + 8 = c.
        self.assertEqual('S2e73c', mirror_symbol('S2e744'))
        self.assertEqual('S2e744', mirror_symbol('S2e73c'))

    def test_8_rotation_contact_base_keeps_fill(self):
        # S226 ships 8 rotations; mirror is (8 - r) % 8 with no fill swap.
        self.assertEqual('S22606', mirror_symbol('S22602'))
        self.assertEqual('S22600', mirror_symbol('S22600'))
        self.assertEqual('S22604', mirror_symbol('S22604'))

    def test_8_rotation_contact_base_swaps_fill(self):
        # S22a / S22f are contact-style but DO encode handedness, so fill
        # 0<->1 swaps on top of the (8 - r) % 8 rotation.
        self.assertEqual('S22a16', mirror_symbol('S22a02'))
        self.assertEqual('S22a06', mirror_symbol('S22a12'))
        self.assertEqual('S22f16', mirror_symbol('S22f02'))

    def test_4_rotation_base_uses_face_style(self):
        # S219 ships 4 rotations per fill; rotation 0 and 2 are self-mirror,
        # rotations 1 and 3 swap.
        self.assertEqual('S21900', mirror_symbol('S21900'))
        self.assertEqual('S21902', mirror_symbol('S21902'))
        self.assertEqual('S21901', mirror_symbol('S21903'))
        self.assertEqual('S21903', mirror_symbol('S21901'))
        # Same pattern for S218 and S21d (and fill 1 versions).
        self.assertEqual('S21811', mirror_symbol('S21813'))
        self.assertEqual('S21d01', mirror_symbol('S21d03'))


class MirrorFaceCase(unittest.TestCase):
    """S2f7+: 8 rotations, no chirality. Mirror reflects the direction.

    Some head bases additionally encode handedness in fill 1 vs fill 2.
    """

    def test_axis_aligned_rotations_fixed(self):
        # S38800 is a punctuation glyph; symmetric, mirror is itself.
        self.assertEqual('S38800', mirror_symbol('S38800'))
        self.assertEqual('S38804', mirror_symbol('S38804'))

    def test_diagonal_rotations_swap(self):
        self.assertEqual('S30007', mirror_symbol('S30001'))
        self.assertEqual('S30001', mirror_symbol('S30007'))

    def test_head_fill_1_2_pair_swaps(self):
        # S30a is a single-eyebrow base; fill 1 and fill 2 are left/right.
        self.assertEqual('S30a20', mirror_symbol('S30a10'))
        self.assertEqual('S30a10', mirror_symbol('S30a20'))

    def test_head_without_fill_pair_keeps_fill(self):
        # S300 fills 1/2 are both symmetric in the font - no swap.
        self.assertEqual('S30000', mirror_symbol('S30000'))


class MirrorXorPairedMovementCase(unittest.TestCase):
    """S2a6-S2d3 (with gaps): fill 0<->1 (handedness) plus rotation XOR 1.
    Fills other than 0/1 are preserved."""

    def test_s2ae_fill_and_rotation_swap(self):
        # Fill 0 swaps to 1 and rotation flips (XOR 1).
        self.assertEqual('S2ae11', mirror_symbol('S2ae00'))
        self.assertEqual('S2ae10', mirror_symbol('S2ae01'))
        self.assertEqual('S2ae13', mirror_symbol('S2ae02'))
        # Fill 2 has no handedness pair, so it stays; rotation still flips.
        self.assertEqual('S2ae21', mirror_symbol('S2ae20'))
        self.assertEqual('S2ae20', mirror_symbol('S2ae21'))

    def test_xor_pairing_covers_full_range(self):
        # Spot-check the boundaries of the XOR range (fill 0 -> 1).
        self.assertEqual('S2a611', mirror_symbol('S2a600'))
        self.assertEqual('S2d311', mirror_symbol('S2d300'))

    def test_alternating_rotation_bases(self):
        # S2ac / S2b3 (Rotation Alternating) swap fill 0<->1 but reflect the
        # 4 rotations via 3 - rotation (0<->3, 1<->2) instead of XOR 1.
        self.assertEqual('S2ac13', mirror_symbol('S2ac00'))
        self.assertEqual('S2ac12', mirror_symbol('S2ac01'))
        self.assertEqual('S2ac00', mirror_symbol('S2ac13'))
        self.assertEqual('S2b313', mirror_symbol('S2b300'))


class MirrorOther16RotationCase(unittest.TestCase):
    """A handful of "other" (S2f7+) bases ship all 16 rotations and follow
    the hand-style +8 mirror convention rather than the 8-rotation face
    reflection."""

    def test_s37e_uses_plus_8(self):
        # User-reported: S37e40 → S37e48 (rotation 0 + 8), S37e42 → S37e4a.
        self.assertEqual('S37e48', mirror_symbol('S37e40'))
        self.assertEqual('S37e4a', mirror_symbol('S37e42'))
        self.assertEqual('S37e40', mirror_symbol('S37e48'))

    def test_other_16_rotation_bases(self):
        self.assertEqual('S32708', mirror_symbol('S32700'))
        self.assertEqual('S36f08', mirror_symbol('S36f00'))
        self.assertEqual('S37008', mirror_symbol('S37000'))
        self.assertEqual('S37108', mirror_symbol('S37100'))


class MirrorDiagonalAndFloorStraightCase(unittest.TestCase):
    """S255-S26b: fill 0<->1, fills 2/3/4 stay; face-style rotation."""

    def test_fill_0_1_swap_with_face_rotation(self):
        # Fill 0 with axis-aligned rotation (0, 4): partner is fill 1.
        self.assertEqual('S25d10', mirror_symbol('S25d00'))
        self.assertEqual('S25d14', mirror_symbol('S25d04'))
        # Fill 0 with diagonal: both fill (0<->1) and rotation flip.
        self.assertEqual('S25d17', mirror_symbol('S25d01'))
        self.assertEqual('S25d13', mirror_symbol('S25d05'))

    def test_higher_fills_stay(self):
        # Fills 2, 3, 4 keep their fill across the mirror.
        self.assertEqual('S25d24', mirror_symbol('S25d24'))
        self.assertEqual('S25d37', mirror_symbol('S25d31'))

    def test_floor_plane_8_rotation_bases(self):
        # S265-S26b have a contiguous 8-rotation set; same rule applies.
        self.assertEqual('S26510', mirror_symbol('S26500'))
        self.assertEqual('S26516', mirror_symbol('S26502'))
        self.assertEqual('S26525', mirror_symbol('S26523'))


class MirrorFaceFillOverrideCase(unittest.TestCase):
    """Per-base fill chirality overrides for the "other" section."""

    def test_s361_no_fill_swap(self):
        self.assertEqual('S36110', mirror_symbol('S36110'))
        self.assertEqual('S36130', mirror_symbol('S36130'))

    def test_s317_fill_3_4_swap(self):
        # S317 Eye Blink Single also pairs fills 3<->4 (other S314-S320
        # bases use only the default 1<->2 swap).
        self.assertEqual('S31720', mirror_symbol('S31710'))
        self.assertEqual('S31740', mirror_symbol('S31730'))
        self.assertEqual('S31730', mirror_symbol('S31740'))

    def test_s32c_combined_fill_swaps(self):
        self.assertEqual('S32c20', mirror_symbol('S32c10'))
        self.assertEqual('S32c30', mirror_symbol('S32c40'))

    def test_s357_s358_fill_4_5_swap(self):
        self.assertEqual('S35740', mirror_symbol('S35750'))
        self.assertEqual('S35840', mirror_symbol('S35850'))


class MirrorUserReportedRegressionCase(unittest.TestCase):
    """Pinned regression tests for every specific case the user has flagged
    so they can't drift. The authoritative list is ``_PAIRS_RAW`` /
    ``CONFIRMED_PAIRS`` at the top of this module."""

    def test_all_confirmed_pairs(self):
        for src, expected in CONFIRMED_PAIRS:
            with self.subTest(src=src, expected=expected):
                self.assertEqual(expected, mirror_symbol(src))

    def test_s37c0d_uses_limb_rule(self):
        # User: S37c0d mirror is either S37c0f or S37c05 (same glyph). With
        # the limb rule (S377-S37d), rotation d -> 5.
        self.assertEqual('S37c05', mirror_symbol('S37c0d'))

    def test_limb_bases_use_limb_rotation(self):
        # User: limbs S377-S37d use 0->0, 8->8, and otherwise +8.
        for base in ['S377', 'S378', 'S37a', 'S37c', 'S37d']:
            with self.subTest(base=base):
                # Axis-aligned rotations are self-mirror.
                self.assertEqual(f'{base}00', mirror_symbol(f'{base}00'))
                self.assertEqual(f'{base}08', mirror_symbol(f'{base}08'))
                # Diagonals chirality-swap via +8 (with wrap).
                self.assertEqual(f'{base}09', mirror_symbol(f'{base}01'))
                self.assertEqual(f'{base}05', mirror_symbol(f'{base}0d'))
                self.assertEqual(f'{base}0f', mirror_symbol(f'{base}07'))

    def test_s2ef_s2f0_fill_pairing(self):
        # User: S2ef rule is fills 0<->1 (rotation preserved), fill 2 uses
        # XOR-1 on rotation. Same for S2f0.
        self.assertEqual('S2ef10', mirror_symbol('S2ef00'))
        self.assertEqual('S2ef00', mirror_symbol('S2ef10'))
        self.assertEqual('S2ef14', mirror_symbol('S2ef04'))
        self.assertEqual('S2ef21', mirror_symbol('S2ef20'))
        self.assertEqual('S2ef23', mirror_symbol('S2ef22'))
        self.assertEqual('S2f010', mirror_symbol('S2f000'))
        self.assertEqual('S2f021', mirror_symbol('S2f020'))

    def test_s2c0_xor_1(self):
        # User: S2c030 -> S2c031, S2c034 -> S2c035 (XOR-1 within base).
        self.assertEqual('S2c031', mirror_symbol('S2c030'))
        self.assertEqual('S2c035', mirror_symbol('S2c034'))

    def test_s2f3_fill_1_mixed_pairings(self):
        # User: S2f3 fill 1 uses XOR-2 for rotations 0-3 and XOR-1 for 4-7.
        self.assertEqual('S2f312', mirror_symbol('S2f310'))
        self.assertEqual('S2f313', mirror_symbol('S2f311'))
        self.assertEqual('S2f315', mirror_symbol('S2f314'))
        self.assertEqual('S2f317', mirror_symbol('S2f316'))

    def test_s368_s369_no_fill_swap(self):
        # User: S368X0 and S368X4 stay; X1 <-> X7, X2 <-> X6, X3 <-> X5.
        # No fill swap, only face-style rotation. Same for S369.
        self.assertEqual('S36810', mirror_symbol('S36810'))
        self.assertEqual('S36817', mirror_symbol('S36811'))
        self.assertEqual('S36815', mirror_symbol('S36813'))
        self.assertEqual('S36814', mirror_symbol('S36814'))
        self.assertEqual('S36917', mirror_symbol('S36911'))
        self.assertEqual('S36916', mirror_symbol('S36912'))

    def test_s330_combined_fill_swaps(self):
        # User: S33010 -> S33020 (default 1<->2), S33040 -> S33030
        # (additional 3<->4 swap), S33000 -> S33000 (self).
        self.assertEqual('S33000', mirror_symbol('S33000'))
        self.assertEqual('S33020', mirror_symbol('S33010'))
        self.assertEqual('S33030', mirror_symbol('S33040'))

    def test_confirmed_self_mirrors_in_other_section(self):
        # User-confirmed self-mirrors that have asymmetric font rendering.
        # S2f9/S2fa used to be self-mirror but now pair via fill 0<->1,
        # 2<->3 (see _FACE_FILL_OVERRIDES); CONFIRMED_PAIRS covers their
        # corrected behavior.
        for s in ['S21e10', 'S32f30', 'S36130',
                  'S32e30', 'S32d30', 'S35010']:
            with self.subTest(s=s):
                self.assertEqual(s, mirror_symbol(s))

    def test_s22632_cross_mirror(self):
        # User: S22632 mirror is S22636 (face-style 2 -> 6 reflection).
        self.assertEqual('S22636', mirror_symbol('S22632'))
        self.assertEqual('S22632', mirror_symbol('S22636'))

    def test_no_mirror_symbols_warn_and_pass_through(self):
        # User: S2ef24/25 and S2f024/25 have no representable horizontal
        # mirror in ISWA; mirror_symbol returns them unchanged with a warning.
        for s in ['S2ef24', 'S2ef25', 'S2f024', 'S2f025']:
            with self.subTest(s=s):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    self.assertEqual(s, mirror_symbol(s))
                self.assertEqual(1, len(caught))
                self.assertIn('no representable horizontal mirror', str(caught[0].message))


class MirrorSymbolCase(unittest.TestCase):

    def test_unknown_symbol_passes_through(self):
        self.assertEqual('Szzzzz', mirror_symbol('Szzzzz'))

    def test_mirror_is_involution(self):
        for s in ['S10000', 'S10005', 'S22a02', 'S22a07',
                  'S38800', 'S2e748', 'S2e700', 'S30001',
                  'S2e95c', 'S21901', 'S21903', 'S20600',
                  'S2ae00', 'S2ae21', 'S37e40', 'S37e42']:
            self.assertEqual(s, mirror_symbol(mirror_symbol(s)))

    def test_mirror_is_involution_over_all_symbols(self):
        # mirror^2 must be the identity for every renderable ISWA symbol.
        # This guards the per-base override tables against asymmetric
        # entries (a pair mapped in only one direction).
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            for base_value in range(0x100, 0x38c):
                for fill in range(6):
                    for rotation in range(16):
                        symbol = f'S{base_value:x}{fill}{rotation:x}'
                        if not _symbol_exists(symbol):
                            continue
                        mirrored = mirror_symbol(symbol)
                        self.assertEqual(
                            symbol, mirror_symbol(mirrored),
                            f'{symbol} -> {mirrored} -> {mirror_symbol(mirrored)}',
                        )


class MirrorSignCase(unittest.TestCase):

    def test_rejects_non_ascii(self):
        with self.assertRaises(ValueError):
            mirror_sign('𝠃𝤛𝤵񍉡𝣴𝣵')

    def test_empty_sign_passes_through(self):
        self.assertEqual('M500x500', mirror_sign('M500x500'))

    def test_box_marker_flips_l_r(self):
        self.assertTrue(mirror_sign('L500x500S38800482x482').startswith('R'))
        self.assertTrue(mirror_sign('R500x500S38800482x482').startswith('L'))

    def test_m_box_marker_preserved(self):
        self.assertTrue(mirror_sign('M500x500S38800482x482').startswith('M'))

    def test_position_reflects_across_500(self):
        # Single-symbol sign with a chiral hand glyph: x should flip to the
        # mirrored side and the box's right edge becomes 1000 - orig_min_x.
        out = mirror_sign('M510x500S20310506x500')
        self.assertEqual('M494x500S20318479x500', out)

    def test_mirror_is_involution_on_renderable_signs(self):
        for fsw in RENDER_MIRROR_CASES:
            with self.subTest(fsw=fsw):
                # Mirroring once may rewrite the box to its canonical
                # symmetric form, but mirror^2 must then be stable.
                normalized = mirror_sign(mirror_sign(fsw))
                self.assertEqual(normalized, mirror_sign(mirror_sign(normalized)))

    def test_render_matches_flipped_original(self):
        # render(mirror(sign)) should equal the horizontal flip of
        # render(sign) up to font glyph asymmetries (some movement arrows
        # have 1px-asymmetric heads). 20% pixel-diff tolerance covers those.
        tolerance = 0.20
        for fsw in RENDER_MIRROR_CASES:
            with self.subTest(fsw=fsw):
                normalized = mirror_sign(mirror_sign(fsw))
                original = _render(normalized)
                mirrored = _render(mirror_sign(normalized))
                flipped = ImageOps.mirror(original)
                ratio = _pixel_diff_ratio(flipped, mirrored)
                self.assertLessEqual(
                    ratio, tolerance,
                    f'pixel diff {ratio:.2%} exceeds {tolerance:.0%} for {fsw}',
                )


if __name__ == '__main__':
    unittest.main()
