# Event camera

An event camera (also called a DVS, dynamic vision sensor) has no frames. Each
pixel works on its own and fires an **event** $(x, y, t, p)$ whenever its
log-brightness has changed by a contrast threshold since its last event:
polarity $p$ = ON when it got brighter, OFF when darker. Event cameras react in
microseconds and do not blur — interesting for fast racing cars.

The simulator adds one as a sensor of its own (own lens, size and mount), by
default on the ego only:

```python
env = gym.make("scuderia-v0", ..., produce_events=True,
               event_camera={"width": 240, "height": 135})
obs["event_counts"]   # (n, H, W, 2) uint8: ON / OFF events per pixel in this step
obs["event_x"], obs["event_y"], obs["event_t"], obs["event_p"]
                      # per car: every event of this step, time-sorted (t in sim time [s])
obs["event_total"]    # (n,) number of events in this step
```

## How it is simulated

The method follows the well-known simulators ESIM and v2e:

1. Every physics step (or several times per step with `substeps`, the poses
   interpolated) the scene is rendered as a mono image through the
   {doc}`camera` renderer.
2. Per pixel, the change of log-brightness since the last render is compared
   with the threshold. Each crossing is one event; its time is found by
   interpolating linearly between the two renders.
3. Sensor effects:
   - **threshold mismatch** — every pixel has a slightly different threshold
     (drawn once from a seed),
   - **refractory period** — after an event a pixel is blind for a short time,
   - **background activity** — random noise events.

Edges fire (barrier rings, other cars, spinning wheels); a flat floor does
not, apart from noise.

## Defaults: a Prophesee EVK4

The defaults model a **Prophesee EVK4** (Sony IMX636 sensor, 1280 × 720),
rendered at a lower resolution for speed; `preset: evk4_full` renders the full
sensor for offline datasets.

| key | default | meaning |
|---|---|---|
| `width`, `height` | 320, 180 (ROS bridge: 160 × 90) | image size [px] |
| `model`, `hfov_deg` | `pinhole`, 70 | about a 4.5 mm lens on the IMX636 |
| `threshold` | 0.22 | contrast threshold in log units (≈ 25 %), set by the sensor's `bias_diff_on/off` |
| `threshold_sigma` | 0.03 | per-pixel threshold mismatch |
| `refractory_s` | 1e-4 | refractory period [s] (`bias_refr`) |
| `noise_hz` | 0.1 | background events per pixel and second |
| `substeps` | 1 | renders per physics step |
| `agents` | `ego` | `ego` or `all` |

These are **typical** sensor values, not a calibration — set them from your
own sensor's biases.

## Timing and cost

A real sensor resolves microseconds. Here event times are interpolated between
renders, so their accuracy depends on the render rate: at 100 Hz physics and
5 m/s the car moves 5 cm between renders. For finer timing raise `substeps` or
shorten the physics step. Each substep costs one mono render, so the event
camera is more expensive than the frame camera; it is well suited to datasets
and evaluation.

Not modelled: anything the renderer does not draw (flicker, real texture,
motion blur of the scene).

## In ROS 2

With `event_camera:=true` the bridge publishes:

- `/ego_racecar/event_camera/events` — `event_camera_msgs/EventPacket`,
  Prophesee **EVT 3.0** encoding, one packet per physics step, as the
  Metavision ROS 2 driver publishes it. Every packet starts with the full time
  and row, so it decodes on its own; the encoding is checked against the
  official decoder.
- `/ego_racecar/event_camera/image` — an event frame accumulated at 30 Hz (ON
  white, OFF blue) for RViz and Foxglove.
- `/ego_racecar/event_camera/camera_info`.

The numba simulator and the JAX twin implement the same model; with the same
seed their per-pixel event counts agree on more than 99.9 % of the pixels.
