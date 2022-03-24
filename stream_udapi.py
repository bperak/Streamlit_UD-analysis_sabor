import os
import math
import time
import streamlit as st
import ufal.udpipe
import uuid 

# Connecting to the Neo4j Database
from py2neo import Graph
try:
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "kultura"))   
    print ("Connected to dedicated Neo4j graph database")

except:
    print ("Could not connect to dedicated Neo4j graph database")


# with authorID and authorFeatures list create node Author
def merge_authors(authors):
    q='''
    unwind $authors as author 
    MERGE (a: Author {author: author})
    //SET a = $authorFeatures
    '''
    graph.run(q, authors=authors)



# UDapi Classes
class Model:
    def __init__(self, path):
        """Load given model."""
        self.model = ufal.udpipe.Model.load(path)
        if not self.model:
            raise Exception("Cannot load UDPipe model from file '%s'" % path)

    def tokenize(self, text):
        """Tokenize the text and return list of ufal.udpipe.Sentence-s."""
        tokenizer = self.model.newTokenizer(self.model.DEFAULT)
        if not tokenizer:
            raise Exception("The model does not have a tokenizer")
        return self._read(text, tokenizer)

    def read(self, text, in_format):
        """Load text in the given format (conllu|horizontal|vertical) and return list of ufal.udpipe.Sentence-s."""
        input_format = ufal.udpipe.InputFormat.newInputFormat(in_format)
        if not input_format:
            raise Exception("Cannot create input format '%s'" % in_format)
        return self._read(text, input_format)

    def _read(self, text, input_format):
        input_format.setText(text)
        error = ufal.udpipe.ProcessingError()
        sentences = []

        sentence = ufal.udpipe.Sentence()
        while input_format.nextSentence(sentence, error):
            sentences.append(sentence)
            sentence = ufal.udpipe.Sentence()
        if error.occurred():
            raise Exception(error.message)

        return sentences

    def tag(self, sentence):
        """Tag the given ufal.udpipe.Sentence (inplace)."""
        self.model.tag(sentence, self.model.DEFAULT)

    def parse(self, sentence):
        """Parse the given ufal.udpipe.Sentence (inplace)."""
        self.model.parse(sentence, self.model.DEFAULT)

    def write(self, sentences, out_format):
        """Write given ufal.udpipe.Sentence-s in the required format (conllu|horizontal|vertical)."""

        output_format = ufal.udpipe.OutputFormat.newOutputFormat(out_format)
        output = ''
        for sentence in sentences:
            output += output_format.writeSentence(sentence)
        output += output_format.finishDocument()

        return output




# take author, title/question, text and parse into conllu 
def parse_OneText(author, title, text, language, model):    
    #parse text
    sentences = model.tokenize(text)
    for s in sentences:
        model.tag(s)
        model.parse(s)
    #conllu output
    conllu = model.write(sentences, "conllu")
    #uuid3() generate MD5 hash based on namespace
    id= uuid.uuid3(uuid.NAMESPACE_URL, text)
    return(author, title, text, conllu, id, language) 


# Sends texts to Neo4j using the conllu
#  :Text :HAS :Sentences :HAS :Tokens schema
# http://lindat.mff.cuni.cz/services/udpipe/api

# createIndexes in Neo4j
@st.cache()
def createIndexes():
    #list of indexes
    indexList=["create index on :Text(author)",
          "create index on :Text(title)",
          "create CONSTRAINT on (i:Text) ASSERT i.text_unique IS UNIQUE",
          "create index on :Sentences(sent_id)",
          "create CONSTRAINT on (s:Sentences) ASSERT s.sent_unique IS UNIQUE",
          "create INDEX on :Sentences(text_unique)",
          "create index on :Tokens(id)",
          "create CONSTRAINT on (t:Tokens) ASSERT t.token_unique IS UNIQUE",
          "create INDEX on :Tokens(sent_unique)",
          "create index on :Tokens(head)",
          "create index on :Tokens(form)",
          "create index on :Tokens(lemma)",
          "create index on :Tokens(upostag)",
          "create index on :Tokens(feats)",
          "create index on :Tokens(deps)",
          "create index on :Tokens(language)" 
        ]
    #check if the Indexes already exist
    queryCheckIndex="""
    CALL db.indexes
    """
    n= graph.run(queryCheckIndex).to_data_frame()
    
    #if Index is empty create Indexes
    if n.empty == True:
        try:    
            for item in indexList:
                createIndex= f'{item}'
                graph.run(createIndex)
                print(f'{item}')
        except:
            pass
    # n[n['description'].str.contains(":Tokens")]
        
    
 
   

# Neo4j : merge text, sentences, tokens, lemma
def textSentTokLemma_2neo(author, title, text, language, model):
    counter=0
    # =============================================================================
    # conllu files to Text, Sentence text, sent_id, Token u Neo4j
    # =============================================================================
    beginTime=time.time() 
    
    # parse the text using the parse_OneText() and return conllu, text_unique values   
    parsed = parse_OneText(author, title, text, language, model)
    conllu = parsed[3]
    text_unique = str(parsed[4])
    
    queryTextId="""
    MERGE (t:Text{text_unique:$text_unique})
    SET t.text=$text, 
        t.author=$author,
        t.title=$title
    """
    graph.run(queryTextId, author=author, title=title, text_unique=text_unique, text=text)

    queryTextToAuthor="""
    MATCH (t:Text{text_unique:$text_unique}), (a:Author{author:$author})
    MERGE (a)-[:Produced]->(t)
    """
    graph.run(queryTextToAuthor, author=author, text_unique=text_unique)
      
    # Sentence to data
    for item in conllu.split("\n"):
        #Sentence sent_id
        if "# sent_id" in item:
            sent_id=item.replace("# sent_id =","").strip()
            sent_unique=text_unique+"_"+sent_id    
        #Sentence text
        if "# text" in item:
            itemSentText = item.replace("# text =","").strip()
            #MERGE
            querySentId="""
            with split($sent_id, "\n") as sent_ids
            unwind sent_ids as sent_id
            with sent_id, split($itemSentText, "\n") as itemSentText
            MERGE (s:Sentences{sent_unique:$sent_unique})
            SET s.text=itemSentText, 
                s.sent_id=toInteger(sent_id),
                s.title=$title, 
                s.text_unique=$text_unique,
                s.author=$author
            """
            graph.run(querySentId, author=author, title=title, text_unique=text_unique, sent_unique=sent_unique, itemSentText = itemSentText, sent_id=sent_id)
            
            queryTextHasSent="""
            MATCH (t:Text{text_unique:$text_unique})
            MATCH (s:Sentences{text_unique:$text_unique})
            MERGE (t)-[:HAS_sentence]->(s)
            """       
            graph.run(queryTextHasSent, text_unique=text_unique)
    
            #Store :NEXT_sentence relations
            queryNextSentence="""
            match (s:Sentences{text_unique:$text_unique})
            set s.sent_id=toInteger(s.sent_id)
            with s 
            ORDER BY s.sent_id
            with collect(s) as sentences
            unwind range(0, size(sentences)-2) as idx
            with sentences[idx] as s1, sentences[idx+1] as s2
            merge (s1)-[:NEXT_sentence]->(s2)
            """
            graph.run(queryNextSentence, author=author, title=title, text_unique=text_unique)     
        
    counter=counter+1
    timePassed=time.time()
    sentenceTime= ("Sentences: "+text_unique, counter, (timePassed-beginTime))
    
    #TOKENI
    counter=0
    tokenBeginTime=time.time()
    
    ####### Sentence to Tokens
    for item in conllu.split("\n"):
        #Sentence sent_id
        if "# sent_id" in item:
            sent_id=item.replace("# sent_id =","").strip()
            sent_unique=text_unique+"_"+sent_id
        #Token data
        if "\t"in item:
            tsvTokensRow = item.strip()
            TokenParse="""
            with $tsvTokensRow as tsvTokensRow
            with split(tsvTokensRow, "\t") as tokenData
            MERGE(t:Tokens{token_unique:$sent_unique+'_'+tokenData[0]})
            ON CREATE SET t.id=toInteger(tokenData[0]), 
                t.form=tokenData[1], 
                t.lemma=tokenData[2], 
                t.upostag=tokenData[3], 
                t.xpostag=tokenData[4], 
                t.feats=tokenData[5], 
                t.head=toInteger(tokenData[6]), 
                t.deprel=tokenData[7],
                t.deps=tokenData[8], 
                t.misc=tokenData[9],
                t.language=$language,
                t.sent_unique=$sent_unique,
                t.text_unique=$text_unique,
                t.author=$author
            """
            graph.run(TokenParse, tsvTokensRow=tsvTokensRow, sent_unique=sent_unique, language=language, text_unique=text_unique, title=title, author=author)
            queryTokToSent="""
            MATCH (tok:Tokens{sent_unique:$sent_unique})
            with collect(tok) as tokens
            unwind (tokens) as token
            MATCH (sent:Sentences{sent_unique:$sent_unique})
            MERGE (sent)-[:HAS_token]->(token)
            """
            graph.run(queryTokToSent, sent_unique=sent_unique)
            
            #Store  Dependencies
            queryDeps="""
            //storing dependencies relation
            MATCH (d:Tokens{sent_unique:$sent_unique})
            with d
            MATCH (h:Tokens{sent_unique:d.sent_unique, id:d.head})
            WITH d, h
            MERGE (d)-[:HAS_deprel{deprel:d.deprel}]->(h)
            """
            graph.run(queryDeps, sent_unique=sent_unique, sent_id=sent_id)
            
            counter=counter+1
    timePassed=time.time()
    tokenTime= ("Tokens file: "+author, text_unique, counter, (timePassed-tokenBeginTime))
    
    #LEMME
    lemmaBeginTime=time.time()
    queryCreateLemma="""
        MATCH (token:Tokens{text_unique:{text_unique}})
        with collect(token) as tokens
        unwind (tokens) as token
        MERGE (lemma:Lemmas{lemma:token.lemma, upostag:token.upostag})
        MERGE (token)-[:HAS_lemma]->(lemma)
        """
    graph.run(queryCreateLemma, text_unique=text_unique)
    timePassed=time.time()
    lemmaTime= ("Lemmas file: "+author, text_unique, counter, (timePassed-lemmaBeginTime))   
    return(sentenceTime, tokenTime, lemmaTime)

# Pass the author and the textcolum to parse the whole dataframe
def parseDataFrame(df, authorColumn, titleColumn, textColumns, language, model):
    BeginTime= time.time()
    counter=0
    for index, row in df.iterrows():
        author = row[authorColumn]
        title = row[titleColumn]
        for column in textColumns:
            text = row[column]
            title = row[titleColumn]
            counter=counter+1
            try:
                textSentTokLemma_2neo(author, title, text, language, model)
            except:
                pass
    TimetimePassed=time.time()
    message= 'DataFrame processed with: '+str(counter)+' texts in: '+str(TimetimePassed-BeginTime)
    return (message)

