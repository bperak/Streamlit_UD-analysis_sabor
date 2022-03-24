import os
import math
import time
# import stream_udapi 
import numpy as np
import pandas as pd
from plotly.offline import plot
import plotly.graph_objs as go
import plotly.io as pio
import plotly.express as px
import streamlit as st
from PIL import Image
import igraph as ig
import louvain
import leidenalg




@st.cache(allow_output_mutation=True, suppress_st_warning=True)#allow_output_mutation=True
def Fgraph(df, source, target, weight, directed):
    #create df variable
    df=df[[source, target,  weight]]
    #create tuples from df.values
    tuples = [tuple(x) for x in df.values]
    #create igraph object from tuples
    G=ig.Graph.TupleList(tuples, directed = directed, edge_attrs=['weight'], vertex_name_attr='name', weights=False)
    #create vertex labels from name attr
    G.vs["label"]= G.vs["name"]
    G.vs["degree"]=G.vs.degree()
    G.vs['betweenness'] = G.betweenness(vertices=None, directed=directed, cutoff=None, weights='weight', nobigint=True)
    G.vs['shape']="circle"
    G.vs["pagerank"]=G.vs.pagerank(directed=directed, weights='weight')
    G.vs["color"] = "rgba(255,0,0,0.2)"
    G.vs["weighteddegree"] = G.strength(G.vs["label"], weights='weight', mode='ALL')
    # G.vs["personalized_pagerank"]=G.vs.personalized_pagerank(directed=False, weights='weight')
    # Community detection
    # G.vs["community"] = G.community_edge_betweenness(directed=False)
    # G.vs["eigenvector"] = G.evcent(directed=True, scale=True, weights=None, return_eigenvalue=False)
    return(G)

####################################FgraphDraw
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
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

#Cluster algorithm
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def cluster_Algo(Fgraph, algorithm, partitionType, resolution):
    G= Fgraph
    # Leiden
    if algorithm == 'leiden':
        #Modularity Vertex Partition
        if partitionType == 'mvp':
            partition = leidenalg.find_partition(G, leidenalg.ModularityVertexPartition)
        #CPM Vertex Partition applies resolution_parameter (1 - every node is a community | 0- all nodes areone community)
        if partitionType == 'cpm':
            # resolution = st.slider('Resolution', 0.0, 1.0, 0.5)
            partition = leidenalg.find_partition(G, leidenalg.CPMVertexPartition, resolution_parameter=resolution)
    
    # Louvain
    if algorithm == 'louvain':
        #Modularity Vertex Partition
        if partitionType == 'mvp':
            partition = louvain.find_partition(G, louvain.ModularityVertexPartition)
        # #CPM Vertex Partition applies resolution_parameter (1 - every node is a community | 0- all nodes areone community)
        if partitionType == 'cpm':
            # resolution = st.slider('Resolution', 0.0, 1.0, 0.5)
            partition = louvain.find_partition(G, louvain.CPMVertexPartition, resolution_parameter=resolution)
    return (partition)


#############################################ClusterAlgoDraw
#@st.cache()#allow_output_mutation=True, suppress_st_warning=True
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

###############################################
# Fgraph image in plotly
# https://plotly.com/python/text-and-annotations/


@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def FgraphDraW_plotly(Fgraph, layout, vertexSize, vertexLabelSize, imageName, edgeLabelSize, songSelected):
    # vertex and edges atributes of Fgraph are treated as lists 
    G=Fgraph
    labels=G.vs['label']
    betweenness=G.vs['betweenness']
    degree = G.vs['degree']
    # Define edge sizes
    edgeSize =1
    N=len(labels)
    E=[e.tuple for e in G.es]# list of edges
    layt=G.layout(layout)
    ## node x, y components of the network
    Xn=[layt[k][0] for k in range(N)]
    Yn=[layt[k][1] for k in range(N)]
    ## edges from the layout
    Xe=[]
    Ye=[]
    for e in E:
        Xe+=[layt[e[0]][0],layt[e[1]][0], None]
        Ye+=[layt[e[0]][1],layt[e[1]][1], None]
    ## Figure
    fig=go.Figure(go.Scatter(x=Xe, y=Ye,
                mode='lines', name='Edges',
                line= dict(color='rgba(210,210,210, 0.4)', width=edgeSize),
                hoverinfo='none'
                ))
    fig.add_trace(go.Scatter(x=Xn, y=Yn,
                mode='markers+text', name='Lemma',
                marker=dict(symbol='circle-dot', 
                            size= [math.log(1/(1/(i+4)))*vertexSize for i in betweenness],
                            color=G.vs['color'],
                            line=dict(color='rgba(50,50,50, 0.2)', 
                            width=0.5)
                                ),
                text=labels, 
                textfont=dict(
                            family="sans serif",
                            size=[math.log(1/(1/(i+5)))*vertexLabelSize*0.6 for i in degree],
                            color='rgba(0,0,0,0.5)'#"crimson"
                        ),
                customdata= G.vs['betweenness'],
                hovertemplate = 
                    "<i>%{text}</i><br>"+"Betweenness: %{customdata}"
                #customdata=sentence_from_lemma(songSelected, labels)['sentence'].values[0]
                ))
    fig.update_layout(title='', showlegend=False, autosize=False,hovermode='closest',
                width=1000, height=1000, margin=dict(l=10, r=0, t=20, b=0),
                paper_bgcolor = 'rgba(0,0,0,0)', plot_bgcolor = 'rgba(0,0,0,0)',
                annotations=[dict(showarrow=False, text='Igraph representation in Plotly', xref='paper', yref='paper',
                x=0, y=-0.1, xanchor='left', yanchor='bottom', font=dict(size=14))], 
                xaxis=dict(showline=False, # hide axis line, grid, ticklabels and  title
                    zeroline=False, showgrid=False, showticklabels=False, title=''),
                yaxis=dict(showline=False, # hide axis line, grid, ticklabels and  title
                    zeroline=False, showgrid=False, showticklabels=False,title=''),
                )
    # config = dict({'scrollZoom': True, 'displaylogo': False, 'displayModeBar': True})
    # fig.write_html('plotly.html',config=config)
    # fig.click_fn(trace, points, state)
    return (fig)
