#!/usr/bin/env python3
"""Write fabrication outputs for the carrier board into fab/:
  gerbers/ + drill files, carrier-gerbers.zip,
  bom-jlc.csv (SMD parts with LCSC numbers), cpl-jlc.csv (SMD placement).
Through-hole parts are hand-soldered and left out of the assembly files.
Run after route_pcb.py:  python3 make_fab.py
"""
import csv, os, subprocess, tempfile, zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
FAB = os.path.join(HERE, "fab")
GER = os.path.join(FAB, "gerbers")
PCB = os.path.join(HERE, "carrier.kicad_pcb")
SCH = os.path.join(HERE, "carrier.kicad_sch")
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def main():
    os.makedirs(GER, exist_ok=True)
    for f in os.listdir(GER):
        os.remove(os.path.join(GER, f))
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask",
        "-o", GER + "/", PCB)
    run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th",
        "--generate-map", "--map-format", "gerberx2", "-o", GER + "/", PCB)
    with zipfile.ZipFile(os.path.join(FAB, "carrier-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(GER)):
            z.write(os.path.join(GER, f), f)

    # BOM from the schematic (SMD parts carry an LCSC field)
    with tempfile.TemporaryDirectory() as td:
        xml = os.path.join(td, "n.xml")
        run("kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, SCH)
        root = ET.parse(xml).getroot()
    groups = defaultdict(list)
    smd_refs = set()
    for c in root.iter("comp"):
        fields = {f.get("name"): f.text for f in c.iter("field")}
        if "LCSC" in fields:
            fp = c.findtext("footprint")
            groups[(c.findtext("value"), fp.split(":")[1], fields["LCSC"])].append(c.get("ref"))
            smd_refs.add(c.get("ref"))
    with open(os.path.join(FAB, "bom-jlc.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (val, fp, lcsc), refs in sorted(groups.items()):
            w.writerow([val, ",".join(sorted(refs, key=lambda r: (r[0], int(r[1:])))), fp, lcsc])

    # placement for the SMD parts
    with tempfile.TemporaryDirectory() as td:
        pos = os.path.join(td, "pos.csv")
        run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
            "--smd-only", "-o", pos, PCB)
        rows = list(csv.DictReader(open(pos)))
    with open(os.path.join(FAB, "cpl-jlc.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            if r["Ref"] in smd_refs:
                w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm",
                            "Top" if r["Side"] == "top" else "Bottom", r["Rot"]])
    print("gerbers:", len(os.listdir(GER)), "files | BOM lines:", len(groups), "| placed SMD parts:", len(smd_refs))


if __name__ == "__main__":
    main()
