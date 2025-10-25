Temporal Order Demo
===================

This repository contains a simple inventory/order workflow concept with a fresh Next.js GUI for demos.

What's included
- Next.js 14 app under `src/gui` with:
  - API routes to read inventory and create/poll orders
  - A lightweight workflow simulator that updates `src/db/state.json` and `src/db/inventory.json`
  - A progress UI that shows each step (created → reserved → payment verified → address verified → paid → shipped)

Run the GUI
1. Open a new terminal and change into the GUI folder:
   - `cd src/gui`
2. Install deps and start the dev server (defaults to Temporal backend):
   - `npm install`
   - `npm run dev`
3. Open http://localhost:3000

Data storage
- Inventory: `src/db/inventory.json`
- Orders: `src/db/state.json`

The simulator updates these files as an order progresses so the UI can poll and render status.

Temporal backend (default)
- The GUI uses Temporal by default if a server is reachable at `localhost:7233` and your worker is running on task queue `order-task-queue`.
- To force the simulator instead, run with `USE_TEMPORAL=0 npm run dev`.
- Failures from workflows (e.g., out of stock) are surfaced to the UI with a helpful message.

Python worker notes
- The current Python workflow/activities under `src/order_workflow` appear incomplete and will likely need fixes before running against a Temporal Server.
- The GUI will still function in simulator mode for product demos without a running Worker.
