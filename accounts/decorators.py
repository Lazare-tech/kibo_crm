from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. Vérifier si l'utilisateur a un profil
            if not hasattr(request.user, 'profile'):
                raise PermissionDenied
            
            # 2. Vérifier si sa boutique est active (Validée par toi)
            if not request.user.profile.boutique.is_active:
                # Tu peux rediriger vers une page "En attente de validation"
                raise PermissionDenied 

            # 3. Vérifier si son rôle est autorisé
            if request.user.profile.role in allowed_roles or request.user.profile.role == 'admin':
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return _wrapped_view
    return decorator