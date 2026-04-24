from app.extensions import db
from datetime import datetime


class NutritionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    source_file = db.Column(db.String(255))

    meals = db.relationship('NutritionMeal', backref='plan', lazy=True, cascade='all, delete-orphan')
    supplements = db.relationship('SupplementProtocol', backref='plan', lazy=True, cascade='all, delete-orphan')


class NutritionMeal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('nutrition_plan.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    name = db.Column(db.String(100), nullable=False)
    meal_type = db.Column(db.String(50), default='regular')  # regular, snack, pre-workout, post-workout
    time_hint = db.Column(db.String(50))  # e.g. "8:00", "Post entreno"

    ingredients = db.relationship('MealIngredient', backref='meal', lazy=True, cascade='all, delete-orphan')


class MealIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('nutrition_meal.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    quantity_g = db.Column(db.Float)
    unit = db.Column(db.String(30))  # g, ml, units, tbsp, etc.
    is_protein_swap = db.Column(db.Boolean, default=False)
    swap_group = db.Column(db.String(50))  # same string on alternatives in same meal
    notes = db.Column(db.String(200))


class NutritionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('nutrition_meal.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    done = db.Column(db.Boolean, default=False)
    variant_chosen = db.Column(db.String(150))  # which protein swap was picked
    completed_at = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint('user_id', 'meal_id', 'date', name='_nutrition_log_uc'),)


class WaterLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount_ml = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_water_log_uc'),)


class SupplementProtocol(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('nutrition_plan.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dose = db.Column(db.String(100))
    timing = db.Column(db.String(50), default='morning')  # morning, post-workout, night, with-meal
    notes = db.Column(db.String(200))


class SupplementLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    supplement_id = db.Column(db.Integer, db.ForeignKey('supplement_protocol.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    timing = db.Column(db.String(50))
    done = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint('user_id', 'supplement_id', 'date', 'timing', name='_supplement_log_uc'),)
