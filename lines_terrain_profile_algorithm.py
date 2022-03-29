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
from qgis.core import QgsProcessingParameterField

import processing

from PyQt5 import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import *
from collections import Counter
import time
import numpy as np

class LinesTerrainProfileAlgorithm(QgsProcessingAlgorithm):            
        
    def initAlgorithm(self, config=None):        
        self.addParameter(QgsProcessingParameterRasterLayer('MDT', 'Field DEM', defaultValue=None))                   
        self.addParameter(QgsProcessingParameterVectorLayer('VectorLineLayer', 'Tile Network Lines', types=[QgsProcessing.TypeVectorLine], defaultValue=None))             
        self.addParameter(QgsProcessingParameterFeatureSink('TerrainProfiles', 'Terrain Profile', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterField('FGH', 'Field ID from Line Layer', parentLayerParameterName = 'VectorLineLayer', type = QgsProcessingParameterField.Any))        
                        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multistep feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model    
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}
        
        alg_params = {'DEM': parameters['MDT'], 'LINES': parameters['VectorLineLayer'], 'NAME': parameters['FGH'], 'PROFILE': QgsProcessing.TEMPORARY_OUTPUT}

        # Check if vector line layer 'VectorLineLayer' is in geographic coordinates
        vector_layer = self.parameterAsVectorLayer(parameters, 'VectorLineLayer', context)
        if vector_layer.crs().isGeographic():

            w = QtWidgets.QWidget()
            b = QtWidgets.QLabel(w)
            w.setGeometry(400,400,800,20)
            w.setWindowTitle("Attention: vector line layers in geographic coordinates are not allowed! Ending plugin without slope calculation...")
            w.show()
            time.sleep(10)
            return results        
            
        # Line Terrain Profiles                      
        outputs['ProfilesFromLines'] = processing.run('saga:profilesfromlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Rename Field Name
        alg_params = {'INPUT': outputs['ProfilesFromLines']['PROFILE'], 'FIELD': 'Z', 'NEW_NAME': 'SURF_ELEV', 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['RenameTableField'] = processing.run('qgis:renametablefield', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Delete Unwanted Field Column        
        alg_params = {'INPUT': outputs['RenameTableField']['OUTPUT'], 'COLUMN': 'DIST_SURF', 'OUTPUT': parameters['TerrainProfiles']}               
                
        outputs['DeleteColumn'] = processing.run('native:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #3                
        results['TerrainProfiles'] = outputs['DeleteColumn']['OUTPUT']
        return results        
 
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return LinesTerrainProfileAlgorithm()
        
    def name(self):
        return '9. Field Terrain Intersections'

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
        return self.tr("""This Tool is uses the DEM layer to calculate the Terrain Profile for each line segment from the Tile Network genrated.
        
        Workflow: 
        1. Select a DEM Layer
        2. Select a Network Generated Vector Line layer (e.g. Tile Network) 
        3. Select the Field ID from the displayed Tile Network
        4. Click on \"Run\"
        
        The script will gives out one output.         
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.             
        """)    
        
    def helpUrl(self):
        return "http://www.wq.illinois.edu/DG/DrainageGuide.html"  
    