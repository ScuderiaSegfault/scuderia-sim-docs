# Testing

Two tools test the whole stack the way a user drives it: **drive_check** in
Python and **run_test_drive** through ROS 2. Both drive 1–3 cars round a test
map on a pure-pursuit autopilot, in any mix of control modes, and check
**independently of the simulator's own code** that the cars drive and that
every sensor agrees with the map. Every test is one command and ends in
`PASS` or `FAIL`.

```{figure} assets/test_overview_sim.jpg
:alt: five test runs, each with a top view of the track and the ego camera, depth, labels and a top view of the 3D LiDAR
:width: 80%

One frame from each of five test runs (three cars, one per control mode): the
bunker track, the bunker with its bridge, ICRA 2026 tracks 1 and 2, and the
master cup with its bridge. Per run: the top view with the three cars, the ego
camera, its depth and labels, and the 3D LiDAR seen from above.
```

## The test maps

| alias | map | bridge |
|---|---|---|
| `bunker` | `bunker_v1` | — |
| `bunker_bridge` | `bunker_over_under_v1` | yes |
| `icra_t1` | `icra2026_t1_v1` | — |
| `icra_t2` | `icra2026_t2_v1` | — |
| `mastercup` | `master_cup_bridge_v1` | yes |
| `figure8` | `figure8_bridge_v1` | yes |
| `trefoil` | `trefoil_bridges_v1` | yes (two levels) |
| `banked` | `banked_oval_v1` | banks (Python only) |

Each test map has a centreline for the autopilot ({doc}`maps`).

## drive_check (Python)

Drives the cars by pure pursuit along the centreline, car 0 in front, the
others a gap behind. Every car can have its own control mode.

```bash
python3 examples/drive_check.py --map bunker --ctrl current                 # one car, current control
python3 examples/drive_check.py --map icra_t1 --cars 2 --ctrl accl --speed 2.5
python3 examples/drive_check.py --map bunker_bridge --cars 3 --ctrl speed,accl,current --video
python3 examples/drive_check.py --map icra_t2 --cars 2 --camera-preset oakd_s2
```

Options: `--map`, `--cars` (1–3), `--ctrl` (one mode, or one per car),
`--model` (`st` / `std`), `--speed`, `--gap`, `--laps`, `--sensors` (`all`,
`lidar`, or a list of `lidar,lidar3d,camera`), `--camera-preset`, `--video`.

How the autopilot makes each command:

| `--ctrl` | command sent | made by |
|---|---|---|
| `speed` | target speed | the simulator's speed controller |
| `accl` | acceleration | a PI speed controller in the test script |
| `current` | motor current | that acceleration converted with the motor model, clipped to the motor's continuous rating |

### The checks

| check | when | passes if |
|---|---|---|
| `no_collision` | always | no car collides |
| `all_cars_drove` | always | every car made at least half the requested laps |
| `speed_tracked` | always | median speed error after the start, while not slowed by a car ahead, is small for every car |
| `lidar2d_matches_map` | 2D LiDAR | the scan, re-cast independently on the map image, agrees for > 90 % of beams within 10 cm + 2 % of range |
| `lidar2d_sees_cars` | ≥ 2 cars | a car 0.5–4 m ahead in the field of view shows up in the scan at its distance |
| `lidar2d_on_car_box_same_step` | ≥ 2 cars | **no-lag check**: scan points on another car lie on that car's box *from the same step* (mean < 1 cm; measured: 0) |
| `camera_floor_depth_consistent` | camera | floor-labelled pixels, projected with their depth, land on the floor plane |
| `camera_wall_depth_consistent` | camera | wall-labelled pixels land next to a map wall |
| `camera_car_depth_consistent` | camera, ≥ 2 cars | car-labelled pixels land next to another car |
| `camera_sees_floor_and_walls` | camera | both labels appear |
| `lidar3d_points_on_map` | 3D LiDAR | > 95 % of points lie on the floor, a wall, a car or a bridge |
| `lidar3d_sees_deck_from_under` | passed under a deck | points overhead while under the bridge |
| `drove_onto_a_deck` | map with a deck | the car reached level 1 or higher |

The geometry checks (2D LiDAR, camera, 3D LiDAR) run on level ground; on a
ramp or deck the bridge checks apply instead.

Output per run: `report.json` (every number above, real-time factor, levels
driven, time under a bridge), `summary.png` (speed and command per car), and
with `--video` a `drive.mp4` with top view, ego camera, depth, labels and 3D
LiDAR.

### The matrix

`run_drive_matrix.sh` runs all test maps × car counts × control modes: per map,
three cars with one mode each and every sensor plus a video, then for each
mode one car (2D LiDAR) and two cars (2D LiDAR + camera). `QUICK=1` runs only
the three-car run per map. The result table has one `PASS`/`FAIL` line per run.

## run_test_drive (ROS 2)

The same through ROS 2, with RViz:

```bash
bash tools/run_test_drive.sh                                         # bunker bridge, 1 car, speed
TRACK=icra_t1 CARS=3 CTRL=speed,accl,current bash tools/run_test_drive.sh
TRACK=mastercup CARS=3 CTRL=speed,accl,current CHECK=60 bash tools/run_test_drive.sh
CHECK=40 RVIZ=0 TRACK=bunker_bridge CARS=3 bash tools/run_test_drive.sh   # headless
```

| variable | default | meaning |
|---|---|---|
| `TRACK` | `bunker_bridge` | test map alias |
| `CARS` | 1 | 1–3 |
| `CTRL` | `speed` | one mode for all, or one per car |
| `SPEED`, `GAP` | 2.0 m/s, 2.0 m | autopilot speed and start gap |
| `LIDAR3D`, `CAMERA` | `true` | ego sensors |
| `RVIZ` | 1 | 0 = no RViz |
| `CHECK` | — | run the sensor check for this many seconds, print PASS/FAIL, stop |
| `OUT` | `./test_drive_out` | report and sample frames |
| `RECORD` | 0 | 1 = record the RViz window to a video while checking |

The script starts the bridge, the map server, the car models, RViz, the
`autopilot` node and — with `CHECK` — the `sensor_check` node. Maps with a
`map_2p5d:` block switch on 2.5D automatically. Stop with Ctrl+C: the autopilot
sends zero commands first, so the cars stop.

### sensor_check

Listens to the running bridge and checks:

| check | passes when |
|---|---|
| `odometry_arrives` | odometry messages come in |
| `car<i>_odom_rate` | odometry faster than 50 Hz |
| `car<i>_drives` | the car moves a reasonable distance |
| `car<i>_not_stuck` | never stopped for 3 s once it was rolling |
| `car<i>_scan` | 2D scan faster than 20 Hz, > 90 % finite ranges, plausible closest range |
| `cars_never_overlap` | no two cars at the same height overlap |
| `scan_on_other_car_box_same_stamp` | **no-lag check through ROS**: scan points on another car lie on its box from the odometry with the same stamp (mean < 1 cm; measured about 1.5 mm) |
| `camera_rate`, `camera_image_not_blank`, `camera_depth_valid`, `camera_labels_floor_wall` | camera topics arrive and make sense |
| `lidar3d_rate`, `lidar3d_points` | point clouds arrive with enough points |
| `bridge_markers` | bridge markers received |
| `ego_went_up_a_ramp` | the ego's odometry height rose onto the deck |

It writes `report.json` and one camera, depth and label frame. Exit code 0
only if all checks passed.

## Known effects (not bugs)

- **3D LiDAR at 10 Hz:** in RViz, its points on a moving car trail the car
  model by up to 0.1 s until the next frame — as with the real sensor. The 2D
  scan, odometry and TF come from one step with one stamp.
- **2D LiDAR vs a cell-exact cast:** the simulator marches to the wall cell,
  the independent check casts to its edge, so ranges differ by about one cell;
  hence the tolerance.
- **The floor beyond the map edge** is an infinite plane; a camera high on a
  deck can see floor pixels with very large depth past the map. The checks
  only use nearby floor pixels.
- **Equal target speeds, different controllers** settle at slightly different
  speeds — gap keeping is needed ({doc}`control_modes`).

## Reporting a problem

Include the exact command (with environment variables), the version of each
repository, `report.json` and the video of the run (`--video` or `RECORD=1`),
and what you expected versus what you saw (time in the video, car number).
