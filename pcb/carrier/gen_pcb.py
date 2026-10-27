#!/usr/bin/env python3
"""Build carrier.kicad_pcb from the schematic netlist, placing every part that
meets the case at the enclosure's own coordinates (read from the OpenSCAD model).

Board coordinates: X = 100 + x, Y = 250 - s, where (x, s) are the enclosure's
panel coordinates (x across, s up the slope from the front edge). The board is
viewed from its top side (the side facing the panel).

Run:  python3 gen_pcb.py        (needs KiCad 7 python + OpenSCAD on PATH)
Leaves the board unrouted: outline, holes, placement and ratsnest only.
"""
import json, os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
import pcbnew
os.environ.setdefault("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")

HERE = os.path.dirname(os.path.abspath(__file__))
SYS_FP = "/usr/share/kicad/footprints"
OUT = os.path.join(HERE, "carrier.kicad_pcb")


def enclosure_params():
    with tempfile.TemporaryDirectory() as td:
        echo = os.path.join(td, "p.echo")
        subprocess.run(["openscad", "-D", 'part="none"', "-o", echo, os.path.join(HERE, "enclosure_params.scad")],
                       check=True, capture_output=True)
        line = next(l for l in open(echo) if "PCB_PARAMS" in l)
    return dict(json.loads(line.split("=", 1)[1].strip().rstrip(";")))


def netlist():
    with tempfile.TemporaryDirectory() as td:
        xml = os.path.join(td, "n.xml")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml,
                        os.path.join(HERE, "carrier.kicad_sch")], check=True, capture_output=True)
        root = ET.parse(xml).getroot()
    comps = {c.get("ref"): (c.findtext("value"), c.findtext("footprint")) for c in root.iter("comp")}
    nets = {}
    for n in root.iter("net"):
        name = n.get("name").lstrip("/")
        for nd in n.iter("node"):
            nets[(nd.get("ref"), nd.get("pin"))] = name
    return comps, nets


P = enclosure_params()
MM = pcbnew.FromMM
X = lambda x: 100 + x
Y = lambda s: 250 - s


def vec(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def pad_xy(fp, num):
    for p in fp.Pads():
        if p.GetNumber() == num:
            v = p.GetPosition()
            return pcbnew.ToMM(v.x), pcbnew.ToMM(v.y)
    raise KeyError(num)


def orient(fp, bottom, want, a, b):
    """Rotate (and flip to the back if asked) so the vector from pad a to pad b
    points in direction `want` ('up' = toward the back wall, -Y)."""
    for rot in (0, 90, 180, 270):
        fp.SetPosition(vec(0, 0))
        if fp.IsFlipped():
            fp.Flip(vec(0, 0), True)
        fp.SetOrientationDegrees(rot)
        if bottom:
            fp.Flip(vec(0, 0), True)
        (ax, ay), (bx, by) = pad_xy(fp, a), pad_xy(fp, b)
        dx, dy = bx - ax, by - ay
        if want == "up" and dy < -abs(dx) * 0.9:
            return
    raise RuntimeError(f"no orientation for {fp.GetReference()}")


def move_so(fp, pad_point, target):
    """Translate fp so that pad_point (absolute mm, current) lands on target."""
    p = fp.GetPosition()
    fp.SetPosition(vec(pcbnew.ToMM(p.x) + target[0] - pad_point[0], pcbnew.ToMM(p.y) + target[1] - pad_point[1]))


def main():
    comps, nets = netlist()
    board = pcbnew.BOARD()
    board.GetDesignSettings().SetCopperLayerCount(2)

    netitems = {}
    for name in sorted(set(nets.values())):
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netitems[name] = ni

    fps = {}
    for ref, (value, fpid) in comps.items():
        lib, name = fpid.split(":")
        path = os.path.join(HERE, "carrier.pretty") if lib == "carrier" else os.path.join(SYS_FP, f"{lib}.pretty")
        fp = pcbnew.FootprintLoad(path, name)
        if fp is None:
            sys.exit(f"missing footprint {fpid}")
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetFPIDAsString(fpid)
        board.Add(fp)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in nets:
                pad.SetNet(netitems[nets[key]])
        fps[ref] = fp

    # ── outline ──────────────────────────────────────────────────────
    hw, s0, s1 = P["pcb_half_w"], P["pcb_s0"], P["pcb_s1"]
    corners = [(X(-hw), Y(s1)), (X(hw), Y(s1)), (X(hw), Y(s0)), (X(-hw), Y(s0))]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.1))
        seg.SetStart(vec(*corners[i]))
        seg.SetEnd(vec(*corners[(i + 1) % 4]))
        board.Add(seg)

    # ── top side: pots, toggles, LED, footswitch connectors ─────────
    pots = [("RV%d" % (i + 1), x, P["level_s"]) for i, x in enumerate(P["level_x"])]
    pots += [("RV%d" % (i + 6), x, P["mid_s"]) for i, x in enumerate(P["mid_pot_x"])]
    for ref, x, s in pots:           # shaft axis sits 7.0 mm behind the pin row
        fps[ref].SetPosition(vec(X(x), Y(s) + 7.0))
        fps[ref].Reference().SetVisible(False)   # the control name is printed instead
    for ref, x in zip(("SW1", "SW2"), P["toggle_x"]):
        fps[ref].SetPosition(vec(X(x), Y(P["mid_s"])))
    fps["D1"].SetPosition(vec(X(P["led_x"]) - 2.54, Y(P["led_s"])))
    fps["J1"].SetPosition(vec(X(22), Y(52)))      # Freeze (right footswitch)
    fps["J2"].SetPosition(vec(X(-22), Y(52)))     # Clear (left footswitch)
    for i, (mx, ms) in enumerate(P["pcb_mounts"]):
        fps[f"H{i+1}"].SetPosition(vec(X(mx), Y(ms)))

    # ── bottom side: jacks along the rear edge, Seed with USB to the back ──
    flange_s = P["slope_len"] - P["wall"]          # inside face of the back wall
    for ref, jx in zip(("J3", "J4", "J5", "J6"), P["jack_x"]):
        fp = fps[ref]
        orient(fp, True, "up", "T", "S")            # T->S runs along the axis toward the nose
        tx, ty = pad_xy(fp, "T")
        nx, ny = pad_xy(fp, "TN")
        # axis is midway between the T and TN rows; panel flange is 16.7 mm past T
        move_so(fp, ((tx + nx) / 2, ty), (X(jx), Y(flange_s - 16.7)))
    seed = fps["U1"]
    orient(seed, True, "up", "20", "1")             # pin 20 -> pin 1 points at the USB end
    p1, p40 = pad_xy(seed, "1"), pad_xy(seed, "40")
    move_so(seed, ((p1[0] + p40[0]) / 2, p1[1]), (X(P["seed_x"]), Y(s1 - 1.37)))

    # ── top side small parts (fab-placed SMD) ───────────────────────
    for i in range(7):
        x = -60 + i * 8
        fps[f"R{i+1}"].SetPosition(vec(X(x), Y(76)))
        fps[f"C{i+1}"].SetPosition(vec(X(x), Y(70)))
    fps["C8"].SetPosition(vec(X(-4), Y(76)))
    fps["C9"].SetPosition(vec(X(-4), Y(70)))
    fps["R8"].SetPosition(vec(X(44), Y(64)))
    fps["R9"].SetPosition(vec(X(44), Y(68)))
    fps["R10"].SetPosition(vec(X(66), Y(100)))
    fps["R11"].SetPosition(vec(X(66), Y(104)))
    fps["R12"].SetPosition(vec(X(60), Y(80)))

    # silkscreen control names next to the pots (top side)
    names = ["Dry", "Loop", "-8", "+5", "+8", "Fade", "Texture"]
    for (ref, x, s), name in zip(pots, names):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(name)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(vec(1.2, 1.2))
        t.SetPosition(vec(X(x), Y(s) + 9.5))
        board.Add(t)
    t = pcbnew.PCB_TEXT(board)
    t.SetText("Daisy Freeze Pedal carrier rev A")
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(vec(1.5, 1.5))
    t.SetPosition(vec(X(-50), Y(58)))
    board.Add(t)

    board.Save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
