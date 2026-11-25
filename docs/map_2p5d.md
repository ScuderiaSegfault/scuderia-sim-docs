# 2.5D maps: bridges, ramps and banked curves

A plain map is flat. With **2.5D maps** a track can cross itself: a car drives
**over** a bridge (up a ramp, along a flat deck between side walls, down the
other ramp) or **under** it, along a road that passes beneath the deck. Bridges
can be **stacked** (a bridge over a bridge), and **banks** tilt the ground
itself for banked curves.

This lets you test what must work on more than one level: localisation,
mapping, planning and perception on a track that crosses itself.

```{figure} assets/ros_rviz_wood_bridge.jpg
:alt: RViz with three cars on a wooden bridge deck, the 3D LiDAR cloud, and camera, depth and label images on the left

Three cars crossing the bridge of the bunker over/under track, seen through the
ROS 2 bridge in RViz: wooden bridge markers, the ego's 3D LiDAR cloud, and the
ego camera's labels, depth and image on the left.
```

## The idea: a 2D map plus deck layers

The design keeps everything that made the 2D simulator fast:

- The world is the 2D map **plus a deck layer**: a height $H$ per map cell
  ($H<0$ = no deck). A bridge over a bridge uses one deck layer per level.
- Each car has a **level**: 0 = ground, 1 = the first deck, 2 = the deck
  above, and so on. On a deck, its height $z$ is the deck height under it;
  its pitch is the slope between the axles, its roll the slope across the car.
- The 2D LiDAR and the wall-collision check work exactly as before, but each
  car uses the **obstacle layer of its own level**. All layers are computed
  once when the map loads, so a step costs the same with bridges as without
  (several thousand steps per second for one car).

## Switching it on

```python
env = gym.make("scuderia-v0", map="figure8_bridge_v1", num_agents=2,
               map_2p5d=True,             # bridges and banks
               produce_lidar3d=True,      # optional: the 3D LiDAR
               disable_env_checker=True).unwrapped
obs, *_ = env.reset(np.array([[0.0, 0.0,  np.pi/4, 1],    # x, y, yaw, level: on the deck
                              [0.0, 0.0, -np.pi/4, 0]]))  # same x, y: under it
obs["levels"]        # (n,) 0 ground, 1 deck, 2 upper deck, ...
obs["poses_z"]       # (n,) height of the floor under the car [m]
obs["poses_pitch"]   # (n,) [rad], nose up > 0
obs["poses_roll"]    # (n,) [rad], left side up > 0
```

**Start levels.** `reset` also takes the usual three columns. The level is
then inferred: the ground, unless the ground is blocked at that spot (a ramp),
in which case the lowest free deck. A car placed under a bridge starts on the
ground. To start **on** a deck where it crosses over a road, give the level as
the fourth column.

Without `map_2p5d` the map loads as a plain 2D map, even if it defines
bridges.

## How levels work

From the deck height image:

- **Side walls** are added along every deck cell that is higher than a small
  *ramp-foot height*. The low ends of the ramps stay open — that is where cars
  drive on.
- **Ground layer** (obstacles for level 0): the map's walls, plus every bridge
  cell whose underside is lower than the *clearance* a car needs (the lower
  part of the ramps, and the walls along them). Under the flat part of the
  deck and the upper ramps the road is free.
- **Deck layer** (level 1): the map's walls plus the bridge side walls.
- **Map walls have a height.** They block a level only where its floor is
  lower than the wall top. So a ground road's walls can stay in the map image
  under a bridge: a car on a deck higher than them drives over them.
- **More levels:** a car on level $k$ is blocked by its own deck's side walls
  and by any other deck that reaches into the height band
  $[F, F + \text{clearance}]$ above its floor $F$. A deck far overhead or far
  below is not in the way.
- **Level switch:** a ground car moves up to level $k$ when its nose is on a
  ramp foot of deck $k$ and its centre is not under any bridge. A car on a
  deck comes down when its nose, centre and tail are all off that deck.
- **Cars meet only at the same height.** Cars touch, and appear in each
  other's 2D scans, only when their height ranges overlap. A car on the deck
  and a car below it at the same $x, y$ pass each other.
- **Slope gravity:** on a ramp, $g\sin(\text{pitch})$ slows the car uphill and
  speeds it up downhill. On a banked surface, $g\sin(\text{roll})$ is added to
  the lateral velocity toward the low side; the tyres then react through the
  slip angle, so the driver has to steer against the bank. At very low speed
  (kinematic regime) there is no sideways pull.

```{figure} assets/map_2p5d_lap.png
:alt: figure-8 path coloured by height, and height, level and speed over time

Two laps on the figure-8: up to the deck on one lobe, under the bridge on the
other. The speed dips on the up ramp (slope gravity) and the level switches
from 0 to 1 on the deck.
```

## Map YAML format: the `map_2p5d:` block

Bridges go into the map YAML (or a side file `<map>_2p5d.yaml`). Two ways,
which can be combined.

**Parametric bridges** — a trapezoid along `yaw_deg` through `x, y` (the
middle of the flat part):

```yaml
map_2p5d:
  bridges:
    - {x: 0.0, y: 0.0, yaw_deg: 45, width: 0.8, height: 0.30,
       ramp_length: 1.4, flat_length: 1.6}          # level: 1 by default
```

| key | meaning |
|---|---|
| `x`, `y` | centre of the flat part [m], map frame |
| `yaw_deg` | direction of the bridge |
| `width` | deck width [m] |
| `height` | deck height above the ground [m] |
| `ramp_length`, `flat_length` | length of each ramp and of the flat part [m] |
| `level` | 1 (default) or 2, … for a bridge over a bridge |

**Painted deck images** — a grey-scale PNG with the same size and orientation
as the map image. 0 = no deck; grey value $v$ = a deck at
$v \times$ `deck_height_scale` metres. Paint the flat part solid grey and each
ramp as a linear gradient up to that grey (for example in GIMP, on a layer
above the map). Side walls are added automatically.

```yaml
map_2p5d:
  deck_image: my_track_deck.png
  deck_height_scale: 0.002          # metres per grey level (150 -> 0.30 m)
  # bridge over a bridge: one image per level
  # deck_images: [my_track_deck.png, my_track_deck2.png]
```

A command-line helper turns a parametric bridge into deck images you can then
edit by hand.

**The road below must be free in the 2D map**: draw both roads as free space
where they cross.

### Global 2.5D settings

The `map_2p5d:` block of the simulator config holds defaults for every bridge
(the map YAML can override them):

| key | default | meaning |
|---|---|---|
| `deck_thickness` | 0.03 | deck slab [m]; the underside is at `H − deck_thickness` |
| `wall_height` | 0.25 | side walls above the deck [m] — taller than a LiDAR on the deck, so it sees them |
| `wall_width` | 0.04 | side wall thickness [m] |
| `enter_height` | 0.04 | ramp-foot height: a ground car whose nose is on a deck cell this low drives up |
| `clearance` | 0.20 | a ground car fits under deck cells whose underside is at least this high |
| `car_height` | 0.15 | cars are boxes `[z, z + car_height]` for contact and occlusion |
| `lidar_height` | 0.10 | 2D LiDAR height above the car's floor (decides which cars it sees) |
| `map_wall_height` | 0.25 | height of the 2D map's walls when extruded |
| `slope_gravity` | true | gravity on ramps and banks |

(m25-stacked)=
## A bridge over a bridge

Each bridge has a `level`. A level-2 bridge may cross a level-1 bridge, and
both may cross a ground road:

```yaml
map_2p5d:
  bridges:
    - {x: 0, y: 0, yaw_deg: 120, width: 0.8, height: 0.25, ramp_length: 1.4, flat_length: 2.6, level: 1}
    - {x: 0, y: 0, yaw_deg: 240, width: 0.8, height: 0.65, ramp_length: 2.6, flat_length: 2.6, level: 2}
```

The heights must leave room: a car on the lower deck needs the clearance below
the upper deck's underside (here 0.25 + 0.20 < 0.62 m), and the lower deck's
side walls must pass under it too. The shipped map `trefoil_bridges_v1` is
exactly this: three straight roads through one point, joined by loops. Three
cars on one spot, one per level, pass each other without contact.

```{figure} assets/map_2p5d_trefoil_lap.png
:alt: trefoil path coloured by height, and height, level and speed over time

A lap of the trefoil: under both bridges, up to the 0.25 m deck (level 1), then
up to the 0.65 m deck (level 2).
```

```{figure} assets/map_2p5d_trefoil_camera.png
:alt: camera at the crossing from level 1, level 2 and the ground

The camera at the crossing. Left: on the lower deck, under the upper deck's
underside. Middle: on the upper deck. Right: on the ground road, under both.
```

(m25-banks)=
## Banked curves

A bank raises the **ground**, not a deck: a ground height per map cell. A car
on the ground takes its $z$, pitch and roll from that height under its axles
and wheels (interpolated, so the roll is smooth), and slope gravity pulls it
toward the low side. There are no walls and no level change. The 3D LiDAR, the
camera and RViz see the bank as a solid surface.

```yaml
map_2p5d:
  banks:
    # a banked curve: the ring radius ± width/2 around (cx, cy), counter-clockwise
    # from start_deg to end_deg; the outer edge is width·tan(angle_deg) higher,
    # faded in and out over transition_deg
    - {cx: 3.0, cy: 0.0, radius: 2.0, width: 1.4, start_deg: -90, end_deg: 90,
       angle_deg: 15, transition_deg: 45}
    # a straight section tilted sideways (left side up), faded over `transition` metres
    - {x: 0.0, y: -2.0, yaw_deg: 0, length: 3.0, width: 1.4, angle_deg: 8, transition: 0.5}
  # optional: ground_image: my_map_ground.png   (grey = height)
```

`inside_up: true` flips a bank. Banks and bridges can be in one map, but a bank
must not lie under a bridge.

```{figure} assets/map_2p5d_banked.png
:alt: the banked oval with the lap coloured by roll, and the camera in a banked curve

The banked oval: the lap coloured by the car's roll (the car rolls in both
curves) and the camera in the right-hand curve, tilted with the car.
```

What a bank buys: with the same pure-pursuit driver at the same speed, the car
on the flat oval slides wide into the wall at the highest test speed, while on
the banked oval it holds its line within a few centimetres. (The model adds
gravity's sideways part but does not raise the tyres' normal load in the bank,
so a simulated bank has a little less grip than a real one.)

## Every sensor sees the bridges

- **2D LiDAR** — through its level's obstacle layer ({doc}`sensors/lidar2d`).
- **3D LiDAR** — decks, ramps, side walls and banks ({doc}`sensors/lidar3d`).
- **Camera and event camera** — each pixel ray is marched through the bridge
  cells and merged by depth. The camera rides at its car's height, pitch and
  roll, so its horizon tilts on a ramp. New labels: 7 = bridge deck,
  8 = bridge wall. Look: `bridge_style: wood | plain`
  ({doc}`sensors/camera`).
- **Top-down window** — decks shaded by height, side walls in orange; cars on
  top, so a car under a bridge stays visible.
- **RViz and Foxglove** — the bridges as markers, wooden or plain
  ({doc}`ros2_viewers`).

```{figure} assets/map_2p5d_camera.png
:alt: camera on the bridge deck between plain side walls, and under the bridge

The camera with `bridge_style: plain`: on the deck between the side walls
(left) and under the bridge, with the deck's underside overhead (right).
```

## Limitations

- Every ramp starts on the ground. A ramp from one deck up to another is not
  supported.
- Decks of one level must not overlap; put the higher one on the next level.
- Cars are boxes for contact and occlusion.
- Load transfer from banking is not modelled (see above).
