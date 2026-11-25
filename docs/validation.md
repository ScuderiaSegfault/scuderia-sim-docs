# Validation against the real car

The vehicle models are checked against recordings of a real 1:10 car. This
page describes **how** the validation is done and what we learned in
qualitative terms. Identified parameters and the plots that would reveal them
are not published here.

## Open-loop replay

For each recording (logged at about 30 Hz: commanded steering and speed, and
measured IMU and odometry), every model variant is driven **open loop**:

1. start from the recording's own measured initial state,
2. feed the exact command sequence the real car received,
3. never correct with a measurement.

The simulated trajectory is then compared with what the car's sensors
measured. The replay uses the simulator's production kernels, so it validates
the code you use, not a re-implementation.

The recordings cover step-steer, ramp-steer and constant speed-and-steer
manoeuvres, longitudinal and lateral.

## Error metric

For a signal $x$ (speed, yaw rate, heading, lateral acceleration) at $N$
recorded time stamps:

$$
\mathrm{RMSE}(x) = \sqrt{\frac{1}{N}\sum_{i=1}^{N}\bigl(x_{\text{sim},i} - x_{\text{meas},i}\bigr)^2}
$$

**Speed, yaw rate and lateral acceleration** are the most telling signals.
Position is compared with the car's own dead-reckoned odometry (there is no
external ground truth in this data), so open-loop position errors grow with the
length of a recording, and must be read with that in mind.

## What we learned

- On short horizons the **ST** model tracks speed and yaw rate about as well
  as the STD variants. On long, continuously turning recordings it falls
  behind in position, because tiny per-step yaw-rate differences add up lap
  after lap.
- ST's hard switch to the kinematic model at low speed is a real
  discontinuity; manoeuvres that dwell at that speed should use STD, which
  blends smoothly.
- The tyre models agree in their linear region and separate near the friction
  limit — which is where the choice of tyre model matters.
- Friction and tyre parameters dominate how well the models match. They can be
  fitted to recordings, with finite differences in the numba simulator or with
  exact gradients in the {doc}`JAX twin <jax_twin>`.

## Choosing recordings for fitting

Not every recording carries the same information about the tyres. The JAX
twin includes a selection step that scores recordings by excitation amplitude,
slip-range coverage, length and quality, and picks a small, diverse set (five
longitudinal and five lateral) greedily by **marginal gain** — five copies of
the best recording carry only one recording's worth of information.

A caveat carried into the results: the longitudinal speed measurement comes
from the motor's electrical speed, i.e. from the wheel, so a naive slip ratio
computed from it is circular. The longitudinal set is therefore the weaker of
the two.
