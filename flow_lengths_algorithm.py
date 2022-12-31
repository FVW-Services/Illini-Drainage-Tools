# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterNets
                                 A QGIS plugin
 This plugin calculates flowpaths
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-07-26
        copyright            : (C) 2019 by Jannik Schilling
        email                : jannik.schilling@uni-rostock.de
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

__author__ = 'Jannik Schilling'
__date__ = '2019-07-26'
__copyright__ = '(C) 2019 by Jannik Schilling'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import inspect
from qgis.PyQt.QtGui import QIcon

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import * 
import processing
import numpy as np
from collections import Counter

import time

class FlowLengthsAlgorithm(QgsProcessingAlgorithm):
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_FIELD_CALC = 'INPUT_FIELD_CALC'
    INPUT_FIELD_ID = 'INPUT_FIELD_ID'
    INPUT_FIELD_NEXT = 'INPUT_FIELD_NEXT'
    INPUT_FIELD_PREV = 'INPUT_FIELD_PREV'
    OUTPUT = 'OUTPUT'


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return FlowLengthsAlgorithm()
        
    def name(self):
        return 'k. Network Flow Lengths'

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
        return self.tr("""This tool calculates the cummulative lengths for all connecting line segments, upstream to downstream of the network layout.
                
        Workflow: 
        1. Select a Vector Line layer that is Topologically Sound. This is a follow-up from "Routine J"
        2. Select the Reference Field for the Cummulative Calculation of Segment lengths along the Tile Flow Line
        3. Select the respective Field IDs that represents the attribute tables from the displayed line layer
        4. Save the output file (optional)        
        5. Click on \"Run\"
        
        The script will give out an output with default names as:
               
        \"Cummulative Network Flow Lengths\" -- The is the cummulative Lenghts from Connecting the entire line segments in the Network
        
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.        
        """) 
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf" 
        
    
    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LAYER, self.tr('Tile Network Statistics'), [QgsProcessing.TypeVectorLine], defaultValue=None))
        
        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD_CALC, self.tr("True_Length: LENGTH"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Numeric, defaultValue=None))
        
        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD_ID, self.tr("Tile_ID"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None))
        
        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD_NEXT, self.tr("Tile_TO"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None))

        self.addParameter(QgsProcessingParameterField(self.INPUT_FIELD_PREV, self.tr("Tile_FROM"), parentLayerParameterName = self.INPUT_LAYER, type = QgsProcessingParameterField.Any, defaultValue=None))
                
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, self.tr('Cummulative Flow Lengths')))

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT_LAYER, context)
        
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        
        '''loading the network'''
        waternet = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        wnet_fields = waternet.fields()
        '''Counter for the progress bar'''
        total = waternet.featureCount()
        parts = 100/total 

        '''names of fields for id,next segment, previous segment'''
        id_field = self.parameterAsString(parameters, self.INPUT_FIELD_ID, context)
        next_field = self.parameterAsString(parameters, self.INPUT_FIELD_NEXT, context)
        prev_field = self.parameterAsString(parameters, self.INPUT_FIELD_PREV, context)
        calc_field = self.parameterAsString(parameters, self.INPUT_FIELD_CALC, context)
        
        '''field index for id,next segment, previous segment'''
        idxId = waternet.fields().indexFromName(id_field) 
        idxPrev = waternet.fields().indexFromName(prev_field)
        idxNext = waternet.fields().indexFromName(next_field)
        idxCalc = waternet.fields().indexFromName(calc_field)


        '''load data from layer "waternet" '''
        feedback.setProgressText(self.tr("Loading network layer\n "))
        Data = [[str(f.attribute(idxId)),str(f.attribute(idxPrev)),str(f.attribute(idxNext)),f.attribute(idxCalc)] for f in waternet.getFeatures()]
        DataArr = np.array(Data, dtype='object')
        DataArr[np.where(DataArr[:,3] == NULL),3]=0
        feedback.setProgressText(self.tr("Data loaded \n Calculating flow paths \n"))

        '''segments with numbers'''
        calc_column = np.copy(DataArr[:,3]) #deep copy of column to do calculations on
        calc_segm = np.where(calc_column > 0)[0].tolist() 
        DataArr[:,3] = 0 # set all to 0

        '''function to find next features in the net'''
        def nextFtsCalc (MARKER2):
            vtx_to = DataArr[np.where(DataArr[:,0] == MARKER2)[0].tolist(),2][0] # "to"-vertex of actual segment
            rows_to = np.where(DataArr[:,1] == vtx_to)[0].tolist() # find rows in DataArr with matching "from"-vertices to vtx_to
            return(rows_to)

        '''function to find flow path'''
        def FlowPath (Start_Row, fp_amount):
            MARKER=DataArr[Start_Row,0] #set MARKER to ID of the first segment
            Weg = [Start_Row]    
            i=0
            while i!=len(DataArr):
                next_rows = nextFtsCalc(MARKER)
                if len(next_rows) > 1: # deviding flow path
                    calc_column[StartRow] = 0
                    calc_column[next_rows] = calc_column[next_rows]+fp_amount/len(next_rows) # this can be changed to weightet separation later
                    out = [Weg, next_rows]
                    break
                if len(next_rows) == 1: # continuing flow path
                    Weg = Weg + next_rows
                    MARKER=DataArr[next_rows[0],0] # change MARKER to Id of next segment 
                if len(next_rows) == 0: # end point
                    out = [Weg]
                    break
                i=i+1
            return (out)

        total2 = len(calc_segm)
        while len(calc_segm) > 0:
            if feedback.isCanceled():
                break
            StartRow = calc_segm[0]
            amount = calc_column[StartRow] # amount to add to flow path
            calc_column[StartRow] = 0 #"delete" calculated amount from list (set 0)
            Fl_pth = FlowPath(StartRow, amount) # get flow path of StartRow 
            if len(Fl_pth)== 2:
                calc_segm = calc_segm + Fl_pth[1] # if flow path devides add new segments to calc_segm
            DataArr[Fl_pth[0],3] = DataArr[Fl_pth[0],3]+amount # Add the amount to the calculated flow path
            calc_segm = calc_segm[1:] # delete used segment
            calc_segm = list(set(calc_segm)) #delete duplicate values
            feedback.setProgress((1-(len(calc_segm)/total2))*100)

        '''add new field'''
        new_field_name = 'FLOW_'+calc_field
        #define new fields
        out_fields = QgsFields()
        #append fields
        for field in wnet_fields:
            out_fields.append(QgsField(field.name(), field.type()))
        out_fields.append(QgsField(new_field_name, QVariant.Double))


        '''sink definition'''
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            source.wkbType(),
            source.sourceCrs())

        '''create output / add features to sink'''
        feedback.setProgressText(self.tr("creating output \n"))
        features = waternet.getFeatures()
#        i=0
        for (i,feature) in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            # Add a feature in the sink
            outFt = QgsFeature()
            outFt.setGeometry(feature.geometry())
            outFt.setAttributes(feature.attributes())
            outFt.setAttributes(feature.attributes()+[DataArr[i,3]])
            sink.addFeature(outFt, QgsFeatureSink.FastInsert)
            feedback.setProgress((i+1)*parts)

        return {self.OUTPUT: dest_id}

        del nextFtsCalc
        del FlowPath
        del DataArr


        return {}