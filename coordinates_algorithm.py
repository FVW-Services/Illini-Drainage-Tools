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
from qgis.core import QgsProcessingParameterCrs


import processing

from PyQt5 import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import *
from collections import Counter
import time
import numpy as np

class CoordinatesAlgorithm(QgsProcessingAlgorithm):           
             
    def initAlgorithm(self, config=None):        
        self.addParameter(QgsProcessingParameterRasterLayer('MDT', 'Input Raster Layer', defaultValue=None))                
        self.addParameter(QgsProcessingParameterVectorLayer('VectorLineLayer', 'Input Vector Layer', types=[QgsProcessing.TypeVectorAnyGeometry], defaultValue=None))
        
        self.addParameter(QgsProcessingParameterCrs('CRS', 'Targeted CRS', defaultValue='EPSG:3435')) 
        
        self.addParameter(QgsProcessingParameterRasterDestination('RasterNew', 'Raster in Desired CRS', createByDefault=True, defaultValue=None))        
        self.addParameter(QgsProcessingParameterFeatureSink('VectorNew', 'Vector in Desired CRS', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
                       
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multistep feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model    
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}                               
                    
        # Raster Coordinates Assignation
        alg_params = {'INPUT': parameters['MDT'], 'TARGET_CRS': parameters['CRS'], 'RESAMPLING': 0, 'DATA_TYPE': 0, 'OUTPUT': parameters['RasterNew']}        
        
        outputs['RasterCRS'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Vector Coordinates Assignation
        alg_params = {'INPUT': parameters['VectorLineLayer'], 'CRS': parameters['CRS'], 'OUTPUT': parameters['VectorNew']}
        
        outputs['VectorCRS'] = processing.run('native:assignprojection', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2
                        
        results['VectorNew'] = outputs['VectorCRS']['OUTPUT']
        return results

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return CoordinatesAlgorithm()
        
    def name(self):
        return 'a. Coordinates Harmonization'

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
        return self.tr("""This Tool is used to ensure both Vector and Raster layers have the same reference coordinate system.
        
        Workflow: 
        1. Select both Raster and Vector Layers, Respectively
        2. Select a Targeted Coordinate Reference System (CRS) for both layers
        3. Save the output files (optional)
        4. Click on \"Run\"
        
        The script will gives out two outputs.         
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.             
        """)    
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf"   
    
    
     