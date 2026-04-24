# MyBrain Gym Module

!!! info Purpose
> The MyBrain Gym module provides comprehensive tools for managing personal fitness, including workout programs, routines, and exercise logging. It integrates AI-powered PDF parsing to effortlessly import external workout plans.

## Core Concepts

The module revolves around several key data structures:

*   **`GymProgram`**: A high-level collection of `GymRoutine`s, representing a complete workout plan (e.g., "Strength Program", "Cutting Phase"). A user can have multiple programs, but only one is `is_active` at a time.
*   **`GymRoutine`**: Represents a specific day's workout within a `GymProgram`. Programs are structured into 7-day routines, which can be custom workouts or "Rest Day" entries.
*   **`GymExercise`**: Individual exercises within a `GymRoutine`, detailing target sets, reps, notes, and advanced parameters like RIR.
*   **`GymLog`**: (Implied, not fully detailed in `routes.py`) Stores records of completed sets, reps, weight, and other performance metrics, enabling progress tracking and PR detection.

## Dashboard Overview

The primary entry point is the dashboard, accessible at `/gym`.

!!! tip Access
> Access to the gym module requires user authentication and the `gym` module to be enabled for the user.
> ```python
> @gym_bp.route('/')
> @login_required
> @module_required('gym')
> ```

Upon loading, the dashboard dynamically displays the user's `active_program` and highlights the `next_routine` based on `current_user.current_gym_day`.

### Automatic Program Provisioning & Self-Healing

If a user has no active `GymProgram`, the system will automatically create a default "My First Program" along with seven "Rest Day" routines for the week.

!!! note 7-Day Structure
> The system enforces a strict 7-day routine structure. If a program somehow has fewer than 7 routines, it will "self-heal" by adding "Rest Day" routines until the count reaches seven.

The `current_user.current_gym_day` value tracks the user's progress through the weekly routine. If this value becomes invalid (e.g., points to a non-existent day), it automatically resets to `1`.

## Program Management

The `/gym/programs` route allows users to view and manage their existing `GymProgram`s. This view lists all programs associated with the current user, ordered by creation date.

## AI-Powered PDF Program Import

A standout feature is the ability to import workout programs directly from PDF documents, leveraging Gemini for intelligent parsing.

!!! info Endpoint
> `POST /gym/import_pdf`

### Workflow

1.  **Upload PDF**: Users upload a PDF file containing their workout plan. The system validates the file to ensure it's a PDF.
2.  **Secure Storage**: The uploaded PDF is saved to a secure, user-specific location within the application's instance folder:
    ```
    /app/instance/uploads/gym_pdfs/
    ```
    The filename is secured and timestamped to prevent collisions and ensure uniqueness: `f'{current_user.id}_{datetime.now().timestamp()}_{f.filename}'`.
3.  **Text Extraction**: `PyPDF2` is used to extract text content from the PDF. A limit of 80,000 characters is applied to the extracted text to manage AI processing load.
4.  **AI Parsing**: The extracted text is sent to a Gemini model via the `_parse_pdf_with_gemini` utility (located in `_parse_pdf_with_gemini`) for structured data extraction.
    *   This function can optionally parse for both gym and nutrition data if `also_nutrition` is enabled.
5.  **Program Creation**:
    *   Any previously active `GymProgram` for the user is deactivated.
    *   A new `GymProgram` is created based on the AI-parsed data.
    *   Seven `GymRoutine`s are created for the new program. If the AI provides specific day data, routines are named accordingly; otherwise, they default to "Rest Day".
    *   For each routine with parsed exercise data, `GymExercise` entries are created. These can include:
        *   `name` (English) and `name_es_display` (Spanish)
        *   `target_sets` (e.g., `3`)
        *   `target_reps` (e.g., `'8-12'` as a string)
        *   `notes`
        *   `is_per_side` (boolean, for unilateral exercises)
        *   `has_drop_set` (boolean)
        *   `rir_target` (Reps In Reserve target)
6.  **Day Reset**: After a successful import, `current_user.current_gym_day` is reset to `1`.

!!! warning Error Handling
> The import process includes robust error handling for file issues, PDF reading failures, and AI parsing errors, providing informative flash messages to the user.

## Technical Architecture Highlights

*   **Flask Blueprint**: The module is encapsulated within `gym_bp = Blueprint('gym', __name__, url_prefix='/gym')`.
*   **Database Models**: It relies heavily on SQLAlchemy models for data persistence, including `GymRoutine`, `GymExercise`, `GymProgram`, and `GymLog`.
*   **Utility Functions**: Uses `werkzeug.utils.secure_filename` for file security and `app.utils.module_required` for access control.

## Related

*   MyBrain Overview
*   MyBrain Nutrition Module
*   MyBrain Development Notes
---