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
// Everything except the two footswitches lives on one carrier PCB parallel to
// the panel: pots, toggles and LED on its top side; the Daisy Seed and the four
// right-angle 1/4" jacks on its underside along the rear edge. The back wall is
// perpendicular to the panel so the jacks meet it square, and the jack/USB
// openings are slots open at the bottom: the board slides up into the shell,
// then the jack nuts clamp it to the wall from outside.
//
// Print: shell face down. The panel face is completely flat (no ridges or
//        recesses) and the back wall is square to it, so it prints with no
//        supports; jack slots print as upright U-shapes. Bottom plate flat.
// Material: PETG or ASA. 4+ perimeters, 40%+ gyroid infill, 100% around the
//           footswitch pads (use a modifier in the slicer).

// ── 0. Part switcher ────────────────────────────────────────────────
part = "assembly"; // [assembly, shell, plate, carrier, exploded]

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

slope    = atan((h_back - h_front) / depth);   // panel angle
slope_len= depth / cos(slope);

function w_at(y)   = front_w + (back_w - front_w) * y / depth;   // outer width at y
function ztop(y)   = plate_t + h_front + y * tan(slope);         // top surface z at y
function y_of(s)   = s * cos(slope);
// Back wall is perpendicular to the panel, so its foot sits behind y=depth
depth_b  = depth + (ztop(depth) - plate_t) * tan(slope);   // footprint depth at the floor

// ── Controls (panel coordinates: x, s) ──────────────────────────────
// Top row: output levels, left→right as the player sees them
level_s   = 121;   // pot bodies clear the jack pins coming through from the underside
level_x   = [-64, -32, 0, 32, 64];     // Dry, Loop, −8, +5, +8 (Seed pins pass between +5 and +8)
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
toggle_hole = 6.5; // E-Switch 100-series 1/4"-40 bushing (datasheet panel hole 6.35)
fs_hole   = 12.4;  // soft-touch footswitch, M12 bushing
led_hole  = 5.3;   // 5 mm LED or light pipe


// Under-panel features
pot_body_h    = 7.6;                        // Alpha RV09AF-40: 6.8 body + 0.8 front boss (datasheet p.3);
                                            // shaft length L is measured from the PCB seating plane
toggle_body_h = 8.89 + 1.5;                 // E-Switch 100SP1T1B1M2QE: single-pole body 8.89 (catalog p.2)
                                            // + 1.5 pin standoff (M2 drawing p.8: 6.60 - 5.10) = PCB to bushing base
toggle_bush_l = 8.89;                       // B1 threaded 1/4-40 bushing length
pcb_gap       = max(pot_body_h + 0.5, toggle_body_h);  // toggles set the gap: bushing base seats on the panel underside
toggle_pad_h  = pcb_gap - toggle_body_h;    // underside pad so each toggle body seats on the panel
toggle_pad_od = 12;
fs_pad_od     = 30;  fs_pad_h = 1.5;        // thickens panel to top_t+1.5 at switches
                                            // check footswitch thread length vs this
col_size      = 8;                          // square support columns under switches
col_offset    = 20;                         // column centre distance from switch centre (X)
col_gap       = 0.2;                        // column foot clearance above bottom plate

// Carrier PCB (panel coordinates). Footswitches stay off the board: they are
// nutted to the panel and wired to 2-pin locking connectors on the carrier.
pcb_t       = 1.6;
pcb_s0      = 47;                               // front edge, behind the footswitch bodies
pcb_s1      = slope_len - wall - 0.5;           // rear edge, 0.5 mm off the back wall
pcb_half_w  = back_w/2 - wall - 1;
pcb_mounts  = [[-70, 62], [70, 62], [-70, 138], [70, 138]];   // hanging M3 standoffs
pcb_bot_z   = -(top_t + pcb_gap + pcb_t);       // carrier underside, panel frame

// Underside parts on the rear edge — VERIFY against the parts you buy
jack_axis_below = 15.67 - 8.14;  // Neutrik NMJ6HCD2 drawing: body 15.67 tall, axis 8.14 below its top = 7.53 from the PCB
jack_body = [18.2, 23.53, 15.67];  // NMJ6HCD2 body w, length behind the panel flange, height
seed_hdr_h  = 8.5;       // female header height
seed_len = 51; seed_w = 18; seed_t = 1.6;       // Daisy Seed3 (datasheet v2.1 p.8)
seed_spacer = 2.5;                               // male-header plastic spacer under the Seed3
seed_usb_h  = 3.25;                              // Seed3 USB-C receptacle height; overhangs the board end by 1.55
seed_x   = 48;                                   // Seed centre X; its micro-USB faces the back wall
usb_axis_below = seed_hdr_h + seed_spacer + seed_t + seed_usb_h/2;   // USB-C axis below the carrier underside

// Bottom plate screws (world X, Y) — inside corners plus front/back centre
corner_in = m3_boss_d/2 - 0.5;   // boss centre inset from inner walls (boss fuses 0.5 mm into wall)
back_boss_y = depth_b - wall / cos(slope) - corner_in;   // fuses to the leaning back wall
plate_screws = [
  [-(w_at(wall+corner_in)/2 - wall - corner_in), wall + corner_in],
  [  w_at(wall+corner_in)/2 - wall - corner_in,  wall + corner_in],
  [-(back_w/2 - wall - corner_in), back_boss_y],
  [  back_w/2 - wall - corner_in,  back_boss_y],
  [0, wall + corner_in],
  [6, back_boss_y]                     // between Out L and Out R so it clears the jack slots
];
plate_boss_h = 10;

// Back face. X as the player sees it (In L at far left).
jack_d    = 11.4;  // NMJ6HCD2 panel cut-out (datasheet); nut A/F 11
jack_x    = [-48, -14, 12];              // In (mono), Out L, Out R
usb_open  = [14, 9];                     // USB-C plug overmould clearance (w, h); many overmoulds are 12–12.5 mm wide

// Note: the panel's true (perpendicular) thickness is top_t·cos(slope), so
// features that hang from the underside overlap 1 mm short of the face to fuse.

// Clearance under each footswitch: panel underside (incl. pad) down to the plate top
fs_clear = ztop(y_of(fs_s)) - plate_t - top_t - fs_pad_h;
echo(str("Footswitch clearance below panel: ", fs_clear, " mm (check switch body + lugs)"));
echo(str("Panel slope: ", slope, " deg"));
pot_shaft_l = 25;                         // Alpha RV09AF-40-25K: L measured from the PCB
led_h = 8.6; led_spacer = pcb_gap + top_t - led_h - 0.3;   // 5 mm LED on a spacer, dome 0.3 mm below the panel top
echo(str("Pot shaft above panel: ", pot_shaft_l - pcb_gap - top_t, " mm"));
echo(str("LED spacer length: ", led_spacer, " mm"));
echo(str("Board gap under panel: ", pcb_gap, " mm"));
echo(str("Toggle thread above panel: ", toggle_bush_l - toggle_pad_h - top_t, " mm (1/4-40 nut ≈2.4 mm)"));
echo(str("Seed3 bottom (USB-C face) below carrier: ", usb_axis_below + seed_usb_h/2, " mm"));

// ── 4. Helpers ──────────────────────────────────────────────────────
module on_panel(x, s) {
  translate([x, y_of(s), ztop(y_of(s))]) rotate([slope, 0, 0]) children();
}

module wedge(fw, bw, y0, y1, zb, inset_top=0) {
  // Footprint from y0 to y1, flat bottom at zb, top following the slope.
  // The back face is perpendicular to the panel, so its foot sits behind y1.
  function hw(y) = (fw + (bw - fw) * y / depth) / 2;
  zt0 = ztop(y0) - inset_top;  zt1 = ztop(y1) - inset_top;
  y1b = y1 + (zt1 - zb) * tan(slope);
  polyhedron(
    points = [
      [-hw(y0), y0, zb], [hw(y0), y0, zb], [hw(y1), y1b, zb], [-hw(y1), y1b, zb],
      [-hw(y0), y0, zt0], [hw(y0), y0, zt0], [hw(y1), y1, zt1], [-hw(y1), y1, zt1]
    ],
    faces = [[0,1,2,3],[4,7,6,5],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]
  );
}

module rrect2(w, h, r) { offset(r=r) square([w - 2*r, h - 2*r], center=true); }

// ── 5. Shell ────────────────────────────────────────────────────────
module shell() {
  // STEP 1 — outer body, minus cavity and every through-cut
  difference() {
    union() {
      wedge(front_w, back_w, 0, depth, plate_t);
    }
    // interior cavity, open at the bottom
    wedge(front_w - 2*wall, back_w - 2*wall, wall, depth - wall*cos(slope) + top_t*sin(slope)*cos(slope), plate_t - eps, top_t);  // puts the inner back face exactly wall-thick, perpendicular to the panel

    // panel holes (cut long so they also clear the footswitch pads added later)
    for (x = level_x)   on_panel(x, level_s) translate([0,0,-20]) cylinder(d=pot_hole, h=30);
    for (x = mid_pot_x) on_panel(x, mid_s)   translate([0,0,-20]) cylinder(d=pot_hole, h=30);
    for (x = toggle_x)  on_panel(x, mid_s)   translate([0,0,-20]) cylinder(d=toggle_hole, h=30);
    for (x = fs_x)      on_panel(x, fs_s)    translate([0,0,-20]) cylinder(d=fs_hole, h=30);
    on_panel(led_x, led_s) {
      translate([0,0,-20]) cylinder(d=led_hole, h=30);
    }

    // back-wall slots for the board-mounted jacks and the Seed's micro-USB,
    // open toward the bottom so the carrier can slide up into place
    on_panel(0, 0) {
      for (x = jack_x) translate([x, slope_len - wall - 1, pcb_bot_z - jack_axis_below]) {
        rotate([-90,0,0]) cylinder(d=jack_d, h=wall + 2);
        translate([-jack_d/2, 0, -60]) cube([jack_d, wall + 2, 60]);
      }
      translate([seed_x, slope_len - wall - 1, pcb_bot_z - usb_axis_below]) {
        translate([-usb_open[0]/2, 0, -usb_open[1]/2]) cube([usb_open[0], wall + 2, usb_open[1]]);
        translate([-usb_open[0]/2, 0, -60]) cube([usb_open[0], wall + 2, 60]);
      }
    }
  }

  // STEP 2 — interior features added after the main difference

  // toggle pads: the toggle body seats on these, its nut clamps from above
  if (toggle_pad_h > 0.05) for (x = toggle_x) on_panel(x, mid_s) difference() {
    translate([0,0,-top_t - toggle_pad_h]) cylinder(d=toggle_pad_od, h=toggle_pad_h + top_t - 1);
    translate([0,0,-top_t - toggle_pad_h - 1]) cylinder(d=toggle_hole, h=toggle_pad_h + top_t + 2);
  }

  // footswitch pads: thicken the panel locally
  for (x = fs_x) on_panel(x, fs_s) difference() {
    translate([0,0,-top_t - fs_pad_h]) cylinder(d=fs_pad_od, h=fs_pad_h + top_t - 1);
    translate([0,0,-top_t - fs_pad_h - 1]) cylinder(d=fs_hole, h=fs_pad_h + top_t + 2);   // bore through pad and panel
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
      polygon([[-front_w/2, 0], [front_w/2, 0], [back_w/2, depth_b], [-back_w/2, depth_b]]);
    // counterbored M3 holes, heads entering from the floor side
    for (p = plate_screws) translate([p[0], p[1], 0]) {
      translate([0,0,-eps]) cylinder(d=m3_cl_d, h=plate_t + 2*eps);
      translate([0,0,-0.5]) cylinder(d=m3_cb_d, h=m3_cb_h + 0.5);
    }
  }
}

// ── 7. Carrier PCB (reference geometry for fit checks, not printed) ──
module carrier() {
  on_panel(0, 0) {
    // board
    color("Goldenrod") translate([-pcb_half_w, pcb_s0, pcb_bot_z]) cube([2*pcb_half_w, pcb_s1 - pcb_s0, pcb_t]);
    // jacks on the underside, mouths flush with the inside of the back wall
    color("DimGray") for (x = jack_x)
      translate([x - jack_body[0]/2, pcb_s1 - jack_body[1], pcb_bot_z - jack_body[2]]) cube(jack_body);
    // Daisy Seed hanging on headers, micro-USB end at the rear edge
    color("RoyalBlue") translate([seed_x - seed_w/2, pcb_s1 - seed_len, pcb_bot_z - seed_hdr_h - seed_spacer - seed_t])
      cube([seed_w, seed_len, seed_t]);
    color("Silver") translate([seed_x - 4.17, pcb_s1 - 6, pcb_bot_z - usb_axis_below - seed_usb_h/2])
      cube([8.34, 7.55, seed_usb_h]);                       // USB-C, 1.55 past the Seed board end
    color("Black") for (dx = [-seed_w/2 + 1.3, seed_w/2 - 3.8])
      translate([seed_x + dx, pcb_s1 - seed_len + 1, pcb_bot_z - seed_hdr_h]) cube([2.5, seed_len - 2, seed_hdr_h]);
  }
}

// ── 8. Render dispatch ──────────────────────────────────────────────
// shell: print upside down (panel face on the bed)
// plate: print flat
if (part == "assembly") {
  color("SeaGreen") shell();
  color("DimGray")  plate();
  carrier();
} else if (part == "exploded") {
  color("SeaGreen") translate([0, 0, 40]) shell();
  color("DimGray")  plate();
} else if (part == "shell") {
  shell();
} else if (part == "plate") {
  plate();
} else if (part == "carrier") {
  carrier();
}
