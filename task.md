# TaskMancer Development Tasks

## v1.1 - Backend & Frontend Refactor (Completed)
- [x] Planning
    - [x] Create implementation plan (v1.1)
    - [x] Create task list (v1.1)
    - [x] Update project rules
- [x] Backend Refactor
    - [x] Implement `scanner.py` (Recursive Project Discovery)
    - [x] Implement `watcher_service.py` (Debounce Logic)
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
- [x] Planning
    - [x] Create implementation plan (v1.2)
    - [x] Update PRD (US-5)
- [/] Backend
    - [x] Update `main.py` (Add ProjectManager, API Endpoint, Dynamic Watcher)
    - [x] Implement Persistence (`projects.json`)
- [x] Frontend
    - [x] Update `projectStore.ts` (Add `addProject` action)
    - [x] Update `App.vue` (Add Input UI)
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

## v1.4 - Smart Discovery (Active)
- [/] Planning
    - [x] Create implementation plan (v1.4)
    - [x] Update PRD (US-6)
- [x] **Backend Implementation**
    - [x] Update `DirectoryScanner` (support shallow scan)
    - [x] Add `POST /api/discover` endpoint
    - [x] Unit Tests for Discovery (Verified via script)
- [x] **Backend Implementation**
    - [x] Update `DirectoryScanner` (support shallow scan)
    - [x] Add `POST /api/discover` endpoint
    - [x] Unit Tests for Discovery (Verified via script)
- [x] **Frontend Implementation**
    - [x] Update `projectStore.ts` (Add `discoverProjects` action)
    - [x] Update `App.vue` (Implement Multi-step Modal: Search -> Select -> Import)
- [x] Verification
    - [x] Manual Test (Discovery Flow)

## v1.5 - Usability Improvements (Active)
- [x] Backend
    - [x] Update `ProjectManager` to support removing roots
    - [x] Add `DELETE /api/roots` endpoint
    - [x] Update `projects.json` schema to store `discovery_root`
    - [x] Add `GET /api/config` (or update logic) to retrieve `discovery_root`
- [x] Frontend
    - [x] Update `projectStore.ts` (fetch config, remove action)
    - [x] Update `App.vue` (Disable existing projects in discovery)
    - [x] Update `ProjectCard.vue` (Add Delete button)
- [x] Verification
    - [x] Manual Test (Persistence & Deletion)

## v2.0 - Analytics Dashboard
- [x] Frontend Architecture
    - [x] Refactor `App.vue` to support Tabs/Views (Dashboard vs Project List)
    - [x] Extract current grid to `ProjectList.vue`
- [x] Dashboard Components
    - [x] Implement `DonutChart.vue` (SVG based)
    - [x] Implement `DashboardView.vue` (Aggregated Stats)
        - [x] Total Projects & Tasks
        - [x] Status Categorization Logic
    - [x] Integrate into Main View

## v2.1 - Dashboard Refinements (Active)
- [x] Filter "Needs Focus" list (Hide completed projects)
- [x] Add "Quick Wins" widget (>75% completion)

## v2.5 - Design Overhaul (Premium Minimalist)
- [x] Config & Assets
    - [x] Import Fonts (Outfit, Plus Jakarta Sans)
    - [x] Update Tailwind Config (Void/Surface Palette)
- [x] Global Styles
    - [x] Update `style.css` (Base typography, animations)
- [x] Component Reskin
    - [x] `App.vue` (Header, Nav, Modal)
    - [x] `DashboardView.vue` (Minimalist Stats, Donut)
    - [x] `ProjectCard.vue` (Border-based design)
    - [x] `DonutChart.vue` (Monochrome/Accent color scheme)

## v2.6 - Project List Categorization (Completed)
- [x] Implement Sectioned View in `ProjectList.vue`
    - [x] Filter logic (Draft, Active, Completed)
    - [x] Section Headers & Layout
    - [x] Empty states for sections

