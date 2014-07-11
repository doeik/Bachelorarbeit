archlinux=(archinstall archuninstall)
debian=(debinstall debuninstall)
declare -A dists
dists[/etc/arch-release]=$archlinux
dists[/etc/debian_version]=$debian

# determine distribution

for fpath in ${!dists[@]}
do
  if [ -f $fpath ]
  then
    installarray=${dists[$fpath]}
    break
  fi
done


if [ -z $installarray ]
then
  echo "no supported distribution found"
  exit 1
fi


function archinstall() {
  yaourt -S --noconfirm --needed git
  yaourt -S --noconfirm --needed python
  yaourt -S --noconfirm --needed python-setproctitle
  yaourt -S --noconfirm --needed lxc-git
  yaourt -S --noconfirm --needed debootstrap
  sudo groupadd info2_containers
  sudo cp ./lxc_daemon.py /usr/local/bin/
  sudo chmod 700 /usr/local/bin/lxc_daemon.py
  sudo cp ./lxc_daemon.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable lxc_daemon.service
  sudo systemctl start lxc_daemon.service
  echo do not forget to add the user who wants to communicate with the daemon to group info2_containers
}


function archuninstall() {
  sudo groupdel info2_containers
  sudo systemctl stop lxc_daemon.service
  sudo systemctl disable lxc_daemon.service
  sudo rm /usr/local/bin/lxc_daemon.py
  sudo rm /etc/systemd/system/lxc_daemon.service
}


function debinstall() {
  sudo apt-get install -y debootstrap
  sudo apt-get install -y python
  sudo apt-get install -y python-setproctitle
  sudo apt-get install -y git
  currentdir=pwd
  mkdir /tmp/lxc_on_github
  cd /tmp/lxc_on_github
  git clone https://github.com/lxc/lxc.git
  cd ./lxc
  ./autogen.sh
  cd ./src
  ./configure
  make
  make install
  sudo rm -rf /tmp/lxc_on_github
  sudo groupadd info2_containers
  cd $currentdir
  sudo cp ./lxc_daemon.py /usr/local/bin/
  sudo chmod 700 /usr/local/bin/lxc_daemon.py
  sudo cp ./lxc_daemon.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable lxc_daemon.service
  sudo systemctl start lxc_daemon.service
  echo do not forget to add the user who wants to communicate with the daemon to group info2_containers
}

function debuninstall() {
  sudo groupdel info2_containers
  sudo systemctl stop lxc_daemon.service
  sudo systemctl disable lxc_daemon.service
  sudo rm /usr/local/bin/lxc_daemon.py
  sudo rm /etc/systemd/system/lxc_daemon.service
}


# run install or uninstall function for current distribution

if [ "$1" = "" ] || [ "$1" = "install" ]
then
  ${installarray[0]}
elif [ "$1" = "uninstall" ]
then
  ${installarray[1]}
fi