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

class FixLineTopologyAlgorithm(QgsProcessingAlgorithm):
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return FixLineTopologyAlgorithm()
                
    def name(self):
        return '6. Tile Network Connectivity'

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
        return self.tr( """This tool is used to clean up a line layer to have a topological connected geometry for building tile networks. 
        
        Workflow:         
        1. Choose a vector Line layer. This is a follow-up from either "Routine 4" or "Routine 5".
        2. Click to select the Field ID that represents the line segments from the displayed line layer 
        3. Click on \"Run\"               
                
        The script will give out an output. 
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.
        """)   
        
    def helpUrl(self):
        return "http://www.wq.illinois.edu/DG/DrainageGuide.html" 
    
    
    def initAlgorithm(self, config=None):
        
        self.addParameter(QgsProcessingParameterVectorLayer('VectorPointLayer', 'Snapped Line Geometry', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('LineFixes', 'Fixed Line Topology', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))        
        self.addParameter(QgsProcessingParameterField('FAGH', 'Vertex Part Index', parentLayerParameterName = 'VectorPointLayer', type = QgsProcessingParameterField.Any)) 
        self.addParameter(QgsProcessingParameterField('FGH', 'Group Vertex Part', parentLayerParameterName = 'VectorPointLayer', type = QgsProcessingParameterField.Any))         
        

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}
                        
        alg_params = {'INPUT': parameters['VectorPointLayer'], 'ORDER_EXPRESSION': parameters['FAGH'], 'GROUP_EXPRESSION': parameters['FGH'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}

        # Check if vector line layer 'VectorPointLayer' is in geogrephic coordinates
        vector_layer = self.parameterAsVectorLayer(parameters, 'VectorPointLayer', context)
        if vector_layer.crs().isGeographic():

            w = QtWidgets.QWidget()
            b = QtWidgets.QLabel(w)
            w.setGeometry(400,400,800,20)
            w.setWindowTitle("Attention: vector point layers in geographic coordinates are not allowed! Ending plugin without slope calculation...")
            w.show()
            time.sleep(10)
            return results
       
            
        # Convert Points To Path              
        outputs['PointsToPath'] = processing.run('native:pointstopath', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
            
        # Fix Line Geometries               
        alg_params = {'INPUT': outputs['PointsToPath']['OUTPUT'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['FixGeometries'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2        
        
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}
            
        # Add Geometry Attributes               
        alg_params = {'INPUT': outputs['FixGeometries']['OUTPUT'], 'CALC_METHOD': 0, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['ExportAddGeometryColumns'] = processing.run('qgis:exportaddgeometrycolumns', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #3   
                       
        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}
            
        # Remove Null Geometries               
        alg_params = {'INPUT': outputs['ExportAddGeometryColumns']['OUTPUT'], 'REMOVE_EMPTY': True, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['RemoveNullGeometries'] = processing.run('native:removenullgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #4   
                       
        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}
            
        # Explode Line Segments               
        alg_params = {'INPUT': outputs['RemoveNullGeometries']['OUTPUT'], 'OUTPUT': parameters['LineFixes']}
        
        outputs['ExplodeLines'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #5  
        results['LineFixes'] = outputs['ExplodeLines']['OUTPUT']
        return results

    