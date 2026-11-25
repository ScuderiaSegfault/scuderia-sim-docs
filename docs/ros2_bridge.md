# ROS 2 bridge

The ROS 2 package `scuderia_gym_ros` runs Scuderia Gymnasium inside a ROS 2
**Jazzy** node (named `bridge`). It speaks the **real car's topics** — `/scan`,
`/odom`, `/phidgets/imu/data_raw` out, `/ackermann_cmd` in — so localisation,
planning and control software written for the car runs against the simulator
unchanged. It supports 1 to 3 cars, the camera, the event camera, the 3D LiDAR
and 2.5D maps. It descends from the original `f1tenth_gym_ros`.

## Architecture

```
 AckermannDriveStamped         ┌───────────────────┐
   /ackermann_cmd    ─────────►│                   │──► /scan, /odom, TF
   /opp_drive, /opp2_drive ───►│   bridge node     │──► /phidgets/imu/data_raw
 PoseWithCovarianceStamped     │                   │──► /ego_racecar/{pose, gt_pose, gps_pose, ...}
   /initialpose      ─────────►│   scuderia-v0     │──► camera, event camera, 3D LiDAR
                               │   (100 Hz)        │──► /map_2p5d/markers
                               └───────────────────┘
```

The node runs three threads so that the 10 ms physics budget is spent on
physics:

| thread | does |
|---|---|
| physics | steps the simulator every 10 ms of wall time and caches the state |
| images | converts and publishes camera and event-camera data from a queue (no step is skipped, so no events are lost) |
| executor | subscriptions, and the odometry / TF / scan publisher, which publishes each physics step exactly once |

The numba kernels release Python's GIL, so rendering overlaps with
publishing. Every 10 s the node logs its real-time factor and the time per
step. With 2 or 3 cars, the physics steps only once **every** car has received
a drive command.

## Launch files

| launch file | starts | notes |
|---|---|---|
| `gym_bridge_launch.py` | bridge + map server + car model + RViz | settings from `config/sim.yaml`; arguments `camera`, `event_camera`, `camera_rate`, `map_2p5d`, `lidar3d`, … |
| `sim_foxglove.launch.py` | bridge + map server + car models + `foxglove_bridge` | arguments `map`, `num_agent` (1–3), `extra_params` (a YAML laid over `sim.yaml`), `auto_reset`, sensors |
| `sim_std_pacejka.launch.py` | STD model, speed control, GPS noise on | |
| `sim_std_accl.launch.py` | STD model, acceleration control | |
| `sim_std_current.launch.py` | STD model, motor-current control | |
| `sim_st.launch.py` | ST model, noisy GPS | |
| `sim_drift.launch.py` | STD, current control, friction map | |
| `sim_headless.launch.py` | bridge only, no GUI | model, control mode, tyre model as arguments |

```bash
ros2 launch scuderia_gym_ros gym_bridge_launch.py                              # RViz
ros2 launch scuderia_gym_ros gym_bridge_launch.py camera:=true event_camera:=true
ros2 launch scuderia_gym_ros gym_bridge_launch.py map_2p5d:=true lidar3d:=true
ros2 launch scuderia_gym_ros sim_foxglove.launch.py num_agent:=3 camera:=true  # Foxglove
```

The easiest way to pick a map, the number of cars and the control mode in one
command is the test-drive script ({doc}`testing`):

```bash
TRACK=icra_t1 CARS=3 CTRL=speed,accl,current bash tools/run_test_drive.sh
```

## Topics

### Subscribed

| topic | type | meaning |
|---|---|---|
| `/ackermann_cmd` | `ackermann_msgs/AckermannDriveStamped` | ego drive command: `steering_angle` [rad] and `speed` = the longitudinal command of its control mode (m/s, m/s² or A) |
| `/opp_drive`, `/opp2_drive` | `AckermannDriveStamped` | car 1 and car 2 |
| `/initialpose` | `geometry_msgs/PoseWithCovarianceStamped` | reset the ego pose (RViz "2D Pose Estimate") |
| `/goal_pose` | `geometry_msgs/PoseStamped` | reset car 1 (RViz "2D Goal Pose") |
| `/cmd_vel` | `geometry_msgs/Twist` | keyboard teleop (`kb_teleop: True`) |

### Published, per car

| | car 0 (ego) | car 1 (opp) | car 2 (opp2) |
|---|---|---|---|
| namespace | `ego_racecar` | `opp_racecar` | `opp2_racecar` |
| drive in | `/ackermann_cmd` | `/opp_drive` | `/opp2_drive` |
| odometry | `/odom` | `/opp_racecar/odom` | `/opp2_racecar/odom` |
| 2D scan | `/scan` | `/opp_scan` | `/opp2_scan` |
| ground-truth pose | `/ego_racecar/pose`, `/ego_racecar/gt_pose` | `/opp_racecar/pose` | `/opp2_racecar/pose` |
| GPS (opt-in) | `/ego_racecar/gps_pose` | `/opp_racecar/gps_pose` | `/opp2_racecar/gps_pose` |
| IMU (opt-in) | `/phidgets/imu/data_raw` | `/opp_racecar/imu` | `/opp2_racecar/imu` |
| slip, steering, wheel speeds (opt-in) | `/ego_racecar/...` | `/opp_racecar/...` | `/opp2_racecar/...` |
| robot model | `/ego_robot_description` | `/opp_robot_description` | `/opp2_robot_description` |
| start pose parameters | `sx`, `sy`, `stheta` | `sx1`, `sy1`, `stheta1` | `sx2`, `sy2`, `stheta2` |
| control mode parameter | `ego_ctrl_mode` | `opp_ctrl_mode` | `opp2_ctrl_mode` |

With 2 cars, each car also gets the other's odometry (`/ego_racecar/opp_odom`,
`/opp_racecar/opp_odom`) for planners that need it.

### Sensors on the ego

| topic | type |
|---|---|
| `/ego_racecar/camera/image_raw`, `.../mono/image_raw` | `sensor_msgs/Image` (`rgb8` / `mono8`) |
| `/ego_racecar/camera/depth/image_raw` | `Image`, `32FC1` metres (or `16UC1` mm) |
| `/ego_racecar/camera/depth/color`, `.../labels/color` | `Image`, colourised for viewing |
| `/ego_racecar/camera/labels/image_raw` | `Image`, `mono8` class ids |
| `/ego_racecar/camera/camera_info` | `sensor_msgs/CameraInfo` |
| `/ego_racecar/event_camera/events` | `event_camera_msgs/EventPacket` (EVT 3.0) |
| `/ego_racecar/event_camera/image`, `.../camera_info` | event frame and lens |
| `/ego_racecar/lidar3d/points` | `sensor_msgs/PointCloud2` (`x y z intensity ring`) |
| `/map_2p5d/markers` | `visualization_msgs/MarkerArray`, latched: bridges and banks |

On 2.5D maps the odometry carries the height (`position.z`) and the pitch and
roll in its orientation, exactly as the TF does.

### TF tree

| parent | child | |
|---|---|---|
| `map` | `<ns>/base_link` | car pose (lifted and tilted on 2.5D maps) |
| `<ns>/base_link` | `<ns>/laser` | 2D LiDAR mount |
| `<ns>/front_*_hinge` | `<ns>/front_*_wheel` | steering of the front wheels |
| `<ns>/base_link` | `camera_link` → `camera_optical_frame` | camera mount (static) |
| `<ns>/base_link` | `event_camera_link` → `event_camera_optical_frame` | event camera mount |
| `<ns>/base_link` | `<ns>/lidar3d` | 3D LiDAR mount |

There is no `odom` frame: the simulator publishes `map → base_link` directly.
If your localiser owns `map → odom → base_link`, set `publish_pose_tf: False`.

## Parameters

Parameters live in `config/sim.yaml` (keyed `bridge:`), are read once at
start-up, and can be overridden by launch arguments, by `extra_params:=<yaml>`
or with `-p name:=value`. With `ros2 run` add `-r __node:=bridge` so that the
YAML applies. The tables list names and meanings; vehicle properties themselves
come from the vehicle parameter file.

**Map, cars and model**

| parameter | default | meaning |
|---|---|---|
| `map_path`, `map_img_ext` | package map, `.png` | map path without extension; image extension |
| `num_agent` | 1 | 1, 2 or 3 cars |
| `sx` … `stheta2` | | start poses [m, m, rad] |
| `model` | `std` | `st` or `std` |
| `ctrl_mode` | `speed` | `speed`, `accl` or `current` for all cars |
| `ego_ctrl_mode`, `opp_ctrl_mode`, `opp2_ctrl_mode` | empty | per-car override |
| `integrator` | `rk4` | `euler`, `rk3`, `rk4` |
| `tire_model` | `full_pacejka_combined` | STD tyre model |
| `std_n_substeps` | 5 | STD sub-steps per 10 ms step |
| `vehicle_config` | empty | your own vehicle parameter YAML (empty = the default car) |
| `kb_teleop` | `True` | listen on `/cmd_vel` |
| `auto_reset` | `False` | after an ego collision, reset all cars (and publish `/initialpose`); otherwise the physics pauses |

**Topics and frames:** `ego_namespace`, `opp_namespace`, `opp2_namespace`, and
the topic names `ego_scan_topic`, `ego_odom_topic`, `ego_imu_topic`,
`ego_drive_topic`, … (a leading `/` makes a name absolute). Best left as they
are.

**Published extras and TF**

| parameter | default | meaning |
|---|---|---|
| `publish_extra_states` | `False` | IMU, slip angle, actual steering, wheel speeds |
| `publish_inner_states` | `False` | full state vector `vehicle_state` |
| `publish_pose_tf`, `publish_wheel_tf`, `publish_laser_tf` | `True` | which TFs the bridge broadcasts |
| `gps_noise_enabled`, `gps_noise_std_xy`, `gps_noise_std_theta`, `gps_hz` | off, 0.03 m, 0.005 rad, 40 Hz | noisy GPS pose |
| `gt_pose_cov_xy`, `gt_pose_cov_yaw` | small | nominal covariance in `gt_pose` |

**2D LiDAR:** `scan_beams` (1080), `scan_fov` (4.7 rad),
`scan_distance_to_base_link` (0 m).

**Friction map:** `friction_map_png`, `friction_map_yaml`,
`friction_map_mu_min`, `friction_map_mu_max` — a grey-scale image (black =
low, white = high friction) aligned with the map.

**2.5D map and 3D LiDAR**

| parameter | default | meaning |
|---|---|---|
| `map_2p5d` | `False` | load the map's bridges and banks |
| `map_2p5d_markers_walls` | `False` | also draw the 2D map's walls as markers (heavier) |
| `map_2p5d_markers_style` | `wood` | bridge look in RViz: `wood` (planked deck, board walls) or `plain` (grey deck, orange walls) |
| `lidar3d_enabled` | `False` | 3D LiDAR on the ego |
| `lidar3d_preset` | `airy` | `airy` or `airy_fast` |
| `lidar3d_rate_hz` | 10.0 | |
| `lidar3d_mount_x`, `lidar3d_mount_z`, `lidar3d_mount_pitch_deg`, `lidar3d_mount_yaw_deg` | 0.10, 0.20, 90, 0 | mount |
| `lidar3d_noise_std` | 0.0 | range noise [m] |

**Camera:** `camera_enabled`, `camera_width` / `camera_height` (320 × 192),
`camera_rate_hz` (30), `camera_model`, `camera_hfov_deg`, `camera_color`,
`camera_mount_*`, `camera_pitch_deg` / `yaw` / `roll`, `camera_show_ego`,
`camera_wall_style`, `camera_publish_mono` / `_depth` / `_labels`,
`camera_depth_mode`, `camera_depth_range_min` / `_max`,
`camera_depth_baseline`, `camera_depth_disparity_std`, `camera_depth_encoding`,
`render_threads`. Meanings as in {doc}`sensors/camera`. A file
`config/oakd_s2.yaml` turns the camera into the OAK-D S2 on the driver's topic
names:

```bash
ros2 launch scuderia_gym_ros sim_foxglove.launch.py camera:=true \
    extra_params:=$(ros2 pkg prefix scuderia_gym_ros)/share/scuderia_gym_ros/config/oakd_s2.yaml
```

**Event camera:** `event_enabled`, `event_width` / `event_height` (160 × 90),
`event_model`, `event_hfov_deg`, `event_mount_*`, `event_threshold`,
`event_threshold_sigma`, `event_refractory_s`, `event_noise_hz`,
`event_substeps`, `event_frame_hz`. See {doc}`sensors/event_camera`.

## Writing your own agent

Write your agent as a ROS 2 node in its own package: subscribe to `/scan` and
`/odom`, publish `AckermannDriveStamped` on `/ackermann_cmd` (and on
`/opp_drive`, `/opp2_drive` for the other cars). The package's `autopilot`
node (pure pursuit on a centreline) is a small example.

**Keyboard:** with `kb_teleop: True`, run
`ros2 run teleop_twist_keyboard teleop_twist_keyboard`; `linear.x` becomes the
drive command and `angular.z` the steering.

## Real time

Measured on a laptop CPU with one car: without extra sensors a physics step
takes well under 1 ms; with the 320 × 192 camera at 30 Hz a few milliseconds;
the 3D LiDAR and the camera together on a bridge map still run at 1.0× real
time. Running the camera and the event camera both at 30 Hz is at the edge of
the 10 ms budget — drop the camera to 15 Hz (`camera_rate:=15`) for margin.
Other heavy jobs on the same machine (training runs) slow the bridge down;
the log line tells you when it falls below real time.

## Reusing a real-car Foxglove layout

Because the topic names match, most of a real-car layout works unchanged.
Differences: the simulator runs no particle filter (use `/odom` and
`/ego_racecar/pose`), has no motor controller or battery topics, publishes
wheel speeds as `/ego_racecar/wheel_speeds` and the actual steering angle as
`/ego_racecar/steer_angle_actual`, and has no `odom` frame. See
{doc}`ros2_viewers`.
