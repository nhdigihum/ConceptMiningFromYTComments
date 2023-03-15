from gensim.models import Word2Vec
from modules.read_write import yield_tokens

def train_w2v_model(path_to_tokens:str, path_to_model_weights:str, save_weights:bool=True):
    class CorpusSentences:
        def __init__(self, filepath):
            self.filepath = filepath

        def __iter__(self):
            yield from yield_tokens(self.filepath,only_tokens=True)

    sentences = CorpusSentences(path_to_tokens)
    model = Word2Vec(sentences, min_count=1, epochs=5)
    print('trained w2v_model')

    if save_weights:
        model.save(path_to_model_weights)
        print(f'weights written to: {path_to_model_weights}')

    return model

def get_embeddings(model, concept_candidates_vocab:list[str])->dict:
    cc_to_embeddings = {}
    for cc in concept_candidates_vocab:
        cc_to_embeddings[cc] = model.wv[cc] 
    return cc_to_embeddings
