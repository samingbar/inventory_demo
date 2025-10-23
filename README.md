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
2. Install deps and start the dev server:
   - `npm install`
   - `npm run dev`
3. Open the app at http://localhost:3000

Data storage
- Inventory: `src/db/inventory.json`
- Orders: `src/db/state.json`

The simulator updates these files as an order progresses so the UI can poll and render status.

Temporal integration (optional)
- The API is structured so it can be swapped to call a real Temporal Client.
- To integrate with your Worker:
  - Replace the simulator in `src/gui/app/api/orders/route.ts` with a call to your Temporal Client to start the workflow (e.g. workflow type `OrderWorkflow` on your task queue), and
  - Implement `GET /api/orders/:id` to query current workflow state (via queries/signals/describe) and return the same shape used by the UI.

Python worker notes
- The current Python workflow/activities under `src/order_workflow` appear incomplete and will likely need fixes before running against a Temporal Server.
- The GUI will still function in simulator mode for product demos without a running Worker.
