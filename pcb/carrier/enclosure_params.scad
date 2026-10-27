// Prints the enclosure geometry the PCB generator needs, so the board is always
// placed from the same numbers as the case. Used by gen_pcb.py:
//   openscad -D 'part="none"' -o params.echo enclosure_params.scad
include <../../enclosure/freeze_pedal_case.scad>

echo(PCB_PARAMS = [
  ["level_s", level_s], ["level_x", level_x],
  ["mid_s", mid_s], ["mid_pot_x", mid_pot_x], ["toggle_x", toggle_x],
  ["fs_s", fs_s], ["fs_x", fs_x], ["led_x", led_x], ["led_s", led_s],
  ["pcb_s0", pcb_s0], ["pcb_s1", pcb_s1], ["pcb_half_w", pcb_half_w],
  ["pcb_mounts", pcb_mounts], ["jack_x", jack_x], ["seed_x", seed_x],
  ["slope_len", slope_len], ["wall", wall], ["seed_len", seed_len]
]);
