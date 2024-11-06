from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, Like, TemporaryUser
from accounts.choices import UserKind
from django.core.exceptions import ValidationError


User = get_user_model()

class UserModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            name="Test User"
        )
        self.staff_user = User.objects.create_user(
            email="staffuser@example.com",
            password="password123",
            name="Staff User",
            kind=UserKind.RESTAURANT_STUFF
        )
        self.consumer_user = User.objects.create_user(
            email="consumer@example.com",
            password="password123",
            name="Consumer User",
            kind=UserKind.CONSUMER
        )

    def test_user_creation(self):
        self.assertIsNotNone(self.user.id)
        self.assertTrue(self.user.check_password("password123"))

    def test_user_str(self):
        self.assertEqual(str(self.user), "testuser@example.com")

    def test_user_profile_creation(self):
        profile = UserProfile.objects.create(user=self.user, introduction="Hello!")
        self.assertIsNotNone(profile.id)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.introduction, "Hello!")

    def test_like_functionality(self):
        like = Like.objects.create(consumer=self.consumer_user, staff=self.staff_user)
        self.assertIsNotNone(like.id)
        self.assertEqual(like.consumer, self.consumer_user)
        self.assertEqual(like.staff, self.staff_user)

        with self.assertRaises(Exception):
            Like.objects.create(consumer=self.consumer_user, staff=self.staff_user)  # Should raise due to unique_together

    def test_temporary_user_creation(self):
        temp_user = TemporaryUser.objects.create(
            email="tempuser@example.com",
            password="temp_password123"
        )
        self.assertIsNotNone(temp_user.id)
        self.assertEqual(temp_user.email, "tempuser@example.com")
        self.assertTrue(temp_user.token)  # Token should be generated
        self.assertEqual(temp_user.kind, UserKind.UNDEFINED)

    def test_temporary_user_str(self):
        temp_user = TemporaryUser.objects.create(
            email="tempuser2@example.com",
            password="temp_password123"
        )
        self.assertEqual(str(temp_user), "tempuser2@example.com")
    
    def test_email_uniqueness(self):
        user1 = User.objects.create_user(
            email="unique@example.com",
            password="password123",
            name="Unique User"
        )
        with self.assertRaises(ValidationError):
            user2 = User(email="unique@example.com", password="another_password")
            user2.full_clean()


class UserProfileTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            name="Test User"
        )
        self.profile = UserProfile.objects.create(user=self.user, introduction="Hello!")

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "Profile of Test User")

    def test_profile_address(self):
        self.profile.address = "123 Main St"
        self.profile.save()
        self.assertEqual(self.profile.address, "123 Main St")

    def test_profile_score(self):
        self.profile.total_score = 10
        self.profile.save()
        self.assertEqual(self.profile.total_score, 10)

