import streamlit as st #For streamlit application developement
from googleapiclient.discovery import build # Google Api python client for fetching the data from youtube using API
from googleapiclient.errors import HttpError # Google Api python client for handling HTTP error 
from datetime import datetime #for handling date and time 
import pandas as pd #pandas 
import pymongo #for connection with mongodb 
import psycopg2 # For postgres queries and connection
import time #for time related functions
import re # for regular expression
import plotly.express as px #for charts 


# Setting page layout

st.set_page_config(
    page_title = "YT Scrapper",
    layout="centered",
    page_icon = ":dna:",
    menu_items = {
        'About' : "Created By Rohit Tambavekar 'https://www.linkedin.com/in/rohit-tambavekar/'"
    }
    
    )

# Define constants
SIDEBAR_EXTRACT_OPTIONS = ["Channel ID", "Multiple Channel IDs"] #, "Video ID", "Playlist ID"
CHANNEL_FIELDS = ["channel_name","_channel_id", "subscriber_count", "view_count", "description", 
                  "country", "video_count", "playlist_id", "channel_type","channel_status"]
VIDEO_FIELDS = ["video_id", "video_title", "video_description", "tags","published_at",
                "view_count", "favorite_Count","video_favorite_Count", "comment_count","thumbnails"]
PLAYLIST_FIELDS = ["title", "description", "publishedAt", "itemCount"]
CHANNEL_VIDEO_COMMENT = ["Video_Id","Video_Name","Tags","PublishedAt","View_Count","Like_Count",
                         "Favorite_Count","Comment_Count","Duration","Thumbnail","Caption_Status"]
REPORTS_OPTION = [
    "1. What are the names of all the videos and their corresponding channels?",
    "2. Which channels have the most number of videos, and how many videos do they have?",
    "3. What are the top 10 most viewed videos and their respective channels?",
    "4. How many comments were made on each video, and what are their corresponding video names?",
    "5. Which videos have the highest number of likes, and what are their corresponding channel names?",
    "6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
    "7. What is the total number of views for each channel, and what are their corresponding channel names?",
    "8. What are the names of all the channels that have published videos in the year 2022?",
    "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?",
    "10.Which videos have the highest number of comments, and what are their corresponding channel names?"    
    ]

# Define helper functions
# Getiing the channel details from youtube using API
def get_youtube_channel_info(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    try:
        channel_response = youtube.channels().list(
            part='snippet,contentDetails,statistics,topicDetails,status',
            id=channel_id,
        ).execute()
        channel = channel_response.get('items', [])[0]
        if not channel:
            st.write(f"No channel found with ID {channel_id}")
            return None
        if 'topicDetails' in channel:
            channel_type = channel['topicDetails'].get('topicCategories', [])
            channel_type = channel_type[0].split('/')[-1]
        else:
            channel_type = "N/A"
        channel_dict = {
            'channel_name': channel['snippet'].get('title', 'N/A'),
            '_channel_id': channel.get('id'),
            'subscriber_count': channel['statistics'].get('subscriberCount', 'N/A'),
            'view_count': channel['statistics'].get('viewCount', 'N/A'),
            'description': channel['snippet'].get('description', 'N/A'),
            'country': channel['snippet'].get('country', 'N/A'),
            'video_count': channel['statistics'].get('videoCount', 'N/A'),
            'playlist_id': channel['contentDetails']['relatedPlaylists'].get('uploads', 'N/A'),
            'channel_type': channel_type,
            'channel_status': channel['status'].get('privacyStatus', 'N/A')
        }
        return channel_dict
    except HttpError as e:
        st.write(f"An error occurred: {e}")
        return None
# Getiing the vedio details from youtube using API
def get_video_details(api_key, video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    response = youtube.videos().list(
        part='snippet,statistics,contentDetails',
        id=video_id
    ).execute()
    video = response.get('items', [])[0]
    video_details = {}
    video_details['Video_Id'] = video.get('id')
    video_details['Video_Name'] = video.get('snippet', {}).get('title')
    video_details['Video_Description'] = video.get('snippet', {}).get('description')
    video_details['Tags'] = video.get('snippet', {}).get('tags', [])
    video_details['PublishedAt'] = datetime.fromisoformat(video.get('snippet', {}).get('publishedAt', '').replace('Z', '+00:00')).strftime('%Y-%m-%d Time %H:%M:%SZ')
    video_details['View_Count'] = video.get('statistics', {}).get('viewCount')
    video_details['Like_Count'] = video.get('statistics', {}).get('likeCount')
    video_details['Favorite_Count'] = video.get('statistics', {}).get('favoriteCount')
    comment_count = video.get('statistics', {}).get('commentCount')
    if comment_count == 'none':
        video_details['Comment_Count'] = None
    elif comment_count == 'Disabled':
        video_details['Comment_Count'] = "Disabled"
    else:
        video_details['Comment_Count'] = comment_count
    duration_str = video.get('contentDetails', {}).get('duration', 'PT0S')[2:].lower()
    # Split duration string into hours, minutes, and seconds
    hours = 0
    if 'h' in duration_str:
        hours, duration_str = duration_str.split('h')
        hours = int(hours)

    minutes = 0
    if 'm' in duration_str:
        minutes, duration_str = duration_str.split('m')
        minutes = int(minutes)
    
    seconds = 0
    if 's' in duration_str:
        seconds = duration_str.replace('s', '')
        seconds = int(seconds)

    # # Convert minutes, seconds, and hours to integers
    # minutes = int(minutes) if minutes else 0
    # seconds = int(seconds) if seconds else 0

    # Compute total duration in seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds

    # Format duration as string
    duration_formatted = f"{total_seconds // 3600:02d}:{total_seconds % 3600 // 60:02d}:{total_seconds % 60:02d}"
    # video_details['Duration'] = video.get('contentDetails', {}).get('duration', 'PT0S')[2:].lower()
    video_details['Duration'] = duration_formatted
    video_details['Thumbnail'] = video.get('snippet', {}).get('thumbnails', {}).get('default', {}).get('url')
    video_details['Caption_Status'] = video.get('contentDetails', {}).get('caption', 'notSpecified')
    return video_details
# Getiing the comments from video details from youtube using API
def get_video_comments(api_key, video_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments_dict = {}
    try:
        next_page_token = None
        while True:
            response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=300,
                pageToken=next_page_token
            ).execute()
            
            for item_index, item in enumerate(response.get('items', [])):
                comment_dict = {}
                comment_dict['Comment_Id'] = item.get('id', '')
                comment_dict['Comment_Text'] = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('textOriginal', '')
                comment_dict['Comment_Author'] = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('authorDisplayName', '')
                comment_dict['Comment_PublishedAt'] = item.get('snippet', {}).get('topLevelComment', {}).get('snippet', {}).get('publishedAt', '')
                comments_dict[f'Comment_id_{item_index+1}'] = comment_dict
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        if not comments_dict:
            comments = {"Comments": "N/A"}
            return comments
    except HttpError as e:
        error = eval(str(e.content.decode()))['error']['errors'][0]
        if error['reason'] == 'commentsDisabled':
            comments = {"Comments": "Disabled"}
            return comments
        else:
            comments = {"Comments": "N/A"}
            return comments
    comments = {"Comments": comments_dict}
    return comments
# updating the video and comments in one Json
def get_channel_videos(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)

    # retrieve the playlist id of the channel's uploaded videos
    channels_response = youtube.channels().list(
        id=channel_id,
        part='contentDetails'
    ).execute()
    
    playlist_id = channels_response.get('items', [])[0].get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
    
    if not playlist_id:
        print(f"No upload playlist found for channel ID {channel_id}")
        return None

    # retrieve all the videos in the playlist
    videos = []
    next_page_token = None

    while True:
        playlist_items = youtube.playlistItems().list(
            playlistId=playlist_id,
            part='snippet',
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        videos += playlist_items.get('items', [])

        next_page_token = playlist_items.get('nextPageToken')

        if not next_page_token:
            break
    # extract the video details and comments for each video
    video_details = {}

    for i, video in enumerate(videos):
        video_id = video.get('snippet', {}).get('resourceId', {}).get('videoId')
        if not video_id:
            print(f"No video ID found for video {i+1} in channel ID {channel_id}")
            continue
        video_info = get_video_details(api_key, video_id)
        if video_info:
            video_comments = get_video_comments(api_key, video_id)
            video_info.update(video_comments)
            video_details[f'Video_Id_{len(video_details)+1}'] = video_info
    return video_details
# Inserting the fetched data to mongoDB 
def push_api_data_in_mongodb(insert_json):
    mongo_conn_str = "mongodb://guvidsm23:dataentry@ac-yaydskh-shard-00-00.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-01.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-02.dbdtjgb.mongodb.net:27017/?ssl=true&replicaSet=atlas-xjikdp-shard-0&authSource=admin&retryWrites=true&w=majority"
    try:
        conn = pymongo.MongoClient(mongo_conn_str)
    except pymongo.errors.ConnectionFailure as e:
        right_col.write("Could not connect to MongoDB: %s" % e)
        exit()
    # for channel_name_index, channel_jsons in enumerate(channel_dict):
    sat_Conn = conn["YoutubeAPI"]
    db_Var = sat_Conn["Channel_data"]
    db_Var.insert_one(insert_json)
    return "Successful"
# checking the channel details are already present in the MongoDB database
def validate_json_in_mongodb(): 
    mongo_conn_str = "mongodb://guvidsm23:dataentry@ac-yaydskh-shard-00-00.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-01.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-02.dbdtjgb.mongodb.net:27017/?ssl=true&replicaSet=atlas-xjikdp-shard-0&authSource=admin&retryWrites=true&w=majority"
    try:
        conn = pymongo.MongoClient(mongo_conn_str)
    except pymongo.errors.ConnectionFailure as e:
        right_col.write("Could not connect to MongoDB: %s" % e)
        exit()
    
    # for channel_name_index, channel_jsons in enumerate(channel_dict):
    db = conn["YoutubeAPI"]
    collection = db["Channel_data"]
    data = list(collection.find())
    name =[]
    for doc in data:
        for subdoc_name, subdoc_value in doc.items():
            if isinstance(subdoc_value, dict) and 'channel_name' in subdoc_value and '_channel_id' in subdoc_value:
                name.append(subdoc_value['channel_name'])
                    
    return name
#Creating a connection to Postgres SQL
def sql_connection():
     # Connect to the Postgres database
    try:
        conn = psycopg2.connect(
            host='localhost', 
            user ='postgres',
            password='rayz',
            port=5432,
            database='YoutubeAPI'
        )
    except Error as e:
        right_col.write(f"Upload data into database: {e}")    
    # Create a cursor object
    cur = conn.cursor()
    return cur, conn
# Fetching the channel names and IDs from MongoDB to populate the dropdown function in the sidebar
def fetch_and_display_data(query_by):
    # Set up the MongoDB connection
    mongo_conn_str = "mongodb://guvidsm23:dataentry@ac-yaydskh-shard-00-00.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-01.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-02.dbdtjgb.mongodb.net:27017/?ssl=true&replicaSet=atlas-xjikdp-shard-0&authSource=admin&retryWrites=true&w=majority"
    conn = pymongo.MongoClient(mongo_conn_str)
    db = conn['YoutubeAPI']
    collection = db['Channel_data']

    # setup Postgres connection
    conn = psycopg2.connect(
        host='localhost',
        user ='postgres',
        password='rayz',
        port=5432,
        database='YoutubeAPI'
    )
    
    sql_ids = []
    sql_names = []
    sql_validator = []
    try:
        with conn.cursor() as cur:
            if query_by == "ID":
                cur.execute("SELECT channel_id, channel_name FROM channel")
                sql_validator = cur.fetchall()
                for sql_id, sql_name in sql_validator:
                    sql_ids.append(sql_id)
                    sql_names.append(sql_name)
            elif query_by == "Name":
                cur.execute("SELECT channel_id, channel_name FROM channel")
                sql_validator = cur.fetchall()
                for sql_id, sql_name in sql_validator:
                    sql_ids.append(sql_id)
                    sql_names.append(sql_name)
                
    except psycopg2.errors.UndefinedTable:
        # The channel table does not exist
        pass

    conn.close()
           
    # Fetch the data from the collection
    data = list(collection.find())
    name =[]
    id = []
    no_db_found = ["No Database found"]
    for doc in data:
        for subdoc_name, subdoc_value in doc.items():
            if isinstance(subdoc_value, dict) and 'channel_name' in subdoc_value and '_channel_id' in subdoc_value:
                name.append(subdoc_value['channel_name'])
                id.append(subdoc_value['_channel_id'])
    
    id = [validated_ids for validated_ids in id if validated_ids not in sql_ids ]
    name = [validated_names for validated_names in name if validated_names not in sql_names]
    
    for i in range(len(name)):
        name[i] = re.sub(r'\s+', '_', name[i])
    if query_by == "ID" and sql_validator is not None:
        if not id:
            selected_db_name = st.sidebar.selectbox("Select a database",no_db_found)
            upload_to_sql = st.sidebar.button("Upload to SQL",key="upload_button",disabled=True)
        else:
            selected_db_name = st.sidebar.selectbox(f"Select a database using channel {query_by}", options=id )
            if selected_db_name:
                upload_to_sql = st.sidebar.button("Upload to SQL",key="upload_button")
    elif query_by == "Name" and sql_validator is not None:
        if not name:
            selected_db_name = st.sidebar.selectbox("Select a database",no_db_found)
            upload_to_sql = st.sidebar.button("Upload to SQL",key="upload_button",disabled=True)
        else:
            selected_db_name = st.sidebar.selectbox(f"Select a database using channel {query_by}", options=name)
            if selected_db_name:
                upload_to_sql = st.sidebar.button("Upload to SQL",key="upload_button")
    
    return upload_to_sql,selected_db_name
# Data fetching and formatting required to push data into Postgres
def upload_sql_procedure(mongo_database_name,query_by):
    # Set up the MongoDB connection
    mongo_conn_str = "mongodb://guvidsm23:dataentry@ac-yaydskh-shard-00-00.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-01.dbdtjgb.mongodb.net:27017,ac-yaydskh-shard-00-02.dbdtjgb.mongodb.net:27017/?ssl=true&replicaSet=atlas-xjikdp-shard-0&authSource=admin&retryWrites=true&w=majority"
    client = pymongo.MongoClient(mongo_conn_str)
    db = client['YoutubeAPI']
    collection = db['Channel_data']
    # Fetch the data from the collection
    if query_by == "Name":
        mongo_database_name = mongo_database_name.replace(" ","_")
        query = {mongo_database_name: {"$exists": True}}
        data = list(collection.find(query))
    elif query_by == "ID":
        data = list(collection.find())
        for doc in data:
            for subdoc_name, subdoc_value in doc.items():
                if isinstance(subdoc_value, dict) and subdoc_value['_channel_id'] == mongo_database_name:
                    mongo_database_name = subdoc_value['channel_name']
                    mongo_database_name = mongo_database_name.replace(" ","_")
        query = {mongo_database_name: {"$exists": True}}
        data = list(collection.find(query))
    return data, mongo_database_name
# Create postgres DB and push the data from MongoDB to Postgres
def process_mongodb_data(data,mongo_database_name):
    
    # Create the Channel table
    create_table("Channel", "channel_id VARCHAR(255) PRIMARY KEY, channel_name VARCHAR(255),channel_type VARCHAR(255), subscriber_count INTEGER, view_count INTEGER, channel_description TEXT, country VARCHAR(255), video_count INTEGER")

    # Insert data into the Channel table
    
    channel = data[0][mongo_database_name]
    channel_insert_data = {
            'channel_id': channel.get('_channel_id'),
            'channel_name': channel.get('channel_name', 'N/A'),
            'channel_type': channel.get('channel_type','N/A'),
            'subscriber_count': channel.get('subscriber_count', 'N/A'),
            'view_count': channel.get('view_count', 'N/A'),
            'channel_description': channel.get('description', 'N/A'),
            'country': channel.get('country', 'N/A'),
            'video_count': channel.get('video_count', 'N/A')                        
        }
    insert_data("Channel", channel_insert_data)

    # Create the Playlist table
    create_table("Playlist", "playlist_id VARCHAR(255) PRIMARY KEY, channel_id VARCHAR(255) REFERENCES Channel(channel_id),  video_count INTEGER") ########playlist name to input

    # Insert data into the Playlist table
    playlist_data = channel["playlist_id"]
    playlist_insert_data = {
        "playlist_id": playlist_data,
        "channel_id": channel.get('_channel_id'),  # Replace with the actual channel ID
        "video_count": channel["video_count"]
    }
    insert_data("Playlist", playlist_insert_data)

    # # Create the Videos table
    # create_table("Videos", "video_id VARCHAR(255) PRIMARY KEY, playlist_id VARCHAR(255) REFERENCES Playlist(playlist_id), video_name VARCHAR(255), video_description TEXT, published_date DATETIME, view_count INTEGER, like_count INTEGER, favorite_count INTEGER, comment_count INTEGER, duration INTEGER, thumbnail VARCHAR(255), caption_status BOOLEAN")

    create_table("Videos", "video_id VARCHAR(255) PRIMARY KEY, playlist_id VARCHAR(255), video_name VARCHAR(255), video_description TEXT, published_date TIMESTAMP, view_count INTEGER, like_count INTEGER, favorite_count INTEGER, comment_count INTEGER, duration INTEGER, thumbnail VARCHAR(255), caption_status BOOLEAN, FOREIGN KEY (playlist_id) REFERENCES Playlist(playlist_id)")

    # Insert data into the Videos table
    for i in range(1, int(channel["video_count"]) + 1):
        video_data = channel[f"Video_Id_{i}"]
        published_dt = video_data["PublishedAt"]
        date, time = published_dt.split("Time")
        time = time[:-1]
        date_time = date + time
        duration_time = video_data["Duration"]
        hours, minutes, seconds = duration_time.split(":")
        duration_formatted = ((int(hours)*3600) + (int(minutes)*60) + int(seconds))
        video_insert_data = {
            "playlist_id": playlist_data,  # Replace with the actual playlist ID
            "video_id": video_data["Video_Id"],
            "video_name": video_data["Video_Name"],
            "video_description": video_data["Video_Description"],
            "published_date": date_time,
            "view_count": video_data["View_Count"],
            "like_count": video_data["Like_Count"],
            "favorite_count": video_data["Favorite_Count"],
            "comment_count": video_data["Comment_Count"],
            "duration": duration_formatted,
            "thumbnail": video_data["Thumbnail"],
            "caption_status": video_data["Caption_Status"]
        }
    
        insert_data("Videos", video_insert_data)

        # Create the Comments table
        create_table("Comments", "comment_id VARCHAR(255) PRIMARY KEY, video_id VARCHAR(255) REFERENCES Videos(video_id), text TEXT, author VARCHAR(255), published_at TIMESTAMP")

        # Insert data into the Comments table

        if isinstance(video_data["Comments"], dict):
            for i in range(1,(len(video_data["Comments"])+1)):
                comment_insert_data = {
                    "video_id": video_data["Video_Id"],
                    "comment_id": video_data["Comments"][f"Comment_id_{i}"]["Comment_Id"],
                    "text": video_data["Comments"][f"Comment_id_{i}"]["Comment_Text"],
                    "author": video_data["Comments"][f"Comment_id_{i}"]["Comment_Author"],
                    "published_at": video_data["Comments"][f"Comment_id_{i}"]["Comment_PublishedAt"]
                }
                insert_data("Comments", comment_insert_data)
        elif video_data["Comments"] == "Disabled":
            disabled_comment_id = video_data["Video_Id"]
            comment_insert_data = {
                    "video_id": video_data["Video_Id"],
                    "comment_id": f"Comments_Disabled_{disabled_comment_id}",
                    "text": "Disabled",
                    "author": "Disabled",
                    "published_at": None
                }
            insert_data("Comments", comment_insert_data)
    st.experimental_rerun()
# format for inserting data with SQL query
def insert_data(table_name, data):
    # Establish connection to the PostgreSQL database
    conn = psycopg2.connect(
        host='localhost',
        user ='postgres',
        password='rayz',
        port=5432,
        database='YoutubeAPI'
    )

    with conn.cursor() as cur:
        keys = data.keys()
        values = [data[key] for key in keys]
        placeholders = ",".join(["%s"] * len(keys))
        columns = ",".join(keys)
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cur.execute(query, values)
        conn.commit()
# format for inserting data with SQL query
def create_table(table_name, columns): 
     # Establish connection to the PostgreSQL database
    conn = psycopg2.connect(
        host='localhost', 
        user ='postgres',
        password='rayz',
        port=5432,
        database='YoutubeAPI'
    )

    with conn.cursor() as cur:
        cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")
        conn.commit()
# fetching all the channels and their videos for analysis
def get_video_names_and_channels():
    # Connect to the Postgres database
    try:
        cur, conn = sql_connection()
    except Error as e:
        right_col.write(f"Upload data into database: {e}")    
        
    # Create a cursor object
    cur = conn.cursor()
    
    # Execute the SQL query to join the three tables
    query = """
        SELECT 
            channel.channel_name, videos.video_name
        FROM 
            channel
        JOIN 
            playlist ON channel.channel_id = playlist.channel_id
        JOIN
            videos ON playlist.playlist_id = videos.playlist_id
        """
    cur.execute(query)
    # Fetch all the rows as a list of tuples
    rows = cur.fetchall()
    
    # Close the cursor and database connection
    cur.close()
    conn.close()
    
    # Return the data as a dictionary
    return rows
# Fetching data from postgres for channels with most videos
def get_channel_video_count():
    cur, conn = sql_connection()
    query = """
        SELECT
            channel_name, video_count
        FROM
            channel
    """
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return rows
# fetching the data from postgres for top 10 most viewed videos
def get_top_ten_videos():
    cur, conn = sql_connection()
    query = """
        SELECT 
            v.video_name, c.channel_name, v.view_count
        FROM 
            channel c
        JOIN 
            playlist p ON c.channel_id = p.channel_id
        JOIN 
            videos v ON p.playlist_id = v.playlist_id
        GROUP BY 
            v.video_name, c.channel_name, v.view_count
        ORDER BY 
            v.view_count DESC
        LIMIT 
            10;      
    """
    cur.execute(query)
    # Fetch all the rows as a list of tuples
    rows = cur.fetchall()
    
    # Close the cursor and database connection
    cur.close()
    conn.close()
    
    # Return the data as a dictionary
    return rows
## fetching the data from postgres to analyse videos and their comment count
def comment_count_for_all_videos():
    cur, conn = sql_connection()
    query = """
        SELECT
            v.video_name, COUNT(*) as comment_id
        FROM
            videos v
        JOIN
            comments c ON v.video_id = c.video_id
        GROUP BY
            v.video_name
        ORDER BY
            comment_id DESC;            
    """
    cur.execute(query)
    
    rows = cur.fetchall()    
    cur.close()
    conn.close()
    
    return rows
# fetching the data from postgres for videos with highest likes
def video_with_highest_likes():
    
    cur, conn = sql_connection()
    query = """
        SELECT
            c.channel_name, v.video_name, v.view_count
        FROM
            channel c
        JOIN
            playlist p ON c.channel_id = p.channel_id
        JOIN
            videos v ON p.playlist_id = v.playlist_id
        GROUP BY
            c.channel_name, v.video_name, v.view_count
        ORDER BY
            v.view_count DESC
        LIMIT
            20;
    """
    cur.execute(query)
    
    rows = cur.fetchall()    
    cur.close()
    conn.close()
    
    return rows
# fetching the data from postgres for total numnber of likes for videos
def total_likes_videos():
    
    cur, conn = sql_connection()
    query = """
        SELECT
            video_name, like_count
        FROM
            videos
    """
    cur.execute(query)
    
    rows = cur.fetchall()    
    cur.close()
    conn.close()
    
    return rows
# fetching the data from postgres for details on total view count on the channel
def channel_view_count():
    
    cur, conn = sql_connection()
    query = """
        SELECT
            channel_name, view_count
        FROM
            channel
    """
    cur.execute(query)
    
    rows = cur.fetchall()    
    cur.close()
    conn.close()
    
    return rows
# fetching the data from postgres to see the channels that have published videos in the the year 2022
def channels_in_year_2022():
    cur, conn = sql_connection()
    
    query = """
        SELECT DISTINCT
            c.channel_name
        FROM
            channel c
        JOIN
            playlist p ON c.channel_id = p.channel_id
        JOIN
            videos v ON p.playlist_id = v.playlist_id
        WHERE
            published_date
        BETWEEN
            '2022-01-01' AND '2022-12-31'
    """
    
    cur.execute(query)
    
    rows = cur.fetchall()    
    cur.close()
    conn.close()
    
    return rows
# fetching the data from postgres to analysie the average duration of all videos    
def avg_duration_of_all_videos():
    cur, conn = sql_connection()
    query = """
        SELECT
            c.channel_name, AVG(v.duration) as avg_duration
        FROM
            channel c
        JOIN
            playlist p ON c.channel_id = p.channel_id
        JOIN
            videos v ON p.playlist_id = v.playlist_id
        GROUP BY
            c.channel_name
        ORDER BY
            avg_duration ASC
    """
    cur.execute(query)
    
    rows = cur.fetchall() 
    rows = [(channel_name, float(avg_duration)) for channel_name, avg_duration in rows]   
    cur.close()
    conn.close()
    
    return rows
# fetching the data from postgres to check the videos with highest comment counts
def videos_with_highest_comments():
    cur, conn = sql_connection()
    query = """
        SELECT
            v.video_name, c.channel_name, COUNT(*) as comments_count
        FROM
            channel c
        JOIN
            playlist p ON c.channel_id = p.channel_id
        JOIN
            videos v ON p.playlist_id = v.playlist_id
        JOIN
            comments cs ON v.video_id = cs.video_id
        GROUP BY
            v.video_name, c.channel_name
        ORDER BY
            comments_count DESC
        Limit
            50  
    """
    cur.execute(query)
    
    rows = cur.fetchall()    
    cur.close()
    conn.close()
    
    return rows

# Create a Streamlit app to retrieve information about a YouTube channel, video, or playlist

# Creating tabs for Extraction and Analysis
extraction_tab, reports_tab = st.tabs(["Extraction", "Analysis"])
option = st.sidebar.selectbox("Select an option:", SIDEBAR_EXTRACT_OPTIONS)
# Creating sidebar radio buttons to switch between channel ID nad name to push data into Postgres
mongo_list_option = st.sidebar.radio(
    "Select channel using: ",
    ('Name','ID'),index = 0)

if mongo_list_option == 'Name':
    # fetch and display the MondoDB databases in a list
    upload_to_sql,selected_db_name= fetch_and_display_data(mongo_list_option)
    #upload_to_sql,
    if upload_to_sql:
        # fetch and format the MondoDB databases to upload in postgres
        query_data, mongo_database_name = upload_sql_procedure(selected_db_name,mongo_list_option)
        # Upload the data into postgres
        process_mongodb_data(query_data,mongo_database_name)
        
elif mongo_list_option == 'ID':
    # fetch and display the MondoDB databases in a list
    upload_to_sql,selected_db_name = fetch_and_display_data(mongo_list_option)
    #upload_to_sql,
    if upload_to_sql:
        # fetch and format the MondoDB databases to upload in postgres
        query_data,mongo_database_name= upload_sql_procedure(selected_db_name,mongo_list_option)
        # Upload the data into postgres
        process_mongodb_data(query_data,mongo_database_name)

with extraction_tab:
    st.title(":red[YouTube API Extraction]",)
    left_col, right_col = st.columns((10, 18))
    api_key = left_col.text_input("Enter your API key",type="password",) #
    if not api_key:
        left_col.write("Please enter your API key.")

    if option == "Channel ID":
        with extraction_tab:
            channel_video_id = left_col.text_input("Enter the Channel ID:", key="channel_video_id")
            leftsub_col1, leftsub_col2 = left_col.columns(2)
            if leftsub_col1.button("Get Data"):
                if channel_video_id:
                    if channel_video_id[-1] == ",":
                        channel_video_id = channel_video_id[:-1]  # Remove the last comma
                    channel_info = get_youtube_channel_info(api_key, channel_video_id)
                    if channel_info:
                        right_col.write("Channel Information:")
                        right_col.write("---")
                        for field in CHANNEL_FIELDS:
                            right_col.write(f"{field.replace('_', ' ').title()}: {channel_info.get(field, 'N/A')}")
                        right_col.write("---")
                if channel_video_id:
                    channel_info = get_channel_videos(api_key, channel_video_id)
                    if channel_info:
                        right_col.write("Video Detail Information:")
                        right_col.write("---")
                        for video_id, video_info in channel_info.items():
                            right_col.write(f"Video ID: {video_info.get('Video_Id', 'N/A')}")
                            right_col.write(f"Video Name: {video_info.get('Video_Name', 'N/A')}")
                            right_col.write(f"Tags: {', '.join(video_info.get('Tags', []))}")
                            right_col.write(f"Published At: {video_info.get('PublishedAt', 'N/A')}")
                            right_col.write(f"View Count: {video_info.get('View_Count', 'N/A')}")
                            right_col.write(f"Like Count: {video_info.get('Like_Count', 'N/A')}")
                            right_col.write(f"Favorite Count: {video_info.get('Favorite_Count', 'N/A')}")
                            comment_count = video_info.get('Comment_Count', 'N/A')
                            if comment_count == 'Disabled':
                                right_col.write("Comment Count: Disabled")
                            elif comment_count is None:
                                right_col.write("Comment Count: Disabled")
                            else:
                                right_col.write(f"Comment Count: {comment_count}")
                            right_col.write(f"Duration: {video_info.get('Duration', 'N/A')}")
                            right_col.write(f"Thumbnail: {video_info.get('Thumbnail', 'N/A')}")
                            right_col.write(f"Caption Status: {video_info.get('Caption_Status', 'N/A')}")
                            comments_dict = video_info.get('Comments', {})
                            if comments_dict == 'Disabled':
                                right_col.write("Comments: Disabled")
                                right_col.write("---")
                            elif comments_dict == 'N/A':
                                right_col.write("Comments: N/A")
                                right_col.write("---")
                            else:
                                right_col.write("Comments:")
                                right_col.write("---")
                                for comment_id, comment_info in comments_dict.items():
                                    sub_col1, sub_col2 = right_col.columns(2)
                                    sub_col1.write(comment_id + ":")
                                    sub_col2.write('\n')
                                    sub_col1, sub_col2 = right_col.columns(2)
                                    sub_col1.write("Comment ID:")
                                    sub_col2.write(comment_info.get('Comment_Id'))
                                    sub_col1, sub_col2 = right_col.columns(2)
                                    sub_col1.write("Comment Text:")
                                    sub_col2.write(comment_info.get('Comment_Text'))
                                    sub_col1, sub_col2 = right_col.columns(2)
                                    sub_col1.write("Comment Author:")
                                    sub_col2.write(comment_info.get('Comment_Author'))
                                    sub_col1, sub_col2 = right_col.columns(2)
                                    sub_col1.write("Comment Published At:")
                                    sub_col2.write(comment_info.get('Comment_PublishedAt'))
                                    right_col.write("---")
                    
        if leftsub_col2.button("Get Json"):
            if channel_video_id:
                if channel_video_id[-1] == ",":
                    channel_video_id = channel_video_id[:-1]  # Remove the last comma
                channel_info = get_youtube_channel_info(api_key, channel_video_id)
            if channel_video_id:
                video_info = get_channel_videos(api_key, channel_video_id)
                channel_info.update(video_info)
                channel_name = channel_info.get('channel_name', "N/A")
                channel_name = channel_name.replace(" ", "_")
                channels = {channel_name: channel_info}
                right_col.write(channels)

        left_col.write("Upload to MongoDB")
        leftsub_col1row2, leftsub_col2row2 = left_col.columns(2)
        if leftsub_col1row2.button("Upload"):
            mongo_validator = validate_json_in_mongodb()
            channel_info = get_youtube_channel_info(api_key, channel_video_id)
            video_info = get_channel_videos(api_key, channel_video_id)
            rightsub_col11, rightsub_col22 = right_col.columns([100,1])
            channel_info.update(video_info)
            channel_name = channel_info.get('channel_name',"N/A")
            channel_names = channel_name.replace(" ","_")
            if channel_name in mongo_validator:
                right_col.error("Channel present in database")
            else:
                latest_iteration = right_col.empty()
                rightsub_col1, rightsub_col2 = right_col.columns([100,1])
                rightsub_col1.bar = rightsub_col1.progress(0)
                for i in range(20):
                        latest_iteration.text(f'Uploading {i+1}')
                        rightsub_col1.bar.progress(i + 1)
                        time.sleep(0.05)
                channels = {channel_names: channel_info}
                mongo_insert = push_api_data_in_mongodb(channels)
                if mongo_insert == "Successful":
                    for i in range(20,100):
                        latest_iteration.text(f'Uploading {i+1}')
                        rightsub_col1.bar.progress(i + 1)
                        time.sleep(0.1)
                    rightsub_col1.write("Upload successful")
            
    if option == "Multiple Channel IDs":
        left_col.write("Enter multiple channel IDs separated by commas:")
        with left_col:
            channel_video_id = st.text_input("Channel IDs", key="channel_video_id")
            leftsub_col1, leftsub_col2 = left_col.columns(2)
            if leftsub_col1.button("Get Data"):
                with right_col:
                    if channel_video_id:
                        if channel_video_id[-1] == ",":
                            channel_video_id = channel_video_id[:-1]  # Remove the last comma
                        channel_video_id = [c.strip() for c in channel_video_id.split(",")]
                    st.write("Channel Information:")
                    st.write("---")
                    counter = 1
                    for channel_video_ids in channel_video_id:
                        channel_info = get_youtube_channel_info(api_key, channel_video_ids)
                        if channel_info:
                            st.write("Channel ",counter)
                            counter += 1
                            for field in CHANNEL_FIELDS:
                                st.write(f"{field.replace('_', ' ').title()}: {channel_info.get(field, 'N/A')}")
                            st.write("")
                        if channel_video_ids:
                            channel_info = get_channel_videos(api_key, channel_video_ids)
                            if channel_info:
                                st.write("Video Detail Information:")
                                st.write("---")
                                for video_id, video_info in channel_info.items():
                                    st.write(f"Video ID: {video_info.get('Video_Id', 'N/A')}")
                                    st.write(f"Video Name: {video_info.get('Video_Name', 'N/A')}")
                                    st.write(f"Tags: {', '.join(video_info.get('Tags', []))}")
                                    st.write(f"Published At: {video_info.get('PublishedAt', 'N/A')}")
                                    st.write(f"View Count: {video_info.get('View_Count', 'N/A')}")
                                    st.write(f"Like Count: {video_info.get('Like_Count', 'N/A')}")
                                    st.write(f"Favorite Count: {video_info.get('Favorite_Count', 'N/A')}")
                                    comment_count = video_info.get('Comment_Count', 'N/A')
                                    if comment_count == 'Disabled':
                                        st.write(f"Comment Count: Disabled")
                                    elif comment_count is None:
                                        st.write(f"Comment Count: N/A")
                                    else:
                                        st.write(f"Comment Count: {comment_count}")
                                    st.write(f"Duration: {video_info.get('Duration', 'N/A')}")
                                    st.write(f"Thumbnail: {video_info.get('Thumbnail', 'N/A')}")
                                    st.write(f"Caption Status: {video_info.get('Caption_Status', 'N/A')}")
                                    comments_dict = video_info.get('Comments', {})
                                    if comments_dict == 'Disabled':
                                        right_col.write("Comments: Disabled")
                                        right_col.write("---")
                                    elif comments_dict == "N/A":
                                        right_col.write("Comments: N/A")
                                        right_col.write("---")
                                    else:
                                        right_col.write("Comments:")
                                        right_col.write("---")
                                        for comment_id, comment_info in comments_dict.items():
                                            sub_col1, sub_col2 = right_col.columns(2)
                                            sub_col1.write(comment_id + ":")
                                            sub_col2.write('\n')
                                            sub_col1, sub_col2 = right_col.columns(2)
                                            sub_col1.write("Comment ID:")
                                            sub_col2.write(comment_info.get('Comment_Id'))
                                            sub_col1, sub_col2 = right_col.columns(2)
                                            sub_col1.write("Comment Text:")
                                            sub_col2.write(comment_info.get('Comment_Text'))
                                            sub_col1, sub_col2 = right_col.columns(2)
                                            sub_col1.write("Comment Author:")
                                            sub_col2.write(comment_info.get('Comment_Author'))
                                            sub_col1, sub_col2 = right_col.columns(2)
                                            sub_col1.write("Comment Published At:")
                                            sub_col2.write(comment_info.get('Comment_PublishedAt'))
                                            right_col.write("---")

            if leftsub_col2.button("Get Json"):
                rightsub_col1, rightsub_col2 = right_col.columns([100,1])
                with rightsub_col2:
                    if channel_video_id:
                        if channel_video_id[-1] == ",":
                            channel_video_id = channel_video_id[:-1]  # Remove the last comma
                        channel_video_id = [c.strip() for c in channel_video_id.split(",")]
                        for channel_video_ids in channel_video_id:
                            channel_info = get_youtube_channel_info(api_key, channel_video_ids)
                            if channel_video_ids:
                                channel_name = channel_info.get('channel_name',"N/A")
                                channel_name = channel_name.replace(" ","_")
                                channel_dict = {channel_name:{}}    
                            if channel_video_ids:
                                video_info = get_channel_videos(api_key, channel_video_ids)
                                channel_info.update(video_info)
                                channel_dict[channel_name].update(channel_info)
                                rightsub_col1.write(channel_dict)

            left_col.write("Upload to MongoDB")
            leftsub_col1row2, leftsub_col2row2 = left_col.columns(2)
            if leftsub_col1row2.button("Upload"):
                latest_iteration = right_col.empty()
                rightsub_col1, rightsub_col2 = right_col.columns([100,1])
                rightsub_col1.bar = rightsub_col1.progress(0)
                channel_names = []
                if channel_video_id:
                    if channel_video_id[-1] == ",":
                        channel_video_id = channel_video_id[:-1]  # Remove the last comma
                    channel_video_id = [c.strip() for c in channel_video_id.split(",")]
                    for channel_video_ids in channel_video_id:
                        channel_dict = {}
                        channel_info = get_youtube_channel_info(api_key, channel_video_ids)
                        if channel_video_ids:
                            video_info = get_channel_videos(api_key, channel_video_ids)
                            channel_info.update(video_info)
                            channel_name = channel_info.get('channel_name',"N/A")
                            channel_name = channel_name.replace(" ","_")
                            channel_dict = {channel_name:channel_info}   
                            mongo_insert = push_api_data_in_mongodb(channel_dict)
                    if mongo_insert == "Successful":
                        for i in range(100):
                            latest_iteration.text(f'Uploading {i+1}')
                            rightsub_col1.bar.progress(i + 1)
                            time.sleep(0.1)
                        rightsub_col1.write("Upload successful")

# Reports Tab
with reports_tab:
    st.title(":blue[Analysis]",)
    reports = st.selectbox("Select an option:", REPORTS_OPTION)
    # Creating two tabs 1. Tabular for tabular data representation 2. Chart for analysis of the data
    tabular, charts = st.tabs(["Tabular representation", "Charts"])
    
    if reports == "1. What are the names of all the videos and their corresponding channels?":
        try:
            # Call the function to get the video names and channels
            video_data = get_video_names_and_channels()
            # Creating a dataframe using pandas
            df_video_data = pd.DataFrame(video_data, columns=['Channel Name', 'Video Title'])
            df_video_data = df_video_data.reset_index(drop=True) #reseting index
            df_video_data.index += 1
        
            with tabular: 
                # Tabular representation
                st.dataframe(df_video_data,use_container_width = True)
            with charts:
                # No charts can be created for this table
                st.error("Charts not available for this data")
        except Exception as e:
            tabular.write(f"Upload data into database")            
            
    elif reports == "2. Which channels have the most number of videos, and how many videos do they have?":
        try:    
            # Call the function to get the channels video count
            channel_count_data = get_channel_video_count()
            # Creating a dataframe using pandas    
            df_channel_count_data = pd.DataFrame(channel_count_data, columns=['Channel Name', 'Video Count'])
            df_channel_count_data.index += 1
            #highlighting the max value
            styled_df = df_channel_count_data.style.highlight_max(subset=["Video Count"],color = '#57DF2F')
            # styled_df = styled_df.reset_index(drop=True) #reseting index
            # creating the framework for charts using plotly and giving the title
            fig = px.bar(
                df_channel_count_data, 
                x="Channel Name", 
                y="Video Count", 
                color="Channel Name", 
                barmode="stack",
                title = "Top 10 Most Viewed Videos And Channels",
                height = 500,
                color_continuous_scale = "jet"
            )
            fig.update_layout(title='Channel with most number of videos')
            with tabular:
                # Tabular representation
                st.subheader('Channel with most number of videos')
                st.dataframe(styled_df, use_container_width=True)
            with charts:
                # Displaying the plotly chart
                st.plotly_chart(fig, use_container_width = True)            
        except Exception as e:
            tabular.write(f"Upload data into database")       
             
    elif reports == "3. What are the top 10 most viewed videos and their respective channels?":
        try:
            # Call the function to get the video names and channels
            top_ten_videos = get_top_ten_videos()
                        
            df_top_ten_videos = pd.DataFrame(top_ten_videos, columns=['Video Title','Channel Name','View Count'])
            video_channel_counts = df_top_ten_videos.groupby([ "Channel Name","Video Title", "View Count"]).size().reset_index(name="count")
            df_top_ten_videos.index += 1

            # Create a horizontal stacked bar chart using Plotly Express
            fig = px.bar(
                video_channel_counts, 
                x="View Count", 
                y="Channel Name", 
                color="Video Title", 
                orientation="h", 
                barmode="stack",
                title = "Top 10 Most Viewed Videos And Channels",
                height = 500,
                color_continuous_scale = "jet",
                hover_data=["View Count"]
            )
            
            fig.update_layout(
                legend=dict(
                    orientation="h", 
                    yanchor="top", 
                    y=-0.14, 
                    xanchor="center", 
                    x=0.35
                    ),
                title='Top 10 most viewed videos',
            )
            
            with tabular: 
                # Tabular representation
                st.subheader("Top 10 most viewed videos")
                st.dataframe(df_top_ten_videos,use_container_width = True)
            with charts:
                # Display the chart in Streamlit
                st.plotly_chart(fig, use_container_width=True)
                # st.bar_chart(df_top_ten_videos, y = 'Channel Name', x = 'Video Title', height = 500)
        except Exception as e:
            tabular.write(f"Upload data into database")
            
    elif reports == "4. How many comments were made on each video, and what are their corresponding video names?":
        try:    
            # Call the function to get the video names and channels
            comment_count = comment_count_for_all_videos()
            df_comment_count = pd.DataFrame(comment_count, columns=['Video Title','Comment Count'])
            df_comment_count.index += 1
            # Create a bar chart using Plotly Express
            fig = px.bar(
                df_comment_count, 
                x='Video Title', 
                y='Comment Count', 
                height=1000,  
                color = 'Comment Count', 
                color_continuous_scale = 'jet'
            )
            fig.update_layout(title='Total comments on each video', yaxis={'range': [0, 110]})
            with tabular:
                # Tabular representation
                st.subheader('Total comments on each video')
                st.dataframe(df_comment_count,use_container_width = True)
            with charts:
                # Create a bar plot using Plotly
                st.plotly_chart(fig, use_container_width = True)
        except Exception as e:
            tabular.write(f"Upload data into database")
            
    elif reports == "5. Which videos have the highest number of likes, and what are their corresponding channel names?":
        try:
            # Call the function to get the video names and channels
            like_count = video_with_highest_likes()
            
            df_like_count = pd.DataFrame(like_count, columns=['Channel Name','Video Title','View Count'])
            df_like_count.index += 1
            # Create a bar chart using Plotly Express
            fig = px.bar(
                df_like_count, 
                x = 'Video Title', 
                y = 'View Count', 
                height = 700,
                color = 'View Count',
                color_continuous_scale = 'bluered'
            )
            fig.update_layout(title='Videos with Highest Number of Likes')
            with tabular:
                # Tabular representation
                st.subheader('Videos with Highest Number of Likes')            
                st.dataframe(df_like_count, use_container_width = True)
            with charts:
                # Create a bar plot using Plotly
                st.plotly_chart(fig, use_container_width = True)
        except Exception as e:
            tabular.write(f"Upload data into database")
            
    elif reports =="6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?":
        try:    
            # Call the function to get the video names and channels
            all_like_count = total_likes_videos()
            
            df_all_like_count = pd.DataFrame(all_like_count, columns = ['Video Name', 'Like Count'])
            df_all_like_count.index += 1
            
            # Create a bar chart using Plotly Express
            fig = px.bar(
                df_all_like_count, 
                x='Video Name', 
                y='Like Count', 
                height=900,  
                color = 'Like Count', 
                color_continuous_scale = 'jet'
            )
            fig.update_layout(xaxis={'range': [0, 120]})
            fig.update_layout(title='Total number of Likes for each video')
            with tabular:
                # Tabular representation
                # Highlighting the max and min value in the table
                styled_df = df_all_like_count.style \
                    .highlight_max(subset=["Like Count"], color='#57DF2F') \
                    .highlight_min(subset=["Like Count"], color='#FF5733')
                st.subheader("Total number of Likes for each video")
                st.dataframe(styled_df, use_container_width = True, height = 500)
            with charts:
                # Create a bar plot using Plotly            
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            tabular.write(f"Upload data into database")
            
    elif reports =="7. What is the total number of views for each channel, and what are their corresponding channel names?":
        try:
            # Call the function to get the video names and channels and view count
            channel_views = channel_view_count()
            
            df_channel_views = pd.DataFrame(channel_views, columns = ['Channel Name','Total View Count'])
            df_channel_views = df_channel_views.sort_values(by='Total View Count',ascending=False) #soriting in ascending order
            df_channel_views = df_channel_views.reset_index(drop=True) #reseting index
            df_channel_views.index += 1
            # Create a bar chart using Plotly Express
            fig = px.bar(
                df_channel_views, 
                x='Channel Name', 
                y='Total View Count',
                height=500,
                color = "Total View Count", 
                color_continuous_scale = 'bluered'    
            )
            fig.update_layout(title='Total number of views for each channel') 
            with tabular:
                # Tabular representation
                st.subheader("Total number of views for each channel")
                st.dataframe(df_channel_views, use_container_width = True)
            with charts:
                # Create a bar plot using Plotly 
                st.plotly_chart(fig ,use_container_width = True)
        except Exception as e:
            tabular.write(f"Upload data into database")
            
    elif reports == "8. What are the names of all the channels that have published videos in the year 2022?":
        try:
            channel_in_twenty_two = channels_in_year_2022() 
            
            df_channel_in_twenty_two = pd.DataFrame(channel_in_twenty_two, columns = ['Channel Name'])
            df_channel_in_twenty_two.index += 1
            
            with tabular:
                # Tabular representation
                st.subheader("Channels with videos published in 2022")
                st.dataframe(df_channel_in_twenty_two, use_container_width = True)
            with charts:
                # No charts for this table
                st.error("Charts not available for this data")
        except Exception as e:
            tabular.write(f"Upload data into database")
    
    elif reports == "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?":
        try:
            # Call the function to get the video names and their average duration
            channel_avg_duration = avg_duration_of_all_videos()
            
            df_channel_avg_duration = pd.DataFrame(channel_avg_duration, columns = ['Channel Name', 'Average Duration'])
            #rounding off the values to 2 decimal values
            df_channel_avg_duration['Average Duration'] = df_channel_avg_duration['Average Duration'].round(2)
            
            df_channel_avg_duration = df_channel_avg_duration.sort_values(by='Average Duration',ascending=False)
            df_channel_avg_duration = df_channel_avg_duration.reset_index(drop=True) #reseting index
            df_channel_avg_duration.index += 1
            # Create a horizontal stacked bar chart using Plotly Express
            fig = px.bar(
                df_channel_avg_duration, 
                x = 'Average Duration', 
                y = 'Channel Name',
                orientation='h', 
                height = 500,
                color = "Average Duration", 
                color_continuous_scale = "jet"
            )
            
            fig.update_layout(title='Average Video Duration by Channel') 
            with tabular:
                # Tabular representation
                st.subheader("Average Video Duration by Channel")
                st.dataframe(df_channel_avg_duration, use_container_width = True)
            with charts:
                # Create a bar plot using Plotly 
                st.plotly_chart(fig, use_container_width = True)
        except Exception as e:
            tabular.write(f"Upload data into database")
    
    elif reports == "10.Which videos have the highest number of comments, and what are their corresponding channel names?":
        try:
            # Call the function to get the video names with highest video comments
            highesh_video_comments = videos_with_highest_comments()
            
            df_highesh_video_comments =pd.DataFrame(
                highesh_video_comments, 
                columns=['Video Title', 'Channel Name', 'Comment Count'] 
            )
            df_highesh_video_comments.index +=1
            px_highesh_video_comments = df_highesh_video_comments.groupby([ "Channel Name","Video Title",'Comment Count']).size().reset_index(name="count")
            # Create a bar chart using Plotly Express
            fig = px.bar(
                px_highesh_video_comments, 
                x='Video Title', 
                y='Comment Count',
                barmode = 'group',
                height=1000, 
                color = "Comment Count", 
                color_continuous_scale = "jet"
            )
            fig.update_layout(
                legend=dict(
                    orientation="h", 
                    yanchor="top", 
                    y=-0.2, 
                    xanchor="center", 
                    x=0.5
                    ),
                title='Videos With The Most Comments'
            )
            fig.update_yaxes(range=[0, 110])
            with tabular:
                # Tabular representation
                st.subheader("Videos With The Most Comments")
                st.dataframe(df_highesh_video_comments, use_container_width = True)
            with charts:
                # Create a bar plot using Plotly         
                st.plotly_chart(fig,use_container_width = True)
        except Exception as e:
            tabular.write(f"Upload data into database")
                
                
            
            
            
            
            
            
