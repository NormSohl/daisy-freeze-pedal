#!/usr/bin/env python3
"""Generate the carrier board schematic (KiCad 7) from one netlist definition.

Every symbol pin gets a local net label (or a no-connect flag), so the sheet
reads as a wiring table and the netlist is exactly what is defined below.
Run:  python3 gen_schematic.py   (writes carrier.kicad_sch, carrier.kicad_sym,
      carrier.kicad_pro, sym-lib-table, fp-lib-table)
"""
import math, os, uuid
from kiutils.symbol import SymbolLib

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD_SYM = "/usr/share/kicad/symbols"
PROJECT = "carrier"
ROOT_UUID = "6f1d3c1e-5a3b-4f0e-9b7a-0c4d2e9a1f00"   # stable so re-runs diff cleanly


def uid(seed):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"daisy-freeze-pedal/{seed}"))


# ── Daisy Seed symbol ────────────────────────────────────────────────
SEED_PINS = {
    1: "D0", 2: "D1", 3: "D2", 4: "D3", 5: "D4", 6: "D5", 7: "D6", 8: "D7",
    9: "D8", 10: "D9", 11: "D10", 12: "D11", 13: "D12", 14: "D13", 15: "D14",
    16: "AUDIO_IN_L", 17: "AUDIO_IN_R", 18: "AUDIO_OUT_L", 19: "AUDIO_OUT_R",
    20: "AGND", 21: "3V3A", 22: "A0/D15", 23: "A1/D16", 24: "A2/D17",
    25: "A3/D18", 26: "A4/D19", 27: "A5/D20", 28: "A6/D21", 29: "A7/D22",
    30: "A8/D23", 31: "A9/D24", 32: "A10/D25", 33: "D26", 34: "D27",
    35: "A11/D28", 36: "D29/USB_D-", 37: "D30/USB_D+", 38: "3V3D", 39: "VIN",
    40: "DGND",
}
SEED_TYPES = {20: "power_in", 40: "power_in", 21: "power_out", 38: "power_out",
              39: "power_in", 16: "input", 17: "input", 18: "output", 19: "output"}


def seed_pin_xy(n):
    if n >= 21:                       # left column, 21 at top
        return -15.24, 24.13 - (n - 21) * 2.54, 0
    return 15.24, -24.13 + (n - 1) * 2.54, 180   # right column, 20 at top


def write_seed_symbol(path):
    pins = []
    for n, name in SEED_PINS.items():
        x, y, a = seed_pin_xy(n)
        t = SEED_TYPES.get(n, "bidirectional")
        pins.append(
            f'      (pin {t} line (at {x} {y} {a}) (length 2.54)\n'
            f'        (name "{name}" (effects (font (size 1.27 1.27))))\n'
            f'        (number "{n}" (effects (font (size 1.27 1.27)))))')
    text = f'''(kicad_symbol_lib (version 20220914) (generator gen_schematic)
  (symbol "DaisySeed" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at 0 29.21 0) (effects (font (size 1.27 1.27))))
    (property "Value" "DaisySeed" (at 0 -29.21 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "carrier:DaisySeed_Socket_2x20" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "https://www.electro-smith.com/daisy/daisy" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "DaisySeed_0_1"
      (rectangle (start -12.7 26.67) (end 12.7 -26.67) (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "DaisySeed_1_1"
{chr(10).join(pins)}
    )
  )
)
'''
    open(path, "w").write(text)


# ── Parts and nets (the single source of truth) ──────────────────────
R0603, C0603, C0805 = "Resistor_SMD:R_0603_1608Metric", "Capacitor_SMD:C_0603_1608Metric", "Capacitor_SMD:C_0805_2012Metric"
# LCSC numbers for fab placement — confirm in the fab's parts search before ordering.
LCSC = {"1k": "C21190", "100k": "C25803", "470": "C23179", "0R": "C21189", "100n": "C14663", "10u": "C15850"}

POTS = [("Dry", "POT_DRY", 22), ("Loop", "POT_LOOP", 23), ("−8", "POT_SUB", 24),
        ("+5", "POT_FIFTH", 25), ("+8", "POT_OCT", 26), ("Fade", "POT_FADE", 27),
        ("Texture", "POT_TEX", 28)]

parts = []   # dicts: ref, lib, value, fp, at, rot, pins{num: net|None}, fields{}


def part(ref, lib, value, fp, at, pins, rot=0, **fields):
    pins = {str(k): v for k, v in pins.items()}
    parts.append(dict(ref=ref, lib=lib, value=value, fp=fp, at=at, rot=rot, pins=pins, fields=fields))


seed_nets = {n: None for n in SEED_PINS}
seed_nets.update({16: "IN_L", 17: "IN_R", 18: "OUT_L", 19: "OUT_R", 20: "AGND", 21: "+3V3A",
                  38: "+3V3D", 40: "DGND",
                  8: "TGL_LAYERS", 9: "TGL_FIFTH_DIR", 10: "FS_FREEZE", 11: "FS_CLEAR",
                  12: "LED_RED_DRV", 13: "LED_GRN_DRV", 33: "OUTR_DETECT"})
for _, net, pin in POTS:
    seed_nets[pin] = "ADC_" + net[4:]
part("U1", "carrier:DaisySeed", "Daisy Seed", "carrier:DaisySeed_Socket_2x20", (210, 150), seed_nets,
     MPN="Electrosmith Daisy Seed (on 2x 1x20 female headers)")

for i, (label, net, _) in enumerate(POTS):
    y = 40 + i * 30
    adc = "ADC_" + net[4:]
    part(f"RV{i+1}", "Device:R_Potentiometer", f"B10K {label}", "carrier:Potentiometer_Alpha_RV09AF-40_Vertical",
         (50, y), {"1": "AGND", "2": net, "3": "+3V3A"}, MPN="Alpha RV09AF-40-20K-B10K")
    part(f"R{i+1}", "Device:R", "1k", R0603, (75, y), {"1": net, "2": adc}, rot=90, LCSC=LCSC["1k"])
    part(f"C{i+1}", "Device:C", "100n", C0603, (95, y), {"1": adc, "2": "AGND"}, LCSC=LCSC["100n"])

part("C8", "Device:C", "10u", C0805, (125, 45), {"1": "+3V3A", "2": "AGND"}, LCSC=LCSC["10u"])
part("C9", "Device:C", "100n", C0603, (140, 45), {"1": "+3V3A", "2": "AGND"}, LCSC=LCSC["100n"])

JACK_FP = "carrier:Jack_6.35mm_Neutrik_NMJ6HCD2_Horizontal_FabOnlySilk"
jacks = [
    ("J3", "In L / Mono", {"T": "IN_L", "TN": None, "R": None, "RN": None, "S": "AGND"}),
    ("J4", "In R (normalled from In L)", {"T": "IN_R", "TN": "IN_L", "R": None, "RN": None, "S": "AGND"}),
    ("J5", "Out L / Mono", {"T": "OUT_L", "TN": None, "R": None, "RN": None, "S": "AGND"}),
    ("J6", "Out R (ring = plug detect)", {"T": "OUT_R", "TN": None, "R": "OUTR_RING", "RN": None, "S": "AGND"}),
]
for i, (ref, val, pins) in enumerate(jacks):
    part(ref, "Connector_Audio:AudioJack3_SwitchTR", val, JACK_FP, (330, 45 + i * 38), pins, rot=180,
         MPN="Neutrik NMJ6HCD2")
part("R10", "Device:R", "1k", R0603, (370, 165), {"1": "OUTR_RING", "2": "OUTR_DETECT"}, rot=90, LCSC=LCSC["1k"])
part("R11", "Device:R", "100k", R0603, (390, 155), {"1": "+3V3D", "2": "OUTR_DETECT"}, LCSC=LCSC["100k"])

part("SW1", "Switch:SW_SPDT", "Single / Multi", "carrier:SW_E-Switch_100SP_M2_PCB", (300, 225),
     {"1": "DGND", "2": "TGL_LAYERS", "3": "+3V3D"}, MPN="E-Switch 100SP1T1B1M2QE")
part("SW2", "Switch:SW_SPDT", "+5 up / down", "carrier:SW_E-Switch_100SP_M2_PCB", (350, 225),
     {"1": "DGND", "2": "TGL_FIFTH_DIR", "3": "+3V3D"}, MPN="E-Switch 100SP1T1B1M2QE")

FS_FP = "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"
part("J1", "Connector_Generic:Conn_01x02", "Freeze footswitch", FS_FP, (140, 225), {"1": "FS_FREEZE", "2": "DGND"},
     MPN="JST B2B-PH-K; footswitch: soft-touch momentary SPST, panel mounted")
part("J2", "Connector_Generic:Conn_01x02", "Clear footswitch", FS_FP, (140, 250), {"1": "FS_CLEAR", "2": "DGND"},
     MPN="JST B2B-PH-K; footswitch: soft-touch momentary SPST, panel mounted")

part("D1", "Device:LED_Dual_AKA", "Red/Green", "LED_THT:LED_D5.0mm-3", (230, 245),
     {"1": "LED_RED", "2": "DGND", "3": "LED_GRN"}, MPN="5 mm bi-colour LED, common cathode (red/green)")
part("R8", "Device:R", "470", R0603, (200, 240), {"1": "LED_RED_DRV", "2": "LED_RED"}, rot=90, LCSC=LCSC["470"])
part("R9", "Device:R", "470", R0603, (200, 252), {"1": "LED_GRN_DRV", "2": "LED_GRN"}, rot=90, LCSC=LCSC["470"])

part("R12", "Device:R", "0R", R0603, (260, 262), {"1": "AGND", "2": "DGND"}, rot=90, LCSC=LCSC["0R"],
     Note="Single-point AGND-DGND join (Seed datasheet: AGND must connect to DGND)")

for i in range(4):
    part(f"H{i+1}", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", (300 + i * 20, 250), {})

# ── Symbol geometry from the libraries ───────────────────────────────
libs = {}


def lib_symbol(lib_id):
    nick, name = lib_id.split(":")
    if nick not in libs:
        path = os.path.join(HERE, "carrier.kicad_sym") if nick == "carrier" else os.path.join(KICAD_SYM, f"{nick}.kicad_sym")
        libs[nick] = SymbolLib.from_file(path)
    for s in libs[nick].symbols:
        if s.entryName == name:
            return s
    raise KeyError(lib_id)


def sym_pins(sym):
    return {p.number: (p.position.X, p.position.Y, p.position.angle or 0) for u in sym.units for p in u.pins}


def to_sheet(at, rot, px, py):
    r = math.radians(rot)
    x = px * math.cos(r) - py * math.sin(r)
    y = px * math.sin(r) + py * math.cos(r)
    return round(at[0] + x, 2), round(at[1] - y, 2)


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def main():
    write_seed_symbol(os.path.join(HERE, "carrier.kicad_sym"))
    out = [f'(kicad_sch (version 20230121) (generator gen_schematic)\n  (uuid {ROOT_UUID})\n  (paper "A3")',
           '  (title_block (title "Daisy Freeze Pedal - carrier board") (date "2026-10-26") (rev "A")\n'
           '    (comment 1 "Generated by gen_schematic.py from one netlist definition - edit the script, not the sheet")\n'
           '    (comment 2 "Pots/toggles/LED on top side; Seed + jacks on bottom side; footswitches off-board on JST PH"))']

    # embedded library symbols
    used = []
    for p in parts:
        if p["lib"] not in used:
            used.append(p["lib"])
    out.append("  (lib_symbols")
    for lib_id in used:
        s = lib_symbol(lib_id)
        s.libraryNickname = lib_id.split(":")[0]
        out.append("    " + s.to_sexpr().strip().replace("\n", "\n    "))
    out.append("  )")

    labels, ncs = [], []
    for p in parts:
        sym = lib_symbol(p["lib"])
        pins = sym_pins(sym)
        x, y = p["at"]
        props = [("Reference", p["ref"], (x, y - 10), False), ("Value", p["value"], (x, y + 10), False),
                 ("Footprint", p["fp"], (x, y), True), ("Datasheet", "", (x, y), True)]
        props += [(k, v, (x, y), True) for k, v in p["fields"].items()]
        body = [f'  (symbol (lib_id "{p["lib"]}") (at {x} {y} {p["rot"]}) (unit 1)',
                '    (in_bom yes) (on_board yes) (dnp no)',
                f'    (uuid {uid(p["ref"])})']
        for k, v, (px, py), hide in props:
            body.append(f'    (property "{esc(k)}" "{esc(v)}" (at {px} {py} 0)'
                        f' (effects (font (size 1.27 1.27)){" hide" if hide else ""}))')
        for num in pins:
            body.append(f'    (pin "{num}" (uuid {uid(p["ref"] + "/" + num)}))')
        body.append(f'    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{p["ref"]}") (unit 1))))')
        body.append("  )")
        out.append("\n".join(body))

        for num, (px, py, pa) in pins.items():
            sx, sy = to_sheet(p["at"], p["rot"], px, py)
            net = p["pins"].get(num, None)
            if net is None:
                ncs.append(f'  (no_connect (at {sx} {sy}) (uuid {uid(p["ref"] + "/nc/" + num)}))')
                continue
            la = (pa + 180 + p["rot"]) % 360
            just = {0: "left bottom", 90: "left bottom", 180: "right bottom", 270: "right bottom"}[la]
            labels.append(f'  (label "{esc(net)}" (at {sx} {sy} {la}) (fields_autoplaced)\n'
                          f'    (effects (font (size 1.27 1.27)) (justify {just}))\n'
                          f'    (uuid {uid(p["ref"] + "/lbl/" + num)}))')

    out += labels + ncs
    notes = [
        (20, 262, "Pots: CCW end (1) to AGND, CW end (3) to +3V3A, wiper through 1k / 100n RC into the ADC pin."),
        (20, 267, "In R is normalled from In L through its tip switch, so a mono source feeds both inputs."),
        (20, 272, "Out R plug detect: a TS plug shorts the ring to the sleeve (AGND), pulling OUTR_DETECT low;"),
        (20, 277, "with nothing plugged in the 100k holds it high and the firmware sums L+R to Out L."),
    ]
    for i, (nx, ny, t) in enumerate(notes):
        out.append(f'  (text "{esc(t)}" (at {nx} {ny} 0) (effects (font (size 1.5 1.5)) (justify left bottom)) (uuid {uid("note"+str(i))}))')
    out.append('  (sheet_instances (path "/" (page "1")))\n)')
    open(os.path.join(HERE, f"{PROJECT}.kicad_sch"), "w").write("\n".join(out) + "\n")

    open(os.path.join(HERE, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (lib (name "carrier")(type "KiCad")(uri "${KIPRJMOD}/carrier.kicad_sym")(options "")(descr "Project symbols"))\n)\n')
    open(os.path.join(HERE, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (lib (name "carrier")(type "KiCad")(uri "${KIPRJMOD}/carrier.pretty")(options "")(descr "Project footprints"))\n)\n')
    pro = os.path.join(HERE, f"{PROJECT}.kicad_pro")
    if not os.path.exists(pro):
        open(pro, "w").write('{\n  "meta": {"filename": "carrier.kicad_pro", "version": 1},\n  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},\n  "sheets": [["' + ROOT_UUID + '", ""]]\n}\n')
    print(f"{len(parts)} parts, {len(labels)} labels, {len(ncs)} no-connects")


if __name__ == "__main__":
    main()
