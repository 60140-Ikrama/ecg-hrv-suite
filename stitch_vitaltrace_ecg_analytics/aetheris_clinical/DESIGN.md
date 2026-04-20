# Design System Document: Biomedical Precision Interface

## 1. Overview & Creative North Star
**Creative North Star: "The Clinical Lens"**

This design system is not merely a data dashboard; it is a high-precision instrument. We move away from the "generic SaaS" look by adopting the aesthetic of advanced medical optics and research-grade laboratory equipment. The "Clinical Lens" focuses on extreme legibility, intentional tonal layering, and the "quiet authority" of professional biomedical tools.

To break the "template" look, we utilize **Asymmetric Information Density**. While the global grid is rigid for data integrity, the layout allows for breathing room in the narrative flow—overlapping secondary data panels over primary waveforms to create a sense of depth and focus. We prioritize the signal over the container.

---

## 2. Colors & Surface Philosophy

The palette is rooted in `surface` (#0d1518), a deep, obsidian blue that provides the ultimate high-contrast foundation for luminous signal colors.

### The "No-Line" Rule
Standard 1px borders are strictly prohibited for sectioning. They create visual noise that competes with ECG waveforms. Boundaries must be defined through **Background Color Shifts**. 
*   Use `surface-container-low` for secondary sidebars sitting on a `surface` background.
*   Use `surface-container-high` for active analysis modules.

### Surface Hierarchy & Nesting
Treat the interface as a series of physical, stacked layers:
1.  **Base Layer:** `surface` (The foundation).
2.  **Sectional Layer:** `surface-container-low` (Navigation or inactive zones).
3.  **Active Workspace:** `surface-container-high` (The primary diagnostic area).
4.  **Floating Analysis Overlays:** `surface-bright` (Transient tooltips or quick-view stats).

### The "Glass & Gradient" Rule
To elevate the "Premium" feel, floating diagnostic panels should utilize **Glassmorphism**.
*   **Token:** `surface-variant` at 60% opacity with a `24px` backdrop-blur.
*   **Signature Texture:** Main CTAs or high-level HRV summaries should use a subtle linear gradient from `primary` (#00daf3) to `primary-container` (#005f6b) at a 135-degree angle. This adds "visual soul" and depth to the clinical precision.

---

### Signal Colors (Semantic)
*   **ECG Primary Signal:** `tertiary` (#a6d700 / Lime) — Maximum luminosity against dark backgrounds.
*   **Frequency Bands / Alerts:** `error` (#ffb4ab) for critical arrhythmias; `primary` (#00daf3) for stable rhythms.

---

## 3. Typography

The system utilizes a dual-font strategy to balance technical authority with human-centric legibility.

*   **Display & Headlines (Manrope):** Used for high-level metrics (e.g., BPM, SDNN). Manrope’s geometric yet modern construction feels like a digital readout from a high-end monitor.
*   **Body & Labels (Inter):** Used for all data-dense grids, settings, and technical annotations. Inter is chosen for its exceptional x-height and legibility in small-scale medical labeling.

**Hierarchy Role:**
*   **display-lg/md:** Used for singular, critical biometric values.
*   **label-md/sm:** Used for axis labeling and unit descriptors (e.g., "ms", "mV"). These should use `on-surface-variant` to recede slightly, keeping the focus on the data.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved via **Tonal Layering**. Place a `surface-container-lowest` card within a `surface-container-low` section to create a "recessed" or "inset" feel, mimicking the physical housing of a medical device.

### Ambient Shadows
For floating modal analysis, use **Diffused Tinted Shadows**:
*   **Blur:** 32px to 48px.
*   **Color:** `surface-container-highest` at 8% opacity.
*   **Logic:** Shadows should not be black; they must be a darker, more saturated version of the background to simulate natural light absorption.

### The "Ghost Border" Fallback
Where separation is critical (e.g., overlapping waveforms), use a **Ghost Border**:
*   **Token:** `outline-variant` at 15% opacity.
*   **Execution:** The border should feel "felt" rather than "seen."

---

## 5. Components

### Precise Waveform Cards
*   **Rule:** Forbid divider lines. Separate time-series data using `8px` of vertical white space or a shift from `surface-container-low` to `surface-container-high`.
*   **Interaction:** On hover, the card should elevate to `surface-bright` with a `primary` "Ghost Border" (20% opacity).

### High-Precision Sliders (Time-Scrubbers)
*   **Track:** `secondary-container`.
*   **Handle:** `primary` solid circle with a `primary-fixed` glow (15% spread).
*   **Value Label:** Use `label-sm` in a `surface-container-highest` tooltip that follows the handle.

### Diagnostic Chips
*   **Action Chips:** Semi-transparent `primary-container` background with `on-primary-container` text.
*   **Corner Radius:** Use `md` (0.375rem) for a professional, slightly technical feel—avoid "pill" shapes unless they are global status indicators.

### Data-Dense Grids
*   **Row Height:** Compact but accessible.
*   **Alignment:** Numeric data must be tabular-lining (monospaced) for vertical scanning of HR values. Use `Inter` with the `tnum` OpenType feature enabled.

---

## 6. Do's and Don'ts

### Do
*   **Do** use `tertiary` (Lime) exclusively for health-positive signals (stable ECG).
*   **Do** use `surface-container` tiers to group related clinical metrics without adding "boxes."
*   **Do** maintain 100% "Breathing Room" around the main waveform—the signal must never feel cramped by the UI.

### Don't
*   **Don't** use 100% opaque borders to separate charts. It creates "grid-prison" and increases cognitive load.
*   **Don't** use pure black (#000000) or pure white (#FFFFFF). Use the `surface` and `on-surface` tokens to maintain the medical-grade tonal range.
*   **Don't** use standard "Drop Shadows" with 25% + opacity. If the shadow is visible as a "dark smudge," it is too heavy for this system.

---

## 7. Accessibility
Ensure that all `label-sm` annotations maintain a 4.5:1 contrast ratio against their respective `surface-container` layer. When using the `tertiary` signal color on `surface`, verify that the "glow" or "trace" remains legible for users with deuteranopia by providing an optional "High Contrast Signal" toggle that shifts Lime to a high-luminosity White/Yellow.