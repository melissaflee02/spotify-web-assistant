import requests
import os, sys
import spotipy
import urllib.request
import shutil
import re

from django.shortcuts import render
from django.http import HttpResponse
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from pytube import YouTube
from moviepy.editor import *

from .models import Greeting

os.environ['SPOTIPY_CLIENT_ID'] = '15d75cfdc63d46ae8f50e345402e6e73'
os.environ['SPOTIPY_CLIENT_SECRET'] = '2fc7c1d2f00a40448adc5af6f7105107'
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:5000/callback'

# Create your views here.
def index(request):
  with open('hello/templates/index_template.txt', 'r') as file:
    index_template = file.read()

  writeToIndex(index_template)

  return render(request,'index.html')

def showResults(request):
  artist_uri = request.GET.get('artistURI')
  spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

  try:
    results_albums = spotify.artist_albums(artist_uri)

    # clear content of directory album_covers
    shutil.rmtree('hello/static/album_covers')
    os.makedirs('hello/static/album_covers')

    # clear content of directory track_sample_audios
    shutil.rmtree('hello/static/track_sample_audios')
    os.makedirs('hello/static/track_sample_audios')

    # clear content of directory track_audios
    shutil.rmtree('hello/static/track_audios')
    os.makedirs('hello/static/track_audios')

    new_content = ''
    count = 1
    album_set = set()
    for key in results_albums['items']:
      album_name = str(key['name'])
      artist_name = str(key['artists'][0]['name'])

      # check if album has already been recorded
      if album_name in album_set:
        continue
      else:
        album_set.add(album_name)

      # retrieve album cover
      urllib.request.urlretrieve(key['images'][0]['url'], 'hello/static/album_covers/track' + str(count) + '.jpg')

      new_content += '<table><th valign=\"top\" style=\"width:40%\"><div class=\"albumsDiv\"><br>Album Name: ' + album_name + '</div><br><br>'
      new_content += '<img src=\"static/album_covers/track' + str(count) + '.jpg\" alt=\"' + str(key['name']) + '\"</th>'
      new_content += '<th><div class=\"tracksDiv\">'
      results_tracks = spotify.album_tracks(key['uri'])
      for track in results_tracks['items']:
        new_content += str(track['name'])

        # retrieve track audio
        preview_url = str(track['preview_url'])
        if (preview_url != 'None'):
          urllib.request.urlretrieve(preview_url, 'hello/static/track_sample_audios/track' + str(count) + '.mp3')
          new_content += '&emsp;<audio controls src=\"static/track_sample_audios/track' + str(count) + '.mp3\">Your browser does not support the <code>audio</code>element.</audio>'
      
        # clean search query for track
        artist_name_cleaned = cleanToken(artist_name)
        track_name_cleaned = cleanToken(str(track['name']))

        track_search_query = artist_name_cleaned + '+' + track_name_cleaned + '+audio'
        new_content += '<form action=\"downloadTrack\" method=\"GET\"><input type=\"hidden\" name=\"track_name\" value=\"' + track_search_query + '\"/><button onclick=\"displayCompletion()\">Download Song</button></form><br>'
        count += 1

      new_content += '</div></th></table><br><br><br>'
  except Exception as e:
    new_content = '<p style=\"color:red\">Invalid Spotify URI, please try again.<br>' + str(e) + '</p>'

  # add new_content to index.html
  with open('hello/templates/index_template.txt', 'r+') as file:
    new_content = file.read().replace('<!--TEXT HERE-->', new_content)
  
  # rewrite index.html
  writeToIndex(new_content)

  return render(request,'index.html')

def downloadTrack(request):
  track_name = request.GET.get('track_name')

  html = urllib.request.urlopen('https://www.youtube.com/results?search_query=' + track_name)
  video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())
  video_url = 'https://www.youtube.com/watch?v=' + video_ids[0]

  # download a mp3 file from youtube
  y = YouTube(video_url)
  t = y.streams.filter(only_audio=True).all()
  SAVE_PATH = 'hello/static/track_audios/'
  t[0].download(output_path=SAVE_PATH)

  new_content = ''
  # create audio player for downloaded track
  dirs = os.listdir('hello/static/track_audios/')
  for file in dirs:
    with open('hello/templates/index.html') as f:
      if file not in f.read():
        new_content = '<br><b style=\"font-size:1.15vw\">' + file + '</b>&emsp;<audio controls src=\"static/track_audios/' + file + '\">Your browser does not support the <code>audio</code>element.</audio><br><!--NEXT SONG-->'

  # add new_content to index.html
  with open('hello/templates/index.html', 'r+') as file:
    new_content = file.read().replace('<!--NEXT SONG-->', new_content)

  # rewrite index.html
  writeToIndex(new_content)

  return render(request,'index.html')

def cleanToken(input):
  cleaned_token = input
  re.sub(r'\W+', '', cleaned_token)
  return cleaned_token.replace(' ', '+')

def writeToIndex(new_content):
  response = open('hello/templates/index.html', 'w')
  response.write(new_content)
  response.close()

def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})
