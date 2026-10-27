#!/usr/bin/env python3
"""Route carrier.kicad_pcb: set design rules, autoroute with Freerouting,
pour GND on both layers with stitching vias, and write a DRC report.

Run after gen_pcb.py:
    python3 route_pcb.py /path/to/freerouting.jar
Freerouting runs headless under xvfb-run when it is available.
"""
import os, shutil, subprocess, sys, tempfile
import pcbnew
os.environ.setdefault("KICAD7_FOOTPRINT_DIR", "/usr/share/kicad/footprints")

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "carrier.kicad_pcb")
MM = pcbnew.FromMM

TRACK, CLEAR = 0.3, 0.25          # default track width / clearance, mm
VIA_D, VIA_DRILL = 0.8, 0.4
EDGE_CLEAR = 0.5


def set_rules(board):
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = MM(0.2)
    ds.m_MinClearance = MM(0.2)
    ds.m_ViasMinSize = MM(0.6)
    ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(EDGE_CLEAR)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetTrackWidth(MM(TRACK))
    nc.SetClearance(MM(CLEAR))
    nc.SetViaDiameter(MM(VIA_D))
    nc.SetViaDrill(MM(VIA_DRILL))
    ds.SetCustomTrackWidth(MM(TRACK))


def autoroute(board, jar):
    with tempfile.TemporaryDirectory() as td:
        dsn, ses = os.path.join(td, "carrier.dsn"), os.path.join(td, "carrier.ses")
        if not pcbnew.ExportSpecctraDSN(board, dsn):
            sys.exit("DSN export failed")
        cmd = ["java", "-jar", jar, "-de", dsn, "-do", ses, "-mp", "60"]
        if shutil.which("xvfb-run"):
            cmd = ["xvfb-run", "-a"] + cmd
        subprocess.run(cmd, check=True, timeout=1800, capture_output=True)
        if not os.path.exists(ses):
            sys.exit("Freerouting produced no session file")
        import_ses(board, ses)


def sexp(text):
    """Tiny S-expression reader for Specctra session files."""
    import re
    tokens = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur); cur = []
        elif t == ")":
            done = cur; cur = stack.pop(); cur.append(done)
        else:
            cur.append(t.strip('"'))
    return cur[0]


def find(node, key):
    for n in node:
        if isinstance(n, list) and n and n[0] == key:
            yield n


def import_ses(board, ses):
    """KiCad 7's ImportSpecctraSES only works inside the GUI, so read the
    session file here: wires become tracks, vias become vias."""
    root = sexp(open(ses).read())
    routes = next(find(root, "routes"))
    res = next(find(routes, "resolution"))
    scale = {"um": 1e-3, "mm": 1.0, "mil": 0.0254}[res[1]] / float(res[2])   # file units -> mm
    to = lambda x, y: pcbnew.VECTOR2I(MM(float(x) * scale), MM(-float(y) * scale))
    layers = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
    net_out = next(find(routes, "network_out"))
    for net in find(net_out, "net"):
        ni = board.FindNet(net[1])
        for wire in find(net, "wire"):
            path = next(find(wire, "path"))
            layer, width, pts = layers[path[1]], float(path[2]) * scale, path[3:]
            xy = [to(pts[i], pts[i + 1]) for i in range(0, len(pts) - 1, 2)]
            for a, b in zip(xy, xy[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a); t.SetEnd(b); t.SetWidth(MM(width)); t.SetLayer(layer); t.SetNet(ni)
                board.Add(t)
        for v in find(net, "via"):
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(to(v[2], v[3]))
            via.SetDrill(MM(VIA_DRILL)); via.SetWidth(MM(VIA_D))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); via.SetNet(ni)
            board.Add(via)


def board_rect(board, inset):
    bb = board.GetBoardEdgesBoundingBox()
    i = MM(inset)
    return [(bb.GetLeft() + i, bb.GetTop() + i), (bb.GetRight() - i, bb.GetTop() + i),
            (bb.GetRight() - i, bb.GetBottom() - i), (bb.GetLeft() + i, bb.GetBottom() - i)]


def pour(board, netname, layers):
    net = board.FindNet(netname)
    for layer in layers:
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNetCode(net.GetNetCode())
        z.SetLocalClearance(MM(0.3))
        z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.4))
        z.SetThermalReliefSpokeWidth(MM(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in board_rect(board, EDGE_CLEAR):
            ol.Append(x, y)
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def stitch(board, netname, pitch=8.0, keep=1.0):
    """Tie the two ground pours together with a grid of vias, skipping any
    spot closer than `keep` mm (plus via radius) to other copper or a hole."""
    T = pcbnew.ToMM
    net = board.FindNet(netname)
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = T(bb.GetLeft()) + 3, T(bb.GetTop()) + 3, T(bb.GetRight()) - 3, T(bb.GetBottom()) - 3
    obstacles = []      # (kind, geometry, radius)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            r = max(T(p.GetSize().x), T(p.GetSize().y)) / 2
            obstacles.append(("p", (T(p.GetPosition().x), T(p.GetPosition().y)), r))
        if fp.GetReference().startswith("H"):
            obstacles.append(("p", (T(fp.GetPosition().x), T(fp.GetPosition().y)), 3.5))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            obstacles.append(("p", (T(t.GetPosition().x), T(t.GetPosition().y)), T(t.GetWidth()) / 2))
        else:
            obstacles.append(("s", (T(t.GetStart().x), T(t.GetStart().y), T(t.GetEnd().x), T(t.GetEnd().y)), T(t.GetWidth()) / 2))
    added = 0
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            ok = True
            for kind, g, r in obstacles:
                d = ((x - g[0]) ** 2 + (y - g[1]) ** 2) ** 0.5 if kind == "p" else seg_dist(x, y, *g)
                if d < r + VIA_D / 2 + keep:
                    ok = False
                    break
            if ok:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                v.SetDrill(MM(VIA_DRILL)); v.SetWidth(MM(VIA_D))
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net)
                board.Add(v)
                obstacles.append(("p", (x, y), VIA_D / 2))
                added += 1
            x += pitch
        y += pitch
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    print("stitching vias:", added)


def main():
    jar = sys.argv[1] if len(sys.argv) > 1 else "freerouting.jar"
    board = pcbnew.LoadBoard(PCB)
    for t in list(board.GetTracks()):      # re-routable: start clean
        board.Remove(t)
    for z in list(board.Zones()):
        board.Remove(z)
    set_rules(board)
    for attempt in range(1, 5):              # Freerouting is not deterministic; retry until complete
        for t in list(board.GetTracks()):
            board.Remove(t)
        for z in list(board.Zones()):
            board.Remove(z)
        autoroute(board, jar)
        pour(board, "GND", [pcbnew.F_Cu, pcbnew.B_Cu])
        stitch(board, "GND")
        board.BuildConnectivity()
        left = board.GetConnectivity().GetUnconnectedCount(True)
        print(f"route attempt {attempt}: {left} unconnected")
        if left == 0:
            break
    board.Save(PCB)
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(PCB)
    rpt = os.path.join(HERE, "drc-report.txt")
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    print("tracks:", len(board.GetTracks()), "| DRC report:", rpt)


if __name__ == "__main__":
    main()
