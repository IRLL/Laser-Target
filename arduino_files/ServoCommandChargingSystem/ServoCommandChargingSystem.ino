#include <ros.h>
#include <std_msgs/Int16MultiArray.h>
#include <Servo.h>

ros::NodeHandle  nh;

// create servo objects to control a servos
Servo servoOne;
Servo servoTwo;
Servo servoThree;
Servo servoFour;
Servo servoFive;

//Subscriber call back
void messageCb(const std_msgs::Int16MultiArray& msg)
{
  //Write servo degree one
  servoOne.write(msg.data[0]);
  servoTwo.write(msg.data[1]);
  servoThree.write(msg.data[2]);
  servoFour.write(msg.data[3]);
  servoFive.write(msg.data[4]);
}

//Define all subscribers
ros::Subscriber<std_msgs::Int16MultiArray> sub("/ServoCommand",messageCb);

void setup()
{
  //Initialize pins 3 and 4
  servoOne.attach(3);
  servoTwo.attach(4);
  servoThree.attach(5);
  servoFour.attach(6);
  servoFive.attach(7);
  
  //Set up ros 
  nh.initNode();
  nh.subscribe(sub);
}

void loop()
{
  nh.spinOnce();
}
