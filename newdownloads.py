#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import string
import re
import textwrap
import time
import shutil
import filecmp
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings
from itertools import chain
from http.client import HTTPConnection  # py3
import logging

'''
This script is to sort and move downloaded Series episodes and Movies to plex library on NAS
'''
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Predefined Params
qbitquery = 'https://<fqdn>:8080/api/v2/torrents/info'
qbitcommand = 'https://<fqdn>:8080/api/v2/torrents/delete'
mountpoint = '/mnt/nas/'
showname = 'Download'
test = []
downloaddir = []
newstuff = []
videofiles = []

# print statements from `http.client.HTTPConnection` to console/stdout
HTTPConnection.debuglevel = 1

# Check for test parameter
if len(sys.argv) == 2:
  if sys.argv[1] == 'test':
    print ("Running testrun")
    test = 'test'

# find all dirs with name under /mnt/nas and put them in list
def find_dirs (showname, *args):
  downloaddir = []
  latest_dir = []
  for dirs in os.walk(mountpoint):
    dirName = str.split(dirs[0], '/')[-1]
    if (dirName == (showname) and 'Recycle' not in dirs[0]):
      downloaddir.append(dirs[0])
  if len(downloaddir) == 0:
    print("creating dir")
    downloaddir = create_dir(showname, args[0], args[1], args[2])
  else:
    latest_dir = max(downloaddir, key=os.path.getmtime)
  if test == 'test':
    print (("showdirs: "), (downloaddir))
    if len(latest_dir) != 0:
      print (("latestdir: "), (latest_dir))
  if len(latest_dir) != 0:
    if showname != 'Download':
      if not os.path.exists(latest_dir + '/' + 'Season ' + str(args[1])):
        print("creating season dir")
        downloaddir = create_dir(showname, args[0], args[1], args[2])
        return downloaddir
    return latest_dir
  else:
    return downloaddir


# find all new dirs and files in downloaddir and put in list
def find_new_items(downloaddir):
  if type(downloaddir) is list:
    for newitems in chain.from_iterable(os.listdir(path) for path in downloaddir):
      newstuff.append(newitems)
  if type(downloaddir) is str:
    for newitems in os.listdir(downloaddir):
      newstuff.append(newitems)
  if test == 'test':
    print (("new items list: "), (newstuff))
  return newstuff

# check if new things exist or exit
def newstuff_exist (newstuff):
  if len(newstuff) == 0:
    print ("no new stuff, exiting")
    exit(1)
  else:
    print (('####################'),(time.strftime("%H:%M:%S %d/%m/%Y")),('####################'),('\n'),("these are the new items:"))
    for stuff in newstuff:
      print (textwrap.indent(stuff, '>     '))
    print ('\n')
  return

# Evaluate what type of media this is
def eval_media (new):
  if len(re.findall(r"[s,S][0-9][0-9][e,E][0-9][0-9]", new)) == 1:
    media = []
    media.append("Episode")
    media.append(re.findall(r"[s,S][0-9][0-9]", new))
    return media
  elif len(re.findall(r"[s,S][0-9][0-9]", new)) == 1:
    media = []
    media.append("Season")
    media.append(re.findall(r"[s,S][0-9][0-9]", new))
    return media
  elif len(re.findall(r"((?:19|20)\d\d)", new)) == 1:
    media = []
    media.append("Movie")
    media.append(re.findall(r"((?:19|20)\d\d)", new))
    return media
  else:
    media = []
    media.append("unknown")
    return media

# Extract and wash season numbers
def wash_season (media):
  if 'Episode' in media or 'Season' in media:
    season = (int(re.sub('[sS0\'\[\]]', '', (str(media[1])))))
    if season >= 10:
      if test == 'test':
        print (("Season is dubbel digit: "), (season))
      return season
    else:
      if test == 'test':
        print (("Season is single digit: "), (season))
      return season
  if 'Movie' in media:
    season = (int(re.sub('[\'\[\]]', '', (str(media[1])))))
    if test == 'test':
      print (("Year is: "), (season))
    return season

# Extract and wash show name
def wash_show_name (new, media):
  if 'Episode' in media or 'Season' in media:
    showsplit = re.split('\.[s,S][0-9][0-9]', new )[-0]
    showname = re.sub('\.', ' ', (showsplit))
    if test == 'test':
                        print (("Showname is: "), (showname))
    return showname
  if 'Movie' in media:
    showsplit = re.split('\.((?:19|20)\d\d)', new )[-0]
    showname = re.sub('\.', ' ', (showsplit))
    if test == 'test':
      print (("Showname is: "), (showname))
    return showname

# Create dir if nonexistent
def create_dir (showname, createdir, season, media):
  if 'Episode' in media or 'Season' in media:
    if not os.path.exists(createdir + '/Series/' + showname):
      print (("No dir found creating dir: "),(createdir + '/Series/' + showname))
      os.makedirs(createdir + '/Series/' + showname, mode=0o777)
    if not os.path.exists(createdir + '/Series/' + showname + '/' + 'Season ' + str(season)):
      print (("No season dir found creating dir: "),(createdir + '/Series/' + showname + '/' + 'Season ' + str(season)))
      os.makedirs(createdir + '/Series/' + showname + '/' + 'Season ' + str(season), mode=0o777)
    seasondir = (createdir + '/Series/' + showname)
    return seasondir

  if 'Movie' in media:
    print (("Creating dir: "),(createdir + '/Movies/' + showname + ' (' + str(season) + ')'))
    moviedir = (createdir + '/Movies/' + showname + ' (' + str(season) + ')')
    os.makedirs(createdir + '/Movies/' + showname + ' (' + str(season) + ')', mode=0o777)
    return moviedir


def find_video (downloaddir, new):
  videofiles = []
  for root, dirs, files in os.walk(str(downloaddir).strip('\'[]\'') + '/' + str(new)):
    for newfile in files:
      if newfile.endswith('.mp4') or newfile.endswith('.mkv'):
        vfile = os.path.join(root, newfile)
        videofiles.append(vfile)
        if test == 'test':
          print (("Videofile is: "), (vfile))
    if test == 'test':
      print (("videofiles is: "), (videofiles))
  return videofiles

def find_subtitle (downloaddir, new):
  subtitles = []
  for root, dirs, files in os.walk(str(downloaddir).strip('\'[]\'') + '/' + str(new)):
    for newfile in files:
      if newfile.endswith('.srt'):
        sfile = os.path.join(root, newfile)
        subtitles.append(sfile)
        if test == 'test':
          print (("Subtitle is: "), (sfile))
  return subtitles

def move_files (videofiles, subtitles, showdirs, media, season):
  for nfile in videofiles:
    if nfile.endswith('.mp4') or nfile.endswith('.mkv'):
      vsuccess = []
      mdir = str()
      vpath, vfile = os.path.split(nfile)
      if 'Episode' in media or 'Season' in media:
        mdir = (str(showdirs).strip('\'[]\'') + '/Season ' + str(season) + '/')
      if 'Movie' in media:
        mdir = (str(showdirs).strip('\'[]\'') + '/')
      print (("File to be moved: "),(vfile))
      print (("Dir to move to: "),(mdir))
      shutil.copy(nfile, mdir)
      if filecmp.cmp(nfile, (mdir + vfile)):
        vsuccess.append(0)
      else:
        vsuccess.append(1)
    for sfile in subtitles:
      if sfile.endswith('.srt'):
        subsuccess = []
        if 'Episode' in media or 'Season' in media:
          mdir = (str(showdirs).strip('\'[]\'') + '/Season ' + str(season) + '/')
        if 'Movie' in media:
          mdir = (str(showdirs).strip('\'[]\'') + '/')
        noext = (os.path.splitext(vfile)[0])
        subpath, subfile = os.path.split(sfile)
        slan = (os.path.splitext(subfile)[0])
        if vpath == subpath:
          print (("Subtitle: "),(subfile))
          shutil.copy(sfile, (mdir + noext + '.' + slan + '.srt' ))
          if filecmp.cmp(sfile, (mdir + noext + '.' + slan + '.srt' )):
            subsuccess.append(0)
          else:
            subsuccess.append(1)
        elif noext in subpath:
          print (("Subtitle: "),(subfile))
          shutil.copy(sfile, (mdir + noext + '.' + slan + '.srt' ))
          if filecmp.cmp(sfile, (mdir + noext + '.' + slan + '.srt' )):
            subsuccess.append(0)
          else:
            subsuccess.append(1)
  if 1 in (vsuccess or subsuccess):
    print ("Failed to move files....exiting")
    exit(1)
  elif 0 in vsuccess:
    return vsuccess

def remove_torrent ( msuccess, new ):
  infoparams = dict(
    filter='completed',
    sort='name'
  )
  with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=InsecureRequestWarning)
    resp = requests.get(url=(qbitquery), params=infoparams, verify=False)  # InsecureRequestWarning suppressed for this request
  for attrs in resp.json():
    if attrs['name'] == new:
      torrenthash = attrs['hash']
      if test == 'test':
        print(torrenthash)
      deletedata = dict(
        hashes=torrenthash,
        deleteFiles='true'
      )
      with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=InsecureRequestWarning)
        delete = requests.get(url=(qbitcommand), params=deletedata, verify=False)  # InsecureRequestWarning suppressed for this requestbreak

# MAIN SCOPE
downloaddir = find_dirs( showname )
createpath = (os.path.split(str(downloaddir))[0])
newstuff = find_new_items( downloaddir )
newstuff_exist (newstuff) #Check for new stuff
for new in newstuff:  #For every new item find Season or year
  media = eval_media( new )
  if "Episode" in media:
    print (('########################################'),('\n')*2, ("¤¤¤¤ This is an episode:     "),(new))
    season = wash_season( media )
    showname = wash_show_name( new, media )
    showdirs = find_dirs( showname, createpath, season, media )
    videofiles = find_video( downloaddir, new )
    subtitles = find_subtitle( downloaddir, new )
    msuccess = move_files( videofiles, subtitles, showdirs, media, season )
    remove_torrent( msuccess, new )
  elif 'Season' in media:
    print (('########################################'),('\n')*2, ("¤ This is a full season:     "),(new))
    season = wash_season( media )
    showname = wash_show_name( new, media )
    showdirs = find_dirs( showname, createpath, season, media )
    videofiles = find_video( downloaddir, new )
    subtitles = find_subtitle( downloaddir, new )
    msuccess = move_files( videofiles, subtitles, showdirs, media, season )
    remove_torrent( msuccess, new )
  elif 'Movie' in media:
    print (('########################################'),('\n')*2, ("¤¤¤¤¤¤¤ This is a movie:     "),(new))
    season = wash_season( media )
    showname = wash_show_name( new, media )
    showdirs = create_dir( showname, createpath, season, media )
    videofiles = find_video( downloaddir, new )
    subtitles = find_subtitle( downloaddir, new )
    msuccess = move_files( videofiles, subtitles, showdirs, media, season )
    remove_torrent( msuccess, new )
  else:
    print (('########################################'),('\n')*2, ("¤¤¤¤ Undetermined media:     "),(new))
exit(0)
