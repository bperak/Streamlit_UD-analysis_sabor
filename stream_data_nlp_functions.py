# 1 Imports
import os
import math
import time
import stream_udapi 
import numpy as np
import pandas as pd
from plotly.offline import plot
import plotly.graph_objs as go
import plotly.io as pio
import streamlit as st
from PIL import Image
import igraph as ig
import louvain
import leidenalg

########################################Fgraph functions
@st.cache(allow_output_mutation=True)#allow_output_mutation=True
def Fgraph(df, source, target, weight):
    #create df variable
    df=df[[source, target, weight]]
    #create tuples from df.values
    tuples = [tuple(x) for x in df.values]
    #create igraph object from tuples
    G=ig.Graph.TupleList(tuples, directed = False, edge_attrs=['weight'], vertex_name_attr='name', weights=False)
    #create vertex labels from name attr
    G.vs["label"]= G.vs["name"]
    G.vs["degree"]=G.vs.degree()
    G.vs['betweenness'] = G.betweenness(vertices=None, directed=False, cutoff=None, weights=None, nobigint=True)
    G.vs['shape']="circle"
    G.vs["pagerank"]=G.vs.pagerank(directed=False, weights='weight')
    G.vs["color"] = "rgba(255,0,0,0.2)"
    # G.vs["personalized_pagerank"]=G.vs.personalized_pagerank(directed=False, weights='weight')
    # Community detection
    # G.vs["community"] = G.community_edge_betweenness(directed=False)
    # G.vs["eigenvector"] = G.evcent(directed=True, scale=True, weights=None, return_eigenvalue=False)
    return(G)

####################################FgraphDraw
@st.cache(allow_output_mutation=True)
def FgraphDraw(Fgraph, layout, vertexSize, vertexLabelSize, imageName, edgeLabelSize, authors):
    G = Fgraph
    visual_style = {}
    visual_style["vertex_size"] = [math.log(1/(1/(i+1)))*vertexSize for i in G.vs["betweenness"]]#vertexSize
    visual_style["vertex_label_color"] = "rgba(0,0,0,0.7)"
    visual_style["vertex_label_size"] = [math.log(1/(1/(i+10)))*vertexLabelSize for i in G.vs["degree"]] #maybe it could be G.vs["degree"]
    visual_style["vertex_color"] = G.vs["color"]#"rgba(255,0,0,0.1)"
    visual_style["vertex_shape"]= G.vs['shape']
    visual_style["vertex_label_dist"] = 0
    visual_style["edge_color"] = G.vs['color']
    visual_style["edge_width"] = G.es["weight"]
    visual_style["edge_label"] = G.es["weight"]
    visual_style["edge_label_size"] = edgeLabelSize
    visual_style['hovermode'] = 'closest'
    visual_style["layout"] = layout#G.layout_fruchterman_reingold(weights=G.es["weight"], maxiter=1000, area=len(G.es)**3, repulserad=len(G.es)**3)#Glayout
    visual_style["bbox"] = (1500, 1500)
    visual_style["margin"] = 60
    visual_style["edge_curved"] = True
    ig.plot(G, imageName+".png", **visual_style)
    return(G)

#############################################ClusterAlgoDraw
@st.cache(allow_output_mutation=True)
def clusterAlgoDraw(Fgraph, clusterAlgo, layout, vertexSize, vertexLabelSize, imageName, edgeLabelSize, authors):
    G=Fgraph
    partition=clusterAlgo
    #Cluster Colors Programatic Method
    palette = ig.drawing.colors.ClusterColoringPalette(len(partition))
    #Vertex transparency
    vtransparency = 0.1 # vertex transparency
    G.vs['color'] = palette.get_many(partition.membership)
    vcolors=[]  
    for v in G.vs['color']:
        #convert tuples to list
        vcolor=list(v)
        #add opacity value
        vcolor[3]= vtransparency
        vcolor=tuple(vcolor)
        vcolors.append(vcolor)
    G.vs['color'] = vcolors
    #Edge color transparency
    transparency = 0.3 # edges transparency
    G.es['color']="rgba(0,0,0,0.1)"
    for p in range(len(partition)): 
        edge = (G.es.select(_within = partition[p]))
        edge['color'] = palette.get_many(p)
        tr_edge=[]
        for c in edge['color']:
            #convert tuples to list, add opacity value, reconvert to tuples
            lst=list(c)
            #set opacity value
            lst[3]= transparency
            tr_edge.append(lst) 
        tr_edge=tuple(tr_edge)
        edge['color'] = tr_edge
    #visual_style settings
    visual_style = {}
    visual_style["vertex_size"] = [math.log(1/(1/(i+1)))*vertexSize for i in G.vs["betweenness"]]#vertexSize
    visual_style["vertex_label_color"] = "rgba(0,0,0,0.8)"
    visual_style["vertex_label_size"] = [math.log(1/(1/(i+10)))*vertexLabelSize for i in G.vs["degree"]] #maybe it could be G.vs["degree"]
    visual_style["vertex_color"] = G.vs["color"]
    visual_style["vertex_shape"]= G.vs['shape']
    visual_style["vertex_label_dist"] = 0
    visual_style["edge_color"] = G.es['color']
    visual_style["edge_width"] = G.es["weight"]
    visual_style["edge_label"] = G.es["weight"]
    visual_style["edge_label_size"] = edgeLabelSize
    visual_style['hovermode'] = 'closest'
    visual_style["layout"] = layout
    visual_style["bbox"] = (1500, 1500)
    visual_style["margin"] = 50
    visual_style["edge_curved"] = True 
    image= ig.plot(partition, imageName+".png", **visual_style)
    return (image)
