# Camera

An on-board camera per car. Every frame gives three images from one render:

- an **image**, RGB or mono,
- **depth** in metres,
- **semantic labels**, one class id per pixel.

The camera sees the track barriers (as round tubes or flat walls), the floor,
every other car as a 3D body on four wheels, the bridges of a 2.5D map, and its
own car's bumper and front tyres, which turn with the steering.

```{figure} ../assets/camera_comparison.png
:alt: RGB, mono and depth on top; labels, event camera and a top-down view below

One moment of every camera output: an opponent ahead in RGB, mono and depth
(top row), and in the labels, the event camera and a top-down view with the
ego in red (bottom row). The ego's own front tyres show at the bottom of the
camera images.
```

## Using it

```python
env = gym.make("scuderia-v0", map=..., num_agents=3, produce_camera=True,
               camera={"width": 320, "height": 192, "color": "mono"},
               disable_env_checker=True).unwrapped
obs, *_ = env.reset(poses)
obs["camera_image"]   # (n, H, W, 3) uint8, or (n, H, W, 1) with color: mono
obs["camera_depth"]   # (n, H, W) float32 [m], 0 = nothing hit
obs["camera_label"]   # (n, H, W) uint8 class ids
obs["camera_stamp"]   # sim time of the frame [s]
obs["camera_new"]     # True on the steps a frame was rendered
```

`n` is the number of cars with a camera: every car, or only the ego with
`agents: ego` (what the ROS bridge uses).

## Lens models

| `model` | lens | notes |
|---|---|---|
| `fisheye` (default) | equidistant fisheye | default 180° horizontal field of view, a wide bonnet camera |
| `pinhole` | ideal pinhole | e.g. 66° for the OAK-D S2 colour camera |
| `opencv_fisheye` | calibrated OpenCV fisheye | give `K` and `D` from your calibration |

Pixel rays are computed once, when the camera is created, so a calibrated lens
or an unusual mount costs nothing per frame.

## Configuration

The `camera:` block of the config file (or `camera={...}` to override single
keys):

| key | default | meaning |
|---|---|---|
| `agents` | `all` | `all` or `ego` |
| `width`, `height` | 160, 96 | image size [px]; the ROS bridge uses 320 × 192 |
| `rate_hz` | 30 | frames per simulated second; 0 = every step |
| `model`, `hfov_deg` | `fisheye`, 180 | lens and horizontal field of view |
| `mount_x`, `mount_y`, `mount_height` | 0.16, 0, 0.15 | position in the car frame [m] |
| `pitch_deg`, `yaw_deg`, `roll_deg` | −12, 0, 0 | negative pitch looks down, positive yaw looks left |
| `show_ego` | `true` | draw the own bumper and front tyres |
| `color` | `rgb` | `rgb` or `mono` (the luma, as a monochrome sensor records it) |
| `falloff_distance`, `ambient` | 3.0, 0.2 | brightness falls off with distance along the ray |
| `wall_height` | 0.25 | barrier height [m] |
| `wall_style` | `tubes` | `tubes` (barrier tubes) or `plain` (see below) |
| `bridge_style` | `wood` | `wood` or `plain` (see below) |
| `tube_ring_spacing`, `tube_ring_width` | 0.3, 0.03 | a dark ring every … m, and its width [m] |
| `tube_segment_length`, `tube_colors`, `tube_seed` | 7.5, orange + yellow, 0 | each tube piece gets one colour |
| `preset` | — | a real camera: `oakd_s2`, `oakd_s2_stereo` |
| `depth_mode` | `ray` | `ray`: distance along the pixel's ray; `z`: along the optical axis (stereo cameras) |
| `depth_min`, `depth_max` | 0, 0 | valid depth range [m]; outside it the pixel reads 0; 0 = no limit |
| `depth_baseline`, `depth_disparity_std` | 0, 0 | stereo noise model (below) |

## Labels

| id | class |
|---|---|
| 0 | background (nothing hit) |
| 1 | floor |
| 2 | wall (barrier) |
| 3 | car body |
| 4 | car wheel |
| 5 | own body (with `show_ego`) |
| 6 | own wheel (with `show_ego`) |
| 7 | bridge deck (2.5D maps) |
| 8 | bridge wall (2.5D maps) |

```{tip}
For learning, train on **depth and labels**, not on the image. Depth and
labels are what a perception network reports on the real car, so a policy
trained on them crosses to the hardware through that network, instead of
across the visual gap between simple shading and a real image. The image is
best for looking at.
```

## Barriers: `wall_style`

Real tracks are often bounded by flexible air ducts, orange and yellow, with a
dark reinforcement ring every few decimetres. With `wall_style: tubes` (the
default) the walls are drawn that way, and **round**: each wall pixel's ray is
intersected with a cylinder lying behind the wall's edge, so the silhouette,
the depth and the shading are those of a tube and the rings show as ellipses.
Rings narrower than a pixel fade into the tube, so distant walls do not
flicker. `plain` draws one flat orange wall with diagonal ribs.

```{figure} ../assets/camera_tubes.png
:alt: the same camera view drawn with plain walls (left) and tubes (right) on two tracks
:width: 100%

The same OAK-D S2 view on two tracks: `plain` (left) and `tubes` (right).
```

To place the rings and colours, the simulator chains each wall's edge cells
once per map, gives them an arc length and a smoothed direction, and per frame
looks those up per beam, not per pixel. A tubes frame costs about the same as a
plain one. The LiDARs still see the flat wall edge; the labels are unchanged.

## Bridges: `bridge_style`

On a {doc}`2.5D map <../map_2p5d>` the camera draws the bridges.
`bridge_style` chooses how they look **in the RGB / mono image**:

- `wood` (default) — a **planked deck** (planks across the bridge, each its own
  shade, wood grain, dark seams) and **side walls of stacked boards**.
- `plain` — a grey deck and orange side walls.

Both simulators draw the same wood (the JAX twin matches the main simulator's
image pixel for pixel, up to single pixels on seams). Only the image changes.
**Depth and labels are identical** for both styles
(deck = 7, bridge wall = 8), so anything trained on depth or labels does not
care.

```{figure} ../assets/camera_bridge_plain_vs_wood.png
:alt: four camera views on a bridge map, top row plain bridges, bottom row wooden bridges
:width: 100%

The same four camera frames on the bunker bridge map with `bridge_style: plain`
(top) and `wood` (bottom): on the ground road, two frames on the deck, and
under the bridge with the deck's underside overhead. The ground barriers are
drawn as tubes in both rows.
```

## Depth camera: the Luxonis OAK-D S2 preset

`camera={"preset": "oakd_s2"}` makes the camera behave like an OAK-D S2 as its
ROS driver delivers it by default: the colour camera with the stereo depth
**aligned** to it.

| | OAK-D S2 (datasheet) | preset `oakd_s2` |
|---|---|---|
| colour camera | HFOV 66° | pinhole, 66°, 640 × 360 |
| stereo pair | global shutter, 80° × 55°, baseline 7.5 cm | `oakd_s2_stereo`: depth on the left mono camera, 80°, 640 × 400 |
| depth | z along the optical axis, 0 = invalid | `depth_mode: z`, 0 outside the range |
| range | about 0.4–15 m with the driver's filter | `depth_min 0.4`, `depth_max 15` |
| accuracy | a few percent, growing with distance | stereo noise model below |

**Stereo noise model.** Stereo depth comes from disparity, $z = f_x B / d$.
A disparity error $\sigma_d$ (in pixels) therefore becomes a depth error that
grows with the square of the distance:

$$
\sigma_z = \frac{z^2\, \sigma_d}{f_x\, B}
$$

with focal length $f_x$ in pixels and baseline $B$. The simulator adds this
Gaussian error to the exact depth. Not modelled: holes on textureless
surfaces, flying pixels at edges, and the driver's filters.

In ROS 2 a configuration file sets the same camera on the driver's topic names
(`/oak/rgb/image_raw`, `/oak/stereo/image_raw` in 16-bit millimetres, and their
`camera_info`). See {doc}`../ros2_bridge`.

## The cars

Every car is drawn as an F1TENTH Traxxas Slash: the chassis outline (a wide
rear with cut corners, tapering to a narrower nose), a trapezoidal front
bumper, four round wheels on the axles of the dynamics model (the front pair
steered) and a tall open box with slats on the rear. `car: {shape: box}` draws
plain boxes instead (cheaper). The ROS bridge builds its RViz and Foxglove car
meshes from the same geometry.

```{figure} ../assets/camera_car.png
:alt: the car model from four sides

The car model from four sides, front wheels turned.
```

The tyres have **knobs** on the tread and **spoked hubs** that rotate with the
wheel speed — from the STD wheel-speed states, so wheel spin and lock-up are
visible. A spinning wheel fires events in the {doc}`event camera
<event_camera>`, a still one does not.

```{figure} ../assets/camera_tyres.png
:alt: a parked car from the side; the event camera fires on its spinning wheels and not on still ones

A car from the side, and the event camera over 50 ms with the wheels spinning
(middle) and still (right): only the spinning tyres fire; the rest is
background noise.
```

## How it works

The trick that makes the camera cheap: **for a vertical wall, where a pixel's
ray meets it depends only on the ray's azimuth**. So one frame is:

1. **One LiDAR-style scan** with one beam per azimuth bin (about twice the
   image width), giving the horizontal distance $d$ to the wall in each
   direction.
2. **Per pixel**, from its azimuth bin and its elevation angle $\varepsilon$, the
   hit height $z = h_{mount} + d \tan\varepsilon$ tells whether the ray hits the
   wall ($0 \le z \le h_{wall}$), the floor ($z < 0$), or nothing.
3. **Cars:** each pixel's ray is tested against the parts of every car (boxes,
   polygons, cylinders for the wheels), after a quick bounding-sphere check, so
   only pixels near a car pay for it. The nearer of wall/floor and car wins.
4. **Bridges** (2.5D maps): rays are marched through the bridge cells,
   skipping free space with a distance transform, and merged by depth.
5. **Shading:** brightness falls off with distance; the deck top is lit, its
   sides darker, its underside darker still.

On a laptop CPU a 320 × 192 frame with three cars in view takes a few
milliseconds, so the ego camera at 30 Hz keeps a 100 Hz simulation in real
time.

## Frame rate

`rate_hz` is the frame rate in **simulated** time; frames are held in between
(see {doc}`index`). A lower rate is also cheaper, since skipped steps are not
rendered.

## In ROS 2

Topics under `/ego_racecar/camera/`: `image_raw` (`rgb8` or `mono8`),
`mono/image_raw`, `depth/image_raw` (`32FC1`, metres — to compute with),
`depth/color` (turbo colours — to look at), `labels/image_raw`,
`labels/color` and `camera_info` (equidistant or plumb-bob distortion). TF:
`base_link → camera_link → camera_optical_frame`. See {doc}`../ros2_bridge`.
