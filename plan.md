# v2.0 - Analytics Dashboard

## Goal Description
Implement a high-level "Dashboard" view to provide aggregated insights into all monitored projects. This will help users get a quick overview of their productivity and project states without diving into individual task lists.

## User Review Required
> [!NOTE]
> **Database Decision**: For this phase (v2.0), we will **NOT** introduce a database. We will rely on real-time aggregation of the `task.md` files. This means we cannot show historical data (e.g., "Tasks completed yesterday"), but we can show current snapshots (e.g., "Total completed tasks"). This keeps the app lightweight and file-system based.

## Proposed Changes

### Frontend
#### [MODIFY] [App.vue](file:///d:/Dev/TaskMancer/frontend/src/App.vue)
- Introduce a simple Tab/Navigation system (e.g., "Dashboard" vs "Projects").
- Move the current Project Grid into a separate component (e.g., `ProjectList.vue`) to clean up `App.vue`.

#### [NEW] [DashboardView.vue](file:///d:/Dev/TaskMancer/frontend/src/components/DashboardView.vue)
- **Stats Cards**:
    - Total Projects
    - Total Tasks (Completed / Total)
    - Completion Rate (Global)
- **Visuals**:
    - **Donut Chart**: CSS/SVG-based chart showing Project Status breakdown (Not Started, In Progress, Done).
        - *Logic*:
            - **Not Started**: 0% progress.
            - **In Progress**: 1% - 99% progress.
            - **Done**: 100% progress.
- **Top Projects List**:
    - Top 3 projects by remaining tasks (Needs Focus).

#### [NEW] [DonutChart.vue](file:///d:/Dev/TaskMancer/frontend/src/components/DonutChart.vue)
- A reusable component using SVG `stroke-dasharray` for lightweight rendering without heavy chart libraries (or use Chart.js if complexities arise, but SVG is preferred for simple donuts).

### Backend
- No significant backend changes required as the aggregation happens on the client-side data store.

## Verification Plan
### Automated Tests
- N/A (UI visual changes mostly).

### Manual Verification
- Check if aggregated numbers match individual project cards.
- Verify chart renders correctly for edge cases (0 projects, all completed, etc.).
- Switch tabs between Dashboard and Projects.
