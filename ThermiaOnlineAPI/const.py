###############################################################################
# General configuration
###############################################################################

THERMIA_CONFIG_URL = "https://online.thermia.se/api/configuration"
THERMIA_INSTALLATION_PATH = "/api/v1/Registers/Installations/"

###############################################################################
# Azure AD configuration
###############################################################################

THERMIA_AZURE_AUTH_URL = "https://thermialogin.b2clogin.com/thermialogin.onmicrosoft.com/b2c_1a_signuporsigninonline"
THERMIA_AZURE_AUTH_CLIENT_ID_AND_SCOPE = "09ea4903-9e95-45fe-ae1f-e3b7d32fa385"
THERMIA_AZURE_AUTH_REDIRECT_URI = "https://online.thermia.se/login"

###############################################################################
# Register groups
###############################################################################

REG_GROUP_TEMPERATURES = "REG_GROUP_TEMPERATURES"
REG_GROUP_OPERATIONAL_STATUS = "REG_GROUP_OPERATIONAL_STATUS"
REG_GROUP_OPERATIONAL_TIME = "REG_GROUP_OPERATIONAL_TIME"
REG_GROUP_OPERATIONAL_OPERATION = "REG_GROUP_OPERATIONAL_OPERATION"
REG_GROUP_HOT_WATER = "REG_GROUP_HOT_WATER"

###############################################################################
# Temperature registers
###############################################################################

REG_OUTDOOR_TEMPERATURE = "REG_OUTDOOR_TEMPERATURE"  # Not used
REG_OPER_DATA_OUTDOOR_TEMP_MA_SA = "REG_OPER_DATA_OUTDOOR_TEMP_MA_SA"  # Not used
REG_INDOOR_TEMPERATURE = "REG_INDOOR_TEMPERATURE"
REG_SUPPLY_LINE = "REG_SUPPLY_LINE"
REG_HOT_WATER_TEMPERATURE = "REG_HOT_WATER_TEMPERATURE" # this is the top hot water temp 

# Added by Francis 
REG_OPER_DATA_HOT_WATER = "REG_OPER_DATA_HOT_WATER" # lower hot water temp 
REG_WEIGHTED_HOT_WATER_TEMP = "REG_WEIGHTED_HOT_WATER_TEMP" # weighted temp 

REG_BRINE_OUT = "REG_BRINE_OUT"
REG_BRINE_IN = "REG_BRINE_IN"
REG_OPER_DATA_BUFFER_TANK = "REG_OPER_DATA_BUFFER_TANK"

###############################################################################
# Temperature registers ("classic" specific)
###############################################################################

REG_RETURN_LINE = "REG_RETURN_LINE"
REG_DESIRED_SUPPLY_LINE = "REG_DESIRED_SUPPLY_LINE"
REG_OPER_DATA_SUPPLY_MA_SA = "REG_OPER_DATA_SUPPLY_MA_SA"
REG_DESIRED_SUPPLY_LINE_TEMP = "REG_DESIRED_SUPPLY_LINE_TEMP"
REG_DESIRED_INDOOR_TEMPERATURE = "REG_DESIRED_INDOOR_TEMPERATURE"
###############################################################################
# Temperature registers ("genesis" specific)
###############################################################################

REG_OPER_DATA_RETURN = "REG_OPER_DATA_RETURN"
REG_DESIRED_SYS_SUPPLY_LINE_TEMP = "REG_DESIRED_SYS_SUPPLY_LINE_TEMP"
REG_COOL_SENSOR_TANK = "REG_COOL_SENSOR_TANK"
REG_COOL_SENSOR_SUPPLY = "REG_COOL_SENSOR_SUPPLY"
REG_ACTUAL_POOL_TEMP = "REG_ACTUAL_POOL_TEMP"

###############################################################################
# Operational operation registers
###############################################################################

REG_OPERATIONMODE = "REG_OPERATIONMODE"

###############################################################################
# Operational status registers
###############################################################################

REG_OPERATIONAL_STATUS_PRIO1 = (
    "REG_OPERATIONAL_STATUS_PRIO1"  # Operational status for most heat pumps
)
COMP_STATUS = "COMP_STATUS"  # Operational status for Diplomat heat pumps
COMP_STATUS_ATEC = "COMP_STATUS_ATEC"  # Operational status for ATEC heat pumps
COMP_STATUS_ITEC = "COMP_STATUS_ITEC"  # Operational status for ITEC heat pumps
REG_OPERATIONAL_STATUS_PRIORITY_BITMASK = (
    "REG_OPERATIONAL_STATUS_PRIORITY_BITMASK"  # Operational status for Atlas heat pumps
)
REG_INTEGRAL_LSD = "REG_INTEGRAL_LSD"
REG_PID = "REG_PID"

COMP_POWER_STATUS = "COMP_POWER_STATUS"

###############################################################################
# Hot water registers
###############################################################################

REG_HOT_WATER_STATUS = "REG_HOT_WATER_STATUS"
REG__HOT_WATER_BOOST = "REG__HOT_WATER_BOOST"

###############################################################################
# Operational time registers
###############################################################################

REG_OPER_TIME_IMM1 = "REG_OPER_TIME_IMM1"  # Auxiliary heater 1
REG_OPER_TIME_IMM2 = "REG_OPER_TIME_IMM2"  # Auxiliary heater 2
REG_OPER_TIME_IMM3 = "REG_OPER_TIME_IMM3"  # Auxiliary heater 3
REG_OPER_TIME_COMPRESSOR = "REG_OPER_TIME_COMPRESSOR"
REG_OPER_TIME_HEATING = "REG_OPER_TIME_HEATING"
REG_OPER_TIME_HOT_WATER = "REG_OPER_TIME_HOT_WATER"

###############################################################################
# Other
###############################################################################

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

###############################################################################
# Only available if you Online login has - Francis 26/03/2025
###############################################################################

# registers for setting the start temp 
REG_SER_HOT_WATER_START = "REG_SER_HOT_WATER_START"

# group for diagnostics
REG_GROUP_OPERATIONAL_DIAGNOSTICS = "REG_GROUP_OPERATIONAL_DIAGNOSTICS"

# group for heating curve 
REG_GROUP_HEATING_CURVE = "REG_GROUP_HEATING_CURVE" 

#register for diagnostics
REG_EXV_EVAP_PRESS_MA_SA = "REG_EXV_EVAP_PRESS_MA_SA"
REG_EXV_DATA_SUCTION_TEMP_MA_SA = "REG_EXV_DATA_SUCTION_TEMP_MA_SA"
REG_OPER_DATA_EVAP_TEMP_MA_SA = "REG_OPER_DATA_EVAP_TEMP_MA_SA"
REG_EXV_SUPER_HEAT_MA_SA = "REG_EXV_SUPER_HEAT_MA_SA"
REG_EXV_OPEN_DEG_MA_SA = "REG_EXV_OPEN_DEG_MA_SA"

#register for heat curve 
REG_DESIRED_DISTR_CIR1 = "REG_DESIRED_DISTR_CIR1"
REG_DESIRED_DISTR_CIR2 = "REG_DESIRED_DISTR_CIR2"
REG_HEATING_HEAT_CURVE = "REG_HEATING_HEAT_CURVE"
REG_HEATING_HEAT_CURVE_MIN = "REG_HEATING_HEAT_CURVE_MIN"
REG_HEATING_HEAT_CURVE_MAX = "REG_HEATING_HEAT_CURVE_MAX"
REG_HEATING_CURVE_PLUS5 = "REG_HEATING_CURVE_PLUS5"
REG_HEATING_CURVE_0 = "REG_HEATING_CURVE_0"
REG_HEATING_CURVE_MINUS5 = "REG_HEATING_CURVE_MINUS5"
REG_HEATING_HEAT_STOP = "REG_HEATING_HEAT_STOP"
REG_HEATING_ROOM_FACTOR = "REG_HEATING_ROOM_FACTOR"

