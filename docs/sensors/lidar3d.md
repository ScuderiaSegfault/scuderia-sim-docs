# 3D LiDAR

A spinning multi-channel LiDAR. The default preset models the **RoboSense
Airy**, a hemispherical 3D LiDAR. It works on every map: on a plain 2D map the
walls are extruded to a fixed height; on a {doc}`2.5D map <../map_2p5d>` it
also sees bridge decks, ramps, side walls and banked ground.

```{figure} ../assets/map_2p5d_rviz.png
:alt: RViz: a car on the bridge deck and a car passing under the bridge, with the 3D LiDAR point cloud

The 3D LiDAR in RViz on the figure-8 bridge map. Left: the car is on the deck;
the dome, pointing forward, sees the deck, the side walls and the ramp down.
Right: one lobe later the car crosses under the bridge; its beams pass beneath
the deck and hit the far ramp.
```

## Presets

| preset | channels | elevation | horizontal resolution | range | rate | beams per frame |
|---|---|---|---|---|---|---|
| `airy` (default) | 96 | 0–90° (a hemisphere) | 0.4° (900 columns) | 0.1–60 m | 10 Hz | 86,400 |
| `airy_fast` | 48 | 0–90° | 0.8° | up to 30 m | 10 Hz | 21,600 (4× cheaper) |

All keys (in the `lidar3d:` block of the config, or as `lidar3d={...}`):

| key | default | meaning |
|---|---|---|
| `preset` | `airy` | `airy` or `airy_fast` |
| `agents` | `ego` | `ego` or `all` |
| `channels`, `elev_min_deg`, `elev_max_deg`, `h_res_deg` | from the preset | the beam pattern |
| `min_range`, `max_range` | from the preset | [m] |
| `rate_hz` | 10 | frames per simulated second; 0 = every step |
| `mount_x`, `mount_y`, `mount_z` | 0.10, 0, 0.20 | position in the car frame [m] |
| `mount_roll_deg`, `mount_pitch_deg`, `mount_yaw_deg` | 0, 90, 0 | orientation, $R = R_z(\text{yaw})\,R_y(\text{pitch})\,R_x(\text{roll})$ |
| `noise_std` | 0 | Gaussian range noise [m] |

## Mounting

The hemisphere is the sensor's $+z$ half-space. With `mount_pitch_deg: 90`
(the default) the dome points **forward**, so the sensor sees the floor, the
walls, the bridges and the cars ahead. With `0` it points straight up.

## How it works

Each beam is **ray-marched** through the 2.5D world:

- the floor (and banked ground),
- the map walls, extruded to the map wall height,
- every bridge deck, ramp and side wall,
- the other cars, as upright boxes at their own height.

Empty space is skipped with distance transforms. Far from anything, a beam
jumps by the 2D distance to the nearest occupied cell. Around the bridges the
skip is done per height band (about 5 cm): a beam jumps by the distance to
anything *in its own band*, so a deck far above or below does not slow it
down. Hits on a deck's top or underside are placed exactly where the beam
crosses that plane. The floor and car boxes are intersected in closed form.
Beams run in parallel (numba threads; on the GPU in the JAX twin).

## Output

```python
obs["lidar3d_ranges"]   # (n, 96, 900) float32 [m], 0 = no return; one row per ring
obs["lidar3d_points"]   # (n, 96*900, 3) float32, sensor frame
obs["lidar3d_new"]      # True on the steps a frame was taken
obs["lidar3d_stamp"]    # sim time of the frame [s]
```

## Timing

Like the real sensor, the 3D LiDAR takes a frame at 10 Hz, not at every
physics step. In RViz its points on a **moving** car can trail the car model
by up to 0.1 s (about 0.2 m at 2 m/s) until the next frame. This is the real
sensor's behaviour, not a lag in the simulator: the 2D scans, odometry and TF
are published together at the physics rate from one step with one stamp. To
see more frames, raise `rate_hz` (e.g. 20).

## Cost

A frame of the full Airy takes a few milliseconds on a laptop CPU on a map
with a bridge (more on a bridge over a bridge, where beams graze along side
walls). With the physics at 100 Hz and the LiDAR at 10 Hz, one car runs well
faster than real time. In the JAX twin on a GPU, one batched Airy scan costs
around a millisecond (see {doc}`../jax_twin`).

## In ROS 2

`/ego_racecar/lidar3d/points` — `sensor_msgs/PointCloud2` with fields
`x y z intensity ring` (intensity = range), frame `ego_racecar/lidar3d`, and a
static TF from `base_link` for the mount. Launch argument `lidar3d:=true`;
parameters `lidar3d_preset`, `lidar3d_rate_hz`, `lidar3d_mount_*`,
`lidar3d_noise_std`. A frame is about 1 MB. See {doc}`../ros2_bridge`.
