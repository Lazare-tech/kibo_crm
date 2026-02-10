from django.contrib import admin
from .models import Lead
# Register your models here.


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'status', 'source', 'date_added')
    list_filter = ('status', 'source', 'agent')
    search_fields = ('first_name', 'last_name', 'email')
