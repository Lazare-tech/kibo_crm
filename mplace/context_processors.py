from .models import Categorie

def categories_processor(request):
    """
    Rend les catégories disponibles dans tous les templates
    pour le menu de navigation.
    """
    return {
        'all_categories': Categorie.objects.all().order_by('nom')
    }