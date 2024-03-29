# -*- coding: utf-8 -*-

"""
/***************************************************************************
 flow_&_ordering
                                 A QGIS plugin
 Flow and Ordering
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-06-13
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
__date__ = '2022-06-13'
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
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterDefinition

import processing
import processing as st
import sys
import csv

from PyQt5 import QtWidgets
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import *
from collections import Counter
import time
import numpy as np

class BenefitsAlgorithm(QgsProcessingAlgorithm):
    INPUT_LAYER = 'INPUT_LAYER'
    SEGMENT_KEY = 'SEGMENT_KEY'
    FLOW_KEY = 'SYSTEM_FLOW'
    TILE_TO_KEY = 'TILE_TO'
    ORDER_KEY = 'ORDER_KEY'
    LENGTH_KEY = 'LENGTH_KEY'
    SLOPE_KEY = 'SLOPE_KEY'
    SPACING_KEY = 'SPACING_KEY'    
    PIPE_KEY = 'PIPE_KEY'
    INTENS_KEY = 'INTENS_KEY' 
    ASS_INTENS_KEY = 'ASS_INTENS_KEY'
    USE_ASS_KEY = 'USE_ASS_KEY'    
    COFF_KEY = 'COFF_KEY'
    SEG_COFF_KEY = 'SEG_COFF_KEY'
    ORDER_COFF_KEY = 'ORDER_COFF_KEY'
    OUTPUT = 'OUTPUT'      
    D_COEFF_KEY = 'D_COEFF'
    PIPE_SIZE_KEY = 'ACTUAL_SIZE'
    NOMINAL_PIPE_SIZE_KEY = 'NOMINAL_SIZE'
        
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BenefitsAlgorithm()
        
    def name(self):        
        return 'n. Network Pipe Sizing'

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
        return self.tr( """This tool is used to determine final pipe sizes for the individual tile networks. 
        
        Workflow:         
        1. Select a vector layer of line segments. This is a follow-up from "Routine K"
        2. Select the respective Field IDs that represents the attribute tables from the displayed line layer
        3. Specify Type of Pipe Material
        4. Specify or Assign Drainage Intensity [DI]
        5. For Advanced Settings, you can either use system assigned default settings for Drainage Coefficient [DC], or rather do the assign desired Drainage Coefficients based on either individual line segments or line orders
        6. Save the output file (optional)        
        7. Click on \"Run\"               
                
        The script will give out an output. 
        
        The script will give out an output with default name as:
        \"Drainage Intensity [DI]\" -- The rate at which an outlet system can remove water from a field. This is the Hydraulic capacity of the drainage system. 
        \"Drainage Coefficient [DC]\" -- The rate at which water can move from the soil through the drain pipes. 
        
        Note: In a subsurface drainage system, [DC] must be "equal to" or "greater than" [DI] for optimal operation. Thus, a pipe depends mainly on the [DC]. 
                
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.
        """)   
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf" 
    
    INTENSITY_OPTIONS = [0.375, 0.500, 0.750, 1.000]

    def addAdvancedParameter(self, parameter):
        parameter.setFlags(parameter.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(parameter)
        
    def initAlgorithm(self, config):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER, self.tr('Tile Network: with Reference IDs'), [QgsProcessing.TypeVectorLine], defaultValue=None))               
        
        self.addParameter(QgsProcessingParameterField(self.SEGMENT_KEY, self.tr("Line Segments [TILE_ID]"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None)) 
        self.addParameter(QgsProcessingParameterField(self.TILE_TO_KEY, self.tr("System Flow [TILE_TO]"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None))
        self.addParameter(QgsProcessingParameterField(self.ORDER_KEY, self.tr("Strahler Orders [TILE_ORDER]"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None))

        self.addParameter(QgsProcessingParameterField(self.LENGTH_KEY, self.tr("Segments Length [True_LENGTH]"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None))               
        self.addParameter(QgsProcessingParameterField(self.SLOPE_KEY, self.tr("Segments Slope [Abs_SLOPE]"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None))
        
        self.addParameter(QgsProcessingParameterNumber(self.SPACING_KEY, self.tr('Specify Drain Spacing [ft]'), type=QgsProcessingParameterNumber.Double, maxValue=200.0, defaultValue=100.0))
        
        self.addParameter(QgsProcessingParameterEnum(self.PIPE_KEY, self.tr('Select Pipe Material'), options=[self.tr("Single Wall"),self.tr("Smooth Wall"),self.tr("Clay or Concrete")], defaultValue=0))
        
        self.addParameter(QgsProcessingParameterEnum(self.INTENS_KEY, self.tr('Drainage Intensity [inch/day]'), options=[self.tr("A: 0.375"),self.tr("B: 0.500"),self.tr("C: 0.750"),self.tr("D: 1.000")], defaultValue=0))
        
        self.addParameter(QgsProcessingParameterNumber(self.ASS_INTENS_KEY, self.tr('E: others = Assign Intensity [inch/day]'), type=QgsProcessingParameterNumber.Double, maxValue=100.0, defaultValue=2.50, optional = True))
        self.addParameter(QgsProcessingParameterBoolean(self.USE_ASS_KEY, self.tr('Use Assigned Value'), defaultValue=False))

        self.addAdvancedParameter(QgsProcessingParameterEnum(self.COFF_KEY, self.tr('Assign Drainage Coefficient [inch/day]'), options=[self.tr("By System [internal]"),self.tr("By Line Segments [self]"),self.tr("By Tile Orders [self]")], defaultValue=0))
        self.addAdvancedParameter(QgsProcessingParameterField(self.SEG_COFF_KEY, self.tr("Line Segment Coefficient Field Name (if \"By Line Segments [self]\" selected)"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None, optional=True))
        self.addAdvancedParameter(QgsProcessingParameterString(self.ORDER_COFF_KEY, self.tr("Order Coefficient separate by ',' (if \"By TIle Orders [self]\" selected)"), optional=True))

        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Network Pipe Sizings'), createByDefault=True, defaultValue=None))
    
    def getCoeff(self, intensity, order):
        if order == 1:
            return intensity        
        if order >= 2:
            return intensity * 1.25
        raise ValueError(f"Unexpected order value: {order}")

    def getFlow(self, length, spacing, DCoeff):  # individual flow
        return length * spacing * DCoeff / 12 / 24 / 60 / 60
    
    def roughness(self, ptype, psize):
        if ptype == 0:  # single wall
            if psize <= 8:
                return 0.015
            if psize <= 12:
                return 0.017
            return 0.02
        if ptype == 1:  # smooth Wall
            return 0.011
        if ptype == 2:  # clay or concrete
            return 0.013
        raise ValueError(f"Unexpected ptype value {ptype}")  # throw error if does not fit into any category
    
    def formula(self, flow, nn, slp):
        return (flow * nn * 4**(5/3) / (1.49 * 3.142 * slp**0.5))**(3/8)

    def inverse_formula(self, d, nn, slp):
        return 1.49 * 3.142 * slp**0.5 / (nn * 4**(5/3)) * d**(8/3)

    def getPipeSize(self, flow, slope, ptype):
        if ptype == 1:  # single wall pipe
            k = 2
            while True:
                k += 4
                nn = self.roughness(ptype, k)
                d = self.formula(flow, nn, slope)
                psize = d * 12
                nn = self.roughness(ptype, d)
                flow1 = self.inverse_formula(d, nn, slope)
                if abs(flow - flow1) <= 0.001:
                    return psize
        else:  # other cases
            nn = self.roughness(ptype, 1)
            psize = self.formula(flow, nn, slope) * 12
            return psize

    AVAILABLE_NOMINAL_SIZES = [4, 5, 6, 8, 10, 12, 15, 18, 21, 24, 30]  # must be sorted in ascending order

    def getNominalSize(self, psize):
        for n_size in self.AVAILABLE_NOMINAL_SIZES:
            if n_size > psize:
                return n_size
        return self.AVAILABLE_NOMINAL_SIZES[-1]  # return the largest size by default

    def processAlgorithm(self, parameters, context, feedback):
        
        raw_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        
        if raw_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        raw_fields = raw_layer.fields()
        
        '''names of fields from Tile Network''' 
        linez_id = self.parameterAsString(parameters, self.SEGMENT_KEY, context)
        tile_to_id = self.parameterAsString(parameters, self.TILE_TO_KEY, context)
        order_id = self.parameterAsString(parameters, self.ORDER_KEY, context)
        length_id = self.parameterAsString(parameters, self.LENGTH_KEY, context)
        slope_id = self.parameterAsString(parameters, self.SLOPE_KEY, context)

        spacing = self.parameterAsDouble(parameters, self.SPACING_KEY, context)
        
        materials = self.parameterAsEnum(parameters, self.PIPE_KEY, context)        
        intensity = self.parameterAsEnum(parameters, self.INTENS_KEY, context)
        
        e_others = self.parameterAsDouble(parameters, self.ASS_INTENS_KEY, context)
        use_e_others = self.parameterAsBoolean(parameters, self.USE_ASS_KEY, context)

        coff_id = self.parameterAsEnum(parameters, self.COFF_KEY, context)
        seg_coff_id = self.parameterAsString(parameters, self.SEG_COFF_KEY, context)
        
        '''add new fields'''
        #define new fields
        out_fields = QgsFields()
        #append fields
        for field in raw_fields:
            out_fields.append(QgsField(field.name(), field.type()))
        out_fields.append(QgsField(self.D_COEFF_KEY, QVariant.String))
        out_fields.append(QgsField(self.FLOW_KEY, QVariant.String))
        out_fields.append(QgsField(self.PIPE_SIZE_KEY, QVariant.String))
        out_fields.append(QgsField(self.NOMINAL_PIPE_SIZE_KEY, QVariant.String))        

        '''Counter for the progress bar'''
        total = raw_layer.featureCount()
        parts = 100 / total

        '''load data from layer "raw_layer" '''
        feedback.setProgressText(self.tr("Loading network layer\n "))

        total = raw_layer.featureCount()
        total = 100.0/total
        
        '''sink definition'''
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, out_fields, raw_layer.wkbType(), raw_layer.sourceCrs())
        
        '''add new features to sink'''
        feedback.setProgressText(self.tr("creating output \n"))

        use_intensity = self.INTENSITY_OPTIONS[intensity] if not use_e_others else float(e_others)
        order_coeffs_config = self.parameterAsString(parameters, self.ORDER_COFF_KEY, context)
        if len(order_coeffs_config) > 0:
            order_coeffs = [None] + list(map(lambda x : float(x.strip()), order_coeffs_config.split(',')))
        
        individual_flow_rates = {}
        sources_map = {}  # string to list[string]

        for (n, feature) in enumerate(raw_layer.getFeatures()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # fill individual flow
            order = int(feature[order_id])
            if coff_id == 0:  # use system assigned
                DCoeff = self.getCoeff(use_intensity, order)
            elif coff_id == 1:  # by line segment
                DCoeff = float(feature[seg_coff_id])
            elif coff_id == 2:
                DCoeff = order_coeffs[order]
            else:
                raise ValueError(f"Invalid coefficient choice index {coff_id}")
            length = float(feature[length_id])
            flow = self.getFlow(length, spacing, DCoeff)
            individual_flow_rates[feature[linez_id]] = flow

            # fill source map
            tile_from = feature[linez_id]
            tile_to = feature[tile_to_id]
            if tile_to in sources_map:
                sources_map[tile_to].append(tile_from)
            else:
                sources_map[tile_to] = [tile_from]

        flow_rates = {}
        
        def get_flow_rate(id):  # returns the flow rate of segment with id
            if id in flow_rates:
                return flow_rates[id]
            flow_sum = individual_flow_rates[id]
            if id in sources_map:
                for source in sources_map[id]:
                    flow_sum += get_flow_rate(source)
            flow_rates[id] = flow_sum
            return flow_sum

        for (n, feature) in enumerate(raw_layer.getFeatures()):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            # Add a feature in the sink
            outFt = QgsFeature(out_fields)
            outFt.setGeometry(feature.geometry())
            outFt.setAttributes(feature.attributes() + [None, None, None, None])

            flow = get_flow_rate(feature[linez_id])
            outFt[self.D_COEFF_KEY] = DCoeff
            outFt[self.FLOW_KEY] = flow
            outFt[self.PIPE_SIZE_KEY] = self.getPipeSize(flow, float(feature[slope_id]), materials)
            outFt[self.NOMINAL_PIPE_SIZE_KEY] = self.getNominalSize(outFt[self.PIPE_SIZE_KEY])
            sink.addFeature(outFt, QgsFeatureSink.FastInsert)
            
            # Update the progress bar
            feedback.setProgress(int(n * total))
        
        return {self.OUTPUT: dest_id}
