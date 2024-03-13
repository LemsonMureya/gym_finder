import requests
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.core.exceptions import ValidationError
from .models import Gym
from django.db.models import Q
from .forms import GymForm, CustomUserCreationForm, LocationForm, ContactInfoForm, GymImageFormSet, MembershipTypeFormSet, OperatingHourFormSet, GymSearchForm
from .models import Location, ContactInfo, Gym
from django.contrib.auth.forms import UserCreationForm
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.conf import settings
from django.contrib.gis.geos import Point, fromstr
from django.contrib.gis.db.models.functions import Distance


User = get_user_model()

class UserRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_business_owner'] = False
        return kwargs

class BusinessOwnerRegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('gymFindr:gym_create')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['is_business_owner'] = True
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        # Check if the registered user is a business owner
        if form.instance.is_business_owner:
            # Redirect to the gym creation page
            return redirect('gymFindr:gym_create')
        return response

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

    def get_success_url(self):
        return reverse_lazy('gymFindr:gym_list')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

class GymListView(ListView):
    model = Gym
    context_object_name = 'gyms'
    template_name = 'gyms/gym_list.html'

class GymDetailView(DetailView):
    model = Gym
    context_object_name = 'gym'
    template_name = 'gyms/gym_detail.html'

def geocode_address(address):
    """Converts address to coordinates using Google Maps Geocoding API."""
    api_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'address': address, 'key': settings.GOOGLE_MAPS_API_KEY}
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    return None, None

class GymCreateView(LoginRequiredMixin, CreateView):
    model = Gym
    form_class = GymForm
    template_name = 'gyms/gym_edit.html'
    success_url = reverse_lazy('gymFindr:gym_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['location_form'] = LocationForm(self.request.POST, prefix='location')
            context['contact_info_form'] = ContactInfoForm(self.request.POST, prefix='contact_info')
            context['image_formset'] = GymImageFormSet(self.request.POST, self.request.FILES, prefix='images')
            context['membership_formset'] = MembershipTypeFormSet(self.request.POST, prefix='memberships')
            context['operating_hour_formset'] = OperatingHourFormSet(self.request.POST, prefix='operating_hours')
        else:
            context['location_form'] = LocationForm(prefix='location')
            context['contact_info_form'] = ContactInfoForm(prefix='contact_info')
            context['image_formset'] = GymImageFormSet(prefix='images')
            context['membership_formset'] = MembershipTypeFormSet(prefix='memberships')
            context['operating_hour_formset'] = OperatingHourFormSet(prefix='operating_hours')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        location_form = context['location_form']
        contact_info_form = context['contact_info_form']
        image_formset = context['image_formset']
        membership_formset = context['membership_formset']
        operating_hour_formset = context['operating_hour_formset']

        if (form.is_valid() and location_form.is_valid() and contact_info_form.is_valid() and
            image_formset.is_valid() and membership_formset.is_valid() and operating_hour_formset.is_valid()):
            self.object = form.save(commit=False)
            self.object.owner = self.request.user

            # Explicitly saving location and contact info first
            # location = location_form.save()
            location = location_form.save(commit=False)
            full_address = f"{location.street_address1}, {location.city}, {location.zip_code}, {location.country}"
            lat, lng = geocode_address(full_address)
            if lat and lng:
                # If geocoding is successful, use the precise coordinates
                location.coordinates = Point(lng, lat, srid=4326)
            else:
                # Fallback: Attempt geocoding with just city and country (or zip code)
                fallback_address = f"{location.city}, {location.country}"
                lat, lng = geocode_address(fallback_address)
                if lat and lng:
                    location.coordinates = Point(lng, lat, srid=4326)
                else:
                     # Set to default New York City coordinates
                     location.coordinates = Point(-74.0060, 40.7128, srid=4326)  # Placeholder or predefined point
            location.save()
            contact_info = contact_info_form.save()
            self.object.location = location
            self.object.contact_info = contact_info
            self.object.save()
            self.object.classes.set(form.cleaned_data['classes'])
            self.object.amenities.set(form.cleaned_data['amenities'])
            # Saving formsets with the instance
            image_formset.instance = self.object
            image_formset.save()
            membership_formset.instance = self.object
            membership_formset.save()
            operating_hour_formset.instance = self.object
            operating_hour_formset.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(context)

class GymUpdateView(LoginRequiredMixin, UpdateView):
    model = Gym
    form_class = GymForm
    template_name = 'gyms/gym_edit.html'
    success_url = reverse_lazy('gymFindr:gym_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = self.get_object()
        if self.request.POST:
            context['location_form'] = LocationForm(self.request.POST, instance=instance.location, prefix='location')
            context['contact_info_form'] = ContactInfoForm(self.request.POST, instance=instance.contact_info, prefix='contact_info')
            context['image_formset'] = GymImageFormSet(self.request.POST, self.request.FILES, instance=instance, prefix='images')
            context['membership_formset'] = MembershipTypeFormSet(self.request.POST, instance=instance, prefix='memberships')
            context['operating_hour_formset'] = OperatingHourFormSet(self.request.POST, instance=instance, prefix='operating_hours')
        else:
            context['location_form'] = LocationForm(instance=instance.location, prefix='location')
            context['contact_info_form'] = ContactInfoForm(instance=instance.contact_info, prefix='contact_info')
            context['image_formset'] = GymImageFormSet(instance=instance, prefix='images')
            context['membership_formset'] = MembershipTypeFormSet(instance=instance, prefix='memberships')
            context['operating_hour_formset'] = OperatingHourFormSet(instance=instance, prefix='operating_hours')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        location_form = context['location_form']
        contact_info_form = context['contact_info_form']
        image_formset = context['image_formset']
        membership_formset = context['membership_formset']
        operating_hour_formset = context['operating_hour_formset']

        if form.is_valid() and location_form.is_valid() and contact_info_form.is_valid() \
                and image_formset.is_valid() and membership_formset.is_valid() and operating_hour_formset.is_valid():

            self.object = form.save()
            # Saving Location and ContactInfo with explicit reference
            location = location_form.save(commit=False)
            full_address = f"{location.street_address1}, {location.city}, {location.zip_code}, {location.country}"
            lat, lng = geocode_address(full_address)

            if lat and lng:
                # If geocoding is successful, use the precise coordinates
                location.coordinates = Point(lng, lat, srid=4326)
            else:
                # Fallback: Attempt geocoding with just city and country (or zip code)
                fallback_address = f"{location.city}, {location.country}"
                lat, lng = geocode_address(fallback_address)
                if lat and lng:
                    location.coordinates = Point(lng, lat, srid=4326)
                else:
                     # Set to default New York City coordinates
                     location.coordinates = Point(-74.0060, 40.7128, srid=4326)  # Placeholder or predefined point
            location.save()
            contact_info = contact_info_form.save()
            self.object.location = location
            self.object.contact_info = contact_info
            self.object.save()
            self.object.classes.set(form.cleaned_data['classes'])
            self.object.amenities.set(form.cleaned_data['amenities'])

            # Saving formsets with the instance
            image_formset.instance = self.object
            image_formset.save()
            membership_formset.instance = self.object
            membership_formset.save()

            operating_hour_formset.instance = self.object
            operating_hour_formset.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(context)

class GymDeleteView(DeleteView):
    model = Gym
    context_object_name = 'gym'
    success_url = reverse_lazy('gymFindr:gym_list')
    template_name = 'gyms/gym_confirm_delete.html'

class MyGymsView(LoginRequiredMixin, ListView):
    model = Gym
    template_name = 'gyms/my_gyms.html'

    def get_queryset(self):
        return Gym.objects.filter(owner=self.request.user)


class GymSearchView(ListView):
    model = Gym
    template_name = 'gyms/gym_search.html'
    context_object_name = 'gyms'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.form = GymSearchForm(self.request.GET or None)
        if self.form.is_bound:
            try:
                self.form.is_valid()
            except ValidationError:
                return Gym.objects.none()

            use_current_location = self.request.GET.get('use_current_location') == 'on'
            lat = self.request.GET.get('lat')
            lng = self.request.GET.get('lng')
            search_location = self.form.cleaned_data.get('search_location')

            if use_current_location and lat and lng:
                try:
                    lat = float(lat)
                    lng = float(lng)
                    user_location = Point(lng, lat, srid=4326)
                    queryset = queryset.annotate(distance=Distance('location__coordinates', user_location)).order_by('distance')
                except ValueError:
                    # Handle the error when conversion fails
                    queryset = Gym.objects.none()
            elif search_location:
                # Use the search_location to geocode and filter the queryset based on distance
                lat, lng = geocode_address(search_location)  # Implement this function based on your geocoding service
                if lat is not None and lng is not None:
                    search_point = Point(lng, lat, srid=4326)
                    queryset = queryset.annotate(distance=Distance('location__coordinates', search_point)).order_by('distance')
                else:
                    # Fallback if geocoding fails or no location found
                    queryset = Gym.objects.none()
            else:
                # Your existing filters for query, class_category, and amenity
                filters = Q()
                query = self.form.cleaned_data.get('query')
                class_category = self.form.cleaned_data.get('class_category')
                amenity = self.form.cleaned_data.get('amenity')
                if query:
                    filters |= Q(name__icontains=query) | Q(description__icontains=query)
                if class_category:
                    filters &= Q(classes=class_category)
                if amenity:
                    filters &= Q(amenities=amenity)
                queryset = queryset.filter(filters).distinct()
        else:
            queryset = Gym.objects.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        return context
