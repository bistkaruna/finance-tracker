from django.contrib import admin
from .models import Transaction, Goal, Budget

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'date', 'type', 'get_category_display', 'user')
    list_filter = ('type', 'date', 'category')
    search_fields = ('description',)
    date_hierarchy = 'date'
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    get_category_display.short_description = 'Category'

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_amount', 'current_amount', 'deadline', 'user')
    list_filter = ('deadline',)
    search_fields = ('name',)

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('get_category_display', 'amount', 'period', 'start_date', 'user')
    list_filter = ('period', 'start_date')
    
    def get_category_display(self, obj):
        return obj.get_category_display()
    get_category_display.short_description = 'Category'