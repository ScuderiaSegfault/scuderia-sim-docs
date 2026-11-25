# Code release

```{admonition} Short version
:class: tip

The code will be published together with the paper that describes the
simulator. This repository is the documentation, released first.
```

## What will be released

When the accompanying paper is published, we plan to release:

- **Scuderia Gymnasium** — the numba simulator, the `scuderia-v0` Gymnasium
  environment, the shipped maps and their centrelines, the example scripts and
  the test tools described in {doc}`testing`.
- **The JAX twin** — the JAX implementation with its parity tests and
  benchmarks.
- **The ROS 2 bridge** — the ROS 2 Jazzy package with its launch files,
  configuration files, RViz configurations, Foxglove layouts and car meshes.

The links to the repositories will be added to this page and to the README.

## What this documentation already covers

Everything a user needs to understand the stack: the architecture, the
vehicle and tyre models (concepts and equations), the control modes, every
sensor and how it is simulated, the 2.5D map format, the ROS 2 topics and
parameters, and the test procedures. Short usage snippets show how the
interfaces will look.

## What this documentation does not contain

- **Source code.** No Python package, examples or API reference yet.
- **Identified vehicle and tyre parameters.** The models are described with
  their parameters' *names and meanings*; the fitted values for our car are
  not part of this documentation.

## Until then

- Read {doc}`overview` and {doc}`usage` to plan your project.
- Prepare an Ubuntu 24.04 machine with ROS 2 Jazzy if you want the ROS side
  ({doc}`installation`).
- The upstream project this simulator grew from, the
  [F1TENTH Gym](https://github.com/f1tenth/f1tenth_gym), is a good place to
  get used to the Gymnasium-style racing interface.
