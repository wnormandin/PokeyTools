#!/usr/bin/env bash
sleep 0.1
clear
sleep 0.25
echo 'You drift into the darkness, to adventure another day'
echo 'Running post-exit cleanup...'
rm -rf ./*.pyc
rm -rf ./data/*.pyc
rm -rf ./modules/*.pyc
sleep 0.25
echo 'Press any key'

