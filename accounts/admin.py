from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'boutique')
    list_filter = ('role', 'boutique')
    search_fields = ('user__username', 'user__email', 'boutique__nom')

# Pour que toi (le Boss) tu puisses valider une boutique par email/tel
# Ajoute BoutiqueAdmin dans mplace/admin.py si ce n'est pas fait