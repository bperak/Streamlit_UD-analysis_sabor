# -*- coding: utf-8 -*-
# This is a main .py code for the Croatian Parliamentary Corpus 

# 1 Imports
import os
import math
import time
# import stream_udapi 
import streamGraph
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


####################################### Connecting to the Neo4j Database
from py2neo import Graph
try:
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "kultura"))   
except:
    print ("Could not connect to dedicated Neo4j graph database")
    pass    
# st.write(graph.run('''call db.index.fulltext.createNodeIndex('IzjavaTekst','ljubav') YIELD node RETURN node id '''))

pretrazi = st.text_input('Pretraži izjave')
if pretrazi:
    nodes = graph.run('''CALL db.index.fulltext.queryNodes("IzjavaTekst", "''' + pretrazi + '''") YIELD node
    RETURN id(node), node.author, node.transkript, node.date''').to_data_frame()
    st.write(nodes)

# stream_udapi.createIndexes() 
# stream_udapi.createIndexes() 


indeksiOnline= '''
#indeksi
ON :Izjava(author) ONLINE
ON :Izjava(redniBrojIzjave) ONLINE
ON :Izjava(tockaDnevnogRedaID) ONLINE
ON :Izjava(tockaDnevnogRedaId) ONLINE
ON :Lemmas(name) ONLINE
ON :SazivSabora(broj) ONLINE
ON :Sentences(izjava_unique) ONLINE
ON :Sentences(sent_id) ONLINE
ON :Sjednica(broj) ONLINE
ON :Sjednica(name) ONLINE
ON :TockaDnevnogReda(name) ONLINE
ON :TockaDnevnogReda(tockaDnevnogRedaID) ONLINE
ON :Tokens(ID) ONLINE
ON :Tokens(deps) ONLINE
ON :Tokens(feats) ONLINE
ON :Tokens(fileName) ONLINE
ON :Tokens(form) ONLINE
ON :Tokens(head) ONLINE
ON :Tokens(id) ONLINE
ON :Tokens(lemma) ONLINE
ON :Tokens(sent_unique) ONLINE
ON :Tokens(textName) ONLINE
ON :Words(POS) ONLINE
ON :Words(POStag) ONLINE
ON :ZastupnickiKlub(name) ONLINE
ON :Zastupnik(name) ONLINE
ON NODE:Izjava(transkript) ONLINE
ON NODE:Sentences(text) ONLINE
ON :Izjava(izjava_unique) ONLINE (for uniqueness constraint)
ON :Lemmas(lempos) ONLINE (for uniqueness constraint)
ON :Sentences(sent_unique) ONLINE (for uniqueness constraint)
ON :Tokens(token_unique) ONLINE (for uniqueness constraint)

'''
unique_upostags=["SYM","PROPN","NOUN","INTJ","ADP","CCONJ","PRON","ADV","DET","VERB","X","SCONJ","PUNCT","AUX","NUM","ADJ","PART"]



@st.cache()
def zastupnici():
    qAuthors='''
    MATCH (n:Zastupnik)
    return n.name as author
    '''
    df = graph.run(qAuthors).to_data_frame()
    return df

########################################################Streamlit start 
st.sidebar.title('Croatian Parliament analysis')

df_authors= zastupnici()
author= st.sidebar.selectbox('Odaberi zastupnika', df_authors['author'])
'', author

lemma= st.sidebar.text_input('Odaberi riječ', 'demokracija')
'', lemma

upostag= st.sidebar.text_input('Odaberi vrstu riječi', 'NOUN')
'', upostag


date= st.sidebar.text_input('choose a date', '')
'', date

deprel= st.sidebar.text_input('choose a dependency relation')
'', deprel

upostag2 =st.sidebar.text_input("Choose second upostag", 'NOUN')
'', upostag2


########
if st.checkbox('0: Count lemmas with upostag: '+upostag):
    @st.cache()
    def lemma_count(upostag):
        q='''
        //
        MATCH (n:Tokens{upostag:$upostag}) 
        with n.lemma as lemma, count(n.lemma) as count 
        return lemma, count order by count desc
        '''
        df=graph.run(q, upostag=upostag).to_data_frame()
        
        return (df)
    df0=lemma_count(upostag)
    'Lemmas Count', df0
    # draw utterances per author
    fig= px.bar(df0[0:50], x='lemma', y='count')
    st.plotly_chart(fig)
########
if st.checkbox('1: Utterances count per Author'):
    def utterances_per_author():
        q='''
        //how many Izjava per Author
        MATCH (n:Izjava{najava:"FALSE"}) 
        with n.author as author 
        return author, count(author) as count order by count desc
        '''
        df=graph.run(q).to_data_frame()
        return df
    uPerAuth= utterances_per_author()

    'Utterances count per Author', uPerAuth 
    # draw utterances per author
    fig= px.bar(uPerAuth[0:50], x='author', y='count')
    st.plotly_chart(fig)


    @st.cache()
    def tokens_per_author():
        q='''
        MATCH (z:Zastupnik)
        with z.name as author
        MATCH (i:Izjava{author:author})-[:HAS_sentence]-(:Sentences)-[:HAS_token]-(t:Tokens)
        with author, count(t) as countT
        return author, countT order by countT desc
        '''
        df= graph.run(q).to_data_frame()
        return df
    tok_per_a= tokens_per_author()
    'Tokens per Author', tok_per_a

    #join two df 
    frames=[uPerAuth, tok_per_a]
    result= uPerAuth.join(tok_per_a.set_index('author'), on='author')
    result['tokPerUt'] = result['countT']/result['count']
    'result', result

####
if st.checkbox('2: Utterances count per Author on a date:'):
    q2='''
    //how many Izjava per Author on any date
    MATCH (n:Izjava) with n.author as author, n.date as date return author, date, count(author) as count order by count desc
    '''
    df2=graph.run(q2).to_data_frame()
    '2: Utterances count per Author on a date:'+date, df2

#######
if st.checkbox('3: how many Izjava per Author on a date'):
    q3='''
    //how many Izjava per Author on a date
    MATCH (n:Izjava) where n.date=$date with n.author as author, n.date as date return author, date, count(date) as count order by count desc
    '''
    df3=graph.run(q3, date=date).to_data_frame()
    '3: how many Izjava per Author on a date', df3

######
if st.checkbox('4: find sentences with lemma:'+lemma+' and upostag:'+upostag):    
    q4='''
    //find sentence and author by lemma+upostag
    match (i:Izjava)-[:HAS_sentence]->(s:Sentences)-[:HAS_token]->(t:Tokens)
    where t.lemma starts with $lemma and t.upostag=$upostag
    return t.form, count(t), i.author, i.date, s.text
    '''
    df4=graph.run(q4, lemma=lemma, upostag=upostag).to_data_frame()
    '4: find sentences with lemma:'+lemma+' and upostag:'+upostag, df4

#######
if st.checkbox('5: find sentences from author: '+author+', lemma: '+lemma+', upostag: '+upostag):
    q5='''
    //find sentences by author with lemma+upostag
    match (i:Izjava)-[:HAS_sentence]->(s:Sentences)-[:HAS_token]->(t:Tokens{lemma:$lemma, upostag:$upostag})
    where i.author starts with  $author
    return i.author, i.date, t.form, count(t),  s.text
    '''
    df5=graph.run(q5, author=author, lemma= lemma, upostag=upostag).to_data_frame()
    '5: find sentences from author: '+author+', lemma: '+lemma+', upostag: '+upostag, df5

def first_order_lemma(lemma, upostag, deprel, upostag2, limit):
        q='''
        match (t:Tokens{lemma:$lemma,upostag:$upostag})
        with t
        match (t)-[d:HAS_deprel{deprel:$deprel}]->(t2:Tokens{upostag:$upostag2})
        where t2.lemma <> t.lemma
        return t.lemma as source ,t2.lemma as target, count(t) as count order by count desc limit $limit
        '''
        df=graph.run(q, author=author, lemma=lemma, deprel=deprel, upostag=upostag, upostag2=upostag2, limit=limit).to_data_frame()
        return df

def first_order_author(author, upostag, deprel, upostag2):
        q='''
        //find dependency author
        match (z:Zastupnik) where z.name starts with $author
        with z.name as author  
        match (i:Izjava{author:author})-[:HAS_sentence]->(s:Sentences)-[:HAS_token]->(t:Tokens{upostag:$upostag})-[d:HAS_deprel{deprel:$deprel}]->(t2:Tokens{upostag:$upostag2})
        return t.lemma as source ,t2.lemma as target, count(t) as count order by count desc
        '''
        df=graph.run(q, author=author, deprel=deprel, upostag=upostag, upostag2=upostag2).to_data_frame()
        return df

def first_order_author_lemma(author, lemma, upostag, deprel, upostag2):
        q='''
        //find dependency author
        match (z:Zastupnik) where z.name starts with $author
        with z.name as author  
        match (i:Izjava{author:author})-[:HAS_sentence]->(s:Sentences)-[:HAS_token]->(t:Tokens{lemma:$lemma,upostag:$upostag})-[d:HAS_deprel{deprel:$deprel}]->(t2:Tokens{upostag:$upostag2})
        return t.lemma as source ,t2.lemma as target, count(t) as count order by count desc
        '''
        df=graph.run(q, author=author, lemma=lemma, deprel=deprel, upostag=upostag, upostag2=upostag2).to_data_frame()
        return df

###
if st.checkbox('6:  find dependency from author: '+author+', upostag: '+upostag+', dependency relation: '+deprel+' upostag2: '+upostag2):
    df6=first_order_author(author, upostag, deprel, upostag2)
    'Result', df6
###
if st.checkbox('7: Lemma dep upostag2'):  
    qLemma='''
        match (t:Tokens{lemma:$lemma, upostag:$upostag})
        return t.lemma, count(t) as freq
    '''
    lemmmaCount=graph.run(qLemma,lemma=lemma, upostag=upostag).to_data_frame()
    'Lemma'+lemma, lemmmaCount

    qLemmaDeprel='''
    match (t:Tokens{lemma:$lemma, upostag:$upostag})-[:HAS_deprel{deprel:$deprel}]->(t2:Tokens) 
    where t2.upostag=$upostag2 //and t2.lemma<>t.lemma
    return t.lemma, t2.lemma as collocation, count(t2) as frequency order by frequency desc
    ''' 
    lemmaDeprel= graph.run(qLemmaDeprel,lemma=lemma, upostag=upostag, upostag2=upostag2, deprel=deprel).to_data_frame()
    'Lemma deprel', lemmaDeprel
    # draw utterances per author
    fig= px.bar(lemmaDeprel[0:50], x='collocation', y='frequency',log_y=True)
    st.plotly_chart(fig)


###
if st.checkbox('8: Lemma per Representative proportions'):
    targetLema=lemma
    '''Upiši targetLema da vidiš :
        koliko se ukupno pojam pojavljuje, koji mu je udio u korpusu
        koliko je neki autor puta rekao taj pojam, koji je udio njegove pojavnosti u ukupnoj pojavnosti u korpusu 
        koliki je udio tog pojma u broju riječi autora
    '''
    #dataframe to collect the results
    # df7=pd.DataFrame()


    q1='''
    match (t:Tokens) return count(t) as allFreq
    '''
    d1=graph.run(q1).data()
    allFreq=d1[0]['allFreq'] #overall number of the tokens in the corpora
    'allFreq', allFreq

    q2='''
    match (t:Tokens) where t.lemma=$targetLema
    return count(t) as lemaFreq
    '''
    d2=graph.run(q2, targetLema=targetLema).data()
    lemaFreq=d2[0]['lemaFreq'] #frequency of the tokens for a lemma in the corpus
    'lemaFreq (lemma occurence in corups)', lemaFreq
    lemaPercentAll=(lemaFreq/allFreq) #procent of the lemma occurence in the corpus
    'lemaPercentAll (proportion of lemma occurence in corpus):', lemaPercentAll
    q3='''
    match (i:Izjava)-[:HAS_sentence]->(s:Sentences)-[:HAS_token]-(t:Tokens{lemma:$targetLema})
    with count(t) as lemaFreqPerAuth, i.author as author 
    return  $lemaFreq as lemaFreq,
            $lemaPercentAll as lemaPercentAll, 
            lemaFreqPerAuth, 
            (toFloat(lemaFreqPerAuth)/($allFreq)) as lemaPercPerAuth, 
            author 
            order by lemaFreqPerAuth desc limit 10
    '''
    d3=graph.run(q3, targetLema=targetLema, allFreq=allFreq, lemaFreq=lemaFreq, lemaPercentAll=lemaPercentAll)
    # dd8=d3.to_data_frame()


    # 'dd8', dd8
    #print ((list(d3), targetLema))

    for d in d3:
        lemaFreqPerAuth=(d3["lemaFreqPerAuth"])
        lemaPercPerAuth=(d3["lemaPercPerAuth"])
        name = (d3["author"])
        #print(name)

        q4='''
        match (a:Zastupnik{name:$name})-[:DELIVERED_izjavu]->(i2:Izjava)-[:HAS_sentence]->(s2:Sentences)-[:HAS_token]->(t2:Tokens)
        with a.name as Zastupnik, count(t2) as freqLemaZastupnik order by freqLemaZastupnik
        return Zastupnik, freqLemaZastupnik, ((toFloat($lemaFreqPerAuth)/freqLemaZastupnik))  as lemaFreqPerAuthAll 
        order by lemaFreqPerAuthAll
        '''
        d4= graph.run(q4, name=name, lemaFreqPerAuth=lemaFreqPerAuth)
        dd4l=[]
        for dd in d4:
            freqLemaZastupnik=(d4["freqLemaZastupnik"])
            lemaFreqPerAuthAll=(d4["lemaFreqPerAuthAll"])
            st.markdown((name,  lemaFreqPerAuth, round(lemaPercPerAuth,9), freqLemaZastupnik,  round(lemaFreqPerAuthAll, 7)))     
            # df7['lemma']= targetLema
            # df7['lemmaFreq']= lemaFreq
            # df7['lemmaPercent'] = lemaPercentAll
            # df7['lemaFreqPerAuth']=lemaFreqPerAuth
            # df7['lemaPercPerAuth']=lemaPercPerAuth
            # df7['freqLemaZastupnik']= freqLemaZastupnik
            # df7['lemaFreqPerAuthAll']=lemaFreqPerAuthAll

    # 'df7',df7
    st.markdown("Lema, ukupni broj, freqInCorp, freqPerZastupnik, percPerZastupnik, ZastupnikAll, percLemaInZastupnikAll")
### second degree df
if st.checkbox('9: Network for Lemma'+lemma+'upostag'+ upostag+'deprel'+deprel+'upostag2'+upostag2): 
    @st.cache()
    def second_degree_lemma(lemma,upostag,deprel,upostag2, limit):
        first_df=first_order_lemma(lemma,upostag,deprel,upostag2, limit)
        #'first', first_df
        second_df=first_df
        for index, row in first_df.iterrows():
            try:
                friend_of_f=first_order_lemma(row['target'], upostag, deprel,upostag2, limit)
                second_df = second_df.append(friend_of_f, sort=True)
                second_df['logCount']=np.log10(second_df['count'])+0.001
            except:
                pass
        return second_df
    
    secondD= second_degree_lemma(lemma,upostag,deprel,upostag2, 50)
    'Result', secondD
    g=streamGraph.Fgraph(secondD, 'source', 'target', 'logCount', False)
    pruning_degree=st.slider('Set the degree', 0, 20, 2)
    pruned_vs=g.vs.select(degree_ge=pruning_degree)
    g=g.subgraph(pruned_vs)
    algorithmType= st.selectbox('Select clustering algorithm', ['mvp', 'cpm'])
    resolution=st.slider('Select resolution for cpm', 0.0, 1.0, 0.5)
    clust= streamGraph.cluster_Algo(g, 'louvain', algorithmType, resolution)
    '', clust
    if st.checkbox('Visualize network'):
        streamGraph.clusterAlgoDraw(g, clust, 'fr', 2, 7, '2nd', 0, author)
        secondD_image = Image.open('2nd.png')
        st.image(secondD_image,use_column_width=True)

if st.checkbox('10: Network for Lemmma'+lemma+'upostag'+upostag+'deprel'+deprel+'upostag2'+upostag2+'zastupnik'):
    # odlično radi i brzo
    def zastupnik_lemma_dep(lemma, upostag, deprel, upostag2):
        q='''
        match (t:Tokens{lemma:$lemma, upostag:$upostag})-[r:HAS_deprel{deprel:$deprel}]-(t2:Tokens{upostag:$upostag2})<-[:HAS_token]-(s:Sentences)<-[:HAS_sentence]-(i:Izjava)  
        where t.lemma <> t2.lemma
        with i.author as author,t2
        return $lemma as source, t2.lemma as target, author, count(t2) as count          
        order by count desc //limit 800
        '''
        df= graph.run(q, lemma=lemma, upostag=upostag, upostag2=upostag, deprel=deprel).to_data_frame()
        return (df)
    zld= zastupnik_lemma_dep(lemma, upostag, deprel, upostag2)
    'zld', zld
    'zastupnik per lemma-deprel-lemma', zld
    #graph construction
    g1= streamGraph.Fgraph(zld, 'source', 'target', 'count', False)
    g2= streamGraph.Fgraph(zld, 'author', 'target', 'count', False)
    #graph pruning 
    pruning_degree=st.slider('Set the degree', 0, 10, 1)
    pruned_vs=g2.vs.select(degree_ge=pruning_degree)
    g2=g2.subgraph(pruned_vs)
    pruning_weighteddegree=st.slider('Set the weighted degree', 0, 120, 2)
    pruned_vs=g2.vs.select(weighteddegree_ge=pruning_weighteddegree)
    g=g2.subgraph(pruned_vs)
    #graph clustering
    algorithmType= st.selectbox('Select clustering algorithm', ['mvp', 'cpm'])
    resolution=st.slider('Select resolution for cpm', 0.0, 1.0, 0.5)
    clust= streamGraph.cluster_Algo(g, 'louvain', algorithmType, resolution)
    'Clusters', clust
    #graph visualization
    if st.checkbox('Visualize network'):
        streamGraph.clusterAlgoDraw(g, clust, 'fr', 2, 8, 'images/agent', 0, author)
        secondD_image = Image.open('images/agent.png')
        st.image(secondD_image,use_column_width=True)





########################################Fgraph functions
# pruning_degree=st.slider('Set the degree', 0, 10, 5)
# proba= streamGraph.Fgraph(secondD, 'source', 'target', 'count')
# pruned_vs=proba.vs.select(degree_ge=pruning_degree)
# proba=proba.subgraph(pruned_vs)
# # '', proba

# streamGraph.FgraphDraw(proba, 'fr', 3, 6, 'proba', 1, author)
# probaImage = Image.open('proba.png')
# st.image(probaImage,use_column_width=True)



# ##################################### Lexical analysis functions
# # Tokens frequency 
# @st.cache()
# def tokens_freq():
#     q='''
#     MATCH(n:Tokens)
#     with n.form as form, n.upostag as upos 
#     return form, upos, count(form) as freq order by freq desc
#     '''
#     df= graph.run(q).to_data_frame()
#     return df
# tokens_freq= tokens_freq()
# 'Tokens processed'


# # Lemma frequency
# @st.cache()
# def lemma_freq():
#     q='''
#     MATCH(n:Tokens)
#     where NOT n.upostag='PUNCT'
#     with n.lemma as lemma, n.upostag as upos 
#     return lemma, upos, count(lemma) as freq order by freq desc
#     '''
#     df= graph.run(q).to_data_frame()
#     return df
# lemma_freq= lemma_freq()
# 'Lemmas processed'

# # Lemma frequency by author
# @st.cache()
# def lemma_freq_author():
#     q='''
#     MATCH(n:Tokens)
#     where not n.upostag = 'PUNCT'
#     with n.author as author, n.lemma as lemma, n.upostag as upos 
#     return author, lemma, upos,  count(lemma) as freq, lemma+"-"+upos as lempos order by freq desc
#     '''
#     df= graph.run(q).to_data_frame()
#     return df
# lemma_freq_author = lemma_freq_author()

# st.title('Lexical analysis by song')

# st.subheader('Token count by text')
# containsInTitle= st.text_input('Search song title')
# containsInText= st.text_input('Search song text')
# # Lemma frequency by text
# def token_freq_text(contains, containsInText):
#     # if containsInTitle=='':
#     #     containsInTitle=''
#     qToken='''
#     MATCH (t:Tokens)<-[rt:HAS_token]-(s:Sentences)<-[rs:HAS_sentence]-(tx:Text)
#     where tx.title contains $containsInTitle 
#     with tx.title as title, tx.author as author, t as t
#     where tx.text contains $containsInText
#     with title+'-'+author as title, t.form as token 
#     return title, token,  count(token) as count order by count desc
#     '''
#     df= graph.run(qToken, containsInTitle=containsInTitle, containsInText=containsInText).to_data_frame()
#     return df
# token_freq_text = token_freq_text(containsInTitle, containsInText)
# data= token_freq_text.groupby(['title'], as_index=False).sum()[0:100].sort_values(by='count', ascending=False)
# fig = go.Figure(data=go.Scatter(x=data['title'],
#                                     y=data['count'],
#                                     mode='markers+text',
#                                     name='Distinct token',
#                                     marker_color=data['count'],
#                                     #text=data['title']
#                                     )) # hover text goes here
# fig.update_layout(title='Token count by text')
# st.plotly_chart(fig)
# if st.checkbox('View token count by text'):
#     'Songs by number of tokens', data





# st.subheader('Lemma count by text')
# # Lemma frequency by text
# def lemma_freq_text():
#     q='''
#     MATCH (t:Tokens)<-[rt:HAS_token]-(s:Sentences)<-[rs:HAS_sentence]-(tx:Text)
#     where not t.upostag = 'PUNCT'
#     with tx.title+'-'+tx.author as title, t.lemma as lemma, t.upostag as upos 
#     return title, lemma, upos,  count(lemma) as count, lemma+"-"+upos as lempos order by count desc
#     '''
#     df= graph.run(q).to_data_frame()
#     return df
# lemma_freq_text = lemma_freq_text()
# data= lemma_freq_text.groupby(['title'], as_index=False).sum().sort_values(by='count', ascending=False)
# fig = go.Figure(data=go.Scatter(x=data['title'],
#                                     y=data['count'],
#                                     mode='markers+lines',
#                                     name='Distinct lemma',
#                                     marker_color=data['count'],
#                                     #text=data['title']
#                                     )) # hover text goes here
# fig.update_layout(title='Lemma count by text')
# st.plotly_chart(fig)
# if st.checkbox('View lemma count by text'):
#     'Songs by number of lemmas', data

###################################### Lema frequency by author_text
@st.cache()
def lemma_freq_author_text(title):
    q='''
    with $title as titles
    unwind titles as title
    MATCH (m:Text{title:title})-[:HAS_sentence]->(:Sentences)-[:HAS_token]->(n:Tokens)
    where not n.upostag = 'PUNCT'
    with n.author as author, n.lemma as lemma, n.upostag as upos 
    return author, lemma, upos,  count(lemma) as freq, lemma+"-"+upos as lempos order by freq desc
    '''
    df= graph.run(q, title=title).to_data_frame()
    return df
# lemma_freq_author_text = lemma_freq_author_text(songSelected)

# POS frequency
@st.cache()
def posList():
    q='''
    MATCH(n:Tokens)
    with n.upostag as upostag
    return distinct(upostag) as upos, count(upostag) as count
    '''
    df = graph.run(q).to_data_frame()
    return df
#%%
import pandas as pd
import corpus_analysis.records as records

pos_df= pd.DataFrame().from_records(records.pos)
zastupnici_df = pd.DataFrame().from_records(records.zastupnici)

#%%

# ########################################### Filter lexemes by title, author
# # select lemma_freq_author by some texts
# if songSelected:  
#     lemma_freq_author = lemma_freq_author_text
# # select lemma_freq_author by some authors
# st.sidebar.subheader('Author selection')
# selectAuthors = st.sidebar.multiselect('Select authors', df[authorColumn])
# if selectAuthors:
#     lemma_freq_author=lemma_freq_author[lemma_freq_author['author'].isin(selectAuthors)]

# ########################################### Lexical analysis
# st.sidebar.subheader('Lexeme selection')
# # select lexemes by POS
# tok_1_pos = st.sidebar.multiselect('Select lexemes by Part of Speech', posList.upos)
# if tok_1_pos:
#     tokens_freq = tokens_freq[tokens_freq['upos'].isin(tok_1_pos)]
#     lemma_freq = lemma_freq[lemma_freq['upos'].isin(tok_1_pos)]
#     lemma_freq_author = lemma_freq_author[lemma_freq_author['upos'].isin(tok_1_pos)]
# # input a lemma
# inputLemma= st.sidebar.text_input('Choose a lemma')
# if inputLemma:
#     lemma_freq_author=lemma_freq_author[lemma_freq_author['lemma']==inputLemma]


# ############################################ Output tokens in texts
# st.subheader('Tokens summary in selected texts')
# 'Total number of tokens', tokens_freq['freq'].sum(), ', distinct number of forms', len(tokens_freq)  
# if st.checkbox('View tokens freq scatter plot'):
#     data= tokens_freq.sort_values(by='freq', ascending=False)[0:100]
#     fig = go.Figure(data=go.Scatter(x=data['form'],
#                                     y=data['freq'],
#                                     mode='markers+lines',
#                                     name='Token forms',
#                                     marker_color=data['freq'],
#                                     text=data['form'])) # hover text goes here
#     fig.update_layout(title='Tokens freq')
#     st.plotly_chart(fig)
# if st.checkbox('View tokens set'):
#     tokens_freq

# ########################################## Lemma in texts
# st.subheader('Lemma (concepts) summary in selected texts')
# 'Total number of lemmas', lemma_freq['freq'].sum(), ', distinct number of lemmas', len(lemma_freq)
# if st.checkbox('View lemma freq scatter plot'):
#     '', lemma_freq
    
#     showLemma= st.slider('Filter lemma by frenquency rank', 0, len(lemma_freq), (0,30))
#     data= lemma_freq.sort_values(by='freq', ascending=False)[showLemma[0]:showLemma[1]]
#     fig = go.Figure(data=go.Scatter(x=data['lemma']+'-'+data['upos'],
#                                     y=data['freq'],
#                                     mode='markers+lines',
#                                     name='Token forms',
#                                     marker_color=data['freq'],
#                                     text=data['lemma'])) # hover text goes here
#     fig.update_layout(title='Lemma freq')
#     st.plotly_chart(fig)
# if st.checkbox('View lemma set'):
#     lemma_freq

# ########################################## POS in texts
# st.subheader('Part of speech summary in selected texts')
# st.write('There are', len(posList), 'part of speech categories.')
# if st.checkbox('View Part of Speech scatter plot'):    
#     data= posList.sort_values(by='count', ascending=False)[0:100]
#     fig = go.Figure(data=go.Scatter(x=data['upos'],
#                                     y=data['count'],
#                                     mode='markers+lines',
#                                     name='POS count',
#                                     marker_color=data['count'],
#                                     text=data['upos'])) # hover text goes here
#     fig.update_layout(title='POS count')
#     st.plotly_chart(fig)
# if st.checkbox('View Part of speech set'):
#      posList 

# ######################################### Lexemes by author
# st.subheader('Lexemes by author in selected texts')
# # def distinct_lemma_freq_author():
# #     q='''
# #     MATCH(n:Tokens)
# #     where not n.upostag = 'PUNCT'
# #     with n.lemma as lemma, n.upostag as upos, n.author as author 
# #     with distinct(lemma+upos) as dist, upos, author
# #     return author, count(dist) as freq order by freq desc
# #     '''
# #     df= graph.run(q).to_data_frame()
# #     return df

# # Scatter plot Lexical statistics by authors
# if st.checkbox('View Lexical statistics by authors scatter plot'):
#     st.write(len(lemma_freq_author['author'].unique()), 'unique authors selected')
#     data= lemma_freq_author.groupby(lemma_freq_author['author'], as_index=False).count().sort_values(by='lemma', ascending=False)
#     fig = go.Figure(data=go.Scatter(x=data['author'],
#                                     y=data['freq'],
#                                     mode='markers+lines',
#                                     name='Distinct lemma',
#                                     marker_color=data['freq'],
#                                     text=data['author'])) # hover text goes here

#     data['sum']= lemma_freq_author.groupby(lemma_freq_author['author'], as_index=False).sum()['freq']
#     fig.add_trace(go.Scatter(x=data['author'], 
#                         y=data['sum'],
#                         mode='markers+lines',
#                         name='Lemma count',
#                         marker_color=data['sum'],
#                         text=data['author']))
#     fig.update_layout(title='Lexical statistics by authors')
#     st.plotly_chart(fig)


# # Scatter plot of lexical diversity by author 
# if st.checkbox('View lexical diversity scatterplot'):
#     aSum=lemma_freq_author.groupby(lemma_freq_author['author'], as_index=False).count()
#     aSum['freq']=lemma_freq_author.groupby(lemma_freq_author['author'], as_index=False).sum()['freq']
#     aSum= aSum.rename(columns={"author": "author", "lemma": "distinct", 'freq': 'sum'})[['author', 'distinct', 'sum']]
#     aSum['lex_diversity']= aSum['distinct']/aSum['sum']
#     data = aSum
#     fig = go.Figure(data=go.Scatter(x=data['sum'],
#                                     y=data['distinct'],
#                                     mode='lines',
#                                     name='lines',
#                                     marker_color=data['distinct'],
#                                     text=data['author'])) # hover text goes here
#     fig.add_trace(go.Scatter(x=data['sum'], y=data['distinct'],
#                         mode='markers',
#                         name='markers', 
#                         text=data['author']))

#     fig.update_layout(title='Lexical diversity by authors',
#                         xaxis_title="Lexemes count",
#                         yaxis_title="Distinct lexemes count")
#     st.plotly_chart(fig)
# if st.checkbox('View lexical diversity dataset'):
#     'Lexical diversity by authors', aSum.sort_values(by='sum')    



################################################## Create the Igraph
st.subheader('Graph representation of the lexemes by author')
# Frequency filter
freqFilter= st.sidebar.slider('Filter by frequency', 0, lemma_freq_author.freq.max(), (0, lemma_freq_author.freq.max()))
lemma_freq_author= lemma_freq_author[(lemma_freq_author['freq'] >=freqFilter[0]) & (lemma_freq_author['freq'] <=freqFilter[1])]

# Calculate Fgraph
# if st.checkbox('View graph'):
Fgraph_lemma_freq_author = Fgraph(lemma_freq_author, 'author', 'lemma', 'freq') 
# Subgraph selection
by_betweeneess= st.slider('Select by betweenness', 0.0, max(Fgraph_lemma_freq_author.betweenness()), (0.0, max(Fgraph_lemma_freq_author.betweenness())))
Fgraph_lemma_freq_author=Fgraph_lemma_freq_author.subgraph(Fgraph_lemma_freq_author.vs.select(betweenness_ge = by_betweeneess[0]), implementation="auto")
by_pagerank= st.slider('Select by pagerank', 0.0, max(Fgraph_lemma_freq_author.pagerank()), (0.0, max(Fgraph_lemma_freq_author.pagerank())))
Fgraph_lemma_freq_author=Fgraph_lemma_freq_author.subgraph(Fgraph_lemma_freq_author.vs.select(betweenness_ge = by_pagerank[0]), implementation="auto")


# Filter by graph measure degree
# Fgraph_lemma_freq_author_selection = Fgraph_lemma_freq_author.vs.select(name_ge = 20 )
# Filter by graph measure betweeneess

# # Cluster Fgraph

#################################################### Visualise the Igraph
st.sidebar.subheader('Graph representation of the lexemes by author')
visualisation = st.sidebar.selectbox('Select visualisation type', ('Static without clusters', 'Static with clusters',  'Interactive without clusters', 'Interactive with clusters' ))
layout = st.sidebar.selectbox('Select graph layout', ('lgl', 'drl', 'fr', 'kk', 'tree', 'rt_circular', 'circle', 'random' ))

vertexSize=st.sidebar.slider('Resize nodes', 0.1, 20.0, 10.0)
vertexLabelSize=st.sidebar.slider('Resize node labels', 0.1, 20.0, 10.0)
edgeLabelSize=st.sidebar.slider('Resize edge labels', 0.1, 20.0, 10.0)

# # Fgraph image with caption
# if visualisation == 'Static without clusters':
#     FgraphDraw(Fgraph_lemma_freq_author, layout, vertexSize, vertexLabelSize, 'Fgraph_lemma_freq_author', edgeLabelSize, lemma_freq_author['author'])
#     Fgraph_lemma_freq_author_image = Image.open('Fgraph_lemma_freq_author.png')
#     st.image(Fgraph_lemma_freq_author_image,use_column_width=True)


# if visualisation == 'Interactive without clusters':
#     plotly_Fgraph = FgraphDraW_plotly(Fgraph_lemma_freq_author, layout, vertexSize, vertexLabelSize, 'Fgraph_plotly', edgeLabelSize, songSelected)
#     st.plotly_chart(plotly_Fgraph)

#######################################
# Lexical summary by authors lemma_freq_author dataset
if st.checkbox('View lexical summary by authors dataset'):
    lemma_freq_author


############################################## Concordancer
# Find sentence by lemma, question, author
# Return sentence
@st.cache(allow_output_mutation=True)
def sentence_from_lemma(title, lemmaSelected):
    q='''
    //UNWIND $title as title
    UNWIND $lemmaSelected as lemmaSelected
    with lemmaSelected
    MATCH (sent:Sentences)-[:HAS_token]->(tok:Tokens{lemma:lemmaSelected})
    with sent.text as sentence, sent.author as author, sent.title as title, tok.lemma as lemma
    RETURN sentence, author, title, lemma
    '''
    df=graph.run(q, lemmaSelected=lemmaSelected, title=title).to_data_frame()
    return df

#############################################
# Select lema for concordance
st.title('Concordance')
concordance= st.text_input('Search for lemma')
if concordance or inputLemma:
    'Concordance table for lemma', concordance
    try:
        concordanceResult= sentence_from_lemma(songSelected, concordance)[['title', 'author', 'sentence']]
        if songSelected:
            if st.checkbox('Show results within selected questions'):
                concordanceResult=concordanceResult[concordanceResult['title'].isin(songSelected)][['author', 'sentence']]
        st.table(concordanceResult)
    except:
        pass




################################################# Clustering
# Clustering Algorithms
st.title('Clusters')
st.sidebar.subheader('Clustering parameters')
# algorithm selection 
algorithm = st.sidebar.selectbox('Cluster algorithm type', ('leiden', 'louvain'))
partitionType= st.sidebar.selectbox('Partition type', ('mvp', 'cpm'))


clusterAlgo = cluster_Algo(Fgraph_lemma_freq_author, algorithm, partitionType)
# if st.checkbox('View lexical clusters'): 
clusterAlgo

########################################################Cluster Draw
# clusterAlgoDraw(Fgraph_lemma_freq_author, clusterAlgo, layout)
clusterAlgoDraw(Fgraph_lemma_freq_author, clusterAlgo, layout, vertexSize, vertexLabelSize, "FoFClusterAlgo", edgeLabelSize, lemma_freq_author['author'])
# Fgraph image with caption
clusterAlgoDraw_image = Image.open('FoFClusterAlgo.png')
st.image(clusterAlgoDraw_image,use_column_width=True)

#######################################Lexical relations filtered by title,author,POS,lemma,
st.title('Lexical relations')
st.sidebar.title('Lexical relations')
st.subheader('Type of grammatical relations')
@st.cache()
def two_tokens(lemma_freq_author):
    lemmasList= lemma_freq_author[['lemma', 'upos']].values.tolist()
    q="""
    unwind $lemmasList as lemmaItem
    MATCH p=(t1:Tokens{lemma:lemmaItem[0], upostag:lemmaItem[1]})-[r1:HAS_deprel]->(t2:Tokens)
    return t1.lemma, t1.upostag, t2.lemma, t2.upostag, 
        r1.deprel as r1, count(r1) as freq order by freq, r1 desc
    """
    df= graph.run(q, lemmasList=lemmasList).to_data_frame()    
    return (df)
two_tokens= two_tokens(lemma_freq_author, ).sort_values(by='freq', ascending=False)

#                         # napraviti tokens by text.title & text.author
#                         # @st.cache()
#                         # def two_tokens_by_title(lemma_freq_author):
#                         #     lemmasList= lemma_freq_author[['lemma', 'upos']].values.tolist()
#                         #     q="""
#                         #     unwind $lemmasList as lemmaItem
#                         #     MATCH p=(t1:Tokens{lemma:lemmaItem[0], upostag:lemmaItem[1]})-[r1:HAS_deprel]->(t2:Tokens)
#                         #     return t1.lemma, t1.upostag, t2.lemma, t2.upostag, 
#                         #         r1.deprel as r1, count(r1) as freq order by freq, r1 desc
#                         #     """
#                         #     df= graph.run(q, lemmasList=lemmasList).to_data_frame()    
#                         #     return (df)
#                         # two_tokens= two_tokens(lemma_freq_author, ).sort_values(by='freq', ascending=False)




# Extract gramRels in t1-r1-t2 set
gramRels = two_tokens['r1'].unique()
st.write('Based on the previous filtering, there are', len(gramRels), 'type of grammatical relations.')
if st.checkbox('View grammatical relations'):
     gramRels 

# Filter two tokens by relations r1
tok_2_rel_1 = st.sidebar.multiselect('Select relations between tokens t1-[r1]-t2', gramRels)
if tok_2_rel_1:
    two_tokens= two_tokens[two_tokens.r1.isin(tok_2_rel_1)]
freqFilter = st.sidebar.slider('Filter by r1 frequency', 1, two_tokens['freq'].max(), (1, two_tokens['freq'].max()))
'2-grams in frequency range:', freqFilter
two_tokens =two_tokens[(two_tokens['freq'] >=freqFilter[0]) & (two_tokens['freq'] <=freqFilter[1])]
st.write(two_tokens)


# two_tokens Fgraph representation
FgraphTwoTokens = Fgraph(two_tokens, 't1.lemma', 't2.lemma', 'freq')
clusterAlgoTwoTokens = cluster_Algo(FgraphTwoTokens, algorithm, partitionType)
clusterAlgoDraw(FgraphTwoTokens,clusterAlgoTwoTokens, layout, vertexSize, vertexLabelSize, 'FgraphTwoTokens', edgeLabelSize, lemma_freq_author['author'])
# represent the Fgraph image with caption
FgraphTwoTokens_image = Image.open('FgraphTwoTokens.png')
st.image(FgraphTwoTokens_image,use_column_width=True)


# # # st.image(Fgraph_image, caption='2-grams '
# # #     +' with vertices: '+str(Fgraph.vcount())
# # #     +', edges: '+str(Fgraph.ecount())
# # #     +', graph density: '+str(Fgraph.density(loops=False))
# # #     +', diameter: '+str(Fgraph.diameter(directed=False, unconn=True, weights=None))
# # #     ,use_column_width=True)

# # # filter by authorSelected
# # def two_tokens_by_author():
# #     q='''
# #     MATCH p=(t1:Tokens)-[r1:HAS_deprel]->(t2:Tokens)
# #     WHERE NOT r1.deprel='punct'
# #     return t1.author as author, t1.lemma, t1.upostag, 
# #         t2.lemma, t2.upostag, r1.deprel as r1, count(r1) as freq order by freq desc
# #     ''' 
# #     df= graph.run(q).to_data_frame()
# #     return (df)
# # n_2_authorCheck= st.checkbox('View 2-grams by author:')
# # if n_2_authorCheck:
# #     n_2_author = two_tokens_by_author()
# #     n_2_author[n_2_author['author']== authorSelected]
# #     st.write('2-grams by author gramRels summary', n_2_author.groupby(['r1','author']).count().sort_values(by='freq', ascending=False)['freq'])

# # #find examples
# #     # define lemma1 
# #     # select lemma from dataframe

# # st.subheader('3-gram constructions')
# # st.sidebar.subheader('3-gram constructions')
# # #% three tokens connected by specific relations r1, r2
# # q3tok='''
# # MATCH p=(t1:Tokens)-[r1:HAS_deprel]->(t2:Tokens)-[r2:HAS_deprel]->(t3:Tokens)
# # WITH t1,r1,t2,r2,t3, (t1.form+" "+t2.form+" "+t3.form) as fraza
# # //WHERE r1.deprel=$tok_3_rel_1 AND r2.deprel=$tok_3_rel_2
# # return fraza, t1.lemma, t1.upostag, r1.deprel as deprel1, count(r1) as freq1,
# #         t2.lemma, t2.upostag, r2.deprel as deprel2, count(r2) as freq2, 
# #         t3.lemma, t3.upostag order by freq1, deprel1 desc
# # '''
# # three_tokens= graph.run(q3tok).to_data_frame()
# # st.write(three_tokens)
# # tok_3_rel_1 = st.sidebar.selectbox('Filter relation between token 1 and 2', gramRels)
# # tok_3_rel_2 = st.sidebar.selectbox('Filter relation between token 2 and 3', gramRels)



# # two tokens with specific upostags connected by specific deprel 
# # upostag1='ADJ'
# # upostag2='ADJ'
# # deprel='conj'
# # q='''
# # MATCH p=(n:Tokens)-[r:HAS_deprel]->(m:Tokens)
# # WHERE n.upostag=$upostag1 AND r.deprel=$deprel AND  m.upostag=$upostag2  
# # return n.lemma, m.lemma, count(r) as freq order by freq desc
# # '''
# # graph.run(q, upostag1=upostag1,upostag2=upostag2, deprel=deprel).to_data_frame()

# # #%% for a lemma get all the relations
# # def lemaRel(lemma, upostag):
# #     q='''
# #     MATCH p=(n:Tokens)-[r:HAS_deprel]->(m:Tokens)
# #     WHERE r.deprel='conj'// AND n.upostag=$upostag  // AND n.lemma=$lemma 
# #     return n.author as author, n.lemma as source, n.upostag as posS, m.lemma as friend, m.upostag as posF, r.deprel as deprel, count(r) as weight order by weight desc
# #     '''
# #     return (graph.run(q, upostag=upostag, lemma=lemma).to_data_frame())

# # lemaRel('tradicijski', 'ADJ')

# # #%%
# # import igraph as ig
# # def Fgraph(lemma, upostag):
# #     #create df variable
# #     df_any=lemaRel(lemma, upostag)
# #     df_any['friend']=df_any['friend']#+'-'+df_any['posF']
# #     df_any['source']=df_any['source']#+'-'+df_any['posS']
# #     df=df_any[['source', 'friend', 'weight']]
# #     #create tuples from df.values
# #     tuples = [tuple(x) for x in df.values]
# #     #create igraph object from tuples
# #     G=ig.Graph.TupleList(tuples, directed = True, edge_attrs=['weight'], vertex_name_attr='name', weights=False)
# #     #create vertex labels from name attr
# #     G.vs["label"]=G.vs["name"]
# #     G.vs["degree"]=G.vs.degree()
# #     G.vs["pagerank"]=G.vs.pagerank(directed=True, weights='weight')
# # #    print(G.vs["pagerank"])
# #     G.vs["personalized_pagerank"]=G.vs.personalized_pagerank(directed=False, weights='weight')
# #     #print(G)
# #     return(G)

# # print(Fgraph('sve', 'NOUN'))


# # #%% Draw Fgraph


# # def FgraphDraw(lemma, upostag, Glayout):
# #     G=Fgraph(lemma, upostag) 
# #     #create vertex labels from name attr
# #     G.vs["label"]=G.vs["name"]
# #     G.vs["degree"]=G.vs.degree()
# # #    G.vs["pagerank"]=G.vs.pagerank(directed=True, weights='weight')
# # #    print(G.vs["pagerank"])
# # #    G.vs["personalized_pagerank"]=G.vs.personalized_pagerank(directed=False, weights='weight')
# #     visual_style = {}
# #     visual_style["vertex_size"] = 5#[i * 2 for i in G.vs["degree"]]
# #     visual_style["vertex_label_color"] = "black"
# #     visual_style["vertex_label_size"] = 15 #[math.log2(i)* 5 for i in G.vs["degree"]] #maybe it could be G.vs["degree"]
# #     visual_style["vertex_color"] = "rgba(255,0,0,0.2)"
# #     visual_style["edge_color"] = "rgba(255,0,0,0.2)"
# #     visual_style["vertex_label_dist"] = 1
# # #    visual_style["edge_width"] = G.es["weight"]
# # #    visual_style["edge_label"] = G.es["weight"]
# #     visual_style['hovermode'] = 'closest'
# #     visual_style["layout"] = Glayout
# #     visual_style["bbox"] = (1500, 1500)
# #     visual_style["margin"] = 250
    
# #     lemmaW= (bytes(lemma, 'utf-8')).decode('mbcs', 'ignore')
# # #    print(G)
# #     ig.plot(G, "Fgraph_"+lemmaW+upostag+".png", **visual_style)
# #     return(G)

# # #limit=15
# # #scoreMin=0
# # #freqMin=0
# # FgraphDraw('conj', 'sve', "fr")



# # #%% Dataframe for friend-of-friend network
# # def FoFNetwork(lemma, pos, corpus, gramRel, pos2, limit, measure):
# #     'for a source lempos extract friend in gramRel, and their friends'
    
# #     #extract F network for a source lempos
# #     df=friendNetwork(lemma, pos, corpus, gramRel, pos2, limit, measure)
    
# #     #extract FoF network 
# #     for index, row in df.iterrows():
# #         try:
# #             df2=friendNetwork(row['friend'][0:-2], row['friend'][-2:], corpus, gramRel, pos, limit, measure)
# #             #append the dataframe of df2 to df
# #             df2.rename(columns={'friend': 'source', 'source':'friend'}, inplace=True)
# #             df=df.append(df2, sort=True)
# #             df=df.drop_duplicates()
            
# #         except:
# #             pass
# #     return(df[['source', 'friend', measure]])


# # FoFNetwork('glazba', '-n', corpus, gramRel, pos2, limit, measure)

        
# # #%%Queries
# # howManySent="""
# # match (n:Sentences) 
# # with count(n) as broj 
# # return broj 
# # """
# # print(graph.run(howManySent).to_table())
# # #%%
# # q='''
# # //how many lemmas 
# # match (n:Tokens) 
# # with n.lemma as lema, count(n.lemma) as broj 
# # return lema, broj order by broj asc
# # '''
# # print (graph.run(q).to_table())
# # #%%
# # q='''
# # //how many lemmas 
# # match (n:Tokens) 
# # where n.upostag='NOUN'
# # with n.lemma as lema, count(n.lemma) as broj 
# # return lema, broj order by broj desc
# # '''
# # print (graph.run(q).to_table())
# # #%%
# # q2='''
# # //how many lemmas from authors
# # match (t:Text)--(s:Sentences)--(n:Tokens) 
# # with t.author as author, n.lemma as lema, count(n.lemma) as broj 
# # return author, lema, broj order by broj asc
# # '''
# # print (graph.run(q2).to_table())
# # #%%
# # q2='''
# # //how many NOUN lemmas from authors
# # match (t:Text)--(s:Sentences)--(n:Tokens) 
# # where n.upostag='VERB'
# # with t.author as author, n.lemma as lema, count(n.lemma) as broj 
# # return author, lema, broj order by broj desc
# # '''
# # print (graph.run(q2).to_table())