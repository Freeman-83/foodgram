from django.contrib import admin

from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name')
    search_fields = ('username',)
    list_filter = ('username', 'email')
    empty_value_display = '-пусто-'


admin.site.register(CustomUser, CustomUserAdmin)
