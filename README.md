<div align="center">
  
# FlexAgX

**Advanced Image Reconstruction & Tone Mapping for ReShade.**  
*Pro-grade dynamic range. Zero color clipping. Uncompromising fidelity.*
</div>

---

## Overview ✨

**FlexAgX** is an advanced image-reconstruction and tone-mapping shader built for ReShade 5.9.0+. Inspired by filmic color science and modern camera pipelines, FlexAgX brings an **HDR-like look** to standard dynamic range (SDR) displays—rescuing blown-out highlights, preserving rich shadow detail, and eliminating harsh color clipping without introducing unnatural haloing or flat contrast.

Unlike traditional tone mappers that shift tints or clip vivid colors into harsh digital bands, FlexAgX operates in perceptually uniform **Oklab LMS color space**. The result is smooth, organic highlight roll-offs, true-to-life hue retention, and a distinct filmic depth.

---

## Key Features 🚀

### 🌈 HDR-ish Dynamic Range Simulation
* **Pseudo-HDR Roll-off:** Curves compressed highlights smoothly into display space, yielding high-dynamic-range punch on standard SDR monitors.
* **Preserved Highlight Detail:** Retains fine textures in bright skies, explosions, and reflective surfaces without white-out blown areas.

### 🧠 Adaptive Real-Time Auto-Exposure
* **Logarithmic Histogram Analysis:** Continuously evaluates 64-bin scene luminance to adapt brightness naturally as you move between indoor and outdoor areas.
* **Scene-Cut & Guard Technology:** Built-in clip guards prevent unwanted exposure flickering during rapid lighting changes or UI pop-ups.

### 🎨 Perceptual Color Science
* **Oklab LMS Processing:** Color temperature shifts and gamut compression occur within perceptual Oklab space, preserving natural hue relationships.
* **Hue Restoration & Gamut Roll-off:** Vivid primary colors gradually soften near boundary limits rather than distorting into unnatural secondary shades.

### 🔍 Guided-Filter Local Contrast
* **Detail Preservation:** Re-introduces micro-contrast in areas flattened by heavy highlight or shadow compressions, preventing "crunchy" or over-sharpened artifacts.

---

## The Visual Difference 👁️

FlexAgX fundamentally changes how light and color interact on screen:

* **Highlights:** Instead of clipping directly to pure `#FFFFFF`, intense light sources roll off gracefully, giving sunbeams, fires, and neon lights an authentic, cinematic glow.
* **Shadows:** Midtones and shadows maintain depth without falling into flat, muddy blacks.
* **Color Stability:** Saturated lights maintain their natural hue at high intensities instead of shifting toward cyan, yellow, or magenta.

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

## System Requirements ⚙️

| Requirement | Minimum |
| :--- | :--- |
| **ReShade Version** | `5.9.0` or higher *(requires storage image reads)* |
| **Graphics API** | DirectX 11, DirectX 12, Vulkan, or OpenGL 4.3+ |
| **Bit Depth** | Supports 8-bit and 10-bit color output |

> **Note:** DirectX 9, DirectX 10, and OpenGL versions below 4.3 are **not supported**.

---

## Installation 📦

1. Download `FlexAgX.fx` from the [Releases](../../releases) section.
2. Move `FlexAgX.fx` into your game's ReShade shader folder:
   ```text
   <Game Directory>/reshade-shaders/Shaders/
   ```
3. Launch your game, open the ReShade overlay (`Home` key by default), and select **FlexAgX** from the active technique list.

---

## Configuration & Controls 🎛️

FlexAgX features intuitive parameters organized by functional category:

| Section | Parameter | Description |
| :--- | :--- | :--- |
| **Main** | Game Colour Curve | Selects the brightness curve used by the game engine (`sRGB` or `Gamma 2.2`). Most modern games use sRGB. |
| **Main** | Monitor Colour Curve | Selects the brightness curve expected by your display (`sRGB` or `Gamma 2.2`). Keep on `sRGB` unless using a custom calibrated display. |
| **Main** | Strength | Controls the overall blend percentage of the FlexAgX effect (0% to 100%). At 0%, the shader is fully bypassed. |
| **Main** | Dithering | Enables faint triangular-PDF noise injection to prevent colour banding across smooth gradients. Adjusts automatically for 8-bit or 10-bit bit depths. |
| **Brightness** | Brightness | Sets exposure offset in Exposure Value steps (-2.0 EV to +2.0 EV). Adjusts scene lighting linearly while preserving highlights. |
| **Brightness** | Auto Brightness | Controls the adaptation strength of dynamic scene exposure (0% to 100%). Automatically scales down when large screen regions reach pure white. |
| **Brightness** | Hold Brightness | Freezes the dynamic auto-exposure and highlight knee adaptation at their current values while allowing manual brightness adjustments. |
| **Highlights and Shadows** | Auto Highlights | Enables automatic calculation of the highlight roll-off knee based on real-time scene analysis. |
| **Highlights and Shadows** | Highlight Start | Sets the manual linear threshold (0.40 to 0.55) where highlights begin rolling off toward white. Only active when *Auto Highlights* is disabled. |
| **Highlights and Shadows** | Shadow Detail | Adjusts shadow preservation (0% to 100%). Elevates deep darks to prevent crushed shadows while maintaining AgX tone characteristics. |
| **Colour** | Hue Stability | Controls hue restoration strength (0% to 100%) in Oklab colour space to prevent tone-curve hue shifting across both vivid and pastel tones. |
| **Colour** | Vivid Colour Softening | Defines the threshold (0.60 to 0.95) where highly saturated colors begin soft-clipping into the display gamut. |
| **Colour** | Colour Temperature | Sets image white balance in Kelvin (2000 K to 12000 K). Neutral reference is 6500 K; lower values warm the image, higher values cool it. |
| **Detail** | Detail | Controls guided-filter local contrast restoration (0% to 50%) to recover fine edge definition flattened by tone mapping, featuring an adaptive noise gate. |

---

## Acknowledgments 👏

FlexAgX builds on the following algorithms, techniques, and resources:

- **AgX tone mapping** by Troy Sobotka. The base tone curve, its polynomial approximation, and the inset/outset chroma matrices follow the AgX view transform, as used in Blender.
- **Oklab colour space** by Björn Ottosson. Used for perceptual lightness and chroma processing, hue restoration, and gamut mapping.
- **Planckian locus approximation** from Kim et al. (2002), "Design of advanced color-temperature control system for HDTV applications," *Journal of the Korean Physical Society*. Used to derive white points for the Colour Temperature control.
- **Guided image filter** by Kaiming He, Jian Sun, and Xiaoou Tang ("Guided Image Filtering," ECCV 2010 / TPAMI 2013). Used as the edge-aware base layer for the Detail control.
- **Interleaved Gradient Noise** by Jorge Jimenez (SIGGRAPH 2014, "Next Generation Post Processing in Call of Duty: Advanced Warfare"). Used for the Dithering option.
- **sRGB transfer function**, as defined in IEC 61966-2-1, along with the gamma 2.2 curve.
- **von Kries chromatic adaptation** in LMS space, used for white balance.
- **ReShade** framework, which provides the shader runtime, compute shader support, and the frame-time uniform.

## License 📄

Distributed under the MIT License. See `LICENSE` for more information.
