# Scuderia Sim

**A simulator stack for 1:10 autonomous racing** — fast enough for
reinforcement learning, detailed enough for vehicle dynamics research, and
compatible with the real car's ROS 2 software.

```{admonition} The code is coming
:class: important

This site holds the **documentation only**. The source code of the simulators
and the ROS 2 bridge will be released **when the accompanying paper is
published**. Until then, use these pages to learn what the stack does and how
it works — so you are ready to drive on day one. See {doc}`code_release`.
```

```{figure} assets/ros_rviz_wood_bridge_zoom.jpg
:alt: three simulated cars on a wooden bridge deck in RViz, one LiDAR point cloud below
:width: 70%

Three cars on the bridge of a real track (2.5D map), shown in RViz through the
ROS 2 bridge. The ego's 3D LiDAR cloud is drawn in orange and yellow.
```

## What is in the stack

- **Scuderia Gymnasium** — the main simulator: a numba-compiled
  [Gymnasium](https://gymnasium.farama.org/) environment, `scuderia-v0`, with
  kinematic, dynamic, drift and four-wheel vehicle models, four tyre models,
  three control modes (speed, acceleration, motor current) and several cars.
- **Sensors** — 2D LiDAR, 3D LiDAR, on-board camera with depth and labels,
  event camera, IMU, odometry and GPS.
- **2.5D maps** — bridges you can drive over *and* under, a bridge over a
  bridge, and banked curves.
- **JAX twin** — the same models in JAX: thousands of environments in one call,
  on the GPU, with gradients through the physics.
- **ROS 2 bridge** — the simulator as a ROS 2 Jazzy node that speaks the real
  car's topics, with RViz and Foxglove views.

Start with the {doc}`overview`.

```{toctree}
:maxdepth: 2
:caption: Getting started

overview
code_release
installation
usage
```

```{toctree}
:maxdepth: 2
:caption: Vehicle physics

vehicle_models
tyre_models
control_modes
```

```{toctree}
:maxdepth: 2
:caption: Sensors

sensors/index
sensors/lidar2d
sensors/lidar3d
sensors/camera
sensors/event_camera
sensors/state_sensors
```

```{toctree}
:maxdepth: 2
:caption: Worlds

maps
map_2p5d
```

```{toctree}
:maxdepth: 2
:caption: Tools

ros2_bridge
ros2_viewers
jax_twin
testing
learning
validation
```
