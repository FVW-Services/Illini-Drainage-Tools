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
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsCoordinateReferenceSystem
import csv


import processing

from PyQt5 import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import *
from collections import Counter
import time
import numpy as np

class ReadoutAlgorithm(QgsProcessingAlgorithm):            
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return ReadoutAlgorithm()
        
    def name(self):
        return 'p. Tile Spreadsheet ReadOut'

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
        return self.tr("""This Tool saves the attribute features of a vector line layer by according it a unique line ID and exporting as spreadsheet readouts.
        
        Workflow: 
        1. Select a Shapefile Layer. This is a follow-up from "Routine O"
        2. Save the output folder (optional)
        3. Click on \"Run\"
        
        
        The script gives out an output that can be saved as a (.xlsx or .csv) file.         
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.             
        """)    
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf"   
        
    
    def initAlgorithm(self, config=None):        
        
        self.addParameter(QgsProcessingParameterVectorLayer('VectorLineLayer', 'Input Vector Layer with Unique Line ID', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))           
        self.addParameter(QgsProcessingParameterFileDestination('Splitty', 'Tile Spreadsheet ReadOut', createByDefault=True, defaultValue=None))
                       
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multistep feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model    
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}               
                       
        # Add Field ID
        idz_params = {
            'FIELD_LENGTH': 11,
            'FIELD_NAME': 'Line_ID',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,
            'FORMULA': '$id',
            'INPUT': parameters['VectorLineLayer'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AddFieldID'] = processing.run('native:fieldcalculator', idz_params, context=context, feedback=feedback, is_child_algorithm=True) #1
        
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        
        # Export Calculations and Save as CSV Files
        alg_params = {'LAYERS': outputs['AddFieldID']['OUTPUT'], 'USE_ALIAS': False, "FORMATTED_VALUES": True, "OVERWRITE": True, 'OUTPUT': parameters['Splitty']}          
                                              
        outputs['SplitToCSV'] = processing.run('native:exporttospreadsheet', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2 
                        
        results['Splitty'] = outputs['SplitToCSV']['OUTPUT']
        return results               
               
    