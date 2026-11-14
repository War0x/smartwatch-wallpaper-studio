# Agent: AMOLED Enhancer & Color Tuner (`@enhancer`)

The **AMOLED Enhancer** maximizes the visual impact, dynamic range, and power efficiency of wallpapers displayed on self-emissive AMOLED and OLED smartwatch screens.

---

## 🎯 Objectives & Responsibilities

1. **AMOLED True-Black Shadow Crushing (`#000000`)**:
   - OLED panels turn off individual organic pixels completely when rendering pure black (`RGB: 0, 0, 0`), consuming **zero power** and producing infinite contrast.
   - Standard wallpapers often have murky dark gray backgrounds (`RGB: 10, 12, 18`), which keep all pixels lit and wash out the display edges.
   - `@enhancer` detects dark shadows below a threshold (`RGB <= 14`) and crushes them to `#000000`.

2. **Smooth Toe Roll-Off (Hermite Smoothstep)**:
   - Hard clipping causes visible color banding and harsh halo contours around subjects.
   - `@enhancer` implements a cubic smoothstep curve ($3t^2 - 2t^3$) across a transition zone to gracefully taper dark hues down to zero without posterization.

3. **Vibrancy and Contrast Scaling**:
   - Smartwatch screens are viewed in outdoor daylight and ambient conditions.
   - Subtle saturation boost ($1.10\times$) and contrast amplification ($1.15\times$) counteract panel reflection and bring out vivid colors.

4. **Micro-Clarity & High-Frequency Sharpening**:
   - Smartwatch screens possess high pixel density (300 to 340+ PPI).
   - High-pass unsharp masking ($1.0\text{px}$ radius, $120\%$, threshold $3$) ensures hair strands, runes, fine text, and textures remain tack-sharp.

5. **Chroma Subsampling & Output Formatting**:
   - Exports pristine **PNG** for lossless quality.
   - Exports high-quality **JPEG** ($98\%$ quality with `subsampling=0` / 4:4:4 full chroma) required by Xiaomi Mi Fitness Album mode to avoid color degradation in compression.

---

## 🔬 Mathematical Tone Curve

For per-pixel maximum channel value $M = \max(R, G, B)$ and threshold $T = 14$, transition span $S = 10$:

$$t = \text{clip}\left(\frac{M - T}{S}, 0, 1\right)$$
$$\text{scale} = 3t^2 - 2t^3$$

$$\text{Pixel}_{\text{out}} = \begin{cases} 
0 & \text{if } M \le T \\ 
\text{Pixel}_{\text{in}} \times \text{scale} & \text{if } T < M < T + S \\ 
\text{Pixel}_{\text{in}} & \text{if } M \ge T + S 
\end{cases}$$

---

## 📡 Swarm Interaction Protocol

- **Receives**: Cropped canvas from `@cropper` + panel tuning metrics from `@profiler`.
- **Emits**: Final optimized PNG and JPG files saved to disk, reporting battery-saving pure black pixel percentages to `@coordinator`.
