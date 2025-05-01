import cv2
import numpy as np

# Параметры
SCALE_FACTOR = 0.5  # Масштабирование кадров
SKIP_FRAMES = 3     # Пропуск кадров для скорости
MIN_MATCHES = 20    # Минимум совпадений для гомографии

# Инициализация видеопотока
cap = cv2.VideoCapture('input-old.mp4')
if not cap.isOpened():
    print("Ошибка открытия видео")
    exit()

# Читаем первый кадр
ret, base_frame = cap.read()
if not ret:
    print("Ошибка чтения первого кадра")
    exit()

# Предобработка первого кадра
base_frame = cv2.resize(base_frame, None, fx=SCALE_FACTOR, fy=SCALE_FACTOR)
base_gray = cv2.cvtColor(base_frame, cv2.COLOR_BGR2GRAY)
panorama = base_frame.copy()
h_pano, w_pano = panorama.shape[:2]

# Инициализация детектора
orb = cv2.ORB_create(nfeatures=2000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

# Для визуализации
debug_mode = True  # Включить для отображения матчей

# Основной цикл обработки
frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_count += 1
    if frame_count % SKIP_FRAMES != 0:
        continue  # Пропускаем кадры
    
    # Предобработка кадра
    curr_frame = cv2.resize(frame, None, fx=SCALE_FACTOR, fy=SCALE_FACTOR)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    
    # Поиск ключевых точек
    kp1, des1 = orb.detectAndCompute(base_gray, None)
    kp2, des2 = orb.detectAndCompute(curr_gray, None)
    
    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
        print(f"Кадр {frame_count}: недостаточно особенностей")
        continue
    
    # Матчинг
    matches = bf.match(des1, des2)
    if len(matches) < MIN_MATCHES:
        print(f"Кадр {frame_count}: недостаточно совпадений ({len(matches)})")
        continue
    
    # Сортировка совпадений
    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = matches[:50]
    
    # Отображение матчей (для отладки)
    if debug_mode:
        match_img = cv2.drawMatches(base_frame, kp1, curr_frame, kp2, 
                                   good_matches, None, flags=2)
        cv2.imshow('Matches', match_img)
        if cv2.waitKey(10) & 0xFF == 27:
            break
    
    # Получаем точки
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1,1,2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1,1,2)
    
    # Вычисляем гомографию
    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    if H is None:
        print(f"Кадр {frame_count}: не удалось найти гомографию")
        continue
    
    # Обновляем панораму
    try:
        # Вычисляем новые размеры
        height, width = curr_frame.shape[:2]
        corners = np.array([
            [0, 0],
            [0, height-1],
            [width-1, height-1],
            [width-1, 0]
        ], dtype=np.float32)
        
        # Трансформируем углы
        warped_corners = cv2.perspectiveTransform(corners.reshape(-1,1,2), H)
        
        # Находим границы
        all_corners = np.concatenate((warped_corners, 
                                     np.array([[[0,0]], [[0,h_pano]], [[w_pano,h_pano]], [[w_pano,0]]], 
                                     dtype=np.float32)), axis=0)
        
        [x_min, y_min] = np.int32(all_corners.min(axis=0).ravel() - 0.5)
        [x_max, y_max] = np.int32(all_corners.max(axis=0).ravel() + 0.5)
        
        # Смещение
        translation_dist = [-x_min, -y_min]
        H_translation = np.array([
            [1, 0, translation_dist[0]],
            [0, 1, translation_dist[1]],
            [0, 0, 1]
        ])
        
        # Применяем преобразование к панораме
        warped_panorama = cv2.warpPerspective(panorama, H_translation, 
                                            (x_max-x_min, y_max-y_min))
        
        # Преобразуем текущий кадр
        warped_curr = cv2.warpPerspective(curr_frame, H_translation.dot(H), 
                                        (x_max-x_min, y_max-y_min))
        
        # Смешивание
        mask = (warped_curr.sum(axis=2) > 0)  # Создаем маску
        warped_panorama[mask] = warped_curr[mask]
        
        # Обновляем панораму
        panorama = warped_panorama
        h_pano, w_pano = panorama.shape[:2]
        base_gray = curr_gray.copy()
        
        print(f"Кадр {frame_count}: размер панорамы {w_pano}x{h_pano}")
        
    except Exception as e:
        print(f"Ошибка при обработке кадра {frame_count}: {str(e)}")
        break

# Сохранение и завершение
cv2.imwrite('panorama_result.jpg', panorama)
cap.release()
if debug_mode:
    cv2.destroyAllWindows()
print("Готово! Панорама сохранена как panorama_result.jpg")