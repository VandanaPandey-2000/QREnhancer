#!/bin/bash
g++ embed.cpp -o embed $(pkg-config --cflags --libs opencv4)