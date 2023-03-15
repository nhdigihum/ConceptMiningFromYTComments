from config import API_KEY
import googleapiclient.discovery
import googleapiclient.errors
import json

# ==============================================================
# variables
# ==============================================================

PATH_TO_VIDEO_GROUPS = './data/quality_videos_groups/v_ids.txt'
PATH_TO_RAW_COMMENT_DATA = './data/comments/comments.json'

QUOTA_COST_LIMIT = 1000 # cancel further requests if quota cost exeeds

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
    
# ==============================================================
# retrieve comments & replies
# ==============================================================

def _request_comments( video_id:str, page_token:str, max_results:int=50,  ) -> dict:
    kwargs = {"part": "snippet,replies", "videoId": video_id, "maxResults": max_results}
    if page_token != '': kwargs["pageToken"] = page_token 
    response = YOUTUBE.commentThreads().list(**kwargs).execute()
    if 'nextPageToken' in response:
        next_page_token = response['nextPageToken']
    else:
        next_page_token = ''
    return (response['items'], next_page_token)

def collect_comments(video_ids:list[str], total_comment_counts:list[int])->list:
    quota_cost = 0
    comments_and_replies = []  #format: [{video_id:str, comment_id:str, type:str<comment/reply>, comment_text:str}, ...]
    for video_id, videos_total_comment_count in zip(video_ids, total_comment_counts):
        print(f'collecting comments for video with id: {video_id}')
        collected_comments_count = 0
        all_pages_retrieved = False
        page_token = ''
        while not all_pages_retrieved:
            comment_items, page_token = _request_comments( video_id, page_token )
            quota_cost += 1
            print(f'current quota cost: {quota_cost}')

            for ci in comment_items:
                comments_and_replies.append(
                    {
                    'video_id':video_id,
                    'comment_id':ci["snippet"]["topLevelComment"]["id"],
                    'type':'comment',
                    'comment_text':ci["snippet"]["topLevelComment"]["snippet"]["textDisplay"] 
                    }
                )
                if 'totalReplyCount' in ci["snippet"].keys() and ci["snippet"]["totalReplyCount"] > 0:
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
            collected_comments_count += len(comment_items)
            print(f'{collected_comments_count}/{videos_total_comment_count} comments collected. (without replies)')
            if not page_token or quota_cost >= QUOTA_COST_LIMIT:
                all_pages_retrieved = True
                            
        print(f"got comments for video with id: {video_id}")
        if quota_cost >= QUOTA_COST_LIMIT:
            break
    return comments_and_replies

# ==============================================================
# write comments
# ==============================================================

def write_comments(filepath, comments:list[dict]):
    data = {'comments':comments}
    with open (filepath, 'w', encoding='utf-8') as f:
        data = json.dump(data, f)
        return data

# ==============================================================
# main process
# ==============================================================

def main():
    data = get_video_ids( PATH_TO_VIDEO_GROUPS )
    vid_tcc = list(set(
        [(key, group[key]['comment_count']) for group in data.values() for key in group.keys() if int(group[key]['comment_count']) > 0 ]
        ))
    video_ids = [video[0] for video in vid_tcc]
    total_comment_counts = [video[1] for video in vid_tcc]
    print(f'video_ids:\n{video_ids}')
    comments = collect_comments( video_ids, total_comment_counts )
    write_comments( PATH_TO_RAW_COMMENT_DATA, comments )
    print(f'wrote raw coment data at: {PATH_TO_RAW_COMMENT_DATA}')

if __name__ == '__main__':
    main()
