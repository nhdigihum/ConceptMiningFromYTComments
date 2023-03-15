import os
import spacy
import math
import random
from sklearn.metrics.pairwise import cosine_similarity
import time

from modules.read_write import yield_sentences, yield_tokens, read_vocab, write_tokens, write_similarities, write_vocab
from modules.concept_candidates import get_concept_candidates, concept_representations
from modules.embeddings import get_embeddings, train_w2v_model
from modules.concept_quality import calculate_similarity_threshold, estimate_concept_quality, create_training_pairs, init_train_rf_regressor

# ==============================================================
# variables
# ==============================================================

PATH_TO_CORPUS = './data/corpus/0comment_sentences_clean.txt' # preprocessed and ready to use
PATH_TO_TEMP_CONCEPT_REPRESENTATION_CORPUS = './data/output/0temp_concept_repr_candidates.txt'
PATH_TO_CONCEPT_REPRESENTATION_CORPUS = './data/output/0concept_representation.txt'
PATH_TO_SIMILARITY_MATRIX_DUMP = './data/output/0similarities.txt'
PATH_TO_MODEL_WEIGHTS = './model/0w2v_model.bin'
PATH_TO_TEMP_CONCEPT_VOCAB = './data/output/0temp_concept_vocab.txt'
PATH_TO_TEMP_ENTITIES_VOCAB = './data/output/0temp_entities_vocab.txt'
assert not os.path.isfile(PATH_TO_TEMP_CONCEPT_REPRESENTATION_CORPUS)
assert not os.path.isfile(PATH_TO_CONCEPT_REPRESENTATION_CORPUS)
assert not os.path.isfile(PATH_TO_SIMILARITY_MATRIX_DUMP)

#WINDOW_SIZE = 5
NUM_RANDFOR_MODEL_SAMPLES = 30

nlp = spacy.load('en_core_web_lg')

concept_candidate_to_quality = {} # str:float
concept_candidate_to_embedding = {} # str:list[float] 
concept_candidates_vocab = [] # list[str]
entities_vocab = []
sentence_count = 0
last_sentence_id = 0

CONTINUE = False #if data processing got interrupted
assert CONTINUE == False
if CONTINUE:
    last_sentence_id = 6978 + 1 #3718 + 1
    concept_candidates_vocab = read_vocab(PATH_TO_TEMP_CONCEPT_VOCAB)['vocab']
    entities_vocab = read_vocab(PATH_TO_TEMP_ENTITIES_VOCAB)['vocab']
    PATH_TO_CORPUS = './data/corpus/comment_sentences_clean_continue.txt'
    print(f'path to corpus is: \n{PATH_TO_CORPUS}')
    assert type(concept_candidates_vocab) == list and type(entities_vocab) == list

# ==============================================================
# create concept candidates 
# & write concept representation candidate sentences,
# & generate contextual embeddings
# ==============================================================

start_time = time.time()
print('create concept candidates ...')
for i,comment in enumerate(yield_sentences(PATH_TO_CORPUS)):

    sentence = comment['sentence']
    comment_id = comment['comment_id']
    video_id = comment['video_id']

    concept_candidates, entities, spans = get_concept_candidates(sentence)

    for ent in entities:
        entities_vocab.append(ent)

    for candidate in concept_candidates: 
        concept_candidates_vocab.append(candidate)
    
    tokenizations = concept_representations(
        sentence,
        spans
        )
    
    write_tokens(
        file_path= PATH_TO_TEMP_CONCEPT_REPRESENTATION_CORPUS,
        sentence_id= i+last_sentence_id,
        comment_id = comment_id,
        video_id = video_id,
        tokenized_sentences= tokenizations
        ) 
    
    write_vocab(
        file_path= PATH_TO_TEMP_CONCEPT_VOCAB,
        vocab = concept_candidates_vocab
    )

    write_vocab(
        file_path= PATH_TO_TEMP_ENTITIES_VOCAB,
        vocab = entities_vocab
    )

    sentence_count += 1
    if sentence_count % 10 == 0:
        print(f'tokenized {sentence_count} of ~75845 sentences.')

concept_candidates_vocab = list(set( concept_candidates_vocab ))
entities_vocab = list(set( entities_vocab ))
print(f"the entirety of the concept candidates consists of:\n{concept_candidates_vocab}")

end_time = time.time()
print(f"Time taken: {end_time - start_time} seconds")

# ==============================================================
# train Word2Vec model
# ==============================================================

w2v_model = train_w2v_model(
    path_to_tokens=PATH_TO_TEMP_CONCEPT_REPRESENTATION_CORPUS,
    path_to_model_weights=PATH_TO_MODEL_WEIGHTS,
    save_weights = True
    )

# ==============================================================
# calculate candidates quality values
# ==============================================================

concept_candidate_to_embedding = get_embeddings(w2v_model, concept_candidates_vocab)
similarity_threshold = calculate_similarity_threshold(concept_candidate_to_embedding)
print(f'similarity threshold: {similarity_threshold}')

concept_candidate_to_quality = estimate_concept_quality(
        concept_candidate_to_embedding,
        similarity_threshold,
        entities_vocab)

# ==============================================================
# train model to weight quality measures
# => use prediction as quality
# ==============================================================

num_of_samples = NUM_RANDFOR_MODEL_SAMPLES
sample_words = [] 

#collect a few sentences to create negative examples 
for sentences in yield_tokens(PATH_TO_TEMP_CONCEPT_REPRESENTATION_CORPUS):

    sentence = sentences['tokenized_sentences'][0]
    if  len(sample_words) < num_of_samples:
        non_concept_words = [token for token in sentence if token not in concept_candidates_vocab]
        if non_concept_words:
            idx = random.randint(0,len(non_concept_words)-1)
            if non_concept_words[idx] not in sample_words:
                sample_words.append(non_concept_words[idx])
    else:
        break
            
negative_examples_enbeddings = get_embeddings(w2v_model, sample_words)
negative_examples_quality = list( estimate_concept_quality(
    negative_examples_enbeddings,
    similarity_threshold,
    entities_vocab).values() )

# per definition DBPedia entities are quality concepts of quality 1.0
sample_words = [entities_vocab[random.randint(0,len(entities_vocab)-1)] for _ in range(num_of_samples)]
positive_examples_enbeddings = get_embeddings(w2v_model, sample_words)
positive_examples_quality = list( estimate_concept_quality(
    negative_examples_enbeddings,
    similarity_threshold,
    entities_vocab).values() ) 

X_train, y_train = create_training_pairs(
    positive_examples_quality,
    negative_examples_quality
    )
print(f'X_train: {X_train}')
print(f'y_train: {y_train}')
quality_prediction_model = init_train_rf_regressor(X_train, y_train)

# ==============================================================
# concept recognition/candidate selection
# & store concepts and their similarity
# ==============================================================

#read the candidate sentences and find the otimal candidate selection for each
print('concept recognition...')
recognized_concepts_with_embeddings = []
for i,sentence in enumerate(yield_tokens(PATH_TO_TEMP_CONCEPT_REPRESENTATION_CORPUS)):
    
    tokenized_sentences = sentence['tokenized_sentences']
    max_objective = -1

    for tokenized_sentence in tokenized_sentences:
        concepts = [concept for concept in tokenized_sentence if concept in concept_candidates_vocab]
        embeddings = [concept_candidate_to_embedding[concept] for concept in concepts]
        context_fitness = 1.0
        if len(embeddings) > 1:
            context_fitness = math.prod(math.prod(cosine_similarity(embeddings)))
        objective = math.prod([quality_prediction_model.predict([concept_candidate_to_quality[concept]])[0] * context_fitness for concept in concepts])
        if objective > max_objective:
            max_objective = objective
            selection = (tokenized_sentence, concepts, embeddings)
    write_tokens(
        file_path=PATH_TO_CONCEPT_REPRESENTATION_CORPUS,
        sentence_id=i,
        comment_id = sentence['comment_id'],
        video_id = sentence['video_id'],
        tokenized_sentences=selection[0],
        concepts = selection[1]
    )
    for concept, embedding in zip(selection[1], selection[2]):
        recognized_concepts_with_embeddings.append((concept,embedding))
    
    print(f'extracted from {i+1} of {sentence_count} sentences')


# store similarity matrix: concept from winning concepts: similarity matrix row
similarities = cosine_similarity( [e for c,e in recognized_concepts_with_embeddings ] )
recognized_concepts_to_siliarities = {c[0] : s.tolist() for c,s in zip(recognized_concepts_with_embeddings,similarities)}
write_similarities( PATH_TO_SIMILARITY_MATRIX_DUMP, recognized_concepts_to_siliarities )

# cleaning up temporary file
#os.remove(PATH_TO_TEMP_CONCEPT_REPRESENTATION_CORPUS)

print('extracted and wrote concepts')
