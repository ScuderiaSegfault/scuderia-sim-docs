# Control modes

Every car takes an action row `[steer, cmd]`:

- `steer` — the **target steering angle** in radians. It passes through the
  steering delay and controller; the actual angle follows within the steering
  rate and angle limits. (Or a steering *rate*, see
  [Steering as a rate](#steering-rate).)
- `cmd` — the longitudinal command. **What it means depends on the control
  mode.**

| mode | `cmd` is | unit | how the simulator uses it |
|---|---|---|---|
| `speed` (default) | target speed | m/s | a speed controller turns it into an acceleration, then the acceleration limits apply |
| `accl` | target acceleration | m/s² | goes straight to the acceleration limits (no speed controller) |
| `current` | motor current | A | DC motor model: wheel torque from the current, then full wheel dynamics (STD only) |

## `speed` — the easy one

Send the speed you want. This is the usual F1TENTH interface: any controller
that publishes an `AckermannDriveStamped` with a speed works unchanged. Use it
for waypoint following, path tracking and first experiments.

## `accl` — direct acceleration

Send an acceleration. The simulator still enforces the physical limits: the
maximum acceleration $a_{max}$, and above the switching speed $v_{switch}$ a
**constant-power** limit (the available acceleration falls with speed, as with
a real motor). Use it when your controller (an MPC, for example) already
outputs an acceleration.

## `current` — motor current

Send a motor current. The DC motor model turns it into a wheel torque,

$$
T_{wheel} = K_{tG}\, I_{cmd},
$$

where $K_{tG}$ is the motor torque constant times the gear ratio. The torque
drives the wheel-speed equations of the STD model; the slip ratio — and with
it traction, wheel spin and lock-up — emerges from the difference between
wheel speed and vehicle speed.

To convert a desired acceleration into a current, use the rule of thumb

$$
I \approx \frac{m\, R_w}{K_{tG}}\; a ,
$$

with mass $m$ and wheel radius $R_w$ of your vehicle parameter set.

**Limits.** The simulator clips the current at the peak limit $I_{max}$ of the
vehicle file. A real motor can only hold a lower *continuous* current; the
simulator does not enforce that, so keep sustained commands within your
motor's continuous rating yourself (the test autopilots do).

```{warning}
`current` needs the STD model (`model: std`). The ST and KS models have no
wheel dynamics; there the number would be read as an acceleration. The test
tools refuse this combination.
```

## Choosing a mode

| you are working on … | mode |
|---|---|
| path following, racing lines, RL with simple actions | `speed` |
| MPC or other model-based control that plans accelerations | `accl` |
| traction control, launch control, drifting, torque-level studies | `current` |

## Per-car control mode

The mode is set globally (`ctrl_mode` in the vehicle parameters) and can be
**overridden per car**. In Python, after creating the environment:

```python
from scuderia_gym.envs.dynamic_models import CTRL_SPEED, CTRL_ACCL, CTRL_CURRENT

env.sim.agents[0].ctrl_mode = CTRL_CURRENT   # car 0: cmd = motor current [A]
env.sim.agents[1].ctrl_mode = CTRL_SPEED     # car 1: cmd = target speed [m/s]
obs, *_ = env.step(np.array([[0.0, 20.0],    # [steer, cmd] per car
                             [0.0,  2.0]]))
```

In ROS 2 the parameters `ego_ctrl_mode`, `opp_ctrl_mode` and `opp2_ctrl_mode`
override the global `ctrl_mode` per car ({doc}`ros2_bridge`). The test tools
take one mode per car, e.g. `speed,accl,current` for three cars
({doc}`testing`).

## Wider action rows

Two optional extensions add columns to the action row:

- **Mechanical brakes (STD):** `[steer, cmd, brake_front, brake_rear]` —
  two brake torques added to the motor braking.
- **STD4W:** a fixed 10-column row with per-wheel drive and brake torques
  ({doc}`vehicle_models`).

The simulator checks the action width and raises an error if the row is too
narrow.

(steering-rate)=
## Steering as a rate (`direct_steer_rate`)

By default `steer` is an angle that goes through the steering delay and the
steering servo controller. With

```yaml
model:
  direct_steer_rate: true
```

`steer` is instead the **steering rate** $\dot\delta$ in rad/s. It is clipped
to the steering-rate limit and fed straight to the model, without the delay and
the servo controller. Use it when your controller's own model integrates the
steering angle from a rate input (many MPC formulations do), so that the
simulator and the controller agree on what the steering command means.

- It works with every vehicle model, including `std4w`, and with every
  control mode for `cmd`.
- It is off by default; existing setups are unchanged.
- It can also be set per car after creating the environment:
  `env.sim.agents[0].direct_steer_rate = True`.
- The JAX twin has the same option (`direct_steer_rate=True` in `make`), and
  its action space bounds then follow the steering-rate limit
  ({doc}`jax_twin`).

## Multi-agent racing: gap keeping

Cars with the same target speed but different control modes settle at slightly
different speeds and slowly close up. The test autopilots therefore include
**gap keeping**: a car slows down when another car at its height is close
ahead within a cone around its heading, and stops if it gets very close. Cars
on a bridge deck and under it do not slow each other down. If you write your
own multi-car driver, it needs something similar.
