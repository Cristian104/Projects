# MyBrain Portal: Modules Reference

The MyBrain Portal is a modular Flask application designed for personal life management. Each module is self-contained within `app/modules/<module_name>/`, following a blueprint-based architecture.

---

## Auth Module
**Purpose:** Handles user identity, session management, and access control for the entire portal.

*   **Main Features:**
    *   Secure login/logout functionality using `Flask-Login`.
    *   Password hashing and session persistence.
    *   Role-based access (implied via `@module_required` decorators).
*   **Database Models:**
    *   `User`: Stores credentials, preferences, and module-specific state (e.g., `current_gym_day`).
*   **Key Routes:**
    ```python
    /auth/login      # User authentication
    /auth/logout     # Session termination
    /auth/profile    # User settings and preferences
    ```

---

## Dashboard Module
**Purpose:** The central nervous system of the portal, serving as a unified landing page and administrative hub.

*   **Main Features:**
    *   **App Launcher:** Quick-access tiles for all active modules.
    *   **Dev Panel:** System status and environment debugging tools.
    *   **Overview Stats:** Aggregated data from Gym and Nutrition (e.g., today's workout, remaining calories).
*   **Database Models:**
    *   Interacts with models from all other modules to provide a summary view.
*   **Key Routes:**
    ```python
    /                # Main dashboard UI
    /admin           # Developer and system management panel
    ```

---

## Gym Module
**Purpose:** A robust workout tracker supporting structured programming, exercise libraries, and AI-powered plan ingestion.

*   **Main Features:**
    *   **7-Day Cycle Logic:** Enforces a strict 7-day routine structure with "Self-Healing" logic (auto-creates rest days if the program is incomplete).
    *   **AI PDF Import:** Uses Gemini Pro to parse coach-provided PDFs into structured database records (Exercises, Sets, Reps, Notes).
    *   **Exercise Library:** Decouples specific workout instances from "Templates," allowing users to "Promote" a one-off exercise to a reusable library item.
    *   **Routine Management:** Drag-and-drop style swapping (Up/Down) and "Skip Day" functionality to progress through the program.
*   **Database Models:**
    *   `GymProgram`: The high-level container (e.g., "Hypertrophy Phase 1").
    *   `GymRoutine`: Specific days within a program (Day 1-7).
    *   `GymExercise`: Individual exercise instances with target sets/reps.
    *   `GymExerciseLibrary`: Global templates for exercises.
    *   `GymLog`: Historical records of completed sets and PRs.
*   **Key Routes:**
    ```python
    /gym/                       # Active routine and next-up logic
    /gym/programs               # Program history and creation
    /gym/import_pdf             # POST: Gemini-powered PDF parsing
    /gym/routine/<id>           # Detailed view/edit of a specific day
    /gym/exercise/promote/<id>  # Convert a one-off exercise to a template
    ```

---

## Nutrition Module
**Purpose:** Precision tracking of dietary intake, macro-nutrients, and supplementation.

*   **Main Features:**
    *   **Macro Tracking:** Real-time calculation of Calories, Protein, Carbs, and Fats.
    *   **Gemini Sync:** Shared logic with the Gym module to parse nutrition plans from the same coach-provided PDFs.
    *   **Water & Supplements:** Dedicated tracking for hydration and daily supplement stacks.
    *   **Food Swaps:** Database of alternatives for flexible dieting.
*   **Database Models:**
    *   `Meal`: Daily food entries.
    *   `FoodItem`: Macro data for specific ingredients or meals.
    *   `WaterIntake`: Daily hydration logs.
*   **Key Routes:**
    ```python
    /nutrition/                 # Daily macro overview and logging
    /nutrition/plan             # Current meal plan viewing
    /nutrition/log_water        # Quick-add for hydration
    ```

---

## Tasks Module
**Purpose:** A streamlined task manager for personal "To-Do" items and project tracking.

*   **Main Features:**
    *   **Status Workflow:** Track tasks from Todo → In Progress → Done.
    *   **Categorization:** Group tasks by project or area of life (Work, Home, Bot).
    *   **Deadlines:** Visual indicators for upcoming or overdue requirements.
*   **Database Models:**
    *   `Task`: The core unit of work.
    *   `Category`: User-defined labels for organization.
*   **Key Routes:**
    ```python
    /tasks/                     # List view of all active tasks
    /tasks/create               # New task entry
    /tasks/update/<id>          # Status and priority toggles
    ```
