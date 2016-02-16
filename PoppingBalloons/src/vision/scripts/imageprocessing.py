#!/usr/bin/env python

# TO DO:
#	


import rospy
from std_msgs.msg import Int16MultiArray

import cv2
import numpy as np
import math
import time

# Set up video to use the default camera
cap = cv2.VideoCapture(-1)

# Wait for connection of serial
time.sleep(2)

# Initialize variables
target = 0 
initialize = 0
x_degree = y_degree = 90
y_point_laser = x_point_laser = -1
y_point_target = x_point_target = -1 

# Window names
RED_LASER_MASK = "Red Image Mask"
BLACK_BALLOON_MASK = "Black Image Mask"
cv2.namedWindow(RED_LASER_MASK)
cv2.namedWindow(BLACK_BALLOON_MASK)

# TO DO: Set individual values
h_min_red = 126
h_max_red = 179
s_min_red = 43 
s_max_red = 255
v_min_red = 142
v_max_red = 255

h_min_black = 64 
h_max_black = 75 
s_min_black = 28
s_max_black = 255
v_min_black = 114
v_max_black = 255

def nothing(x):
    pass

cv2.createTrackbar('LowH', BLACK_BALLOON_MASK, h_min_black, 179, nothing)
cv2.createTrackbar('HighH', BLACK_BALLOON_MASK, h_max_black, 179, nothing)
cv2.createTrackbar('LowS', BLACK_BALLOON_MASK, s_min_black, 255, nothing)
cv2.createTrackbar('HighS', BLACK_BALLOON_MASK, s_max_black, 255, nothing) 
cv2.createTrackbar('LowV', BLACK_BALLOON_MASK, v_min_black, 255, nothing)
cv2.createTrackbar('HighV', BLACK_BALLOON_MASK, v_max_black, 255, nothing) 

cv2.createTrackbar('LowH', RED_LASER_MASK, h_min_red, 179, nothing)
cv2.createTrackbar('HighH', RED_LASER_MASK, h_max_red, 179, nothing)
cv2.createTrackbar('LowS', RED_LASER_MASK, s_min_red, 255, nothing)
cv2.createTrackbar('HighS', RED_LASER_MASK, s_max_red, 255, nothing) 
cv2.createTrackbar('LowV', RED_LASER_MASK, v_min_red, 255, nothing)
cv2.createTrackbar('HighV', RED_LASER_MASK, v_max_red, 255, nothing) 

erodeKernel = cv2.getStructuringElement(cv2.MORPH_RECT,(1,1))
dilateKernel = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))

def publisher():
  pub = rospy.Publisher('/commands', Int16MultiArray, queue_size = 2)
  rospy.init_node('publisher', anonymous = True)
  rate = rospy.Rate(.2) #10hz
  
  while not rospy.is_shutdown():
    flag, frame = cap.read()

    # If no image is recieved, exit
    if flag == False:
	print "No Image recieved! Exiting ..."
	break

    # Get image Size
    width, height = frame.shape[:2]

    # Convet to HSV 
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h_min_black = cv2.getTrackbarPos('LowH', BLACK_BALLOON_MASK)
    h_max_black = cv2.getTrackbarPos('HighH', BLACK_BALLOON_MASK)
    s_min_black = cv2.getTrackbarPos('LowS', BLACK_BALLOON_MASK)
    s_max_black = cv2.getTrackbarPos('HighS', BLACK_BALLOON_MASK) 
    v_min_black = cv2.getTrackbarPos('LowV', BLACK_BALLOON_MASK)
    v_max_black = cv2.getTrackbarPos('HighV', BLACK_BALLOON_MASK) 
	  
    h_min_red = cv2.getTrackbarPos('LowH', RED_LASER_MASK)
    h_max_red = cv2.getTrackbarPos('HighH', RED_LASER_MASK)
    s_min_red = cv2.getTrackbarPos('LowS', RED_LASER_MASK)
    s_max_red = cv2.getTrackbarPos('HighS', RED_LASER_MASK) 
    v_min_red = cv2.getTrackbarPos('LowV', RED_LASER_MASK)
    v_max_red = cv2.getTrackbarPos('HighV', RED_LASER_MASK) 
	  
    # Get only specified color
    lower = np.array([h_min_black, s_min_black, v_min_black], dtype=np.uint8)
    upper = np.array([h_max_black, s_max_black, v_max_black], dtype=np.uint8)
    black_mask = cv2.inRange(hsv, lower, upper)
    lower = np.array([h_min_red, s_min_red, v_min_red], dtype=np.uint8)
    upper = np.array([h_max_red, s_max_red, v_max_red], dtype=np.uint8)
    red_mask = cv2.inRange(hsv, lower, upper)

    black_mask = cv2.erode(black_mask,erodeKernel,iterations=2)
    black_mask = cv2.dilate(black_mask,dilateKernel,iterations=1)
    red_mask = cv2.erode(red_mask,erodeKernel,iterations=3)
    red_mask = cv2.dilate(red_mask,dilateKernel,iterations=4)
	
    # Show video
    cv2.imshow(RED_LASER_MASK, red_mask)
    cv2.imshow(BLACK_BALLOON_MASK, black_mask)
	
    # Find Target Location
    findTargetLocation()
	
    # Find Laser Location
    findLaserLocation()
	
    # Check X Point
    checkXPoint()
	
    # Check Y Point
    checkYPoint()
	
    # Set array
    d = IntList()
    d.data = [x_degree, y_degree]
    
    # Publish array
    pub.publish(d)
	
    # Show video
    cv2.imshow("frame", frame)
    
    rate.sleep()
	
    if cv2.waitKey(1) >= 0:
      break
    
if __name__ == '__main__':
  try:
    publisher()
  except rospy.ROSInterruptException:
    pass
  
#Functions
def findLaserLocation():
  # Find Laser Location
  contours, hierarchy = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
				
  # Find the index of the largest contour
  areas = [cv2.contourArea(c) for c in contours]

  if len(areas) >= 1:
    max_index = np.argmax(areas)
    cnt = contours[max_index]

  # Bounding rectangle
  x, y, w, h = cv2.boundingRect(cnt)
  cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
	
  # Calculate coordinates
  x_point_laser = x + w/2
  y_point_laser = y + h/2
  
def findTargetLocation():
  contours, hierarchy = cv2.findContours(black_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
		
  # Find the index of the largest contour
  areas = [cv2.contourArea(c) for c in contours]
	
  if len(areas) >= 1:
    # Sort list
    areas.sort()
	
    # Max
    max_index = np.argmax(areas)
    cnt = contours[max_index]
	
    # Bounding rectangle
    x_point_target, y_point_target, w1, h1 = cv2.boundingRect(cnt)
	
    cv2.circle(frame, (int(x_point_target), int(y_point_target)), 4, (0,255,0)) 

    # Initialize as target found
    target = 1
  else:
    # Initailize target as not found
    target = 0
    
def checkXPoint():
  # Check if laser is at the right point relative to the x axis
  if 8 < math.fabs(x_point_laser - x_point_target) and target == 1 and initialize != 0:
    # Point is not realative to the x axis
    # Change X degrees
    if x_point_laser < x_point_target:
      x_degree++
    elif x_point_laser > x_point_target:
      x_degree--

def checkYPoint():
  # Check if laser is at the right point relative to the y axis
  if  8 < math.fabs(y_point_laser - y_point_target) and target == 1 and initialize != 0:
    # Point is not realative to the y axis      
    # Change Y degrees
    if y_point_laser < y_point_target:
      y_degree++
    elif y_point_laser > y_point_target:
      y_degree--