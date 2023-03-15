from config import API_KEY
import googleapiclient.discovery
import googleapiclient.errors
import json

# ==============================================================
# variables
# ==============================================================

PATH_TO_VIDEO_IDS = '../data/quality_videos_groups/v_ids.txt'
PATH_TO_RAW_COMMENT_DATA = '../data/comments/00comments.txt'

NUMBER_OF_VIDEOS_PER_REQUEST = 5

# Create a YOUTUBE API client
YOUTUBE = googleapiclient.discovery.build(
    'youtube',
    'v3',
    developerKey=API_KEY
    )

# ==============================================================
# load videos
# ==============================================================

def get_video_ids(filepath):
    with open (filepath, 'r', encoding='utf8') as f:
        data = json.load(f)
        return data
    
def _request_comments( video_id:str,  max_results:int=NUMBER_OF_VIDEOS_PER_REQUEST ) -> dict:
    kwargs = {"part": "snippet,replies", "order": "relevance", "videoId": video_id, "maxResults": max_results}
    response = YOUTUBE.commentThreads().list(**kwargs).execute()
    return (response['items'])

def collect_comments(video_ids:list[str])->list:

    comments_and_replies = []  #format: [{video_id:str, comment_id:str, type:str<comment/reply>, comment_text:str}, ...]
    for video_id in video_ids:
        print(f'collecting comments for video with id: {video_id}')

        comment_items = _request_comments( video_id )
        for ci in comment_items:
            comments_and_replies.append(
                {
                'video_id':video_id,
                'comment_id':ci["snippet"]["topLevelComment"]["id"],
                'type':'comment',
                'comment_text':ci["snippet"]["topLevelComment"]["snippet"]["textDisplay"] 
                }
            )
            if 'totalReplyCount' in ci["snippet"].keys() and ci["snippet"]["totalReplyCount"] > 0 and 'replies' in ci:
                if 'comments' in ci['replies']:
                    replies = ci["replies"]["comments"]
                    for reply in replies:
                        comments_and_replies.append(
                            {
                            'video_id':video_id,
                            'comment_id':reply["snippet"]["parentId"],
                            'type':'reply',
                            'comment_text':reply["snippet"]["textOriginal"]
                            }
                        )
                        
    return comments_and_replies

# ==============================================================
# write comments
# ==============================================================

def write_comments(filepath, comments:list[dict]):
    data = {'comments':comments}
    with open (filepath, 'w', encoding='utf-8') as f:
        data = json.dump(data, f)
        return data

def main():
    vid_ids = get_video_ids(PATH_TO_VIDEO_IDS)
    comments = collect_comments(vid_ids['ids'])
    write_comments(PATH_TO_RAW_COMMENT_DATA,comments)

if __name__ == '__main__':
    main()
