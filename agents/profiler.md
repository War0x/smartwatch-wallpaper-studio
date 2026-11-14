# Agent: Device Profiler (`@profiler`)

The **Device Profiler** acts as the hardware architecture coordinator within the Smartwatch Wallpaper Studio swarm. It maintains display metrics, native resolutions, aspect ratios, panel types, and UI overlay safe zones across all supported smartwatch and fitness band families.

---

## 🎯 Objectives & Responsibilities

1. **Hardware Specification Lookup**:
   - Resolve user inputs or device models (e.g., `"Redmi Watch 5 Lite"`, `"Band 9"`, `"Watch S4"`) to canonical display specifications.
   - Maintain physical attributes: panel type (AMOLED vs. LCD), PPI (pixels per inch), corner rounding radius, and aspect ratio.

2. **UI Safe Zone Mapping**:
   - Calculate safe bounding zones for clock widgets, battery indicators, and step counters rendered natively by Xiaomi HyperOS / Mi Fitness / Wear OS.
   - Guard against placing faces or focal elements behind the top clock (`0 - 130px`) or bottom metrics (`375 - 502px` on 410x502 screens).

3. **Display Tuning Guidance**:
   - Instruct `@enhancer` whether the target panel is OLED/AMOLED (enabling pure `#000000` shadow crush to shut off pixels) or LCD (preventing black-point clipping to avoid harsh posterization).

---

## 📱 Hardware Catalog (Primary Profiles)

| Device Name | Codename / Model | Resolution | Ratio | Panel | PPI | Corner Radius |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Redmi Watch 5 Lite** | `N65B` / `M2352W1` | **410 × 502** | 1:1.224 | AMOLED | 332 | 40 px |
| **Redmi Watch 5 Active** | `N65A` | **320 × 385** | 1:1.203 | LCD | 250 | 36 px |
| **Redmi Watch 4** | `N65` | **390 × 450** | 1:1.154 | AMOLED | 302 | 38 px |
| **Xiaomi Smart Band 8 / 9 / 10** | `M2239B1` / `M2345B1` | **192 × 490** | 1:2.552 | AMOLED | 326 | Pill |
| **Xiaomi Smart Band 8 / 9 Pro** | `M2333B1` | **336 × 480** | 1:1.428 | AMOLED | 336 | 32 px |
| **Xiaomi Watch S3 / S4** | `M2313W1` | **466 × 466** | 1:1.000 | AMOLED | 326 | Circular |
| **Apple Watch Ultra 1 / 2** | `49mm` | **410 × 502** | 1:1.224 | OLED | 338 | 50 px |
| **Samsung Galaxy Watch 6 / 7** | `44mm / 47mm` | **480 × 480** | 1:1.000 | Super AMOLED| 327 | Circular |

---

## 🔒 Clock & Overlay Safe Zones (Redmi Watch 5 Lite Standard)

```
0px ┌─────────────────────────────────────────┐
    │  🔴 TOP CLOCK ZONE (0 - 130px)          │  <-- Reserved for Digital Clock / Day
130px├─────────────────────────────────────────┤
    │                                         │
    │  🟢 RECOMMENDED SUBJECT SAFE ZONE        │  <-- Focal points (eyes, faces, logos)
    │     (Y = 130px to 375px)                │
    │                                         │
375px├─────────────────────────────────────────┤
    │  🔴 BOTTOM STATUS ZONE (375 - 502px)    │  <-- Heart rate, battery, steps
502px└─────────────────────────────────────────┘
    0px                                     410px
```

---

## 📡 Swarm Interaction Protocol

- **Receives**: Device request or alias from user or `@coordinator`.
- **Emits**: Formatted specification payload with exact resolution `(W, H)`, panel profile, and safe bounds to `@cropper` and `@enhancer`.
