import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import utils
import constants


def _register_payload(test_user):
    return {
        "phone_number": test_user["phone_number"],
        "password": test_user["password"],
        "first_name": test_user["first_name"],
        "last_name": test_user["last_name"],
    }


def _complete_registration(client, email, password="p455w0rd"):
    r = client.post(f"{constants.BASE_URL}/auth/register/request-otp", json={"email": email})
    assert r.status_code == 200, f"request-otp failed: {r.text}"
    verify_token = r.json()["token"]

    headers = {"Authorization": f"Bearer {verify_token}"}
    r = client.post(f"{constants.BASE_URL}/auth/register/verify-otp", json={"code": constants.OTP_CODE}, headers=headers)
    assert r.status_code == 200, f"verify-otp failed: {r.text}"
    register_token = r.json()["token"]

    headers = {"Authorization": f"Bearer {register_token}"}
    payload = {
        "phone_number": utils.random_phone(),
        "password": password,
        "first_name": "Name",
        "last_name": "Surname",
    }
    r = client.post(f"{constants.BASE_URL}/auth/register", json=payload, headers=headers)
    assert r.status_code == 200, f"register failed: {r.text}"
    return r.json()


@pytest.mark.order(1)
class TestAUTH:
    def test_request_otp(self, client, test_user):
        r = client.post(f"{constants.BASE_URL}/auth/register/request-otp", json={"email": test_user["email"]})
        assert r.status_code == 200, f"Failed to request OTP: {r.text}"

        verify_token = r.json().get("token")
        assert verify_token, f"request-otp did not return a verify token: {r.text}"
        test_user["verify_token"] = verify_token


    def test_verify_otp(self, client, test_user):
        headers = {"Authorization": f"Bearer {test_user['verify_token']}"}
        r = client.post(f"{constants.BASE_URL}/auth/register/verify-otp", json={"code": constants.OTP_CODE}, headers=headers)
        assert r.status_code == 200, f"Failed to verify OTP: {r.text}"

        register_token = r.json().get("token")
        assert register_token, f"verify-otp did not return a registration token: {r.text}"
        test_user["register_token"] = register_token


    def test_register(self, client, test_user):
        headers = {"Authorization": f"Bearer {test_user['register_token']}"}
        r = client.post(f"{constants.BASE_URL}/auth/register", json=_register_payload(test_user), headers=headers)
        assert r.status_code == 200, f"Registration failed: {r.text}"

        body = r.json()
        assert body.get("access_token") and body.get("refresh_token"), f"Registration did not return tokens: {r.text}"
        test_user["access_token"] = body["access_token"]
        test_user["refresh_token"] = body["refresh_token"]


    def test_logout(self, client, test_user):
        r = client.post(f"{constants.BASE_URL}/auth/logout", json={"refresh_token": test_user["refresh_token"]})
        assert r.status_code == 200, f"Logout failed: {r.text}"

        r = client.post(f"{constants.BASE_URL}/auth/refresh", json={"refresh_token": test_user["refresh_token"]})
        assert r.status_code == 401, f"Refresh token should be revoked after logout: {r.text}"


    def test_reset(self, client, test_user):
        r = client.post(f"{constants.BASE_URL}/auth/forgot-password", json={"email": test_user["email"]})
        assert r.status_code == 200, f"Reset request failed: {r.text}"

        verify_token = r.json().get("token")
        assert verify_token, f"Request did not return a verification token: {r.text}"

        headers = {"Authorization": f"Bearer {verify_token}"}
        r = client.post(f"{constants.BASE_URL}/auth/verify-reset-token", json={"code": constants.OTP_CODE}, headers=headers)
        assert r.status_code == 200, f"Code is invalid: {r.text}"

        reset_token = r.json().get("token")
        assert reset_token, f"Request did not return a reset token: {r.text}"

        new_password = test_user["password"] + "2"
        test_user["password"] = new_password

        headers = {"Authorization": f"Bearer {reset_token}"}
        r = client.patch(f"{constants.BASE_URL}/auth/reset-password", json={"new_password": new_password}, headers=headers)
        assert r.status_code == 200, f"Reset confirm failed: {r.text}"

        body = r.json()
        assert body.get("access_token") and body.get("refresh_token"), f"Request did not return access: {r.text}"
        test_user["access_token"] = body["access_token"]
        test_user["refresh_token"] = body["refresh_token"]


    def test_login(self, client, test_user):
        r = client.post(f"{constants.BASE_URL}/auth/login", json={"email": test_user["email"], "password": test_user["password"]})
        assert r.status_code == 200, f"Login request failed: {r.text}"

        body = r.json()
        assert body.get("access_token") and body.get("refresh_token"), f"Login did not return access: {r.text}"


@pytest.mark.order(2)
class TestRegistrationValidation:
    def test_request_otp_duplicate_email(self, client):
        email = utils.random_email()
        _complete_registration(client, email)

        r = client.post(f"{constants.BASE_URL}/auth/register/request-otp", json={"email": email})
        assert r.status_code == 409, f"Duplicate email should be rejected: {r.text}"


    def test_verify_otp_wrong_code(self, client):
        email = utils.random_email()
        r = client.post(f"{constants.BASE_URL}/auth/register/request-otp", json={"email": email})
        assert r.status_code == 200, f"request-otp failed: {r.text}"
        verify_token = r.json()["token"]

        headers = {"Authorization": f"Bearer {verify_token}"}
        r = client.post(f"{constants.BASE_URL}/auth/register/verify-otp", json={"code": "000000"}, headers=headers)
        assert r.status_code == 400, f"Wrong code should be rejected: {r.text}"


    def test_register_without_token_rejected(self, client):
        payload = {
            "phone_number": utils.random_phone(),
            "password": "p455w0rd",
            "first_name": "Name",
            "last_name": "Surname",
        }
        r = client.post(f"{constants.BASE_URL}/auth/register", json=payload)
        assert r.status_code == 401, f"Registration without a token should be rejected: {r.text}"


    def _obtain_register_token(self, client):
        email = utils.random_email()
        r = client.post(f"{constants.BASE_URL}/auth/register/request-otp", json={"email": email})
        assert r.status_code == 200, f"request-otp failed: {r.text}"
        verify_token = r.json()["token"]

        headers = {"Authorization": f"Bearer {verify_token}"}
        r = client.post(f"{constants.BASE_URL}/auth/register/verify-otp", json={"code": constants.OTP_CODE}, headers=headers)
        assert r.status_code == 200, f"verify-otp failed: {r.text}"
        return r.json()["token"]


    def test_register_rejects_short_password(self, client):
        register_token = self._obtain_register_token(client)
        payload = {
            "phone_number": utils.random_phone(),
            "password": "ab",
            "first_name": "Name",
            "last_name": "Surname",
        }
        headers = {"Authorization": f"Bearer {register_token}"}
        r = client.post(f"{constants.BASE_URL}/auth/register", json=payload, headers=headers)
        assert r.status_code == 422, f"Short password should be rejected: {r.text}"


    def test_register_rejects_missing_password(self, client):
        register_token = self._obtain_register_token(client)
        payload = {
            "phone_number": utils.random_phone(),
            "first_name": "Name",
            "last_name": "Surname",
        }
        headers = {"Authorization": f"Bearer {register_token}"}
        r = client.post(f"{constants.BASE_URL}/auth/register", json=payload, headers=headers)
        assert r.status_code == 422, f"Missing password should be rejected: {r.text}"


    def test_rate_limiting(self, client):
        email = utils.random_email()
        for _ in range(constants.RATE_LIMIT_THRESHOLD):
            r = client.post(f"{constants.BASE_URL}/auth/register/request-otp", json={"email": email})
            assert r.status_code == 200, f"request-otp failed: {r.text}"

        r = client.post(f"{constants.BASE_URL}/auth/register/request-otp", json={"email": email})
        assert r.status_code == 429, f"Rate limiting should be enforced: {r.text}"