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

import processing
import os, math
import inspect
import time
import qgis.utils
import numpy as np

from qgis.gui import *
from osgeo import gdal
from PyQt5 import QtWidgets
from osgeo import gdalnumeric
from collections import Counter
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, QVariant, QObject
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterExtent
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterPoint
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsFeatureSink
from qgis.core import QgsFeatureRequest
from qgis.core import QgsVectorLayer
from qgis.core import QgsLineSymbol
from qgis.core import QgsProperty
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingLayerPostProcessorInterface
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterVectorDestination

from qgis.core import (edit,QgsField, QgsFeature, QgsPointXY, QgsWkbTypes, QgsGeometry, QgsFields)


class PlottingFieldLaylinesAlgorithm(QgsProcessingAlgorithm):
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return PlottingFieldLaylinesAlgorithm()
                
    def name(self):
        return 'c. Plot Field Laylines'

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
                
        The script will give out four outputs.
        
        Colors: Laylines/Drain Nets in (Blue) & Contour Lines Nets in (Yellow)
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.
        """)   
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf" 
    
    
    def initAlgorithm(self, config=None):
        
        self.addParameter(QgsProcessingParameterRasterLayer('HGF', 'Original LiDAR DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('MDT', 'Thinned LiDAR DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('VectorPolygonLayer', 'Field Boundary', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        
        self.addParameter(QgsProcessingParameterCrs('CRSZ', 'Specify Layer CRS', defaultValue='EPSG:3435')) 
        
        self.addParameter(QgsProcessingParameterNumber('ContourInterval', 'Contour Line Interval (ft)', type=QgsProcessingParameterNumber.Double, maxValue=100.0, defaultValue=1))
        self.addParameter(QgsProcessingParameterNumber('RasterDepth', 'Raster Depth Difference (ft)', type=QgsProcessingParameterNumber.Double, maxValue=100.0, defaultValue=1))
        
        self.addParameter(QgsProcessingParameterVectorDestination('UnfilledDEM', 'Unfilled Laylines', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('FilledContour', 'Filled Contour Lines', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorDestination('FilledDEM', 'Filled Laylines', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('DeRaster', 'Identified Depression Areas', createByDefault=True, defaultValue=None))
        
    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        
        feedback = QgsProcessingMultiStepFeedback(15, model_feedback)
        results = {}
        outputs = {}                   
                                  
        # Buffer the Boundary Plot  
        alg_params = {'INPUT': parameters['VectorPolygonLayer'], 'DISTANCE':20, 'SEGMENTS':5, 'END_CAP_STYLE':0, 'JOIN_STYLE:':0, 'MITER_LIMIT':2, 'DISSOLVE':False, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
        
        outputs['VectorBuffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #1
        results['VectorBuffer'] = outputs['VectorBuffer']['OUTPUT']
            
        # Clip Raster DEM Layer Out  
        alg_params = {'INPUT': parameters['MDT'], 'MASK': results['VectorBuffer'], 'CROP_TO_CUTLINE': True, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT} 
                              
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}
            
        outputs['ClipRasterbyMaskLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)#2     
        results['ClipRasterbyMaskLayer'] = outputs['ClipRasterbyMaskLayer']['OUTPUT']
        
        # Find Channel Network from Terrain Analysis (unfilled DEM)
        alg_params = {'ELEVATION': results['ClipRasterbyMaskLayer'], 'INIT_GRID': outputs['ClipRasterbyMaskLayer']['OUTPUT'], 'INIT_METHOD': 2, 'INIT_VALUE': 0, 'DIV_CELLS': 10, 'MINLEN': 10,
                                    'CHNLNTWRK': QgsProcessing.TEMPORARY_OUTPUT, 'CHNLROUTE': QgsProcessing.TEMPORARY_OUTPUT, 'SHAPES': QgsProcessing.TEMPORARY_OUTPUT}
                
        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}
            
        outputs['ChannelNetworkz'] = processing.run('sagang:channelnetwork', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #3
        results['ChannelNetworkz'] = outputs['ChannelNetworkz']['SHAPES']
    
        # Clip Field Laylines               
        alg_params = {'INPUT': results['ChannelNetworkz'], 'MASK': parameters['VectorPolygonLayer'], 'OUTPUT': parameters['UnfilledDEM']}
        
        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {} 
            
        outputs['ChannelNetwork'] = processing.run('gdal:clipvectorbypolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #4
        results['ChannelNetwork'] = outputs['ChannelNetwork']['OUTPUT'] 
        
        # Define Current Projection
        alg_params = {'INPUT': results['ChannelNetwork'], 'CRS': parameters['CRSZ']}
                
        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}
            
        outputs['ChannelNetwork_A'] = processing.run('qgis:definecurrentprojection', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #4
        results['ChannelNetwork_A'] = outputs['ChannelNetwork_A']['INPUT']
        
        # Fill DEM Sinks               
        alg_params = {'DEM': results['ClipRasterbyMaskLayer'], 'MINSLOPE': 0.03, 'RESULT': QgsProcessing.TEMPORARY_OUTPUT}
        
        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {} 
        
        outputs['FillSinks'] = processing.run('sagang:fillsinksplanchondarboux2001', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #5        
        results['FillSinks'] = outputs['FillSinks']['RESULT']      
                                                              
        # Find Field Contour               
        alg_params = {'INPUT': results['FillSinks'], 'BAND': 1, 'INTERVAL': parameters['ContourInterval'], 'FIELD_NAME': 'ELEV', 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        
        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {} 
            
        outputs['Contoky'] = processing.run('gdal:contour', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #6
        results['Contoky'] = outputs['Contoky']['OUTPUT']                             
                                             
        # Define Current Projection
        alg_params = {'INPUT': results['Contoky'], 'CRS': parameters['CRSZ']}
                
        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}
            
        outputs['Contour_A'] = processing.run('qgis:definecurrentprojection', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #7
        results['Contour_A'] = outputs['Contour_A']['INPUT']
                
        # Clip Field Contour               
        alg_params = {'INPUT': results['Contour_A'], 'OVERLAY': parameters['VectorPolygonLayer'], 'OUTPUT': parameters['FilledContour']} #QgsProcessing.TEMPORARY_OUTPUT
        
        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {} 
            
        outputs['Contour'] = processing.run('qgis:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #8
        results['Contour'] = outputs['Contour']['OUTPUT']   
        
        # Find Channel Network from Terrain Analysis (filled DEM)
        alg_params = {'ELEVATION': outputs['FillSinks']['RESULT'], 'INIT_GRID': outputs['FillSinks']['RESULT'], 'INIT_METHOD': 2, 'INIT_VALUE': 0, 'DIV_CELLS': 10, 'MINLEN': 10,
                                    'CHNLNTWRK': QgsProcessing.TEMPORARY_OUTPUT, 'CHNLROUTE': QgsProcessing.TEMPORARY_OUTPUT, 'SHAPES': QgsProcessing.TEMPORARY_OUTPUT}
                
        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}
        
        outputs['ChannelNetworkys'] = processing.run('sagang:channelnetwork', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #9
        results['ChannelNetworkys'] = outputs['ChannelNetworkys']['SHAPES']                
        
        # Clip Field Laylines               
        alg_params = {'INPUT': results['ChannelNetworkys'], 'MASK': parameters['VectorPolygonLayer'], 'OUTPUT': parameters['FilledDEM']}
        
        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {} 
            
        outputs['ChannelNetwork2'] = processing.run('gdal:clipvectorbypolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #10
        results['ChannelNetwork2'] = outputs['ChannelNetwork2']['OUTPUT'] 
                
        # Define Current Projection
        alg_params = {'INPUT': results['ChannelNetwork2'], 'CRS': parameters['CRSZ']}
                
        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}
            
        outputs['ChannelNetwork_B'] = processing.run('qgis:definecurrentprojection', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #11
        results['ChannelNetwork_B'] = outputs['ChannelNetwork_B']['INPUT']
        
        # Clip Original Raster DEM Layer Out  
        alg_params = {'INPUT': parameters['HGF'], 'MASK': results['VectorBuffer'], 'CROP_TO_CUTLINE': True, 'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT} 
                              
        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}
            
        outputs['ClipLayer'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)#12     
        results['ClipLayer'] = outputs['ClipLayer']['OUTPUT']
        
        # Fill DEM Sinks               
        alg_params = {'DEM': results['ClipLayer'], 'MINSLOPE': 0.03, 'RESULT': QgsProcessing.TEMPORARY_OUTPUT}
        
        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {} 
        
        outputs['FillSinkz'] = processing.run('sagang:fillsinksplanchondarboux2001', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #13        
        results['FillSinkz'] = outputs['FillSinkz']['RESULT'] 
        
        ## Raster Calculator
        B = outputs['ClipLayer']['OUTPUT']#10
        A = outputs['FillSinkz']['RESULT'] #11              
        
        alg_params = {
        'INPUT_A': results['FillSinkz'], 
        'BAND_A': 1, 
        'INPUT_B': results['ClipLayer'],              
        'FORMULA': "A-B>parameters['RasterDepth']",
        'NO_DATA': None,        
        'RTYPE': 5, 
        'OUTPUT': parameters['DeRaster']
        }       
        
        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}
        
        outputs['RasterCalculator'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True) #14
        results['RasterCalculator'] = outputs['RasterCalculator']['OUTPUT']
        
        if context.willLoadLayerOnCompletion(results['Contour']):
            context.layerToLoadOnCompletionDetails(results['Contour']).setPostProcessor(GridPostProcessor.create())

        if context.willLoadLayerOnCompletion(results['ChannelNetwork2']):
            context.layerToLoadOnCompletionDetails(results['ChannelNetwork2']).setPostProcessor(LinePostProcessor.create())
        
        return results             

class GridPostProcessor(QgsProcessingLayerPostProcessorInterface):

    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        renderer = layer.renderer().clone()
        symbol = QgsLineSymbol.createSimple({'line_color': '251,247,4,255', 'line_width': '0.45', 'line_style': 'solid'})
        renderer.setSymbol(symbol)
        layer.setRenderer(renderer)

    @staticmethod
    def create() -> 'GridPostProcessor':
        GridPostProcessor.instance = GridPostProcessor()
        return GridPostProcessor.instance


class LinePostProcessor(QgsProcessingLayerPostProcessorInterface):

    instance = None

    def postProcessLayer(self, layer, context, feedback):
        if not isinstance(layer, QgsVectorLayer):
            return
        renderer = layer.renderer().clone()
        symbol = QgsLineSymbol.createSimple({'line_color': '14,186,238,253', 'line_width': '0.66', 'line_style': 'solid'})
        renderer.setSymbol(symbol)
        layer.setRenderer(renderer)

    @staticmethod
    def create() -> 'LinePostProcessor':
        LinePostProcessor.instance = LinePostProcessor()
        return LinePostProcessor.instance