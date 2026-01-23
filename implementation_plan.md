# v2.5 - Design System Overhaul (Premium Minimalist)

## Goal Description
Apply the `frontend-design` skill to transform TaskMancer into a **Premium Minimalist** experience.
**Aesthetic Direction**: "Void & Light". A deep, immersive dark mode using mostly varying shades of black/gray, distinct typography (Outfit + Plus Jakarta Sans), and subtle but sharp interactions. Avoid generic "slate" cards.

## User Review Required
> [!NOTE]
> **Visual Change**: This will significantly darken the UI (from Slate-800/900 to nearly pure black) and remove "card" backgrounds in favor of borders and negative space. The vibe will be more "Developer Tool / Terminal" chic.

## Proposed Changes

### Configuration
#### [MODIFY] [index.html](file:///d:/Dev/TaskMancer/frontend/index.html)
- Import Google Fonts: `Outfit` (Headings) and `Plus Jakarta Sans` (Body).

#### [MODIFY] [tailwind.config.js](file:///d:/Dev/TaskMancer/frontend/tailwind.config.js)
- Define custom specific colors:
    - `void`: `#050505` (Main BG)
    - `surface`: `#121212` (Cards/Panels)
    - `border`: `#2A2A2A` (Subtle borders)
    - `primary`: `#F8FAFC` (High contrast text)
    - `secondary`: `#94A3B8` (Muted text)
    - `accent`: `#8B5CF6` (Violet - "Magic" feel)
- Add animation keyframes (fade-in-up, subtle-scale).

### Styles
#### [MODIFY] [style.css](file:///d:/Dev/TaskMancer/frontend/src/style.css)
- Reset base styles.
- Apply new font families.
- Add utility classes for "glass" effects if needed (minimal usage).

### Components
#### [MODIFY] [App.vue](file:///d:/Dev/TaskMancer/frontend/src/App.vue)
- **Header**: Remove gradients. Use simple, bold typography.
- **Tabs**: Switch to a "segmented control" or simple text links with active indicator.
- **Layout**: Increase padding/gap.

#### [MODIFY] [DashboardView.vue](file:///d:/Dev/TaskMancer/frontend/src/components/DashboardView.vue)
- **Stats**: Remove card backgrounds. Use big numbers with small labels directly on the grid.
- **Charts**: Simplify Donut Chart colors to Monochrome or specific accent scales.

#### [MODIFY] [ProjectList.vue](file:///d:/Dev/TaskMancer/frontend/src/components/ProjectList.vue)
- Update grid spacing.

#### [MODIFY] [ProjectCard.vue](file:///d:/Dev/TaskMancer/frontend/src/components/ProjectCard.vue)
- **Redesign**:
    - Remove heavy background.
    - Use a 1px border.
    - Show progress bar as a thin line.
    - Focus on typography for the project name.

## Verification Plan
### Manual Verification
- Verify visual hierarchy is adequate without relying on heavy card backgrounds.
- Check contrast ratios for accessibility.
- Verify animations feel "premium" (smooth, not jumpy).
