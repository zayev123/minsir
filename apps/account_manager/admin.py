from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User

# Register your models here.
class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'phone', 'name', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('Personal info', {'fields': (
            'name', 
            'image_url',
            'image', 
            'location',
            "date_of_birth",
        )}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin statistic. UserAdmin
    # overrides get_fieldsets to use this statistic when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'name', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'phone', 'name')
    ordering = ('id',)
    filter_horizontal = ()
    list_display = ['id', 'email', 'phone', 'name']


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)

# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)