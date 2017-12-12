import os
import sys
import logging

from syncrosim import SynrosimDB

DATASHEET_FARSITE_OPTIONS_NAME = 'Farsite_Options'
DATASHEET_RUN_CONTROL_NAME = 'STSim_RunControl'
DATASHEET_OUTPUT_OPTIONS_NAME = 'STSim_OutputOptions'
DATASHEET_SSIM_PROCESSING = 'SSim_Processing'

# Farsite Options
OPTION_ENABLED = 'Enabled'
OPTION_FREQUENCY = 'TimestepFrequency'
OPTION_STATE_ATTR_FUEL_MODEL = 'FuelModelStateAttributeTypeID'
OPTION_STATE_ATTR_CANOPY_COVER = 'CanopyCoverStateAttributeTypeID'
OPTION_TRANSITION_GROUP= 'TransitionGroupID'
OPTION_TRANSITION_MULTIPLIER_TYPE = 'TransitionMultiplierTypeID'

OPTION_ELEVATION_RASTER_FILE="ElevationRasterFile"
OPTION_SLOPE_RASTER_FILE="SlopeRasterFile"
OPTION_ASPECT_RASTER_FILE="AspectRasterFile"
OPTION_NUM_IGNITIONS_PER_TIMESTEP="NumIgnitionsPerTimestep"
OPTION_DISTRIBUTION_FOR_NUM_IGNITIONS="DistForNumIgnitions"
OPTION_FIRE_SEASON_START_JULIAN_DAY="FireSeasonStartJulianDay"
OPTION_FIRE_SEASON_END_JULIAN_DAY="FireSeasonEndJulianDay"
OPTION_MEAN_FIRE_DURATION_HOURS="MeanFireDurationHours"
OPTION_WEATHER_MIN_TEMP="WeatherMinTemp"
OPTION_WEATHER_MAX_TEMP="WeatherMaxTemp"
OPTION_WEATHER_MIN_TEMP_HOUR="WeatherMinTempHour"
OPTION_WEATHER_MAX_TEMP_HOUR="WeatherMaxTempHour"
OPTION_WEATHER_MIN_HUMIDITY="WeatherMinHumidity"
OPTION_WEATHER_MAX_HUMIDITY="WeatherMaxHumidity"
OPTION_WEATHER_ELEVATION="WeatherElevation"
OPTION_WEATHER_PRECIPITATION="WeatherPrecipitation"
# OPTION_WEATHER_PRECIP_START_TIME="WeatherPrecipStartTime"
# OPTION_WEATHER_PRECIP_END_TIME="WeatherPrecipEndTime"
OPTION_WIND_SPEED="WindSpeed"
OPTION_WIND_DIRECTION="WindDirection"
OPTION_CLOUD_COVER_PERCENT="CloudCoverPercent"
# OPTION_WEATHERWINDDATAUNITS="WeatherWindDataUnits"
OPTION_TIME_STEP_RESOLUTION_MINUTES="TimeStepResolutionMinutes"
OPTION_FARSITE_ACCELERATION="FarsiteAccelerationOn"
OPTITON_SAVE_INTERMEDIATE_FILES = "SaveIntermediateFiles"
OPTION_FUEL_MOISTURE_1= "FuelMoisture1"
OPTION_FUEL_MOISTURE_10= "FuelMoisture10"
OPTION_FUEL_MOISTURE_100= "FuelMoisture100"
OPTION_FUEL_MOISTURE_LIVE_HERB= "FuelMoistureLiveHerb"
OPTION_FUEL_MOISTURE_LIVE_WOODY= "FuelMoistureLiveWoody"
OPTION_DISTANCE_RESOLUTION = "DistanceResolution"
OPTION_PERIMETER_RESOLUTION = "PerimeterResolution"

#SSIM_PROCESSING
SSIM_PROCESSING_DELETE_TEMP_FILE = 'AutoDeleteTempFiles'


class Config:


    def __init__(self, cmdArgs):

        # Fetch the Syncrosim specific External Transformer Environmental Variables
        # SSIM_BASE_DIRECTORY       - The location of the entry assembly. Ex: D:\\SVNProjects\\SyncroSim-1\\WinForm\\bin\\x86\\Debug
        # SSIM_CONNECTION_STRING    - The connection string for the Transformer's Library. Ex: D:\\ApexRMS\\Raster Simulator A131\\Sample Landfire Data\\ST-Sim-Spatial-Sample-V2-4-6.ssim
        # SSIM_PROJECT_ID           - The Project ID for the Transformer's Result Scenario
        # SSIM_SCENARIO_ID          - The Scenario ID for the Transformer's Result Scenario
        # SSIM_INPUT_DIRECTORY      - The external file input directory for the Transformer's Result Scenario
        # SSIM_OUTPUT_DIRECTORY     - The external file output directory for the Transformer's Result Scenario
        # SSIM_TEMP_DIRECTORY       - The temporary directory for the Transformer's Result Scenario
        # SSIM_DATA_DIRECTORY       - The data directory for the Transformer's Result Scenario. Ex: D:\\ApexRMS\\Raster Simulator A131\\Sample Landfire Data\\ST-Sim-Spatial-Sample-V2-4-6.ssim.temp\\ExternalProgramData'
        # SSIM_STOCHASTIC_TIME_BEFORE_ITERATION - current iteration
        # SSIM_STOCHASTIC_TIME_BEFORE_TIMESTEP - current timestep


        self.library = os.environ["SSIM_CONNECTION_STRING"]

        self.projectId = int(os.environ["SSIM_PROJECT_ID"])

        self.scenarioId = int(os.environ["SSIM_SCENARIO_ID"])

        self.base_dir = os.environ["SSIM_BASE_DIRECTORY"]

        self.data_dir = os.environ["SSIM_DATA_DIRECTORY"]

        self.input_dir =os.environ["SSIM_INPUT_DIRECTORY"]

        self.output_dir = os.environ["SSIM_OUTPUT_DIRECTORY"]

        self.temp_dir = os.environ["SSIM_TEMP_DIRECTORY"]

        self.iteration = int(os.environ["SSIM_STOCHASTIC_TIME_BEFORE_ITERATION"])

        self.timestep = int(os.environ["SSIM_STOCHASTIC_TIME_BEFORE_TIMESTEP"])

        # Lets load up the various runtime parameters needed to run

        self.db = SynrosimDB(self.library,self.base_dir)

        dsFarsiteOptions = self.db.getScenarioDataSheet(DATASHEET_FARSITE_OPTIONS_NAME, self.scenarioId)
        if dsFarsiteOptions == None:
            # If none returned, then most like no scenario ( or lib...)
            logging.error('Scenario {0} not found.'.format(self.scenarioId))
            sys.exit(1)

        if len(dsFarsiteOptions)==0:
            logging.info("The Farsite Options have not been configured for this scenario. No processing performed.")
            sys.exit(0)

        options = dsFarsiteOptions[0]

        expected_option_fields = [OPTION_ENABLED, OPTION_FREQUENCY,OPTION_TRANSITION_GROUP,OPTION_TRANSITION_MULTIPLIER_TYPE,
                                OPTION_STATE_ATTR_CANOPY_COVER,OPTION_STATE_ATTR_FUEL_MODEL,
                                OPTION_ELEVATION_RASTER_FILE,OPTION_SLOPE_RASTER_FILE,OPTION_ASPECT_RASTER_FILE,
                                OPTION_NUM_IGNITIONS_PER_TIMESTEP,
                                OPTION_DISTRIBUTION_FOR_NUM_IGNITIONS,
                                OPTION_FIRE_SEASON_START_JULIAN_DAY,OPTION_FIRE_SEASON_END_JULIAN_DAY,
                                OPTION_MEAN_FIRE_DURATION_HOURS,
                                OPTION_WEATHER_MIN_TEMP,OPTION_WEATHER_MAX_TEMP,
                                OPTION_WEATHER_MIN_TEMP_HOUR,OPTION_WEATHER_MAX_TEMP_HOUR,
                                OPTION_WEATHER_MIN_HUMIDITY,OPTION_WEATHER_MAX_HUMIDITY,
                                OPTION_WEATHER_ELEVATION,
                                OPTION_WEATHER_PRECIPITATION,
                                # OPTION_WEATHER_PRECIP_START_TIME,OPTION_WEATHER_PRECIP_END_TIME,
                                OPTION_WIND_SPEED,OPTION_WIND_DIRECTION,
                                OPTION_CLOUD_COVER_PERCENT,
                                OPTION_TIME_STEP_RESOLUTION_MINUTES,
                                OPTION_FARSITE_ACCELERATION,OPTITON_SAVE_INTERMEDIATE_FILES,
                                OPTION_FUEL_MOISTURE_1,OPTION_FUEL_MOISTURE_10,OPTION_FUEL_MOISTURE_100,OPTION_FUEL_MOISTURE_LIVE_HERB,OPTION_FUEL_MOISTURE_LIVE_WOODY,
                                OPTION_DISTANCE_RESOLUTION,OPTION_PERIMETER_RESOLUTION
                                ]
        for exp in expected_option_fields:
            if not options.has_key(exp):
                logging.error('Farsite Options missing expected "{0}"'.format(exp))
                sys.exit(1)

        self.enabled = options[OPTION_ENABLED]
        if (self.enabled !='Yes'):
            logging.info("Farsite Enabled option is not set to 'Yes'. Processing not performed.")
            sys.exit(0)

        self.frequency = int(options[OPTION_FREQUENCY])
        self.sa_fuel_model_name = options[OPTION_STATE_ATTR_FUEL_MODEL]
        self.sa_fuel_model_id = int(self.db.getStateAttributeId(self.projectId, self.sa_fuel_model_name))

        self.sa_canopy_cover_name = options[OPTION_STATE_ATTR_CANOPY_COVER]
        if self.sa_canopy_cover_name:
            self.sa_canopy_cover_id = int(self.db.getStateAttributeId(self.projectId, self.sa_canopy_cover_name))
        else:
            self.sa_canopy_cover_id = None

        self.transition_group_name = options[OPTION_TRANSITION_GROUP]
        self.transition_group_id = int(self.db.getTransitionGroupId(self.projectId, self.transition_group_name))

        self.transition_multiplier_type_name = options[OPTION_TRANSITION_MULTIPLIER_TYPE]
        self.transition_multiper_type_id = int(self.db.getTransitionMultiplierTypeId(self.projectId, self.transition_multiplier_type_name))

        inputFSOPath = self.getScenarioDatasheetInputPath('Farsite_Options')
        self.elevation_raster_file =  os.path.join(inputFSOPath,options[OPTION_ELEVATION_RASTER_FILE])

        self.slope_raster_file = os.path.join(inputFSOPath,options[OPTION_SLOPE_RASTER_FILE])
        self.aspect_raster_file = os.path.join(inputFSOPath,options[OPTION_ASPECT_RASTER_FILE])
        self.num_ignitions_per_timestep = int(options[OPTION_NUM_IGNITIONS_PER_TIMESTEP])
        self.dist_for_num_ignitions= options[OPTION_DISTRIBUTION_FOR_NUM_IGNITIONS]
        self.fire_season_start_julian_day = int(options[OPTION_FIRE_SEASON_START_JULIAN_DAY])
        self.fire_season_end_julian_day = int(options[OPTION_FIRE_SEASON_END_JULIAN_DAY])
        self.mean_fire_duration_hours = float(options[OPTION_MEAN_FIRE_DURATION_HOURS])
        self.weather_min_temp = int(options[OPTION_WEATHER_MIN_TEMP])
        self.weather_max_temp = int(options[OPTION_WEATHER_MAX_TEMP])
        self.weather_min_temp_hour = int(options[OPTION_WEATHER_MIN_TEMP_HOUR])
        self.weather_max_temp_hour = int(options[OPTION_WEATHER_MAX_TEMP_HOUR])
        self.weather_min_humidity = int(options[OPTION_WEATHER_MIN_HUMIDITY])
        self.weather_max_humidity = int(options[OPTION_WEATHER_MAX_HUMIDITY])
        self.weather_elevation = int(options[OPTION_WEATHER_ELEVATION])
        self.weather_precipitation =  float(options[OPTION_WEATHER_PRECIPITATION])
        # self.weather_precip_start_time = int(options[OPTION_WEATHER_PRECIP_START_TIME])
        # self.weather_precip_end_time = int(options[OPTION_WEATHER_PRECIP_END_TIME])
        self.wind_speed = int(options[OPTION_WIND_SPEED])
        self.wind_direction = int(options[OPTION_WIND_DIRECTION])
        self.cloud_cover_percent = int(options[OPTION_CLOUD_COVER_PERCENT])
        self.time_step_resolution_minutes = int(options[OPTION_TIME_STEP_RESOLUTION_MINUTES])
        self.farsite_acceleration = options[OPTION_FARSITE_ACCELERATION]
        self.save_intermediate_files = options[OPTITON_SAVE_INTERMEDIATE_FILES]
        self.fuel_moisture_1  =int(options[OPTION_FUEL_MOISTURE_1])
        self.fuel_moisture_10 =int(options[OPTION_FUEL_MOISTURE_10])
        self.fuel_moisture_100=int(options[OPTION_FUEL_MOISTURE_100])
        self.fuel_moisture_live_herb =int(options[OPTION_FUEL_MOISTURE_LIVE_HERB])
        self.fuel_moisture_live_woody=int(options[OPTION_FUEL_MOISTURE_LIVE_WOODY])
        self.distance_resolution = int(options[OPTION_DISTANCE_RESOLUTION])
        self.perimeter_resolution = int(options[OPTION_PERIMETER_RESOLUTION])

        # Do some QA
        # Check to see if this is a spatial run
        dsRunControl = self.db.getScenarioDataSheet(DATASHEET_RUN_CONTROL_NAME, self.scenarioId)
        run_control = dsRunControl[0]
        if run_control['IsSpatial']<>'Yes':
            logging.warning("The current scenario has not been selected to Run model Spatially")
            sys.exit(1)

        # Fetch the Timestep Start and End
        self.minimum_timestep = int(run_control['MinimumTimestep'])
        self.maximum_timestep = int(run_control['MaximumTimestep'])

        # Check to see if State Attribute Output is enabled
        dsOutputOptions= self.db.getScenarioDataSheet(DATASHEET_OUTPUT_OPTIONS_NAME, self.scenarioId)
        if len(dsOutputOptions) == 0:
            logging.error("The Output Options have not been configured for this scenario.")
            sys.exit(1)

        outputOptions = dsOutputOptions[0]
        # Is State Attribute Spatial Output Enabled
        if outputOptions['RasterOutputSA'] <> 'Yes':
            logging.error("State Attribute Spatial Output in not enabled.")
            sys.exit(1)

        if outputOptions['RasterOutputSATimesteps']:
            saTimesteps = int(outputOptions['RasterOutputSATimesteps'])
            # Check to see if State Attribute frequency if a divisor of Farsite Frequency
            if (self.frequency  % saTimesteps ) <> 0:
                logging.warning('State Attribute frequency ({0}) must be an even divisor of Farsite Frequency ({1})'.format(saTimesteps,self.frequency))
                sys.exit(1)
        else:
            logging.warning("State Attribute Spatial Output Timesteps is not set.")
            sys.exit(1)

        # Get the IC Primary Stratum file name. We will use this for our definitive Raster (row,cols, cell_size, extent..
        dsICS = self.db.getScenarioDataSheet('STSim_InitialConditionsSpatial',self.scenarioId)
        if dsICS == None or len(dsICS) == 0:
            logging.error('Could not find Initial Conditions Spatial for Scenario {0}'.format(self.scenarioId))
            sys.exit(1)

        stratum_file = dsICS[0]['StratumFileName']
        self.primaryStratumFile = os.path.join(self.getScenarioInitConditionalSpatialInputPath(),stratum_file)

        # See if the Farsite Rasters exist
        if not os.path.exists(self.aspect_raster_file):
            logging.error('Could not find the FARSITE Aspect Raster file "{0}"'.format(self.aspect_raster_file))
            sys.exit(1)

        if not os.path.exists(self.elevation_raster_file):
            logging.error('Could not find the FARSITE Elevation Raster file "{0}"'.format(self.elevation_raster_file))
            sys.exit(1)

        if not os.path.exists(self.slope_raster_file):
            logging.error('Could not the FARSITE Slope Raster file "{0}"'.format(self.slope_raster_file))
            sys.exit(1)


        # TODO: Future - Should I test these files for NROW, NCOLS match to Primary Stratum ? YES


        return


    def isOutputTimestep(self,timestep):
        '''
        Determines whether or not the specified timestep is an Output timestep

        :param timestep: The timestep to test
        :return: True if the timestep is within the frequency specified by the user.

        :remarks
        The frequency of the timestep corresponds to the values that the user has specified for timestep output.  For example, someone
        might specify that they only want data every 5 timesteps.  In this case, the frequency will be 5.

        '''
        start_timestep = self.minimum_timestep + 1

        if (((timestep - start_timestep) % self.frequency) == 0):
            return  True

        return False


    def ifnull(self,var, val):
      if var is None:
        return val
      return var

    def getScenarioSpatialOutputPath(self):
        return os.path.join(self.getScenarioOutputPath(), "Spatial")

    def getScenarioInitConditionalSpatialInputPath(self):
        return os.path.join(self.getScenarioInputPath(), "STSim_InitialConditionsSpatial")

    def getScenarioInputPath(self):
        return os.path.join(self.input_dir,"Scenario-{0}".format(self.scenarioId))

    def getScenarioOutputPath(self):
        return os.path.join(self.output_dir,"Scenario-{0}".format(self.scenarioId))

    def getScenarioTempPath(self):
        """
            Get the Scenario Temporary Path
        @type scenarioId: int - The ID of the scenario of interest
        @return: The Scenario Temporary Path @rtype: str| unicode
        """
        return os.path.join(self.temp_dir(),"Scenario-{0}".format(self.scenarioId))


    def getScenarioDatasheetInputPath(self, datasheet_name):
        return os.path.join(self.getScenarioInputPath(), datasheet_name)

