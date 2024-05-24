from ultralytics import YOLO
 
# load a pretrained model 
model = YOLO('cs2_yolov8m_640_augmented_v4.pt')
# model = YOLO('./runs/detect/cs2_yolov8m_640_augmented_v4/weights/last.pt')

# training
if __name__ == '__main__':
	results = model.train(
	   data='cs2.yaml',
	   cfg='cs2_cfg.yaml',
	   imgsz=640, # 640
	   epochs=600,
	   batch=64,
	   patience=100,
	   cache="ram",
	   name='cs2_yolov8m_640_augmented_v4',
	   device="cuda",
	   resume=True,
	   augment=True)
	results = model.val()