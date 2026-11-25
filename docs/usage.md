# Using the simulator

This page shows how the Gymnasium environment is used. Snippets are short on
purpose; they show the interface, not a full program.

## Create, reset, step

```python
import gymnasium as gym
import numpy as np
import scuderia_gym                     # registers "scuderia-v0"

env = gym.make("scuderia-v0", map="icra2026_t1_v1", num_agents=2,
               disable_env_checker=True).unwrapped

poses = np.array([[0.0, 0.0, 0.0],      # one row per car: x [m], y [m], yaw [rad]
                  [-1.0, 0.0, 0.0]])
obs, *_ = env.reset(poses)

action = np.array([[0.1, 2.0],          # per car: [steer, longitudinal command]
                   [0.0, 2.0]])
obs, reward, done, info = env.step(action)
```

- `map` takes the name of a shipped map ({doc}`maps`) or the path to a map
  YAML.
- `num_agents` is the number of cars (car 0 is the *ego*).
- The action has one row per car: a steering command and a longitudinal
  command whose meaning depends on the {doc}`control mode <control_modes>`.

```{note}
The environment keeps the classic F1TENTH-style `reset(poses)` /
`step(action)` signatures. The example code that will be released includes a
thin wrapper with the modern Gymnasium `(obs, reward, terminated, truncated,
info)` signature for RL libraries.
```

## Main keywords of `gym.make`

| keyword | meaning |
|---|---|
| `map`, `map_ext` | shipped map name or YAML path; image extension (`.png`, `.pgm`) |
| `num_agents` | number of cars |
| `timestep` | physics step in seconds (default 0.01 → 100 Hz) |
| `integrator` | `RK4` (default), `RK3` or `Euler` |
| `ego_idx` | which car is the ego |
| `params` | the vehicle parameter set (model, control mode, tyre model, vehicle properties) |
| `config_path` | a config YAML with the sensor and map blocks (`camera:`, `event_camera:`, `lidar3d:`, `map_2p5d:`) |
| `produce_camera`, `camera` | switch on the camera; override single camera keys |
| `produce_events`, `event_camera` | switch on the event camera |
| `produce_lidar3d`, `lidar3d` | switch on the 3D LiDAR |
| `map_2p5d` | load bridges and banks ({doc}`map_2p5d`) |
| `seed` | random seed (sensor noise) |

Every sensor is **off by default** except the 2D LiDAR, so a plain environment
is as fast as possible.

## What the observation contains

The observation is a dictionary with one entry per car for each key.

| key | content |
|---|---|
| `poses_x`, `poses_y`, `poses_theta` | pose in the map frame |
| `linear_vels_x`, `linear_vels_y`, `ang_vels_z` | body-frame velocities and yaw rate |
| `scans` | 2D LiDAR ranges ({doc}`sensors/lidar2d`) |
| `collisions` | collision flag per car |
| `lap_counts`, `lap_times` | lap counting |
| `steer_angle`, `slip_angle`, `yaw_rate`, `a_x`, `a_y`, `imu_ax`, `imu_ay` | extra states and IMU-like signals ({doc}`sensors/state_sensors`) |
| `omega_f`, `omega_r` | front / rear wheel speeds (STD model) |
| `camera_*` | camera image, depth, labels, stamp ({doc}`sensors/camera`) |
| `event_*` | event-camera counts and event lists ({doc}`sensors/event_camera`) |
| `lidar3d_*` | 3D LiDAR ranges and points ({doc}`sensors/lidar3d`) |
| `levels`, `poses_z`, `poses_pitch`, `poses_roll` | on 2.5D maps ({doc}`map_2p5d`) |

## Several cars

Set `num_agents`, give one pose row per car, and send one action row per
car. All cars are integrated in the same physics step, every car's LiDAR and
camera see the other cars, and collisions between cars are checked on their
real rectangles. 1, 2 or 3 cars are the tested configurations (the ROS bridge
supports up to 3); the Python environment and the JAX twin accept more.

Each car can use its own control mode — see {doc}`control_modes`.

## Watching a run

- `env.render()` opens a top-down window (pyglet) with the map, the cars and,
  on 2.5D maps, the bridges.
- The test tool writes a video with a top view, the ego camera, depth, labels
  and the 3D LiDAR ({doc}`testing`).
- Through the ROS 2 bridge you get RViz and Foxglove ({doc}`ros2_viewers`).
- The JAX twin writes a self-contained HTML dashboard (no OpenGL needed)
  ({doc}`jax_twin`).

## Friction map

Besides a single friction coefficient, the simulator accepts a **friction
map**: a grey-scale image aligned with the track map, where black means low
and white high friction. The car reads the friction under it every step —
useful for drifting studies or wet patches.
