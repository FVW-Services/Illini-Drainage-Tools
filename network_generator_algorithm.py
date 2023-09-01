# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterNets
                                 A QGIS plugin
 This plugin calculates flowpaths
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------        
        begin                : 2019-07-26
        copyright            : (C) 2020 by Jannik Schilling
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
__date__ = '2020-01-26'
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
from qgis.core import QgsProcessingParameterVectorDestination

import time

class NetworkGeneratorAlgorithm(QgsProcessingAlgorithm):
    INPUT_LINE = 'INPUT_LINE'
    REVERSE_OPTION = 'REVERSE_OPTION'
    INPUT_FIELD_ID = 'INPUT_FIELD_ID'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)
        
    def createInstance(self):
        return NetworkGeneratorAlgorithm()
        
    def name(self):
        return 'g. Tile Network Generator'

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
        return self.tr("""This tool creates a connected Network of Tile Lines using each line segment of a vector line layer. 
        It is the routine that serves as the "check for topologically-sound networks".
        
        Workflow: 
        1. Select a Vector Line layer that is Topologically Sound. This is a follow-up from "Routine F"
        2. On the Map Canvas, select an outlet line segment from the displayed line layer
        3. Save the output file (optional)        
        4. Click on \"Run\"
        
        The script will give out an output with default names as:
               
        \"Tile Network\" -- The is the Tile Network for the entire line segments
        
        The help link in the Graphical User Interface (GUI) provides more information about the plugin.        
        """) 
        
    def helpUrl(self):
        return "https://publish.illinois.edu/illinoisdrainageguide/files/2022/06/PublicAccess.pdf" 
    
       
    def initAlgorithm(self, config=None):        
        self.addParameter(QgsProcessingParameterVectorLayer(self.INPUT_LINE, self.tr('Rebuilt Tile Lines with Fixed Geometries'), [QgsProcessing.TypeVectorLine]))      
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, self.tr('Tile Network')))    
        
    def processAlgorithm(self, parameters, context, feedback):
                                                           
        source = self.parameterAsSource(parameters, self.INPUT_LINE, context)
        
        flip_opt = self.parameterAsString(parameters, self.REVERSE_OPTION, context)
        
        raw_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LINE, context)
        
        if raw_layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        raw_fields = raw_layer.fields()

        '''Counter for the progress bar'''
        total = raw_layer.featureCount()
        parts = 100/total 

        '''optional: Existing ID field'''
        id_field = self.parameterAsString(parameters, self.INPUT_FIELD_ID, context)
        if len(id_field) == 0:
            pass
        else:
            idxid = raw_layer.fields().indexFromName(id_field)

        '''check if one feature is selected'''
        sel_feat = raw_layer.selectedFeatures() #selected Feature
        if not sel_feat:
            feedback.reportError(self.tr('{0}: No segment selected. Please select outlet in layer "{1}" ').format(self.displayName(), parameters[self.INPUT_LINE]))
            raise QgsProcessingException()
        if len(sel_feat) > 1:
            feedback.reportError(self.tr('{0}: Too many segments selected. Please select outlet in layer "{1}" ').format(self.displayName(), parameters[self.INPUT_LINE]))
            raise QgsProcessingException()
        
        '''add new fields'''
        #define new fields
        out_fields = QgsFields()
        #append fields
        for field in raw_fields:
            out_fields.append(QgsField(field.name(), field.type()))
        out_fields.append(QgsField('TILE_ID', QVariant.String))
        out_fields.append(QgsField('TILE_TO', QVariant.String))
        out_fields.append(QgsField('TILE_FROM', QVariant.String))
        
        '''get features'''
        feedback.setProgressText(self.tr("Loading line layer\n "))
        def get_features_data(ft):
            ge = ft.geometry()
            if ge.isMultipart():
                vert1 = ge.asMultiPolyline()[0][0]
                vert2 = ge.asMultiPolyline()[0][-1]
            else: 
                vert1 = ge.asPolyline()[0]
                vert2 = ge.asPolyline()[-1]
            vert1x = [str(vert1.x())[:15],"_",str(vert1.y())[:15]]
            vert2x = [str(vert2.x())[:15],"_",str(vert2.y())[:15]]
            SP1 = "".join(str(x) for x in vert1x)
            SP2 = "".join(str(x) for x in vert2x)
            if len(id_field) == 0:
                return [SP1,SP2,ft.id(),"NULL"]
            else:
                column_id = str(ft.attribute(idxid))
                return [SP1,SP2,column_id,"NULL",ft.id()]
        data_list = [get_features_data(f) for f in raw_layer.getFeatures()]
        data_arr = np.array(data_list)
        feedback.setProgressText(self.tr("Data loaded without problems\n "))

        '''id of actual/first segment'''
        if len(id_field) == 0:
            act_id = str(sel_feat[0].id())
        else:
            act_id = str(sel_feat[0].attributes()[idxid])

        '''first segment'''
        act_segm = data_arr[np.where(data_arr[:,2] == act_id)][0]
                
        '''mark segment as outlet'''
        out_marker = "Out"
        data_arr[np.where(data_arr[:,2] == act_segm[2])[0][0],3] = out_marker

        '''store first segment and delete from data_arr'''
        finished_segm = data_arr[np.where(data_arr[:,2]==act_id)]
        data_arr = np.delete(data_arr, np.where(data_arr[:,2]==act_id)[0],0)

        '''find connecting vertex of act_segm, flip if conn_vert is not vert1'''
        if np.isin(act_segm[1], np.concatenate((data_arr[:,0],data_arr[:,1]))):
            if np.isin(act_segm[0], np.concatenate((data_arr[:,0],data_arr[:,1]))):
                feedback.reportError(self.tr('The selected segment is connecting two segments. Please chose another segment in layer "{0}" or add a segment as a single outlet').format(parameters[self.INPUT_LINE]))
                raise QgsProcessingException()
            else:
                if len(id_field) == 0:
                    flip_list = [act_id]
                else:
                    flip_list = [act_segm[4]]
                vert_save = np.copy(act_segm[0])
                act_segm[0] = act_segm[1]
                act_segm[1] = vert_save
        else:
            flip_list = []

        '''function to find the next segment upstream'''
        #connecting vertex of a_segm is always act_segm[0]
        def nextftsConstr (a_segm, flp_list):
                conn_vert = a_segm[0]
                if np.isin(conn_vert,data_arr[:,1]) or np.isin(conn_vert,data_arr[:,0]):
                    n_segm1 = data_arr[data_arr[:,1] == conn_vert]
                    n_segm0 = data_arr[data_arr[:,0] == conn_vert]
                    if len(n_segm0) > 0:
                        '''turn vertice information if conn_vert in data_arr[:,0]'''
                        vert_save = np.copy(n_segm0[:,0])
                        n_segm0[:,0] = n_segm0[:,1]
                        n_segm0[:,1] = vert_save
                        if len(id_field) == 0:
                            flp_list = flp_list + n_segm0[:,2].tolist()
                        else:
                            flp_list = flp_list + n_segm0[:,4].tolist()
                    n_segm = np.concatenate((n_segm1,n_segm0))
                else:
                    n_segm=n_segm = np.array([])
                    conn_vert = 'None'
                return([n_segm,conn_vert,flp_list])


        '''this function will find circles'''
        def checkForCircles (ne_segm, conn_v):
                    all_finished_pts = np.concatenate((finished_segm[:,0],finished_segm[:,1]))
                    all_act_pts = np.concatenate((ne_segm[:,0],ne_segm[:,1]))
                    pts_count = Counter(all_act_pts)
                    count_arr = np.array(list(pts_count.items()))
                    '''Option 1: any vertex of ne_segm already is in finished_segm'''
                    count_arr2 = np.delete(count_arr, np.where(count_arr[:,0] == conn_v)[0],0)
                    circ_segm1 = ne_segm[np.all(np.isin(ne_segm[:,:2],all_finished_pts),axis = 1)]
                    circ_segm2 = finished_segm[np.any(np.isin(finished_segm[:,:2],count_arr2[:,0]), axis= 1)]
                    circ_segm = np.array(circ_segm2.tolist()+circ_segm1.tolist())
                    if len (circ_segm) > 0:
                        circ_id = [circ_segm[:,2].tolist()]
                    else: 
                        circ_id = []
                    '''Option 2: two (or more) segments of ne_segm form a circle'''
                    if len(ne_segm) > 1:
                        count_arr3 = np.delete(count_arr, np.where(count_arr[:,1] == '1')[0],0)
                        circ_segm = ne_segm[np.all(np.isin(ne_segm[:,:2],count_arr3[:,0]),axis = 1)]
                        circ_id = circ_id + [circ_segm[:,2].tolist()]
                    circ_ids = [x for x in circ_id if x]
                    return (circ_ids)

        '''list to save circles if the algothm finds one'''
        circ_list = list()

        ''' "do later list" with 'X' as marker'''
        do_later=np.array([np.repeat('X',len(act_segm))])

        i=1
        while len(data_arr) != 0:
            if feedback.isCanceled():
                    break
            '''id of next segment'''
            next_data = nextftsConstr(act_segm, flip_list)
            next_fts = next_data[0]
            conn_vertex = next_data[1]
            flip_list = next_data[2]
            '''check for circles'''
            if len(next_fts)>0:
                circ_segments = checkForCircles(next_fts, conn_vertex)
                circ_list = circ_list + circ_segments
            '''handle next features'''
            if len(next_fts) == 1:
                next_fts[:,3] = str(act_id)
                '''store finish segment and delete from data_arr'''
                finished_segm = np.concatenate((finished_segm,next_fts))
                data_arr = np.delete(data_arr,np.where(data_arr[:,2] == next_fts[:,2]),0)
                ''' upstream segment'''
                next_segm = next_fts[0]
            if len(next_fts) == 0:
                ''' upstream segment'''
                next_segm = do_later[0]
                do_later = do_later[1:]
            if len(next_fts) > 1:
                next_fts[:,3] = str(act_id)
                '''store first segment and delete from data_arr'''
                finished_segm = np.concatenate((finished_segm,next_fts))
                data_arr = np.delete(data_arr,np.where(np.isin(data_arr[:,2],next_fts[:,2])),0)
                ''' upstream segment'''
                do_later = np.concatenate((next_fts[1:],do_later))
                next_segm = next_fts[0]
            if next_segm[0] == 'X':
                break
            '''changing actual segment'''
            act_segm = next_segm
            act_id = act_segm[2]
            feedback.setProgress(100*(1-(len(data_arr)/total)))



        '''unconnected features'''
        data_arr[:,3] = 'unconnected'
        finished_segm = np.concatenate((finished_segm,data_arr))
        feedback.setProgressText(self.tr('network generated with {0} unconnected segments').format(str(len(data_arr))))


        '''sort finished segments for output'''
        if len(id_field) == 0:
            fin_order = [int(f) for f in finished_segm[:,2]]
        else:
            fin_order = [int(f) for f in finished_segm[:,4]]
            finished_segm = np.delete(finished_segm, 4,1)
        finished_segm = finished_segm[np.array(fin_order).argsort()]
        finished_segm = np.c_[finished_segm, finished_segm[:,2]]
        finished_segm[np.where(finished_segm[:,3] == 'unconnected'),4] = 'unconnected'


        '''feedback for circles'''
        if len (circ_list)>0:
            feedback.reportError("Warning: Circle closed at Tile_ID = ")
            for c in circ_list:
                feedback.reportError(self.tr('{0}, ').format(str(c)))               
                          
                          
            
        '''sink definition'''
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            raw_layer.wkbType(),
            raw_layer.sourceCrs())

        
        
        '''add features to sink'''
        features = raw_layer.getFeatures()
        for (i,feature) in enumerate(features):
            if feedback.isCanceled():
                break # Stop the algorithm if cancel button has been clicked
            outFt = QgsFeature() # Add a feature
            if flip_opt == '0':
                if str(i) in flip_list:
                    flip_geom = feature.geometry()
                    if flip_geom.isMultipart():
                        multi_geom = QgsMultiLineString()
                        for line in flip_geom.asGeometryCollection():
                            multi_geom.addGeometry(line.constGet().reversed())
                        rev_geom = QgsGeometry(multi_geom)
                    else:
                        rev_geom = QgsGeometry(flip_geom.constGet().reversed())
                    outFt.setGeometry(rev_geom)
                else:
                    outFt.setGeometry(feature.geometry())
            else:
                outFt.setGeometry(feature.geometry())
            outFt.setAttributes(feature.attributes()+finished_segm[i,2:].tolist())
            sink.addFeature(outFt, QgsFeatureSink.FastInsert)
            
        del i
        del outFt
        del features
        del checkForCircles
        del nextftsConstr
        return {self.OUTPUT: dest_id}
          
