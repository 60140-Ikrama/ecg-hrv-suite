# Design System Strategy: The Clinical Sentinel

## 1. Overview & Creative North Star
The "Clinical Sentinel" is the creative north star for this design system. It moves beyond the typical "tech dashboard" to create a high-fidelity diagnostic instrument. The goal is to evoke the feeling of a premium medical workstation—where precision is paramount and cognitive load is minimized through intentional depth and sophisticated tonal shifts.

Instead of a rigid, boxy grid, this system utilizes **Intentional Asymmetry** and **Tonal Layering**. We prioritize "The Signal" (biometric data) over "The Chrome" (the interface). By removing traditional borders and using editorial-scale typography, we create an environment that feels authoritative, calm, and hyper-accurate.

## 2. Color & Tonal Architecture
The palette is rooted in a deep, slate-based "Medical Dark" theme. Color is never decorative; it is functional, used only to signify status, signal type, or critical alerts.

### The "No-Line" Rule
Standard UI relies on 1px borders to separate content. **This design system prohibits 1px solid borders for sectioning.** Boundaries must be defined solely through:
- **Background Color Shifts:** Placing a `surface-container-high` (`#282a2d`) card against a `surface` (`#111316`) background.
- **Negative Space:** Utilizing the spacing scale to create mental groupings.

### Surface Hierarchy & Nesting
Depth is achieved through "Tonal Stacking." To create a nested hierarchy:
1.  **Level 0 (Base):** `surface` (`#111316`)
2.  **Level 1 (Sectioning):** `surface-container-low` (`#1a1c1f`)
3.  **Level 2 (Interaction/Cards):** `surface-container` (`#1e2023`) or `surface-container-high` (`#282a2d`)
4.  **Level 3 (Popovers/Modals):** `surface-bright` (`#37393d`)

### The "Glass & Gradient" Rule
For floating telemetry windows or real-time signal overlays, use **Glassmorphism**. Apply `surface-container-highest` (`#333538`) at 60% opacity with a 20px backdrop blur. This ensures the high-density data beneath remains visible but non-distracting. For primary action states, use a subtle linear gradient from `primary` (`#c3f5ff`) to `primary_container` (`#00e5ff`) to provide a tactile "glow" reminiscent of high-end medical hardware.

## 3. Typography: The Expert Voice
We use a dual-typeface system to balance clinical authority with high-density legibility.

- **The Voice (Manrope):** Used for `display` and `headline` roles. Manrope’s geometric yet open structure provides a sophisticated, modern editorial feel. It should be used for high-level summaries and "The Big Number" callouts.
- **The Data (Inter):** Used for `title`, `body`, and `label` roles. Inter is the workhorse. Its high x-height and tall ascenders ensure that complex biomedical strings and metrics are legible even at `label-sm` (`0.6875rem`).

**Intentional Scale:** Use high contrast between `display-lg` (`3.5rem`) for critical vital signs and `label-md` (`0.75rem`) for secondary metadata. This creates a clear "at-a-glance" reading path.

## 4. Elevation & Depth
In a medical context, shadows can feel "muddy." We prioritize **Tonal Layering** over heavy drop shadows.

- **Ambient Shadows:** Only used for elevated elements like tooltips or modals. Use a tinted shadow: `rgba(0, 218, 243, 0.08)` (a 8% opacity tint of `surface_tint`) with a 32px blur. This mimics the glow of a backlit screen.
- **The "Ghost Border" Fallback:** If a boundary is strictly required for accessibility, use a "Ghost Border": `outline-variant` (`#3b494c`) at 15% opacity. Never use 100% opaque borders.
- **Precision Corners:** Use the Roundedness Scale strictly. `sm` (`0.125rem`) for data points/status pips, and `md` (`0.375rem`) for primary data cards. Avoid `xl` or `full` roundedness unless it's a toggle or a pill-button, as overly round corners feel too "consumer" and less "surgical."

## 5. Components

### Data Cards & Waveform Containers
- **Visuals:** Use `surface-container-low` backgrounds. 
- **Rule:** No dividers. Separate headers from content using a vertical 16px (Spacing Scale) gap and a weight shift in Inter (Title-SM vs Body-MD).
- **Signal Colors:** ECG signals must use `secondary_fixed` (`#c3f400`), HRV metrics use `primary` (`#c3f5ff`), and ectopic alerts use `tertiary_fixed_dim` (`#ffba38`).

### Buttons
- **Primary:** Gradient from `primary` to `primary_container`. Text in `on_primary` (`#00363d`).
- **Secondary:** Transparent background with a `Ghost Border` (15% `outline`).
- **States:** On hover, increase the opacity of the `surface-tint` overlay by 8%.

### Interactive Charts (The "Pulse" Component)
- **Grid Lines:** Use `outline_variant` at 10% opacity. 
- **Interaction:** Hovering over a data point should trigger a `surface-bright` tooltip with a 12px backdrop-blur.

### Status Indicators
- **High-Precision Pips:** Use `sm` (`0.125rem`) roundedness. 
- **Critical:** `error` (`#ffb4ab`).
- **Warning:** `tertiary` (`#ffe9cd`).
- **Stable:** `secondary_fixed` (`#c3f400`).

## 6. Do's and Don'ts

### Do:
- **Do** use `surface-container` shifts to group related biometric data.
- **Do** use `Manrope` for large, single-metric displays to give the dashboard a premium, editorial feel.
- **Do** leverage `primary_fixed_dim` (`#00daf3`) for active toggle states to ensure they "pop" against the dark slate background.
- **Do** ensure `on_surface_variant` (`#bac9cc`) is used for units (e.g., "bpm", "ms") to keep them secondary to the numerical data.

### Don't:
- **Don't** use pure black (`#000000`). Always use the specified `surface` (`#111316`) for depth.
- **Don't** use 1px solid borders. If you feel the need for a line, increase the spacing or shift the background tone by one tier.
- **Don't** use "consumer" roundedness (like `xl`). Keep it tight and professional (`sm` to `md`).
- **Don't** use standard "Blue" for medical trust. Use the `primary` Cyan (`#c3f5ff`) and `secondary` Lime (`#c3f400`) to evoke a modern, high-precision laboratory environment.