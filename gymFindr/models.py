from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.gis.db import models as geomodels


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, first_name, last_name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_business_owner = models.BooleanField(default=False)
    business_name = models.CharField(max_length=255, blank=True, null=True)
    # city_location = models.CharField(max_length=100, blank=True, null=True)
    # mobile_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    # For any additional fields that are not part of the CustomUser

    def __str__(self):
        return f"{self.user.email}'s profile"

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

class Gym(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    free_trial = models.BooleanField(default=False)
    classes_available = models.BooleanField(default=False) #e.g Swimming
    location = models.OneToOneField('Location', on_delete=models.CASCADE, null=True, blank=True)
    contact_info = models.OneToOneField('ContactInfo', on_delete=models.CASCADE, null=True, blank=True)
    classes = models.ManyToManyField('ClassCategory', blank=True)
    amenities = models.ManyToManyField('Amenity', blank=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    street_address1 = models.CharField(max_length=255)
    street_address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    coordinates = geomodels.PointField(geography=True, blank=True, null=True)

    def __str__(self):
        return f"{self.street_address1}, {self.city}, {self.country}"


class ContactInfo(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.email


class GymImage(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='gym_images/', blank=True, null=True)

    def __str__(self):
        return f"Image for {self.gym.name}"

class MembershipType(models.Model):
    MEMBERSHIP_CHOICES = [
        ('DAY_PASS', 'Day Pass'),
        ('WEEKLY_PASS', 'Weekly Pass'),
        ('BIWEEKLY_PASS', 'Bi-weekly Pass'),
        ('MONTH', 'Monthly Membership'),
        ('YEAR', 'Annual Membership'),
    ]
    gym = models.ForeignKey(Gym, related_name='membership_types', on_delete=models.CASCADE)
    type = models.CharField(max_length=100, choices=MEMBERSHIP_CHOICES)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.get_type_display()} for {self.gym.name}"


class ClassCategory(models.Model):
    CATEGORY_CHOICES = [
        ('YOGA', 'Yoga'),
        ('CROSSFIT', 'CrossFit'),
        ('STRENGTH', 'Strength Training'),
        ('ZUMBA', 'Zumba'),
        ('SWIMMING', 'Swimming'),
        ('BOXING', 'Boxing'),
        ('CYCLING', 'Cycling'),
        ('PILATES', 'Pilates'),
        ('DANCE', 'Dance'),
        ('MEDITATION', 'Meditation'),
        ('MASSAGES', 'Massages'),
        ('MARTIAL_ARTS', 'Martial Arts'),
        ('PRENATAL_CLASS', 'Prenatal Class')
    ]
    name = models.CharField(max_length=100, choices=CATEGORY_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Amenity(models.Model):
    AMENITY_CHOICES = [
        ('PARKING', 'Parking'),
        ('LOCKER', 'Locker'),
        ('SHOWER', 'Shower'),
        ('SAUNA', 'Sauna'),
        ('POOL', 'Swimming Pool'),
        ('PERSONAL_TRAINING', 'Personal Training'),
        ('STEAM_ROOM', 'Steam Room'),
        ('CARDIO_EQUIPMENT', 'Cardio Equipment'),
        ('NUTRITIONAL_SUPPORT', 'Nutritional Support'),
        ('CHILD_CARE', 'Child Care'),
        ('GROUP_CLASSES', 'Group Classes'),
        ('SUNDAY_OPEN', 'Sunday Open'),
        ('24_HOUR', '24-Hour'),
    ]
    name = models.CharField(max_length=100, choices=AMENITY_CHOICES, unique=True)

    def __str__(self):
        return self.name


class OperatingHour(models.Model):
    gym = models.ForeignKey(Gym, related_name='operating_hours', on_delete=models.CASCADE)
    DAY_CHOICES = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    ]
    day = models.CharField(max_length=3, choices=DAY_CHOICES)
    open_time = models.TimeField()
    close_time = models.TimeField()

    def __str__(self):
        return f"{self.get_day_display()} {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorites', on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, related_name='favorited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'gym')  # Ensures a user can only favorite a gym once

    def __str__(self):
        return f"{self.user.username} likes {self.gym.name}"
