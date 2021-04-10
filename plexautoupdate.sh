#!/bin/bash

updateurl="https://plex.tv/downloads/latest/1?channel=16&build=linux-ubuntu-x86_64&distro=redhat&X-Plex-Token=removed"
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
NORMAL=$(tput sgr0)
sessions=$(ps aux |grep "Plex Transcoder" | grep plex | cut -d " " -f1 | wc -l);
col=80 # change this to whatever column you want the output to start at

########### MAIN SCRIPT ########################
echo "---===$(date)===---" ; 
echo -n "Checking if any movies are being watched" ;
updatefile=$(wget -q --spider "$updateurl");
if [ "$sessions" -lt "1" ]
  then
    printf '%s%*s%s' "$GREEN" $col "[OK]" "$NORMAL" && echo -ne "\n" ;
    echo -n "Checking if download file is accessible" ;
    wget -q --spider "https://plex.tv/downloads/latest/1?channel=16&build=linux-ubuntu-x86_64&distro=redhat&X-Plex-Token=removed" ;
    if [ $? -eq 0 ] 
      then
        printf '%s%*s%s' "$GREEN" 81 "[OK]" "$NORMAL" && echo -ne "\n" ;	 
        echo -n "Downloading plex.rpm" ;
        wget -q -O /root/plex.rpm "https://plex.tv/downloads/latest/1?channel=16&build=linux-ubuntu-x86_64&distro=redhat&X-Plex-Token=removed" ;
        if [ -f /root/plex.rpm ];
          then
            printf '%s%*s%s' "$GREEN" 100 "[OK]" "$NORMAL" && echo -ne "\n" ;
          else
            printf '%s%*s%s' "$RED" 100 "[FAIL]" "$NORMAL" && echo -ne "\n" && echo "Failed downloading file, exiting" && exit 1 ;
        fi
        newplex="$(rpm -qp /root/plex.rpm | grep plex | cut -d "-"  -f 2)" ;
        currentplex="$(rpm -q plexmediaserver | cut -d "-" -f 2)" ;
        echo "Comparing versions, CURRENT=$currentplex DOWNLOADED=$newplex" ;
        compare=$(rpmdev-vercmp $newplex $currentplex 2>/dev/null);
        qnewlatest=$(echo $compare |grep ">" |cut -d ">" -f 1 | xargs) ;
        oldlatest=$(echo $compare |grep "<" |cut -d ">" -f 1 | xargs) ;
        nochange=$(echo $compare |grep "==" | cut -d " " -f 2 | xargs) ;
        if [ -n "$nochange" ]
          then
            echo "There is no update to PlexMediaServer, exiting." ;
            rm -f /root/plex.rpm && exit 0 ;
        elif [ -n "$oldlatest" ]
          then	
            echo "Installed version of PlexMediaServer is newer than download, exiting" ;
            rm -f /root/plex.rpm&& exit 1 ;
        elif [ -n "$newlatest" ]
          then 
            echo "Found new version $newlatest of PlexMediaServer, continuing with installation" ;
            mv "/root/plex.rpm" "/root/plex-$newlatest.rpm" >/dev/null 2>/dev/null;
            systemctl stop plexmediaserver ;
            yum -y localinstall "/root/plex-$newlatest.rpm" >/dev/null 2>/dev/null;
            sleep 30 ;
            systemctl start plexmediaserver ;
            if [ $? -eq 0 ];then 
              printf '%s%*s%s' "$GREEN" $col "Installation Success" "$NORMAL" && echo -ne "\n" ;
            fi
        fi
    else
      printf '%s%*s%s' "$RED" 67 "[FAIL]" "$NORMAL" && echo -ne "\n" ;
      echo "No rpm file was found on plex.tv, exiting" && exit 1 ;
    fi

  else
    printf '%s%*s%s' "$RED" 67 "[FAIL]" "$NORMAL" && echo -ne "\n" ;
    echo "A movie is currently being streamed, will not check on upgrade" && exit 1 ;
fi
exit 0
