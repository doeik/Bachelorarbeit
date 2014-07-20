declare -A dists
dists[/etc/arch-release]=archinstall
dists[/etc/debian_version]=debinstall

# determine distribution

for fpath in ${!dists[@]}
do
  if [ -f $fpath ]
  then
    installfunction=${dists[$fpath]}
    break
  fi
done


if [ -z $installfunction ]
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
}


function debinstall() {
  sudo apt-get install -y gcc
  sudo apt-get install -y debootstrap
  sudo apt-get install -y python
  sudo apt-get install -y python-setproctitle
  sudo apt-get install -y git
  sudo apt-get install -y make
  sudo apt-get install -y automake
  sudo apt-get install -y pkg-config
  currentdir=$(pwd)
  mkdir /tmp/lxc_on_github
  cd /tmp/lxc_on_github
  git clone https://github.com/lxc/lxc.git
  cd ./lxc
  ./autogen.sh
  ./configure
  make
  sudo make install
  sudo rm -rf /tmp/lxc_on_github
  cd $currentdir
}


function coreinstall() {
  sudo groupadd info2_containers
  sudo cp ./lxc_daemon.py /usr/local/bin/
  sudo chmod 700 /usr/local/bin/lxc_daemon.py
  sudo mkdir /usr/local/lib/lxc_daemon
  sudo cp ./config_template /usr/local/lib/lxc_daemon/config_template
  sudo cp ./lxc_daemon.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable lxc_daemon.service
  sudo systemctl start lxc_daemon.service
}


function uninstall() {
  sudo groupdel info2_containers
  sudo systemctl stop lxc_daemon.service
  sudo systemctl disable lxc_daemon.service
  sudo rm /usr/local/bin/lxc_daemon.py
  sudo rm /etc/systemd/system/lxc_daemon.service
  sudo rm -rf /usr/local/lib/lxc_daemon
  sudo rm /run/uds_lxcdaemon
}


# run install or uninstall function for current distribution

if [ "$1" = "" ] || [ "$1" = "install" ]
then
  $installfunction
  coreinstall
  echo do not forget to add the user who wants to communicate with the daemon to group info2_containers
elif [ "$1" = "uninstall" ]
then
  uninstall
fi