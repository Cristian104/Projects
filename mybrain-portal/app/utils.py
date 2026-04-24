from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def module_required(module_name):
    """Decorator that restricts route access based on per-user module permissions."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from app.models import user_has_module
            if not user_has_module(current_user, module_name):
                flash("You don't have access to this module.", 'error')
                return redirect(url_for('dashboard.dashboard_view'))
            return f(*args, **kwargs)
        return wrapper
    return decorator
