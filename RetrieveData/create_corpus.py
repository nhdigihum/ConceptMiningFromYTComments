import json
import html
import re
import spacy

PATH_TO_RAW_DATA = './data/comments/00comments.txt'
PATH_TO_PROCESSED_DATA = './data/corpus/0comment_sentences_clean.txt'

MAX_SENTENCE_LENGTH = 100 #somewhat arbitrary max sentence threshold

nlp = spacy.load('en_core_web_lg')

# ==============================================================
# read raw data
# ==============================================================
def read_data(filepath):
    with open (filepath, 'r', encoding='utf8') as f:
        raw_data = json.load(f)
        return raw_data

# ==============================================================
# sentenize & preprocess
# ==============================================================

def split_comment_to_sentences( comment:str )->list[str]:
    sentences = [sent.text for sent in nlp(comment).sents]
    for sentence in sentences:
        yield sentence

def preprocess_sentence( comment ):
    processed = html.unescape(comment.lower())
    #processed = re.sub(r'(<a [\s\w\d\S+]*>)','[link]', processed)
    processed = re.sub(r'(\,(<br>\s*)+)', ', ', processed)
    processed = re.sub(r'(\:(<br>\s*)+)', ': ', processed)
    processed = re.sub(r'(\;(<br>\s*)+)', '; ', processed)
    processed = re.sub(r'(\.(<br>\s*)+)', '. ', processed)
    processed = re.sub(r'((<br>\s*)+)', ' – ', processed)
    processed = re.sub(r'(<.*?>)', '', processed)
    return processed

# ==============================================================
# write preprocessed sentences
# ==============================================================

def write_sentence(
        file_path:str,
        sentence:str,
        video_id:str,
        comment_id:str,
        comment_type:str
        ):
    with open(file_path, 'a', encoding='utf8') as f:
        data = {
            'sentence':sentence,
            'video_id':video_id,
            'comment_id':comment_id,
            'type':comment_type
        }
        f.write(json.dumps(data) + '\n')

# ==============================================================
# main process
# ==============================================================

def main():
    print('read data raw data into memory ...')
    raw_data = read_data(PATH_TO_RAW_DATA)['comments']
    total_comment_count = len(raw_data)
    for i,comment in enumerate(raw_data):
        video_id = comment['video_id']
        comment_text = comment['comment_text']
        comment_id = comment['comment_id']
        comment_type = comment['type']
        preprocessed_comment = preprocess_sentence(comment_text)
        for sentence in split_comment_to_sentences(preprocessed_comment):
            if len(sentence) <= MAX_SENTENCE_LENGTH:
                write_sentence(
                    PATH_TO_PROCESSED_DATA,
                    sentence,
                    video_id,
                    comment_id,
                    comment_type
                    )
            print(f'wrote {i}/{total_comment_count} comments.')
    print(f'corpus has been created and written to:\n{PATH_TO_PROCESSED_DATA}')

if __name__ == '__main__':
    main()
