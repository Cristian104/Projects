import os
import json
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.modules.nutrition.models import (
    NutritionPlan, NutritionMeal, MealIngredient,
    NutritionLog, WaterLog, SupplementProtocol, SupplementLog
)
from app.utils import module_required

nutrition_bp = Blueprint('nutrition', __name__, url_prefix='/nutrition')


def _get_active_plan():
    return NutritionPlan.query.filter_by(user_id=current_user.id, is_active=True).first()


@nutrition_bp.route('/')
@login_required
@module_required('nutrition')
def today():
    today_date = date.today()
    plan = _get_active_plan()

    meals = []
    supplements = []
    water_ml = 0
    meal_logs = {}
    supplement_logs = {}

    if plan:
        meals = NutritionMeal.query.filter_by(plan_id=plan.id).order_by(NutritionMeal.order_index).all()
        supplements = SupplementProtocol.query.filter_by(plan_id=plan.id).order_by(SupplementProtocol.timing).all()

        # Load today's meal logs
        for m in meals:
            log = NutritionLog.query.filter_by(
                user_id=current_user.id, meal_id=m.id, date=today_date).first()
            meal_logs[m.id] = log

        # Load today's supplement logs
        for s in supplements:
            log = SupplementLog.query.filter_by(
                user_id=current_user.id, supplement_id=s.id, date=today_date, timing=s.timing).first()
            supplement_logs[s.id] = log

        # Water
        wl = WaterLog.query.filter_by(user_id=current_user.id, date=today_date).first()
        water_ml = wl.amount_ml if wl else 0

    return render_template('nutrition/today.html',
                           plan=plan, meals=meals, supplements=supplements,
                           water_ml=water_ml, meal_logs=meal_logs,
                           supplement_logs=supplement_logs, today=today_date)


@nutrition_bp.route('/api/toggle_meal', methods=['POST'])
@login_required
def toggle_meal():
    data = request.get_json()
    meal_id = data.get('meal_id')
    today_date = date.today()
    variant = data.get('variant')

    meal = NutritionMeal.query.get_or_404(meal_id)
    log = NutritionLog.query.filter_by(
        user_id=current_user.id, meal_id=meal_id, date=today_date).first()

    if log:
        log.done = not log.done
        log.completed_at = datetime.utcnow() if log.done else None
        if variant:
            log.variant_chosen = variant
    else:
        log = NutritionLog(
            user_id=current_user.id,
            meal_id=meal_id,
            date=today_date,
            done=True,
            variant_chosen=variant,
            completed_at=datetime.utcnow()
        )
        db.session.add(log)

    db.session.commit()
    return jsonify({'success': True, 'done': log.done})


@nutrition_bp.route('/api/water', methods=['POST'])
@login_required
def log_water():
    data = request.get_json()
    amount = data.get('amount_ml', 0)
    today_date = date.today()

    wl = WaterLog.query.filter_by(user_id=current_user.id, date=today_date).first()
    if wl:
        wl.amount_ml = max(0, wl.amount_ml + amount)
    else:
        wl = WaterLog(user_id=current_user.id, date=today_date, amount_ml=max(0, amount))
        db.session.add(wl)
    db.session.commit()
    return jsonify({'success': True, 'amount_ml': wl.amount_ml})


@nutrition_bp.route('/api/toggle_supplement', methods=['POST'])
@login_required
def toggle_supplement():
    data = request.get_json()
    supplement_id = data.get('supplement_id')
    today_date = date.today()

    sup = SupplementProtocol.query.get_or_404(supplement_id)
    log = SupplementLog.query.filter_by(
        user_id=current_user.id, supplement_id=supplement_id,
        date=today_date, timing=sup.timing).first()

    if log:
        log.done = not log.done
        log.completed_at = datetime.utcnow() if log.done else None
    else:
        log = SupplementLog(
            user_id=current_user.id,
            supplement_id=supplement_id,
            date=today_date,
            timing=sup.timing,
            done=True,
            completed_at=datetime.utcnow()
        )
        db.session.add(log)

    db.session.commit()
    return jsonify({'success': True, 'done': log.done})


@nutrition_bp.route('/plans')
@login_required
def plans():
    all_plans = NutritionPlan.query.filter_by(
        user_id=current_user.id).order_by(NutritionPlan.created_at.desc()).all()
    return render_template('nutrition/plans.html', plans=all_plans)


@nutrition_bp.route('/plan/<int:plan_id>')
@login_required
def plan_detail(plan_id):
    plan = NutritionPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        return redirect(url_for('nutrition.plans'))
    meals = NutritionMeal.query.filter_by(plan_id=plan.id).order_by(NutritionMeal.order_index).all()
    supplements = SupplementProtocol.query.filter_by(plan_id=plan.id).order_by(SupplementProtocol.timing).all()
    return render_template('nutrition/plan_detail.html', plan=plan, meals=meals, supplements=supplements)


@nutrition_bp.route('/plan/activate/<int:plan_id>')
@login_required
def activate_plan(plan_id):
    NutritionPlan.query.filter_by(user_id=current_user.id).update({'is_active': False})
    plan = NutritionPlan.query.get_or_404(plan_id)
    if plan.user_id == current_user.id:
        plan.is_active = True
        db.session.commit()
        flash(f'Nutrition plan "{plan.name}" is now active.', 'success')
    return redirect(url_for('nutrition.today'))


@nutrition_bp.route('/plan/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete_plan(plan_id):
    plan = NutritionPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        return redirect(url_for('nutrition.plans'))
    name = plan.name
    db.session.delete(plan)
    db.session.commit()
    flash(f'Plan "{name}" deleted.', 'success')
    return redirect(url_for('nutrition.plans'))


@nutrition_bp.route('/history')
@login_required
def history():
    meal_logs = (NutritionLog.query
                 .filter_by(user_id=current_user.id, done=True)
                 .order_by(NutritionLog.date.desc())
                 .limit(300).all())
    water_logs = (WaterLog.query
                  .filter_by(user_id=current_user.id)
                  .order_by(WaterLog.date.desc())
                  .limit(60).all())

    # Build meal id → name lookup
    meal_ids = {log.meal_id for log in meal_logs}
    meals_map = {}
    if meal_ids:
        for m in NutritionMeal.query.filter(NutritionMeal.id.in_(meal_ids)).all():
            meals_map[m.id] = m

    # Group by date
    days = {}
    for log in meal_logs:
        d = log.date
        if d not in days:
            days[d] = {'meals': [], 'water_ml': 0}
        days[d]['meals'].append({'log': log, 'meal': meals_map.get(log.meal_id)})

    for wl in water_logs:
        if wl.date in days:
            days[wl.date]['water_ml'] = wl.amount_ml
        else:
            days[wl.date] = {'meals': [], 'water_ml': wl.amount_ml}

    sorted_days = sorted(days.items(), key=lambda x: x[0], reverse=True)
    return render_template('nutrition/history.html', days=sorted_days)


@nutrition_bp.route('/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
    f = request.files.get('pdf_file')
    plan_name = request.form.get('plan_name', 'Imported Plan')
    also_gym = request.form.get('also_gym') == 'on'

    if not f or not f.filename.lower().endswith('.pdf'):
        flash('Please upload a PDF file.', 'error')
        return redirect(url_for('nutrition.plans'))

    # Save file
    upload_dir = os.path.join(current_app.instance_path, 'uploads', 'nutrition')
    os.makedirs(upload_dir, exist_ok=True)
    from werkzeug.utils import secure_filename
    filename = secure_filename(f'{current_user.id}_{datetime.utcnow().timestamp()}_{f.filename}')
    filepath = os.path.join(upload_dir, filename)
    f.save(filepath)

    # Extract text
    try:
        import PyPDF2
        with open(filepath, 'rb') as pf:
            reader = PyPDF2.PdfReader(pf)
            text = '\n'.join(page.extract_text() or '' for page in reader.pages)
        text = text[:80000]
    except Exception as e:
        flash(f'Could not read PDF: {e}', 'error')
        return redirect(url_for('nutrition.plans'))

    # Parse with Gemini
    try:
        parsed = _parse_pdf_with_gemini(text, plan_name)
    except Exception as e:
        flash(f'Gemini parsing failed: {e}', 'error')
        return redirect(url_for('nutrition.plans'))

    # Create records
    try:
        new_plan = _create_records_from_parsed(parsed, plan_name, filename, also_gym)
        flash(f'Plan "{new_plan.name}" imported successfully!', 'success')
        return redirect(url_for('nutrition.plan_detail', plan_id=new_plan.id))
    except Exception as e:
        flash(f'Failed to save plan: {e}', 'error')
        return redirect(url_for('nutrition.plans'))


def _parse_pdf_with_gemini(text, plan_name):
    import google.generativeai as genai

    api_key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""You are parsing a Spanish-language fitness coach PDF that contains a gym training program and a nutrition plan.

Extract ALL the information and return a single valid JSON object with EXACTLY this structure:

{{
  "gym_program": {{
    "name": "string (program name or '{plan_name}')",
    "days": [
      {{
        "day_number": 1,
        "name": "string (e.g. Pecho y Tríceps)",
        "exercises": [
          {{
            "name_es": "string",
            "name_en": "string (translate)",
            "sets": 3,
            "reps": "8-12",
            "notes": "string or null",
            "is_per_side": false,
            "has_drop_set": false,
            "rir_target": null
          }}
        ]
      }}
    ]
  }},
  "nutrition_plan": {{
    "name": "string (plan name or '{plan_name}')",
    "meals": [
      {{
        "order": 1,
        "name": "COMIDA I",
        "meal_type": "regular",
        "time_hint": "string or null",
        "ingredients": [
          {{
            "name": "string",
            "quantity_g": 100,
            "unit": "g",
            "is_protein_swap": false,
            "swap_group": null,
            "notes": null
          }}
        ]
      }}
    ],
    "supplements": [
      {{
        "name": "string",
        "dose": "string",
        "timing": "morning|post-workout|night|with-meal",
        "notes": null
      }}
    ]
  }}
}}

IMPORTANT RULES:
- For protein swaps (e.g. "Pollo / Res / Cerdo"), set is_protein_swap=true and give all alternatives the SAME swap_group string (e.g. "protein_comida_1")
- "c/u" or "cada uno" means is_per_side=true
- "al fallo" means reps="al fallo"
- "drop set" or "descendente" means has_drop_set=true
- RIR numbers: extract the integer
- If the PDF has no gym program, set gym_program to null
- If the PDF has no nutrition plan, set nutrition_plan to null
- Return ONLY the raw JSON, no markdown, no explanation

PDF TEXT:
{text}"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown fences if present
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[1] if '\n' in raw else raw[3:]
        if raw.endswith('```'):
            raw = raw[:-3]
        raw = raw.strip()

    return json.loads(raw)


def _create_records_from_parsed(parsed, plan_name, source_file, also_gym):
    from app.modules.gym.models import GymProgram, GymRoutine, GymExercise

    nutrition_data = parsed.get('nutrition_plan')
    gym_data = parsed.get('gym_program')

    # Deactivate current plan
    NutritionPlan.query.filter_by(user_id=current_user.id).update({'is_active': False})

    new_plan = NutritionPlan(
        user_id=current_user.id,
        name=nutrition_data['name'] if nutrition_data else plan_name,
        is_active=True,
        source_file=source_file
    )
    db.session.add(new_plan)
    db.session.flush()

    if nutrition_data:
        for meal_data in nutrition_data.get('meals', []):
            meal = NutritionMeal(
                plan_id=new_plan.id,
                order_index=meal_data.get('order', 0),
                name=meal_data.get('name', 'Meal'),
                meal_type=meal_data.get('meal_type', 'regular'),
                time_hint=meal_data.get('time_hint')
            )
            db.session.add(meal)
            db.session.flush()

            for ing_data in meal_data.get('ingredients', []):
                ing = MealIngredient(
                    meal_id=meal.id,
                    name=ing_data.get('name', ''),
                    quantity_g=ing_data.get('quantity_g'),
                    unit=ing_data.get('unit', 'g'),
                    is_protein_swap=ing_data.get('is_protein_swap', False),
                    swap_group=ing_data.get('swap_group'),
                    notes=ing_data.get('notes')
                )
                db.session.add(ing)

        for sup_data in nutrition_data.get('supplements', []):
            sup = SupplementProtocol(
                plan_id=new_plan.id,
                name=sup_data.get('name', ''),
                dose=sup_data.get('dose'),
                timing=sup_data.get('timing', 'morning'),
                notes=sup_data.get('notes')
            )
            db.session.add(sup)

    if also_gym and gym_data:
        GymProgram.query.filter_by(user_id=current_user.id).update({'is_active': False})
        gym_prog = GymProgram(
            user_id=current_user.id,
            name=gym_data.get('name', plan_name),
            is_active=True
        )
        db.session.add(gym_prog)
        db.session.flush()

        days = gym_data.get('days', [])
        # Fill up to 7 days
        for i in range(1, 8):
            day_data = next((d for d in days if d.get('day_number') == i), None)
            routine = GymRoutine(
                user_id=current_user.id,
                program_id=gym_prog.id,
                name=day_data['name'] if day_data else 'Rest Day',
                order_index=i
            )
            db.session.add(routine)
            db.session.flush()

            if day_data:
                for idx, ex_data in enumerate(day_data.get('exercises', [])):
                    ex = GymExercise(
                        routine_id=routine.id,
                        name=ex_data.get('name_en') or ex_data.get('name_es', ''),
                        name_es_display=ex_data.get('name_es'),
                        target_sets=ex_data.get('sets', 3),
                        target_reps=str(ex_data.get('reps', '8-12')),
                        notes=ex_data.get('notes'),
                        is_per_side=ex_data.get('is_per_side', False),
                        has_drop_set=ex_data.get('has_drop_set', False),
                        rir_target=ex_data.get('rir_target'),
                        order_index=idx
                    )
                    db.session.add(ex)

        current_user.current_gym_day = 1

    db.session.commit()
    return new_plan
