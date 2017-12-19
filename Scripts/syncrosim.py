import logging
import os
import subprocess
import tempfile
import csv
import shutil

from subprocess import call

class SynrosimDB:

    lib_filename = ''
    # ssim_version = 0
    # isValidDB = False
    # isValidVersion = False
    __folders = []
    syncrosim_console_path = ''


    def __init__(self,ssimFilename,console_root):
        self.lib_filename = ssimFilename

        # Gotta do this before anything else, as this points to Console exe, which most/all other functions rely on.
        self.syncrosim_console_path = os.path.join(console_root,'SyncroSim.Console.exe')

        fld = self.getFolders()
        if fld:
            self.__folders = fld[0]



    def getModels(self):
  # --models         Lists the available models
        cmdLine = '"{0}" --lib="{1}" --list --models'.format(self.syncrosim_console_path, self.lib_filename)
        print cmdLine
        subprocess.call(cmdLine)

    def getConsoles(self):
  # --consoles       Lists the available consoles
        cmdLine = '"{0}" --lib="{1}" --list --consoles'.format(self.syncrosim_console_path, self.lib_filename)
        print cmdLine
        subprocess.call(cmdLine)

    def getLibrary(self):
  # --library        Lists information about a library
        cmdLine = '"{0}" --lib="{1}" --list --library'.format(self.syncrosim_console_path, self.lib_filename)
        print cmdLine
        subprocess.call(cmdLine)
        # TODO: Note that this doesnt return a CSV file

    def getScenarios(self, project_id = None):
        '''
            Get a list of the Scenarios in the library.

            :param project_id: (Optional ) The project we want the scenarios for
        '''

        # Create a temp dir for syncrosim.console to store the export file to. Get's around having to predelete the file all the time
        tmp_dir = tempfile.mkdtemp()
        export_filename = os.path.join(tmp_dir, "export.csv")

        # --scenarios      Lists the scenarios in a library
        cmdLine = '"{0}" --lib="{1}" --list --scenarios --file="{2}"'.format(self.syncrosim_console_path, self.lib_filename,export_filename)

        if project_id <> None:
            cmdLine += ' --pid={0}'.format(project_id)

        proc = subprocess.call(cmdLine)
        if proc <> 0:
            logging.error("Error calling Syncrosim.Console:{0}".format(cmdLine))
            return None

        with open(export_filename, 'rb') as f:
            reader = csv.DictReader(f)
            lst = list(reader)

        # Clean up the temp file
        shutil.rmtree(tmp_dir)
        return lst



    def getScenarioId(self,project_id,scenarioName):
        '''
        Get the Scenario ID for the specified Scenario Name

        :param project_id: The project of interest
        :param scenarioName: The name of the Scenario that we would like the ID for
        '''

        scens = self.getScenarios(project_id)
        for row in scens:
            if row['Name'] ==scenarioName:
                return row['ScenarioID']
        else:
            return None


    def getDatafeeds(self):
        # --datafeeds      Lists the data feeds in a library
        cmdLine = '"{0}" --lib="{1}" --list --datafeeds'.format(self.syncrosim_console_path, self.lib_filename)
        print cmdLine
        subprocess.call(cmdLine)

    def getScenarioDependencies(self,scenarioId):
        # --dependencies   Lists the dependencies for a scenario
        cmdLine = '"{0}" --lib="{1}" --list --dependencies -sid={2}'.format(self.syncrosim_console_path, self.lib_filename, scenarioId)
        print cmdLine
        subprocess.call(cmdLine)

    def getDataProviders(self):
        # --dataproviders  Lists the available data providers
        cmdLine = '"{0}" --lib="{1}" --list --dataproviders'.format(self.syncrosim_console_path, self.lib_filename)
        print cmdLine
        subprocess.call(cmdLine)


    def getTransitionGroups(self,projectId):
        '''
            Get a list of Transition Groups for the specified Project

            :param: The ID of the Project of Interest

        '''
        sheet = "STSim_TransitionGroup"
        return self.getProjectDataSheet(sheet, projectId)


    def getTransitionGroupId(self, projectId,transitionGroupName):
        '''
            Get the ID of the specified Transition Group

            :param projectId: The project of interest
            :param transitionGroupName: The name of the Transition Group of interest
        '''
        sheet = "STSim_TransitionGroup"
        pk_name = "TransitionGroupID"
        return self.getDataSheetVal(projectId, sheet, 'Name', transitionGroupName, pk_name)


    def getTransitionMultiplierTypeId(self, projectId, transitionMultiplierTypeName):
        '''
            Get the ID of the specified Transition Multiplier Type

            :param projectId: The project of interest
            :param transitionMultiplierTypeName: The name of the Transition Multiplier Type of interest
        '''
        sheet = "STSim_TransitionMultiplierType"
        pk_name = "TransitionMultiplierTypeID"
        return self.getDataSheetVal(projectId, sheet, 'Name', transitionMultiplierTypeName, pk_name)

    def getStockTypes(self,projectId):
        '''
            Get a list of Stock Types for the specified project

            :param projectId: The project of interest

        '''
        sheet = "SF_StockType"
        return self.getProjectDataSheet(sheet, projectId)

    def getFlowTypes(self,projectId):
        '''
            Get a list of Flow Types for the specified project

            :param projectId: The project of interest

        '''
        sheet = "SF_FlowType"
        return self.getProjectDataSheet(sheet, projectId)


    def getProjects(self):
        '''
            Get a list of Projects in the current library
        '''

        # Create a temp dir for syncrosim.console to store the export file to. Get's around having to predelete the file all the time
        tmp_dir =tempfile.mkdtemp()
        export_filename = os.path.join(tmp_dir,"projects.csv")

        cmdLine = '"{0}" --lib="{1}" --list --projects --csv --file="{2}"'.format(self.syncrosim_console_path, self.lib_filename, export_filename)
        proc = subprocess.call(cmdLine)
        if proc <>0:
            logging.error("Error calling Syncrosim.Console:{0}".format(cmdLine))
            return None


        with open(export_filename, 'rb') as f:
            reader = csv.DictReader(f)
            lst = list(reader)

        # Clean up the temp file
        shutil.rmtree(tmp_dir)
        return lst



    def getProjectId(self,name):
        '''
            Get the ID of the project specified by name

            :param name: The name of the project of interest

        '''

        rows= self.getProjects()

        for row in rows:
            if row['Name'] == name:
                return row['ProjectID']
        else:
            return None


    def getStratum(self,projectId):
        '''
            Get a list of Stratum for the specified project

            :param projectId: The project of interest

        '''

        sheet = 'STSim_Stratum'
        return self.getProjectDataSheet(sheet, projectId)


    def getStateAttributes(self,projectId):
        '''
            Get a list of State Attributes for the specified project

            :param projectId: The project of interest

        '''

        sheet = 'STSim_StateAttributeType'
        return self.getProjectDataSheet(sheet, projectId)


    def getStateAttributeId(self, projectId, saName):
        '''
            Get the ID of the specified State Attribute

            :param projectId: The project of interest
            :param saName: The name of the State Attribute of interest
        '''
        sheet = 'STSim_StateAttributeType'
        pk_name = "StateAttributeTypeID"
        return self.getDataSheetVal(projectId, sheet, 'Name', saName, pk_name)


    def getOutputSpatialRaster(self, scenarioId, dsName, iteration, timestep, id, pkName):
        '''
            Get the raster name from the specified Output Spatial datasheet

            :param scenarioId: The scenario of interest
            :param dsName : The name of the datasheet we're extracting the raster from
            :param iteration: The iteration of interest
            :param timestep: The timestep of interest
            :param id: The ID value of interest. Can typically be the lookup value. ie 'Invaded Cover' instead of 156.
            :param pkName: The name of the PK value column ( ie 'StateAttributeTypeID")
        '''

        rows = self.getScenarioDataSheet(dsName, scenarioId)
        if rows == None or len(rows) == 0:
            logging.error('Could not find entries for Datasheet {1} for Scenario {0}'.format(
                scenarioId,dsName))
            return None

        #     Now we need to loop thru the datasheet contents looking for appropriate iteration, timesteps, id
        for row in rows:
            print row
            if row['Iteration'] == str(iteration) and row['Timestep']== str(timestep) and row[pkName]== str(id):
                return row['Filename']

        else:
            return None


    def getTransitionAttributes(self, projectId):
        '''
            Get a list of Transition Attributes for the specified project

            :param projectId: The project of interest

        '''

        sheet = 'STSim_TransitionAttributeType'
        return self.getProjectDataSheet(sheet, projectId)


    def getTransitionAttributeId(self, projectId, name):
        '''
            Get the ID of the specified Transition Attribute

            :param projectId: The project of interest
            :param name: The name of the Transition Attribute of interest
        '''
        sheet = 'STSim_TransitionAttributeType'
        pk_name = "TransitionAttributeTypeID"
        return self.getDataSheetVal(projectId, sheet, 'Name', name, pk_name)


    def getLibDataSheet(self, data_sheet_name):

        return self.__getDataSheet(data_sheet_name)

    def getProjectDataSheet(self, data_sheet_name, project_id):

        return self.__getDataSheet(data_sheet_name, project_id)


    def getScenarioDataSheet(self, data_sheet_name, scenario_id):

        return self.__getDataSheet(data_sheet_name, None, scenario_id)


    def __getDataSheet(self, data_sheet_name, project_id = None,scenario_id = None):

        # Ex:SyncroSim.Console.exe" --lib="libname.ssim" --export --sheet=ST_StateAttributeTypeID --file=temp.csv --pid=256
        tmp_dir = tempfile.mkdtemp()
        export_filename = os.path.join(tmp_dir, "export.csv")


        cmdLine = '"{0}" --lib="{1}" --export --sheet="{2}" --file="{3}" - --includepk'.format(self.syncrosim_console_path,
                                                                                       self.lib_filename,
                                                                                       data_sheet_name,
                                                                                       export_filename)
        if project_id <> None:
            cmdLine += ' --pid={0}'.format(project_id)

        if scenario_id <> None:
            cmdLine += ' --sid={0}'.format(scenario_id)

        proc = subprocess.call(cmdLine)
        if proc<> 0:
            logging.error("Problems exporting. cmd:{0}".format(cmdLine))
            return None

        with open(export_filename, 'rb') as f:
            reader = csv.DictReader(f)
            lst = list(reader)

        # Clean up the temp file
        shutil.rmtree(tmp_dir)
        return lst


    def getDataSheetVal(self, project_id, data_sheet_name, key_name, key_val, val_name):

        rows = self.__getDataSheet(data_sheet_name, project_id)
        for row in rows:
            if row[key_name] == key_val:
                return row[val_name]

        else:
            return None


    def putDataSheet(self, data_sheet_name, scenario_id):

        # SyncroSim.Console.exe --lib="D:...ssim
        # " --export --sheet="STSim_TransitionSpatialMultiplier" --file="d:\temp\tsm_export2.csv" --sid=3290

        # Ex:SyncroSim.Console.exe" --lib="libname.ssim" --import --sheet=ST_StateAttributeTypeID --file=temp.csv --sid=256

        tmp_dir = tempfile.mkdtemp()
        export_filename = os.path.join(tmp_dir, "export.csv")

        export_filename = 'd:/temp/tsm_export4.csv'

        # TODO: Turn off --append for now as getting unique constraint errors on compound key
        cmdLine = '"{0}" --lib="{1}" --import --sheet="{2}" --file="{3}" --sid={4}'.format(self.syncrosim_console_path,
                                                                                               self.lib_filename,
                                                                                               data_sheet_name,
                                                                                               export_filename,
                                                                                               scenario_id)
        # if project_id <> None:
        #     cmdLine += ' --pid={0}'.format(project_id)

        proc = subprocess.call(cmdLine)
        if proc <> 0:
            logging.error("Problems importing. cmd:{0}".format(cmdLine))
            return None

        # with open(export_filename, 'rb') as f:
        #     reader = csv.DictReader(f)
        #     lst = list(reader)
        #
        # # Clean up the temp file
        # shutil.rmtree(tmp_dir)
        # return lst


    def getFolders(self):
        sheet = 'SSim_Files'
        return self.getLibDataSheet(sheet)


    def getLibraryRoot(self):
        return  os.path.dirname(self.lib_filename)

    # def getLibraryOutputPath(self):
    #
    #     if self.__folders:
    #         outputPath = self.__folders['OutputFolderName']
    #         if outputPath:
    #             return outputPath
    #
    #     # If no Files records, or empty, use Default
    #     outputPath = self.lib_filename + '.output'
    #     return outputPath
    #
    #
    # def getLibraryInputPath(self):
    #
    #     if self.__folders:
    #         inputPath = self.__folders['InputFolderName']
    #         if inputPath:
    #             return inputPath
    #
    #     # If no Files records, or empty, use Default
    #     inputPath = self.lib_filename + '.input'
    #     return inputPath
    #
    #
    # def getLibraryTempPath(self):
    #
    #     if self.__folders:
    #         tempPath = self.__folders['TempFolderName']
    #         if tempPath:
    #             return tempPath
    #
    #     # If no Files records, or empty, use Default
    #     tempPath = self.lib_filename + '.temp'
    #     return tempPath
    #
    # def getScenarioInputPath(self,scenarioId):
    #     return os.path.join(self.getLibraryInputPath(),"Scenario-{0}".format(scenarioId))
    #
    # def getScenarioOutputPath(self,scenarioId):
    #     return os.path.join(self.getLibraryOutputPath(),"Scenario-{0}".format(scenarioId))
    #
    #
    # def getScenarioSpatialOutputPath(self, scenarioId):
    #     return os.path.join(self.getScenarioOutputPath(scenarioId), "Spatial")
    #
    # def getScenarioInitConditionalSpatialInputPath(self, scenarioId):
    #     return self.getScenarioDatasheetInputPath(scenarioId, "STSim_InitialConditionsSpatial")

    # def getScenarioDatasheetInputPath(self, input_path, datasheet_name):
    #     return os.path.join(input_path, datasheet_name)

    # def getScenarioTempPath(self,scenarioId):
    #     """
    #         Get the Scenario Temporary Path
    #     @type scenarioId: int - The ID of the scenario of interest
    #     @return: The Scenario Temporary Path @rtype: str| unicode
    #     """
    #     return os.path.join(self.getLibraryTempPath(),"Scenario-{0}".format(scenarioId))


    def __callSyncrosimConsole(self, cmdLineArgs):
        # TODO: Look at using this as a command routine to call console

        cmdLine = '"{0}" "{1}"'.format(self.syncrosim_console_path, cmdLineArgs)
        proc = subprocess.call(cmdLine)
        if proc <>0:
            logging.error("Error calling Syncrosim.Console:{0}".format(cmdLine))
            return None

    def putTransitionSpatialMult(self, export_dir, scenarioId, iteration, timestep, transitionGroupId, transitionMultiplierType,
                                 multiplierFileName):

        # ' Create a CSV file   with following header columms:
        # Iteration
        # Timestep
        # TransitionGroupID
        # TransitionMultiplierTypeID
        # MultiplierFileName
        sheet = 'STSim_TransitionSpatialMultiplier'
        export_filename = os.path.join(export_dir,sheet + '.csv')
        # TODO: See of lineterminator and/or open with 'w' vs 'wb' will give us grief in Linux
        with open(export_filename, 'w') as csvfile:
            fieldnames = ['Iteration','Timestep','TransitionGroupID','TransitionMultiplierTypeID','MultiplierFileName']
            writer = csv.DictWriter(csvfile,lineterminator='\n', fieldnames=fieldnames)

            writer.writeheader()
            writer.writerow({'Iteration': iteration,
                             'Timestep': timestep,
                             'TransitionGroupID':transitionGroupId,
                             'TransitionMultiplierTypeID':transitionMultiplierType,
                             'MultiplierFileName':multiplierFileName})


            csvfile.flush()
            os.fsync(csvfile.fileno())

        logging.debug('Created new Transition Spatial Multiplier Import File "{0}".'.format(export_filename))




if __name__ == '__main__':

    LIBNAME = "D:/ApexRMS/A165/FarsiteSTSim/Test Data/STSim/Newmont_SandBox.ssim"
    SYNCROSIM_DIR = "D:/SVNProjects/SyncroSim-1/WinForm/bin/x86/Debug"

    syn = SynrosimDB(LIBNAME,SYNCROSIM_DIR)

    # Folders
    # print syn.__folders
    print "Input Folder: " + syn.getLibraryInputPath()
    print "Output Folder: " + syn.getLibraryOutputPath()
    print "Scenario Output Folder: " + syn.getScenarioOutputPath(111)

    # Projects
    print "Projects:"
    projs = syn.getProjects()
    print projs

    pid = syn.getProjectId('New Project - Test')
    print "Project ID={0}".format(pid)

    # Stratum
    print "Stratum:"
    strata = syn.getStratum(pid)
    print strata

    # Scenarios
    scens = syn.getScenarios()
    print "All Scenarios:"
    for row in scens:
        print "\t" + row['ScenarioID'], row['Name']

    scens = syn.getScenarios(pid)
    print "Project Scenarios:"
    for row in scens:
        print "\t" + row['ScenarioID'], row['Name']


    sas = syn.getStateAttributes(11)
    print sas

    sa = syn.getStateAttributeId(11,'Early-succesion Lek Class')
    print "State Attribute ID :{0}".format(sa)




    # syn.getConsoles()
    # syn.getLibrary()
    # syn.getDatafeeds()
    # syn.getDataProviders()
    # # syn.getScenarioDependencies()
    # syn.getModels()



    tgs = syn.getTransitionGroups(11)
    print "Transition Groups"
    for tg in tgs:
        print "\t" + tg['Name']

    if tgs:
        test_tg_name = tgs[0]['Name']
        tgId = syn.getTransitionGroupId(11,test_tg_name)
        print "Transition Group Name: '{0}' ID:{1}".format(test_tg_name, tgId)


    # Stock Types
    sts = syn.getStockTypes(11)
    print "Stock Types:"
    for tg in sts:
        print tg['Name']
    else:
        print "\tNo Stock Types found."

    # Flow Types
    flts = syn.getFlowTypes(11)
    print "Flow Types:"
    for tg in flts:
        print tg['Name']
    else:
        print "\tNo Flow Types found."




#     From the Python shell
# >>> import syncrosim as ss
# >>> syn = ss.SynrosimDB(ss.LIBNAME)
# >>> syn.getProjects()
