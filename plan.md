# Implementation Plan - Stopping Visual Effect

## Goal Description
Add a visual "Stopping..." indicator with an animation effect to the Project Card's Dev Switch when a service is in the process of stopping. This mirrors the existing "Starting..." effect.

## User Review Required
None.

## Proposed Changes

### Frontend
#### [MODIFY] [ProjectCard.vue](file:///d:/Dev/TaskMancer/frontend/src/components/ProjectCard.vue)
- Update the Dev Switch button:
    - Disable the button when `alert_level` is `'stopping'`.
    - Apply a pulsing red background (`bg-danger/50 animate-pulse`) when stopping.
- Add a text label "Stopping..." next to the switch, visible only when `alert_level` is `'stopping'`.

## Verification Plan
### Manual Verification
1. Open TaskMancer.
2. Start the `dummy_service`.
3. Wait for it to be fully running (Green/Live).
4. Click the Dev Switch to stop it.
5. **Verify**:
    - The switch becomes disabled.
    - The switch background pulses red.
    - The text "Stopping..." appears next to the switch.
    - After the process stops, the switch returns to the off state (gray) and the text disappears.
