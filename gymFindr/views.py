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
            location = location_form.save()
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
            location = location_form.save()
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
            # Ensure the form is valid or raise a validation error
            try:
                self.form.is_valid()
            except ValidationError:
                return Gym.objects.none()

            # Ensure at least one field has been filled
            query = self.form.cleaned_data.get('query')
            class_category = self.form.cleaned_data.get('class_category')
            amenity = self.form.cleaned_data.get('amenity')

            if query or class_category or amenity:
                filters = Q()
                if query:
                    filters |= Q(name__icontains=query) | Q(description__icontains=query) | Q(location__city__icontains=query) | Q(location__zip_code__icontains=query) | Q(location__street_address1__icontains=query)
                if class_category:
                    filters &= Q(classes=class_category)
                if amenity:
                    filters &= Q(amenities=amenity)
                queryset = queryset.filter(filters).distinct()
            else:
                # If no search criteria are entered, do not return any results
                queryset = Gym.objects.none()
        else:
            # If the form is not bound (i.e., no GET parameters), do not return any results
            queryset = Gym.objects.none()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form
        return context
