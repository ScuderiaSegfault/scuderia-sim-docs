# 2D LiDAR

A planar laser scanner, like the Hokuyo or similar units on F1TENTH cars. It is
on for every car by default.

| setting | default | meaning |
|---|---|---|
| beams | 1080 | number of beams in one scan |
| field of view | 4.7 rad (about 270°) | centred on the car's heading |
| mount offset | 0 m | distance of the scanner ahead of the car's reference point |
| maximum range | 30 m | beams that hit nothing return the maximum range |
| noise | small Gaussian noise per beam | white noise on every range |

## How it works

1. **Distance transform.** When a map is loaded, the simulator computes, for
   every free cell, the distance to the nearest wall cell (a Euclidean
   distance transform).
2. **Ray marching.** For each beam, the simulator starts at the sensor and
   jumps forward along the beam by the distance-transform value at the current
   point. Far from walls the jumps are large; near a wall they shrink. When the
   distance falls below a small threshold, the beam has hit the wall. This is
   *sphere tracing*, and it needs only a few lookups per beam.
3. **Other cars.** Each beam is then intersected with the rectangles of the
   other cars. If a car is closer than the wall, the beam returns the
   distance to the car.
4. **Noise.** Gaussian noise is added to every range.

The kernels are compiled with numba, so a full 1080-beam scan costs a fraction
of a millisecond.

## Timing: no lag

The scan is taken at the **same physics step** as the poses it is compared
with. The test tools check this directly: the scan points that land on another
car must lie on that car's box from the same step. Measured mean distance:
below 1 cm (in the Python simulator: zero). A lag of one step would show up as
about 2 cm at 2 m/s.

```{figure} ../assets/test_lidar_no_lag.png
:alt: ego's 2D LiDAR points lying on the box of the car ahead at three moments

The ego's 2D scan (red dots) on the car ahead (green box) at three moments of a
test drive: the points lie on the true box of the same step. (The dashed
outline is an older, too-large drawing of the car used in a video overlay.)
```

## Collision detection

The scan is also used for collisions: for each beam, the simulator computes an
instantaneous time-to-collision from the car's speed and the distance to the
car's own outline; a value below a small threshold is a collision with the
environment. Car–car collisions are checked separately on the cars' rectangles
(separating-axis test).

On a collision with the environment the car **stops**: its velocities (speed,
yaw rate, wheel speeds) are set to zero, while its position, steering angle
and **heading** stay as they were. So an evaluation that keeps running after a
contact (lap time, lateral error, steering rate) sees the car where and how it
hit the wall, not turned to a default heading.

## On 2.5D maps

Each car has a **level** (ground, deck 1, deck 2, …). Its 2D LiDAR traces the
distance transform of its own level's obstacle layer: a car under a bridge
sees the low parts of the ramps (too low to pass under) but not the deck
overhead; a car on the deck sees the
deck's side walls. The cost per scan is the same as on a flat map. See
{doc}`../map_2p5d`.

## In ROS 2

`/scan` (ego), `/opp_scan`, `/opp2_scan` — `sensor_msgs/LaserScan`, frame
`<namespace>/laser`. Beam count and field of view are the parameters
`scan_beams` and `scan_fov`. See {doc}`../ros2_bridge`.
