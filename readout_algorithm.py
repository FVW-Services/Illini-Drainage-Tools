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
from qgis.core import QgsProcessingParameterVectorDestination
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
        return 'm. Tile Spreadsheet ReadOut'

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
        1. Select a Shapefile Layer. This is a follow-up from "Routine L"
        2. Save the output folder (This is Not Optional)
        3. Click on \"Run\"
        
        
        The script gives out an output that can be saved as a (.csv, .txt, or .xlsx, etc) file.         
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.             
        """)    
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf"   
        
    
    def initAlgorithm(self, config=None):        
        
        self.addParameter(QgsProcessingParameterVectorLayer('VectorLineLayer', 'Input Vector Layer with Unique Line ID', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        self.addParameter(QgsProcessingParameterField('FGHTY', 'Unique Field ID', parentLayerParameterName = 'VectorLineLayer', type = QgsProcessingParameterField.Any,))
        
        self.addParameter(QgsProcessingParameterFileDestination('Splitty', 'Tile Spreadsheet ReadOut: Export as an Individual File', createByDefault=True, defaultValue=None, fileFilter='CSV files (*.csv);;Text files (*.txt)'))

        self.addParameter(QgsProcessingParameterFolderDestination('Spready', 'Tile Network Spreadsheet ReadOut: Export into a Folder', createByDefault=True, defaultValue=None))
                       
    def processAlgorithm(self, parameters, context, model_feedback):                    
                       
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
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
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        outputs['AddFieldID'] = processing.run('native:fieldcalculator', idz_params, context=context, feedback=feedback, is_child_algorithm=True) #1
        results['AddFieldID'] = outputs['AddFieldID']['OUTPUT']
                       
        # Export Calculations and Save as CSV Files
        alg_params = {'LAYERS': results['AddFieldID'], 'USE_ALIAS': False, "FORMATTED_VALUES": True, "OVERWRITE": True, 'OUTPUT': parameters['Splitty']}

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}        
                                              
        outputs['SplitToCSV'] = processing.run('native:exporttospreadsheet', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2
        results['Splitty'] = outputs['SplitToCSV']['OUTPUT']
        
        # Split and Save as CSV Files
        split_params = {'INPUT': results['AddFieldID'], 'FIELD': parameters['FGHTY'], "FILE_TYPE": 5, 'OUTPUT': parameters['Spready']}          
                                              
        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}        
        
        outputs['SplitToCSV'] = processing.run('qgis:splitvectorlayer', split_params, context=context, feedback=feedback, is_child_algorithm=True) #9
        results['SplitToCSV'] = outputs['SplitToCSV']['OUTPUT']                  
        
        return results                 
        