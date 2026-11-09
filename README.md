<div align="center">

# FlexAgX

### Adaptive AgX Tone Mapping for ReShade

<p align="center">
  <img src="https://img.shields.io/badge/ReShade-5.9.0%2B-00E5FF?style=flat&labelColor=111827&logoColor=white" alt="ReShade Version">
  <img src="https://img.shields.io/badge/Version-1.9.2-34D399?style=flat&logo=semanticrelease&logoColor=white&labelColor=111827" alt="Version 1.9.2">
  <img src="https://img.shields.io/badge/License-MIT-C084FC?style=flat&logo=opensourceinitiative&logoColor=white&labelColor=111827" alt="MIT License">
  <img src="https://img.shields.io/badge/APIs-DX11%20%7C%20DX12%20%7C%20Vulkan%20%7C%20OpenGL-FB923C?style=flat&logo=vulkan&logoColor=white&labelColor=111827" alt="Supported APIs">
</p>

*Crafted for pure visual clarity. Film-grade AgX color science meets real-time gaming.*

[Key Features](#-key-features) • [Visual Experience](#%EF%B8%8F-visual-experience) • [Installation](#-installation) • [Configuration](#%EF%B8%8F-configuration) • [Acknowledgements](#-acknowledgements)

</div>

## 🌟 Overview

**FlexAgX** brings the advanced filmic color science of Troy Sobotka’s **AgX** tone-mapping pipeline to real-time rendering. By intelligently reshaping brightness and color through custom sigmoid curves and inset color spaces, FlexAgX replaces harsh, digital clipping with organic light roll-off. Inspired by professional motion-picture workflows and modern perceptual color spaces, it dynamically adapts to every frame—preventing highlight blowouts, recovering shadow detail, and compressing vivid colors without hue distortion.

## ✨ Key Features

* **AgX-Derived Filmic Tone Curve**

  Utilizes specialized sigmoid response curves mapped on a log luminance axis to simulate organic film emulsion response, ensuring bright highlights roll off gracefully rather than hard-clipping.

* **Oklab Perceptual Gamut Mapping**

  Leveraging Björn Ottosson’s Oklab color space, vivid and over-saturated colors soft-roll into your monitor's display gamut using analytical Halley & Newton boundary solvers, preventing unnatural hue shifts.

* **Highlight Shoulder & Shadow Detail**

  A dynamic Hermite curve seamlessly blends low-end shadows with high-end highlights, protecting dark areas from crushing to flat black while maintaining pristine contrast.

* **Advanced Auto White Balance**

  Removes colour casts from your scene’s lighting automatically. Three analysers vote on the light colour, and a correction only happens when at least two agree. Changes arrive gradually,  so the image stays natural, and scenes without clear evidence are left alone.

* **Von Kries White Balance**

  Adjust scene white point seamlessly from 2000K to 12000K using a high-precision cubic fit of the Planckian locus.

* **Sub-Sampled Dithering**

  Supports 8-bit, 10-bit, and FP16 buffer targets using Interleaved Gradient Noise (IGN), tapered dynamically at extreme luminance points to prevent gradient banding.

* **Zero-Fail Architecture**

  Every dynamic lookup table (LUT) passes through a multi-point validation suite every frame. If an illegal slope or monotonicity breakdown is detected, FlexAgX gracefully degrades through tiered fallbacks to ensure uncompromised stability.

## 👁️ Visual Experience

Once enabled, FlexAgX instantly transforms your game's presentation, delivering a striking, **HDR-like image** even on standard SDR displays:

* **Graceful Highlight Roll-Off:** Blinding light sources, explosions, and sunny skies transition smoothly into white instead of clipping into harsh, flat plateaus.

* **Preserved Shadow Detail:** Deep, murky shadows open up to reveal environmental textures and subtle details without looking washed out or crushed.

* **Controlled Color Vibrancy:** Highly saturated colors are reined in organically to fit within your display's color gamut, ensuring rich reds, blues, and neon lights remain vibrant and distinct without blowing out into incorrect hues.

* **Cinematic Cohesion:** The interplay of auto-exposure, white balance, and perceptual gamut compression gives games a rich, film-emulated atmosphere of depth and realism.

<table>
  <tr>
    <td align="center"><b>Before</b></td>
    <td align="center"><b>After</b></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/5fab81c5-e8d2-4d8a-93d9-ad3b575a0f61" alt="Before" /></td>
    <td><img src="https://github.com/user-attachments/assets/34c4d945-956e-48e0-8a7c-5d04700df5cd" alt="After" /></td>
  </tr>
</table>
<table>
  <tr>
    <td align="center"><b>Before</b></td>
    <td align="center"><b>After</b></td>
  </tr>
  <tr>
    <td><img src="https://github.com/user-attachments/assets/b1e77469-d456-4a42-9d43-bf3319835db6" alt="Before" /></td>
    <td><img src="https://github.com/user-attachments/assets/8dc278e6-e7a3-446a-8211-3c8e57ee1f00" alt="After" /></td>
  </tr>
</table>

## 📦 Installation

### Requirements

* **ReShade:** 5.9.0 or newer

* **Graphics API:** DirectX 11, DirectX 12, OpenGL 4.3+, or Vulkan

### Setup

1. Download `FlexAgX.fx` from the [Releases](../../releases) tab.

2. Move the file into your game's ReShade shader folder:

   ```
   <GameDirectory>/reshade-shaders/Shaders/
   ```

3. Launch your game, open the ReShade overlay (`Home` key by default), and select `FlexAgX`.

## ⚙️ Configuration

FlexAgX provides intuitive controls grouped for quick tuning:

| Section | Parameter | Description |
|---|---|---|
| Main | `Game Colour Curve` | Input encoding curve used by the game (`sRGB` or `Gamma 2.2`). |
| | `Monitor Colour Curve` | Output display gamma target (`sRGB` or `Gamma 2.2`). |
| | `Strength` | Master blend slider (0 to 100). |
| | `Dithering` | Adds faint noise to smooth gradients to prevent colour banding (on or off). |
| Brightness | `Brightness` | Manual exposure adjustment (±2.0, EV). |
| | `Auto Brightness` | Automated exposure adaptation strength (0 to 100). |
| | `Hold Brightness` | Freeze adaptation at current exposure level. |
| Highlights & Shadows | `Auto Highlights` | Dynamically calculate highlight roll-off point from scene histogram. |
| | `Highlight Start` | Manual highlight knee position (0.40 to 0.55). Used when Auto Highlights is off. |
| | `Shadow Detail` | Softens shadow crushing via Hermite toe blending (0 to 100). |
| Colour | `Hue Stability` | Restores original hue angle post-tone curve (0 to 100). |
| | `Vivid Colour Softening` | Threshold where extreme saturation begins compressing (0.60 to 0.95). |
| | `Colour Temperature` | White balance temperature adjustment (2000 K to 12000 K). Disabled while Auto White Balance is on. |
| | `Auto White Balance` | Automatically removes the colour tint from the scene's lighting. Off by default. |
| | `Auto White Balance Strength` | How strongly the automatic correction is applied (0 to 100). Only works when Auto White Balance is on. |

## 📜 Acknowledgements

FlexAgX is built on the work of many researchers, engineers, and open projects. We are grateful to everyone listed below.

- **ReShade**: the post-processing framework FlexAgX runs in. Thanks to the ReShade developers and community.
- **Björn Ottosson**: the Oklab perceptual colour space. The LMS matrices and cube-root transform used for lightness, chroma, and hue calculations follow this work.
- **Björn Ottosson**: the Oklab cusp-based gamut boundary approach, used for keeping very vivid colours within the displayable range.
- **IEC 61966-2-1**: the sRGB transfer function, used for encoding and decoding display colour.
- **Johannes von Kries**: von Kries chromatic adaptation (1902), used for the diagonal white-balance correction in LMS space.
- **Troy Sobotka**: AgX, and its Blender implementation. The inset and outset colour matrices and the sigmoid polynomial that shapes the tone curve follow this approach.
- **Hermite spline**: cubic Hermite splines, used to build the smooth shoulder and toe curves.
- **Oklab hue correction**: keeps colours from drifting to a different hue when they are brightened, darkened, or muted.
- **Graham Finlayson and Elisabetta Trezzi**: Shades of Grey (2004), which uses a Minkowski p-norm to estimate the scene illuminant.
- **Joost van de Weijer, Theo Gevers, and Arjan Gijsenij**: Grey Edge (2007), which estimates the illuminant from edge statistics.
- **Edwin Land and John McCann**: Max-RGB / White Patch from their Retinex work (1971), used for the highlight-based estimator.
- **Calvin McCamy**: McCamy's approximation (1992) for converting chromaticity to correlated colour temperature.
- **Photographic convention**: middle grey, the long-standing practice of mapping average scene brightness to about 18% grey.
- **Histogram-based metering**: uses luminance percentiles to measure the scene and detect large changes between frames.
- **Jorge Jimenez**: Interleaved Gradient Noise (2014), used for dithering to prevent colour banding.

Released under the [MIT License](LICENSE)
