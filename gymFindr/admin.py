from django.contrib import admin
from .models import CustomUser, Gym, Location, ContactInfo, GymImage, MembershipType, ClassCategory, Amenity, OperatingHour
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_business_owner']
    # Customizing the fieldsets to include fields in the CustomUser model
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Business info', {'fields': ('business_name', 'website')}),
        # ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_business_owner', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_business_owner', 'business_name', 'website'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


class GymImageInline(admin.TabularInline):
    model = GymImage
    extra = 1  # Number of extra empty forms

class MembershipTypeInline(admin.TabularInline):
    model = MembershipType
    extra = 1  # Number of extra empty forms

class OperatingHourInline(admin.TabularInline):
    model = OperatingHour
    extra = 1  # one for each day of the week

@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'location', 'free_trial', 'classes_available')
    inlines = [GymImageInline, OperatingHourInline, MembershipTypeInline]
    filter_horizontal = ('classes', 'amenities')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('street_address1', 'city', 'zip_code', 'country')

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'website')

@admin.register(MembershipType)
class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ('gym', 'type', 'price')

@admin.register(ClassCategory)
class ClassCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(OperatingHour)
class OperatingHourAdmin(admin.ModelAdmin):
    list_display = ('gym', 'day', 'open_time', 'close_time')
