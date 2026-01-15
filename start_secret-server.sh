#!/data/data/com.termux/files/usr/bin/sh
# Standard Termux Boot Script for Secret Server
# Starts SSH Daemon and Web Server on boot
termux-wake-lock
sshd
sleep 10
cd $HOME/secret-server
./start_server.sh
