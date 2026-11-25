# Maps

A map is an occupancy-grid image with a YAML file next to it — the same format
the ROS `map_server` uses, so maps recorded with SLAM on the real car work
directly.

```yaml
image: my_track.png       # black = wall, white = free
mode: trinary
resolution: 0.05          # metres per pixel
origin: [-3.65, -1.5, 0.0]  # map frame position of the lower-left pixel (x, y, yaw)
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
# optional: bridges and banks, see "2.5D maps"
map_2p5d:
  bridges: [...]
```

Pass the YAML path (with or without `.yaml`) or the name of a shipped map as
`map=`. A `map_2p5d:` block is ignored unless 2.5D is switched on, so the same
file also works as a plain 2D map.

## Centrelines

Test maps come with a `<map>_centreline.csv`: the track centre as `x, y`
points, a closed loop in the driving direction. The autopilots of the test
tools follow it, and you can use it as a reference line for your own
controller. A tool that extracts a centreline from a new map image (given a
start pose on the track) is part of the release.

## Shipped maps

| map | what it is | 2.5D | centreline |
|---|---|---|---|
| `vegas`, `berlin`, `skirk`, `stata_basement`, `levine` | classic F1TENTH maps | — | — |
| `curvy_corridor_v1`, `icra_t2_corridor_v1` | synthetic corridors (the second is *not* the real ICRA track) | — | — |
| `bunker_v1` | the bunker track, ground loop only | — | yes |
| `icra2026_t1_v1` | ICRA 2026 track 1, SLAM map | — | yes |
| `icra2026_t2_v1` | ICRA 2026 track 2, SLAM map | — | yes |
| `bunker_over_under_v1` | the bunker track **with its bridge**: over the deck, under it through an S-bend | bridge | yes |
| `master_cup_bridge_v1` | the ICRA 2026 master cup track **with its bridge** over a hairpin | bridge | yes |
| `figure8_bridge_v1` | synthetic figure-8 whose crossing is a bridge | bridge | yes |
| `trefoil_bridges_v1` | synthetic: three roads through one point — ground, a bridge, and a bridge over that bridge | 2 bridge levels | yes |
| `banked_oval_v1` | synthetic oval with both curves banked at 15° | banks | yes |

```{figure} assets/map_2p5d_real_tracks.png
:alt: the bunker and master cup bridge maps with one autopilot lap each, coloured by height, and the camera on and under the deck

The two real tracks with bridges: the bunker over/under track (top) and the
ICRA 2026 master cup (bottom). One autopilot lap each, coloured by the car's
height; red where the car drives under the deck. Left: the on-board camera on
the deck and under it.
```

```{note}
The bridge heights of the two real tracks were not measured; both decks are
modelled at a height that clears the ground walls. Change `height:` in the map
YAML if you know the real value.
```

## Test aliases

The test tools use short names:

| alias | map |
|---|---|
| `bunker` | `bunker_v1` |
| `bunker_bridge` | `bunker_over_under_v1` |
| `icra_t1` | `icra2026_t1_v1` |
| `icra_t2` | `icra2026_t2_v1` |
| `mastercup` | `master_cup_bridge_v1` |
| `figure8` | `figure8_bridge_v1` |
| `trefoil` | `trefoil_bridges_v1` |
| `banked` | `banked_oval_v1` (Python test tool only) |

## Your own map

1. Record a map with SLAM on your car (or draw one): a black-and-white image
   and a `map_server` YAML.
2. Clean it up in an image editor if needed (close gaps in the walls).
3. Generate a centreline for the autopilots.
4. Optionally add bridges or banks — see {doc}`map_2p5d`.
