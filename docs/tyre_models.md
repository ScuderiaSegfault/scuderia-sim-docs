# Tyre models

The STD and STD4W models compute each tyre's forces from its slip. Four tyre
models are available; you pick one with the `tire_model` setting (or
`std_tire_model` in the vehicle file). All of them map the longitudinal slip
ratio $\kappa$, the slip angle $\alpha$ and the normal load $F_z$ to a
longitudinal force $F_x$ and a lateral force $F_y$.

| setting | model | character |
|---|---|---|
| `full_pacejka_combined` | full Pacejka "Magic Formula" with combined slip | highest fidelity, most coefficients; the default |
| `simplified_combined` | reduced Magic Formula | fewer coefficients, good for controller development |
| `brush_combined` | brush model with friction ellipse | compact, intuitive, cheap |
| `dugoff_combined` | Dugoff model | analytical, control-friendly |

```{admonition} About parameter values
:class: note

The equations and coefficient *names* are documented here. Fitted coefficients
for our tyres are not published.
```

## Full Pacejka (combined slip)

Pure-slip forces $F_{x0}(\kappa)$ and $F_{y0}(\alpha)$ from the Magic Formula,
then combined-slip weighting functions that reduce each force when the other
direction is also used:

$$
F_x = G_{x\alpha}\, F_{x0}, \qquad
F_y = G_{y\kappa}\, F_{y0} + S_{v\kappa}
$$

The Magic Formula itself has the familiar shape

$$
F_0 = D \sin\bigl(C \arctan\bigl(B s - E\,(B s - \arctan(B s))\bigr)\bigr) + S_v
$$

with stiffness factor $B$, shape factor $C$, peak $D \propto \mu F_z$,
curvature $E$ and shifts. In this full form, the force is homogeneous in $F_z$
— two half-loaded corners give the same force as one fully-loaded axle —
which is why STD4W reduces exactly to STD with this tyre.

## Simplified combined

The same structure with fewer coefficients:

$$
F_{x0} = \mu F_z \sin\bigl(C_x \arctan(B_x \kappa)\bigr), \qquad
F_{y0} = \mu F_z \sin\bigl(C_y \arctan(B_y \alpha)\bigr)
$$

followed by a cosine-shaped combined-slip weighting.

## Brush combined

A linear stiffness per direction, saturated with `tanh`, then limited by a
friction ellipse:

$$
F_{x,lin} = C_{sx} \tanh\!\left(k_\kappa \frac{\kappa}{\sigma_{sat}}\right) \sigma_{sat}, \qquad
F_{y,lin} = C_{sy} \tanh\!\left(k_\alpha \frac{\alpha}{\alpha_{sat}}\right) \alpha_{sat}
$$

$$
\rho = \left(\left|\frac{F_{x,lin}}{\mu F_z}\right|^p + \left|\frac{F_{y,lin}}{\mu F_z}\right|^p\right)^{1/p}
$$

If $\rho > 1$, both forces are scaled by $1/\rho$, so the total force never
exceeds the friction limit.

## Dugoff combined

Linear forces from regularised slips, multiplied by a friction-utilisation
factor:

$$
F_{x,lin} = C_{sx}\, s_{x}, \qquad F_{y,lin} = C_{sy} \tan\alpha
$$

$$
\lambda = \mathrm{clip}\!\left(\frac{\mu F_z}{2\sqrt{F_{x,lin}^2 + F_{y,lin}^2}},\ \lambda_{min},\ \lambda_{max}\right),
\qquad
\phi = \begin{cases} \lambda(2-\lambda), & \lambda < 1 \\ 1, & \lambda \ge 1 \end{cases}
$$

$$
F_x = \phi\, F_{x,lin}, \qquad F_y = \phi\, F_{y,lin}
$$

## Normal loads

The normal load on each axle (STD) or corner (STD4W) is quasi-static: the
static split from the CG position plus longitudinal load transfer
($\propto m\,a_x\,h / l_{wb}$) and, for STD4W, lateral load transfer across the
track width.

## Which tyre should I use?

- For most work: the default **full Pacejka**.
- For fast experiments and controllers that need a simple model:
  **simplified** or **brush**.
- For analytical work (e.g. deriving a controller): **Dugoff**.

Near the friction limit the models differ most. At moderate speeds — tyres in
their linear region — they agree closely, so if you compare tyre models on a
lap, drive close to the limit.

## The ST model's tyre

The ST model does not use these four models. It uses a linear cornering
stiffness per axle with a combined-slip saturation, either a friction ellipse
(`ellipse`) or a brush-like curve (`brush`).

## Further reading

- H. B. Pacejka, *Tire and Vehicle Dynamics*.
- H. Dugoff, P. S. Fancher, L. Segel (1970), tyre model for combined braking
  and cornering.
- R. Rajamani, *Vehicle Dynamics and Control* (single-track foundations).
