#%%
import numpy as np
import pandas as pd
import nltk
# nltk.download('omw')
from nltk.corpus import wordnet as wn
from itertools import islice
from py2neo import Graph
try:
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "kultura"))   
    print ("Connected to dedicated Neo4j graph database")
except:
    print ("Could not connect to dedicated Neo4j graph database")


#%%
def synsetlemma2nodes():
    'store all synsets in nodes'
    for synset in islice(wn.all_synsets(), None):
        name= (str(synset)[8:-2])
        word = (str(synset)[8:-7])
        pos= (str(synset)[-6:-5])
        sense= (str(synset)[-4:-2])
        definition=synset.definition()
        q='''
        merge (n:Synset{name:$name})
        set n.language ='en'
        set n.word =$word
        set n.pos= $pos
        set n.sense= $sense
        set n.definition= $definition
        '''
        # print(name, word, pos, sense, definition)
        graph.run(q, name=name, word=word, pos=pos, sense=sense, definition=definition)
    

        'create :Lemma english and connect to :Synset'        
        for lemma in synset.lemma_names():
            q2='''      
            merge (l:Lemma{lemma:$lemma, pos:$pos, language:'en'})                        
            '''
            graph.run(q2, lemma=lemma, name=name, pos=pos)
            # print(lemma)
            q22='''      
            match (l:Lemma{lemma:$lemma, pos:$pos, language:'en'})                        
            match (s:Synset{name:$name})
            merge (l)<-[:HAS_lemma]-(s)
            '''
            graph.run(q22, lemma=lemma, name=name, pos=pos)
            # print(lemma)
        

        for lemma in synset.lemmas('hrv'):
            name= (str(lemma)[7:-2])

            syn= ".".join(name.split(".")[0:3])
            lemma_en= name.split(".")[0]
            lemma= name.split(".")[3]
            pos= name.split(".")[1]
            language= 'hrv'
            print(syn)

            q3='''
            merge (l:Lemma{lemma:$lemma, pos:$pos, language:$language})
            '''
            graph.run(q3,  lemma= lemma, pos=pos, language=language)

            q32='''
            match (l:Lemma{lemma:$lemma, pos:$pos, language:$language})
            match (s:Synset{name:$syn})
            merge (l)<-[:HAS_lemma{language:$language}]-(s)
            //merge (l)<-[:Translation]-(:Lemma{lemma:$lemma_en, pos:$pos, language:'en'})                        
            '''
            graph.run(q32, syn=syn, lemma= lemma, pos=pos, lemma_en=lemma_en, language=language)
            q33='''
            match (l:Lemma{lemma:$lemma, pos:$pos, language:$language})
            match (l2:Lemma{lemma:$lemma_en, pos:$pos, language:'en'})
            merge (l)<-[:Translation]-(l2)                        
            '''
            graph.run(q33, lemma= lemma, pos=pos, lemma_en=lemma_en, language=language)
    
    print('Finished')
# synsetlemma2nodes()


#%% store hypernyms
def syn2syn_hypernym():
    for synset in islice(wn.all_synsets(), None):
        # synset = wn.synset('dog.n.01')
        for hypernym in synset.hypernyms():
            synset_name=(str(synset)[8:-2])
            hypernym_name=(str(hypernym)[8:-2])
            print(synset_name, hypernym_name)
            q_hypr='''
            match (s:Synset{name:$synset_name}), (hypr:Synset{name:$hypernym_name})
            merge(s)-[:HAS_hypernym]->(hypr)
            '''
            graph.run(q_hypr, synset_name= synset_name, hypernym_name=hypernym_name)
    print("Finished")
syn2syn_hypernym()
#%% store hyponyms
def syn2syn_hyponym():
    for synset in islice(wn.all_synsets(), None):
        for hyponym in synset.hyponyms():
            synset_name=(str(synset)[8:-2])
            hyponym_name=(str(hyponym)[8:-2])
            print(synset_name, hyponym_name)
            q_hypo='''
            match (s:Synset{name:$synset_name}), (hypo:Synset{name:$hyponym_name})
            merge(s)-[:HAS_hyponym]->(hypo)
            '''
            graph.run(q_hypo, synset_name= synset_name, hyponym_name=hyponym_name)
    print("Finished")
syn2syn_hyponym()
#%% store member_holonyms()
def syn2syn_member_holonym():
    for synset in islice(wn.all_synsets(), None):
        for member_holonym in synset.member_holonyms():
            synset_name=(str(synset)[8:-2])
            member_holonym_name=(str(member_holonym)[8:-2])
            print(synset_name, member_holonym_name)
            q_hypo='''
            match (s:Synset{name:$synset_name}), (member_holonym:Synset{name:$member_holonym_name})
            merge(s)-[:HAS_member_holonym]->(member_holonym)
            '''
            graph.run(q_hypo, synset_name= synset_name, member_holonym_name=member_holonym_name)
    print("Finished")
syn2syn_member_holonym()
#%% store root_hypernyms()
def syn2syn_root_hypernym():
    for synset in islice(wn.all_synsets(), None):
        for root_hypernym in synset.root_hypernyms():
            synset_name=(str(synset)[8:-2])
            root_hypernym_name=(str(root_hypernym)[8:-2])
            print(synset_name, root_hypernym_name)
            q_hypo='''
            match (s:Synset{name:$synset_name}), (root_hypernym:Synset{name:$root_hypernym_name})
            merge(s)-[:HAS_root_hypernym]->(root_hypernym)
            '''
            graph.run(q_hypo, synset_name= synset_name, root_hypernym_name=root_hypernym_name)
    print("Finished")
syn2syn_root_hypernym()
#%% store antonyms 
def lema2lema_antonym():
    'store english antonyms'
    language='en'
    for l in islice(wn.all_synsets(), None):
        for lemma in l.lemmas():
            lemma_name=(str(lemma)[7:-2]).split('.')[0]
            pos=(str(lemma)[7:-2]).split('.')[1]
            antonyms= lemma.antonyms()
            print(lemma, lemma_name, pos, antonyms)
            for antonym in antonyms:
                antonym_name=(str(antonym)[7:-2]).split('.')[0]
                print(lemma_name, pos, antonym_name)
                q='''
                match (l:Lemma{lemma:$lemma_name, pos:$pos, language:$language}), (a:Lemma{lemma:$antonym_name, pos:$pos, language:$language})
                merge (l)-[:HAS_antonym]->(a)
                '''
                graph.run(q,lemma_name=lemma_name, antonym_name= antonym_name, pos=pos, language=language)
    print("Finished")

lema2lema_antonym()

#%% antonyms for other languages from english
def lema2lema_antonym_lang(language):
    q='''
    MATCH p=(hn:Lemma{language:$language})-[:Translation]-(n:Lemma{language:'en'})-[:HAS_antonym]->(a)-[:Translation]-(ha) 
    WITH hn, ha
    MERGE (hn)-[:HAS_antonym{source:'derived from eng'}]->(ha)
    '''
    graph.run(q, language=language)
lema2lema_antonym_lang('hrv')

#%% derivationally_related_forms
def lema2lema_derivationally_related_forms():
    'store english derivationally_related_forms'
    language='en'
    for l in islice(wn.all_synsets(), None):
        for lemma in l.lemmas():
            lemma_name=(str(lemma)[7:-2]).split('.')[0]
            pos=(str(lemma)[7:-2]).split('.')[1]
            derivationally_related_forms = lemma.derivationally_related_forms()
            # print(lemma, lemma_name, pos, derivationally_related_forms)
            for derivationally_related_form in derivationally_related_forms:
                derivationally_related_form_name=(str(derivationally_related_form)[7:-2]).split('.')[3]
                derivationally_related_form_pos=(str(derivationally_related_form)[7:-2]).split('.')[1]
                print(lemma_name, pos, derivationally_related_form_name, derivationally_related_form_pos)
                q='''
                match (l:Lemma{lemma:$lemma_name, pos:$pos, language:$language}), (a:Lemma{lemma:$derivationally_related_form_name, pos:$derivationally_related_form_pos, language:$language})
                merge (l)-[:HAS_derivationally_related_form]->(a)
                '''
                graph.run(q,lemma_name=lemma_name, pos=pos, derivationally_related_form_pos= derivationally_related_form_pos,derivationally_related_form_name= derivationally_related_form_name, language=language)
    print("Finished")

lema2lema_derivationally_related_forms()

#%% pertainyms
def lema2lema_pertainyms():
    'store english pertainyms'
    language='en'
    for l in islice(wn.all_synsets(), None):

        for lemma in l.lemmas():
            lemma_name=(str(lemma)[7:-2]).split('.')[0]
            pos=(str(lemma)[7:-2]).split('.')[1]
            pertainyms = lemma.pertainyms()
            # print(lemma, lemma_name, pos, pertainyms)
            for pertainym in pertainyms:
                pertainym_name=(str(pertainym)[7:-2]).split('.')[3]
                pertainym_pos=(str(pertainym)[7:-2]).split('.')[1]
                print(lemma_name, pos, pertainym_name, pertainym_pos)
                q='''
                match (l:Lemma{lemma:$lemma_name, pos:$pos, language:$language}), (a:Lemma{lemma:$pertainym_name, pos:$pertainym_pos, language:$language})
                merge (l)-[:HAS_pertainym]->(a)
                '''
                graph.run(q,lemma_name=lemma_name, pos=pos, pertainym_pos= pertainym_pos,pertainym_name= pertainym_name, language=language)
    print("Finished")

lema2lema_pertainyms()

#%% find lowest common hypernyms
print(wn.synset('group.n.01').lowest_common_hypernyms(wn.synset('set.n.02')))


#%%
q='''
match (l:Lemma)
return l.name as lemma
limit 10
'''
lemmmas= graph.run(q).to_series
for l in lemmmas:
    a= l.antonyms()
    print(l, a)



#%% example of analysis in wn
wn.synset('dog.n.01').lowest_common_hypernyms(wn.synset('cat.n.01'))
# can we do that more efficiently with graphs?


#%% jezici
sorted(wn.langs())

#%% ? od niza riječi dobiti kategoriju
lista= ['kuća', 'dom', 'soba']
# nađi synsetove
a= wn.synsets('kuća', pos=wn.NOUN, lang='hrv')
b= wn.synsets('soba', pos=wn.NOUN, lang='hrv')
a.lowest_common_hypernyms(b)

#%%

for lemma in wn.synset('dog.n.01').lemmas('hrv'):
    name= (str(lemma)[7:-2])
    lemma= name.split(".")[3]
    print(lemma)

#%% get synset from word

wn.synsets('dog', pos=wn.VERB)

#%% provjera postoji li riječ u nekom wordnetu
if 'no' in wn.all_lemma_names(pos='a', lang='hrv'):
    print('1')
else:
    print('0')






# %%
