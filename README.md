# Scuderia Sim — documentation

Documentation for the **Scuderia** simulator stack for 1:10 autonomous racing
(F1TENTH / RoboRacer-style cars), built by the Scuderia Segfault team at TU Wien.

> **About the code:** this repository holds the **documentation only**. The
> source code of the simulators and the ROS 2 bridge will be released when the
> accompanying paper is published. Until then you can read here what the stack
> does and how it works, so you are ready to use it on day one.

**Read the docs:** <https://REPLACE-ME.readthedocs.io> *(link will be added once the site is live)*

## What is documented

| part | what it is |
|---|---|
| **Scuderia Gymnasium** | the main simulator: a fast numba-compiled Gymnasium environment (`scuderia-v0`) with several vehicle and tyre models, three control modes and 1–3+ cars |
| **Sensors** | 2D LiDAR, 3D LiDAR (RoboSense Airy presets), on-board camera (RGB / mono, depth, semantic labels, OAK-D S2 preset), event camera, IMU, odometry, GPS |
| **2.5D maps** | bridges to drive over and under, stacked bridges, ramps and banked curves |
| **JAX twin** | the same physics and sensors in JAX: batched, GPU-capable and differentiable |
| **ROS 2 bridge** | runs the simulator as a ROS 2 Jazzy node with the real car's topics, RViz and Foxglove views |
| **Testing** | drive-and-sensor checks for every map, control mode and car count |

## Building the docs locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
# open docs/_build/html/index.html
```

The build needs only Sphinx, MyST and the theme; it does not need (or import)
the simulator.

## License

The documentation is released under the MIT License (see `LICENSE`), the same
license the simulator code is derived under (the original
[F1TENTH Gym](https://github.com/f1tenth/f1tenth_gym)).
