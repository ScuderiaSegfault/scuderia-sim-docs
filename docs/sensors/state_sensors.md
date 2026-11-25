# IMU, odometry, wheel speeds and GPS

These signals come directly from the vehicle state at every physics step.

## Odometry

Pose and velocity of each car:

| signal | meaning | unit |
|---|---|---|
| `x`, `y` | position in the map frame | m |
| `yaw` | heading | rad |
| `vx = v cos β` | longitudinal velocity, body frame | m/s |
| `vy = v sin β` | lateral velocity, body frame | m/s |
| `r` | yaw rate | rad/s |
| `z`, `pitch`, `roll` | height and tilt on 2.5D maps (0 elsewhere) | m, rad |

The odometry is **ground truth** — no drift, no noise. In ROS 2 it is `/odom`
(`nav_msgs/Odometry`, ego), `/opp_racecar/odom`, `/opp2_racecar/odom`.

## IMU

The simulator provides body-frame accelerations and the yaw rate. From the
vehicle derivatives:

$$
a_x = \dot v \cos\beta - v\,(\dot\beta + r)\sin\beta, \qquad
a_y = \dot v \sin\beta + v\,(\dot\beta + r)\cos\beta
$$

Two flavours:

- `a_x`, `a_y` — the clean acceleration of the CG,
- `imu_ax`, `imu_ay` — what a body-mounted accelerometer measures, including
  the centripetal terms ($a_{x,imu} = a_x - r\,v_y$, $a_{y,imu} = a_y + r\,v_x$),
  with sensor noise.

The gyro channel is the yaw rate $r$ (a planar model has no roll or pitch rate).
In ROS 2 the IMU is published as `sensor_msgs/Imu` on the real car's topic,
`/phidgets/imu/data_raw`, when `publish_extra_states` is on.

## Wheel speeds, slip angle, actual steering

| signal | meaning | model |
|---|---|---|
| `omega_f`, `omega_r` | front / rear wheel angular speed [rad/s] | STD |
| `slip_angle` | body slip angle β [rad]; positive: rear sliding outward | ST, STD |
| `steer_angle` | the actual steering angle [rad] (lags the command) | all |

Wheel speeds are useful for slip-ratio estimation, traction control and
observer design. STD4W has four wheel-speed states internally; they are part of
its state vector.

In ROS 2: `/ego_racecar/wheel_speeds`, `/ego_racecar/slip_angle`,
`/ego_racecar/steer_angle_actual`, and the full state vector
`/ego_racecar/vehicle_state` `[x, y, δ, v, ψ, r, β, ω_f, ω_r]` (with
`publish_inner_states`).

## Ground-truth pose and GPS

- **Ground-truth pose** — `/ego_racecar/pose` and `/ego_racecar/gt_pose`, the
  exact pose at every physics step (with a small nominal covariance for
  filters that need one).
- **GPS** (opt-in) — `/<car>/gps_pose`, the same pose plus Gaussian noise on
  position and heading, at its own rate. Use it to study localisation and
  Kalman filters under noise.

| parameter | default | meaning |
|---|---|---|
| `gps_noise_enabled` | off | publish the noisy GPS pose |
| `gps_noise_std_xy` | 0.03 m | position noise, 1σ (RTK-like) |
| `gps_noise_std_theta` | 0.005 rad | heading noise, 1σ |
| `gps_hz` | 40 Hz | publication rate (launch files use 10 Hz) |

The car model in RViz is always placed by the ground-truth TF; GPS noise is
never applied to it.
