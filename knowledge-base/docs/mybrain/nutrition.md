# MyBrain Nutrition Module Overview

The `MyBrain Nutrition` module (`app/modules/nutrition`) within the MyBrain Portal is designed to empower users with comprehensive tools for managing their dietary intake, hydration, and supplement protocols. It provides a structured approach to meal planning, daily tracking of consumption, and robust management of nutrition plans.

!!! info Purpose
> This module aims to facilitate personal health and fitness goals by making it easy to log meals, track water intake, and adhere to supplement regimens, all within customizable nutrition plans.

## Key Functionalities

The module is built around several core features, accessible via a Flask web interface and specific API endpoints.

### 1. Daily Tracking & Logging
The primary interface for daily interaction is the `/nutrition` route. Users can view their active plan for the day and log completed items.

!!! tip Today's Summary
> Navigate to `/nutrition` to see your active plan, meals, supplements, and water intake for the current day.

*   **Meal Logging**: Users can mark meals as consumed, with support for choosing specific variants.
    *   **Endpoint**: `POST /nutrition/api/toggle_meal`
    *   **Payload**: `{ "meal_id": <int>, "variant": <string, optional> }`
*   **Water Intake**: Track daily water consumption.
    *   **Endpoint**: `POST /nutrition/api/water`
    *   **Payload**: `{ "amount_ml": <int> }` (Adds or subtracts from current total)
*   **Supplement Logging**: Mark specific supplements as taken according to their protocol.
    *   **Endpoint**: `POST /nutrition/api/toggle_supplement`
    *   **Payload**: `{ "supplement_id": <int> }`

### 2. Nutrition Plan Management
The module allows for the creation, viewing, activation, and deletion of personalized nutrition plans. Each plan can comprise multiple meals and supplement protocols.

*   **View All Plans**: Lists all nutrition plans created by the user.
    *   **Route**: `/nutrition/plans`
*   **Plan Details**: Provides a detailed view of a specific nutrition plan, including its associated meals and supplements.
    *   **Route**: `/nutrition/plan/<int:plan_id>`
*   **Activate Plan**: Sets a specific plan as the active plan, deactivating any previously active plans for the user.
    *   **Route**: `/nutrition/plan/activate/<int:plan_id>`
*   **Delete Plan**: Removes a nutrition plan and all its associated data (meals, ingredients, logs).
    *   **Route**: `POST /nutrition/plan/delete/<int:plan_id>`

!!! warning Data Deletion
> Deleting a nutrition plan is irreversible and will remove all linked meals, ingredients, and historical logs for that plan.

## Technical Details

The MyBrain Nutrition module leverages standard Flask patterns and integrates with the application's core services.

*   **Blueprint**: `nutrition_bp` is registered with the application, handling all routes prefixed with `/nutrition`.
*   **Authentication**: All endpoints are protected with `@login_required`, ensuring only authenticated users can access nutrition data.
*   **Authorization**: The `@module_required('nutrition')` decorator ensures that the user has access to this specific module.
*   **Database Integration**: Uses SQLAlchemy via `app.extensions.db` to interact with the PostgreSQL database. Key models include:
    *   `NutritionPlan`: Defines a user's overarching nutrition strategy.
    *   `NutritionMeal`: Individual meals within a plan.
    *   `MealIngredient`: Components of a meal.
    *   `NutritionLog`, `WaterLog`, `SupplementLog`: Records of daily consumption.
    *   `SupplementProtocol`: Defines a user's supplement regimen.
*   **Templates**: Renders HTML templates located in `templates/nutrition/` for the web interface (e.g., `today.html`, `plans.html`, `plan_detail.html`).

```python
# Example Blueprint registration (conceptual)
# In app/__init__.py or similar configuration file
from app.modules.nutrition.routes import nutrition_bp
app.register_blueprint(nutrition_bp)
```

## Developer Notes

When developing or extending this module:
*   Ensure all data access respects user ownership (`user_id=current_user.id`).
*   Consider cascading deletes for `NutritionPlan` to efficiently remove dependent `NutritionMeal`, `SupplementProtocol`, and related log entries.
*   API endpoints return JSON, making them suitable for dynamic client-side updates.

## Related

*   MyBrain Portal Overview
*   MyBrain Gym Module
*   SQLAlchemy
*   Flask
*   PostgreSQL