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
  sudo apt-get install -y gcc debootstrap python python3-dev python3-setproctitle git make automake pkg-config linux-headers-amd64 libcap-dev libcap2 libcgmanager-dev
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
  sudo groupadd lxc_containers
  sudo cp ./lxc_daemon.py /usr/local/bin/
  sudo chmod 700 /usr/local/bin/lxc_daemon.py
  sudo mkdir /usr/local/share/lxc_daemon
  sudo cp ./config_template /usr/local/share/lxc_daemon/config_template
  sudo cp ./lxc_daemon.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable lxc_daemon.service
  sudo systemctl start lxc_daemon.service
}


function uninstall() {
  sudo groupdel lxc_containers
  sudo systemctl stop lxc_daemon.service
  sudo systemctl disable lxc_daemon.service
  sudo rm /usr/local/bin/lxc_daemon.py
  sudo rm /etc/systemd/system/lxc_daemon.service
  sudo rm -rf /usr/local/share/lxc_daemon
  sudo rm /run/uds_lxcdaemon
}

function upgrade() {
  sudo cp ./lxc_daemon.py /usr/local/bin/lxc_daemon.py
  sudo cp ./lxc_daemon.service /etc/systemd/system/
  sudo cp ./config_template /usr/local/share/lxc_daemon/config_template
  sudo systemctl daemon-reload
  sudo systemctl restart lxc_daemon.service
}


# run install or uninstall function for current distribution

if [ "$1" = "" ] || [ "$1" = "install" ]
then
  $installfunction
  coreinstall
  echo do not forget to add the user who wants to communicate with the daemon to group lxc_containers
elif [ "$1" = "uninstall" ]
then
  uninstall
elif [ "$1" = "upgrade" ]
then
  upgrade
fi