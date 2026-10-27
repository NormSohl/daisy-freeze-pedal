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
- The Daisy Seed's own micro-USB faces the back wall for 5 V power and firmware updates. Holding Clear at power-up will jump to the bootloader so the case never needs opening to flash.

## Hardware plan

- **One carrier PCB** mounted parallel to the panel carries everything except the footswitches:
  - Top side: seven 9 mm PCB-mount pots (plastic shafts), two PCB-mount mini toggles, LED under a light pipe.
  - Underside, rear edge: four right-angle 1/4" jacks with threaded bushings (nutted to the back wall so plug forces go into the case) and the Daisy Seed on female headers, its micro-USB facing the back wall.
- **Footswitches** are nutted to the panel and wired to 2-pin locking connectors on the carrier; stomps never load solder joints.
- **Enclosure**: reinforced 3D-printed wedge, PETG or ASA. See [`enclosure/`](enclosure/).

## Parts chosen so far

| Part | Choice | Notes |
|---|---|---|
| Pots (×7) | [Alpha RV09AF-40-20K-B10K](https://www.jameco.com/z/RV09AF-40-20K-B10K-Taiwan-Alpha-9mm-Linear-Taper-Potentiometer-10K-Ohm-50mW-20-20mm-Long-Vertical-Knurled-Shaft_2272207.html) (Jameco 2272207): 9 mm, vertical PCB mount, 20 mm knurled plastic shaft, B10K linear | 7.0 mm mounting height. Used bare, no knobs or caps: the knurled shaft is the grip, with a painted index line across its top face. |
| Toggles (×2) | E-Switch 100SP1T1B4M2QE, PCB-mount SPDT on-on, 1/4"-40 bushing | 8.89 mm body sets the board-to-panel gap; the body seats against the panel underside and the nut clamps from above. |
| Footswitches (×2) | Soft-touch momentary SPST, M12 bushing | Panel-mounted, wired to the carrier. |

Board stack: carrier top 8.9 mm under the panel, panel 3.5 mm, so a 20 mm shaft clears the panel by about 7.6 mm if L is measured from the PCB seating plane (about 14.6 mm if from the body top), enough to grip the bare shaft either way; trim if needed. VERIFY against the datasheet before ordering.

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

- Wedge, front to back only: 35 mm overall at the front rising to 50 mm at the back (≈5.7° panel), 150 mm deep, 160 mm wide. ≈28 mm of clearance under the panel at the footswitches (the model echoes this value); jacks sit low on the back wall so their bodies pass under the carrier PCB.
- Flat 5 mm removable bottom plate for a full rubber mat; six M3 SHCS counterbored from below into Ruthex heat-set inserts.
- Each footswitch: thickened panel pad plus two 8 × 8 mm columns straight down to the bottom plate, so stomps load the floor rather than the panel.
- Panel face is completely flat (no ridges or recesses) so the shell prints face-down without supports; the back wall, square to the panel, prints vertical. The carrier sits 7.5 mm under the panel and the panel holes bear the pot shafts.

![Section through a jack](enclosure/renders/section.png)
- Back wall is perpendicular to the panel so the board-mounted jacks meet it square. Jack and USB openings are slots open at the bottom: the carrier slides up into the shell, then the jack nuts clamp it to the wall.
- `part = "carrier"` renders the board, jacks and Seed as reference geometry for fit checks.
- Print the shell face down (panel face on the bed). 4+ perimeters, 40%+ gyroid, 100% infill around the footswitch pads.

Dimensions marked `VERIFY` in the SCAD file depend on the parts you buy: pot body height, footswitch thread length, jack bushing size, USB-C panel module cutout.
