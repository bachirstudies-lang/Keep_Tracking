"""Génère le schéma KiCad (format v8, lisible par KiCad 9) du traceur Keep Tracking — rév. C.

Rév. C : brochages corrigés d'après les datasheets (STM32WLE5 UFQFPN48, TPS63900, MAX-M10S, LIS2DW12),
ITERM BQ24074, LM66100 en blocage de courant inverse + OR-ing VIN_BB, équilibrage supercaps sans fuite,
V_BCKP GNSS commuté, couplage TCXO 220 Ω + 10 pF, accord d'antenne LoRa en Pi, classes de nets 50 Ω.

Rév. B : protections d'entrée (USB, batterie, piézo, RF), filtrage par rail (ferrites + découplage
par broche), séries anti-rétro-alimentation GNSS, points de test. Feuille A1, blocs déplaçables (ORG).
"""
import sys, uuid, math, os

OUT = sys.argv[1]
U = lambda: str(uuid.uuid4())
ROOT = U()
G = 1.27

def f(v):
    v = round(v, 4)
    return ("%.4f" % v).rstrip("0").rstrip(".") if v != int(v) else str(int(v))

FONT = "(effects (font (size 1.27 1.27)))"

# ---------------------------------------------------------------- lib symbols
lib = {}          # lib_id -> sexpr
pins_of = {}      # lib_id -> list of (num, x, y, dir)  dir = outward direction 'L','R','U','D'

def prop(name, val, x=0, y=0, hide=False, just=None):
    j = f" (justify {just})" if just else ""
    eff = f"(effects (font (size 1.27 1.27)){j}{' hide' if hide else ''})"
    return f'(property "{name}" "{val}" (at {f(x)} {f(y)} 0) {eff})'

def pin_s(num, name, x, y, ang, length, ptype="passive", hide=False):
    h = " hide" if hide else ""
    return (f'(pin {ptype} line (at {f(x)} {f(y)} {ang}) (length {f(length)}){h} '
            f'(name "{name}" {FONT}) (number "{num}" {FONT}))')

def add_lib(lid, ref, body, pins, pin_names_hide=False, pin_numbers_hide=False,
            power=False, ref_xy=(0, 0), val_xy=(0, 0), ref_just=None, offset=0.508):
    short = lid.split(":")[1]
    hdr = f'(symbol "{lid}"' + (" (power)" if power else "")
    if pin_numbers_hide: hdr += " (pin_numbers hide)"
    hdr += f" (pin_names (offset {f(offset)})" + (" hide)" if pin_names_hide else ")")
    hdr += " (exclude_from_sim no) (in_bom yes) (on_board yes)"
    props = [prop("Reference", ref, *ref_xy, hide=power, just=ref_just),
             prop("Value", short, *val_xy, just=ref_just),
             prop("Footprint", "", hide=True), prop("Datasheet", "", hide=True),
             prop("Description", "", hide=True)]
    s = hdr + " " + " ".join(props)
    s += f' (symbol "{short}_0_1" {" ".join(body)})'
    s += f' (symbol "{short}_1_1" {" ".join(p[0] for p in pins)})'
    s += ")"
    lib[lid] = s
    pins_of[lid] = [p[1] for p in pins]

def poly(pts, w=0.254, fill="none"):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return f"(polyline (pts {p}) (stroke (width {w}) (type default)) (fill (type {fill})))"

def rect(x1, y1, x2, y2, w=0.254, fill="background"):
    return (f"(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) "
            f"(stroke (width {w}) (type default)) (fill (type {fill})))")

def arc(s, m, e, w=0.254):
    return (f"(arc (start {f(s[0])} {f(s[1])}) (mid {f(m[0])} {f(m[1])}) (end {f(e[0])} {f(e[1])}) "
            f"(stroke (width {w}) (type default)) (fill (type none)))")

def circle(cx, cy, r, w=0.254, fill="none"):
    return (f"(circle (center {f(cx)} {f(cy)}) (radius {f(r)}) "
            f"(stroke (width {w}) (type default)) (fill (type {fill})))")

def two_pin(lid, ref, body, half=3.81, plen=1.27):
    pins = [(pin_s("1", "~", 0, half, 270, plen), ("1", 0, half, "U")),
            (pin_s("2", "~", 0, -half, 90, plen), ("2", 0, -half, "D"))]
    add_lib(lid, ref, body, pins, pin_names_hide=True, pin_numbers_hide=True,
            ref_xy=(2.54, 1.27), val_xy=(2.54, -1.27), ref_just="left", offset=0)

two_pin("keeptracker:R", "R", [rect(-1.016, -2.54, 1.016, 2.54, fill="none")])
two_pin("keeptracker:C", "C", [poly([(-2.032, 0.762), (2.032, 0.762)], 0.508),
                      poly([(-2.032, -0.762), (2.032, -0.762)], 0.508)], plen=3.048)
two_pin("keeptracker:CP", "C", [rect(-2.286, 0.508, 2.286, 1.016, fill="none"),
                       rect(-2.286, -1.016, 2.286, -0.508, fill="outline"),
                       poly([(-1.778, 2.286), (-0.762, 2.286)]), poly([(-1.27, 2.794), (-1.27, 1.778)])],
        plen=2.794)
two_pin("keeptracker:L", "L", [arc((0, 2.54), (0.635, 1.905), (0, 1.27)), arc((0, 1.27), (0.635, 0.635), (0, 0)),
                      arc((0, 0), (0.635, -0.635), (0, -1.27)), arc((0, -1.27), (0.635, -1.905), (0, -2.54))])
two_pin("keeptracker:FB", "FB", [poly([(-1.778, 1.27), (0.508, 2.54), (1.778, 0.254), (-0.508, -1.016), (-1.778, 1.27)], fill="outline"),
                        poly([(0, 2.286), (0, 3.81)]), poly([(0, -3.81), (0, 0.508)])], plen=0)
# TVS bidirectionnelle (piézo, ESD RF)
two_pin("keeptracker:TVS", "D", [poly([(-1.27, 1.27), (1.27, 1.27), (0, 0), (-1.27, 1.27)]),
                        poly([(-1.27, -1.27), (1.27, -1.27), (0, 0), (-1.27, -1.27)]),
                        poly([(-1.778, 0.508), (-1.27, 0), (1.27, 0), (1.778, -0.508)])], half=3.81, plen=2.54)
# TVS / ESD unidirectionnelle : broche 1 = cathode (haut), broche 2 = anode (bas)
two_pin("keeptracker:D_TVS", "D", [poly([(-1.27, -1.016), (1.27, -1.016), (0, 1.016), (-1.27, -1.016)], fill="outline"),
                          poly([(-1.778, 1.524), (-1.27, 1.016), (1.27, 1.016), (1.778, 0.508)])], plen=2.794)
# ESD RF TPD1E0B04DPY : broche 1 = GND (bas), broche 2 = IO (haut) — conforme à l'empreinte
add_lib("keeptracker:ESD_RF", "D", [poly([(-1.27, -1.016), (1.27, -1.016), (0, 1.016), (-1.27, -1.016)], fill="outline"),
                                    poly([(-1.778, 1.524), (-1.27, 1.016), (1.27, 1.016), (1.778, 0.508)])],
        [(pin_s("2", "IO", 0, 3.81, 270, 2.794), ("2", 0, 3.81, "U")),
         (pin_s("1", "GND", 0, -3.81, 90, 2.794), ("1", 0, -3.81, "D"))],
        pin_names_hide=True, pin_numbers_hide=True, ref_xy=(2.54, 1.27), val_xy=(2.54, -1.27), ref_just="left", offset=0)
two_pin("keeptracker:Fuse", "F", [rect(-0.762, -2.54, 0.762, 2.54, fill="none"), poly([(0, -2.54), (0, 2.54)])])
two_pin("keeptracker:PTC", "F", [rect(-0.762, -2.54, 0.762, 2.54, fill="none"),
                        poly([(-1.524, -2.032), (1.524, 2.032), (2.286, 2.032)])])
two_pin("keeptracker:XTAL", "Y", [rect(-1.143, -0.762, 1.143, 0.762, fill="none"),
                         poly([(-1.778, 1.27), (1.778, 1.27)]), poly([(-1.778, -1.27), (1.778, -1.27)])], plen=2.54)

# antenna: single pin at bottom
add_lib("keeptracker:ANT", "AE", [poly([(0, 0), (0, 3.81)]), poly([(-1.905, 3.81), (0, 1.27), (1.905, 3.81), (-1.905, 3.81)])],
        [(pin_s("1", "A", 0, -2.54, 90, 2.54), ("1", 0, -2.54, "D"))],
        pin_names_hide=True, pin_numbers_hide=True, ref_xy=(2.54, 2.54), val_xy=(2.54, 0.635), ref_just="left")
# point de test et trou de fixation : une broche en bas
add_lib("keeptracker:TestPoint", "TP", [circle(0, 1.016, 1.016)],
        [(pin_s("1", "1", 0, -2.54, 90, 2.54), ("1", 0, -2.54, "D"))],
        pin_names_hide=True, pin_numbers_hide=True, ref_xy=(1.905, 1.905), val_xy=(1.905, 0), ref_just="left")
add_lib("keeptracker:MountingHole", "H", [circle(0, 2.032, 2.032), circle(0, 2.032, 1.016)],
        [(pin_s("1", "1", 0, -2.54, 90, 2.54), ("1", 0, -2.54, "D"))],
        pin_names_hide=True, pin_numbers_hide=True, ref_xy=(3.048, 2.54), val_xy=(3.048, 0.635), ref_just="left")

# power symbols
RAILS = ["+3V3", "+3V3_RF", "VSYS", "VBAT", "VBUS", "VIN_BB"]
for r in RAILS:
    add_lib(f"keeptracker:{r}", "#PWR",
            [poly([(-0.762, 1.27), (0, 2.54)]), poly([(0, 0), (0, 2.54)]), poly([(0, 2.54), (0.762, 1.27)])],
            [(pin_s("1", r, 0, 0, 90, 0, "power_in", hide=True), ("1", 0, 0, "U"))],
            pin_names_hide=True, pin_numbers_hide=True, power=True, ref_xy=(0, -3.81), val_xy=(0, 3.556), offset=0)
add_lib("keeptracker:GND", "#PWR",
        [poly([(0, 0), (0, -1.27), (1.27, -1.27), (0, -2.54), (-1.27, -1.27), (0, -1.27)])],
        [(pin_s("1", "GND", 0, 0, 270, 0, "power_in", hide=True), ("1", 0, 0, "D"))],
        pin_names_hide=True, pin_numbers_hide=True, power=True, ref_xy=(0, -6.35), val_xy=(0, -3.81), offset=0)
add_lib("keeptracker:PWR_FLAG", "#FLG",
        [poly([(0, 0), (0, 1.27), (-1.016, 1.905), (0, 2.54), (1.016, 1.905), (0, 1.27)])],
        [(pin_s("1", "pwr", 0, 0, 90, 0, "power_out"), ("1", 0, 0, "U"))],
        pin_names_hide=True, pin_numbers_hide=True, power=True, ref_xy=(0, 1.905), val_xy=(0, 3.81), offset=0)

IC_GEOM = {}  # lid -> (half_w, half_h)

def add_ic(lid, ref, left, right):
    """left/right: lists of (num, name) or None (spacer). Pins aligned from top."""
    n = max(len(left), len(right))
    lw = max([len(p[1]) for p in left if p] + [2])
    rw = max([len(p[1]) for p in right if p] + [2])
    w = math.ceil(((lw + rw) * 0.95 + 4) / 2 / 2.54) * 2.54
    top = (n - 1) * 1.27
    hh = top + 2.54
    pins, body = [], [rect(-w, -hh, w, hh, w=0.254, fill="background")]
    for side, lst in (("L", left), ("R", right)):
        for i, p in enumerate(lst):
            if not p: continue
            y = top - i * 2.54
            if side == "L":
                pins.append((pin_s(p[0], p[1], -w - 2.54, y, 0, 2.54), (p[0], -w - 2.54, y, "L")))
            else:
                pins.append((pin_s(p[0], p[1], w + 2.54, y, 180, 2.54), (p[0], w + 2.54, y, "R")))
    add_lib(lid, ref, body, pins, ref_xy=(-w, hh + 1.27), val_xy=(-w, -hh - 1.27), ref_just="left")
    IC_GEOM[lid] = (w, hh)

# ---- IC definitions — rév. C : brochages vérifiés sur les datasheets constructeur
# STM32WLE5CCU6 : DS13105 rév. 6, tableau 19 (UFQFPN48). PB9/PC4/PC5 n'existent pas en UFQFPN48.
add_ic("keeptracker:STM32WLE5CCU6", "U", [
    ("11", "VDD"), ("44", "VDD"), ("46", "VDDSMPS"), ("37", "VBAT"), ("41", "VDDA"), ("25", "VDDPA"), ("28", "VDDRF"), None,
    ("47", "VLXSMPS"), ("45", "VFBSMPS"), ("29", "VDDRF1V55"), ("24", "VR_PA"), None,
    ("18", "NRST"), ("19", "PH3-BOOT0"), None,
    ("30", "PB0-VDD_TCXO"), ("26", "OSC_IN"), ("27", "OSC_OUT"), ("39", "PC14-OSC32_IN"), ("40", "PC15-OSC32_OUT"), None,
    ("48", "VSSSMPS"), ("49", "VSS/EP")],
    [("9", "PA2/LPUART1_TX"), ("10", "PA3/LPUART1_RX"), ("31", "PB2"), ("32", "PB12"), ("17", "PA9"), None,
     ("35", "PA12/I2C2_SCL"), ("34", "PA11/I2C2_SDA"), ("7", "PA0/WKUP1"), ("1", "PB3/WKUP3"), ("2", "PB4/ADC_IN3"),
     ("3", "PB5"), ("4", "PB6"), ("5", "PB7"), None,
     ("36", "PA13/SWDIO"), ("42", "PA14/SWCLK"), None,
     ("12", "PA4"), ("13", "PA5"), ("14", "PA6"), None,
     ("23", "RFO_HP"), ("22", "RFO_LP"), ("20", "RFI_P"), ("21", "RFI_N"), None,
     ("6", "PB8"), ("8", "PA1"), ("15", "PA7"), ("16", "PA8"), ("33", "PA10"), ("38", "PC13"), ("43", "PA15")])
# XA17-G4K (Xinluda, ≡ AS179-92) : SPDT GaAs SOT-363 — 1 J3, 2 GND, 3 J2, 4 V1, 5 J1 (commun), 6 V2
add_ic("keeptracker:XA17-G4K", "U", [("1", "J3"), ("3", "J2"), None, ("4", "V1"), ("6", "V2")],
       [("5", "J1"), None, None, None, ("2", "GND")])
# MAX-M10S : UBX-20035208, tableau 10 (18 broches LCC)
add_ic("keeptracker:MAX-M10S", "U", [("8", "VCC"), ("7", "V_IO"), ("6", "V_BCKP"), None, ("11", "RF_IN"), None,
                                     ("15", "VIO_SEL"), ("14", "VCC_RF"), ("13", "LNA_EN"), None,
                                     ("1", "GND"), ("10", "GND"), ("12", "GND")],
       [("2", "TXD"), ("3", "RXD"), ("9", "RESET_N"), ("4", "TIMEPULSE"), ("5", "EXTINT"), ("18", "SAFEBOOT_N"),
        ("16", "SDA"), ("17", "SCL")])
# LIS2DW12 : LGA-12, broche 10 = VDD_IO, broche 5 = NC
add_ic("keeptracker:LIS2DW12", "U", [("9", "VDD"), ("10", "VDD_IO"), None, ("6", "GND"), ("7", "RES"), ("8", "GND"), ("5", "NC")],
       [("1", "SCL/SPC"), ("4", "SDA/SDI"), None, ("2", "CS"), ("3", "SDO/SA0"), None, ("12", "INT1"), ("11", "INT2")])
# ALD910025SALI : SAB MOSFET double (équilibrage supercondensateurs sans fuite), SOIC-8
add_ic("keeptracker:ALD910025", "U", [("8", "V+"), ("2", "GN1"), ("3", "DN1"), None, ("4", "SN1"), ("6", "GN2"), ("7", "DN2"),
                                      None, ("1", "V-"), ("5", "IC")], [])
add_ic("keeptracker:LTC3588-1", "U", [("1", "PZ1"), ("2", "PZ2"), None, ("3", "CAP"), ("4", "VIN"), ("7", "VIN2"), None, ("11", "GND")],
       [("5", "SW"), ("6", "VOUT"), None, ("8", "D1"), ("9", "D0"), None, ("10", "PGOOD")])
add_ic("keeptracker:BQ24074RGT", "U", [("13", "IN"), None, ("4", "~{CE}"), ("6", "EN1"), ("5", "EN2"), ("15", "ITERM"), None,
                              ("1", "TS"), ("12", "ILIM"), ("16", "ISET"), ("14", "TMR"), None, ("8", "VSS"), ("17", "EP")],
       [("10", "OUT"), ("11", "OUT"), None, ("2", "BAT"), ("3", "BAT"), None, ("7", "~{PGOOD}"), ("9", "~{CHG}")])
# TPS63900 : SLVSET3D, fig. 5-1 (WSON-10 DSK)
add_ic("keeptracker:TPS63900", "U", [("10", "VIN"), ("1", "EN"), None, ("9", "LX1"), None, ("3", "CFG1"), ("4", "CFG2"), ("5", "CFG3"),
                            ("2", "SEL"), None, ("8", "GND"), ("11", "EP")],
       [("6", "VOUT"), None, ("7", "LX2")])
add_ic("keeptracker:TPS22916C", "U", [("A2", "VIN"), None, ("B2", "ON"), None, ("B1", "GND")], [("A1", "VOUT")])
add_ic("keeptracker:MAX17048", "U", [("3", "VDD"), ("2", "CELL"), None, ("1", "CTG"), ("6", "QSTRT"), ("4", "GND"), ("9", "EP")],
       [("7", "SCL"), ("8", "SDA"), ("5", "~{ALRT}")])
add_ic("keeptracker:S-8261", "U", [("5", "VDD"), ("6", "VSS"), ("2", "VM")], [("1", "DO"), ("3", "CO"), ("4", "DS")])
add_ic("keeptracker:AO8814", "Q", [("2", "S1"), ("3", "S1"), ("4", "G1"), None, ("1", "D"), ("8", "D")],
       [("6", "S2"), ("7", "S2"), ("5", "G2")])
add_ic("keeptracker:LM66100", "U", [("1", "VIN"), ("3", "~{CE}"), ("2", "GND")], [("6", "VOUT"), ("4", "ST"), ("5", "NC")])
add_ic("keeptracker:TCXO_32MHz", "Y", [("4", "VCC"), ("1", "VC/NC"), ("2", "GND")], [("3", "OUT")])
add_ic("keeptracker:USB_C_Power", "J", [("A4", "VBUS"), ("A9", "VBUS"), ("B4", "VBUS"), ("B9", "VBUS"), None,
                               ("A5", "CC1"), ("B5", "CC2"), None,
                               ("A1", "GND"), ("A12", "GND"), ("B1", "GND"), ("B12", "GND"), ("S1", "SHIELD")],
       [("A6", "D+"), ("B6", "D+"), ("A7", "D-"), ("B7", "D-"), ("A8", "SBU1"), ("B8", "SBU2")])
add_ic("keeptracker:Conn_Batt_NTC", "J", [], [("1", "BAT+"), ("3", "NTC"), ("2", "BAT-"), ("MP", "MP")])
add_ic("keeptracker:Conn_Piezo", "J", [], [("1", "PIEZO+"), ("2", "PIEZO-"), ("MP", "MP")])
add_ic("keeptracker:TagConnect", "J", [], [("1", "VCC"), None, ("2", "SWDIO"), ("3", "~{RESET}"), ("4", "SWCLK"), None, ("5", "GND"), ("6", "SWO")])
add_ic("keeptracker:U.FL", "J", [], [("1", "RF"), ("2", "GND")])

# ---------------------------------------------------------------- schematic items
items = []
pwr_n = [0]
labels_used = {}
ORG = [0.0, 0.0]   # origine du bloc courant : toutes les primitives ci-dessous sont décalées de ORG

def org(x, y):
    ORG[0], ORG[1] = x, y

def wire(x1, y1, x2, y2):
    ox, oy = ORG
    items.append(f"(wire (pts (xy {f(x1 + ox)} {f(y1 + oy)}) (xy {f(x2 + ox)} {f(y2 + oy)})) "
                 f"(stroke (width 0) (type default)) (uuid {U()}))")

def junction(x, y):
    items.append(f"(junction (at {f(x + ORG[0])} {f(y + ORG[1])}) (diameter 0) (color 0 0 0 0) (uuid {U()}))")

def text(s, x, y, size=1.27, bold=False, just="left top", absolute=False):
    if not absolute:
        x, y = x + ORG[0], y + ORG[1]
    b = " bold" if bold else ""
    th = f" (thickness {f(size * 0.18)})" if bold else ""
    s = s.replace('"', '\\"').replace("\n", "\\n")
    items.append(f'(text "{s}" (exclude_from_sim no) (at {f(x)} {f(y)} 0) '
                 f'(effects (font (size {f(size)} {f(size)}){th}{b}) (justify {just})) (uuid {U()}))')

def frame(x1, y1, x2, y2, title):
    """Cadre de bloc, coordonnées absolues."""
    items.append(f"(rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) "
                 f"(stroke (width 0.35) (type dash) (color 0 72 132 1)) (fill (type none)) (uuid {U()}))")
    text(title, x1 + 2.54, y1 + 2.54, size=2.2, bold=True, absolute=True)

def place_symbol(lid, ref, value, x, y, fp="", ds="", rot=0, ref_at=None, val_at=None, hide_val=False,
                 extra=None, dnp=False):
    ox, oy = ORG
    sh = lambda a: (a[0] + ox, a[1] + oy) + tuple(a[2:])
    ref_at = sh(ref_at) if ref_at is not None else None
    val_at = sh(val_at) if val_at is not None else None
    x, y = x + ox, y + oy
    pins = pins_of[lid]
    pl = " ".join(f'(pin "{p[0]}" (uuid {U()}))' for p in pins)
    hidden_ref = ref.startswith("#")
    if ref_at is None:
        ref_at = (x, y)
    if val_at is None:
        val_at = (x, y)
    fang = 90 if rot in (90, 270) else 0
    def P(name, val, at, hide=False, just=None, ang=None):
        j = f" (justify {just})" if just else ""
        a = fang if ang is None else ang
        return (f'(property "{name}" "{val}" (at {f(at[0])} {f(at[1])} {a}) '
                f'(effects (font (size 1.27 1.27)){j}{" hide" if hide else ""}))')
    props = [P("Reference", ref, ref_at[:2], hide=hidden_ref, just=ref_at[2] if len(ref_at) > 2 else None),
             P("Value", value, val_at[:2], hide=hide_val, just=val_at[2] if len(val_at) > 2 else None),
             P("Footprint", fp, (x, y), hide=True), P("Datasheet", ds, (x, y), hide=True),
             P("Description", "", (x, y), hide=True)]
    for k, v in (extra or {}).items():
        props.append(P(k, v, (x, y), hide=True))
    items.append(f'(symbol (lib_id "{lid}") (at {f(x)} {f(y)} {rot}) (unit 1) (exclude_from_sim no) '
                 f'(in_bom {"no" if hidden_ref else "yes"}) (on_board {"no" if hidden_ref else "yes"}) '
                 f'(dnp {"yes" if dnp else "no"}) '
                 f'(uuid {U()}) {" ".join(props)} {pl} '
                 f'(instances (project "keeptracker" (path "/{ROOT}" (reference "{ref}") (unit 1)))))')

def power(net, x, y, rot=0):
    pwr_n[0] += 1
    lid = "keeptracker:GND" if net == "GND" else f"keeptracker:{net}"
    if net == "GND":
        va = (x, y + 3.81) if rot == 0 else (x, y - 3.81)
    else:
        va = (x, y - 3.556) if rot == 0 else (x, y + 3.556)
    place_symbol(lid, f"#PWR{pwr_n[0]:03d}", net, x, y, rot=rot, ref_at=(x, y), val_at=va)

flg_n = [0]
def pwr_flag(x, y):
    flg_n[0] += 1
    place_symbol("keeptracker:PWR_FLAG", f"#FLG{flg_n[0]:02d}", "PWR_FLAG", x, y, ref_at=(x, y), val_at=(x, y - 3.81))

def label(net, x, y, d):
    ang, just = {"R": (0, "left bottom"), "L": (180, "right bottom"),
                 "U": (90, "left bottom"), "D": (270, "right bottom")}[d]
    items.append(f'(label "{net}" (at {f(x + ORG[0])} {f(y + ORG[1])} {ang}) (fields_autoplaced yes) '
                 f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {U()}))')
    labels_used.setdefault(net, 0)
    labels_used[net] += 1

def no_connect(x, y):
    items.append(f"(no_connect (at {f(x + ORG[0])} {f(y + ORG[1])}) (uuid {U()}))")

DV = {"L": (-1, 0), "R": (1, 0), "U": (0, -1), "D": (0, 1)}  # schematic coords (y down)

def side_power(net, x, y, d):
    """Symbole d'alimentation orienté vers l'extérieur d'une broche latérale."""
    pwr_n[0] += 1
    lid = "keeptracker:GND" if net == "GND" else f"keeptracker:{net}"
    if net == "GND":
        rot = 270 if d == "L" else 90
    else:
        rot = 90 if d == "L" else 270
    off = (3.4 if net != "GND" else 2.9) + len(net) * 0.62
    va = (x - off, y) if d == "L" else (x + off, y)
    place_symbol(lid, f"#PWR{pwr_n[0]:03d}", net, x, y, rot=rot, ref_at=(x, y), val_at=va)

def connect_group(net, pts, d):
    """Broches consécutives d'un même côté sur le même net : un seul bus, un seul symbole/label."""
    if len(pts) == 1 or net == "NC":
        for ex, ey in pts:
            connect(net, ex, ey, d)
        return
    dx = -1 if d == "L" else 1
    xe = pts[0][0] + dx * 2.54
    for ex, ey in pts:
        wire(ex, ey, xe, ey)
    ys = [p[1] for p in pts]
    for ya, yb in zip(ys, ys[1:]):
        wire(xe, ya, xe, yb)
    for y in ys[:-1]:
        junction(xe, y)
    connect(net, xe, ys[0], d, stub=2.54)

def connect(net, ex, ey, d, stub=5.08):
    if net is None:
        return
    if net == "NC":
        no_connect(ex, ey); return
    dx, dy = DV[d]
    if net == "GND" or net in RAILS:
        if d in ("L", "R"):
            sx, sy = ex + dx * 2.54, ey
            wire(ex, ey, sx, sy)
            side_power(net, sx, sy, d)
        elif net == "GND":
            if d == "D":
                power(net, ex, ey)
            else:
                wire(ex, ey, ex, ey - 2.54); power(net, ex, ey - 2.54, rot=180)
        else:
            if d == "U":
                power(net, ex, ey)
            else:
                wire(ex, ey, ex, ey + 2.54); power(net, ex, ey + 2.54, rot=180)
        return
    st = stub if d in ("L", "R") else 2.54
    sx, sy = ex + dx * st, ey + dy * st
    wire(ex, ey, sx, sy)
    label(net, sx, sy, d)

def ic(lid, ref, value, x, y, nets, fp="", ds="", mpn=None, dnp=False):
    w, hh = IC_GEOM[lid]
    place_symbol(lid, ref, value, x, y, fp=fp, ds=ds,
                 ref_at=(x - w, y - hh - 1.27, "left bottom"), val_at=(x - w, y + hh + 1.27, "left top"),
                 extra={"MPN": mpn} if mpn else None, dnp=dnp)
    groups, prev = [], None
    for num, px, py, d in pins_of[lid]:
        net = nets.get(num)
        pt = (x + px, y - py)
        if prev and prev[0] == net and prev[2] == d and net != "NC" and abs(prev[3] - py) < 2.6:
            prev[1].append(pt); prev[3] = py
        else:
            prev = [net, [pt], d, py]; groups.append(prev)
    for net, pts, d, _ in groups:
        connect_group(net, pts, d)
    missing = [p[0] for p in pins_of[lid] if p[0] not in nets]
    if missing:
        raise SystemExit(f"{ref}: broches non affectées {missing}")

def two(lid, ref, value, x, y, top, bot, fp="", mpn=None, dnp=False):
    """Composant 2 broches vertical : broche 1 en haut, broche 2 en bas."""
    place_symbol(lid, ref, value, x, y, fp=fp, ref_at=(x + 2.54, y - 1.27, "left"), val_at=(x + 2.54, y + 1.27, "left"),
                 extra={"MPN": mpn} if mpn else None, dnp=dnp)
    pins = pins_of[lid]
    _, px, py, d = pins[0]; connect(top, x + px, y - py, d)
    if len(pins) > 1:
        _, px, py, d = pins[1]; connect(bot, x + px, y - py, d)

def one(lid, ref, value, x, y, net, fp="", mpn=None):
    """Symbole à une broche (point de test, trou de fixation, antenne), broche vers le bas."""
    place_symbol(lid, ref, value, x, y, fp=fp, ref_at=(x + 2.54, y - 1.905, "left"), val_at=(x + 2.54, y + 0.635, "left"),
                 extra={"MPN": mpn} if mpn else None)
    _, px, py, d = pins_of[lid][0]
    connect(net, x + px, y - py, d)

def hpart(lid, ref, value, x, y, fp="", mpn=None, dnp=False):
    """Composant 2 broches horizontal (rot 90) : broche 1 à gauche, broche 2 à droite."""
    place_symbol(lid, ref, value, x, y, fp=fp, rot=90, ref_at=(x, y - 3.302), val_at=(x, y + 3.302),
                 extra={"MPN": mpn} if mpn else None, dnp=dnp)
    half = [p for p in pins_of[lid] if p[0] == "1"][0][2]
    return (x - half, y), (x + half, y)

def chain(x0, y, parts, nodes, pitch=17.78):
    """Chaîne série horizontale câblée.
    parts : n × dict(lid, ref, val, fp, mpn, dnp) ; nodes : n+1 × (net|None, [shunts])
    shunt : dict(lid, ref, val, fp, bot, mpn, dnp) — composant vertical vers 'bot' sous le nœud."""
    pins = [hpart(p["lid"], p["ref"], p["val"], x0 + i * pitch, y, p.get("fp", ""), p.get("mpn"), p.get("dnp", False))
            for i, p in enumerate(parts)]

    def shunt(xs, s):
        wire(xs, y, xs, y + 5.08)
        junction(xs, y)
        two(s["lid"], s["ref"], s["val"], xs, y + 8.89, None, s["bot"], fp=s.get("fp", ""), mpn=s.get("mpn"),
            dnp=s.get("dnp", False))

    for k, (net, shunts) in enumerate(nodes):
        if k in (0, len(parts)):                       # extrémités
            sgn = -1 if k == 0 else 1
            xp = pins[0][0][0] if k == 0 else pins[-1][1][0]
            xs = [xp + sgn * (7.62 + 15.24 * i) for i in range(len(shunts))]
            xe = xs[-1] if xs else xp
            for xa, xb in zip([xp] + xs, xs):          # un segment par prise (pas de T en milieu de fil)
                wire(xa, y, xb, y)
            for xi, s in zip(xs, shunts):
                shunt(xi, s)
            connect(net, xe, y, "L" if k == 0 else "R")
        else:                                          # nœud intermédiaire
            xa, xb = pins[k - 1][1][0], pins[k][0][0]
            xm = round((xa + xb) / 2 / G) * G
            if shunts:
                wire(xa, y, xm, y); wire(xm, y, xb, y)
                shunt(xm, shunts[0])
            else:
                wire(xa, y, xb, y)
            if net:
                label(net, xa + 1.27, y, "R")

def P(lid, ref, val, fp="", mpn=None, dnp=False):
    return dict(lid=lid, ref=ref, val=val, fp=fp, mpn=mpn, dnp=dnp)

def S(lid, ref, val, bot="GND", fp="", mpn=None, dnp=False):
    return dict(lid=lid, ref=ref, val=val, bot=bot, fp=fp, mpn=mpn, dnp=dnp)

R0603 = "Resistor_SMD:R_0603_1608Metric"
R0402 = "Resistor_SMD:R_0402_1005Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
FB0603 = "Inductor_SMD:L_0603_1608Metric"
FB0402 = "Inductor_SMD:L_0402_1005Metric"

def R(ref, val, x, y, top, bot, fp=R0603, mpn=None, dnp=False):
    two("keeptracker:R", ref, val, x, y, top, bot, fp, mpn, dnp)
def C(ref, val, x, y, top, bot, fp=C0402, mpn=None, dnp=False):
    two("keeptracker:C", ref, val, x, y, top, bot, fp, mpn, dnp)

# Convention de valeurs : capacité + tension nominale ; diélectrique X7R ≤ 100 nF, X5R au-delà, C0G ≤ 1 nF.

# =========================================================== BLOC A : USB-C + chargeur
frame(12.7, 15.24, 262.89, 154.94, "A · Entrée USB-C protégée et chargeur Li-ion (BQ24074)")
org(0, 0)
ic("keeptracker:USB_C_Power", "J1", "USB4105-GF-A", 40.64, 60.96,
   {"A4": "VBUS_IN", "A9": "VBUS_IN", "B4": "VBUS_IN", "B9": "VBUS_IN", "A5": "USB_CC1", "B5": "USB_CC2",
    "A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "S1": "USB_SHIELD",
    "A6": "NC", "B6": "NC", "A7": "NC", "B7": "NC", "A8": "NC", "B8": "NC"},
   fp="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", mpn="GCT USB4105-GF-A")
# chaîne de protection d'entrée : TVS → PTC → ferrite → IN chargeur
chain(83.82, 35.56,
      [P("keeptracker:PTC", "F1", "PTC 1,5A", "Fuse:Fuse_1206_3216Metric", "Bourns MF-MSMF150-2"),
       P("keeptracker:FB", "FB2", "120Ω@100MHz 3A", FB0603, "Murata BLM18SG121TN1D")],
      [("VBUS_IN", [S("keeptracker:D_TVS", "D1", "SMF5.0A", fp="Diode_SMD:D_SOD-123F", mpn="Littelfuse SMF5.0A")]),
       (None, []),
       ("VBUS", [])])
text("Protection d'entrée", 76.2, 22.86, size=1.27, bold=True)
R("R1", "5,1k 1%", 22.86, 100.33, "USB_CC1", "GND")
two("keeptracker:D_TVS", "D3", "ESD 5V", 35.56, 100.33, "USB_CC1", "GND", fp="Diode_SMD:D_SOD-923", mpn="onsemi ESD9B5.0ST5G")
R("R2", "5,1k 1%", 48.26, 100.33, "USB_CC2", "GND")
two("keeptracker:D_TVS", "D4", "ESD 5V", 60.96, 100.33, "USB_CC2", "GND", fp="Diode_SMD:D_SOD-923", mpn="onsemi ESD9B5.0ST5G")
R("R23", "1M", 73.66, 100.33, "USB_SHIELD", "GND")
C("C31", "4,7nF 50V", 86.36, 100.33, "USB_SHIELD", "GND")
ic("keeptracker:BQ24074RGT", "U1", "BQ24074RGTR", 132.08, 63.5,
   {"13": "VBUS", "4": "GND", "6": "GND", "5": "VSYS", "15": "BQ_ITERM", "1": "BQ_TS", "12": "BQ_ILIM",
    "16": "BQ_ISET", "14": "BQ_TMR", "8": "GND", "17": "GND",
    "10": "VSYS", "11": "VSYS", "2": "VBAT", "3": "VBAT", "7": "PG_N", "9": "CHG_N"},
   fp="Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm", ds="https://www.ti.com/lit/ds/symlink/bq24074.pdf",
   mpn="TI BQ24074RGTR")
R("R3", "10k", 101.6, 110.49, "BQ_TS", "GND", dnp=True)
R("R4", "1,18k 1%", 114.3, 110.49, "BQ_ILIM", "GND")
R("R5", "1,5k 1%", 127.0, 110.49, "BQ_ISET", "GND")
R("R6", "46,4k 1%", 139.7, 110.49, "BQ_TMR", "GND")
C("C1", "1µF 25V", 152.4, 100.33, "VBUS", "GND", fp=C0603)
C("C32", "100nF 25V", 167.64, 100.33, "VBUS", "GND")
C("C2", "10µF 10V", 182.88, 100.33, "VSYS", "GND", fp=C0805)
C("C33", "100nF 16V", 198.12, 100.33, "VSYS", "GND")
C("C3", "4,7µF 10V", 213.36, 100.33, "VBAT", "GND", fp=C0603)
C("C54", "100nF 16V", 228.6, 100.33, "VBAT", "GND")
R("R33", "3,01k 1%", 243.84, 100.33, "BQ_ITERM", "GND")
text("Découplage IN / OUT / BAT au plus près des broches du BQ24074", 152.4, 86.36, size=1.0)
text("D1 : TVS 5 V (VBR 6,4 V) avant le PTC · F1 : PTC 1,5 A (≥ ILIM) · FB2 : ferrite 3 A / RDC 25 mΩ · D3/D4 : ESD CC1/CC2\n"
     "Blindage USB relié à GND par R23 // C31 (1 MΩ // 4,7 nF) : écoule l'ESD sans boucle de masse.\n"
     "TS relié à la NTC 10 k de la cellule (J2) : charge suspendue hors 0–45 °C. R3 (10 k fixe) = DNP, uniquement si cellule sans NTC.\n"
     "R4 : ILIM = 1550/1,18k ≈ 1,3 A · R5 : ICHG = 890/1,5k ≈ 0,59 A (0,3 C) · R6 : timers 46,4 k (plage 18–72 k).\n"
     "R33 : ITERM = 0,03 × 3,01k / 1,5k = 60 mA (rév. B : ITERM à GND ⇒ courant de fin de charge nul, charge jamais terminée).\n"
     "BQ24074 : OVP 10,5 V, VOUT(REG) 4,4 V, IBAT(PDWN) ≤ 6,5 µA sans USB · EN2 = 1 / EN1 = 0 ⇒ limite d'entrée par ILIM.",
     22.86, 124.46, size=1.0)

# =========================================================== BLOC B : batterie, protection, jauge
frame(266.7, 15.24, 515.62, 154.94, "B · Batterie Li-ion 1S, protection, fusible et jauge")
org(60.96, 0)
ic("keeptracker:Conn_Batt_NTC", "J2", "Cellule Li-ion 2000 mAh + NTC", 220.98, 40.64,
   {"1": "BAT_P", "3": "BQ_TS", "2": "BATN", "MP": "NC"},
   fp="Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal", mpn="JST S3B-PH-SM4-TB")
ic("keeptracker:S-8261", "U2", "S-8261ABJMD-G3J2G", 271.78, 45.72,
   {"5": "PROT_VDD", "6": "BATN", "2": "PROT_VM", "1": "PROT_DO", "3": "PROT_CO", "4": "NC"},
   fp="Package_TO_SOT_SMD:SOT-23-6", mpn="ABLIC S-8261ABJMD-G3J2G")
R("R7", "470", 228.6, 73.66, "VBAT", "PROT_VDD")
C("C4", "100nF 16V", 241.3, 73.66, "PROT_VDD", "BATN")
R("R8", "2k", 256.54, 73.66, "PROT_VM", "GND")
ic("keeptracker:AO8814", "Q1", "AO8814", 347.98, 45.72,
   {"2": "BATN", "3": "BATN", "4": "PROT_DO", "1": "Q1_D", "8": "Q1_D", "6": "GND", "7": "GND", "5": "PROT_CO"},
   fp="Package_SO:TSSOP-8_4.4x3mm_P0.65mm", mpn="AOS AO8814")
ic("keeptracker:MAX17048", "U3", "MAX17048G+T10", 271.78, 101.6,
   {"3": "VBAT", "2": "VBAT", "1": "GND", "6": "GND", "4": "GND", "9": "GND",
    "7": "I2C_SCL", "8": "I2C_SDA", "5": "GAUGE_ALRT"},
   fp="Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm", mpn="Maxim MAX17048G+T10")
C("C5", "1µF 10V", 327.66, 101.6, "VBAT", "GND")
C("C34", "100nF 16V", 342.9, 101.6, "VBAT", "BATN")
# fusible secondaire en série avec le pôle + de la cellule
chain(228.6, 139.7,
      [P("keeptracker:Fuse", "F2", "3A rapide", "Fuse:Fuse_0603_1608Metric", "Littelfuse 0467003.NR")],
      [("BAT_P", []), ("VBAT", [])])
text("F2 : fusible secondaire 3 A (court-circuit franc,\ndéfaillance du MOSFET de protection).", 251.46, 136.52, size=1.0)
text("Protection côté négatif : BATN = pôle − cellule,\nGND = masse système après MOSFET dos-à-dos.\n"
     "R7 = 470 Ω / C4 = 100 nF / R8 = 2 kΩ : valeurs typ. datasheet S-8261.\n"
     "Q1 : RDS(on) < 2 × 20 mΩ à VGS 3,6 V ⇒ 4 mW perdus à 300 mA.\nC34 au plus près du connecteur cellule.",
     312.42, 116.84, size=1.0)

# =========================================================== BLOC C : 3,3 V + rail RF
frame(520.7, 15.24, 826.77, 154.94, "C · Buck-boost 3,3 V (TPS63900, IQ 75 nA) et rail RF filtré")
org(124.46, 0)
ic("keeptracker:TPS63900", "U4", "TPS63900DSKR", 459.74, 55.88,
   {"10": "VIN_BB", "1": "VIN_BB", "9": "LX1", "3": "CFG1", "4": "CFG2", "5": "CFG3", "2": "GND",
    "8": "GND", "11": "GND", "6": "+3V3", "7": "LX2"},
   fp="Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm", ds="https://www.ti.com/lit/ds/symlink/tps63900.pdf",
   mpn="TI TPS63900DSKR")
two("keeptracker:L", "L1", "2,2µH Isat 3,3A", 511.81, 55.88, "LX1", "LX2", fp="Inductor_SMD:L_1008_2520Metric",
    mpn="Murata DFE252012F-2R2M")
C("C6", "10µF 10V", 416.56, 101.6, "VIN_BB", "GND", fp=C0805)
C("C35", "100nF 16V", 431.8, 101.6, "VIN_BB", "GND")
R("R9", "36,5k 1%", 447.04, 101.6, "CFG1", "GND", fp=R0402)
R("R10", "0Ω", 459.74, 101.6, "CFG2", "GND", fp=R0402)
R("R11", "16,2k 1%", 472.44, 101.6, "CFG3", "GND", fp=R0402)
C("C7", "22µF 10V", 535.94, 101.6, "+3V3", "GND", fp=C0805)
C("C8", "22µF 10V", 551.18, 101.6, "+3V3", "GND", fp=C0805)
C("C36", "100nF 16V", 566.42, 101.6, "+3V3", "GND")
text("SEL = 0 ⇒ VO(1) fixé par CFG3 : R11 = 16,2 k ⇒ 3,3 V. CFG1/CFG2 : R9 = 36,5 k, R10 = 0 Ω ⇒ VO(2) = 3,3 V,\n"
     "limite d'entrée « unlimited » (pics TX +22 dBm). Résistances 1 %, ≤ 200 ppm/°C (lues une seule fois au démarrage).\n"
     "L1 DFE252012F-2R2M (2520) : ISAT 3,3 A ≥ 2 A exigés en « unlimited », Itemp 2,3 A, RDC 82 mΩ max.\n"
     "C6 / C7-C8 : boucles d'entrée et de sortie les plus courtes possibles (courant pulsé).\n"
     "Capacité effective 22 µF/0805 à 3,3 V ≈ 50 % (polarisation DC) : 2 × 22 µF nécessaires.",
     416.56, 116.84, size=1.0)
# rail RF : isolé du découpage par ferrite faible RDC, réservoir local pour les pics TX +22 dBm
chain(607.06, 76.2,
      [P("keeptracker:FB", "FB3", "220Ω@100MHz", FB0603, "Murata BLM18PG221SN1D")],
      [("+3V3", []),
       ("+3V3_RF", [S("keeptracker:C", "C37", "10µF 10V", fp=C0805),
                    S("keeptracker:C", "C38", "100nF 16V", fp=C0402)])])
text("Rail +3V3_RF (VDDPA, VDDRF, front-end)", 596.9, 63.5, size=1.27, bold=True)
text("FB3 : 220 Ω @ 100 MHz, RDC ≤ 0,1 Ω, 1,4 A —\nchute < 15 mV à 120 mA (TX +22 dBm).", 596.9, 101.6, size=1.0)
for i, net in enumerate(["VBUS", "VSYS", "VBAT", "VIN_BB", "+3V3", "+3V3_RF", "GND"]):
    x = 518.16 + i * 12.7; y = 30.48 if net != "GND" else 33.02
    pwr_flag(x, y)
    if net == "GND":
        power("GND", x, y)
    else:
        wire(x, y, x, y + 2.54); power(net, x, y + 2.54, rot=180)

# =========================================================== BLOC D : piézo
frame(12.7, 160.02, 347.98, 294.64, "D · Récupération d'énergie piézoélectrique (LTC3588-1 + supercondensateurs)")
org(0, 25.4)
ic("keeptracker:Conn_Piezo", "J3", "Transducteur piézo externe", 22.86, 167.64, {"1": "PIEZO_P", "2": "PIEZO_N", "MP": "NC"},
   fp="Connector_JST:JST_ZH_B2B-ZR-SM4-TF_1x02-1MP_P1.50mm_Vertical", mpn="JST B2B-ZR-SM4-TF")
two("keeptracker:TVS", "D2", "SMAJ24CA", 60.96, 167.64, "PIEZO_P", "PIEZO_N", fp="Diode_SMD:D_SMA", mpn="Littelfuse SMAJ24CA")
R("R12", "1k anti-surge", 76.2, 167.64, "PIEZO_P", "PZ1", fp=R1206, mpn="Panasonic ERJ-P08J102V")
R("R13", "1k anti-surge", 96.52, 167.64, "PIEZO_N", "PZ2", fp=R1206, mpn="Panasonic ERJ-P08J102V")
ic("keeptracker:LTC3588-1", "U5", "LTC3588EDD-1", 165.1, 172.72,
   {"1": "PZ1", "2": "PZ2", "3": "LTC_CAP", "4": "LTC_VIN", "7": "LTC_VIN2", "11": "GND",
    "5": "LTC_SW", "6": "VPZ", "8": "LTC_VIN2", "9": "LTC_VIN2", "10": "PZ_PGOOD"},
   fp="Package_DFN_QFN:DFN-10-1EP_3x3mm_P0.5mm_EP1.65x2.38mm", ds="https://www.analog.com/media/en/technical-documentation/data-sheets/35881fc.pdf",
   mpn="ADI LTC3588EDD-1")
C("C9", "22µF 25V", 124.46, 223.52, "LTC_VIN", "GND", fp=C1206)
C("C10", "1µF 10V", 142.24, 223.52, "LTC_VIN", "LTC_CAP", fp=C0603)
C("C11", "4,7µF 10V", 160.02, 223.52, "LTC_VIN2", "GND", fp=C0603)
two("keeptracker:L", "L2", "22µH Isat≥350mA", 213.36, 172.72, "LTC_SW", "VPZ", fp="Inductor_SMD:L_1210_3225Metric",
    mpn="Murata LQH32PH220MN0")
C("C12", "47µF 6,3V", 223.52, 215.9, "VPZ", "GND", fp=C1206)
two("keeptracker:CP", "SC1", "10F 2,7V", 248.92, 205.74, "VPZ", None, fp="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
    mpn="Eaton HV0830-2R7106-R")
two("keeptracker:CP", "SC2", "10F 2,7V", 248.92, 213.36, None, "GND", fp="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
    mpn="Eaton HV0830-2R7106-R")
R("R14", "1M", 271.78, 205.74, "VPZ", None, dnp=True)
R("R15", "1M", 271.78, 213.36, None, "GND", dnp=True)
ic("keeptracker:ALD910025", "U12", "ALD910025SALI", 254.0, 248.92,
   {"8": "VPZ", "2": "VPZ", "3": "VPZ", "4": "SC_MID", "6": "SC_MID", "7": "SC_MID", "1": "GND", "5": "GND"},
   fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", mpn="ALD910025SALI")
wire(248.92, 209.55, 271.78, 209.55); junction(248.92, 209.55); junction(271.78, 209.55)
label("SC_MID", 254.0, 209.55, "R"); labels_used["SC_MID"] += 1
# surveillance : PGOOD (référé à VOUT = 3,6 V) limité en courant, mesure VPZ haute impédance
text("Surveillance VPZ / PGOOD", 287.02, 147.32, size=1.27, bold=True)
R("R28", "100k", 292.1, 167.64, "PZ_PGOOD", "PZ_PGOOD_MCU")
R("R25", "10M 1%", 309.88, 167.64, "VPZ", "VPZ_SENSE")
R("R26", "10M 1%", 309.88, 203.2, "VPZ_SENSE", "GND")
C("C40", "100nF 16V", 325.12, 203.2, "VPZ_SENSE", "GND")
text("Pont 10 M / 10 M : 0,18 µA ; C40 fournit\nla charge d'échantillonnage de l'ADC.", 287.02, 222.25, size=1.0)
text("D2 : TVS bidirectionnelle 24 V à l'entrée (chocs, ESD câble). R12/R13 1 kΩ anti-surge : limitent le courant dans le shunt 20 V\n"
     "interne du LTC3588 sans pénaliser la récupération (chute < 0,1 V à 100 µA). D1 = D0 = VIN2 → VOUT = 3,6 V.\n"
     "2 supercondensateurs 2,7 V en série (1,8 V chacun). Équilibrage U12 ALD910025 (SAB MOSFET, seuil 2,50 V) : ≈ 0 A à 1,8 V/cellule,\n"
     "contre 1,8 µA perdus en permanence dans R14/R15 (2 MΩ, rév. B → DNP). Gain ≈ 57 µAh/an… et surtout la récolte n'est plus gaspillée.\n"
     "Valeurs TVS / R à confirmer après mesure Voc, fréquence et puissance du piézo sur véhicule.",
     22.86, 236.22, size=1.0)

# =========================================================== BLOC E : diode idéale
frame(353.06, 160.02, 500.38, 294.64, "E · OR-ing des sources (2 × LM66100, RCB)")
org(50.8, 25.4)
ic("keeptracker:LM66100", "U6", "LM66100DCKR", 365.76, 175.26,
   {"1": "VPZ", "3": "VIN_BB", "2": "GND", "6": "VIN_BB", "4": "GND", "5": "NC"},
   fp="Package_TO_SOT_SMD:SOT-363_SC-70-6", ds="https://www.ti.com/lit/ds/symlink/lm66100.pdf", mpn="TI LM66100DCKR")
ic("keeptracker:LM66100", "U11", "LM66100DCKR", 365.76, 152.4,
   {"1": "VSYS", "3": "VIN_BB", "2": "GND", "6": "VIN_BB", "4": "GND", "5": "NC"},
   fp="Package_TO_SOT_SMD:SOT-363_SC-70-6", ds="https://www.ti.com/lit/ds/symlink/lm66100.pdf", mpn="TI LM66100DCKR")
C("C13", "1µF 10V", 330.2, 208.28, "VPZ", "GND")
C("C42", "1µF 10V", 345.44, 208.28, "VIN_BB", "GND")
text("U6 (VPZ) et U11 (VSYS) en OR-ing vers VIN_BB : la source\nla plus haute alimente le buck-boost.\n"
     "CE relié à VOUT = blocage permanent du courant inverse\n(RCB, datasheet §8.3.2). Rév. B : CE à GND ⇒ interrupteur\n"
     "toujours passant, la batterie se vidait dans les supercaps.\n"
     "Le piézo ne charge plus jamais la cellule via le BATFET\n(contrôle NTC/TS du BQ24074 respecté).\n"
     "RON 79 mΩ ⇒ 9 mV à 110 mA · IQ 150 nA chacun · ST → GND.",
     312.42, 228.6, size=1.1)

# =========================================================== BLOC F : notes
frame(505.46, 160.02, 826.77, 294.64, "F · Notes de conception")
org(0, 0)
text("Généralités", 510.54, 170.18, size=1.5, bold=True, absolute=True)
text("1. Rév. C : brochages vérifiés sur datasheets (DS13105, SLVSET3D, SLUS810N,\n"
     "    UBX-20035208, LTC3588, MAX17048, XA17-G4K). Empreintes projet : keeptracker.pretty.\n"
     "2. LoRaWAN EU868 (863–870 MHz) : vérifier la bande applicable au Maroc (ANRT).\n"
     "3. Réseau RF STM32WL (MN1) : reprendre la référence ST (AN5457 / Nucleo-WL55JC),\n"
     "    filtre harmonique, lignes 50 Ω, adaptation en Pi validée au VNA.\n"
     "4. PCB 4 couches (SIG / GND / PWR / SIG), plan de masse continu sous radio et GNSS,\n"
     "    vias de couture tous les ≈ 3 mm le long des pistes RF et du bord de carte.\n"
     "5. Antenne LoRa en bord de carte avec keepout ; antenne GNSS éloignée de la LoRa,\n"
     "    du LTC3588 et des convertisseurs à découpage (TPS63900, LTC3588).\n"
     "6. Séquence : veille (LIS2DW12 seul actif) → INT1 réveille le MCU → GNSS ON →\n"
     "    fix → trame START/STOP (position, batterie, qualité GNSS) → veille.\n"
     "7. GNSS_EN tiré à la masse : GNSS coupé par défaut (TPS22916C, décharge rapide).\n"
     "8. Firmware : GNSS coupé ⇒ PA2 / PA3 / PB2 en mode analogique (pas de\n"
     "    rétro-alimentation du module par les E/S). LPUART1 : réception en Stop2.\n"
     "9. Réveils : ACC_INT → PA0/WKUP1, GAUGE_ALRT → PB3/WKUP3 (Standby possible).",
     510.54, 175.26, size=1.3, absolute=True)
text("Filtrage, découplage et robustesse (rév. B)", 668.02, 170.18, size=1.5, bold=True, absolute=True)
text("• Condensateurs : tension nominale ≥ 2 × tension de service ; X7R ≤ 100 nF,\n"
     "   X5R au-delà, C0G pour 47 pF / 6,8 pF. Prévoir −50 % (polarisation DC) sur 10–22 µF.\n"
     "• Découplage : 1 × 100 nF par broche d'alimentation à < 2 mm, via direct vers GND ;\n"
     "   réservoir 4,7–10 µF par rail ; 47 pF C0G (résonance ≈ 868 MHz) sur VDDPA,\n"
     "   VDDRF et VCC GNSS pour court-circuiter les résidus RF.\n"
     "• Rails séparés : +3V3 (numérique) · +3V3_RF (FB3) · VDDA (FB1) · GNSS_VCC (FB4).\n"
     "   Ferrites RDC ≤ 0,1 Ω pour ne pas créer de chute en émission.\n"
     "• Entrée USB : TVS + PTC + ferrite ; ESD sur CC1/CC2 ; blindage via 1 MΩ // 4,7 nF.\n"
     "• Batterie : fusible 3 A + protection S-8261 / AO8814 + NTC sur TS.\n"
     "• Piézo : TVS 24 V + 2 × 1 kΩ anti-surge en amont du LTC3588.\n"
     "• RF : ESD ≤ 0,2 pF sur les deux antennes ; Pi (NM / 0 Ω / NM) devant RF_IN GNSS.\n"
     "• Signaux : PGOOD via 100 kΩ, UART GNSS via 1 kΩ, pull-up 100 kΩ sur ALRT/PG/CHG\n"
     "   (alerte jauge active = 33 µA au lieu de 330 µA prélevés sur la batterie).\n"
     "• Deux-roues : passifs AEC-Q200 de préférence, ≥ 1 µF en 0603 minimum (fissuration\n"
     "   par vibration), vernis de tropicalisation, supercondensateurs collés/brisés.",
     668.02, 175.26, size=1.3, absolute=True)

# =========================================================== BLOC G : MCU + LoRa
frame(12.7, 299.72, 457.2, 482.6, "G · Microcontrôleur STM32WLE5 et radio LoRa 868 MHz")
org(0, 45.72)
ic("keeptracker:STM32WLE5CCU6", "U7", "STM32WLE5CCU6", 109.22, 326.39,
   {"11": "+3V3", "44": "+3V3", "46": "+3V3", "37": "+3V3", "41": "VDDA", "25": "+3V3_RF", "28": "+3V3_RF",
    "47": "VLXSMPS", "45": "VFBSMPS", "29": "VFBSMPS", "24": "VR_PA", "18": "NRST", "19": "BOOT0",
    "30": "VDD_TCXO", "26": "HSE_IN", "27": "NC", "39": "OSC32_IN", "40": "OSC32_OUT", "48": "GND", "49": "GND",
    "9": "GNSS_RX", "10": "GNSS_TX", "31": "GNSS_RST", "32": "GNSS_EN", "17": "GNSS_BCKP_IO",
    "35": "I2C_SCL", "34": "I2C_SDA", "7": "ACC_INT", "1": "GAUGE_ALRT", "2": "VPZ_SENSE",
    "3": "PZ_PGOOD_MCU", "4": "CHG_N", "5": "PG_N", "36": "SWDIO", "42": "SWCLK",
    "12": "FE_CTRL1", "13": "FE_CTRL2", "14": "NC",
    "23": "RFO_HP", "22": "RFO_LP", "20": "RFI_P", "21": "RFI_N",
    "6": "NC", "8": "NC", "15": "NC", "16": "NC", "33": "NC", "38": "NC", "43": "NC"},
   fp="Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.3x5.3mm", ds="https://www.st.com/resource/en/datasheet/stm32wle5cc.pdf",
   mpn="ST STM32WLE5CCU6")
# découplage numérique / analogique / SMPS
text("Découplage VDD (11, 44) · VBAT (37) · VDDSMPS · VDDA · SMPS 1,55 V : VFBSMPS = VDDRF1V55, Cout = 470 nF (DS13105)", 20.32, 378.46, size=1.0, bold=True)
C("C14", "100nF 16V", 22.86, 397.51, "+3V3", "GND")
C("C15", "100nF 16V", 38.1, 397.51, "+3V3", "GND")
C("C16", "4,7µF 10V", 53.34, 397.51, "+3V3", "GND", fp=C0603)
C("C18", "10µF 10V", 68.58, 397.51, "+3V3", "GND", fp=C0805)
two("keeptracker:FB", "FB1", "600Ω@100MHz", 83.82, 397.51, "+3V3", "VDDA", fp=FB0603, mpn="Murata BLM18KG601SN1D")
C("C19", "1µF 10V", 106.68, 397.51, "VDDA", "GND")
C("C20", "100nF 16V", 121.92, 397.51, "VDDA", "GND")
two("keeptracker:L", "L3", "15µH", 137.16, 397.51, "VLXSMPS", "VFBSMPS", fp="Inductor_SMD:L_0805_2012Metric",
    mpn="Murata LQM21PN150MC0")
C("C21", "470nF 10V", 152.4, 397.51, "VFBSMPS", "GND")
C("C47", "100nF 16V", 167.64, 397.51, "+3V3", "GND")
C("C23", "100nF 16V", 182.88, 397.51, "VDD_TCXO", "GND")
C("C58", "100nF 16V", 198.12, 397.51, "+3V3", "GND")
# TCXO → OSC_IN : 220 Ω série + 10 pF série (diviseur capacitif, 0,4–0,5 Vpp sur OSC_IN — DS13105 tab. 58)
chain(167.64, 421.64,
      [P("keeptracker:R", "R42", "220 1%", R0402),
       P("keeptracker:C", "C55", "10pF C0G", C0402)],
      [("TCXO_OUT", []), (None, []), ("HSE_IN", [])])
text("TCXO → 220 Ω + 10 pF → OSC_IN : amplitude ramenée à 0,4–0,5 Vpp\n(limite l'injection de raies parasites dans la radio).", 147.32, 429.26, size=1.0)
# découplage RF
text("Découplage RF (+3V3_RF) — VDDPA : 4,7 µF + 100 nF + 47 pF · VDDRF : 100 nF + 47 pF", 20.32, 411.48, size=1.0, bold=True)
C("C17", "100nF 16V", 22.86, 425.45, "+3V3_RF", "GND")
C("C43", "47pF C0G", 38.1, 425.45, "+3V3_RF", "GND")
C("C44", "100nF 16V", 53.34, 425.45, "+3V3_RF", "GND")
C("C45", "47pF C0G", 68.58, 425.45, "+3V3_RF", "GND")
C("C46", "4,7µF 10V", 83.82, 425.45, "+3V3_RF", "GND", fp=C0603)
R("R16", "10k", 22.86, 276.86, "+3V3", "NRST", dnp=True)
C("C22", "100nF 16V", 33.02, 276.86, "NRST", "GND")
R("R17", "100k", 48.26, 276.86, "BOOT0", "GND")
ic("keeptracker:TCXO_32MHz", "Y1", "TCXO 32 MHz", 215.9, 383.54,
   {"4": "VDD_TCXO", "1": "NC", "2": "GND", "3": "TCXO_OUT"},
   fp="Oscillator:Oscillator_SMD_SiT_PQFN-4Pin_2.0x1.6mm")
two("keeptracker:XTAL", "Y2", "32,768 kHz", 246.38, 397.51, "OSC32_IN", "OSC32_OUT", fp="Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm")
C("C24", "6,8pF C0G", 261.62, 397.51, "OSC32_IN", "GND")
C("C25", "6,8pF C0G", 276.86, 397.51, "OSC32_OUT", "GND")
# pull-ups
R("R18", "4,7k", 177.8, 276.86, "+3V3", "I2C_SCL")
R("R19", "4,7k", 187.96, 276.86, "+3V3", "I2C_SDA")
R("R20", "100k", 198.12, 276.86, "+3V3", "PG_N")
R("R21", "100k", 208.28, 276.86, "+3V3", "CHG_N")
R("R22", "100k", 218.44, 276.86, "GNSS_EN", "GND")
R("R24", "100k", 228.6, 276.86, "+3V3", "GAUGE_ALRT")
# front-end RF
# front-end RF 868 MHz discret — topologie et valeurs de la carte Olimex BB-STM32WL rév. D1
# (STM32WLE5CCU6 UFQFPN48, PA haute puissance validé 868/915 MHz) ; accord final au VNA sur notre PCB.
text("Front-end RF 868 MHz : PA HP (+22 dBm) → filtre passe-bas / piège H2 → switch SPDT → 50 Ω", 243.84, 274.32, size=1.27, bold=True)
chain(256.54, 297.18,
      [P("keeptracker:R", "R44", "0Ω", R0402),
       P("keeptracker:L", "L5", "2,6nH", FB0402, "Murata LQW15AN2N6B00"),
       P("keeptracker:L", "L6", "1,8nH ±0,3nH", FB0402, "Murata LQG15HS1N8S02D"),
       P("keeptracker:L", "L7", "7nH", FB0402, "Murata LQW15AN7N0G00"),
       P("keeptracker:C", "C64", "68pF C0G", C0402, "Murata GRM1555C1H680JA01")],
      [("RFO_HP", []), ("PA_A", []),
       ("PA_B", [S("keeptracker:C", "C61", "6,2pF C0G", fp=C0402, mpn="Murata GJM1555C1H6R2DB01")]),
       ("PA_C", [S("keeptracker:C", "C63", "2,4pF C0G", fp=C0402, mpn="Murata GJM1555C1H2R4CB01")]),
       ("PA_D", []),
       ("TX_SW", [S("keeptracker:C", "C65", "2,4pF C0G", fp=C0402, mpn="Murata GJM1555C1H2R4CB01")])])
# C62 en parallèle sur L6 : piège sur l'harmonique 2
a, b = hpart("keeptracker:C", "C62", "4pF C0G", 292.1, 284.48, C0402, "Murata GJM1555C1H4R0CB01")
connect("PA_B", a[0], a[1], "L"); connect("PA_C", b[0], b[1], "R")
# RFO_LP non utilisé (option PA basse puissance)
a, b = hpart("keeptracker:R", "R45", "NM", 337.82, 284.48, R0402, dnp=True)
connect("RFO_LP", a[0], a[1], "L"); connect("PA_A", b[0], b[1], "R")
# alimentation du PA : self de choc depuis VR_PA + découplage
a, b = hpart("keeptracker:L", "L4", "47nH", 274.32, 317.5, FB0402, "Murata LQW15AN47NG00")
connect("VR_PA", a[0], a[1], "L"); connect("PA_B", b[0], b[1], "R")
C("C59", "47nF X7R", 218.44, 325.12, "VR_PA", "GND")
C("C60", "68pF C0G", 233.68, 325.12, "VR_PA", "GND", mpn="Murata GRM1555C1H680JA01")
# réception : balun discret RFI_P / RFI_N
chain(274.32, 342.9,
      [P("keeptracker:C", "C66", "3,3pF C0G", C0402, "Murata GJM1555C1H3R3CB01")],
      [("RFI_P", []), ("RX_SW", [S("keeptracker:C", "C68", "NM", fp=C0402, dnp=True)])])
two("keeptracker:L", "L8", "11nH", 256.54, 346.71, "RFI_P", "RFI_N", fp=FB0402, mpn="Murata LQW15AN11NG00")
C("C67", "3,6pF C0G", 238.76, 354.33, "RFI_N", "GND", mpn="Murata GJM1555C1H3R6CB01")
# switch TX/RX (alimenté par ses commandes : 0 µA en veille si FE_CTRL1 = FE_CTRL2 = 0)
ic("keeptracker:XA17-G4K", "U13", "XA17-G4K", 325.12, 330.2,
   {"1": "TX_SW", "3": "RX_SW", "4": "FE_CTRL2", "6": "FE_CTRL1", "5": "SW_COM", "2": "GND"},
   fp="Package_TO_SOT_SMD:SOT-363_SC-70-6", mpn="Xinluda XA17-G4K (LCSC C513494)")
C("C69", "1nF X7R", 302.26, 358.14, "FE_CTRL1", "GND")
C("C70", "1nF X7R", 314.96, 358.14, "FE_CTRL2", "GND")
# sortie 50 Ω : liaison DC + accord d'antenne en Pi (C56 / R43 / C57)
chain(372.11, 345.44,
      [P("keeptracker:C", "C71", "68pF C0G", C0402, "Murata GRM1555C1H680JA01"),
       P("keeptracker:R", "R43", "0Ω", R0402)],
      [("SW_COM", []),
       ("LORA_RF", [S("keeptracker:C", "C56", "3,0pF C0G", fp=C0402, mpn="Murata GJM1555C1H3R0CB01")]),
       ("LORA_ANT", [S("keeptracker:C", "C57", "NM", dnp=True)])])
text("Accord antenne (Abracon : 0 Ω + 3,0 pF)", 363.22, 336.55, size=1.0, bold=True)
two("keeptracker:ANT", "AE1", "ACAG1204-868-T", 320.04, 375.92, "LORA_ANT", None,
    fp="keeptracker:Abracon_ACAG1204-868-T", mpn="Abracon ACAG1204-868-T")
ic("keeptracker:U.FL", "J4", "U.FL (option LoRa)", 287.02, 377.19, {"1": "LORA_RF", "2": "GND"},
   fp="Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", dnp=True)
two("keeptracker:ESD_RF", "D5", "ESD 0,15pF", 350.52, 383.54, "LORA_ANT", "GND", fp="Diode_SMD:D_0402_1005Metric",
    mpn="TI TPD1E0B04DPYR")
text("Table switch : TX ⇒ FE_CTRL1 = 0, FE_CTRL2 = 1 · RX ⇒ FE_CTRL1 = 1, FE_CTRL2 = 0 · veille ⇒ 0 / 0.\n"
     "Selfs RF : bobinées 0402 Murata LQW15 (Q élevé, pertes mini) · condensateurs C0G ±0,25 pF.\n"
     "Réseau recopié de la carte Olimex BB-STM32WL rév. D1 (même MCU) : à reconfirmer au VNA sur notre PCB.\n"
     "D5 : ESD 0,15 pF (broche 1 = GND) au pied de l'antenne · J4 (DNP) : mesure conduite 50 Ω — retirer R43.",
     342.9, 393.7, size=1.0)

# =========================================================== BLOC H : GNSS
frame(462.28, 299.72, 826.77, 393.7, "H · GNSS u-blox MAX-M10S, interrupteur d'alimentation et filtrage")
org(111.76, 45.72)
ic("keeptracker:TPS22916C", "U8", "TPS22916CYFPR", 381.0, 281.94,
   {"A2": "+3V3", "B2": "GNSS_EN", "B1": "GND", "A1": "GNSS_3V3"},
   fp="keeptracker:TI_DSBGA-4_YFP_0.78x0.78mm_P0.4mm", mpn="TI TPS22916CYFPR")
C("C26", "1µF 10V", 364.49, 311.15, "+3V3", "GND")
C("C27", "1µF 10V", 379.73, 311.15, "GNSS_3V3", "GND")
two("keeptracker:FB", "FB4", "120Ω@100MHz", 394.97, 311.15, "GNSS_3V3", "GNSS_VCC", fp=FB0402, mpn="Murata BLM15PX121SN1D")
C("C28", "100nF 16V", 417.83, 311.15, "GNSS_VCC", "GND")
C("C48", "10µF 10V", 433.07, 311.15, "GNSS_VCC", "GND", fp=C0805)
C("C49", "47pF C0G", 448.31, 311.15, "GNSS_VCC", "GND")
C("C50", "100nF 16V", 520.7, 311.15, "GNSS_VBCKP", "GND")
R("R41", "0Ω", 495.3, 311.15, "+3V3", "GNSS_VBCKP", fp=R0402, dnp=True)
R("R40", "0Ω", 508.0, 311.15, "GNSS_BCKP_IO", "GNSS_VBCKP", fp=R0402)
ic("keeptracker:MAX-M10S", "U9", "MAX-M10S-00B", 473.71, 279.4,
   {"8": "GNSS_VCC", "7": "GNSS_VCC", "6": "GNSS_VBCKP", "11": "GNSS_RF", "15": "NC", "14": "NC", "13": "NC",
    "1": "GND", "10": "GND", "12": "GND",
    "2": "GNSS_TXD_M", "3": "GNSS_RXD_M", "9": "GNSS_RST_M", "4": "NC", "5": "NC", "18": "GNSS_SAFEBOOT",
    "16": "NC", "17": "NC"},
   fp="RF_GPS:ublox_MAX", ds="https://www.u-blox.com/en/product/max-m10-series", mpn="u-blox MAX-M10S-00B")
R("R29", "1k", 525.78, 284.48, "GNSS_TXD_M", "GNSS_TX", fp=R0402)
R("R30", "1k", 538.48, 284.48, "GNSS_RXD_M", "GNSS_RX", fp=R0402)
R("R31", "1k", 551.18, 284.48, "GNSS_RST_M", "GNSS_RST", fp=R0402)
# antenne → ESD → réseau en Pi d'accord → RF_IN
one("keeptracker:ANT", "AE2", "Patch GNSS 25 mm", 594.36, 289.56, "GNSS_ANT")
ic("keeptracker:U.FL", "J5", "U.FL (option GNSS)", 622.3, 292.1, {"1": "GNSS_ANT", "2": "GND"},
   fp="Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical", dnp=True)
two("keeptracker:ESD_RF", "D6", "ESD 0,15pF", 604.52, 325.12, "GNSS_ANT", "GND", fp="Diode_SMD:D_0402_1005Metric",
    mpn="TI TPD1E0B04DPYR")
chain(640.08, 320.04,
      [P("keeptracker:R", "R32", "0Ω", R0402)],
      [("GNSS_ANT", [S("keeptracker:C", "C51", "NM", dnp=True)]),
       ("GNSS_RF", [S("keeptracker:C", "C52", "NM", dnp=True)])])
text("Réseau en Pi (NM / 0 Ω / NM) : accord de l'antenne sur carte", 612.14, 303.53, size=1.0, bold=True)
text("FB4 + C28/C48/C49 : isolent le GNSS du bruit numérique et de l'émission LoRa.\n"
     "R29–R31 (1 kΩ série) : limitent la rétro-alimentation quand GNSS_EN = 0.\n"
     "V_IO = VCC (VIO_SEL ouvert ⇒ E/S 3,3 V). V_BCKP alimenté par PA9 via R40 : 28 µA en backup matériel,\n"
     "1er poste de consommation en veille ⇒ le firmware coupe V_BCKP après ≈ 4 h d'immobilité (éphémérides périmées).\n"
     "R41 (DNP) : V_BCKP permanent sur +3V3. SAFEBOOT_N → TP10 (récupération firmware).",
     500.38, 330.2, size=1.0)

# =========================================================== BLOC I : accéléromètre
frame(462.28, 398.78, 619.76, 482.6, "I · Détection de mouvement (LIS2DW12)")
org(111.76, 66.04)
ic("keeptracker:LIS2DW12", "U10", "LIS2DW12TR", 403.86, 365.76,
   {"9": "+3V3", "10": "+3V3", "5": "NC", "6": "GND", "7": "GND", "8": "GND",
    "1": "I2C_SCL", "4": "I2C_SDA", "2": "+3V3", "3": "GND", "12": "ACC_INT", "11": "NC"},
   fp="Package_LGA:LGA-12_2x2mm_P0.5mm", mpn="ST LIS2DW12TR")
C("C29", "100nF 16V", 360.68, 393.7, "+3V3", "GND")
C("C30", "100nF 16V", 375.92, 393.7, "+3V3", "GND")
C("C53", "10µF 10V", 391.16, 393.7, "+3V3", "GND", fp=C0805)
text("C29 → VDD, C30 → VDD_IO, C53 réservoir (recommandation ST).", 355.6, 406.4, size=1.0)

# =========================================================== BLOC J : SWD
frame(624.84, 398.78, 826.77, 439.42, "J · Programmation SWD")
org(149.86, 66.04)
ic("keeptracker:TagConnect", "J6", "TC2030-NL", 495.3, 354.33,
   {"1": "+3V3", "2": "SWDIO", "3": "NRST", "4": "SWCLK", "5": "GND", "6": "NC"},
   fp="Connector:Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical")

# =========================================================== BLOC K : points de test et fixation
frame(624.84, 444.5, 826.77, 543.56, "K · Points de test et fixations")
org(0, 0)
for i, net in enumerate(["VBUS", "VSYS", "VBAT", "+3V3", "+3V3_RF", "VPZ", "GNSS_VCC", "GND", "VIN_BB", "GNSS_SAFEBOOT"]):
    one("keeptracker:TestPoint", f"TP{i + 1}", net, 637.54 + i * 17.78, 467.36, net, fp="TestPoint:TestPoint_Pad_D1.5mm")
for i in range(4):
    one("keeptracker:MountingHole", f"H{i + 1}", "M3", 637.54 + i * 22.86, 510.54, "GND",
        fp="MountingHole:MountingHole_3.2mm_M3_Pad_Via")

# =========================================================== BLOC L : arbre d'alimentation
frame(12.7, 487.68, 619.76, 546.1, "L · Arbre d'alimentation, impédances contrôlées et pertes")
text("USB-C 5 V  →  D1 TVS + F1 PTC + FB2  →  BQ24074 (IN, OVP 10,5 V, ILIM 1,3 A, ITERM 60 mA)  →  VSYS\n"
     "Cellule Li-ion 1S  →  F2 3 A  →  S-8261 / AO8814 (OV · UV · OC · CC)  →  VBAT  →  BQ24074 (chemin d'alimentation)  →  VSYS\n"
     "Piézo  →  D2 TVS + R12/R13  →  LTC3588-1  →  VPZ 3,6 V (2 × 10 F, U12 ALD910025)  →  U6 LM66100  →  VIN_BB\n"
     "VSYS  →  U11 LM66100  →  VIN_BB  →  TPS63900 buck-boost (IQ 75 nA)  →  +3V3  →  MCU, LIS2DW12, VDDA (FB1), V_BCKP GNSS (PA9)\n"
     "+3V3  →  FB3  →  +3V3_RF  →  VDDPA, VDDRF, front-end RF        +3V3  →  TPS22916C (GNSS_EN)  →  GNSS_3V3  →  FB4  →  GNSS_VCC",
     17.78, 496.57, size=1.5, absolute=True)
text("Impédance contrôlée (classe RF_50R)", 17.78, 519.43, size=1.3, bold=True, absolute=True)
text("Empilage JLC04161H-7628 (1,6 mm) : L1 SIG/RF · L2 GND plein · L3 PWR · L4 SIG — diélectrique L1→L2 = 0,21 mm, εr 4,4.\n"
     "CPWG 50 Ω (L1, référence L2) : piste 0,26 mm, fente 0,20 mm, εeff ≈ 3,05 (calcul Wadell, à reconfirmer sur le calculateur du fabricant).\n"
     "Nets 50 Ω : LORA_RF, LORA_ANT, GNSS_ANT, GNSS_RF — longueur minimale, pas de via, coudes à 45°, vias de couture ≤ λ/20 (≈ 1,5 mm à 1,6 GHz).\n"
     "RFO_HP / RFO_LP / RFI_P / RFI_N / VR_PA : impédances complexes ⇒ recopier le placement ST (composants 0402 accolés aux broches).",
     17.78, 523.24, size=1.15, absolute=True)
text("Pertes maîtrisées (rév. C)", 330.2, 519.43, size=1.3, bold=True, absolute=True)
text("TPS63900 IQ 75 nA · LM66100 IQ 150 nA, RON 79 mΩ · TPS22916 coupe le GNSS · ALD910025 : 0 A d'équilibrage à 1,8 V/cellule.\n"
     "Pull-ups côté batterie 100 kΩ (ALRT, PG, CHG) · pont VPZ 2 × 10 MΩ (0,18 µA) · V_BCKP GNSS (28 µA) commuté par PA9.\n"
     "Chemin de puissance : FB2 25 mΩ, F2 + Q1 ≈ 50 mΩ, L1 ISAT ≥ 2 A · fin de charge à 60 mA (ITERM) au lieu d'une charge perpétuelle.\n"
     "Firmware : Stop2 + RTC, GPIO inutilisés en analogique, GNSS en mode backup puis coupé, LoRa SF adaptatif (ADR).",
     330.2, 523.24, size=1.15, absolute=True)

# ---------------------------------------------------------------- write
title = """(title_block (title "Keep Tracking — Traceur GPS autonome pour deux-roues")
 (date "2026-10-11") (rev "C")
 (company "INSA — Projet GPS Tracker 2026-2027")
 (comment 1 "M. Bachir · A. E. Douimi · W. Laghbissi · N. Ezzouhri — encadrant : M. Duclos")
 (comment 2 "GNSS MAX-M10S · LoRaWAN 868 MHz (STM32WLE5) · Li-ion 1S + piézo")
 (comment 3 "Rév. C : brochages vérifiés datasheets, pertes réduites (OR-ing RCB, SAB, V_BCKP commuté), lignes 50 Ω")
 (comment 4 "Front-end RF discret (réf. Olimex BB-STM32WL D1) — accord final au VNA sur le PCB"))"""

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0") (uuid "{ROOT}") (paper "A1")\n')
    fh.write(title + "\n(lib_symbols\n")
    for s in lib.values():
        fh.write(s + "\n")
    fh.write(")\n")
    for it in items:
        fh.write(it + "\n")
    fh.write('(sheet_instances (path "/" (page "1")))\n)\n')

d = os.path.dirname(os.path.abspath(OUT))
with open(os.path.join(d, "keeptracker.kicad_sym"), "w", encoding="utf-8") as fh:
    fh.write('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") (generator_version "8.0")\n')
    for lid, sx in lib.items():
        fh.write(sx.replace(f'(symbol "{lid}"', f'(symbol "{lid.split(":")[1]}"', 1) + "\n")
    fh.write(")\n")
with open(os.path.join(d, "sym-lib-table"), "w", encoding="utf-8") as fh:
    fh.write('(sym_lib_table\n  (version 7)\n  (lib (name "keeptracker")(type "KiCad")(uri "${KIPRJMOD}/keeptracker.kicad_sym")(options "")(descr "Symboles du projet Keep Tracking"))\n)\n')
pro = os.path.join(d, "keeptracker.kicad_pro")


def netclass(name, track, clear, via_d=0.6, via_drill=0.3, prio=0):
    return {"name": name, "track_width": track, "clearance": clear, "via_diameter": via_d, "via_drill": via_drill,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0, "priority": prio,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}


# classes de nets : RF 50 Ω (CPWG 0,26 / 0,20 mm), puissance forte, puissance, signal par défaut
NETCLASS_PATTERNS = {
    "RF_50R": ["LORA_RF", "LORA_ANT", "GNSS_ANT", "GNSS_RF", "SW_COM", "TX_SW", "RX_SW", "PA_D"],
    "RF_MATCH": ["RFO_HP", "RFO_LP", "RFI_P", "RFI_N", "VR_PA", "PA_A", "PA_B", "PA_C", "HSE_IN", "TCXO_OUT"],
    "PWR_1A": ["VBUS_IN", "VBUS", "VSYS", "VBAT", "BAT_P", "BATN", "Q1_D", "VIN_BB", "LX1", "LX2", "+3V3"],
    "PWR": ["+3V3_RF", "GNSS_3V3", "GNSS_VCC", "VDDA", "VPZ", "LTC_*", "PZ1", "PZ2", "PIEZO_*", "VLXSMPS", "VFBSMPS"],
}
project = {
    "meta": {"filename": "keeptracker.kicad_pro", "version": 1},
    "sheets": [[ROOT, "Root"]],
    "net_settings": {
        "classes": [netclass("Default", 0.15, 0.15, prio=2147483647),
                    netclass("RF_50R", 0.26, 0.20, 0.45, 0.2, prio=0),
                    netclass("RF_MATCH", 0.20, 0.15, 0.45, 0.2, prio=1),
                    netclass("PWR_1A", 0.50, 0.20, 0.8, 0.4, prio=2),
                    netclass("PWR", 0.30, 0.15, 0.6, 0.3, prio=3)],
        "meta": {"version": 4},
        "net_colors": None,
        "netclass_assignments": None,
        "netclass_patterns": [{"netclass": c, "pattern": n} for c, nets in NETCLASS_PATTERNS.items() for n in nets],
    },
}
import json
with open(pro, "w", encoding="utf-8") as fh:
    json.dump(project, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
# ---------------------------------------------------------------- empreintes projet (keeptracker.pretty)
PRETTY = os.path.join(d, "keeptracker.pretty")
os.makedirs(PRETTY, exist_ok=True)


def fp_text(kind, val, x, y, layer, size=0.8):
    th = round(size * 0.15, 3)
    return (f'(property "{kind}" "{val}" (at {f(x)} {f(y)} 0) (layer "{layer}") (uuid "{U()}") '
            f'(effects (font (size {f(size)} {f(size)}) (thickness {f(th)}))))')


def fp_rect(x1, y1, x2, y2, layer, w=0.1):
    return (f'(fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(w)}) (type solid)) '
            f'(fill no) (layer "{layer}") (uuid "{U()}"))')


def fp_line(x1, y1, x2, y2, layer, w=0.12):
    return (f'(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(w)}) (type solid)) '
            f'(layer "{layer}") (uuid "{U()}"))')


def write_fp(name, descr, tags, body):
    with open(os.path.join(PRETTY, name + ".kicad_mod"), "w", encoding="utf-8") as fh:
        fh.write(f'(footprint "{name}" (version 20240108) (generator "pcbnew") (generator_version "8.0") '
                 f'(layer "F.Cu") (descr "{descr}") (tags "{tags}")\n')
        for item in body:
            fh.write("  " + item + "\n")
        fh.write(")\n")


# TPS22916 YFP : DSBGA-4 0,78 × 0,78 mm, pas 0,4 mm — billes Ø 0,23 NSMD, ouverture vernis Ø 0,33, pochoir 0,25
body = [fp_text("Reference", "REF**", 0, -1.1, "F.SilkS", 0.6), fp_text("Value", "TPS22916CYFPR", 0, 1.1, "F.Fab", 0.5),
        fp_rect(-0.39, -0.39, 0.39, 0.39, "F.Fab", 0.05), fp_rect(-0.6, -0.6, 0.6, 0.6, "F.CrtYd", 0.05),
        fp_line(-0.55, -0.55, -0.15, -0.55, "F.SilkS", 0.08), fp_line(-0.55, -0.55, -0.55, -0.15, "F.SilkS", 0.08),
        '(attr smd)']
for num, (px, py) in {"A1": (-0.2, -0.2), "A2": (0.2, -0.2), "B1": (-0.2, 0.2), "B2": (0.2, 0.2)}.items():
    body.append(f'(pad "{num}" smd circle (at {f(px)} {f(py)}) (size 0.23 0.23) (layers "F.Cu" "F.Mask" "F.Paste") '
                f'(solder_mask_margin 0.05) (solder_paste_margin 0.01) (uuid "{U()}"))')
write_fp("TI_DSBGA-4_YFP_0.78x0.78mm_P0.4mm", "TI YFP0004 DSBGA-4, 0.78x0.78mm, pitch 0.4mm, NSMD 0.23mm (SLVSDO5F)",
         "DSBGA WCSP TPS22916", body)

# ACAG1204-868-T : pastilles 1,15 × 4,2 mm espacées de 10,3 mm ; zone dégagée 15,3 × 15,0 mm en bord de carte
kx1, kx2, ky1, ky2 = -7.1, 8.2, -2.9, 12.1
body = [fp_text("Reference", "REF**", 0, -4.0, "F.SilkS", 0.8), fp_text("Value", "ACAG1204-868-T", 0, 3.2, "F.Fab", 0.8),
        fp_rect(-6.0, -2.0, 6.0, 2.0, "F.Fab", 0.1), fp_rect(kx1, ky1, kx2, ky2, "F.CrtYd", 0.05),
        fp_line(-4.9, -2.2, 4.9, -2.2, "F.SilkS"), fp_line(-4.9, 2.2, 4.9, 2.2, "F.SilkS"),
        fp_line(kx1, ky1, kx2, ky1, "Cmts.User", 0.1),
        '(fp_text user "BORD DE CARTE — zone sans cuivre 15,3 x 15,0 mm" (at 0.55 11.2 0) (layer "Cmts.User") '
        f'(uuid "{U()}") (effects (font (size 0.45 0.45) (thickness 0.07))))',
        '(attr smd)',
        f'(pad "1" smd rect (at 5.725 0) (size 1.15 4.2) (layers "F.Cu" "F.Mask" "F.Paste") (uuid "{U()}"))',
        f'(pad "2" smd rect (at -5.725 0) (size 1.15 4.2) (layers "F.Cu" "F.Mask" "F.Paste") (uuid "{U()}"))',
        f'(zone (net 0) (net_name "") (layers "*.Cu") (uuid "{U()}") (name "ANT_KEEPOUT") (hatch edge 0.5) '
        '(connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no) '
        '(keepout (tracks allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) '
        '(fill (thermal_gap 0.5) (thermal_bridge_width 0.5)) '
        f'(polygon (pts (xy {f(kx1)} {f(ky1)}) (xy {f(kx2)} {f(ky1)}) (xy {f(kx2)} {f(ky2)}) (xy {f(kx1)} {f(ky2)}))))']
write_fp("Abracon_ACAG1204-868-T", "Abracon ACAG1204-868-T 868MHz chip antenna 12x4mm, pad 1 = feed, pad 2 = NC (mechanical), "
         "keepout 15.3x15mm at board edge", "antenna LoRa 868", body)
with open(os.path.join(d, "fp-lib-table"), "w", encoding="utf-8") as fh:
    fh.write('(fp_lib_table\n  (version 7)\n  (lib (name "keeptracker")(type "KiCad")(uri "${KIPRJMOD}/keeptracker.pretty")'
             '(options "")(descr "Empreintes du projet Keep Tracking"))\n)\n')

single = sorted(n for n, c in labels_used.items() if c == 1)
print("labels utilisés une seule fois:", single)
