<div align="center">

# FlexAgX

### Light, reconsidered.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A ReShade post-process that brings the AgX look to your games, refined for real displays.<br>
Shadows that keep their shape. Highlights that hold their color. Detail that stays sharp.

[Get Started](#installation) · [Controls](#controls) · [How It Works](#how-it-works) · [What You'll See](#what-youll-see)

</div>

---

## ✨ Introducing FlexAgX.

FlexAgX is a tone-mapping shader for ReShade. It takes the final image of your game and reshapes its brightness and color so it reads the way a well-exposed photograph would: balanced, luminous, and natural. No crushed blacks. No blown-out skies. No muddy midtones.

It is a single file. It looks good out of the box, and every decision it makes can be overruled with a slider.

---

## 🤔 Why it's different.

Most tone mappers ask you to choose a trade-off. Lift the shadows and the highlights go flat. Protect the highlights and the darks turn to mud. Push the brightness and the colors drift.

FlexAgX was built on the idea that these should not be trade-offs. It adapts exposure to each scene. It lifts shadows without washing them out. It rolls off highlights without clipping them. It restores the hue that bright colors would otherwise lose. Then it returns the fine texture that brightness changes so often flatten.

Every stage is designed to work with the others. Nothing is bolted on.

---

## 🧩 Features

### Brightness, understood.

Auto exposure gently guides each scene toward a natural mid-grey reference. Dark rooms brighten. Bright scenes stay composed. A Clip Guard backs off the adjustment whenever too many pixels are already white, and a scene-change detector responds quickly when you move from a cave into daylight.

### Shadows that keep their shape.

Shadow Preservation lifts the darkest tones along a smooth, monotone toe, so night scenes keep their depth instead of collapsing into black. Set it to 0% for the plain AgX character.

### Highlights, held.

Bright areas are compressed into the top of the range along a single continuous curve that reaches full white at the limit. Skies, lamps, and sunlight keep their gradients. The Highlight Knee can be chosen automatically for each scene or set by hand.

### Color, respected.

Hue Restoration keeps colors from drifting as they brighten, so reds stay red and blues stay blue. Very vivid colors soften gently at the edge of the display's range rather than clipping into flat, unnatural patches.

### Detail, distilled.

Local Detail restores fine contrast in foliage, fabric, stone, and faces, the kind of texture that brightness changes tend to flatten. It works from a guided base, so it enhances texture without the halos that ordinary sharpening leaves behind.

### Banding, gone.

Dithering adds imperceptible noise to smooth gradients, so skies and fog do not break into visible rings. The curve itself is checked for monotonicity across every 8-bit code before it is used, so the image never reverses direction or steps unnaturally.

### Diagnostics, built in.

Clipping Warning paints anything the game has already blown out in magenta, so you can see exactly what FlexAgX cannot recover. Exposure Gain shows how much brightness it is adding, in real time.

---

<a id="what-youll-see"></a>

## 👀 What You'll See

FlexAgX is designed to deliver the following. Results depend on the game, the scene, your display, and your settings.*

**Shadows.** Dark corners and night scenes hold their shape. Near-black stays near-black, and auto exposure eases off so deep darkness is not dragged up to grey.

**Midtones.** Faces, skin, and foliage sit at a natural brightness with a softer, more filmic contrast than the original tone curve. Textures read as textures.

**Highlights.** Sunlit surfaces, windows, and specular glints compress smoothly toward white instead of clipping into flat patches. Gradients in bright skies keep moving.

**Color.** Hues hold steady as colors brighten. Saturated colors stay vivid but soften at the top, so an intense red does not become a flat, neon blob.

**Overall.** The image looks composed rather than processed. It is brighter where it was too dark, calmer where it was too hot, and it keeps a sense of depth that a harsher tone curve would flatten.

<table>
  <tr>
    <td align="center">
      <b>Before</b><br />
      <img src="https://github.com/user-attachments/assets/f73eac74-a38f-4ded-a856-6f798035b6ef" width="100%" alt="Before" />
    </td>
    <td align="center">
      <b>After</b><br />
      <img src="https://github.com/user-attachments/assets/c24c0a3d-fccb-4dd7-aacb-51b8aa54b273" width="100%" alt="After" />
    </td>
  </tr>
</table>


---

## 📋 Requirements

| Requirement | Details |
|---|---|
| ReShade | 5.9.0 or newer |
| Graphics API | Direct3D 11, Direct3D 12, OpenGL 4.3, or Vulkan |
| Output | Standard dynamic range (sRGB or gamma 2.2) |

Older ReShade versions, Direct3D 9 and 10, and OpenGL below 4.3 are rejected at compile time with a clear error message.

---

<a id="installation"></a>

## 📥 Installation

1. Install ReShade 5.9.0 or newer for your game's graphics API.
2. Download `FlexAgX.fx` and place it in your ReShade shaders folder, usually `reshade-shaders/Shaders/`.
3. Launch the game and press **Home** to open the ReShade overlay.
4. On the Home tab, enable **FlexAgX**.
5. Open the FlexAgX settings and adjust to taste. The defaults are the recommended starting point.

---

<a id="controls"></a>

## 🎛️ Controls

Set `Overall Strength` to 0% and FlexAgX becomes a bit-exact pass-through: your image is returned exactly as the game rendered it. The debug views remain available at 0% for diagnostics.

| Category | Control | Default | Range | Description |
|---|---|---|---|---|
| Main | Overall Strength | 100% | 0 – 100 | How strongly FlexAgX changes the image. |
| Main | Debug View | Off | Off, Clipping Warning, Exposure Gain | Diagnostic overlays. Keep Off for normal play. |
| Brightness | Auto Exposure Strength | 30% | 0 – 100 | How much the scene brightens or darkens automatically. |
| Brightness | Exposure Offset | 0.0 EV | −2.0 – +2.0 | Manual brightness, like a camera's exposure dial. One step doubles the light. |
| Brightness | Freeze Exposure | Off | On / Off | Locks automatic brightness adaptation. |
| Adaptation | Brighten Speed | 0.60 | 0.10 – 3.00 | How quickly the image gets brighter. Lower is faster. |
| Adaptation | Darken Speed | 1.20 | 0.10 – 5.00 | How quickly the image gets darker. Lower is faster. |
| Adaptation | Max Change Rate | 3.0 | 0.5 – 6.0 | Limits how fast brightness can change, so nothing jumps. |
| Adaptation | Scene Change Sensitivity | 0.35 | 0.10 – 0.60 | How different a new scene must look before brightness resets quickly. Higher means fewer resets. |
| Adaptation | Deadband | 0.04 | 0.00 – 0.10 | Ignores tiny brightness fluctuations so the image does not shimmer. |
| Adaptation | Clip Guard | 2.0% | 0.5 – 5.0 | Share of blown-out white pixels above which auto exposure ramps down to zero. |
| Highlights and Shadows | Auto Highlight Knee | On | On / Off | Chooses where highlights begin to be lifted, per scene. |
| Highlights and Shadows | Highlight Knee | 0.50 | 0.40 – 0.55 | Where highlights start to be lifted. Used only when Auto is off. |
| Highlights and Shadows | Shadow Preservation | 100% | 0 – 100 | Prevents dark areas from turning muddy black. 0% gives the plain AgX look. |
| Color | Hue Restoration | 100% | 0 – 100 | Keeps colors from drifting in hue when they get bright. |
| Color | Gamut Roll-off Start | 0.80 | 0.60 – 0.95 | How early very vivid colors begin to soften. Lower softens more. |
| Detail | Local Detail | 20 | 0 – 50 | Restores fine contrast. Too much looks crunchy. |
| Input and Output | Input Encoding | sRGB | sRGB, Gamma 2.2 | The brightness curve the game uses to store its colors. Most games use sRGB. |
| Input and Output | Output Encoding | sRGB | sRGB, Gamma 2.2 | The brightness curve your monitor expects. Keep sRGB unless you know yours differs. |
| Input and Output | Dithering | On | On / Off | Adds invisible noise so gradients do not show color bands. |

---

<a id="how-it-works"></a>

## ⚙️ How It Works

Every frame, FlexAgX runs a short pipeline entirely on the GPU. It first samples a log-luminance histogram of the frame and compares it with the previous frame to measure how much the scene has changed. An adaptation stage updates the scene's exposure with critically damped smoothing and a rate limit, then builds a 1,024-entry tone curve from that state. The curve is checked for monotonicity across every 8-bit code. If the check fails, the curve is adjusted and rebuilt, with a strictly monotone fallback as a last resort.

The image then passes through the curve. Hue is restored in Oklab, a perceptual color space, so the curve's brightness changes do not drag colors off course. Local detail is restored from a guided base. Finally, very saturated colors are rolled off to fit the display, the result is encoded for your monitor, and dithering is applied.

FlexAgX runs as a compute pass and several full-screen passes at your render resolution. Its cost scales with resolution and GPU, so benchmark it on your own setup before settling on a configuration.

---

## 🛠️ Troubleshooting

| Symptom | What to try |
|---|---|
| "FlexAgX requires ReShade 5.9.0 or newer" | Update ReShade to 5.9.0 or later. |
| "FlexAgX requires D3D11, D3D12, OpenGL 4.3 or Vulkan" | The game uses an unsupported API. Direct3D 9 and 10 and OpenGL below 4.3 are not supported. |
| Brightness keeps shifting between shots | Enable Freeze Exposure, or lower Auto Exposure Strength. |
| Highlights look flat or white | Open Debug View and choose Clipping Warning. Areas the game already clipped cannot be recovered. |
| Dark scenes look too bright | Lower Auto Exposure Strength, or use a negative Exposure Offset. |
| Faint shimmer during slow pans | Raise Deadband. |
| Textures look crunchy | Lower Local Detail. |
| Gradients still show bands | Confirm Dithering is on. |

---

## 🙏 Credits

FlexAgX stands on the work of others. The AgX display transform was developed by Troy Sobotka and popularized by Blender. The Oklab color space was designed by Björn Ottosson. The guided filtering approach follows the work of Kaiming He, Jian Sun, and Xiaoou Tang. ReShade is the work of crosire and its contributors.

---

## 📜 License

FlexAgX is released under the [MIT License](LICENSE).

---

<div align="center">

**FlexAgX.** Light, reconsidered.

<sub>* Results vary by game, scene, display, and settings.</sub>

</div>
