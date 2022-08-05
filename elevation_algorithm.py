# -*- coding: utf-8 -*-

"""
/***************************************************************************
 illini_drainage_tools
                                 A QGIS plugin
 Performs Specific Draiange Related Tasks and Analysis on a Site
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-03-15
        copyright            : (C) 2022 by FALASY  Anamelechi
        email                : fvw.services@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'FALASY  Anamelechi'
__date__ = '2022-03-15'
__copyright__ = '(C) 2022 by FALASY  Anamelechi'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import inspect
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsProcessingParameterVectorDestination

import processing

from PyQt5 import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import *
from collections import Counter
import time
import numpy as np

class ElevationAlgorithm(QgsProcessingAlgorithm):            
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return ElevationAlgorithm()
        
    def name(self):
        return 'k. Network Elevation Exports'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return ''
        
    def icon(self):
        cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
        icon = QIcon(os.path.join(os.path.join(cmd_folder, 'logo.png')))
        return icon
        
    def shortHelpString(self):
        return self.tr("""This Tool generates elevation points for each line segment of the Tile Network.
        
        Workflow: 
        1. Select a DEM Layer and a Line Layer. This is a follow-up from "Routine J"
        2. Select a reference field for generating the elevation points from
        3. Save the output files (optional)
        4. Click on \"Run\"
        
        The script will gives out three outputs.         
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.             
        """)    
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf"  
    
    
    def initAlgorithm(self, config=None):        
        self.addParameter(QgsProcessingParameterRasterLayer('MDFT', 'Field DEM',  defaultValue=None))        
        self.addParameter(QgsProcessingParameterVectorLayer('LineSegmentLayer', 'Tile Network Lines', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('FGHTY', 'Field to Calculate [Tile_ID]', parentLayerParameterName = 'LineSegmentLayer', type = QgsProcessingParameterField.Any,)) 
        self.addParameter(QgsProcessingParameterFeatureSink('FinalFields', 'Final Reference Fields', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))       
        self.addParameter(QgsProcessingParameterVectorDestination('TerrainProfiles', 'Network Elevation Points', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFolderDestination('Splitty', 'Network Spreadsheet', createByDefault=True, defaultValue=None))
                     
                        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multistep feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model    
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}
                                       
        
        # Final Retained Fields of Interest
        alg_params = {"INPUT": parameters['LineSegmentLayer'], "FIELDS": ['Tile_ID', 'Tile_TO', 'Elev_First', 'Elev_Last', 'True_Length', 'Abs_Slope', 'FLOW_LINE', 'FLOW_ORDER', 'Tile_ORDER'], "OUTPUT": parameters['FinalFields']}
                    
        outputs['RetainFields'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        
        # Line Terrain Profiles
        alg_params = {'DEM': parameters['MDFT'], 'LINES': outputs['RetainFields']['OUTPUT'], 'NAME': parameters['FGHTY'], 'PROFILE': QgsProcessing.TEMPORARY_OUTPUT}
                
        outputs['ProfilesFromLines'] = processing.run('saga:profilesfromlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Rename Field Name        
        alg_params = {'INPUT': outputs['ProfilesFromLines']['PROFILE'], 'FIELD': 'Z', 'NEW_NAME': 'SURF_ELEV', 'OUTPUT': parameters['TerrainProfiles']}
        
        outputs['RenameTableField'] = processing.run('qgis:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #3                  

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}     
               
        # Split and Save as CSV Files
        alg_params = {'INPUT': outputs['RenameTableField']['OUTPUT'], 'FIELD': 'LINE_ID', "FILE_TYPE": 4, 'OUTPUT': parameters['Splitty']}          
                                              
        outputs['SplitToCSV'] = processing.run('qgis:splitvectorlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #4 
                        
        results['Splitty'] = outputs['SplitToCSV']['OUTPUT']
        return results          
    