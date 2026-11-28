# The JAX twin

A second implementation of the simulator in [JAX](https://jax.readthedocs.io/).
It has the same vehicle and tyre models, the same LiDAR, camera, event camera,
3D LiDAR and 2.5D maps — and it is tested against the numba simulator at every
level. What it adds:

- **`jax.jit`** — the whole step, sensors included, compiles into one program.
- **`jax.vmap`** — thousands of environments in one call.
- **GPU** — physics, cameras and 3D LiDAR run on the GPU.
- **`jax.grad`** — gradients of a rollout with respect to the state **and the
  vehicle and tyre parameters**.

## Models

Five vehicle models — KS, ST-linear (the CommonRoad reference model), ST, STD
and STD4W — and the four tyre models (full Pacejka, simplified, brush, Dugoff),
plus RK4 / RK3 / Euler with sub-stepping, LiDAR ray marching that sees the
other cars, collision checking (separating-axis test on the car rectangles) and
a friction map.

## Interface

The API is **pure-functional** in the style of JaxMARL, not Gymnasium: the
environment holds no state; you pass the state in and get a new one back.

```python
import jax, jax.numpy as jnp
import scuderia_gym_jax as sgj

env = sgj.make(model="std", num_agents=1)
obs, state = env.reset(jax.random.key(0), jnp.zeros((1, 3)))       # poses (n, 3)
action = {"agent_0": jnp.array([0.2, 3.0])}                        # steering angle [rad], speed [m/s]
obs, state, rewards, dones, info = env.step(jax.random.key(1), state, action)
```

`dones["__all__"]` triggers an automatic reset.

```{warning}
The action is a steering **angle** plus a speed setpoint (in `speed` mode),
as in the numba simulator. Many other F1TENTH-style simulators take a steering
*rate* and an acceleration. A controller brought over without changing the
mapping will seem to work and steer wrongly. If your controller does command
a steering rate, switch on `direct_steer_rate` ({doc}`control_modes`) in both
simulators instead of converting.
```

## Batching

The batch dimension is yours: the environment has no `num_envs`.

```python
n = 4096
keys = jax.random.split(jax.random.key(0), n)
obs, state = jax.vmap(env.reset, in_axes=(0, None))(keys, jnp.zeros((1, 3)))
obs, state, *_ = jax.vmap(env.step)(keys, state, actions)
```

A rollout without a Python loop uses `jax.lax.scan` over time.

**Sensors and batching.** A camera at 30 Hz or a LiDAR at 10 Hz should only
render on some steps. Under `vmap`, a per-environment `lax.cond` evaluates
*both* branches, so nothing is skipped. For RL with cameras or the 3D LiDAR
there is a batch API, `env.reset_batch` / `env.step_batch`: the sensors of all
environments share one clock, so steps without a due frame really skip the
render, and environments that reset get their first frame at once.
Throughput with 256 environments × 2 cars on a bridge map (GPU, env-steps per
second):

| sensors | `vmap(env.step)` | `env.step_batch` |
|---|---:|---:|
| camera 160 × 96 at 30 Hz | 4.4k | 11.7k |
| 3D LiDAR `airy_fast` at 10 Hz | 3.2k | 18.7k |
| both | 1.9k | 8.6k |

## Differentiating through the physics

Vehicle and tyre parameters are **traced**, not compile-time constants. So you
can differentiate a loss with respect to them, `vmap` over a grid of parameter
sets (domain randomisation, sensitivity studies), and change them without
recompiling.

```python
def loss(p):
    _final, trace = rollout(x0, u, p, spec, dt=0.01, n_steps=200)
    return jnp.sum((trace - measured) ** 2)

grad = jax.grad(loss)(p)      # with respect to every tyre and vehicle parameter
```

Only structural choices are static: which vehicle model, which tyre model,
which integrator, how many sub-steps.

Design points that keep the gradients finite:

- The tyre model is chosen at trace time, not with a traced switch — under
  `vmap` a switch would evaluate all four models, and a `NaN` in an unused
  branch would poison the gradient.
- Every branch of the original is reproduced exactly and made finite on
  **both** sides (`jnp.where` evaluates both).
- The test suite checks that gradients are finite for every model × tyre ×
  parameter block, at every branch boundary, and compares them with central
  differences (with kink detection, since automatic differentiation returns a
  one-sided derivative at a kink).

**When do gradients pay off?** A reverse-mode gradient through the nested
scans (rollout → sub-steps → RK4 stages) costs a fixed multiple of one forward
simulation (about 17× on CPU), independent of the number of parameters. Finite
differences cost one simulation per parameter. The break-even is at about
**16 parameters**; with the full Pacejka set (32) automatic differentiation is
about twice as fast, and the gap grows with more parameters.

## Parity with the numba simulator

Bit-exact equality is impossible (the numba kernels use fast-math, which lets
the compiler reorder floating-point operations differently from XLA), so the
tests are tiered:

| tier | what is compared | tolerance |
|---|---|---|
| T0 | packed parameter arrays | exact |
| T1 | four tyre models + ST saturation | 1e-12 |
| T2 | vehicle right-hand sides × tyres | 1e-11 |
| T3 | one integration step | 1e-11 |
| T4 | 1000-step rollout | 1e-8 |
| T5 | open-loop replay of real recordings | 1e-7 (measured ~1e-14 for STD/STD4W) |
| T6 | validation metrics | 1e-6 |
| T7 | LiDAR scan (noise off) | 1e-9 m |
| T8 | collision flags | exact |

The camera is compared pixel for pixel with the numba camera; the event camera
agrees on > 99.9 % of pixels; the 3D LiDAR has the same return / no-return on
99.9 % of beams, median range difference 0 and 99th percentile below 1 cm.

Two findings worth knowing:

- **The ST model is ill-conditioned in one regime.** Its hard low-speed switch
  plus a high-gain steering controller make the yaw rate oscillate on some
  recordings; perturbing the input by one unit in the last place changes the
  result visibly — in the original as much as in the port. ST replays are
  therefore held to the model's own rounding spread, while its per-step
  kernels are pinned to 1e-11.
- **STD4W reduces to STD only with the full Pacejka tyre**, because only that
  model's force is homogeneous in the normal load. For the other tyres the
  difference is a property of the model, not a bug.

## Cameras and 3D LiDAR on the GPU

The camera renders inside the compiled step: it `jit`s, `vmap`s over
environments and runs inside a `lax.scan` with no host round-trips. Pixel rays
are fixed in the car frame and computed once.

```{figure} assets/jax_camera_view.png
:alt: six frames of RGB, depth, labels and a top-down view while the ego passes traffic cars
:width: 80%

The JAX camera while the ego passes two traffic cars: RGB, depth, labels and
a top-down view per row.
```

Rough numbers (GPU, batched):

| workload | cost |
|---|---|
| 256 cameras 160 × 96, flat map | ~3 ms per batch |
| 1024 cameras 64 × 48 on a bridge map, half at the bridge | ~30 ms per batch (~34k frames/s) |
| full Airy 3D LiDAR scan, batched × 256 | 0.7 ms (flat) – 1.7 ms (bridges) per scan |
| `airy_fast` scan, batched × 256 | 0.2 – 0.4 ms per scan |

On bridge maps the camera rays are marched in **stages**: every ray first
takes a few steps; the rays still open are gathered into smaller batches and
continue. Under `vmap` a loop runs as long as its slowest lane, so this avoids
having every pixel wait for the one ray grazing along a bridge wall. The result
is identical to one long march, and several times faster.

The JAX camera draws the bridges in wood by default, exactly like the main
simulator's camera (`bridge_style: wood`, see {doc}`sensors/camera`). With
`bridge_style: plain` and `wall_style: tubes` it can instead draw the
**bridges' side rails as tubes** (only in the image; collisions and LiDARs keep
the thin rails):

```{figure} assets/jax_camera_rail_tubes.png
:alt: plain walls and rails (left) and tube walls and rails (right) on two bridge maps
:width: 80%

JAX camera: `plain` (left) and `tubes` (right) on bridge maps, from the
approach, from the ramp, from the deck and from the road under the bridge.
```

```{tip}
Use 32-bit mode on consumer GPUs. The twin runs in 64-bit by default for exact
parity with the numba simulator, but consumer GPUs are many times slower in
64-bit.
```

## Benchmark: when is JAX faster?

On a 16-core CPU without GPU, 64-bit, one process each:

| regime | workload | numba vs JAX |
|---|---|---|
| single step | one environment | numba ~10× faster |
| long rollout | 1000 steps in one call | numba ~4× faster |
| **batch** | 4096 environments | **JAX ~2.3× faster** |
| **gradient** | 32 parameters | **JAX ~1.9× faster** than finite differences |

On a single small state there is nothing to parallelise, and a hand-tuned
numba kernel is hard to beat. JAX wins where batching (from a few thousand
environments on a CPU; far earlier on a GPU) or gradients come in. The
benchmark reports compile time separately, waits for JAX's asynchronous
results, and uses medians over repeated runs.

## Visualisation without a window

The twin is normally run headless, so it has no OpenGL window. Instead, it
writes a **self-contained HTML dashboard**: an animated trajectory with car
bodies, signal panels, a toggle per trace, an optional reference line, and a
camera panel that scrubs with the trajectory. No server, no internet
connection, no OpenGL. A rollout, a replay and a real recording can be drawn
on the same axes. Static matplotlib figures are available for reports.

A channel a trace does not have (for example slip angle in a real recording)
is left out, never drawn as zero.
