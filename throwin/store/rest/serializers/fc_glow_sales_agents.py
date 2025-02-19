"""Serializer for FC/Glow/Sales agents."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

from rest_framework import serializers

from accounts.choices import UserKind
from accounts.models import UserProfile
from accounts.utils import generate_admin_email_activation_url
from accounts.tasks import send_mail_task

from payment_service.bank_details.bank_details_model import BankAccount

from store.models import Restaurant

User = get_user_model()


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

    def validate_agency_code(self, value):
        """
        Validate the agency code and return the associated sales agent.
        This method is called when agency_code has a value.
        """
        try:
            sales_agent = UserProfile.objects.get(agency_code=value).user
            return sales_agent
        except ObjectDoesNotExist:
            raise serializers.ValidationError("Invalid agency code provided.")

    @transaction.atomic
    def create(self, validated_data):
        """
        Create a restaurant, restaurant owner, and bank account, then return
        the created Restaurant instance.
        """
        user = self.context["request"].user

        try:
            # Create the restaurant owner account
            owner = User.objects.create_user(
                email=validated_data.get("email"),
                name=validated_data.get("owner_name"),
                phone_number=validated_data.get("telephone_number"),
                kind=UserKind.RESTAURANT_OWNER,
            )
            owner.set_password(validated_data.get("telephone_number"))
            owner.save()

            # Update user profile
            profile = owner.profile
            profile.post_code = validated_data.get("post_code")
            profile.company_name = validated_data.get("company_name")
            profile.invoice_number = validated_data.get("invoice_number")
            profile.corporate_number = validated_data.get("corporate_number")
            profile.save(update_fields=[
                'post_code', 'company_name', 'invoice_number', 'corporate_number',
            ])

            # Conditionally validate and retrieve sales agent if provided
            sales_agent = validated_data.get("agency_code")
            if sales_agent:
                sales_agent = self.validate_agency_code(sales_agent) if sales_agent else None

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

            if sales_agent:
                restaurant.sales_agent = sales_agent
                restaurant.save(update_fields=["sales_agent"])

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

            # Send activation email
            activation_url = generate_admin_email_activation_url(owner)
            subject = "Activate Your Account"
            message = f"Please click the following link to activate your account: {activation_url}"
            send_mail_task.delay(subject, message, owner.email)

            return restaurant

        except Exception as e:
            # Rollback transaction and raise error
            transaction.set_rollback(True)
            raise serializers.ValidationError(f"An error occurred: {str(e)}")

    def update(self, instance, validated_data):
        """
        Update the Restaurant instance along with its associated owner's profile and active bank account.
        Fields updated:
          - Restaurant: company name, address, post code, industry, invoice number, corporate number, and sales agent if agency_code provided.
          - Owner's profile: post code, company name, invoice number, and corporate number.
          - Active bank account: bank name, branch name, account type, account number, and account holder name.
        """
        # Update restaurant fields
        instance.name = validated_data.get("company_name", instance.name)
        instance.address = validated_data.get("address", instance.address)
        instance.post_code = validated_data.get("post_code", instance.post_code)
        instance.industry = validated_data.get("industry", instance.industry)
        instance.invoice_number = validated_data.get("invoice_number", instance.invoice_number)
        instance.corporate_number = validated_data.get("corporate_number", instance.corporate_number)
        instance.save()

        # Update owner fields
        owner = instance.restaurant_owner

        # Update owner's email and name
        new_email = validated_data.get("email", owner.email)
        if owner.email != new_email:
            owner.email = new_email
            owner.is_verified = False  # Deactivate until email is confirmed
            activation_url = generate_admin_email_activation_url(owner)
            subject = "Activate Your Account"
            message = f"Please click the following link to activate your account: {activation_url}"
            send_mail_task.delay(subject, message, new_email)

        owner.name = validated_data.get("owner_name", owner.name)
        owner.save(update_fields=["email", "name", "is_verified"])

        profile = owner.profile
        profile.post_code = validated_data.get("post_code", profile.post_code)
        profile.company_name = validated_data.get("company_name", profile.company_name)
        profile.invoice_number = validated_data.get("invoice_number", profile.invoice_number)
        profile.corporate_number = validated_data.get("corporate_number", profile.corporate_number)
        profile.save(update_fields=["post_code", "company_name", "invoice_number", "corporate_number"])

        # Update sales agent if agency_code is provided
        agency_code = validated_data.get("agency_code")
        if agency_code:
            sales_agent = self.validate_agency_code(agency_code)
            instance.sales_agent = sales_agent
            instance.save(update_fields=["sales_agent"])

        # Update active bank account details if available
        bank_account = BankAccount.objects.filter(user=owner, is_active=True).first()
        if bank_account:
            bank_account.bank_name = validated_data.get("bank_name", bank_account.bank_name)
            bank_account.branch_name = validated_data.get("branch_name", bank_account.branch_name)
            bank_account.account_type = validated_data.get("account_type", bank_account.account_type)
            bank_account.account_number = validated_data.get("account_number", bank_account.account_number)
            bank_account.account_holder_name = validated_data.get("account_holder_name",
                                                                  bank_account.account_holder_name)
            bank_account.save(
                update_fields=["bank_name", "branch_name", "account_type", "account_number", "account_holder_name"])

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

        data['user'] = user
        return data



