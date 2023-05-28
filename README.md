# YouTube Data Scraper 


- [Introduction](#Introduction)
- [Features](#features)
- [Requirements](#Requirements)
- [Installation](#installation)
- [App-Flow](#App-Flow)
- [Screenshots](#screenshots)
- [License](#license)

# Introduction
The YouTube Data Scraper is a Python application that allows you to fetch information from YouTube channels, videos, and playlists using the YouTube Data API. With this tool, you can easily gather valuable data from YouTube and perform various data analysis tasks. Whether you need to retrieve channel information, fetch video details, analyze comments, or generate reports, the YouTube Data Scraper has got you covered. 

# Features 

**The** YouTube Data Scraper offers a range of features to help you extract and analyze data from YouTube. Some of the key features include: 

### `Get Channel Information: `
You can fetch detailed information about a specific YouTube channel using its channel ID. The scraper retrieves the channel name, subscriber count, view count, description, country, video count, playlist ID, channel type, and channel status. This information can be useful for analyzing the popularity and engagement of a channel. Along with the channel details we can fetch the following sub-details in one go. 

### `Get Video Information:`
Retrieve comprehensive details about a specific video. The scraper fetches the video title, description, tags, published date, view count, like count, favourite count, comment count, and thumbnails. This information can be used to analyze video performance, identify trends, and understand audience engagement. 

### `Get Playlist Information: `
The YouTube Data Scraper lets you fetch playlist information. You can retrieve details such as the playlist title, description, published date, and item count. This feature is particularly useful when you want to analyze playlists and their contents. 

### `Get Comments: `
You can also retrieve comments for a specific video. This feature allows you to gather user feedback, sentiment analysis, and engage in deeper audience insights. 

### `Multiple Channel and Video Data Retrieval: `
In addition to fetching data for individual channels and videos, the YouTube Data Scraper also supports bulk data retrieval. By selecting the "Multiple Channel IDs" option, you can enter multiple YouTube channel IDs (separated by commas) and fetch information for all the specified channels at once. Similarly, you can provide multiple video IDs to retrieve details for multiple videos simultaneously. This feature is extremely helpful when dealing with large datasets and conducting comparative analyses. 

### `Data Analysis and Reports:` 
The YouTube Data Scraper provides various data analysis capabilities to help you make sense of the fetched data. Using the interactive reports feature, you can generate insightful visualizations and reports based on the retrieved information. The application utilizes the Plotly library for creating interactive and dynamic charts, making it easy to explore the data and draw meaningful conclusions. 

## Requirements 

To run the YouTube Data Scraper, you need to have the following requirements installed: 

> `Python 3.11`: The application is built using Python and requires a compatible version (preferably Python 3.11) to run smoothly. 

> `Streamlit`: Streamlit is the framework used to create the interactive web application. Make sure you have Streamlit installed. 

> `google-api-python-client`: This library provides the necessary tools for interacting with the YouTube Data API. Install it to enable communication with the API. 

> `pymongo`: If you wish to store the fetched data in a MongoDB database, install the pymongo library to establish the connection. 

> `psycopg2`: Similarly, if you want to perform SQL queries on the fetched data using a PostgreSQL database, install the psycopg2 library. 

> `plotly`: This library is used for data visualization and generating interactive charts and reports. 

> `pandas`: Install the pandas library for data manipulation and analysis tasks. 

 

You can easily install the required dependencies by running the following command: 

`pip install -r requirements.txt  `

## Installation 

Follow these steps to set up the YouTube Data Scraper on your local machine: 

`Clone the repository: `

git clone https://github.com/Rohit-Tambavekar/Youtube-Data-API-Scrapping
 

### Navigate to the project directory: 

`cd youtube-data-scraper ` 
 

## Install the required dependencies:

 `pip install -r requirements.txt `
 

### Obtain YouTube API credentials: 

> Visit the `Google Cloud Console`. 

> Create a new project or select an existing project. 

> Enable the `YouTube Data API v3` for your project. 

> Create API credentials for youtube API v3. 

### Run the application: 

`streamlit run YoutubeAPI.py ` 
 
The application will start running and open in your default web browser. 

## App-Flow 

> Once the application is running, you will see a web interface with various options. 

> Choose the desired operation: "Get Channel Information," "Get Video Information," "Get Playlist Information," and "Get Comments" in one click. 

> Enter the required information, such as `channel ID`, `channel IDs`, and `YouTube API`, depending on the selected operation. 

> Click the `"Get Data"` button to fetch the data from YouTube and display it in a readable format.

> Click the `"Get Json"` button to fetch the data from YouTube and display it in a JSON format.

> Click the `"Upload"` button to to upload the data fetched from the youtube to MongoDB

> The uploaded data will then be displayed on the sidebar dropdown list.

> Select the Youtube channel name from the dropdown list and click `"Upload to SQL"` to migrate the selected Database from MongoDB to Postgres

> The Migrated data will be displayed on the Analysis Tab interface, and you can explore it further using the provided interactive Analysis. 

> If you have MongoDB or PostgreSQL set up, you can configure the database connection by providing the necessary details in the respective fields. 

> To exit the application, press `CTRL+C` in the terminal or command prompt. 


## Additional Information 

The YouTube Data Scraper utilizes the YouTube Data API to retrieve information from YouTube. Make sure you comply with the API's terms of service and usage limits. 

If you encounter any issues or have any questions, please refer to the project's documentation or open an issue on the GitHub repository. 

## License 

The YouTube Data Scraper is released under the MIT License. Feel free to modify and use the code according to the terms of the license. 

## Acknowledgments 

The YouTube Data Scraper was developed by Rohit Tambavekar.

## Conclusion 

The YouTube Data Scraper provides a convenient way to fetch and analyze data from YouTube channels, videos, and playlists. With its various features and data analysis capabilities, you can gain insights into channel performance, video engagement, and audience feedback. Whether you're a data analyst, researcher, or marketer, the YouTube Data Scraper can help you extract valuable insights and inform your decision-making processes. 

 
