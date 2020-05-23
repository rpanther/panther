#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2020, Raffaello Bonghi <raffaello@rnext.it>
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import rospy
import importlib
import rosservice
import genpy
from threading import Thread

class Observer(Thread):

    def __init__(self, topic_name, topic_type, timeout, service, request):
        super(Observer, self).__init__()
        self.timer = None
        self.timeout = timeout
        self.service = service
        self.request = request
        # Disable check timeout
        self.last_message = -1
        # Extract topic class
        package, message = topic_type.split('/')
        mod = importlib.import_module(package + '.msg')
        topic_type = getattr(mod, message)
        # Launch Joystick reader
        rospy.Subscriber(topic_name, topic_type, self.topic_callback)
        # Service classes
        self.service_proxy = None
        self.service_class = None
        # Start Service client
        self._thread = Thread(target=self._init_service, args=[])
        self._thread.start()
        # Start thread
        self.start()

    def _init_service(self):
        try:
            rospy.wait_for_service(self.service)
            # Extract service class by name
            self.service_class = rosservice.get_service_class_by_name(self.service)
            self.service_proxy = rospy.ServiceProxy(self.service, self.service_class)
            rospy.loginfo("Initialized {service}".format(service=self.service))
        except rospy.ServiceException, error:
            rospy.logerr("Service call failed: {error}".format(error=error))
        except rosservice.ROSServiceException, error:
            rospy.logerr("Service call failed: {error}".format(error=error))
        except rospy.ROSException, error:
            rospy.loginfo("Service error")

    def fire_service(self):
        # Call service
        if self.service_proxy is None and self.service_class is None:
            rospy.logerr("Service {service} not initializated".format(service=self.service))
            return
        # Make service message
        service_class = self.service_class._request_class()
        try:
            genpy.message.fill_message_args(service_class, [self.request])
        except genpy.MessageException, error:
            rospy.logerr("Message in {service}: {error}".format(service=self.service, error=error))
            return
        # Run  service proxy
        try:
            res = self.service_proxy(service_class)
            rospy.loginfo("Output {service} {res}".format(service=self.service, res=res.return_))
        except rospy.ServiceException, error:
            rospy.logerr("Service call failed: {error}".format(error=error))
            # Restart initialization thread
            self._thread.join()
            if not self._thread.is_alive():
                self._thread = Thread(target=self._init_service, args=[])
                self._thread.start()

    def run(self):
        # Running only with ROS active
        while not rospy.is_shutdown():
            if self.last_message > 0:
                # Timeout in minutes
                if rospy.get_time() - self.last_message >= self.timeout * 60:
                    # Clean message
                    self.last_message = -1
                    # Fire service
                    self.fire_service()
        # Close thread
        rospy.logdebug("Close!")

    def topic_callback(self, data):
        # Initialize timer
        self.last_message = rospy.get_time()


def topic_observer():
    rospy.init_node('topic_observer', anonymous=True)
    # Load topic to observer
    topic_name = rospy.get_param("~name", "chatter")
    topic_type = rospy.get_param("~type", "std_msgs/String")
    timeout = rospy.get_param("~timeout", 1)
    # Load service and request
    service = rospy.get_param("~service", "")
    request = rospy.get_param("~request", {})
    rospy.loginfo("Timeout={timeout}min Name={name} Type={type}".format(timeout=timeout, name=topic_name, type=topic_type))
    # Start observer
    Observer(topic_name, topic_type, timeout, service, request)
    # Spin message
    rospy.spin()


if __name__ == '__main__':
    topic_observer()
# EOF
