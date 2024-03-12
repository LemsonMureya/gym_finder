from django import forms
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Gym, Location, ContactInfo, GymImage, MembershipType, ClassCategory, Amenity, OperatingHour



User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2', 'business_name', 'website']

    def __init__(self, *args, **kwargs):
        self.is_business_owner = kwargs.pop('is_business_owner', False)
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)

        business_fields = ['business_name', 'website']
        for field in business_fields:
            self.fields[field].required = False
            if not self.is_business_owner:
                self.fields[field].widget = forms.HiddenInput()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_business_owner = self.is_business_owner
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_business_owner', 'business_name', 'website']

class GymForm(forms.ModelForm):
    classes = forms.ModelMultipleChoiceField(queryset=ClassCategory.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    amenities = forms.ModelMultipleChoiceField(queryset=Amenity.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = Gym
        exclude = ('owner', 'location', 'contact_info')

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = '__all__'

class ContactInfoForm(forms.ModelForm):
    class Meta:
        model = ContactInfo
        fields = '__all__'

class GymSearchForm(forms.Form):
    query = forms.CharField(required=False, label='Search', widget=forms.TextInput(attrs={'placeholder': 'Search by name, location...'}))
    class_category = forms.ModelChoiceField(queryset=ClassCategory.objects.all(), required=False, label='Class')
    amenity = forms.ModelChoiceField(queryset=Amenity.objects.all(), required=False, label='Amenity')

class GymImageForm(forms.ModelForm):
    class Meta:
        model = GymImage
        fields = ('image',)

GymImageFormSet = forms.inlineformset_factory(Gym, GymImage, form=GymImageForm, extra=1)

class MembershipTypeForm(forms.ModelForm):
    class Meta:
        model = MembershipType
        fields = '__all__'

MembershipTypeFormSet = forms.inlineformset_factory(Gym, MembershipType, form=MembershipTypeForm, extra=1)

class OperatingHourForm(forms.ModelForm):
    class Meta:
        model = OperatingHour
        fields = '__all__'

OperatingHourFormSet = forms.inlineformset_factory(Gym, OperatingHour, form=OperatingHourForm, extra=1)
