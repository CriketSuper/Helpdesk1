from django.contrib import admin
from .models import Ticket, UserProfile, Document
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'get_created_by_verbose_name', 'get_technician_verbose_name', 'criticalness', 'published', 'progress', 'status')
    list_display_links = ('id', 'title')
    search_fields = ('id', 'title')
    
    def get_created_by_verbose_name(self, obj):
        return obj.created_by.profile.verbose_name if obj.created_by and obj.created_by.profile else None
    get_created_by_verbose_name.short_description = 'Автор'

    def get_technician_verbose_name(self, obj):
        return obj.technician.profile.verbose_name if obj.technician and obj.technician.profile else None
    get_technician_verbose_name.short_description = 'Исполнитель'

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Дополнительная информация'
    verbose_name_plural = 'Дополнительная информация'

    fieldsets = (
        (None, {
            'fields': ('verbose_name',)
        }),
    )
    
class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Document)
