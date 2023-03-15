from sklearn.metrics.pairwise import cosine_similarity

#imports for est. concept quality
from collections import defaultdict

#imports for quality factor weighting
from sklearn.ensemble import RandomForestRegressor

def init_train_rf_regressor(X_train, y_train):
    rf_model = RandomForestRegressor()
    rf_model.fit(X_train, y_train)
    return rf_model

def create_training_pairs(positive_examples_quality:list, negative_examples_quality:list):
    X_train = positive_examples_quality + negative_examples_quality
    p_label = [1.0]*len(positive_examples_quality)
    n_label = [0.0]*len(negative_examples_quality)
    y_train = p_label + n_label
    return (X_train, y_train)


def calculate_similarity_threshold(concept_candidate_to_embedding:dict)->float:
    '''
    to define a concepts similarity neighborhood a threshold variable is used to
    decide within which cosine similarity value (cosine similarity of 1.0 being a 
    distance of 0.0) two concepts are to be treated neighbors. this function calculates
    then variable's value.
    '''

    similarity_matrix = cosine_similarity(list(concept_candidate_to_embedding.values())) 
    top_similarities = []
    for lst in similarity_matrix:
        top_similarities.append(sorted(lst, reverse=True)[10])
    threshold_value =  sum(top_similarities)/len(top_similarities)
    return threshold_value

def estimate_concept_quality(concept_candidate_to_embedding, threshold_value:float, entities_vocab:list)->dict:
    concepts = list(concept_candidate_to_embedding.keys())
    quality_measures = [[] for _ in concepts]
    similarity_neighborhoods = defaultdict(list) 

    #context commonness
    similarity_matrix = cosine_similarity([concept_candidate_to_embedding[c] for c in concepts]) 
    for i, similarity_values in enumerate(similarity_matrix):
        concept_a = concepts[i]
        context_commonness = 0
        for j, similarity in enumerate(similarity_values):
            concept_b = concepts[j]
            if similarity >= threshold_value and concept_b != concept_a:
                context_commonness += 1
                similarity_neighborhoods[concept_a].append(concept_b)
        quality_measures[i].append(context_commonness)

    # context purity
    for i, concept in enumerate(concepts):
        embeddings = [concept_candidate_to_embedding[concept]] +  [concept_candidate_to_embedding[c] for c in similarity_neighborhoods[concept]]
        if len(similarity_neighborhoods[concept]) >= 1:
            avg_similarity_within_similarity_neighborhood = sum(cosine_similarity(embeddings)[0][1:])/len(similarity_neighborhoods[concept])
        else:
            avg_similarity_within_similarity_neighborhood = 0
        context_purity = avg_similarity_within_similarity_neighborhood
        quality_measures[i].append(context_purity)

    # context link-ability
    for i, concept in enumerate(concepts):
        similarity_neighborhood = similarity_neighborhoods[concept]
        context_linkability = sum([1 for snc in similarity_neighborhood if snc in entities_vocab])
        quality_measures[i].append(context_linkability)
    
    # context generalizability

    for i, concept in enumerate(concepts):
        similarity_neighborhood = similarity_neighborhoods[concept]
        context_generalizability = sum([1 for snc in similarity_neighborhood if concept in snc])
        quality_measures[i].append(context_generalizability)
    
    concept_to_quality_measures = {}
    for c,qm in zip(concepts,quality_measures):
        concept_to_quality_measures[c] = qm

    return  concept_to_quality_measures