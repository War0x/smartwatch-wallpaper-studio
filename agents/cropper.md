# Agent: Smart Cropper & Aspect Ratio Adapter (`@cropper`)

The **Smart Cropper** is responsible for aspect ratio adaptation, portrait framing, subject alignment, and high-fidelity resampling.

---

## 🎯 Objectives & Responsibilities

1. **Aspect Ratio Conformance**:
   - Compare source aspect ratio against target hardware aspect ratio (e.g. `410:502` ≈ `1:1.224` for Redmi Watch 5 Lite).
   - Prevent any non-uniform geometric stretching or aspect ratio distortion.

2. **Smart Subject Framing**:
   - `smart` (Default): Biases the vertical crop window upwards towards the upper 38% rule-of-thirds mark. This ensures character faces, eyes, and portrait subjects remain centered within the smartwatch's visible zone without falling under the bottom UI indicators.
   - `center`: Strict 50% geometric center cropping.
   - `top`: Locks top edge at `Y=0` (ideal for landscapes with majestic skies or tall monuments).
   - `bottom`: Locks bottom edge (ideal for foreground ground-level subjects).

3. **High-Order Resampling**:
   - Employs **Lanczos (sinc-windowed filter)** 8-tap interpolation for downscaling and upscaling, minimizing ringing artifacts and aliasing along diagonal edges.

---

## 📐 Mathematical Framing Modes

```
Original Landscape Source:
┌────────────────────────────────────────────────────────┐
│               [   Cropping Window   ]                  │
│               [ (Target Aspect 1:1.22) ]               │
│               [                     ]                  │
└────────────────────────────────────────────────────────┘
                  |<-- Centered X -->|

Original Portrait Source (Rule-of-Thirds Vertical Bias):
┌────────────────┐
│   Sky / Space  │
├────────────────┤ <-- Y = (src_h - target_h) * 0.38 (Smart Focus)
│    [ Head ]    │
│   [ Subject ]  │ <-- Kept inside Safe Zone
│   [ Torso ]    │
├────────────────┤
│   Foreground   │
└────────────────┘
```

---

## 📡 Swarm Interaction Protocol

- **Receives**: Source image from `@ingester` + target dimensions and safe zones from `@profiler`.
- **Emits**: Pixel-perfect framed image matching exact hardware target dimensions to `@enhancer`.
