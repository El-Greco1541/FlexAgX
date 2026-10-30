<div align="center">
  
# FlexAgX

**Advanced Image Reconstruction & Tone Mapping for ReShade.**  
*Pro-grade dynamic range. Zero color clipping. Uncompromising fidelity.*
</div>

---

## Overview ✨

**FlexAgX** is an advanced image-reconstruction and tone-mapping shader built for ReShade 5.9.0+. Inspired by filmic color science and modern camera pipelines, FlexAgX brings an **HDR-like look** to standard dynamic range (SDR) SDR displays—rescuing blown-out highlights, preserving rich shadow detail, and eliminating harsh color clipping without introducing unnatural haloing or flat contrast.

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

---

## System Requirements ⚙️

| Requirement | Minimum |
| :--- | :--- |
| **ReShade Version** | `5.9.0` or higher *(requires storage image reads)* |
| **Graphics API** | DirectX 11, DirectX 12, Vulkan, or OpenGL 4.3+ |
| **Bit Depth** | Supports 8-bit, 10-bit, and 16-bit color output |

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

| Section | Parameter | Default | Description |
| :--- | :--- | :--- | :--- |
| **Main** | `Overall Strength` | `100.0%` | Global effect intensity (0% provides bit-exact bypass). |
| | `Debug View` | `Off` | Toggle between *Off*, *Clipping Warning*, and *Exposure Gain*. |
| **Brightness** | `Auto Exposure Strength` | `30.0%` | Percentage of automatic brightness adaptation applied. |
| | `Exposure Offset` | `0.0 EV` | Manual camera exposure compensation dial. |
| **Highlights/Shadows**| `Shadow Preservation` | `50.0%` | Lifts deep shadows away from flat black. |
| **Color** | `Hue Restoration` | `100.0%` | Fixes color drift in ultra-bright highlight regions. |
| | `Color Temperature` | `6500 K` | White balance adjustment (2000 K to 12000 K). |
| **Detail** | `Local Detail` | `20.0` | Guided micro-contrast recovery to preserve fine surface detail. |

---

## License 📄

Distributed under the MIT License. See `LICENSE` for more information.
