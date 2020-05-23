cmake_minimum_required(VERSION 2.8.3)
project(panther_common)

find_package(catkin REQUIRED COMPONENTS rospy genpy rosservice)

catkin_package()

roslaunch_add_file_check(launch)

include_directories()

catkin_install_python(PROGRAMS scripts/topic_observer.py
                      DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

catkin_install_python(PROGRAMS scripts/zed_to_pose_estimate.py
                      DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

# Install param and launch folders
install(DIRECTORY launch config
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
