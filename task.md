# TaskMancer Development Tasks

## v1.1 - Backend & Frontend Refactor (Completed)
- [x] Planning
    - [x] Create implementation plan (v1.1)
    - [x] Create task list (v1.1)
    - [x] Update project rules
- [x] Backend Refactor
    - [x] Implement `scanner.py` (Recursive Project Discovery)
    - [x] Implement `watcher_service.py` (Debounce Logic)
    - [x] Implement Persistence (`projects.json`)
    - [x] Implement `parser.py` (Indentation-Aware Tree Parsing)
    - [x] Update `main.py` (CLI Args & WS Payload Structure)
    - [x] Verify Backend
- [x] Frontend Refactor
    - [x] Initialize Vue 3 Project & Dependencies
    - [x] Setup Pinia Store (`projectStore.js`)
    - [x] Create `ProjectCard.vue` & Grid Layout
    - [x] Implement `TaskTree.vue` (Recursive Component)
    - [x] Update `Dashboard.vue` to consume multi-project data
- [x] Verification
    - [x] End-to-End Multi-project Test

## v1.2 - Dynamic Project Management (Active)
- [/] Planning
    - [x] Create implementation plan (v1.2)
    - [x] Update PRD (US-5)
- [ ] Backend
    - [ ] Update `main.py` (Add ProjectManager, API Endpoint, Dynamic Watcher)
- [ ] Frontend
    - [ ] Update `projectStore.ts` (Add `addProject` action)
    - [ ] Update `App.vue` (Add Input UI)
- [x] Verification
    - [x] Manual Test (Add Path -> Verify Watcher)
    - [x] Fix UI Layout (Grid Stretch Issue)

## v1.3 - UI Polish (Active)
- [/] Planning
    - [x] Create implementation plan (v1.3)
- [x] Frontend
    - [x] Install `marked` & `dompurify`
    - [x] Update `App.vue` (Switch to Masonry Layout)
    - [x] Update `TaskTree.vue` (Implement Markdown Rendering)
- [x] Verification
    - [x] Visual Check (Layout & Markdown Style)
