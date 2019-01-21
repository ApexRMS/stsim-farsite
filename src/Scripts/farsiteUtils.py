import logging
import os
import subprocess

import sys
import tempfile

import datetime
import gdal
import shutil

import win32api
from osgeo import ogr
from osgeo import osr
import numpy as np

from gdalconst import *

import random
from shapely.geometry import Point, Polygon

# Path to the Farsite EXE relative to the Python Scripts directory
LCPMAKE_EXE_PATH ="../exe/lcpmake.exe"
FARSITE_EXE_PATH="../exe/TestFARSITE.exe"


def makeFarsiteInputFile( inputs_filename, ignition_filename, config):


    logging.debug('Making Farsite Input file "{0}"'.format(inputs_filename))

    try:
        f = open(inputs_filename, 'w')

        f.write('FARSITE INPUTS FILE VERSION 1.0 produced by FARSITE-STSim Python script {0}\n'.format(datetime.datetime.now()))

        #
        # ii- Generate the Farsite input file including:
        # 1. -Fire start date/time (sampled from a probability distribution)


        fire_start_day =  np.random.uniform(config.fire_season_start_julian_day,config.fire_season_end_julian_day)
        # DEVNOTE: Seems to give us grief if day_start = 1 "Invalid start time Start Date is NOT within usable range of daily weather data", so force to 2 if thats the case
        fire_start_day = max(2,fire_start_day)
        # DEVNOTE: Use a constant non-leap year year, as Farsite doesnt care about year, and we dont want to have date variations
        # due to leap years
        fire_start_datetime = datetime.datetime(2015,1,1) + datetime.timedelta(days=fire_start_day - 1.0)
        f.write('FARSITE_START_TIME: {:%m %d %H%M}\n'.format(fire_start_datetime))

        # 2. - Fire end date/time (use a fixed duration for each ignition for now. Can conduct sensitivity analysis)
        fire_duration_mins  = np.random.poisson(config.mean_fire_duration_hours * 60.0)
        # DEVNOTE: It seems that Farsite wont process if duration less than 10 minutes.
        # TODO: Ask Leo what he want to do with this. Might want to restrict in UI to >=10
        fire_duration_mins = max(fire_duration_mins, 10.0)
        logging.debug('Fire duration (mins)= {}'.format(fire_duration_mins))

        fire_end_day = fire_start_day + fire_duration_mins/(24.0 * 60.0)
        # TODO: Ask Leo - I dont think I want to do the following, becuase you'll end up with a clipping of duration.
        # fire_end_day = min(fire_end_day,config.fire_season_end_julian_day)
        fire_end_datetime = datetime.datetime(2015,1,1) + datetime.timedelta(days= fire_end_day -1.0)
        # Clip within the year
        fire_end_datetime = min(datetime.datetime(2015,12,31,23,59,59),fire_end_datetime)
        f.write('FARSITE_END_TIME: {:%m %d %H%M}\n'.format(fire_end_datetime))

        # 3. - Timestep resolution (minutes)
        #DEVNOTE: In Help file says:
        # Surface Fire/Timber Timestep = 20 to 120 minutes
        # Surface / brush, dry grass = 10 to 20 minutes
        #surface extreme or or torching/crowning/ all fuel = 5 to 10 minutes
        f.write('FARSITE_TIMESTEP: {0}\n'.format(config.time_step_resolution_minutes))

        # 4. - distance and perimeter resolutions - match ST-Sim
        # Match cell size of input rasters
        gdal.UseExceptions()
        ref_raster = gdal.Open(config.primaryStratumFile, gdal.GA_ReadOnly)
        if ref_raster is None:
            logging.error("Cannot open Source Raster file '{0}'".format(config.primaryStratumFile))
            sys.exit(1)


        f.write('FARSITE_DISTANCE_RES: {0}\n'.format(config.distance_resolution))
        f.write('FARSITE_PERIMETER_RES: {0}\n'.format(config.perimeter_resolution))


        # 5. - Fuel moisture by fuel model - need input from the user as a percent moisture by fuel model for 1 hour, 10 hour,
        # 100 hour and live woody and herbaceous fuels.  These numbers are specified as integers and may exceed 100. To begin
        # use hard coded values for extreme conditions.
        # Ex:
        # Fuel mode entry format:
        # Model  FM1   FM10  FM100   FMLiveHerb   FMLiveWoody
        # 0      2      2     3         4           5

        # FUEL_MOISTURES_DATA: 1
        # 0 3 4 8 9 70

        # FUEL_MOISTURE_XXX = 10  # 10% for now
        f.write('FUEL_MOISTURES_DATA: 1\n')
        f.write('0 {0} {1} {2} {3} {4}\n'.format(config.fuel_moisture_1,config.fuel_moisture_10,config.fuel_moisture_100,config.fuel_moisture_live_herb,config.fuel_moisture_live_woody))


        # 6. - weather stream data (wind, temperature, humidity and precip). To begin use hard coded values for extreme conditions.
        #  Example files for the Tucson area are available online.
        # http://fireweather.sc.egov.usda.gov/applications/farsite/farsite_map8.php?usr=lfrid&model=wrf&state=AZ
        # TODO: Website down "RMC Temporarily Unavailable"
        f.write('WEATHER_DATA: 365\n')
        # Weather Data Format:
        # Mth  Day  Pcp  mTH  xTH   mT xT   xH mH   Elv   PST  PET
        # Mth = month,
        # Day = day,
        # Per = precip in hundredths of an inch (integer e.g. 10 = 0.1 inches),
        # mTH = min_temp_hour 0-2400,
        # xTH = max_temp_hour 0 - 2400,
        # mT  = min_temp,
        # xT  = max_temp,
        # mH  = max_humidity
        # xH  = min_humidity,
        # Elv = elevation,
        # PST = precip_start_time 0-2400 * Optional
        # PET = precip_end_time   0-2400 * Optional
        # NOTE: do not leave any blank values


        # Weather Data Example:
        # Mth  Day  Pcp  mTH  xTH   mT xT   xH mH   Elv   PST  PET
        # 6 16 0 500 1500 38 74 58 14 6903 0 0
        # DEVNOTE: Weather data seems to need to be contiguous, and to bookend the Start Time/End Time range. Easist thing to do
        # is just spit out records for complete year
        for day in range(365):
            dt = datetime.date(2015, 1, 1) + datetime.timedelta(days=day)

            # DEVNOTE: Precipitation Times are supposed to optional, but seem to be required if a precip value of <> 0 enter, so hack in 0 and 24
            # Also, if precip = 0, then dont include Start Time/End Time
            if config.weather_precipitation ==0:
                precip_time = ''
            else:
                precip_time = '0 24'

            f.write('{:%m %d} {} {} {} {} {} {} {} {} {}\n'
                    .format(dt,
                            int(config.weather_precipitation * 100),
                            (config.weather_min_temp_hour * 100), (config.weather_max_temp_hour * 100),config.weather_min_temp,config.weather_max_temp,
                            config.weather_max_humidity, config.weather_min_humidity,
                            config.weather_elevation,precip_time
                            )
                    )

        # DEVNOTE: Hardcode units to English, to match the units in the STSim UI boilerplate
        f.write('WEATHER_DATA_UNITS: English\n\n')

        # Wind data
        f.write('WIND_DATA: 365\n')
        # Mth  Day  Hour   Speed Direction CloudCover
        for day in range(365):
            dt = datetime.date(2015, 1, 1) + datetime.timedelta(days=day)
            f.write('{:%m %d} 0 {} {} {}\n'.format(dt,
                                                    config.wind_speed,config.wind_direction, config.cloud_cover_percent))

        # DEVNOTE: Hardcode units to English, to match the units in the STSim UI boilerplate
        f.write('WIND_DATA_UNITS: English\n\n')

        # 7. - Spotting parameters: can probably be ignored or set to non-spotting behaviour defaults as we are not dealing with a forested system.
        #   a. --Spot probability
        #   b. --Spot ignition delay
        #   c. -- Minimum spot distance
        # DEVNOTE: Ignore for now. But maybe a Future
        # These are mandatory switches, so can't be ignored. Set Prob = 0.
        f.write('FARSITE_SPOT_PROBABILITY: 0.0\n')
        f.write('FARSITE_SPOT_IGNITION_DELAY: 0\n')
        f.write('FARSITE_MINIMUM_SPOT_DISTANCE: 0\n')

        # 8. Acceleration
        f.write('FARSITE_ACCELERATION_ON: {}'.format( '1' if config.farsite_acceleration == 'Yes' else '0' ))

        logging.debug("Making Farsite Input file complete.")

    finally:
        f.close()

def createFarsiteCommandFile(command_filename, lcp_filename, inputs_filename, ignitions_filename, output_dir,
                             output_files_prefix, output_type=1, barrier_filename=0):
    '''
        Create a TestFarsite command file

        TestFARSITE Usage:
        TestFARSITE [commandfile]
        Where:
                [commandfile] is the path to the command file.
        The command file contains command lines for multiple Farsite runs, each run's command on a seperate line.
        Each command expects six parameters, all required
        [LCPName] [InputsFileName] [IgnitionFileName] [BarrierFileName] [outputDirPath] [outputsType]
        Where:
                [LCPName] is the path to the Landscape File
                [InputsFileName] is the path to the FARSITE Inputs File (ASCII Format)
                [IgnitionFileName] is the path to the Ignition shape File
                [BarrierFileName] is the path to the Barrier shape File (0 if no barrier)
                [outputDirPath] is the path to the output files base name (no extension)
                [outputsType] is the file type for outputs (0 = both, 1 = ASCII grid, 2 = FlamMap binary grid
                :param output_files_prefix:
    '''

    logging.debug('Making Farsite Command file "{0}"'.format(command_filename))

    f = open(command_filename, 'w')

    # DEVNOTE: We assume we're running on a Windows machine, as Farsite is only PC/Windows based (?)
    # DEVNOTE: It appears that Farsite command file does NOT support spaces in file paths, or wrapping with quotes, so convert to Windows short name
    f.write('{0} {1} {2} {3} {4} {5}'.format(
        getShortName(lcp_filename),
        getShortName(inputs_filename),
        getShortName(ignitions_filename),
        0 if barrier_filename ==0 else getShortName(barrier_filename),
        getShortName(output_dir) + "\\" + output_files_prefix,
        output_type))
    f.close()


def getShortName(filename):
    '''
    Get the Short Name of the specified file. This function gets the short path, but maintains the full resolution base filename.

    This is a workaround for an issue that Farsite has with the command file containing blanks in the file paths. We can't go to
    full 8.3 syntax, because this confuses dealing with Shapefiles. We were having issues with the 3rd Ignition Points file
    always gave us grief, no matter what the name.

    This is required because:
    1) The command file wont support quotes around file paths that contains spaces. So we need a way to remove spaces, thus Short Names
    2) Unfortunately Short Names aren't prefix consistent. So the short name prefix of FileName.shp isnt neccessarily the same as Filename.dbf.
    Ex:
        IT69BF~1.DBF It0001-Ts2028-ignitionPtsFile.dbf
        IT3ED5~1.PRJ It0001-Ts2028-ignitionPtsFile.prj

    :param filename: The filename we want to get the short path for
    :return: The absolute path of the file, with the directory of the file expressing in short format, but the base filename itself in full "resolution"
    '''

    file_dir = os.path.dirname(filename)
    return os.path.join(win32api.GetShortPathName(file_dir),os.path.basename(filename))


def runFarsite(command_filename):
    # iii - Invoke Farsite and wait for it to complete the run
    # TestFARSITE SampleCommand.txt

    logging.info('Running Farsite...')

    cmdLine  = '"{0}" "{1}" '.format(FARSITE_EXE_PATH,getShortName(command_filename))
    logging.debug(cmdLine)
    proc = subprocess.call(cmdLine)
    if proc <> 0:
        logging.error("Error calling Farsite:{0}".format(cmdLine))
        sys.exit(1)


    logging.info('Farsite run complete.')


def lcpMake(landscape, elevation_filename, slope_filename, aspect_filename, fuel_filename, canopy_filename, latitude):
    """
    Call the compiled lcpmake.exe c++ code to make the landscape file for Farsite from the spatial attribute files exported
    by ST-Sim and the static spatial files above.
    Example:

        lcpmake -latitude 45 -landscape ashleyTest
            -elevation "D:/FARSITE 4/Ashley/ash_elev.asc"
            -slope "D:/FARSITE 4/Ashley/ash_slope.asc"
            -aspect "D:/FARSITE 4/Ashley/ash_aspect.asc"
            -fuel "D:/FARSITE 4/Ashley/ash_fuel.asc"
            -cover "D:/FARSITE 4/Ashley/ash_canopy.asc"

    :param landscape: The name of the Landscape file (LCP), without extension
    :param elevation_filename: The full absolute name of the Elevation ASCII Grid raster file
    :param slope_filename: The full absolute name of the Slope ASCII Grid raster file
    :param aspect_filename: The full absolute name of the Aspect ASCII Grid raster file
    :param fuel_filename: The full absolute name of the Fuel ASCII Grid raster file
    :param canopy_filename: The full absolute name of the Canopy ASCII Grid raster file
    :return: Nothing

    """

    logging.info('Running LCPMake')

    # Convert the TIF raster files to ASC.
    elevation_filename_asc = convertToAAIGrid(elevation_filename)
    slope_filename_asc = convertToAAIGrid(slope_filename)
    aspect_filename_asc = convertToAAIGrid(aspect_filename)
    fuel_filename_asc = convertToAAIGrid(fuel_filename)
    canopy_filename_asc =  convertToAAIGrid(canopy_filename)

    cmdLine = '{0} -latitude {7} ' \
              '-landscape "{1}" ' \
              '-elevation "{2}" ' \
              '-slope "{3}" ' \
              '-aspect "{4}" ' \
              '-fuel "{5}" ' \
              '-cover "{6}"'.format(LCPMAKE_EXE_PATH,
                                    landscape,
                                    elevation_filename_asc,
                                    slope_filename_asc,
                                    aspect_filename_asc,
                                    fuel_filename_asc,
                                    canopy_filename_asc,
                                    latitude)

    logging.debug(cmdLine)
    proc = subprocess.call(cmdLine)
    if proc <> 0:
        logging.error("Error calling Syncrosim.Console:{0}".format(cmdLine))
        sys.exit(1)

    # Now remove the ASC files as we dont need them anymore
    os.remove(elevation_filename_asc)
    os.remove(elevation_filename_asc + '.aux.xml')
    os.remove(slope_filename_asc)
    os.remove(slope_filename_asc + '.aux.xml')
    os.remove(aspect_filename_asc)
    os.remove(aspect_filename_asc + '.aux.xml')
    os.remove(fuel_filename_asc)
    os.remove(fuel_filename_asc + '.aux.xml')
    os.remove(canopy_filename_asc)
    os.remove(canopy_filename_asc + '.aux.xml')

    logging.info('LCPMake run complete.')


def createZeroValRaster(dest_filename, source_filename):
    '''
        Create a zero value raster, using the same characteristics as the source file ( num_rows, num_cols,...)

        DEVNOTE: To generate a zero value raster using gdal_translate
        gdal_translate sclass_100x100.tif squashed.tif -scale 1 1 0 0
        DEVNOTE: To 'flatten' any raster to a single value use:
        gdal_translate sourcefile.tif dest_file.tif -scale 1 1 final_squash_value final_squash_value
        The above command doesnt honor NODATA values

    '''

    tmp_dir = tempfile.mkdtemp()

    try:

        logging.debug("dest_filename:{0}, source_filename:{1}".format(dest_filename,source_filename))

        # Delete the file it is exists
        if os.path.exists(dest_filename):
            os.remove(dest_filename)

        # Convert the source_filename raster into a Int32 datatype, so we can support NoDataValue of -9999
        tmp_raster = os.path.join(tmp_dir, "zv_raster.tif")
        convertToInt32(source_filename,tmp_raster)

        gdal.UseExceptions()
        srcData = gdal.Open(tmp_raster, gdal.GA_ReadOnly)
        if srcData is None:
            logging.error("Cannot open Source Raster file '{0}'".format(tmp_raster))
            sys.exit(1)

        # TODO: srcData.ReadAsArray() is causing Python to crash. It's probably a gdal/python binding mismatch issue. See if
        # any hints at https: // trac.osgeo.org / gdal / wiki / PythonGotchas

        x = np.array(srcData.ReadAsArray())
        # Just in case NoDataValue is 0, change to -9999.
        if srcData.GetRasterBand(1).GetNoDataValue() == 0.0:
            np.putmask(x, x == 0, -9999)

            np.putmask(x, x > 0, 0)


        # we already have the raster with exact parameters that we need
        # so we use CreateCopy() method instead of Create() to save our time
        rasterFormat = "GTiff"
        driver = gdal.GetDriverByName(rasterFormat)
        destData = driver.CreateCopy(dest_filename, srcData, 0)
        band = destData.GetRasterBand(1)
        # Change NoDataValue  to -9999.
        band.SetNoDataValue(-9999)
        band.WriteArray(x)
        logging.debug('Created new Zero Value Raster "{0}"'.format(dest_filename))
        destData = None
        srcData = None

    finally:
        # Clean up the temp files
        shutil.rmtree(tmp_dir)
        pass


def createOneValRaster(dest_filename, source_filename):
    '''
        Create a One value raster, using the same characteristics as the source file ( num_rows, num_cols,...)
    '''

    # Delete the file it is exists
    if os.path.exists(dest_filename):
        os.remove(dest_filename)

    gdal.UseExceptions()
    srcData = gdal.Open(source_filename, gdal.GA_ReadOnly)
    if srcData is None:
        logging.error("Cannot open Source Raster file '{0}'".format(source_filename))
        sys.exit(1)

    # TODO: srcData.ReadAsArray() is causing Python to crash. It's probably a gdal/python binding mismatch issue. See if
    # any hints at https: // trac.osgeo.org / gdal / wiki / PythonGotchas

    x = np.array(srcData.ReadAsArray())
    np.putmask(x, x > 0, 1)

    # we already have the raster with exact parameters that we need
    # so we use CreateCopy() method instead of Create() to save our time
    rasterFormat = "GTiff"
    driver = gdal.GetDriverByName(rasterFormat)
    destData = driver.CreateCopy(dest_filename, srcData, 0)
    destData.GetRasterBand(1).WriteArray(x)
    logging.debug('Created new One-value Raster "{0}"'.format(dest_filename))
    destData = None
    srcData = None

def convertFireIntensityRaster(reference_raster_filename, src_intensity_filename, src_ignitions_filename, converted_filename):
    '''
        Convert the Fire Intensity Raster generated by Farsite into a Transition Spatial Multiplier (TSM)
        raster suitable for import into Syncrosim. Use the Fire ignitions raster to mask the intensity.
    '''

    # DEVNOTE: FUTURE:
    # Then convert different fire intensities to different fire transition types (will need a crosswalk between continuous
    # fire intensity and fire transition type - i.e., low, mid high severity).
    # i. - Generate a spatial multiplier for each fire transition type according to the fire intensity of each cell.
    # DEVNOTE: END OF FUTURE

    reference_raster = gdal.Open(reference_raster_filename, gdal.GA_ReadOnly)
    if reference_raster is None:
        logging.error("Cannot open Farsite Reference Raster file '{0}'".format(reference_raster_filename))
        sys.exit(1)

    cols = reference_raster.RasterXSize
    rows = reference_raster.RasterYSize
    # reference_raster = None

    intensity_raster = gdal.Open(src_intensity_filename, gdal.GA_ReadOnly)
    if intensity_raster is None:
        logging.error("Cannot open Farsite Fire Intensity Raster file '{0}'".format(src_intensity_filename))
        sys.exit(1)

    raster_intensity = intensity_raster.ReadAsArray()
    x = np.array(raster_intensity)
    if (rows ,cols) != x.shape :
        xrows, xcols = x.shape
        logging.warning(
            "The Fire Intensity raster was not of the expected size ({},{}) vs ({},{}).".format(
                xrows, xcols, rows, cols))
        if cols > xcols:
            logging.warning("Resizing Fire Intensity raster by adding columns.")
            x = np.hstack((x, np.zeros((x.shape[0], cols - xcols), dtype=x.dtype)))
        else:
            logging.error("Unable to process existing Fire Intensity raster")
            sys.exit(1)

    # Convert cell value > 0 to 1. Any other value, including NO_DATA_VALUE,  = 0
    np.putmask(x, x > 1, 1)
    np.putmask(x, x < 0, 0)

    # Mask the Intensity raster with the Ignitions raster
    ignition_raster = gdal.Open(src_ignitions_filename, gdal.GA_ReadOnly)
    if ignition_raster is None:
        logging.error("Cannot open Farsite Fire Ignitions Raster file '{0}'".format(src_ignitions_filename))
        sys.exit(1)
    raster_ignitions = ignition_raster.ReadAsArray()
    y = np.array(raster_ignitions)

    if (rows ,cols) != y.shape :
        yrows, ycols = y.shape
        logging.warning(
            "The Fire Ignitions raster was not of the expected size ({},{}) vs ({},{}).".format(
                yrows, ycols, rows, cols))
        if cols > ycols:
            logging.warning("Resizing Fire Ignitions raster by adding columns.")
            y = np.hstack((y, np.zeros((y.shape[0], cols - ycols), dtype=y.dtype)))
        else:
            logging.error("Unable to process existing Fire Ignitions raster")
            sys.exit(1)


    # Test that the Ignition  and Intensity raster as the same size - we've seen cases where Farsite produces slightly mismatched
    # raster size, resulting in putmask cratering
    if x.size <> y.size:
        logging.warning("The Fire Intensity and Ignition rasters are different sizes.")
        sys.exit(1)

    # Set any ignitions pts in the massaged intensity raster
    np.putmask(x, y>=1 ,1)

    # we already have the raster with exact parameters that we need, in the reference raster. Cant use createCopy becuase of the change
    # band size different
    # Refer to array2raster(rasterfn,newRasterfn,array) in https://pcjericks.github.io/py-gdalogr-cookbook/raster_layers.html
    geotransform = reference_raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]

    rasterFormat = "GTiff"
    driver = gdal.GetDriverByName(rasterFormat)
    outRaster = driver.Create(converted_filename, cols, rows, 1, GDT_Int32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(x)
    outband.SetNoDataValue(-9999)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(reference_raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

    logging.debug('Created new Farsite TSM Raster "{0}"'.format(converted_filename))


def convertToAAIGrid(src_filename):
    # We need to convert tif -> ASC before we can use them in LCPMake
    filename_asc = src_filename.replace('.tif', '.asc')
    cmdLine = 'gdal_translate -of "AAIGrid" "{0}" "{1}"'.format(src_filename,filename_asc)
    logging.debug(cmdLine)
    proc = subprocess.call(cmdLine)
    if proc <> 0:
        logging.error("Error calling gdal_translate:{0}".format(cmdLine))
        sys.exit(1)

    return filename_asc

def convertToInt32(src_filename, dest_filename):

    filename_asc = src_filename.replace('.tif', '.asc')
    cmdLine = 'gdal_translate -ot "Int32" "{0}" "{1}"'.format(src_filename,dest_filename)
    logging.debug(cmdLine)
    proc = subprocess.call(cmdLine)
    if proc <> 0:
        logging.error("Error calling gdal_translate:{0}".format(cmdLine))
        sys.exit(1)

    return dest_filename


def generateIgnitionPoints(barrier_raster_file, ignition_pts_shapefile, num_ignitions ):

    # Generate a boundary file from the specified raster

    tmp_dir = tempfile.mkdtemp()

    try:
        # 1st create a zero value raster with the same characteristics as the specified raster
        zv_raster = os.path.join(tmp_dir, "zv_raster.tif")
        createZeroValRaster( zv_raster,barrier_raster_file)

        # gdal_polygonize
        boundary_file = os.path.join(tmp_dir, "boundary.shp")

        cmdLine = 'gdal_polygonize.bat "{0}" "{1}" -f "ESRI Shapefile"'.format(zv_raster, boundary_file)
        logging.debug(cmdLine)
        proc = subprocess.call(cmdLine)
        if proc <> 0:
            logging.error("Error calling gdal_polygonize:{0}".format(cmdLine))
            sys.exit(1)

        # OK, we've got our boundary file, so lets generate some random points
        createIgnitionPtFile(boundary_file,ignition_pts_shapefile,num_ignitions)
        logging.info('Created Ignition Point file "{0}" with {1} points'.format(ignition_pts_shapefile,num_ignitions))

    finally:
        # Clean up the temp files
        shutil.rmtree(tmp_dir)
        pass

def createIgnitionPtFile(boundary_fn, ignition_points_fn, num_ignition_points):
    """
        Create a new Point Layer containing Randomly placed Ignition points, within the constraints of the Boundary file

    @param boundary_fn: The file name of the Boundary shapefile
    @param ignition_points_fn: The filename of the output file containing the ignition points.
    @return:
    """

    inputDs = ogr.Open(boundary_fn)
    if not inputDs:
        logging.error(("Unable to open input boundary file '{0}'".format(boundary_fn)))
        sys.exit(1)

    inputLyr = inputDs.GetLayer()
    inpSRS = inputLyr.GetSpatialRef()
    (minx, maxx, miny, maxy) = inputLyr.GetExtent()

    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(ignition_points_fn):
        shpdriver.DeleteDataSource(ignition_points_fn)

    if os.path.exists(ignition_points_fn):
        sys.exit("Unable to delete old file '{0}".format(ignition_points_fn))

    output_ds = shpdriver.CreateDataSource(ignition_points_fn)
    if output_ds is None:
        logging.error('Creation of Ignition Points file "{}" failed'.format(ignition_points_fn))
        sys.exit(1)

    pts_lyr = output_ds.CreateLayer('Ignition Points', geom_type=ogr.wkbPoint, srs=inpSRS)
    if pts_lyr is None:
        logging.error("Layer creation failed.")
        sys.exit(1)

    featureDefn = pts_lyr.GetLayerDefn()
    num_created_pts = 0
    while num_created_pts < num_ignition_points:
        ign_pt = ogr.Geometry(ogr.wkbPoint)
        ign_pt.SetPoint_2D(0,random.uniform(minx, maxx), random.uniform(miny, maxy))

        # Make sure the new proposed point falls within valid area of Boundary shapefile
        inputLyr.SetSpatialFilter(ign_pt)
        if inputLyr.GetFeatureCount()==0:
            logging.debug('Skipped creating a Ignition point because outside of Boundary layer')
            continue

        num_created_pts +=1
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(ign_pt)
        pts_lyr.CreateFeature(outFeature)

        outFeature.Destroy()

    # TODO: Create a PRJ file for this shapefile
    # pu.createPrjFile(ignition_points_fn,inpSRS)

    inputLyr = None
    inputDs = None

    pts_lyr = None
    output_ds = None


def compareRasterRowsCols(reference_raster_filename, comparison_raster_filename):
    """
        Verify that the raster file specified has the same number of rows and columns as the reference raster.

    @param reference_raster_filename: The filename of the raster we're using as reference
    @:param comparison_raster_filename: The filename of the raster we're comparing the reference to
    @return: True is rows and cols the same
    """

    gdal.UseExceptions()
    raster = gdal.Open(reference_raster_filename, gdal.GA_ReadOnly)
    if raster is None:
        logging.error("Cannot open Reference Raster file '{0}'".format(reference_raster_filename))
        sys.exit(1)

    num_rows = raster.RasterYSize
    num_cols = raster.RasterXSize
    raster = None

    raster = gdal.Open(comparison_raster_filename, gdal.GA_ReadOnly)
    if raster is None:
        errMsg = "Cannot open Comparison Raster file '{0}'".format(comparison_raster_filename)
        logging.error(errMsg)
        sys.exit(errMsg)

    if num_rows != raster.RasterYSize :
        return False

    if num_cols != raster.RasterXSize:
        return False

    return True

def verifyRasterMetadata(config):
    """
        Verify that the raster file specified in the config object have sufficiently matching metadata. If not, do a sys.exit()

    @param config: The configuration object, containing the file names for all the input files
    @return:
    """

    logging.info("Verifying Raster Metadata...")

    gdal.UseExceptions()
    raster = gdal.Open(config.primaryStratumFile, gdal.GA_ReadOnly)
    if raster is None:
        logging.error("Cannot open Source Raster file '{0}'".format(config.primaryStratumFile))
        sys.exit(1)

    num_rows = raster.RasterYSize
    num_cols = raster.RasterXSize
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]

    raster = None

    files = [config.aspect_raster_file, config.elevation_raster_file, config.slope_raster_file]
    for file in files:
        raster = gdal.Open(file, gdal.GA_ReadOnly)
        if raster is None:
            errMsg = "Cannot open Source Raster file '{0}'".format(config.primaryStratumFile)
            logging.error(errMsg)
            sys.exit(errMsg)

        geotransform = raster.GetGeoTransform()

        if num_rows != raster.RasterYSize:
            errMsg = "The raster '{0}' does not match the Number of Rows of the Primary Stratum raster specified in Initial Conditions Spatial.".format(file)
            logging.error(errMsg)
            sys.exit(errMsg)

        if num_cols != raster.RasterXSize:
            errMsg ="The raster '{0} does not match the Number of Columns of the Primary Stratum raster specified in Initial Conditions Spatial.".format(file)
            logging.error(errMsg)
            sys.exit(errMsg)

        # X Origin. Test no more than 1/2 of pixel width
        diff = abs(originX - geotransform[0])
        if diff > (pixelWidth / 2.0):
            errMsg ="The raster '{0}' does not match the X Origin of the Primary Stratum raster specified in Initial Conditions Spatial.".format(file)
            logging.error(errMsg)
            sys.exit(errMsg)

        # Y Origin. Test no more than 1/2 of pixel height
        diff = abs(originY - geotransform[3])
        if diff > abs(pixelHeight / 2.0):
            diff = abs(originY - geotransform[3])
            errMsg ="The raster '{0}' does not match the Y Origin of the Primary Stratum raster specified in Initial Conditions Spatial.".format(file)
            logging.error(errMsg)
            sys.exit(errMsg)

        # Pixel Width. Test for 1% diff
        diff  = abs(pixelWidth - geotransform[1])
        if abs(diff / pixelWidth) > .01:
            errMsg ="The raster '{0}' does not match the Pixel Width of the Primary Stratum raster specified in Initial Conditions Spatial.".format(file)
            logging.error(errMsg)
            sys.exit(errMsg)

        # Pixel Height. Test for 1% diff
        diff = abs(pixelHeight - geotransform[5])
        if abs(diff / pixelHeight) > .01:
            errMsg = "The raster '{0}' does not match the Pixel Height of the Primary Stratum raster specified in Initial Conditions Spatial.".format(file)
            logging.error(errMsg)
            sys.exit(errMsg)

def cleanRuntimeFiles(farsite_output_dir):
    shutil.rmtree(farsite_output_dir)

if __name__ == '__main__':
    pass
    # Test
    # createIgnitionPtFile('D:/ApexRMS/A165/FarsiteSTSim/Test Data/STSim/Small Testing Library/FarsiteTesting.ssim.input/Scenario-1/STSim_InitialConditionsSpatial/sqaushed2.shp',
    #                      'd:/temp/test1.shp',1000)

    # convertFireIntensityRaster("D:\ApexRMS\Syncrosim Data File\BuffleTest\Buffelgrass.ssim.input\Scenario-1190\STSim_InitialConditionsSpatial\RMD_Strata_QuarterHa_Filt100.tif",
    # "D:\ApexRMS\Syncrosim Data File\BuffleTest\Buffelgrass.ssim.output\Scenario-1186\Spatial\Farsite\It0001-Ts2015-FARSITE_Intensity.asc",
    # "D:\ApexRMS\Syncrosim Data File\BuffleTest\Buffelgrass.ssim.output\Scenario-1186\Spatial\Farsite\It0001-Ts2015-FARSITE_Ignitions.asc",
    # "d:\Temp\conv.tif")
    # createZeroValRaster("d:/temp/zero.tif","D:\ApexRMS\Syncrosim Data File\BuffleTest\Buffelgrass.ssim.input\Scenario-1190\STSim_InitialConditionsSpatial\RMD_Strata_QuarterHa_Filt100.tif")
