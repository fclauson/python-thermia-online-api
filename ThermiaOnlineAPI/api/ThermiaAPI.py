import logging
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter, Retry
from requests import cookies  # Kept here as it's used in the deep __authenticate method
import json
import hashlib
from typing import Dict, Optional, Any, List

from ThermiaOnlineAPI.const import (
    REG_GROUP_HOT_WATER,
    REG_GROUP_OPERATIONAL_OPERATION,
    REG_GROUP_OPERATIONAL_STATUS,
    REG_GROUP_OPERATIONAL_TIME,
    REG_GROUP_TEMPERATURES,
    REG_HOT_WATER_STATUS,
    REG__HOT_WATER_BOOST,
    REG_OPERATIONMODE,
    REG_GROUP_OPERATIONAL_DIAGNOSTICS,
    REG_GROUP_HEATING_CURVE, 
    THERMIA_CONFIG_URL,
    THERMIA_AZURE_AUTH_URL,
    THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE,
    THERMIA_AZURE_AUTH_REDIRECT_URI,
    THERMIA_INSTALLATION_PATH,
)

from ..exceptions.AuthenticationException import AuthenticationException
from ..exceptions.NetworkException import NetworkException
from ..model.HeatPump import ThermiaHeatPump
from ..utils import utils

_LOGGER = logging.getLogger(__name__)

AZURE_AUTH_AUTHORIZE_URL = f"{THERMIA_AZURE_AUTH_URL}/oauth2/v2.0/authorize"
AZURE_AUTH_GET_TOKEN_URL = f"{THERMIA_AZURE_AUTH_URL}/oauth2/v2.0/token"
AZURE_SELF_ASSERTED_URL = f"{THERMIA_AZURE_AUTH_URL}/SelfAsserted"
AZURE_AUTH_CONFIRM_URL = f"{THERMIA_AZURE_AUTH_URL}/api/CombinedSigninAndSignup/confirmed"

azure_auth_request_headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

REG_OPERATIONMODE_SKIP_VALUES = ["REG_VALUE_OPERATION_MODE_SERVICE"]
GLOBAL_TIMEOUT = (5, 10)

# Constants to eliminate magic numbers
HOT_WATER_START_TEMP_REGISTER_INDEX = 107061


class ThermiaAPI:
    def __init__(self, email, password):
        self.__email = email
        self.__password = password
        self.__token = None
        self.__token_valid_to = None
        self.__refresh_token_valid_to = None
        self.__refresh_token = None

        # Cleaned up unnecessary CORS request headers
        self.__default_request_headers = {
            "Authorization": "Bearer ",
            "Content-Type": "application/json",
            "cache-control": "no-cache",
        }

        self.__session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.__session.mount("https://", adapter)

        self.configuration = self.__fetch_configuration()
        self.authenticated = self.__authenticate()

    def __make_get_request(self, url: str, error_msg: str) -> Optional[List[Dict[str, Any]]]:
        """Reviewer #1: Helper to eliminate repetitive GET request logic across the API."""
        self.__check_token_validity()
        try:
            response = self.__session.get(url, headers=self.__default_request_headers, timeout=GLOBAL_TIMEOUT)
            if response.status_code != 200:
                _LOGGER.error("Error: %s. Status: %s, Response: %s", error_msg, response.status_code, response.text)
                return None
            return utils.get_response_json_or_log_and_raise_exception(response, error_msg)
        except requests.RequestException as e:
            _LOGGER.error("Timeout or network error during '%s': %s", error_msg, e)
            return None

    def get_devices(self) -> List[Dict[str, Any]]:
        url = f"{self.configuration['apiBaseUrl']}/api/v1/installationsInfo"
        response = self.__make_get_request(url, "fetching devices list")
        return response.get("items", []) if response else []

    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        # Reviewer #4: Simplified lookup using next()
        devices = self.get_devices()
        device = next((d for d in devices if str(d["id"]) == str(device_id)), None)
        if device is None:
            _LOGGER.error("Device not found with id: %s", device_id)
        return device

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.configuration['apiBaseUrl']}/api/v1/installations/{device_id}"
        return self.__make_get_request(url, "fetching device info")

    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.configuration['apiBaseUrl']}/api/v1/installationstatus/{device_id}/status"
        return self.__make_get_request(url, "fetching device status")

    def get_all_alarms(self, device_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.configuration['apiBaseUrl']}/api/v1/installation/{device_id}/events?onlyActiveAlarms=false"
        return self.__make_get_request(url, "fetching active alarms")

    def get_historical_data_registers(self, device_id: str) -> Optional[Dict[str, Any]]:
        url = f"{self.configuration['apiBaseUrl']}/api/v1/DataHistory/installation/{device_id}"
        return self.__make_get_request(url, "fetching historical data registers")

    def get_historical_data(
        self, device_id: str, register_id: Any, start_date_str: str, end_date_str: str
    ) -> Optional[Dict[str, Any]]:
        url = (
            f"{self.configuration['apiBaseUrl']}/api/v1/datahistory/installation/{device_id}"
            f"/register/{register_id}/minute?periodStart={start_date_str}&periodEnd={end_date_str}"
        )
        return self.__make_get_request(url, "fetching historical register specific data")

    def get_all_available_groups(self, installation_profile_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.configuration['apiBaseUrl']}/api/v1/installationprofiles/{installation_profile_id}/groups"
        return self.__make_get_request(url, "fetching available configuration groups")

    def get_group_temperatures(self, device_id: str) -> List[Dict[str, Any]]:
        return self.__get_register_group(device_id, REG_GROUP_TEMPERATURES)

    def get_group_operational_status(self, device_id: str) -> List[Dict[str, Any]]:
        return self.__get_register_group(device_id, REG_GROUP_OPERATIONAL_STATUS)

    def get_group_operational_time(self, device_id: str) -> List[Dict[str, Any]]:
        return self.__get_register_group(device_id, REG_GROUP_OPERATIONAL_TIME)

    def get_group_operational_operation(self, device: ThermiaHeatPump) -> Optional[Dict[str, Any]]:
        return self.__get_group_operational_operation_from_register_group(device, REG_GROUP_OPERATIONAL_OPERATION)

    def get_group_operational_operation_from_status(self, device: ThermiaHeatPump) -> Optional[Dict[str, Any]]:
        return self.__get_group_operational_operation_from_register_group(device, REG_GROUP_OPERATIONAL_STATUS)

    def __get_group_operational_operation_from_register_group(
        self, device: ThermiaHeatPump, register_group: str
    ) -> Optional[Dict[str, Any]]:
        register_data = self.__get_register_group(device.id, register_group)
        data = next((d for d in register_data if d["registerName"] == REG_OPERATIONMODE), None)

        if not data:
            return None

        device.set_register_index_operation_mode(data["registerId"])
        current_operation_mode_value = int(data.get("registerValue"))
        operation_modes_data = data.get("valueNames")

        if operation_modes_data is not None:
            # Reviewer #5: Cleaned up ugly nested lambda maps with an explicit readable loop
            operation_modes = {}
            for values in operation_modes_data:
                name = values.get("name", "")
                if name not in REG_OPERATIONMODE_SKIP_VALUES:
                    mode_name = name.split("REG_VALUE_OPERATION_MODE_")[1]
                    operation_modes[values.get("value")] = mode_name

            current_operation_mode = [
                name for value, name in operation_modes.items() if value == current_operation_mode_value
            ]
            if len(current_operation_mode) != 1:
                return None

            return {
                "current": current_operation_mode[0],
                "available": operation_modes,
                "isReadOnly": data["isReadOnly"],
            }
        return None

    def __get_switch_register_index_and_value_from_group_by_register_name(
        self, register_group: List[Dict[str, Any]], register_name: str
    ) -> Dict[str, Any]:
        default_return_object = {"registerId": None, "registerValue": None}
        switch_data = next((d for d in register_group if d["registerName"] == register_name), None)

        if not switch_data:
            return default_return_object

        register_value = switch_data.get("registerValue")
        if register_value is None:
            return default_return_object

        switch_states_data = switch_data.get("valueNames")
        if switch_states_data is None or len(switch_states_data) != 2:
            return default_return_object

        return {
            "registerId": switch_data["registerId"],
            "registerValue": int(register_value),
        }

    def get_group_hot_water_installer(self, device: ThermiaHeatPump) -> List[Dict[str, Any]]:
        return self.__get_register_group(device.id, REG_GROUP_HOT_WATER)
    
    def get_hp_diagnostics(self, device: ThermiaHeatPump) -> List[Dict[str, Any]]:
        return self.__get_register_group(device.id, REG_GROUP_OPERATIONAL_DIAGNOSTICS)

    def get_heating_curve(self, device: ThermiaHeatPump) -> List[Dict[str, Any]]:
        return self.__get_register_group(device.id, REG_GROUP_HEATING_CURVE)

    def get_group_hot_water(self, device: ThermiaHeatPump) -> Dict[str, Optional[int]]:
        register_data = self.__get_register_group(device.id, REG_GROUP_HOT_WATER)

        hot_water_switch_data = self.__get_switch_register_index_and_value_from_group_by_register_name(
            register_data, REG_HOT_WATER_STATUS
        )
        hot_water_boost_switch_data = self.__get_switch_register_index_and_value_from_group_by_register_name(
            register_data, REG__HOT_WATER_BOOST
        )

        device.set_register_index_hot_water_switch(hot_water_switch_data["registerId"])
        device.set_register_index_hot_water_boost_switch(hot_water_boost_switch_data["registerId"])

        return {
            "hot_water_switch": hot_water_switch_data["registerValue"],
            "hot_water_boost_switch": hot_water_boost_switch_data["registerValue"],
        }

    def set_temperature(self, device: ThermiaHeatPump, temperature: Any):
        device_temperature_register_index = device.get_register_indexes()["temperature"]
        if device_temperature_register_index is None:
            _LOGGER.error("Error setting device's temperature. No temperature register index.")
            return

        safe_temp = int(round(float(temperature)))
        self.__set_register_value(device, device_temperature_register_index, safe_temp)

    def set_hot_water_start_temperature(self, device: ThermiaHeatPump, temperature: Any):
        # Reviewer #2: Eliminated hardcoded magic numbers
        _LOGGER.info("set_hot_water_start_temp requested: %s", temperature)
        safe_temp = int(round(float(temperature)))
        self.__set_register_value(device, HOT_WATER_START_TEMP_REGISTER_INDEX, safe_temp)

    def set_operation_mode(self, device: ThermiaHeatPump, mode: str):
        if device.is_operation_mode_read_only:
            _LOGGER.error("Error setting device's operation mode. Operation mode is read only.")
            return

        operation_mode_int = next((val for val, name in device.available_operation_mode_map.items() if name == mode), None)

        if operation_mode_int is None:
            _LOGGER.error("Error setting device's operation mode. Invalid operation mode: %s", mode)
            return

        device_operation_mode_register_index = device.get_register_indexes()["operation_mode"]
        if device_operation_mode_register_index is None:
            _LOGGER.error("Error setting device's operation mode. No operation mode register index.")
            return

        self.__set_register_value(device, device_operation_mode_register_index, operation_mode_int)

    def set_hot_water_switch_state(self, device: ThermiaHeatPump, state: int):  
        register_index = device.get_register_indexes()["hot_water_switch"]
        if register_index is None:
            _LOGGER.error("Error setting device's hot water switch state. No register index.")
            return
        self.__set_register_value(device, register_index, int(state))

    def set_hot_water_boost_switch_state(self, device: ThermiaHeatPump, state: int):  
        register_index = device.get_register_indexes()["hot_water_boost_switch"]
        if register_index is None:
            _LOGGER.error("Error setting device's hot water boost switch state. No register index.")
            return
        self.__set_register_value(device, register_index, int(state))

    def get_register_group_json(self, device_id: str, register_group: str) -> List[Dict[str, Any]]:
        return self.__get_register_group(device_id, register_group)

    def set_register_value(self, device: ThermiaHeatPump, register_index: int, value: int):
        self.__set_register_value(device, register_index, int(value))

    def __get_register_group(self, device_id: str, register_group: str) -> List[Dict[str, Any]]:
        url = f"{self.configuration['apiBaseUrl']}{THERMIA_INSTALLATION_PATH}{device_id}/Groups/{register_group}"
        response = self.__make_get_request(url, f"fetching register group {register_group}")
        return response if response else []

    def __set_register_value(self, device: ThermiaHeatPump, register_index: int, register_value: int):
        """Modified: Keeps log patterns but raises NetworkExceptions on failure to notify HA frontend cleanly."""
        self.__check_token_validity()
        _LOGGER.info("set_register_value: device.id=%s, register_index=%s, register_value=%s", device.id, register_index, register_value)
        
        url = f"{self.configuration['apiBaseUrl']}{THERMIA_INSTALLATION_PATH}{device.id}/Registers"
        body = {
            "registerSpecificationId": register_index,
            "registerValue": register_value,
            "clientUuid": "api-client-uuid",
        }

        try:
            request = self.__session.post(url, headers=self.__default_request_headers, json=body, timeout=GLOBAL_TIMEOUT)
            if request.status_code != 200:
                _LOGGER.error("Error setting register %s value. Status: %s, Response: %s", register_index, request.status_code, request.text)
                raise NetworkException(f"Failed to set register value. API returned status {request.status_code}")
        except requests.RequestException as e:
            _LOGGER.error("Timeout or network error setting register %s: %s", register_index, e)
            raise NetworkException("Network timeout updating register state via cloud API")

    def __fetch_configuration(self) -> Dict[str, Any]:
        try:
            request = self.__session.get(THERMIA_CONFIG_URL, timeout=GLOBAL_TIMEOUT)
            if request.status_code != 200:
                _LOGGER.error("Error fetching API configuration. Status: %s, Response: %s", request.status_code, request.text)
                raise NetworkException("Error fetching API configuration.", request.status_code)
            return utils.get_response_json_or_log_and_raise_exception(request, "Error fetching API configuration.")
        except requests.RequestException as e:
            _LOGGER.error("Critical timeout fetching API configuration framework: %s", e)
            raise NetworkException("Critical timeout fetching API configuration framework.", 0)

    def __authenticate_refresh_token(self) -> Optional[str]:
        _LOGGER.info("Attempting to renew session via Azure OAuth refresh token.")
        request_token__data = {
            "client_id": THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE,
            "redirect_uri": THERMIA_AZURE_AUTH_REDIRECT_URI,
            "scope": THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE,
            "refresh_token": self.__refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            request_token = self.__session.post(
                AZURE_AUTH_GET_TOKEN_URL,
                headers=azure_auth_request_headers,
                data=request_token__data,
                timeout=GLOBAL_TIMEOUT
            )
            if request_token.status_code != 200:
                self.__refresh_token = None
                self.__refresh_token_valid_to = None
                _LOGGER.warning("Refresh token renewal rejected by Azure. Status: %s", request_token.status_code)
                return None
            return request_token.text
        except requests.RequestException as e:
            _LOGGER.error("Timeout during refresh token authentication request: %s", e)
            return None

    def __authenticate(self) -> bool:
        refresh_azure_token = bool(self.__refresh_token and self.__refresh_token_valid_to and (
            self.__refresh_token_valid_to > datetime.now().timestamp()
        ))

        request_token_text = None
        if refresh_azure_token:  
            request_token_text = self.__authenticate_refresh_token()

        if request_token_text is None:  
            _LOGGER.info("Performing full web-credential login cycle.")
            self.__token = None
            self.__token_valid_to = None

            code_challenge = utils.generate_challenge(43)
            request_auth__data = {
                "client_id": THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE,
                "scope": THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE,
                "redirect_uri": THERMIA_AZURE_AUTH_REDIRECT_URI,
                "response_type": "code",
                "code_challenge": str(
                    utils.base64_url_encode(hashlib.sha256(code_challenge.encode("utf-8")).digest()), "utf-8"
                ),
                "code_challenge_method": "S256",
            }

            try:
                request_auth = self.__session.get(AZURE_AUTH_AUTHORIZE_URL, data=request_auth__data, timeout=GLOBAL_TIMEOUT)
            except requests.RequestException as e:
                raise NetworkException("Timeout hitting Azure Authorize endpoint", e)

            state_code = ""
            csrf_token = ""

            if request_auth.status_code == 200:
                settings_string = request_auth.text.split("var SETTINGS = ")
                settings_string = settings_string[1].split("};")[0] + "}"
                if len(settings_string) > 0:
                    try:
                        settings = json.loads(settings_string)
                        state_code = str(settings["transId"]).split("=")[1]
                        csrf_token = settings["csrf"]
                    except Exception as e:
                        _LOGGER.error("Error parsing authorization API settings.", exc_info=True)
                        raise NetworkException(f"Error parsing authorization API settings. {request_auth.text}", e)
            else:
                _LOGGER.error("Error fetching authorization API. Status: %s", request_auth.status_code)
                raise NetworkException("Error fetching authorization API.", request_auth.reason)

            request_self_asserted__data = {
                "request_type": "RESPONSE",
                "signInName": self.__email,
                "password": self.__password,
            }
            request_self_asserted__query_params = {
                "tx": f"StateProperties={state_code}",
                "p": "B2C_1A_SignUpOrSigninOnline",
            }

            try:
                request_self_asserted = self.__session.post(
                    AZURE_SELF_ASSERTED_URL,
                    cookies=request_auth.cookies,
                    data=request_self_asserted__data,
                    headers={**azure_auth_request_headers, "X-Csrf-Token": csrf_token},
                    params=request_self_asserted__query_params,
                    timeout=GLOBAL_TIMEOUT
                )
            except requests.RequestException as e:
                raise NetworkException("Timeout hitting Azure Self Asserted login endpoint", e)

            if request_self_asserted.status_code != 200 or '{"status":"400"' in request_self_asserted.text:
                _LOGGER.error("Error in API authentication. Wrong credentials.")
                raise NetworkException("Error in API authentication. Wrong credentials", request_self_asserted.text)

            request_confirmed__cookies = request_self_asserted.cookies
            cookie_obj = cookies.create_cookie(
                name="x-ms-cpim-csrf", value=request_auth.cookies.get("x-ms-cpim-csrf")
            )
            request_confirmed__cookies.set_cookie(cookie_obj)

            request_confirmed__params = {
                "csrf_token": csrf_token,
                "tx": f"StateProperties={state_code}",
                "p": "B2C_1A_SignUpOrSigninOnline",
            }

            try:
                request_confirmed = self.__session.get(
                    AZURE_AUTH_CONFIRM_URL,
                    cookies=request_confirmed__cookies,
                    params=request_confirmed__params,
                    timeout=GLOBAL_TIMEOUT
                )
            except requests.RequestException as e:
                raise NetworkException("Timeout hitting Azure Confirmation redirect", e)

            request_token__data = {
                "client_id": THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE,
                "redirect_uri": THERMIA_AZURE_AUTH_REDIRECT_URI,
                "scope": THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE,
                "code": utils.get_list_value_or_default(request_confirmed.url.split("code="), 1, ""),
                "code_verifier": code_challenge,
                "grant_type": "authorization_code",
            }

            try:
                request_token = self.__session.post(
                    AZURE_AUTH_GET_TOKEN_URL,
                    headers=azure_auth_request_headers,
                    data=request_token__data,
                    timeout=GLOBAL_TIMEOUT
                )
            except requests.RequestException as e:
                raise NetworkException("Timeout requesting JWT bearer access token", e)

            if request_token.status_code != 200:
                raise AuthenticationException(f"Authentication request failed. Status: {request_token.status_code}")

            request_token_text = request_token.text

        try:
            token_data = json.loads(request_token_text)
        except Exception as e:
            raise NetworkException(f"Error parsing token payload string: {request_token_text}", e)

        self.__token = token_data["access_token"]
        self.__token_valid_to = token_data["expires_on"]
        self.__refresh_token_valid_to = (datetime.now() + timedelta(hours=6)).timestamp()
        self.__refresh_token = token_data.get("refresh_token")

        self.__default_request_headers["Authorization"] = f"Bearer {self.__token}"
        _LOGGER.info("Authentication cycle resolved successfully.")
        return True

    def __check_token_validity(self):
        now_with_padding = datetime.now().timestamp() + 60
        if (
            self.__token_valid_to is None
            or self.__token_valid_to < now_with_padding
            or self.__refresh_token_valid_to is None
            or self.__refresh_token_valid_to < now_with_padding
        ):
            _LOGGER.info("API Session token expiration threshold reached. Re-validating identity tokens.")
            self.authenticated = self.__authenticate()
