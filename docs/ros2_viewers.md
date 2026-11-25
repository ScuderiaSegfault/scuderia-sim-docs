# RViz and Foxglove

Both viewers show the same topics: the map, the LiDAR scans, the car models,
the poses, the camera images, the event camera, the 3D point cloud and the
bridges. RViz runs on the machine with ROS; Foxglove can run anywhere (also on
Windows next to a WSL simulator) and connects over a WebSocket.

## RViz

```bash
ros2 launch scuderia_gym_ros gym_bridge_launch.py camera:=true event_camera:=true
```

The default RViz configuration shows the map, the scan coloured by range, the
car model, the ground-truth pose and a raceline, plus image displays for the
camera, the mono image, the labels, the depth (turbo colours, 0–8 m) and the
event camera. To follow the car, set the view's target frame to
`ego_racecar/base_link`.

```{figure} assets/ros_rviz.png
:alt: RViz following the car, with camera labels, depth and event-camera images on the left

RViz following the car. The car is the F1TENTH Slash model; its front wheels
turn with the steering TF. On the left: the camera labels, depth and event
camera.
```

Two more configurations come with the package:

- a **2.5D view** — the map, the bridges, the car and the 3D LiDAR cloud;
- a **test-drive view** — the map, the bridges, all three car models, the
  three scans, the 3D LiDAR, and the camera, depth and label images (used by
  the test-drive script, {doc}`testing`).

### Several cars

```{figure} assets/ros_rviz_opponents.png
:alt: RViz with three cars following each other, and the ego's camera and event camera seeing the car ahead

Three cars (`num_agent:=3`), each driven by its own follow-the-gap controller.
RViz has one robot model per car; on the left, the ego's camera sees the car
ahead and the event camera fires on its spinning wheels.
```

### Bridges in RViz: wooden or plain

On 2.5D maps, `/map_2p5d/markers` (a latched `MarkerArray`) draws the bridges
in 3D and the banks in green. The parameter `map_2p5d_markers_style` chooses
the look:

- `wood` (default) — a planked deck and side walls of boards, matching the
  camera's `bridge_style: wood`;
- `plain` — a grey deck with orange side walls.

`map_2p5d_markers_walls: True` additionally extrudes the 2D map's walls
(heavier for RViz).

```{figure} assets/ros_rviz_wood_bridge_zoom.jpg
:alt: three car models on a wooden bridge in RViz
:width: 70%

Wooden bridge markers on the bunker over/under track, three cars on the deck,
the ego's 3D LiDAR cloud in front of it.
```

## The camera topics

```{figure} assets/ros_camera_topics.png
:alt: the camera's RGB, mono, depth and label images and the event-camera image from one moment

One moment of every image topic: RGB, mono and depth in turbo colours (top);
labels and the event camera's 30 Hz frame, ON white and OFF blue (bottom).
```

Use `depth/image_raw` (32-bit float metres) to compute with and
`depth/color` to look at — a viewer draws the float image as grey, which looks
like one more mono camera.

## Foxglove

```bash
sudo apt install ros-jazzy-foxglove-bridge      # once
ros2 launch scuderia_gym_ros sim_foxglove.launch.py camera:=true event_camera:=true
```

This starts the bridge, `foxglove_bridge` on port 8765 and the robot state
publishers for the car models. In Foxglove:

1. *Open connection* → *Foxglove WebSocket* → `ws://localhost:8765`.
2. *Layout* → *Import from file* → the layout shipped with the package.

The layout's tabs: *Overview* (3D view, speed, steering, IMU), *Camera* (a
chase view that follows the car, beside the RGB, mono, labels and depth
images), *Event camera*, and sensors / state estimation.

Tips:

- The cars come from URDF layers on `/ego_robot_description` and
  `/opp_robot_description`. To add a car to another 3D panel: *Custom layers*
  → *URDF*, source *Topic*.
- Give every 3D panel a follow frame (`map` or `ego_racecar/base_link`).
  Otherwise Foxglove may pick a camera optical frame and draw the world on its
  side.
- Foxglove keeps its own copy of an imported layout; after the file changes,
  import it again.
- Add `auto_reset:=true` to put the cars back at the start after a crash
  instead of pausing — handy while you watch a simple controller.

## When it looks slow

The bridge logs `physics: N steps/s (X× real time)` every 10 s. Below 1×,
everything — the car, the plots, the cameras — runs in slow motion. The usual
cause is another heavy job on the same machine.
