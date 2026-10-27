// Daisy freeze pedal — reinforced 3D-printed floor enclosure
// Wedge body (low at the front, tall at the back), optional plan taper
// (narrower at the front), flat removable bottom plate for a full rubber mat.
//
// Coordinates: X = width (left/right as seen by the player),
//              Y = depth (front edge y=0, back edge y=depth),
//              Z = up (floor z=0).
// Top-panel features are placed in "panel coordinates": x across, s = distance
// up the slope from the front edge. on_panel(x, s) puts you on the top surface
// with +Z pointing out of the panel.
//
// Print: shell upside down (top face on the bed, no supports needed inside
//        except bridges over jack holes); bottom plate flat.
// Material: PETG or ASA. 4+ perimeters, 40%+ gyroid infill, 100% around the
//           footswitch pads (use a modifier in the slicer).

// ── 0. Part switcher ────────────────────────────────────────────────
part = "assembly"; // [assembly, shell, plate, exploded]

// ── 1. Global constants ─────────────────────────────────────────────
$fn = 64;
eps = 0.01;

// ── 2. Fastener parameters (metric-fasteners skill) ─────────────────
m3_ins_d=4.6; m3_ins_l=6.2; m3_cl_d=3.4; m3_boss_d=8;
m3_cb_d=5.8;  m3_cb_h=3.5;

// ── 3. Primary dimensions ───────────────────────────────────────────
back_w   = 160;   // outer width at the back
front_w  = back_w; // outer width at the front (set smaller for a plan taper)
depth    = 150;   // front to back
plate_t  = 5;     // bottom plate (thick enough for M3 counterbores from below)
front_total = 35;                // overall front edge height incl. bottom plate
back_total  = 50;                // overall back edge height incl. bottom plate
h_front  = front_total - plate_t; // shell height at the front edge (above the bottom plate)
h_back   = back_total - plate_t;  // shell height at the back edge
wall     = 3;     // side / front / back walls
top_t    = 3.5;   // top panel thickness

slope    = atan((h_back - h_front) / depth);   // panel angle, ≈10.6°
slope_len= depth / cos(slope);

function w_at(y)   = front_w + (back_w - front_w) * y / depth;   // outer width at y
function ztop(y)   = plate_t + h_front + y * tan(slope);         // top surface z at y
function y_of(s)   = s * cos(slope);

// ── Controls (panel coordinates: x, s) ──────────────────────────────
// Top row: output levels, left→right as the player sees them
level_s   = 125;
level_x   = [-56, -28, 0, 28, 56];     // Dry, Loop, −8, +5, +8
// Middle row: Fade, Texture pots + two mini toggles
mid_s     = 92;
mid_pot_x = [-52, -24];                // Fade, Texture
toggle_x  = [14, 44];                  // Single/Multi, +5 up/down
// Footswitch row (Clear left, Freeze right), LED above Freeze
fs_s      = 32;    // footswitch clearance below panel is echoed at render
fs_x      = [-35, 35];
led_x     = 35;   led_s = 56;

// Hole sizes — VERIFY against the parts you buy
pot_hole  = 7.0;   // 6 mm plastic shaft, 0.5 mm clearance per side
toggle_hole = 6.5; // mini toggle, 1/4"-40 bushing
fs_hole   = 12.4;  // soft-touch footswitch, M12 bushing
led_hole  = 5.3;   // 5 mm LED or light pipe
led_recess_d = 9; led_recess_h = 1.5;  // shallow well so a shoe can't flatten it

// Kick ridge between the footswitch row and the knob rows
ridge_s   = 72;
ridge_w   = 6;
ridge_h   = 9;     // above panel surface

// Under-panel features
pot_collar_od = 12;  pot_collar_h = 2;      // bearing collar around each shaft
pot_body_h    = 7;                          // 9 mm pot body height — VERIFY
pcb_gap       = pot_body_h + pot_collar_h + 0.5;  // panel underside to carrier PCB top
fs_pad_od     = 30;  fs_pad_h = 1.5;        // thickens panel to top_t+1.5 at switches
                                            // check footswitch thread length vs this
col_size      = 8;                          // square support columns under switches
col_offset    = 20;                         // column centre distance from switch centre (X)
col_gap       = 0.2;                        // column foot clearance above bottom plate

// Carrier PCB mounting (hanging M3 standoffs, panel coordinates)
pcb_mounts = [[-66, 80], [66, 80], [-66, 138], [66, 138]];

// Bottom plate screws (world X, Y) — inside corners plus front/back centre
corner_in = m3_boss_d/2 - 0.5;   // boss centre inset from inner walls (boss fuses 0.5 mm into wall)
plate_screws = [
  [-(w_at(wall+corner_in)/2 - wall - corner_in), wall + corner_in],
  [  w_at(wall+corner_in)/2 - wall - corner_in,  wall + corner_in],
  [-(w_at(depth-wall-corner_in)/2 - wall - corner_in), depth - wall - corner_in],
  [  w_at(depth-wall-corner_in)/2 - wall - corner_in,  depth - wall - corner_in],
  [0, wall + corner_in],
  [0, depth - wall - corner_in]
];
plate_boss_h = 12;

// Back face (world X, height above plate top). Order as the player sees it.
jack_d    = 9.7;   // 3/8" bushing panel jacks (Switchcraft/Cliff style) — VERIFY
jack_z    = 15;    // centre height above plate top (keeps jack bodies under the carrier PCB)
jack_x    = [-60, -32, -4, 24];           // In L, In R, Out L, Out R
usb_x     = 54;  usb_z = 14;
usb_w     = 9.6; usb_h = 4.0; usb_r = 1.5;  // panel-mount USB-C cutout — VERIFY
usb_screw_sp = 0;                          // set to the module's hole spacing, 0 = none

// Note: the panel's true (perpendicular) thickness is top_t·cos(slope), so
// features that hang from the underside overlap 1 mm short of the face to fuse.

// Clearance under each footswitch: panel underside (incl. pad) down to the plate top
fs_clear = ztop(y_of(fs_s)) - plate_t - top_t - fs_pad_h;
echo(str("Footswitch clearance below panel: ", fs_clear, " mm (check switch body + lugs)"));
echo(str("Panel slope: ", slope, " deg"));

// ── 4. Helpers ──────────────────────────────────────────────────────
module on_panel(x, s) {
  translate([x, y_of(s), ztop(y_of(s))]) rotate([slope, 0, 0]) children();
}

module wedge(fw, bw, y0, y1, zb, inset_top=0) {
  // Trapezoid footprint from y0 to y1, flat bottom at zb, top following the slope.
  function hw(y) = (fw + (bw - fw) * y / depth) / 2;
  zt0 = ztop(y0) - inset_top;  zt1 = ztop(y1) - inset_top;
  polyhedron(
    points = [
      [-hw(y0), y0, zb], [hw(y0), y0, zb], [hw(y1), y1, zb], [-hw(y1), y1, zb],
      [-hw(y0), y0, zt0], [hw(y0), y0, zt0], [hw(y1), y1, zt1], [-hw(y1), y1, zt1]
    ],
    faces = [[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]
  );
}

module rrect2(w, h, r) { offset(r=r) square([w - 2*r, h - 2*r], center=true); }

// ── 5. Shell ────────────────────────────────────────────────────────
module shell() {
  // STEP 1 — outer body + ridge, minus cavity and every through-cut
  difference() {
    union() {
      wedge(front_w, back_w, 0, depth, plate_t);
      ridge_len = w_at(y_of(ridge_s)) - 2*wall - 8;
      on_panel(0, ridge_s)
        translate([-ridge_len/2, -ridge_w/2, -1]) cube([ridge_len, ridge_w, ridge_h + 1]);
    }
    // interior cavity, open at the bottom
    wedge(front_w - 2*wall, back_w - 2*wall, wall, depth - wall, plate_t - eps, top_t);

    // panel holes (cut long so they also clear collars/pads added later)
    for (x = level_x)   on_panel(x, level_s) translate([0,0,-20]) cylinder(d=pot_hole, h=30);
    for (x = mid_pot_x) on_panel(x, mid_s)   translate([0,0,-20]) cylinder(d=pot_hole, h=30);
    for (x = toggle_x)  on_panel(x, mid_s)   translate([0,0,-20]) cylinder(d=toggle_hole, h=30);
    for (x = fs_x)      on_panel(x, fs_s)    translate([0,0,-20]) cylinder(d=fs_hole, h=30);
    on_panel(led_x, led_s) {
      translate([0,0,-20]) cylinder(d=led_hole, h=30);
      translate([0,0,-led_recess_h]) cylinder(d=led_recess_d, h=led_recess_h + 1);
    }

    // back-wall jacks and USB-C
    for (x = jack_x)
      translate([x, depth + 1, plate_t + jack_z]) rotate([90,0,0]) cylinder(d=jack_d, h=wall + 2);
    translate([usb_x, depth + 1, plate_t + usb_z]) rotate([90,0,0])
      linear_extrude(wall + 2) rrect2(usb_w, usb_h, usb_r);
    if (usb_screw_sp > 0) for (sx = [-1,1])
      translate([usb_x + sx*usb_screw_sp/2, depth + 1, plate_t + usb_z]) rotate([90,0,0])
        cylinder(d=m3_cl_d, h=wall + 2);
  }

  // STEP 2 — interior features added after the main difference

  // bearing collars under each pot shaft (side loads go into the case, not the PCB)
  for (p = concat([for (x = level_x) [x, level_s]], [for (x = mid_pot_x) [x, mid_s]]))
    on_panel(p[0], p[1]) difference() {
      translate([0,0,-top_t - pot_collar_h]) cylinder(d=pot_collar_od, h=pot_collar_h + top_t - 1);  // overlaps 2.5 mm into the panel
      translate([0,0,-top_t - pot_collar_h - 1]) cylinder(d=pot_hole, h=pot_collar_h + 2);
    }

  // footswitch pads: thicken the panel locally
  for (x = fs_x) on_panel(x, fs_s) difference() {
    translate([0,0,-top_t - fs_pad_h]) cylinder(d=fs_pad_od, h=fs_pad_h + top_t - 1);
    translate([0,0,-top_t - fs_pad_h - 1]) cylinder(d=fs_hole, h=fs_pad_h + 2);
  }

  // footswitch support columns: panel underside straight down to the bottom plate
  for (x = fs_x, dx = [-col_offset, col_offset]) {
    y = y_of(fs_s);
    z0 = plate_t + col_gap;
    z1 = ztop(y - col_size/2) - top_t + 1;   // buried 1 mm into the panel at its low edge
    translate([x + dx - col_size/2, y - col_size/2, z0]) cube([col_size, col_size, z1 - z0]);
  }

  // carrier PCB standoffs hanging from the panel, insert pocket at the free end
  for (m = pcb_mounts) on_panel(m[0], m[1]) difference() {
    translate([0,0,-top_t - pcb_gap]) cylinder(d=m3_boss_d, h=pcb_gap + top_t - 1);
    translate([0,0,-top_t - pcb_gap - eps]) cylinder(d=m3_ins_d, h=m3_ins_l + eps);
  }

  // bottom-plate bosses rising from the shell's lower edge, inserts from below
  for (p = plate_screws) translate([p[0], p[1], plate_t]) difference() {
    cylinder(d=m3_boss_d, h=plate_boss_h);
    translate([0,0,-eps]) cylinder(d=m3_ins_d, h=m3_ins_l + eps);
  }
}

// ── 6. Bottom plate ─────────────────────────────────────────────────
module plate() {
  difference() {
    linear_extrude(plate_t)
      polygon([[-front_w/2, 0], [front_w/2, 0], [back_w/2, depth], [-back_w/2, depth]]);
    // counterbored M3 holes, heads entering from the floor side
    for (p = plate_screws) translate([p[0], p[1], 0]) {
      translate([0,0,-eps]) cylinder(d=m3_cl_d, h=plate_t + 2*eps);
      translate([0,0,-0.5]) cylinder(d=m3_cb_d, h=m3_cb_h + 0.5);
    }
  }
}

// ── 7. Render dispatch ──────────────────────────────────────────────
// shell: print upside down (panel face on the bed)
// plate: print flat
if (part == "assembly") {
  color("SeaGreen") shell();
  color("DimGray")  plate();
} else if (part == "exploded") {
  color("SeaGreen") translate([0, 0, 40]) shell();
  color("DimGray")  plate();
} else if (part == "shell") {
  shell();
} else if (part == "plate") {
  plate();
}
