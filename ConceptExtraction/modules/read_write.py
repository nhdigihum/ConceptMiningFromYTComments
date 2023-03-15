import json

def yield_sentences(file_path):
    with open(file_path, 'r', encoding='utf8') as f:
        for line in f:
            data = json.loads(line)
            yield data

def yield_tokens(file_path:str, only_tokens:bool=False):
    with open(file_path, 'r', encoding='utf8') as f:
        for line in f:
            entry = json.loads(line)
            if only_tokens:
                for tokenized_sent in entry['tokenized_sentences']:
                    yield tokenized_sent
            else:   
                yield entry

def read_vocab(file_path:str):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            print(f'read:{f}')
        return data

def write_tokens(
        file_path:str,
        sentence_id:int,
        comment_id:str,
        video_id:str,
        tokenized_sentences:list,
        concepts:list[str]=[]
        ):
    with open(file_path, 'a') as f:
        data = {
            'sentence_id': sentence_id,
            'comment_id': comment_id,
            'video_id': video_id,
            'tokenized_sentences': tokenized_sentences,
            'concepts': concepts
        }
        json.dump(data, f)
        f.write('\n')

def write_vocab(file_path:str, vocab:list):
    with open(file_path,'w') as f:
        data = {'vocab':vocab}
        json.dump(data, f)

def write_similarities(file_path:str, concept_to_similarities):
    with open(file_path, 'w') as f:
        json.dump(concept_to_similarities, f)