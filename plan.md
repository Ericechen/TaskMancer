# v1.5 - Usability Improvements

## Goal Description
Enhance user experience by allowing project removal, preventing duplicate imports, and persisting the discovery root path in the backend configuration.

## Proposed Changes

### Backend
#### [MODIFY] [backend/main.py](file:///d:/Dev/TaskMancer/backend/main.py)
- Update `ProjectManager`:
    - Track `observer` watches to enable removal (`unschedule`).
    - Update `load_projects` and `save_projects` to handle `discovery_root` field in `projects.json`.
    - Add `remove_root(path)` method.
- Add `DELETE /api/roots` endpoint.
- Add `GET /api/config` endpoint (to get `discovery_root` and potentially other settings).

### Frontend
#### [MODIFY] [frontend/src/stores/projectStore.ts](file:///d:/Dev/TaskMancer/frontend/src/stores/projectStore.ts)
- Add `removeProject(path)` action.
- Add `fetchConfig()` action to load `discoveryRoot`.
- Update `addProject` or `setDiscoveryRoot` to sync `discoveryRoot` to backend (maybe via a specific config endpoint or just updating it when scanning).

#### [MODIFY] [frontend/src/App.vue](file:///d:/Dev/TaskMancer/frontend/src/App.vue)
- In "Discovery Modal":
    - Initial `discoveryPath` should come from store (fetched from backend).
    - When rendering results, check if `store.projects` already contains the path.
    - If contained: Disable checkbox and visually mark as "Added".

#### [MODIFY] [frontend/src/components/ProjectCard.vue](file:///d:/Dev/TaskMancer/frontend/src/components/ProjectCard.vue)
- Add a "Delete/Remove" button (e.g., trash icon) in the header.
- Connect to `store.removeProject`.

## Verification Plan
### Manual Verification
- **Persistence**: Restart backend, verify `discoveryRoot` is remembered.
- **Deletion**: Add a project, delete it, ensure it disappears from UI and `projects.json`.
- **Duplicate Prevention**: Scan a folder with already added projects. Verify checkboxes are disabled.
