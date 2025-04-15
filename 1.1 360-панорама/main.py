import cv2
import numpy as np

# Параметры скрипта
VIDEO_PATH = 'input.mp4'    # Путь к исходному видео
OUTPUT_IMAGE = 'panorama.jpg'     # Путь для сохранения панорамы
STRIPE_WIDTH = 30                 # Ширина вырезаемой полосы в пикселях
OVERLAP = 10                       # Перекрытие между полосами (должно быть < STRIPE_WIDTH)
POSITION = 'center'               # Позиция вырезания полосы: 'left', 'center', 'right'

# Проверка параметров
assert OVERLAP < STRIPE_WIDTH, "Перекрытие должно быть меньше ширины полосы"

# Открываем видеофайл
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise ValueError("Не удалось открыть видеофайл")

# Получаем параметры видео
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Рассчитываем позицию вырезания полосы
if POSITION == 'left':
    x = 0
elif POSITION == 'right':
    x = frame_width - STRIPE_WIDTH
else:  # center
    x = (frame_width - STRIPE_WIDTH) // 2

# Рассчитываем шаг между полосами
step = STRIPE_WIDTH - OVERLAP
panorama_width = (frame_count - 1) * step + STRIPE_WIDTH

# Создаем контейнер для панорамы
panorama = np.zeros((frame_height, panorama_width, 3), dtype=np.uint8)

# Обрабатываем первый кадр
ret, prev_frame = cap.read()
if ret:
    first_stripe = prev_frame[:, x:x+STRIPE_WIDTH]
    panorama[:, :STRIPE_WIDTH] = first_stripe

# Обрабатываем остальные кадры
for i in range(1, frame_count):
    ret, frame = cap.read()
    if not ret:
        break

    # Вырезаем вертикальную полосу
    stripe = frame[:, x:x+STRIPE_WIDTH]
    
    # Позиция для вставки
    col_start = i * step
    col_end = col_start + STRIPE_WIDTH
    
    # Область перекрытия
    overlap_start = max(0, col_start)
    overlap_end = col_start + OVERLAP
    
    # Линейное смешивание в зоне перекрытия
    if overlap_end > overlap_start:
        # Весовые коэффициенты
        blend_width = overlap_end - overlap_start
        alpha = np.linspace(0, 1, blend_width).reshape(1, blend_width, 1)
        
        # Смешивание
        panorama_part = panorama[:, overlap_start:overlap_end]
        stripe_part = stripe[:, :blend_width]
        blended = (stripe_part * alpha + panorama_part * (1 - alpha)).astype(np.uint8)
        
        # Обновление панорамы
        panorama[:, overlap_start:overlap_end] = blended
        panorama[:, overlap_end:col_end] = stripe[:, blend_width:]
    else:
        panorama[:, col_start:col_end] = stripe

# Сохраняем результат
cv2.imwrite(OUTPUT_IMAGE, panorama)
cap.release()

print(f"Панорама успешно сохранена как {OUTPUT_IMAGE}")