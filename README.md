<div align="center">

# FlexAgX

### Adaptive tone mapping and colour restoration for ReShade

![ReShade](https://img.shields.io/badge/ReShade-5.9.0%2B-0A84FF?style=flat-square)
![Version](https://img.shields.io/badge/version-1.7.1-30D158?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-8E8E93?style=flat-square)
</div>

---

## ✨ Overview

FlexAgX gives your games a more natural, filmic response to light. Instead of harsh highlights that clip to flat white, bright areas roll off smoothly into the range your display can show, while shadows keep their detail and colours stay true to their original hue.

Every frame, FlexAgX studies the brightness distribution of the scene, tracks a smoothed exposure level over time, and builds a custom tone curve to match. The result adapts naturally as you move between dark caves and bright outdoor scenes, without the sudden jumps that plague simpler post-processing filters.

---

## 🌟 Key Features

### 🎞️ HDR-like Image
- Highlights are softly compressed rather than clipped, delivering the depth and dynamic range associated with HDR presentation on standard displays.

### 🧠 Adaptive Exposure
- A centre-weighted histogram drives automatic brightness that tracks the scene, with built-in scene-cut detection for sudden changes like cutscenes or loading transitions.

### 🌑 Shadow Detail Preservation
- Dark regions retain texture and depth instead of collapsing into black.

### 🎨 Hue Stability
- Colours hold their character through the tone curve, and neutral greys stay neutral.

### 🌈 Vivid Colour Softening
- Intensely saturated colours are gently brought into the displayable gamut, avoiding harsh, cut-off hues.

### 🌡️ Colour Temperature Control
- Warm or cool the image with a white-balance adjustment anchored to a 6500 K neutral point.

### 🔲 Dithering
- Triangular, interleaved-gradient-noise dithering reduces banding in smooth gradients.

### 🛡️ Safe on HDR Displays
- When an HDR colour space is detected, FlexAgX steps aside and passes the image through untouched.

---

## 👁️ The Visual Difference

Without FlexAgX, bright skies and sunlit surfaces often flatten into pale, featureless patches, while deep shadows sink into murky black. Saturated colours can look electric and oversharpened at their peaks, and a sudden change in brightness can make the image feel jarring.

With FlexAgX enabled, the same scene breathes. Skies keep their gradients and cloud detail. Sunlit stone retains its texture rather than washing out. Shadowed corners reveal the shapes hiding within them. Vivid reds and blues remain rich but no longer glow beyond what the screen can honestly reproduce. Exposure settles gradually as you move through a scene, so the image feels consistent rather than reactive.

The overall impression is of a picture that has been carefully graded for the room you are playing in: fuller, calmer, and more cinematic, without looking over-processed.

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

---

## 🖥️ System Requirements

| Component | Requirement |
|---|---|
| **ReShade** | 5.9.0 or newer |
| **Graphics API** | Direct3D 11 (feature level 11.0), Direct3D 12, OpenGL 4.3, or Vulkan |
| **Shader support** | Compute shaders and storage images |
| **Display** | SDR displays are fully supported; HDR output is passed through unchanged |

---

## 📦 Installation

1. 📥 Download `FlexAgX.fx` from this repository.
2. 📂 Copy the file into your ReShade shaders folder, typically `reshade-shaders/Shaders/`.
3. 🎮 Launch your game and open the ReShade overlay (the default key is **Home**).
4. 🔍 In the **Home** tab, find **FlexAgX** and enable it.
5. 🧭 For best results, place FlexAgX late in the effect chain, after other colour-grading effects, so it works on the final image.

---

## 🎛️ Configuration

| Setting | Category | Purpose |
|---|---|---|
| **Game Colour Curve** | Main | The brightness encoding your game uses |
| **Monitor Colour Curve** | Main | The brightness encoding your monitor uses |
| **Strength** | Main | Blends the effect with the original image |
| **Dithering** | Main | Reduces colour banding in gradients |
| **Brightness** | Brightness | Makes the whole image brighter or darker |
| **Auto Brightness** | Brightness | Strength of automatic exposure adjustment |
| **Hold Brightness** | Brightness | Freezes exposure and highlight position |
| **Auto Highlights** | Highlights and Shadows | Chooses the highlight roll-off point automatically |
| **Highlight Start** | Highlights and Shadows | Manual roll-off point, used when Auto Highlights is off |
| **Shadow Detail** | Highlights and Shadows | Keeps dark areas from turning flat black |
| **Hue Stability** | Colour | Prevents colours from drifting to other hues |
| **Vivid Colour Softening** | Colour | Lower values soften very saturated colours more |
| **Colour Temperature** | Colour | Warms or cools the image |

---

## 🙏 Acknowledgments

FlexAgX builds on the work of many people and projects. Thank you to:

- **Björn Ottosson** for the Oklab perceptual colour space, whose matrices, cube-root non-linearity, and gamut-boundary formulas form the backbone of the colour pipeline.
- **Troy Sobotka** for the AgX tone-mapping approach, whose inset and outset matrices and sigmoid curve inspired the tone mapping.
- **Kim et al. (2002)** for the Planckian locus approximation used to derive colour-temperature white points.
- **Jorge Jimenez** for interleaved gradient noise, used for dithering.
- **crosire and the ReShade team** for the ReShade FX framework, which makes effects like this possible.
- **Bruce Lindbloom** for the widely published XYZ-to-sRGB colour matrices.
- **IEC 61966-2-1**, the standard defining the sRGB transfer functions.
- The **community**, whose shared techniques for fullscreen triangles and von Kries-style white balancing make this shader possible.

---

## 📄 License

FlexAgX is released under the **MIT License**.

Copyright © 2026 El-Greco1541

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, subject to the conditions set out in the full license text. See [LICENSE](LICENSE) for details.

---

<div align="center">

Made with care for better-looking games. ✨

</div>
