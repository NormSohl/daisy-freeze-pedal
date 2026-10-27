# Daisy Freeze Pedal

A line-level stereo freeze/drone floor pedal built on the Electrosmith Daisy Seed, designed for playing hands-free alongside a WARBL wind controller or analog synths. Hold a footswitch to record, release to loop; the loop plays back as a Clouds-style granular freeze with sub-octave, fifth and octave voices.

![Enclosure, front view](enclosure/renders/front.png)

## Status

Prototyping. The DSP and control scheme are validated in a browser bench model; the enclosure has a first-pass parametric model. Next: validate the panel on the bench, then draw the carrier schematic.

## Panel

| Control | Type | Function |
|---|---|---|
| Freeze | Soft-touch momentary footswitch | Hold to record (up to 8 s), release to start looping |
| Clear | Soft-touch momentary footswitch | Tap: fade out the oldest layer. Hold 0.7 s: clear all |
| Dry | Pot | Passthrough level |
| Loop | Pot | Frozen 1:1 voice level |
| −8 | Pot | Sub-octave voice (1:2), 28 Hz high-pass |
| +5 | Pot | Fifth voice, 3:2 up or 3:4 down |
| +8 | Pot | Octave voice (2:1) |
| Fade | Pot | Layer swell-in and release time, 20 ms to 8 s |
| Texture | Pot | Macro: grain size, window shape and density, smooth → grainy |
| Single / Multi | Toggle | Single crossfades each capture over the last loop; Multi stacks up to 6 layers |
| +5 up / down | Toggle | Fifth above (3:2) or below (3:4) |
| LED | Bi-color | Red while recording, green while layers play, off when empty |

Fixed in firmware: grain spread, drift (random per-grain detune), output level. No reverb.

## I/O and power

- Four switched 1/4" jacks on the back face: In L/Mono, In R, Out L/Mono, Out R.
  - Nothing in In R: In L is normalled to both channels.
  - Nothing in Out R: L+R is summed to Out L (detected on a GPIO via the jack switch).
- Line level in and out; no instrument buffer needed. Optional input pad/trim for hot +4 dBu sources.
- USB-C on the back for 5 V power and firmware updates. Holding Clear at power-up will jump to the bootloader so the case never needs opening to flash.

## Hardware plan

- **Daisy Seed** socketed on a custom 2-layer carrier PCB mounted parallel to the panel.
- **Carrier** holds the seven 9 mm PCB-mount pots (plastic shafts), LED, audio coupling caps and pad, and headers for the jacks, footswitches, toggles and USB-C.
- **Enclosure**: reinforced 3D-printed wedge, PETG or ASA. See [`enclosure/`](enclosure/).

## Repository layout

```
bench/index.html                 Browser prototype of the pedal (AudioWorklet DSP + simulated synth input)
enclosure/freeze_pedal_case.scad Parametric OpenSCAD enclosure
enclosure/stl/                   shell.stl, plate.stl (first pass, renders manifold)
enclosure/renders/               Front, side and underside views
```

## Bench prototype

Open `bench/index.html` in a browser (Chrome, Safari or Firefox). Power on, start the melody or play the keyboard, then hold Freeze. The DSP engine is written as a plain class so it ports to DaisySP C++ almost line for line:

- 8 s stereo ring buffer, record buffer preallocated (no allocation on the audio thread at capture)
- Grains read with Hermite interpolation; voices above 1:1 read a copy low-passed at 0.2·fs to avoid aliasing
- Up to 6 layers, each with its own fade envelope; 4 voices per layer
- tanh soft clip at the output

## Enclosure

- Wedge: 34 mm at the front rising to 62 mm at the back (≈10.6°), 150 mm deep; 140 mm wide at the front, 160 mm at the back (set `front_w = back_w` for a plain wedge).
- Flat 5 mm removable bottom plate for a full rubber mat; six M3 SHCS counterbored from below into Ruthex heat-set inserts.
- Each footswitch: thickened panel pad plus two 8 × 8 mm columns straight down to the bottom plate, so stomps load the floor rather than the panel.
- Bearing collars around pot shafts; 9 mm kick ridge between the footswitches and the knobs; recessed LED well.
- Print the shell upside down (panel face on the bed). 4+ perimeters, 40%+ gyroid, 100% infill around the footswitch pads.

Dimensions marked `VERIFY` in the SCAD file depend on the parts you buy: pot body height, footswitch thread length, jack bushing size, USB-C panel module cutout.
