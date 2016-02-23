#!/usr/bin/env python

# TO DO:
#       Implement when laser is out of sight of camera
#       Set max and min values for servos

# Reference:
#       Servo 1 : Left x servo (starts at 135 degrees)
#       Servo 2 : Right x servo (starts at 135 degrees)
#       Servo 3 : Directional y servo (starts at 90 degrees)
#       Servo 4 : y servo (starts at 45 degrees)
#       Servo 5 : safe laser servo (starts at 180 degrees)
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
y_point_laser = x_point_laser = -1
y_point_target = x_point_target = -1

# Initialize servo
servo1 = 135
servo2 = 135
servo3 = 90
servo4 = 45
servo5 = 180

# Window names
RED_LASER_MASK = "Red Laser Image Mask"
BLUE_TARGET_MASK = "Blue Target Image Mask"
cv2.namedWindow(RED_LASER_MASK)
cv2.namedWindow(BLUE_TARGET_MASK)

# TO DO: Set individual values
h_min_red = 126
h_max_red = 179
s_min_red = 43 
s_max_red = 255
v_min_red = 142
v_max_red = 255

h_min_blue = 64 
h_max_blue = 75 
s_min_blue = 28
s_max_blue = 255
v_min_blue = 114
v_max_blue = 255

def nothing(x):
    pass

cv2.createTrackbar('LowH', BLUE_TARGET_MASK, h_min_blue, 179, nothing)
cv2.createTrackbar('HighH', BLUE_TARGET_MASK, h_max_blue, 179, nothing)
cv2.createTrackbar('LowS', BLUE_TARGET_MASK, s_min_blue, 255, nothing)
cv2.createTrackbar('HighS', BLUE_TARGET_MASK, s_max_blue, 255, nothing) 
cv2.createTrackbar('LowV', BLUE_TARGET_MASK, v_min_blue, 255, nothing)
cv2.createTrackbar('HighV', BLUE_TARGET_MASK, v_max_blue, 255, nothing) 

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

    h_min_blue = cv2.getTrackbarPos('LowH', BLUE_TARGET_MASK)
    h_max_blue = cv2.getTrackbarPos('HighH', BLUE_TARGET_MASK)
    s_min_blue = cv2.getTrackbarPos('LowS', BLUE_TARGET_MASK)
    s_max_blue = cv2.getTrackbarPos('HighS', BLUE_TARGET_MASK) 
    v_min_blue = cv2.getTrackbarPos('LowV', BLUE_TARGET_MASK)
    v_max_blue = cv2.getTrackbarPos('HighV', BLUE_TARGET_MASK) 
          
    h_min_red = cv2.getTrackbarPos('LowH', RED_LASER_MASK)
    h_max_red = cv2.getTrackbarPos('HighH', RED_LASER_MASK)
    s_min_red = cv2.getTrackbarPos('LowS', RED_LASER_MASK)
    s_max_red = cv2.getTrackbarPos('HighS', RED_LASER_MASK) 
    v_min_red = cv2.getTrackbarPos('LowV', RED_LASER_MASK)
    v_max_red = cv2.getTrackbarPos('HighV', RED_LASER_MASK) 
          
    # Get only specified color
    lower = np.array([h_min_blue, s_min_blue, v_min_blue], dtype=np.uint8)
    upper = np.array([h_max_blue, s_max_blue, v_max_blue], dtype=np.uint8)
    blue_mask = cv2.inRange(hsv, lower, upper)
    lower = np.array([h_min_red, s_min_red, v_min_red], dtype=np.uint8)
    upper = np.array([h_max_red, s_max_red, v_max_red], dtype=np.uint8)
    red_mask = cv2.inRange(hsv, lower, upper)

    blue_mask = cv2.erode(blue_mask,erodeKernel,iterations=2)
    blue_mask = cv2.dilate(blue_mask,dilateKernel,iterations=1)
    red_mask = cv2.erode(red_mask,erodeKernel,iterations=3)
    red_mask = cv2.dilate(red_mask,dilateKernel,iterations=4)
        
    # Show video
    cv2.imshow(RED_LASER_MASK, red_mask)
    cv2.imshow(BLUE_TARGET_MASK, blue_mask)
        
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
  contours, hierarchy = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
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
      #move right
      servo1++
      #move directional y right
      servo3++
    elif x_point_laser > x_point_target: 
      #move left
      servo1--
      #move directional y left
      servo3--

def checkYPoint():
  # Check if laser is at the right point relative to the y axis
  if  8 < math.fabs(y_point_laser - y_point_target) and target == 1 and initialize != 0:
    # Point is not realative to the y axis
    # Change Y degrees
    if y_point_laser < y_point_target:
      #move up
      servo4++
    elif y_point_laser > y_point_target:
      #move down
      servo4--