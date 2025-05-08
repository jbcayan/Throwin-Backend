"""Serializer for FC/Glow/Sales agents."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from accounts.choices import UserKind
from accounts.models import UserProfile
from accounts.rest.serializers.user_registration import validate_password_complexity
from accounts.utils import (
    generate_admin_new_account_activation_url,
    generate_admin_account_activation_url
)
from accounts.tasks import send_mail_task

from payment_service.bank_details.bank_details_model import BankAccount

from store.models import Restaurant, RestaurantUser

User = get_user_model()


class FcGlowAgentAccountDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for representing FC/Glow account details.
    """
    company_name = serializers.CharField(source="profile.company_name")
    address = serializers.CharField(source="profile.address")
    corporate_number = serializers.CharField(source="profile.corporate_number")
    invoice_number = serializers.CharField(source="profile.invoice_number")
    agency_code = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "phone_number",
            "company_name",
            "address",
            "corporate_number",
            "invoice_number",
            "agency_code",
        ]

    def get_agency_code(self, obj) -> str or None:
        # Check if the user is a Sales Agent and return the agency_code
        if obj.kind == UserKind.SALES_AGENT:
            return obj.profile.agency_code
        return None



class BankAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for representing bank account details.
    """
    class Meta:
        model = BankAccount
        fields = [
            "bank_name",
            "bank_code",
            "branch_name",
            "branch_code",
            "account_number",
            "account_type",
            "account_holder_name",
            "is_active",
        ]

class OrganizationCreateSerializer(serializers.Serializer):
    """
    Serializer to create an organization, its restaurant, owner, and bank account.
    Ensures atomicity and validates uniqueness of key fields.
    """

    company_name = serializers.CharField(max_length=100)
    address = serializers.CharField(max_length=255, required=False)
    agency_code = serializers.CharField(max_length=20, required=False)
    post_code = serializers.CharField(max_length=10)
    industry = serializers.CharField(max_length=100)
    invoice_number = serializers.CharField(max_length=100, required=False)
    corporate_number = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
    owner_name = serializers.CharField(max_length=100)
    telephone_number = serializers.CharField(max_length=15)
    email = serializers.EmailField()
    bank_name = serializers.CharField(max_length=100)
    branch_name = serializers.CharField(max_length=100)
    account_type = serializers.ChoiceField(choices=BankAccount.ACCOUNT_TYPE_CHOICES)
    account_number = serializers.CharField(max_length=16)
    account_holder_name = serializers.CharField(max_length=100)

    class Meta:
        fields = [
            "company_name", "address", "agency_code", "post_code",
            "industry", "invoice_number", "corporate_number", "owner_name",
            "telephone_number", "email", "bank_name", "branch_name",
            "account_type", "account_number", "account_holder_name",
        ]

    def validate(self, attrs):
        """
        Perform serializer-level validation for unique constraints.
        """
        email = attrs.get("email")
        phone = attrs.get("telephone_number")
        invoice = attrs.get("invoice_number")
        corporate = attrs.get("corporate_number")

        if User.objects.filter(email=email).exists():
            raise ValidationError({"email": "Email already exists."})
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError({"telephone_number": "Phone number already exists."})
        if invoice and UserProfile.objects.filter(invoice_number=invoice).exists():
            raise ValidationError({"invoice_number": "Invoice number already exists."})
        if corporate and UserProfile.objects.filter(corporate_number=corporate).exists():
            raise ValidationError({"corporate_number": "Corporate number already exists."})

        return attrs

    def _get_sales_agent(self, agency_code):
        """
        Retrieve sales agent user by agency code.
        """
        if not agency_code:
            return None
        try:
            return UserProfile.objects.get(agency_code=agency_code).user
        except ObjectDoesNotExist:
            raise ValidationError({"sales_agent": "Invalid agency code."})

    def _create_owner(self, validated_data):
        """
        Create a restaurant owner user and update their profile.
        """
        owner = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["owner_name"],
            phone_number=validated_data["telephone_number"],
            kind=UserKind.RESTAURANT_OWNER,
            is_active=False,
        )
        profile = owner.profile
        profile.post_code = validated_data["post_code"]
        profile.company_name = validated_data["company_name"]
        profile.invoice_number = validated_data.get("invoice_number")
        profile.corporate_number = validated_data.get("corporate_number")
        profile.save(update_fields=["post_code", "company_name", "invoice_number", "corporate_number"])
        return owner

    def _create_restaurant(self, validated_data, owner, user, sales_agent=None):
        """
        Create the restaurant and associated RestaurantUser(s).
        """
        restaurant = Restaurant.objects.create(
            name=validated_data["company_name"],
            restaurant_owner=owner,
            post_code=validated_data["post_code"],
            address=validated_data.get("address"),
            industry=validated_data["industry"],
            invoice_number=validated_data.get("invoice_number"),
            corporate_number=validated_data.get("corporate_number"),
            created_by=user,
            sales_agent=sales_agent,
        )
        RestaurantUser.objects.create(
            restaurant=restaurant,
            user=owner,
            created_by=user,
            role=UserKind.RESTAURANT_OWNER,
        )
        if sales_agent:
            RestaurantUser.objects.get_or_create(
                restaurant=restaurant,
                user=sales_agent,
                defaults={"created_by": user, "role": UserKind.SALES_AGENT},
            )
        return restaurant

    def _create_bank_account(self, validated_data, owner):
        """
        Create a bank account for the owner.
        """
        BankAccount.objects.create(
            user=owner,
            bank_name=validated_data["bank_name"],
            branch_name=validated_data["branch_name"],
            account_type=validated_data["account_type"],
            account_holder_name=validated_data["account_holder_name"],
            account_number=validated_data["account_number"],
            is_active=True,
        )

    def _send_activation_email(self, owner):
        """
        Send activation email to the owner.
        """
        activation_url = generate_admin_new_account_activation_url(owner)
        subject = "Activate Your Account"
        message = f"Please click the following link to set password and activate your account: {activation_url}"
        send_mail_task.delay(subject, message, owner.email)

    @transaction.atomic
    def create(self, validated_data):
        """
        Create an organization, owner, restaurant, and bank account atomically.
        """
        user = self.context["request"].user
        try:
            sales_agent = self._get_sales_agent(validated_data.get("agency_code"))
            owner = self._create_owner(validated_data)
            restaurant = self._create_restaurant(validated_data, owner, user, sales_agent)
            self._create_bank_account(validated_data, owner)
        except IntegrityError as e:
            raise ValidationError(f"Database integrity error: {str(e)}")
        except Exception as e:
            raise ValidationError(f"An error occurred: {str(e)}")

        # Send activation email outside the transaction
        self._send_activation_email(owner)
        return restaurant

    def update(self, instance, validated_data):
        """
        Update the restaurant, owner's profile, and active bank account.
        """
        # Uniqueness checks for invoice and corporate numbers
        invoice = validated_data.get("invoice_number")
        corporate = validated_data.get("corporate_number")
        if invoice and instance.invoice_number != invoice:
            if UserProfile.objects.filter(invoice_number=invoice).exists():
                raise ValidationError({"invoice_number": "Invoice number already exists."})
        if corporate and instance.corporate_number != corporate:
            if UserProfile.objects.filter(corporate_number=corporate).exists():
                raise ValidationError({"corporate_number": "Corporate number already exists."})

        # Update restaurant fields
        for attr in ["company_name", "address", "post_code", "industry", "invoice_number", "corporate_number"]:
            val = validated_data.get(attr)
            if val is not None:
                setattr(instance, "name" if attr == "company_name" else attr, val)

        # Update sales agent if agency code provided
        agency_code = validated_data.get("agency_code")
        if agency_code:
            instance.sales_agent = self._get_sales_agent(agency_code)
        instance.save()

        # Update owner
        owner = instance.restaurant_owner
        new_phone = validated_data.get("telephone_number")
        new_email = validated_data.get("email")
        if new_phone and owner.phone_number != new_phone:
            if User.objects.filter(phone_number=new_phone).exists():
                raise ValidationError({"telephone_number": "Phone number already exists."})
        if new_email and owner.email != new_email:
            if User.objects.filter(email=new_email).exists():
                raise ValidationError({"email": "This email already exists."})
            activation_url = generate_admin_account_activation_url(owner, new_email)
            subject = "Email Change Request"
            message = f"Please click the following link to verify your new email: {activation_url}"
            send_mail_task.delay(subject, message, new_email)

        owner.name = validated_data.get("owner_name", owner.name)
        owner.phone_number = new_phone or owner.phone_number
        owner.save(update_fields=["name", "phone_number", "is_verified"])

        # Update owner's profile
        profile = owner.profile
        for attr in ["post_code", "company_name", "invoice_number", "corporate_number"]:
            val = validated_data.get(attr)
            if val is not None:
                setattr(profile, attr, val)
        profile.save()

        # Update bank account
        bank_account = BankAccount.objects.filter(user=owner, is_active=True).first()
        if bank_account:
            for attr in ["bank_name", "branch_name", "account_type", "account_number", "account_holder_name"]:
                val = validated_data.get(attr)
                if val is not None:
                    setattr(bank_account, attr, val)
            bank_account.save()

        return instance

    def to_representation(self, instance):
        """
        Return key details of the created or updated restaurant.
        """
        return {
            "uid": instance.uid,
            "name": instance.name,
            "restaurant_owner_uid": instance.restaurant_owner.uid,
            "sales_agent_uid": getattr(instance.sales_agent, "uid", None),
            "post_code": instance.post_code,
            "address": instance.address,
            "industry": instance.industry,
            "invoice_number": instance.invoice_number,
            "corporate_number": instance.corporate_number,
        }


class OrganizationListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing organizations.
    Includes key fields for a concise overview.
    """
    owner_name = serializers.CharField(source="restaurant_owner.name")

    class Meta:
        model = Restaurant
        fields = [
            'uid',
            'name',
            'post_code',
            'industry',
            'owner_name'
        ]


class ActivationSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()

    def validate(self, data):
        """ Validate the UID and token, and return the user if valid. """
        try:
            uid = urlsafe_base64_decode(data['uidb64']).decode()
            user = User.objects.get(pk=uid)

            # Decode the token
            access_token = AccessToken(data['token'])
            new_email = access_token.get("new_email")

            # If token is invalid or expired, an exception will be raised
            # No need to manually check the token
        except (TypeError, ValueError, OverflowError, User.DoesNotExist, TokenError) as e:
            raise serializers.ValidationError("Invalid activation link.") from e

        data['user'] = user
        data['new_email'] = new_email
        return data

class ActivationNewUserSerializer(serializers.Serializer):
    uidb64 = serializers.CharField(write_only=True, required=True)
    token = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password, validate_password_complexity],
    )
    confirm_password = serializers.CharField(write_only=True, required=True)


    def validate(self, data):
        """
        Validate the UID and token, and return the user if valid.
        """
        try:
            uid = urlsafe_base64_decode(data['uidb64']).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid activation link.")

        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError("Invalid activation link.")

        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")

        data['user'] = user
        return data


class SalesAgentListCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, updating, and listing Sales Agent accounts.
    Handles agent creation/updates with associated profile and bank account information.
    """
    # Profile Information
    post_code = serializers.CharField(
        max_length=20,
        help_text="Postal code for the agent's company"
    )
    company_name = serializers.CharField(
        max_length=100,
        help_text="Legal name of the agent's company"
    )
    address = serializers.CharField(
        max_length=255,
        help_text="Physical address of the company"
    )
    invoice_number = serializers.CharField(
        max_length=20,
        help_text="Unique identifier for invoicing purposes"
    )
    corporate_number = serializers.CharField(
        max_length=100,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Corporate registration number if available"
    )

    # Bank Account Information
    bank_name = serializers.CharField(
        max_length=100,
        help_text="Name of the bank"
    )
    branch_name = serializers.CharField(
        max_length=100,
        help_text="Branch name of the bank"
    )
    account_type = serializers.CharField(
        max_length=100,
        help_text="Type of bank account (e.g., checking, savings)"
    )
    account_number = serializers.CharField(
        max_length=100,
        help_text="Bank account number"
    )
    account_holder_name = serializers.CharField(
        max_length=100,
        help_text="Name of the account holder"
    )

    class Meta:
        model = User
        fields = [
            "email",
            "name",
            "phone_number",
            "post_code",
            "company_name",
            "address",
            "invoice_number",
            "corporate_number",
            "bank_name",
            "branch_name",
            "account_type",
            "account_number",
            "account_holder_name",
        ]
        extra_kwargs = {
            "email": {
                "required": True,
                "help_text": "Email address for the agent account"
            },
            "name": {
                "required": True,
                "help_text": "Full name of the agent"
            },
            "phone_number": {
                "required": True,
                "help_text": "Contact phone number"
            },
        }

    def validate(self, data):
        """Perform cross-field validation and uniqueness checks."""
        errors = {}
        instance = self.instance  # Will be None for create, existing instance for update

        # Check for existing user with same email or phone
        email = data.get('email')
        phone_number = data.get('phone_number')
        invoice_number = data.get('invoice_number')
        corporate_number = data.get('corporate_number')

        if email and (not instance or instance.email != email):
            if User.objects.filter(email=email).exclude(pk=getattr(instance, 'pk', None)).exists():
                errors['email'] = "This email already exists."

        if phone_number and (not instance or instance.phone_number != phone_number):
            if User.objects.filter(phone_number=phone_number).exclude(pk=getattr(instance, 'pk', None)).exists():
                errors['phone_number'] = "This phone number already exists."

        if invoice_number and (not instance or instance.profile.invoice_number != invoice_number):
            if UserProfile.objects.filter(invoice_number=invoice_number).exclude(
                    user=getattr(instance, 'pk', None)).exists():
                errors['invoice_number'] = "Invoice number already exists."

        if corporate_number and (not instance or instance.profile.corporate_number != corporate_number):
            if UserProfile.objects.filter(corporate_number=corporate_number).exclude(
                    user=getattr(instance, 'pk', None)).exists():
                errors['corporate_number'] = "Corporate number already exists."

        if errors:
            raise serializers.ValidationError(errors)

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Create a new Sales Agent with associated profile and bank account."""
        # Extract profile data
        profile_data = {
            'post_code': validated_data.pop('post_code'),
            'company_name': validated_data.pop('company_name'),
            'address': validated_data.pop('address'),
            'invoice_number': validated_data.pop('invoice_number'),
            'corporate_number': validated_data.pop('corporate_number', None) or None,
        }

        # Extract bank account data
        bank_account_data = {
            'bank_name': validated_data.pop('bank_name'),
            'branch_name': validated_data.pop('branch_name'),
            'account_type': validated_data.pop('account_type'),
            'account_number': validated_data.pop('account_number'),
            'account_holder_name': validated_data.pop('account_holder_name'),
        }

        # Create user (sales agent)
        validated_data.update({
            'kind': UserKind.SALES_AGENT,
            'is_active': False,
        })
        sales_agent = User.objects.create_user(**validated_data)

        # Create profile
        self._create_user_profile(sales_agent, profile_data)

        # Create bank account
        self._create_bank_account(sales_agent, bank_account_data)

        # Send activation email (after transaction completes successfully)
        self._send_activation_email(sales_agent, is_new_account=True)

        return sales_agent

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update an existing Sales Agent and associated profile."""
        # Extract profile data
        profile_data = {
            'post_code': validated_data.pop('post_code', instance.profile.post_code),
            'company_name': validated_data.pop('company_name', instance.profile.company_name),
            'address': validated_data.pop('address', instance.profile.address),
            'invoice_number': validated_data.pop('invoice_number', instance.profile.invoice_number),
            'corporate_number': validated_data.pop('corporate_number', instance.profile.corporate_number) or None,
        }

        # Handle email change
        new_email = validated_data.get('email', instance.email)
        if new_email != instance.email:
            self._handle_email_change(instance, new_email)

        # Update user fields
        instance.name = validated_data.get('name', instance.name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save(update_fields=['name', 'phone_number', 'email', 'is_verified'])

        # Update profile
        self._update_user_profile(instance, profile_data)

        return instance

    def _create_user_profile(self, user, profile_data):
        """Create or update user profile with the given data."""
        profile = user.profile
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()

    def _update_user_profile(self, user, profile_data):
        """Update existing user profile with the given data."""
        profile = user.profile
        update_fields = []

        for field, value in profile_data.items():
            if getattr(profile, field) != value:
                setattr(profile, field, value)
                update_fields.append(field)

        if update_fields:
            profile.save(update_fields=update_fields)

    def _create_bank_account(self, user, bank_account_data):
        """Create a bank account for the user."""
        BankAccount.objects.create(
            user=user,
            is_active=True,
            **bank_account_data
        )

    def _handle_email_change(self, user, new_email):
        """Handle email change including verification flow."""
        user.email = new_email
        user.is_verified = False
        self._send_activation_email(user, is_new_account=False)

    def _send_activation_email(self, user, is_new_account=True):
        """Send appropriate activation email based on context."""
        activation_url = generate_admin_new_account_activation_url(user)

        if is_new_account:
            subject = "Activate Your Sales Agent Account"
            message = (
                f"Dear {user.name},\n\n"
                f"Your sales agent account has been created. "
                f"Please click the following link to set your password and activate your account:\n\n"
                f"{activation_url}\n\n"
                f"Thank you,\n"
                f"The Management Team"
            )
        else:
            subject = "Verify Your New Email Address"
            message = (
                f"Dear {user.name},\n\n"
                f"You have requested to change your email address. "
                f"Please click the following link to verify your new email address:\n\n"
                f"{activation_url}\n\n"
                f"If you didn't request this change, please contact support immediately.\n\n"
                f"Thank you,\n"
                f"The Management Team"
            )

        transaction.on_commit(
            lambda: send_mail_task.delay(subject, message, user.email)
        )

    def to_representation(self, instance):
        bank_accounts = instance.bank_accounts
        return {
            "uid": instance.uid,
            "name": instance.name,
            "email": instance.email,
            "agency_code": instance.profile.agency_code,
            "phone_number": instance.phone_number,
            "password_status": "password set" if instance.is_active else "password not set",
            "post_code": instance.profile.post_code,
            "company_name": instance.profile.company_name,
            "address": instance.profile.address,
            "invoice_number": instance.profile.invoice_number,
            "corporate_number": instance.profile.corporate_number,
            "bank_accounts": BankAccountSerializer(bank_accounts, many=True).data,
        }


class AdminsChangeEmailRequestSerializer(serializers.Serializer):
    """
    Serializer to request an email change for an admin user.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        # Authenticate user with provided password
        if not user.check_password(data['password']):
            raise serializers.ValidationError({
                "detail": "Incorrect password."
            })

        if user.email == data['email']:
            raise serializers.ValidationError({"email": "New email is the same as the current email."})

        # Check if the new email is already in use
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})

        return data

    def save(self):
        user = self.context['request'].user
        new_email = self.validated_data['email']

        # Generate activation link
        activation_url = generate_admin_account_activation_url(user, new_email)

        # Send activation email
        subject = "Email Change Request"
        message = f"Please click the following link to verify your new email: {activation_url}"
        send_mail_task.delay(subject, message, new_email)


class ChangeAdminNameSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)

    def create(self, validated_data):
        name = validated_data.pop("name", None)
        user = self.context["request"].user
        user.name = name
        user.save(
            update_fields=["name"]
        )
        return user