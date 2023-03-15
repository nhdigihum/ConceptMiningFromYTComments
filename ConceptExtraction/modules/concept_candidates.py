import spacy
import spacy_dbpedia_spotlight
from itertools import product

#DBpedia SSLCertVerificationError:
#https://github.com/MartinoMensio/spacy-dbpedia-spotlight/issues/23
# you can suppress warnings with this
import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
# and now no warnings

nlp = spacy.load('en_core_web_lg')
nlp.add_pipe('dbpedia_spotlight', config={'verify_ssl': False}) #temp SSL cert verification off -> workaround for the issue
print(f'nlp pipeline in concept_candidates.py: {nlp.pipeline}')

def get_concept_candidates(sentence:str)->tuple[list, list, list]:
    '''
    takes sentence and extracts & returns 
    DBpedia entities, single nouns and noun chunks from it.
    '''

    try:
        sentence = nlp(sentence)
    except:
        return ([],[],[])

    spans = []
    single_nouns = []
    noun_chunks = []
    db_pedia_entities = []

    #for i,sn in enumerate(sentence):
        #if sn.pos_ =='NOUN':
            #spans.append( (i,i+1) )
            #single_nouns.append(sn.text)
    for nc in sentence.noun_chunks:
        spans.append( (nc.start, nc.end) )
        noun_chunks.append(nc.text)
    for dbe in sentence.ents:
        if dbe.label_ == 'DBPEDIA_ENT' and dbe.root.pos_ == "NOUN":
            spans.append( (dbe.start, dbe.end) )
            db_pedia_entities.append(dbe.text)

    
    concept_candidates = list(set(single_nouns + noun_chunks + db_pedia_entities))
    return (concept_candidates, db_pedia_entities, spans)

def concept_representations(sentence:str, spans:list[tuple[int]])->list:
   
    try:
        sentence = nlp(sentence)
    except:
        return []


    doc_spans = [ sentence[ span[0]:span[1] ] for span in spans ]
    filtered = spacy.util.filter_spans(doc_spans)
    end_exclusive_superspans = [(t.start, t.end) for t in filtered]
    end_inclusive_superspans = [(t.start, t.end-1) for t in filtered]

    end_exclusive_spans = spans + end_exclusive_superspans
    end_inclusive_spans = [( s[0], s[1]-1 ) for s in end_exclusive_spans]

    superspan_groups = []

    for i,super_span in enumerate(end_inclusive_superspans):
        superspan_members = [ end_exclusive_superspans[i] ] #always add end-exclusive span
        for j,other_span in enumerate(end_inclusive_spans):
            if super_span != other_span and ((other_span[0] >= super_span[0] and other_span[0] <= super_span[1]) or (other_span[1] >= super_span[0] and other_span[1] <= super_span[1])):
                superspan_members.append( end_exclusive_spans[j] )
        min_end = min([s[0] for s in superspan_members])
        max_end = max([s[1] for s in superspan_members])
        if (min_end,max_end) not in superspan_members:
            superspan_members.append((min_end,max_end))
        superspan_members = list(set(superspan_members))
        superspan_groups.append(superspan_members)

    combinations = list(product(*superspan_groups))

    repr_sentences = []
    token_spans = [(i,i+1) for i,_ in enumerate(sentence)]
    for comb in combinations:
        comb_spans = token_spans + [c for c in comb]
        comb_spans = [sentence[c[0]:c[1]] for c in comb_spans]
        filtered = spacy.util.filter_spans(comb_spans)
        sent = [t.text for t in filtered]
        if sent not in repr_sentences:
            repr_sentences.append( sent )
    
    
        
    return repr_sentences
