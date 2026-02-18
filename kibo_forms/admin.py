from django.contrib import admin

from django.contrib import admin
from .models import Form, Question, Submission
# Register your models here.

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3

@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'created_at')
    inlines = [QuestionInline]

admin.site.register(Submission)