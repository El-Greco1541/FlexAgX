# Eight-pass shader source mapping

The immutable source is [reference/FlexAgX_1.2.fx](../reference/FlexAgX_1.2.fx).

| FX pass | Code-transmigration owner | Current numerical adapter | Fidelity |
|---|---|---|---|
| 1 Histogram | observer | `compute.observe` | Source-style phase/population, not FX runtime |
| 2 State | controller + tone | `SessionStore.prepare` + `compute.make_lut` | Stateful CPU approximation |
| 3 Curve | renderer | grouped `compute.render_pixels` | FX intermediate precision approximate |
| 4 Hue | renderer | grouped `compute.render_pixels` | FX intermediate precision approximate |
| 5 Detail Mean | renderer | grouped `compute.render_pixels` | Float16 intermediate approximate |
| 6 Detail Base | renderer | grouped `compute.render_pixels` | Float16 intermediate approximate |
| 7 Detail Apply | renderer | grouped `compute.render_pixels` | Float16 intermediate approximate |
| 8 Output | renderer | grouped `compute.render_pixels` | White balance/gamut/encoding approximate |

Pass 2 includes LUT construction within the original FX state shader. The CPU module separates tone synthesis as a replaceable service. The map deliberately does not fabricate CPU service-per-pixel-pass fidelity or claim identical render-target scheduling.
