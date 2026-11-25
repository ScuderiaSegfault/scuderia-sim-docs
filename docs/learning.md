# Reinforcement learning and deployment

Both simulators are built to be fast enough for reinforcement learning (RL),
and the release will include complete examples from training to running a
policy on another computer.

## Training in the numba simulator

- A **PPO** implementation written from scratch (only PyTorch needed), with a
  wrapper that gives the environment the modern Gymnasium interface.
- Two reward modes: **track** (follow the centreline fast) and **drift** (hold
  a power slide).
- Logging to TensorBoard.
- Controllers to compare against: pure pursuit, follow-the-gap, a sampling-based
  MPC (MPPI) and a two-car overtaking demo.

## Training in the JAX twin

- **PPO entirely in JAX**: environment, network and update compile into one
  program; thousands of environments run in parallel ({doc}`jax_twin`).
- A **drift task** that the STD model is made for: hold a target side-slip
  angle at a set speed on a low-grip surface without spinning out. The reward
  is a product of two Gaussians in $[0, 1]$, so it reads directly as the
  fraction of time spent in the target drift. A baseline search tells you what
  score is achievable, so a weak score can be blamed on the algorithm rather
  than on the task.
- The `step_batch` API keeps cameras and the 3D LiDAR cheap when many
  environments run at once.

```{tip}
For policies that use the camera, train on **depth and labels** rather than
the RGB image. They are what a perception network delivers on the real car,
so the policy crosses to the hardware through that network
({doc}`sensors/camera`).
```

## Exporting a policy: ONNX

A trained policy has to run where neither PyTorch, JAX nor the simulator is
installed — a ROS node, a C++ controller, an embedded board. Both simulators
export the policy to **ONNX**, which runs with
[onnxruntime](https://onnxruntime.ai/).

What the exported graph contains: the **deterministic actor only** —
observation in, action out. Left out on purpose: the value head (a training
signal) and the exploration noise (on the car you want the mean action).
In the JAX export the output squashing (`tanh`, scale and offset) is included,
so the output is already in physical units.

Every export is **verified** before it is written: the saved graph is run with
onnxruntime on random observations and compared with the original policy; the
remaining difference is float32 rounding.

```{important}
**The model is not the interface.** An `.onnx` file is a few matrix
multiplications with an input port. *Which* numbers go into the observation,
in which order, scaled by what, and at what rate — that contract lives in the
training code, not in the file. Copy the file without the contract and you get
a model that runs, gives plausible numbers, and drives wrongly. The release
documents the observation layout of each example next to the export.
```

Before trusting a policy on the target system:

1. Feed it recorded observations and compare its actions with the training
   code's.
2. Run it at the control rate it was trained for, with the same action delay.
3. Check the action units (steering angle vs rate, speed vs acceleration vs
   current — see {doc}`control_modes`).
