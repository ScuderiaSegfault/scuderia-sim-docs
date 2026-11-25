# Vehicle models

The simulator has four vehicle models of increasing detail. All of them share
one planar geometry and one parameter set; you pick one with the `model`
setting.

| model | name | states | when to use it |
|---|---|---|---|
| `ks` | kinematic single track | 5 | planning prototypes, low speed, no tyre physics |
| `st` | dynamic single track | 7 | yaw and side-slip dynamics without wheel spin |
| `std` | single track drift | 9 | traction, wheel spin, braking, drifting, motor-current control |
| `std4w` | four-wheel (two-track) drift | 11 | torque vectoring, brake vectoring, per-wheel forces |

```{admonition} About parameter values
:class: note

The tables on this page list **which** parameters exist and what they mean.
The identified values for our car are not published here.
```

## Geometry: the single-track ("bicycle") model

`ks`, `st` and `std` lump the two wheels of each axle into one wheel on the
centre line of the car.

```{figure} assets/bicycle_model_diagram.png
:alt: single-track model with CG, axle distances l_f and l_r, velocity v, slip angle beta, steering delta and wheel slip angles

The single-track model. $l_f$ and $l_r$ are the distances from the centre of
gravity (CG) to the front and rear axle, $v$ the velocity at the CG, $\beta$ the
body slip angle, $\delta$ the steering angle, $r=\dot\psi$ the yaw rate and
$\alpha_f$, $\alpha_r$ the wheel slip angles.
```

## Geometry: the two-track ("plate") model

`std4w` treats the body as a rigid plate with four independent wheel corners
(front-left, front-right, rear-left, rear-right). It adds the front and rear
track widths $t_f$, $t_r$. Each corner has its own tyre forces, so a
difference between left and right creates a yaw moment — the basis of torque
and brake vectoring.

```{figure} assets/plate_model_diagram.png
:alt: two-track plate model with four wheel corners FL, FR, RL, RR and track widths t_f and t_r

The two-track model with its four corners and track widths.
```

## Common parameters

| symbol | meaning |
|---|---|
| $l_f$, $l_r$ | CG to front / rear axle; wheelbase $l_{wb}=l_f+l_r$ |
| $h$ | CG height (longitudinal load transfer) |
| $m$ | vehicle mass |
| $I_z$ | yaw moment of inertia |
| $\delta_{min}, \delta_{max}$ | steering angle limits |
| $\dot\delta_{min}, \dot\delta_{max}$ | steering rate limits |
| $v_{switch}$ | speed above which the acceleration becomes power-limited |
| $a_{max}$ | maximum acceleration |
| $v_{min}, v_{max}$ | speed limits (reverse and forward) |
| $\mu$ | peak friction coefficient |

## KS — kinematic single track

The rear wheel follows exactly the direction the body points: no side slip,
no tyre forces.

States $\mathbf{x} = [X,\ Y,\ \delta,\ v,\ \psi]^T$ — position of the CG,
steering angle, speed and heading. Inputs: steering rate and acceleration.

$$
\dot X = v\cos\psi, \qquad
\dot Y = v\sin\psi, \qquad
\dot\delta = u_0, \qquad
\dot v = u_1, \qquad
\dot\psi = \frac{v}{l_{wb}}\tan\delta
$$

## ST — dynamic single track

Adds the yaw rate $r$ and the body slip angle $\beta$: the car can now travel
at an angle to its heading. Lateral tyre forces come from the slip angles with
a linear cornering stiffness per axle ($C_{S,f}$, $C_{S,r}$), limited by a
combined-slip saturation (friction ellipse or brush-type).

States $\mathbf{x} = [X,\ Y,\ \delta,\ v,\ \psi,\ r,\ \beta]^T$.

At very low speed the dynamic equations become singular, so ST switches to the
kinematic model below a small speed threshold. The switch is a hard one; for
manoeuvres that hover around that speed, prefer STD (which blends smoothly).

## STD — single-track drift model

Adds the **wheel speeds** of the front and rear axle. Each wheel has its own
rotational inertia, so it can spin up (wheel spin) or lock (lock-up). Traction
and braking come out of the tyre model instead of being imposed directly.

States $\mathbf{x} = [X,\ Y,\ \delta,\ v,\ \psi,\ r,\ \beta,\ \omega_f,\ \omega_r]^T$.

Wheel dynamics, with wheel radius $R_w$, wheel inertia $I_{yw}$ and the drive
or brake torques $T_f$, $T_r$:

$$
\dot\omega_f = \frac{-R_w F_{x,f} + T_f}{I_{yw}}, \qquad
\dot\omega_r = \frac{-R_w F_{x,r} + T_r}{I_{yw}}
$$

Longitudinal slip ratios (the denominator has a small floor so the ratio stays
finite near standstill):

$$
s_f = \frac{R_w \omega_f}{u_{w,f}} - 1, \qquad
s_r = \frac{R_w \omega_r}{u_{w,r}} - 1
$$

with the wheel contact speeds

$$
u_{w,f} = \max\bigl(0,\ v_x\cos\delta + (v_y + l_f r)\sin\delta\bigr), \qquad
u_{w,r} = \max(0,\ v_x)
$$

The slip ratio and slip angle of each wheel go into one of the
{doc}`tyre models <tyre_models>`. At low speed STD blends smoothly into the
kinematic model (a `tanh` weight), so there is no hard switch.

Additional STD parameters: wheel radius $R_w$, wheel/drivetrain inertia
$I_{yw}$, the front/rear split of drive and brake torque, the tyre model and
its coefficients, and — for current control — the motor torque constant times
gear ratio $K_{tG}$ and the current limit $I_{max}$ ({doc}`control_modes`).

### Optional mechanical brakes

STD can take two extra action columns, a front and a rear brake torque, on top
of the braking that comes from the motor. The action row then is
`[steer, drive, brake_front, brake_rear]`. Off by default.

## STD4W — four independent corners

Extends STD to four wheel contacts. Each corner has its own normal load
(longitudinal load transfer as in STD plus a lateral split across the track
width), its own slip angle and slip ratio, and its own tyre-force evaluation
with the same four tyre models. The yaw equation gains the lever arms of
left/right force differences; under symmetric commands these vanish and
STD4W reduces to STD.

States: the seven chassis states plus four wheel speeds
$\omega_{FL}, \omega_{FR}, \omega_{RL}, \omega_{RR}$ (11 in total).

The action row always has **10 columns**:

| columns | meaning | active when |
|---|---|---|
| 0 | steering command | always |
| 1 | one drive command (interpreted by the control mode) | `motor_mode: single` |
| 2–5 | drive torque per wheel FL, FR, RL, RR | `motor_mode: four` (torque vectoring) |
| 6–9 | brake torque per wheel, added to motor braking | always |

Additional parameters: front and rear track width, the left/right drive and
brake torque splits, per-corner brake torque limits and a per-wheel drive
torque limit.

```{note}
STD4W gives you the **actuators** an ABS, ESP or torque-vectoring controller
would drive. No such control logic is built in — that is yours to write.
Load transfer is quasi-static; there are no roll, pitch or heave states.
```

## Integration

The models are integrated with RK4 (default), RK3 or explicit Euler. STD and
STD4W can take several sub-steps per physics step for stiffness (the wheel
dynamics are fast); the sub-step count is a setting.

## Steering and actuator dynamics

The steering input passes through a short delay and a steering controller, and
the steering angle is rate- and angle-limited, as on the real servo. The
published "actual steering angle" therefore lags the command. Acceleration is
limited by $a_{max}$ and, above $v_{switch}$, by a constant-power limit.
