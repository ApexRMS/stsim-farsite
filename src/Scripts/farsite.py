# coding=utf-8
import logging
import os
import sys
import numpy
import config as cc
from farsiteUtils import createZeroValRaster, convertFireIntensityRaster, convertToAAIGrid, generateIgnitionPoints, \
    createOneValRaster, cleanRuntimeFiles, verifyRasterMetadata,compareRasterRowsCols


def main(argv):

    # Documentation from : https://docs.google.com/document/d/1dYQgkw-VGhacOG71v15SYbmy-iNbZ_1HmaYioeYc60M/edit?pli=1#

    # Changes specific to linking Farsite to ST-Sim
    # Note, there is a very good description of the Farsite model including inputs and outputs at:
    # http://www.fs.fed.us/rm/pubs/rmrs_rp004.pdf
    #

    from farsiteUtils import makeFarsiteInputFile, createFarsiteCommandFile, runFarsite, lcpMake

    # Log to file
    #DEVNOTE: Future - Would be nice to put it in the Scenario Output directory.
    # DEVNOTE: Future - Add code to suport external logging config https://docs.python.org/2.6/library/logging.html
    logging.basicConfig(filename='farsite.py.log', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add console logging as well
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logging.getLogger('').addHandler(ch)


    logging.info('Entering Farsite Python script')

    try:

        config = cc.Config(argv)

        logging.info('Running Farsite script for Iteration {0}, Timestep {1} for Project {4},Scenario {2}, Library "{3}"'
                     .format(config.iteration, config.timestep, config.scenarioId, config.library, config.projectId))

        # Verify that the raster input files are sufficiently matched
        verifyRasterMetadata(config)

        # Create the Data dir is it doesnt exits. Helps with standalone testing. STSim typically removes it after each call.
        # Files that Syncrosim imports after this script is run must be in this directory.
        if not os.path.exists(config.data_dir):
            os.makedirs(config.data_dir)

        # DEVNOTE: Although old-school naming convention, this is internal to this "module", so we can still use
        # it.
        file_prefix = 'It{0:04d}-Ts{1:04d}-'.format(config.iteration,config.timestep)

        stateAttrSpatialOutputDir = os.path.join(config.getScenarioOutputPath(),
                                                 cc.DATASHEET_OUTPUT_SPATIAL_STATE_ATTR)

        # Create a subdirectory in output just for Farsite files.
        farsiteOutputDir = os.path.join(config.getScenarioOutputPath(), 'STSim_OutputSpatialFarsite')
        if not os.path.exists(farsiteOutputDir):
            os.makedirs(farsiteOutputDir)

        # Based on the Timestep frequency, should we process this timestep
        if not config.isOutputTimestep(config.timestep):

            # We dont need to do the full Farsite treatment, but we need to generated a Zero value raster
            #  that will be applicable till the next "real" timestep
            # See if we created a "real" record for the previous timestep
            if config.isOutputTimestep(config.timestep - 1):
                logging.info('Creating Zero Value Raster for skipped timestep {0}'.format(config.timestep))
                # Create a 0 value raster for TSM's.
                tsm_filename = "zeroValue.tif"
                tsm_filename = os.path.join(farsiteOutputDir, tsm_filename)
                if not os.path.exists(tsm_filename):
                    createZeroValRaster(tsm_filename, config.primaryStratumFile)
            else:
                logging.info('Skipping timestep {0}'.format(config.timestep))
                tsm_filename = ''

        else:
            # f. Determine the number of ignitions for the timestep (sampled from a poisson probability distribution - conduct
            # sensitivity analysis to the mean number of ignitions per year.
            if config.dist_for_num_ignitions == 'Fixed':
                num_ignitions = config.num_ignitions_per_timestep
            else:
                num_ignitions = numpy.random.poisson(config.num_ignitions_per_timestep)

            if num_ignitions == 0:
                logging.info('No ignitions this timestep.')
                # Create a 0 value raster for TSM's.
                tsm_filename = "zeroValue.tif"
                tsm_filename = os.path.join(farsiteOutputDir, tsm_filename)

                if not os.path.exists(tsm_filename):
                    #TODO: Something in this function is causing python to crash.
                    createZeroValRaster(tsm_filename,config.primaryStratumFile)

            else:

                # 6.) For each state class (and possibly by age range) users will specify state attribute values for:
                # a. - fuel model (integer id - see http://www.fs.fed.us/rm/pubs/rmrs_gtr153.pdf)

                # Figure out the name of the SA Raster file output by Syncrosim at the end of previous timestep
                sa_fuel_model_filename = config.db.getOutputSpatialRaster(config.scenarioId,
                                                                          cc.DATASHEET_OUTPUT_SPATIAL_STATE_ATTR,
                                                                          config.iteration, config.timestep - 1, config.sa_fuel_model_name,
                                                 'StateAttributeTypeID')

                if sa_fuel_model_filename ==None:
                    logging.error(
                        'The expected Fuel Model State Attribute raster file cannot be found in Output Spatial datasheet.')
                    sys.exit(1)

                sa_fuel_model_filename = os.path.join(stateAttrSpatialOutputDir, sa_fuel_model_filename)
                if not os.path.exists(sa_fuel_model_filename):
                    logging.error('The expected Fuel Model State Attribute raster file "{0}" can not be found.'.format(sa_fuel_model_filename))
                    sys.exit(1)

                # Canopy cover class (integer id - 1: 1-20%, 2: 21-50%, 3: 50-80%, and 4: 81-100%)
                if config.sa_canopy_cover_id:
                    # Figure out the name of the SA Raster file output by Syncrosim  at the end of previous timestep
                    sa_canopy_cover_filename = config.db.getOutputSpatialRaster(config.scenarioId,
                                                                                cc.DATASHEET_OUTPUT_SPATIAL_STATE_ATTR,
                                                                                config.iteration, config.timestep - 1,
                                                                                config.sa_canopy_cover_name,
                                                                              'StateAttributeTypeID')
                    if sa_canopy_cover_filename ==None:
                        logging.error(
                            'The expected Canopy Cover State Attribute raster file cannot be found in Output Spatial datasheet.')
                        sys.exit(1)

                    sa_canopy_cover_filename = os.path.join(stateAttrSpatialOutputDir, sa_canopy_cover_filename)
                    if not os.path.exists(sa_canopy_cover_filename):
                        logging.error(
                            'The expected Canopy Cover State Attribute raster file "{0}" can not be found.'.format(sa_canopy_cover_filename))
                        sys.exit(1)

                else:
                    # If Canopy Cover State Attribute not spec'd, then generate a 1-value raster to use in its place.
                    sa_canopy_cover_filename = os.path.join(farsiteOutputDir, 'canopy_cover_1.tif')
                    createOneValRaster(sa_canopy_cover_filename,config.primaryStratumFile)

                # FUTURE: c. -  other possible variables - fuel moisture - can be time varying.
                # STATE_ATTRIBUTE_NAME_FUEL_MOISTURE = 'Farsite Fuel Moisture'
                # sa_fuel_moisture_id = syn.getStateAttributeId(config.projectId, STATE_ATTRIBUTE_NAME_FUEL_MOISTURE)

                # TODO: We should determine latitide from the Primary Stratum file
                latitude = 45

                # d. - Call the compiled lcpmake.exe make the landscape file for Farsite from the spatial attribute files exported
                farsite_lcp_name = file_prefix + "farsiteSTSIM"
                lcp_name = os.path.join(farsiteOutputDir, farsite_lcp_name)
                lcp_filename = lcp_name + '.lcp'
                lcpMake(lcp_name,
                        config.elevation_raster_file,
                        config.slope_raster_file,
                        config.aspect_raster_file,
                        sa_fuel_model_filename,
                        sa_canopy_cover_filename,
                        latitude
                        )

                # e. -Find additional Optional static spatial inputs such as the barrier shp file.
                # VECTOR_FILENAME_BARRIER = "barrier.shp"

                # i. - Generate the ignition point shape file by sampling a num_ignitions random point from the landscape.
                # DEVNOTE: See if we can assign a start_date to each ignition point.
                # TODO: Make sure its NOT a NoData value cell
                # TODO: Future :should this be weighted with a spatial multiplier somehow?
                FARSITE_IGNITION_PTS_FILENAME = file_prefix+'ignitionPtsFile.shp'
                ignition_file = os.path.join(farsiteOutputDir, FARSITE_IGNITION_PTS_FILENAME)
                generateIgnitionPoints(config.primaryStratumFile, ignition_file, num_ignitions)

                # ii- Generate the Farsite input file ...
                FARSITE_INPUTS_FILENAME = file_prefix+'farsiteInputs.txt'
                inputs_filename = os.path.join(farsiteOutputDir, FARSITE_INPUTS_FILENAME)
                makeFarsiteInputFile(inputs_filename,ignition_file, config)

                FARSITE_COMMAND_FILENAME = file_prefix+'command.txt'
                command_file = os.path.join(farsiteOutputDir, FARSITE_COMMAND_FILENAME)
                FARSITE_FILES_PREFIX = file_prefix + 'FARSITE'
                createFarsiteCommandFile(command_file, lcp_filename, inputs_filename, ignition_file, farsiteOutputDir,
                                         FARSITE_FILES_PREFIX)

                runFarsite(command_file)

                # iv - Get the fire intensity raster output file for this fire
                # DEVNOTE: The Fire intensity Raster is XXXX_Intensity.asc, where XXXX was specified as part of the Command file Output Dir
                INTENSITY_RASTER_FILENAME = FARSITE_FILES_PREFIX + '_Intensity.asc'
                fire_intensity_filename =  os.path.join(farsiteOutputDir, INTENSITY_RASTER_FILENAME)
                if not os.path.exists(fire_intensity_filename):
                    logging.error(
                        'The expected Fire Intensity raster file "{0}" can not be found.'.format(
                            fire_intensity_filename))
                    sys.exit(1)

                IGNITIONS_RASTER_FILENAME = FARSITE_FILES_PREFIX + '_Ignitions.asc'
                fire_ignitions_filename =  os.path.join(farsiteOutputDir, IGNITIONS_RASTER_FILENAME)
                if not os.path.exists(fire_ignitions_filename):
                    logging.error(
                        'The expected Fire Ignitions raster file "{0}" can not be found.'.format(
                            fire_ignitions_filename))
                    sys.exit(1)


                # Save the new raster value to a new TSM file
                tsm_filename = file_prefix+ 'tg-{}.tif'.format(config.transition_group_id)
                tsm_filename = os.path.join(config.data_dir, tsm_filename)
                convertFireIntensityRaster(config.primaryStratumFile, fire_intensity_filename,fire_ignitions_filename,tsm_filename)

                # Make sure that Farsite produced an output with the same number of row and columns.
                # If not, then somethng really not OK
                if not compareRasterRowsCols(config.primaryStratumFile,tsm_filename):
                    logging.error("The generated TSM raster size did not match that of the Primary Stratum raster, so a Zero Value raster will be used instead.")
                    sys.exit(1)

        if tsm_filename <> '':
            # Append to existing transition spatial multipliers to include these multipliers.
            config.db.putTransitionSpatialMult(config.data_dir, config.scenarioId, config.iteration, config.timestep,
                                               config.transition_group_name, config.transition_multiplier_type_name, tsm_filename)

        # Clean up Farsite intermediate product
        if not (config.save_intermediate_files == 'Yes'):
            logging.info('Removing Farsite intermediate file at "{}"'.format(farsiteOutputDir))
            cleanRuntimeFiles(farsiteOutputDir)

        logging.info('Successful completion of script.')

    except Exception as ex:
        logging.exception("message")

    finally:
        logging.info('Exiting Farsite Python script')


if __name__ == '__main__':

    main(sys.argv[1:])
    sys.exit(0)