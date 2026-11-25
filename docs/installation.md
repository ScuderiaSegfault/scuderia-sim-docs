# Installation (outline)

```{admonition} Available when the code is released
:class: note

The packages are not public yet (see {doc}`code_release`). This page tells you
what you will need, so you can prepare your machine now. Exact commands will be
added with the release.
```

## Scuderia Gymnasium (numba simulator)

**You need:**

- Linux (Ubuntu is tested), Python 3.10 or newer.
- OpenGL, only if you want the live top-down window (headless use works
  without it).

**Steps (planned):**

```bash
python3 -m venv .venv            # one virtual environment per project
source .venv/bin/activate
pip install --upgrade pip
pip install -e .                 # inside the simulator's repository
```

Core dependencies (installed automatically): `gymnasium`, `numpy`, `numba`,
`scipy`, `pyyaml`, `Pillow`, `pyglet`, `pyopengl`.

Optional extras:

| package | for |
|---|---|
| `matplotlib` | plots after a run, the test summaries and videos |
| `ffmpeg` (system package) | writing videos |
| `torch`, `tensorboard` | the PPO examples |
| `onnx`, `onnxruntime` | exporting a trained policy |

```{tip}
The first run of each map is slower: numba compiles the kernels just in time
(10–30 s). Later runs use the cache.
```

## JAX twin

**You need:** Python 3.11 or newer, JAX (CPU or CUDA). A GPU is optional but is
where batching pays off most. A conda or venv environment of its own is
recommended, because JAX and CUDA versions must match.

The JAX twin switches on JAX's 64-bit mode by default, so that its results
match the numba simulator. For speed on a consumer GPU you can run it in
32-bit (see {doc}`jax_twin`).

## ROS 2 bridge

**You need:**

- Ubuntu 24.04 with **ROS 2 Jazzy** (desktop install).
- A few ROS packages: `ackermann_msgs`, `nav2_map_server`,
  `nav2_lifecycle_manager`, `robot_state_publisher`, `xacro`,
  `joint_state_publisher`.
- Optional: `foxglove_bridge` (Foxglove), `event_camera_msgs` (event-camera
  packets), `teleop_twist_keyboard` (driving with the keyboard), `ffmpeg`.

**Planned layout:** one Python virtual environment that can see the ROS
Python packages, with the simulator installed into it:

```bash
source /opt/ros/jazzy/setup.bash
python3 -m venv --system-site-packages ~/ros2_ws/venv   # rclpy stays visible
source ~/ros2_ws/venv/bin/activate
pip install -e <path to Scuderia Gymnasium>
cd ~/ros2_ws && python -m colcon build --packages-select scuderia_gym_ros
```

```{important}
Build with `python -m colcon` **from inside the activated venv**. A plain
`colcon build` writes the system Python into the node scripts, and the bridge
then cannot find the simulator.
```

Every new terminal then needs, in this order:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
source ~/ros2_ws/venv/bin/activate
```

Stop ROS launches with **Ctrl+C**. Killing `ros2` or `rviz2` harder makes
Ubuntu show crash pop-ups.

ROS 2 Humble may work but is not tested.
