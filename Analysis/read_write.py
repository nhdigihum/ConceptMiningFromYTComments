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


def write_notes(file_path:str, notes:list[str]):
    with open(file_path, 'a', encoding='utf-8') as f:
        for note in notes:
            f.write(note)
            f.write('\n')
        f.write('\n')
