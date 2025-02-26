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
    Serializer to create an organization along with its associated restaurant, owner account, and bank account.
    Validates the agency code to retrieve a sales agent and updates the owner's user profile.
    Executes the creation process within an atomic transaction to ensure data integrity.
    """
    company_name = serializers.CharField(max_length=100)
    address = serializers.CharField(max_length=255, required=False)
    agency_code = serializers.CharField(max_length=20, required=False)
    post_code = serializers.CharField(max_length=10)
    industry = serializers.CharField(max_length=100)
    invoice_number = serializers.CharField(max_length=100, required=False)
    corporate_number = serializers.CharField(max_length=100, required=False)
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

    @transaction.atomic
    def create(self, validated_data):
        """Create a restaurant, restaurant owner, and bank account, then return the created Restaurant instance."""
        user = self.context["request"].user
        sales_agent = None

        try:
            # Check for existing email and phone number
            if User.objects.filter(email=validated_data.get("email")).exists():
                raise ValidationError({"email": "Email already exists."})

            if User.objects.filter(phone_number=validated_data.get("telephone_number")).exists():
                raise ValidationError({"telephone_number": "Phone number already exists."})

            if UserProfile.objects.filter(invoice_number=validated_data.get("invoice_number")).exists():
                raise ValidationError({"invoice_number": "Invoice number already exists."})

            if UserProfile.objects.filter(corporate_number=validated_data.get("corporate_number")).exists():
                raise ValidationError({"corporate_number": "Corporate number already exists."})

            if validated_data.get("agency_code"):
                try:
                    sales_agent = UserProfile.objects.get(agency_code=validated_data.get("agency_code")).user
                except ObjectDoesNotExist:
                    raise ValidationError({"sales_agent": "Invalid agency code."})

            # Create owner
            owner = User.objects.create_user(
                email=validated_data.get("email"),
                name=validated_data.get("owner_name"),
                phone_number=validated_data.get("telephone_number"),
                kind=UserKind.RESTAURANT_OWNER,
                is_active=False,
            )

            # Update user profile
            profile = owner.profile
            profile_fields = {
                'post_code': validated_data.get("post_code"),
                'company_name': validated_data.get("company_name"),
                'invoice_number': validated_data.get("invoice_number"),
                'corporate_number': validated_data.get("corporate_number"),
            }
            for field, value in profile_fields.items():
                setattr(profile, field, value)
            profile.save(update_fields=profile_fields.keys())

            # Create the restaurant
            restaurant = Restaurant.objects.create(
                name=validated_data.get("company_name"),
                restaurant_owner=owner,
                post_code=validated_data.get("post_code"),
                address=validated_data.get("address"),
                industry=validated_data.get("industry"),
                invoice_number=validated_data.get("invoice_number"),
                corporate_number=validated_data.get("corporate_number"),
                created_by=user,
            )

            restaurant_user = RestaurantUser.objects.create(
                restaurant=restaurant,
                user=owner,
                created_by=user,
                role=UserKind.RESTAURANT_OWNER,
            )

            if sales_agent:
                restaurant.sales_agent = sales_agent
                restaurant.save(update_fields=["sales_agent"])

                restaurant_user_sales = RestaurantUser.objects.create(
                    restaurant=restaurant,
                    user=sales_agent,
                    created_by=user,
                    role=UserKind.SALES_AGENT,
                )

            # Create bank account for the owner
            BankAccount.objects.create(
                user=owner,
                bank_name=validated_data.get("bank_name"),
                branch_name=validated_data.get("branch_name"),
                account_type=validated_data.get("account_type"),
                account_holder_name=validated_data.get("account_holder_name"),
                account_number=validated_data.get("account_number"),
                is_active=True,
            )

            # Send activation email outside the transaction
            # Send activation email
            activation_url = generate_admin_new_account_activation_url(owner)
            subject = "Activate Your Account"
            message = f"Please click the following link to set password and activate your account: {activation_url}"
            send_mail_task.delay(subject, message, owner.email)

            return restaurant

        except IntegrityError as e:
            # Rollback and raise a meaningful error
            raise ValidationError(f"Database integrity error: {str(e)}")
        except Exception as e:
            # Rollback and raise a general error
            raise ValidationError(f"An error occurred: {str(e)}")

    def update(self, instance, validated_data):
        """ Update the Restaurant instance along with its associated owner's profile and active bank account. """

        # Check if invoice_number is provided and perform uniqueness check
        new_invoice_number = validated_data.get("invoice_number")
        if new_invoice_number and instance.invoice_number != new_invoice_number:
            if UserProfile.objects.filter(invoice_number=new_invoice_number).exists():
                raise ValidationError({"invoice_number": "Invoice number already exists."})

        # Check if corporate_number is provided and perform uniqueness check
        new_corporate_number = validated_data.get("corporate_number")
        if new_corporate_number and instance.corporate_number != new_corporate_number:
            if UserProfile.objects.filter(corporate_number=new_corporate_number).exists():
                raise ValidationError({"corporate_number": "Corporate number already exists."})

        # Update restaurant fields
        instance.name = validated_data.get("company_name", instance.name)
        instance.address = validated_data.get("address", instance.address)
        instance.post_code = validated_data.get("post_code", instance.post_code)
        instance.industry = validated_data.get("industry", instance.industry)
        instance.invoice_number = new_invoice_number or instance.invoice_number
        instance.corporate_number = new_corporate_number or instance.corporate_number

        new_agency_code = validated_data.get("agency_code")
        if new_agency_code:
            try:
                sales_agent = UserProfile.objects.get(agency_code=new_agency_code).user
                instance.sales_agent = sales_agent
            except ObjectDoesNotExist:
                raise ValidationError({"sales_agent": "Invalid agency code."})

        instance.save(update_fields=[
            "name", "address", "post_code", "industry", "invoice_number", "corporate_number", "sales_agent"
        ])

        # Update owner fields
        owner = instance.restaurant_owner
        # Check if telephone_number is provided and perform uniqueness check
        new_telephone_number = validated_data.get("telephone_number")
        if new_telephone_number and owner.phone_number != new_telephone_number:
            if User.objects.filter(phone_number=new_telephone_number).exists():
                raise serializers.ValidationError({"telephone_number": "Phone number already exists."})

        # Update owner's email and name
        new_email = validated_data.get("email", owner.email)
        if owner.email != new_email:
            if User.objects.filter(email=new_email).exists():
                raise serializers.ValidationError({"email": "This email already exists."})
            activation_url = generate_admin_account_activation_url(owner, new_email)
            subject = "Email Change Request"
            message = f"Please click the following link to verify your new email: {activation_url}"
            send_mail_task.delay(subject, message, new_email)

        owner.name = validated_data.get("owner_name", owner.name)
        owner.phone_number = validated_data.get("telephone_number", owner.phone_number)
        owner.save(update_fields=["name", "phone_number", "is_verified"])

        profile = owner.profile
        profile.post_code = validated_data.get("post_code", profile.post_code)
        profile.company_name = validated_data.get("company_name", profile.company_name)
        profile.invoice_number = new_invoice_number or profile.invoice_number
        profile.corporate_number = new_corporate_number or profile.corporate_number
        profile.save(update_fields=["post_code", "company_name", "invoice_number", "corporate_number"])

        # Update active bank account details if available
        bank_account = BankAccount.objects.filter(user=owner, is_active=True).first()
        if bank_account:
            bank_account.bank_name = validated_data.get("bank_name", bank_account.bank_name)
            bank_account.branch_name = validated_data.get("branch_name", bank_account.branch_name)
            bank_account.account_type = validated_data.get("account_type", bank_account.account_type)
            bank_account.account_number = validated_data.get("account_number", bank_account.account_number)
            bank_account.account_holder_name = validated_data.get("account_holder_name",
                                                                  bank_account.account_holder_name)
            bank_account.save(update_fields=[
                "bank_name", "branch_name", "account_type", "account_number", "account_holder_name"
            ])

        return instance

    def to_representation(self, instance):
        """
        Custom representation after creation of the restaurant.
        This method returns key details of the created restaurant.
        """
        return {
            "uid": instance.uid,
            "name": instance.name,
            "restaurant_owner_uid": instance.restaurant_owner.uid,
            "sales_agent_uid": instance.sales_agent.uid if instance.sales_agent else None,
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
    owner_name = serializers.CharField(source="""restaurant_owner.name""")

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
    Serializer for creating a sales agent.
    """
    post_code = serializers.CharField(max_length=20)
    company_name = serializers.CharField(max_length=100)
    address = serializers.CharField(max_length=255)
    invoice_number = serializers.CharField(max_length=20)
    corporate_number = serializers.CharField(max_length=100)

    bank_name = serializers.CharField(max_length=100)
    branch_name = serializers.CharField(max_length=100)
    account_type = serializers.CharField(max_length=100)
    account_number = serializers.CharField(max_length=100)
    account_holder_name = serializers.CharField(max_length=100)

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
            "email": {"required": True},
            "name": {"required": True},
            "phone_number": {"required": True},
        }


    @transaction.atomic
    def create(self, validated_data):
        post_code = validated_data.pop("post_code")
        company_name = validated_data.pop("company_name")
        address = validated_data.pop("address")
        invoice_number = validated_data.pop("invoice_number")
        corporate_number = validated_data.pop("corporate_number")

        bank_name = validated_data.pop("bank_name")
        branch_name = validated_data.pop("branch_name")
        account_type = validated_data.pop("account_type")
        account_number = validated_data.pop("account_number")
        account_holder_name = validated_data.pop("account_holder_name")

        name = validated_data.pop("name")
        phone_number = validated_data.pop("phone_number")
        email = validated_data.pop("email")

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email already exists."})

        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({"phone_number": "This phone number already exists."})

        if UserProfile.objects.filter(invoice_number=invoice_number).exists():
            raise serializers.ValidationError({"invoice_number": "Invoice number already exists."})

        if UserProfile.objects.filter(corporate_number=corporate_number).exists():
            raise serializers.ValidationError({"corporate_number": "Corporate number already exists."})

        sales_agent = User.objects.create_user(
            name=name,
            phone_number=phone_number,
            email=email,
            kind=UserKind.SALES_AGENT,
            is_active=False,
        )

        # Send activation email
        activation_url = generate_admin_new_account_activation_url(sales_agent)
        subject = "Activate Your Account"
        message = f"Please click the following link to set password and activate your account: {activation_url}"
        send_mail_task.delay(subject, message, sales_agent.email)

        profile = sales_agent.profile
        profile.post_code = post_code
        profile.company_name = company_name
        profile.address = address
        profile.invoice_number = invoice_number
        profile.corporate_number = corporate_number
        profile.save()

        bank_account = BankAccount.objects.create(
            user=sales_agent,
            bank_name=bank_name,
            branch_name=branch_name,
            account_type=account_type,
            account_number=account_number,
            account_holder_name=account_holder_name,
            is_active=True
        )

        return sales_agent

    @transaction.atomic
    def update(self, instance, validated_data):
        post_code = validated_data.pop("post_code", instance.profile.post_code)
        company_name = validated_data.pop("company_name", instance.profile.company_name)
        address = validated_data.pop("address", instance.profile.address)
        invoice_number = validated_data.pop("invoice_number", instance.profile.invoice_number)
        corporate_number = validated_data.pop("corporate_number", instance.profile.corporate_number)

        name = validated_data.pop("name", instance.name)
        email = validated_data.pop("email", instance.email)
        phone_number = validated_data.pop("phone_number", instance.phone_number)

        if (instance.phone_number != phone_number and
                User.objects.filter(phone_number=phone_number).exists()):
            raise serializers.ValidationError("This phone number already exists")

        if instance.email != email:
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError("This email already exists")

            instance.email = email
            instance.is_verified = False  # Deactivate until email is confirmed
            activation_url = generate_admin_new_account_activation_url(instance)
            subject = "Activate Your Account"
            message = f"Please click the following link to activate your account with new email: {activation_url}"
            send_mail_task.delay(subject, message, email)

        instance.name = name
        instance.phone_number = phone_number
        instance.save(
            update_fields=[
                "email",
                "name",
                "phone_number",
                "is_verified"
            ]
        )

        profile = instance.profile
        profile.post_code = post_code
        profile.company_name = company_name
        profile.address = address
        profile.invoice_number = invoice_number
        profile.corporate_number = corporate_number
        profile.save(
            update_fields=[
                "post_code",
                "company_name",
                "address",
                "invoice_number",
                "corporate_number",
            ]
        )

        return instance

    def to_representation(self, instance):
        bank_accounts = instance.bank_accounts
        return {
            "uid": instance.uid,
            "name": instance.name,
            "email": instance.email,
            "agency_code": instance.profile.agency_code,
            "phone_number": instance.phone_number,
            "post_code": instance.profile.post_code,
            "company_name": instance.profile.company_name,
            "address": instance.profile.address,
            "invoice_number": instance.profile.invoice_number,
            "corporate_number": instance.profile.corporate_number,
            "bank_accounts": BankAccountSerializer(bank_accounts, many=True).data
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