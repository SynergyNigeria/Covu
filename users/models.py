from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator


# ==============================================================================
# NIGERIAN STATES & LGAs (For Location-based Store Listing - 40% weight)
# ==============================================================================

NIGERIAN_STATES = [
    ("abia", "Abia"),
    ("adamawa", "Adamawa"),
    ("akwa_ibom", "Akwa Ibom"),
    ("anambra", "Anambra"),
    ("bauchi", "Bauchi"),
    ("bayelsa", "Bayelsa"),
    ("benue", "Benue"),
    ("borno", "Borno"),
    ("cross_river", "Cross River"),
    ("delta", "Delta"),
    ("ebonyi", "Ebonyi"),
    ("edo", "Edo"),
    ("ekiti", "Ekiti"),
    ("enugu", "Enugu"),
    ("fct", "Federal Capital Territory"),
    ("gombe", "Gombe"),
    ("imo", "Imo"),
    ("jigawa", "Jigawa"),
    ("kaduna", "Kaduna"),
    ("kano", "Kano"),
    ("katsina", "Katsina"),
    ("kebbi", "Kebbi"),
    ("kogi", "Kogi"),
    ("kwara", "Kwara"),
    ("lagos", "Lagos"),
    ("nasarawa", "Nasarawa"),
    ("niger", "Niger"),
    ("ogun", "Ogun"),
    ("ondo", "Ondo"),
    ("osun", "Osun"),
    ("oyo", "Oyo"),
    ("plateau", "Plateau"),
    ("rivers", "Rivers"),
    ("sokoto", "Sokoto"),
    ("taraba", "Taraba"),
    ("yobe", "Yobe"),
    ("zamfara", "Zamfara"),
]

# Note: Full LGA list will be stored in a separate JSON file for better management
# This allows for easy updates without code changes
# Format: { "lagos": ["Alimosho", "Ikeja", "Surulere", ...], ... }
# For now, we use CharField to allow free-form LGA input
# TODO: Create lgas.json file with complete LGA mapping per state


# ==============================================================================
# CUSTOM USER MANAGER
# ==============================================================================


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    instead of username.
    """

    def create_user(
        self, email, phone_number, full_name, state, city, password=None, **extra_fields
    ):
        """
        Create and save a regular user with the given email, phone, name, state, city, and password.
        """
        if not email:
            raise ValueError("The Email field must be set")
        if not phone_number:
            raise ValueError("The Phone Number field must be set")
        if not full_name:
            raise ValueError("The Full Name field must be set")
        if not state:
            raise ValueError("The State field must be set")
        if not city:
            raise ValueError("The City/LGA field must be set")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            phone_number=phone_number,
            full_name=full_name,
            state=state,
            city=city,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email, phone_number, full_name, state, city, password=None, **extra_fields
    ):
        """
        Create and save a superuser with the given email, phone, name, state, city, and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email, phone_number, full_name, state, city, password, **extra_fields
        )


# ==============================================================================
# CUSTOM USER MODEL
# ==============================================================================


class CustomUser(AbstractUser):
    """
    Custom user model for COVU.

    Philosophy: "Everyone is a potential seller, but by default everyone is a buyer"

    - Email-based authentication (no username)
    - State + City (LGA) fields for location-based store listing (40% algorithm weight split randomly)
    - Wallet auto-created on user registration via Django signal
    - Phone number for WhatsApp notifications (sellers only)
    - is_seller flag automatically set to True when user creates a store
    """

    # Remove username field (we use email instead)
    username = None
    first_name = None  # We use full_name instead
    last_name = None  # We use full_name instead

    # Phone number validator (Nigerian format)
    phone_regex = RegexValidator(
        regex=r"^(\+234|0)[789][01]\d{8}$",
        message="Phone number must be in Nigerian format: +234XXXXXXXXXX or 0XXXXXXXXXX",
    )

    # Required fields
    email = models.EmailField(
        unique=True, db_index=True, help_text="User's email address (used for login)"
    )
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[phone_regex],
        db_index=True,
        help_text="Nigerian phone number for WhatsApp notifications",
    )
    full_name = models.CharField(max_length=255, help_text="User's full name")
    state = models.CharField(
        max_length=50,
        choices=NIGERIAN_STATES,
        db_index=True,  # Important for location-based queries
        help_text="Nigerian state (used in 40% location-based algorithm)",
    )
    city = models.CharField(
        max_length=100,
        db_index=True,  # Critical for granular location matching
        help_text="City/LGA (Local Government Area) - used in 40% location-based algorithm",
    )

    # Auto-managed fields
    is_seller = models.BooleanField(
        default=False,
        help_text="True when user creates a store. Everyone is a buyer by default.",
    )

    # Rate limiting fields for profile updates
    location_last_updated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time user updated state/city (30-day limit to prevent abuse)",
    )
    contact_last_updated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time user updated phone_number (30-day limit to prevent abuse)",
    )

    # Timestamps (inherited from AbstractUser, but good to document)
    # date_joined - auto-populated on creation
    # last_login - auto-populated on login

    # Override the manager
    objects = CustomUserManager()

    # Use email as the unique identifier for authentication
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number", "full_name", "state", "city"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["state"]),  # Critical for location-based listing
            models.Index(fields=["city"]),  # Critical for granular location matching
            models.Index(
                fields=["state", "city"]
            ),  # Composite index for combined queries
            models.Index(fields=["is_seller"]),
            models.Index(fields=["location_last_updated"]),
            models.Index(fields=["contact_last_updated"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def get_full_name(self):
        """Return the user's full name."""
        return self.full_name

    def get_short_name(self):
        """Return the first part of the full name."""
        return self.full_name.split()[0] if self.full_name else self.email

    @property
    def is_buyer(self):
        """Everyone is a buyer (can always purchase)."""
        return True

    def save(self, *args, **kwargs):
        """Override save to ensure email is lowercase."""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)
