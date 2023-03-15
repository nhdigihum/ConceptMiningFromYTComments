from config import API_KEY
import googleapiclient.discovery
import googleapiclient.errors

import json


PATH_TO_WRITE = './data/quality_videos_groups/v_ids.txt'

CHANNEL_ID = "UC5B86a7N4VvxgoiVKBNHBMA" #channelid of the YouTube channel: F4m1LyGuy10

YOUTUBE = googleapiclient.discovery.build(
    'youtube',
    'v3',
    developerKey=API_KEY
    )

def channel_upload_playlist(channel_id):
    channel_response = YOUTUBE.channels().list(
        part = 'contentDetails',
        id = channel_id
    ).execute()
    uploads = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    return uploads

def get_vids(playlist_id):
    last_page_tokens = []

    video_ids = []
    items = []
    page_token = ""
    result_count = 0
    max_results = 50
    terminator = 100000
    
    while result_count <= terminator:
        if page_token != "":
            playlist_response = YOUTUBE.playlistItems().list(
                part = 'snippet',
                playlistId = playlist_id,
                maxResults = max_results,
                pageToken = page_token
            ).execute()
        else:
            playlist_response = YOUTUBE.playlistItems().list(
                part = 'snippet',
                playlistId = playlist_id,
                maxResults = max_results
            ).execute() 
        items = items + playlist_response["items"]
        total_results = playlist_response["pageInfo"]["totalResults"]
        terminator = total_results 
        if "nextPageToken" in playlist_response:
            page_token = playlist_response["nextPageToken"]
        result_count = result_count + max_results
       
    last_page_tokens.append(page_token)

    for item in items:
        video_ids.append(item["snippet"]["resourceId"]["videoId"])
    
    return video_ids

def write_ids(file_path, ids):
    with open(file_path, 'w') as f:
        json.dump(ids, f)
        print('wrote video ids.')

def main():
    playlist = channel_upload_playlist(CHANNEL_ID)
    vid_ids = get_vids(playlist)
    vid_ids  = {'ids':vid_ids}
    write_ids(PATH_TO_WRITE, vid_ids)


if __name__ == '__main__':
    main()
