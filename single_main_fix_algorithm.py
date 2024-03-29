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

class SingleMainFixAlgorithm(QgsProcessingAlgorithm):
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return SingleMainFixAlgorithm()
                
    def name(self):
        return 'e1. Single-Main Node Generator'

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
        return self.tr( """This tool is used to clean up a line layer from its global properties in space. 
        
        Workflow:         
        1. Select two Vector Line layers respectively: 1: Single Main; and 2: Associated Laterals
        2. Select a desired Coordinate Reference System for displaying the generated points
        3. Save the output file (optional)
        4. Click on \"Run\"               
                
        The script will give out an output.
        Use this output with "Routine F" to have a topologically sound tile network.        
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.
        """)   
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf" 
    
    
    def initAlgorithm(self, config=None):
        
        self.addParameter(QgsProcessingParameterVectorLayer('VectorMain', 'Single Tile Main', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('VectorLaterals', 'Associated Lateral Lines', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterCrs('CRS', 'Coordinate Reference System', defaultValue='EPSG:3435'))
        self.addParameter(QgsProcessingParameterFeatureSink('LineFixes', 'New Line Nodes', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))                              
        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        
        feedback = QgsProcessingMultiStepFeedback(9, model_feedback)
        results = {}
        outputs = {}
                       
        # Join Lines     
        alg_params = {'INPUT': parameters['VectorMain'], 'OVERLAY':parameters['VectorLaterals'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
                        
        outputs['FaGiHe'] = processing.run('qgis:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1               
        
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}                    
               
        # Add Incremental Field     
        alg_params = {'INPUT': outputs['FaGiHe']['OUTPUT'], 'FIELD_NAME': 'New_ID', 'START': 1, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
                
        outputs['AddNewID'] = processing.run('native:addautoincrementalfield', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2        
        
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}
            
        # Retain Fields     
        alg_params = {'INPUT': outputs['AddNewID']['OUTPUT'], 'FIELDS':['New_ID'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['RetainFields'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #3
        
        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}
            
        # Extend Lines     
        alg_params = {'INPUT': outputs['RetainFields']['OUTPUT'], 'START_DISTANCE':0, 'END_DISTANCE':7,'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['ExtendLines'] = processing.run('native:extendlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #4
        
        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}
        
        # MultiPart To SingleParts
        alg_params = {'INPUT': outputs['ExtendLines']['OUTPUT'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['MultiPartToSingleParts'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #5

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Dissolve Line Split lines by maximum length
        alg_params = {'INPUT': outputs['MultiPartToSingleParts']['OUTPUT'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}        

        outputs['Dissolve'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #6

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}
        
        # Extract Vertices
        alg_params = {'INPUT': outputs['Dissolve']['OUTPUT'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['ExtractVertices'] = processing.run('native:extractvertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #7

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Add X/Y Fields
        alg_params = {'INPUT': outputs['ExtractVertices']['OUTPUT'], 'CRS': parameters['CRS'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['AddxyFields'] = processing.run('native:addxyfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #8

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Snap Geometries to Layers        
        alg_params = {'INPUT': outputs['AddxyFields']['OUTPUT'], 'REFERENCE_LAYER': outputs['AddxyFields']['OUTPUT'], 'TOLERANCE': 10, 'BEHAVIOR': 0, 'OUTPUT': parameters['LineFixes']}
                
        outputs['SnapGeometries'] = processing.run('native:snapgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #9
                
        results['LineFixes'] = outputs['SnapGeometries']['OUTPUT']
        return results      
    
