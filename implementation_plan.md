# v2.6 - Project List Categorization (Kanban-style)

## Goal Description
Enhance `ProjectList.vue` to categorize monitored projects into three distinct sections based on their progress status, as requested by the user.

## User Review Required
> [!NOTE]
> **Interpretation of "3. 開始"**: The user requested "3. 開始", which translates to "Start". In the context of "Not Started" and "In Progress", the third logical state is "Completed" (Done). I will implement this section as **"Completed (已完成)"** to list projects with 100% progress.

## Proposed Changes

### Components
#### [MODIFY] [ProjectList.vue](file:///d:/Dev/TaskMancer/frontend/src/components/ProjectList.vue)
- **Computed Properties**: Create filters for:
    - `draftProjects`: 0% progress.
    - `activeProjects`: 1% - 99% progress.
    - `completedProjects`: 100% progress.
- **Layout**:
    - Remove the single grid.
    - Create 3 vertical sections, each with a Header (Void style text) and a Grid.
    - Section Headers:
        1. **Drafts / Pending** (未開始)
        2. **In Progress** (進行中)
        3. **Completed** (已完成) - *Assuming this is what "開始" meant intended contextually.*
    - Handle empty states for each section comfortably.

## Verification Plan
### Manual Verification
- Check if projects appear in the correct section based on `task.md` ticks.
- Verify the "Empty State" when no projects exist at all.
- Ensure the minimalist design (borders, typography) is consistent.
