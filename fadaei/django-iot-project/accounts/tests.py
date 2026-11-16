
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AccountAPITests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="account_test",
            email="account@test.com",
            password="TestPassword123!"
        )

    def test_authenticated_user_can_view_own_profile(self):
        token_response = self.client.post(
            "/api/token/",
            {
                "username": "account_test",
                "password": "TestPassword123!"
            },
            format="json"
        )

        self.assertEqual(token_response.status_code, 200)

        access_token = token_response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "account_test")

    def test_unauthenticated_user_cannot_view_profile(self):
        response = self.client.get("/api/accounts/me/")

        self.assertEqual(response.status_code, 401)
