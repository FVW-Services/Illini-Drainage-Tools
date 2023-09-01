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
from qgis.core import QgsProcessingParameterVectorDestination

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
        return 'f. Tile Node Connectivity'

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
        1. Select a vector Line layer. This is a follow-up from "Routine E"
        2. Select the Field IDs ("Vertex Part Index" and "Group Vertex part") that represents the line segments to be corrected
        3. Save the output file (optional)        
        4. Click on \"Run\"               
                
        The script will give out an output. 
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.
        """)   
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf" 
    
    
    def initAlgorithm(self, config=None):
        
        self.addParameter(QgsProcessingParameterVectorLayer('VectorPointLayer', 'New Line Nodes', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('LineFixes', 'Fixed Line Topology', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))        
        self.addParameter(QgsProcessingParameterField('FAGH', 'Vertex Part Index', parentLayerParameterName = 'VectorPointLayer', type = QgsProcessingParameterField.Any)) 
        self.addParameter(QgsProcessingParameterField('FGH', 'Group Vertex Part', parentLayerParameterName = 'VectorPointLayer', type = QgsProcessingParameterField.Any))         
        

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        
        feedback = QgsProcessingMultiStepFeedback(9, model_feedback)
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
            
        # Explode Line Segments               
        alg_params = {'INPUT': outputs['ExportAddGeometryColumns']['OUTPUT'], 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}        
        
        outputs['ExplodeLines'] = processing.run('native:explodelines', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #4  
                
        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}
            
        # Remove Null Geometries               
        alg_params = {'INPUT': outputs['ExplodeLines']['OUTPUT'], 'REMOVE_EMPTY': True, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['RemoveNullGeometries'] = processing.run('native:removenullgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #5   
                       
        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}                                  
        
        # Validate Attribute Checks               
        alg_params = {
            'INPUT_LAYER': outputs['RemoveNullGeometries']['OUTPUT'], 
            'METHOD': 2, 
            'IGNORE_RING_SELF_INTERSECTION': False, 
            'INVALID_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT, 
            'ERROR_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT, 
            'VALID_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }        
        outputs['AttributeChecker'] = processing.run('qgis:checkvalidity', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #6   
                       
        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}                   
               
        # Field calculator
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'ID',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,
            'FORMULA': '$id',
            'INPUT': outputs['AttributeChecker']['VALID_OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FieldCalculator'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #7
        
        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}
                
         # Final Retained Fields of Interest
        alg_params = {"INPUT": outputs['FieldCalculator']['OUTPUT'], "FIELDS": ['vertex_part', 'begin', 'end', 'ID'], "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
        
        outputs['InterestFields'] = processing.run('native:retainfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #8
        
        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}
            
        # Fix Line Geometries               
        alg_params = {'INPUT': outputs['InterestFields']['OUTPUT'], 'OUTPUT': parameters['LineFixes']}
        
        outputs['FixGeometries2'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #9
        results['LineFixes'] = outputs['FixGeometries2']['OUTPUT']        
                
        return results
    