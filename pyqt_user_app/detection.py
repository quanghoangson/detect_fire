from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import time
import requests
from ultralytics import YOLO

import time

class Detection(QThread):

	def __init__(self, token, location, receiver):
		super(Detection, self).__init__()	

		self.token = token
		self.location = location
		self.receiver = receiver
		self.yolo = YOLO('./models/best.pt')
		self.running = True
		self.starting_time = time.time() - 11   #ql khung hình 
	
	changePixmap = pyqtSignal(QImage)

	


	def run(self):
		cap = cv2.VideoCapture(0) 
		classes = ['Fire', 'Smoke']
		while self.running:
			ret, frame = cap.read()  							#chụp khung hình ,fps
			if ret:

				height, width, channels = frame.shape
				results = self.yolo(frame)  					# run model yolo,fps
				
				for result in results: #class, boxes, conf
					boxes = result.boxes.numpy()
					for box in boxes:
						cls = int(box.cls.item()) 
						conf = box.conf.item()
						print("Confident: ",conf)
						x, y, x2, y2 = map(int, box.xyxy[0])  #map tọa độ các điểm

						if conf > 0.8:
							# play_alert_sound('./sound/emergency_sound.mp3')   

							cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)  
							cv2.putText(frame, f"{classes[cls]}: {conf:.2f}", (x, y - 20), cv2.FONT_HERSHEY_PLAIN, 3, (0, 255, 0), 3)
						
							elapsed_time = self.starting_time - time.time()
							if elapsed_time <= -30: 
								self.starting_time = time.time()
								self.save_detection(frame)
				#display
				rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #convert bgr to rgb
				bytesPerLine = channels * width
				convertToQtFormat = QImage(rgbImage.data, width, height, bytesPerLine, QImage.Format_RGB888)
				p = convertToQtFormat.scaled(854, 480, Qt.KeepAspectRatio)
				self.changePixmap.emit(p)
			else:
				pass
			
	def save_detection(self, frame):

		cv2.imwrite("saved_frames/frame.jpg", frame)
		print('Frame Saved')
		self.post_detection()

	# Sends alert to the server
	def post_detection(self):

			url = 'http://127.0.0.1:8000/api/images/'
			headers = {'Authorization': 'Token ' + self.token}
			files = {'image': open('saved_frames/frame.jpg', 'rb')}
			data = {'user_ID': self.token,'location': self.location, 'alert_receiver': self.receiver}
			print('headder', headers)
			print('data', data)
			response = requests.post(url, files=files, headers=headers, data=data)

			# HTTP 200
			if response.ok:
				print('Alert was sent to the server')
			# Bad response
			else:
				print('Unable to send alert to the server')
				
