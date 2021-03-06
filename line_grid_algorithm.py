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
from qgis.core import QgsProcessingParameterExtent
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterField

from qgis.core import (edit,QgsProcessingParameterBoolean,QgsField, QgsFeature, QgsPointXY, QgsProcessingParameterExtent, QgsProcessingParameterNumber, QgsProcessing,QgsWkbTypes, QgsGeometry, QgsProcessingAlgorithm, QgsProcessingMultiStepFeedback, QgsProcessingParameterCrs, QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink,QgsProcessingParameterNumber,QgsFeatureSink,QgsFeatureRequest,QgsFields,QgsProperty,QgsVectorLayer)
import processing

from PyQt5 import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import *
from collections import Counter
import time
import numpy as np

class LineGridAlgorithm(QgsProcessingAlgorithm):        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return LineGridAlgorithm()
                
    def name(self):
        return '3. Tile Layout Grids'

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
        return self.tr( """This tool creates a merged vector layers (both linear and perpendicular) of grids covering a given extent of a Field.         
        
        Workflow: 
        1. From the Grid Extent options, choose the "Use Map Canvas Extent" to define the spatial extent for the grid lines. 
        2. Specify the grid cell dimensions. The Default values can be left so if desired.
        3. From the layers Panel, left-click on the Field Boundary Layer to highlight it and then on the map Canvas "Zoom Out" a liitle bit
        4. Click on \"Run\"
                       
        The script will give out two outputs.        
        
        Note: To have the full benefits of this tool, ensure the input Boundary Layer is at least twice the field of interest. 
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.
        """) 
        
    def helpUrl(self):
        return "http://www.wq.illinois.edu/DG/DrainageGuide.html" 
        
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterExtent('Extent', 'Grid Extent', defaultValue=None))
        self.addParameter(QgsProcessingParameterCrs('CRS', 'Coordinate Reference System', defaultValue='EPSG:3435'))
        self.addParameter(QgsProcessingParameterFeatureSink('LinearGrid', 'Linear Grids', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('PerpendicularGrid', 'Perpendicular Grids', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))            
        self.addParameter(QgsProcessingParameterNumber('GridWidth', 'Horizontal Spacing', type=QgsProcessingParameterNumber.Double, minValue=0.000001, defaultValue=100))
        self.addParameter(QgsProcessingParameterNumber('GridHeight', 'Vertical Spacing', type=QgsProcessingParameterNumber.Double, minValue=0.000001, defaultValue=100))
        self.addParameter(QgsProcessingParameterNumber('RotateGrid', 'Rotation Angle', type=QgsProcessingParameterNumber.Double, minValue=1.0,maxValue=90.0, defaultValue=15.0))
    def processAlgorithm(self, parameters, context, model_feedback):

        # Use a multistep feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}
                        
        # Create grid
        # Create the original parent grid
        alg_params = {'TYPE': 1, 'EXTENT': parameters['Extent'], 'HSPACING': parameters['GridWidth'], 'VSPACING': parameters['GridHeight'], 'HOVERLAY': 0, 'VOVERLAY': 0, 'CRS': parameters['CRS'], 'OUTPUT': parameters['LinearGrid']}
        
        outputs['CreateGrid'] = processing.run('native:creategrid', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1
        
        # outFeats = outputs['CreateGrid']['OUTPUT']
        
        # #Editing a Line Layer
        # symbol = QgsLineSymbol.createSimple({'line_style': 'dot', 'line_width': '0.99', 'color': 'red'})
        # outFeats.renderer().setSymbol(symbol)
        # # show the change
        # outFeats.triggerRepaint()
        
        # results['DisplayedGrid'] = outFeats
        # results['DisplayedGrid'] = outputs['CreateGrid']['OUTPUT']
        # return results

        
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
            
        # Rotate grid
        # Create the original parent grid
        alg_params = {'INPUT': outputs['CreateGrid']['OUTPUT'], 'ANGLE': parameters['RotateGrid'], 'OUTPUT': parameters['PerpendicularGrid']}        
        outputs['RotateFeatures'] = processing.run('native:rotatefeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #2
        
        # outFeats = outputs['RotateFeatures']['OUTPUT']
        
        # #Editing a Line Layer
        # symbol = QgsLineSymbol.createSimple({'line_style': 'dot', 'line_width': '0.99', 'color': 'red'})
        # outFeats.renderer().setSymbol(symbol)
        # # show the change
        # outFeats.triggerRepaint()
        
        # results['DisplayedGrid'] = outFeats
        # return results
        
        results['DisplayedGrid'] = outputs['RotateFeatures']['OUTPUT']
        return results               
    