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

import os, math
import inspect
from qgis.PyQt.QtGui import QIcon

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFeatureSink
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

class PlottingFieldLaylinesAlgorithm(QgsProcessingAlgorithm):
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return PlottingFieldLaylinesAlgorithm()
                
    def name(self):
        return 'd. Plot Field Laylines'

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
        return self.tr( """This tool is used to find the surface water flow paths on a field. 
        
        Workflow: 
        1. Select a LiDAR DEM Raster Layer and a Polygon Vector Layer. 
        2. Specify a Desired Contour Interval (feet)
        3. Save the output files (optional)        
        4. Click on \"Run\"              
                
        The script will give out three outputs.       
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.
        """)   
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf" 
    
    
    def initAlgorithm(self, config=None):
        
        self.addParameter(QgsProcessingParameterRasterLayer('MDT', 'Field LiDAR DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('VectorPolygonLayer', 'Field Boundary', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('ContourInterval', 'Contour Line Interval (ft)', type=QgsProcessingParameterNumber.Double, maxValue=100.0, defaultValue=1))      
        self.addParameter(QgsProcessingParameterFeatureSink('UnfilledDEM', 'Unfilled Laylines', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('FilledContour', 'Filled Contour Lines', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('FilledDEM', 'Filled Laylines', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))            
        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}                       
        
        # Check if vector line layer 'VectorPointLayer' is in geogrephic coordinates
        vector_layer = self.parameterAsVectorLayer(parameters, 'VectorPolygonLayer', context)
        if vector_layer.crs().isGeographic():

            w = QtWidgets.QWidget()
            b = QtWidgets.QLabel(w)
            w.setGeometry(400,400,800,20)
            w.setWindowTitle("Attention: vector point layers in geographic coordinates are not allowed! Ending plugin without slope calculation...")
            w.show()
            time.sleep(10)
            return results
       
            
        # Clip Raster DEM Layer Out  
        alg_params = {'INPUT': parameters['MDT'], 'MASK': parameters['VectorPolygonLayer'], 'CROP_TO_CUTLINE': True, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT} 
        
        outputs['ClipRasterbyMaskLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
            
            
        # Find Channel Network from Terrain Analysis (unfilled DEM)
        alg_params = {'ELEVATION': outputs['ClipRasterbyMaskLayer']['OUTPUT'], 'INIT_GRID': outputs['ClipRasterbyMaskLayer']['OUTPUT'], 'INIT_METHOD': 2, 'INIT_VALUE': 0, 'DIV_CELLS': 10, 'MINLEN': 10,
                                    'CHNLNTWRK': QgsProcessing.TEMPORARY_OUTPUT, 'CHNLROUTE': QgsProcessing.TEMPORARY_OUTPUT, 'SHAPES': parameters['UnfilledDEM']}
        
        outputs['ChannelNetwork'] = processing.run('saga:channelnetwork', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}
            
            
        # Fill DEM Sinks               
        alg_params = {'DEM': outputs['ClipRasterbyMaskLayer']['OUTPUT'], 'MINSLOPE': 0.01, 'RESULT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['FillSinks'] = processing.run('saga:fillsinks', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #3        
        
        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}
            
            
        # Find Field Contour               
        alg_params = {'INPUT': outputs['FillSinks']['RESULT'], 'BAND': 1, 'INTERVAL': parameters['ContourInterval'], 'FIELD_NAME': 'ELEV', 'OUTPUT': parameters['FilledContour']}
        
        outputs['Contour'] = processing.run('gdal:contour', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #4   
                       
        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}            
            
        
        # Find Channel Network from Terrain Analysis (filled DEM)
        alg_params = {'ELEVATION': outputs['FillSinks']['RESULT'], 'INIT_GRID': outputs['FillSinks']['RESULT'], 'INIT_METHOD': 2, 'INIT_VALUE': 0, 'DIV_CELLS': 10, 'MINLEN': 10,
                                    'CHNLNTWRK': QgsProcessing.TEMPORARY_OUTPUT, 'CHNLROUTE': QgsProcessing.TEMPORARY_OUTPUT, 'SHAPES': parameters['FilledDEM']}
        
        outputs['ChannelNetwork2'] = processing.run('saga:channelnetwork', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #5               
        
        results['FilledDEM'] = outputs['ChannelNetwork2']['SHAPES']
        return results

    
