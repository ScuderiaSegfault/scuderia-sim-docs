# Overview and architecture

The stack has three parts. They share one set of vehicle models, one map format
and one sensor design, so a controller, a map or a trained policy moves between
them without changes.

```
                    ┌────────────────────────────────────────────┐
                    │  Scuderia Gymnasium  (numba, CPU)          │
                    │  gymnasium env "scuderia-v0"               │
                    │  vehicle + tyre models, 2D/3D LiDAR,       │
                    │  camera, event camera, 2.5D maps           │
                    └───────────────┬──────────────┬─────────────┘
                                    │              │
              same models,          │              │  runs inside
              parity-tested         │              │
                                    ▼              ▼
   ┌───────────────────────────────────┐   ┌─────────────────────────────────┐
   │  JAX twin  (JAX, CPU or GPU)      │   │  ROS 2 bridge  (ROS 2 Jazzy)    │
   │  jit / vmap / grad                │   │  real car's topics: /scan,      │
   │  thousands of envs per call,      │   │  /odom, IMU in, /ackermann_cmd  │
   │  gradients through the physics    │   │  out; RViz and Foxglove         │
   └───────────────────────────────────┘   └─────────────────────────────────┘
```

## Scuderia Gymnasium — the main simulator

A [Gymnasium](https://gymnasium.farama.org/) environment (`scuderia-v0`) for
1:10 racing cars. It started as a fork of the
[F1TENTH Gym](https://github.com/f1tenth/f1tenth_gym) and has been rebuilt
around three goals:

1. **Speed.** All physics and sensor kernels are compiled with
   [numba](https://numba.pydata.org/); the Python overhead in `step` and
   `reset` is kept small. One car on a plain map runs at several thousand
   physics steps per second on a laptop CPU.
2. **Vehicle dynamics you can trust.** Kinematic, dynamic, drift and
   four-wheel models; four tyre models; wheel-speed states; a DC motor model
   for current control. See {doc}`vehicle_models`.
3. **Realistic sensors.** A 2D LiDAR, a 3D LiDAR, a camera with depth and
   labels, an event camera, IMU, odometry and GPS — all computed from the
   same physics step, so there is no artificial lag between them. See
   {doc}`sensors/index`.

The physics runs at a fixed step (10 ms by default, i.e. 100 Hz). Sensors that
are slower in reality (camera, 3D LiDAR) take a frame only when their own
clock says so and hold it in between.

## The JAX twin

A second implementation of the same models in [JAX](https://jax.readthedocs.io/).
It is not a different simulator but a *twin*: it is tested against the numba
version at every level, from a single tyre force to complete replays of real
recordings. What JAX adds:

- **Batching** — `jax.vmap` runs thousands of environments in one call.
- **GPU** — the physics, the cameras and the 3D LiDAR run on a GPU.
- **Gradients** — `jax.grad` differentiates a whole rollout with respect to the
  state *and* the vehicle and tyre parameters.

Use it for large-scale reinforcement learning, parameter studies and
gradient-based fitting. See {doc}`jax_twin`.

## The ROS 2 bridge

A ROS 2 Jazzy package that runs Scuderia Gymnasium inside a node. It publishes
and subscribes the **same topics as the real car** (`/scan`, `/odom`,
`/phidgets/imu/data_raw`, `/ackermann_cmd`), so the car's localisation,
planning and control software can run against the simulator unchanged. It adds
TF, camera and point-cloud topics, car models for RViz and Foxglove, an
autopilot and a sensor checker for tests. See {doc}`ros2_bridge`.

## Which one should I use?

| you want to … | use |
|---|---|
| train an RL policy with one or a few environments, or try a controller in Python | Scuderia Gymnasium |
| train with thousands of environments, on a GPU | JAX twin |
| differentiate through the dynamics (fitting, sensitivity, gradient-based control) | JAX twin |
| test your ROS 2 racing stack (localisation, planner, controller) before the real car | ROS 2 bridge |
| look at your car in RViz or Foxglove | ROS 2 bridge |

## Coordinate frames and units

- SI units everywhere: metres, seconds, radians (degrees only where a key name
  says `_deg`).
- The map frame is the frame of the occupancy-grid map (ROS `map_server`
  convention: the map YAML gives resolution and origin).
- A car pose is `x, y, yaw`; on {doc}`2.5D maps <map_2p5d>` also a `level`,
  and the simulator reports `z`, `pitch` and `roll`.
- Body frame: `x` forward, `y` left, `z` up. Camera optical frames follow the
  ROS convention (`z` forward, `x` right, `y` down).
