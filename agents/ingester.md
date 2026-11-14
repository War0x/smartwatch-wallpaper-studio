# Agent: Image Ingester (`@ingester`)

The **Image Ingester** manages universal media acquisition, sanitization, and decoding for the Smartwatch Wallpaper Studio pipeline.

---

## 🎯 Objectives & Responsibilities

1. **Universal Source Support**:
   - Local filesystem paths (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`, `.avif`).
   - Remote HTTP / HTTPS image URLs.
   - Steam Workshop thumbnail and preview scrapers.
   - In-memory binary byte buffers.

2. **Sanitization & Normalization**:
   - Handle custom HTTP User-Agent headers to prevent `403 Forbidden` / `429 Too Many Requests` blocks on protected CDNs.
   - Strip alpha channels and transparency safely, compositing over `#000000` (AMOLED true black) to prevent transparent fringing on watch displays.
   - Standardize all internal representations to 8-bit uncompressed RGB raster data before handing off to `@cropper`.

---

## 🛠️ Ingestion Logic Specification

```python
# Concept implemented in core/ingester.py
def load_image(source: Union[str, bytes]) -> Image.Image:
    # 1. Inspect source signature
    # 2. Fetch remote buffer with desktop browser headers if URL
    # 3. Open via Pillow backend
    # 4. Normalize color space (RGBA/P/CMYK -> RGB)
    # 5. Return standardized raster object
```

---

## 📡 Swarm Interaction Protocol

- **Receives**: Target URL or local path string from `@coordinator`.
- **Emits**: Cleaned, uncompressed Pillow `RGB` image object directly to `@cropper`.
