import cv2
import os
import csv

# Настройки
input_folder = 'frames'
input_table = 'table.csv'
output_file = 'output.mp4'
fps = 25
duration_per_frame = 2
text_color = (0, 0, 0)
text_position = (250, 800)

year_data = {}
with open(input_table, 'r') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        year = row[0]
        values = row[1:]
        year_data[year] = values

images = {}
for img_name in os.listdir(input_folder):
    if img_name.endswith(('.png', '.jpg', '.jpeg')):
        try:
            frame_num = int(os.path.splitext(img_name)[0])
            img_path = os.path.join(input_folder, img_name)
            images[frame_num] = img_path
        except ValueError:
            continue

if not images:
    print("В папке нет изображений!")
    exit()

sample_frame = cv2.imread(next(iter(images.values())))
height, width, _ = sample_frame.shape

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

for year, values in year_data.items():
    if year == '':
        continue
    count = 0
    for frame_num, value in enumerate(values, start=0):
        if value.strip() == '+':
            count += 1

    frame = cv2.imread(images[count])
    
    if frame.shape != (height, width, 3):
        frame = cv2.resize(frame, (width, height))
    
    cv2.putText(frame, year, text_position, 
                cv2.FONT_HERSHEY_SIMPLEX, 5, text_color, 10)
    
    for _ in range(int(fps * duration_per_frame)):
        video.write(frame)

video.release()
print(f"Анимация успешно сохранена как {output_file}")