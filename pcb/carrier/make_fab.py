#!/usr/bin/env python3
"""Write fabrication outputs for the bare carrier board into fab/:
  gerbers/ + drill files, carrier-gerbers.zip (upload this; no assembly),
  bom.csv (every part, for hand soldering).
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
LAYERS = "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(*args):
    subprocess.run(args, check=True, capture_output=True)


def main():
    os.makedirs(GER, exist_ok=True)
    for f in os.listdir(GER):
        os.remove(os.path.join(GER, f))
    for old in ("bom-jlc.csv", "cpl-jlc.csv"):       # no assembly order any more
        if os.path.exists(os.path.join(FAB, old)):
            os.remove(os.path.join(FAB, old))
    run("kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--subtract-soldermask",
        "-o", GER + "/", PCB)
    run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th",
        "--generate-map", "--map-format", "gerberx2", "-o", GER + "/", PCB)
    with zipfile.ZipFile(os.path.join(FAB, "carrier-gerbers.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(GER)):
            z.write(os.path.join(GER, f), f)

    with tempfile.TemporaryDirectory() as td:
        xml = os.path.join(td, "n.xml")
        run("kicad-cli", "sch", "export", "netlist", "--format", "kicadxml", "-o", xml, SCH)
        root = ET.parse(xml).getroot()
    groups = defaultdict(list)
    for c in root.iter("comp"):
        ref = c.get("ref")
        if ref.startswith("H"):
            continue
        fields = {f.get("name"): f.text for f in c.iter("field")}
        groups[(fields.get("MPN", c.findtext("value")), c.findtext("value"))].append(ref)
    key = lambda r: (r.rstrip("0123456789"), int(r[len(r.rstrip("0123456789")):]))
    with open(os.path.join(FAB, "bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Qty", "References", "Value", "Part"])
        for (mpn, val), refs in sorted(groups.items(), key=lambda kv: key(sorted(kv[1], key=key)[0])):
            w.writerow([len(refs), " ".join(sorted(refs, key=key)), val, mpn])
    print("gerbers:", len(os.listdir(GER)), "files | BOM lines:", len(groups))


if __name__ == "__main__":
    main()
