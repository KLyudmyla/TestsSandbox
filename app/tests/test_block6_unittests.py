import unittest
from unittest import mock
from unittest.mock import MagicMock
import requests


class ThirdPartyServiceError(Exception):
    """Raised when an external API integration fails or returns an unhealthy status."""
    pass

# =====================================================================
# BLOCK 6: Network Mocking Practice (Third-Party HTTP Requests)
# ---------------------------------------------------------------------
# Testing Guidance:
# - CRITICAL: Use 'unittest.mock.patch' to isolate the networking layer.
# - Real HTTP calls must be completely blocked during unit test execution.
# - Use 'MagicMock' to simulate HTTP 200, 404, or 500 status codes and raw JSON responses.
# - Use 'side_effect=requests.RequestException' to ensure proper handling of network timeout spikes.
# =====================================================================

class WeatherAlertService:
    """
    Fetches real-time critical weather status from a third-party global monitoring API
    to determine if field automation tools should be paused.
    """

    def __init__(self, endpoint_url: str = "https://api.weather-service.external/v1/alert"):
        self.endpoint_url = endpoint_url

    def should_pause_operations(self) -> bool:
        """
        Sends an HTTP GET request to the external server.
        Expects a JSON response like: {"status": "success", "alert_level": "RED"}

        :return: True if the alert_level is 'RED' or 'ORANGE'.
        :raises ThirdPartyServiceError: If HTTP status is not 200, or connection fails.
        """
        try:
            response = requests.get(self.endpoint_url, timeout=5)

            if response.status_code != 200:
                raise ThirdPartyServiceError(f"External service returned status code {response.status_code}")

            data = response.json()
            alert_level = data.get("alert_level", "").upper()

            return alert_level in ["RED", "ORANGE"]

        except requests.RequestException as e:
            raise ThirdPartyServiceError(f"Failed to connect to weather provider: {str(e)}")

class TestWeatherAlertService(unittest.TestCase):

    @mock.patch.object(requests, 'get') # it is required to patch an object here to avoid incorrect target
    def test_status_code_200_with_red_alert_level(self, mock_get):
        service = WeatherAlertService()
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {
            "status": "success", "alert_level": "RED"}
        mock_get.return_value = response_mock
        assert service.should_pause_operations() is True

    @mock.patch.object(requests, 'get')
    def test_status_code_200_with_orange_alert_level(self, mock_get):
        service = WeatherAlertService()
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {
            "status": "success", "alert_level": "ORANGE"}
        mock_get.return_value = response_mock
        assert service.should_pause_operations() is True

    @mock.patch.object(requests, 'get')
    def test_status_code_200_with_wrong_alert_level(self, mock_get):
        service = WeatherAlertService()
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {
            "status": "success", "alert_level": "YELLOW"}
        mock_get.return_value = response_mock
        assert service.should_pause_operations() is False

    @mock.patch.object(requests, 'get')
    def test_weather_alert_service_with_empty_json(self, mock_get): # if response.json is empty
        service = WeatherAlertService()
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {}
        mock_get.return_value = response_mock
        assert service.should_pause_operations() is False

    @mock.patch.object(requests, 'get')
    def test_upper_job_for_weather_alert_service(self, mock_get): # verifying .upper function
        service = WeatherAlertService()
        response_mock = MagicMock()
        response_mock.status_code = 200
        response_mock.json.return_value = {
            "status": "success", "alert_level": "orange"}
        mock_get.return_value = response_mock
        assert service.should_pause_operations() is True


    @mock.patch.object(requests, "get", side_effect=ThirdPartyServiceError)  # raising ThirdPartyServiceError
    def test_raising_third_party_error_msg(self, mock_get):
        service = WeatherAlertService()
        with self.assertRaises(ThirdPartyServiceError):
            service.should_pause_operations()

    @mock.patch.object(requests, "get")  # verifying error message for codes != 200
    def test_status_code_400(self, mock_get):
        service = WeatherAlertService()
        response_mock = MagicMock()
        response_mock.status_code = 404
        mock_get.return_value = response_mock
        with self.assertRaises(ThirdPartyServiceError) as e:
            service.should_pause_operations()
        self.assertIn("External service returned status code 404", str(e.exception))

    @mock.patch.object(requests, "get", side_effect=requests.exceptions.Timeout)  # verifying Timeout message
    def test_verifying_timeout_message_for_lost_connection(self, mock_get):
        service = WeatherAlertService()
        response_mock = MagicMock()
        response_mock.status_code = 500
        mock_get.return_value = response_mock
        with self.assertRaises(ThirdPartyServiceError) as e:
            service.should_pause_operations()
        self.assertIn("Failed to connect to weather provider: ", str(e.exception))

if __name__ == '__main__':
    unittest.main()
