<div align="center">

# FlexAgX

### Adaptive AgX Tone Mapping for ReShade

  <img src="https://img.shields.io/badge/ReShade-5.9.0%2B-blue?style=for-the-badge&logo=reshade&logoColor=white" alt="ReShade Version">
  <img src="https://img.shields.io/badge/Version-1.7.1-emerald?style=for-the-badge" alt="Version 1.7.1">
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="MIT License">
  <img src="https://img.shields.io/badge/API-DX11%20%7C%20DX12%20%7C%20Vulkan%20%7C%20OpenGL-orange?style=for-the-badge" alt="Supported APIs">

*Crafted for pure visual clarity. Film-grade AgX color science meets real-time gaming.*

[Key Features](#-key-features) • [Visual Experience](#%EF%B8%8F-visual-experience) • [Installation](#-installation) • [Configuration](#%EF%B8%8F-configuration) • [Acknowledgements](#-acknowledgements)

<img width="1774" height="887" alt="Logo" src="https://github.com/user-attachments/assets/a719c7ff-77d1-4443-80b6-8a5c8901c2c1" />


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
| ----- | ----- | ----- |
| **Main** | `Game Colour Curve` | Input encoding curve used by the game (`sRGB` or `Gamma 2.2`). |
|  | `Monitor Colour Curve` | Output display gamma target (`sRGB` or `Gamma 2.2`). |
|  | `Strength` | Master blend slider ($0\%$ to $100\%$). |
| **Brightness** | `Brightness` | Manual exposure adjustment ($\pm 2.0\,\text{EV}$). |
|  | `Auto Brightness` | Automated exposure adaptation strength ($0\%$ to $100\%$). |
|  | `Hold Brightness` | Freeze adaptation at current exposure level. |
| **Highlights & Shadows** | `Auto Highlights` | Dynamically calculate highlight roll-off point from scene histogram. |
|  | `Highlight Start` | Manual highlight knee position ($0.40$ to $0.55$). Used when Auto Highlights is off. |
|  | `Shadow Detail` | Softens shadow crushing via Hermite toe blending ($0\%$ to $100\%$). |
| **Colour** | `Hue Stability` | Restores original hue angle post-tone curve ($0\%$ to $100\%$). |
|  | `Vivid Colour Softening` | Threshold where extreme saturation begins compressing ($0.60$ to $0.95$). |
|  | `Colour Temperature` | White balance temperature adjustment ($2000\,\text{K}$ to $12000\,\text{K}$). |

## 📜 Acknowledgements

FlexAgX builds upon mathematical formulations and color research established by the following creators and visual engineers:

* **Troy Sobotka:** Creator of the AgX tone-mapping approach, from which the non-linear inset/outset matrix transformations and 6th-order sigmoid response curves are derived.

* **Björn Ottosson (2020):** Formulated the Oklab perceptual color space, including the RGB-to-LMS/Oklab matrices, cube-root non-linearities, and gamut-boundary coefficients.

* **Kim et al. (2002):** Provided the Planckian locus cubic approximation fits for chromaticities `x(T)` and `y(T)` used in kelvin white-balance evaluation.

* **Jorge Jimenez (2014):** Created Interleaved Gradient Noise (IGN), utilized for high-efficiency sub-sampled gradient dithering.

* **Bruce Lindbloom:** Published the widely adopted D65 XYZ-to-linear-sRGB transformation matrix and standard colorimetry reference tables.

* **crosire:** Developer of the ReShade framework, infrastructure, texture/uniform annotations, and FX macro system.

* **IEC Standard (IEC 61966-2-1):** Standardized sRGB electro-optical and opto-electronic transfer functions.

Released under the [MIT License](LICENSE). Designed for high-fidelity real-time rendering.
