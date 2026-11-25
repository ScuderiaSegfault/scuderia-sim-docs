# Sensors overview

Every sensor is computed from the **same physics step** as the car's pose. A
scan, an odometry message and a camera frame taken at the same step describe
the same instant — there is no artificial lag between them unless a sensor's
own frame rate says so.

| sensor | default | rate | how it is computed | page |
|---|---|---|---|---|
| 2D LiDAR | on, every car | every physics step | ray marching on the map's distance transform, plus the other cars' rectangles | {doc}`lidar2d` |
| 3D LiDAR | off; ego (or all cars) | own rate (10 Hz) | ray marching against the 2.5D world: floor, extruded walls, bridges, car boxes | {doc}`lidar3d` |
| camera (RGB/mono, depth, labels) | off; all cars or ego | own rate (30 Hz) | one LiDAR-style scan per frame + per-pixel ray tests | {doc}`camera` |
| event camera | off; ego | events every step | brightness changes between renders, with sensor noise | {doc}`event_camera` |
| IMU, odometry, wheel speeds, GPS | on (some opt-in) | every physics step | from the vehicle state | {doc}`state_sensors` |

## Frame rates and the physics step

The physics runs at a fixed step (10 ms by default). A sensor with its own rate
— the camera at 30 Hz, the 3D LiDAR at 10 Hz — takes a frame on the first
physics step at or after each of its frame times and **holds** that frame in
between. Each such sensor reports:

- a **stamp**: the simulated time of the frame, and
- a **new** flag: whether this step produced a new frame.

That is what a detector consuming frames, or a ROS node publishing them,
needs. Frames can only be taken on a physics step, so a sensor's rate is
capped at the step rate (100 Hz by default). For a faster camera, shorten the
step: with `timestep=0.005`, a 150 Hz camera delivers 150 frames per simulated
second.

## Everything sees everything

- Every car's 2D LiDAR sees the other cars (ray cast onto their rectangles).
- The camera and event camera draw the other cars as 3D bodies with wheels.
- The 3D LiDAR sees the other cars as boxes.
- On {doc}`2.5D maps <../map_2p5d>` all sensors see the bridges, and a car
  only appears in another car's 2D scan when its height range crosses that
  scan's plane.

## Sensor mounts

The camera, event camera and 3D LiDAR each have a mount (`mount_x`,
`mount_y`, `mount_height` / `mount_z`, and roll / pitch / yaw angles) in the
car's body frame. On a ramp or a banked curve the sensors tilt with the car.
