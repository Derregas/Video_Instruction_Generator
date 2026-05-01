from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector

def get_video_scenes(video_path):
    """Находит границы смены сцен в видео."""
    print("--- ФТ-3: Поиск смен планов (сцен) ---")
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=30))

    scene_manager.detect_scenes(video)
    scenes = scene_manager.get_scene_list()
    return scenes

def find_best_scene_for_speech(speech_segment, scenes):
    t1, t2 = speech_segment['start'], speech_segment['end']
    best_scene = None
    best_idx = -1
    max_overlap = -1
    
    for idx, scene in enumerate(scenes):
        s1, s2 = scene[0].get_seconds(), scene[1].get_seconds()
        # Находим длину пересечения интервалов
        overlap = min(t2, s2) - max(t1, s1)
        
        if overlap > max_overlap:
            max_overlap = overlap
            best_scene = scene
            best_idx = idx
            
    return best_scene, best_idx

def align_data(transcript, scenes, video_path):
    final_steps = []
    
    for i, text_block in enumerate(transcript):
        # Ищем сцену, которая "покрывает" этот текст
        target_scene, scene_idx = find_best_scene_for_speech(text_block, scenes)
        
        if not target_scene:
            continue

        s1, s2 = target_scene[0].get_seconds(), target_scene[1].get_seconds()
        # Определяем время для скриншота (середина пересечения)
        shot_time = (max(text_block['start'], s1) + 
                     min(text_block['end'], s2)) / 2
        
        img_path = f"temp/step_{i}.jpg"
        extract_keyframe(video_path, shot_time, img_path)
        
        final_steps.append({
            "step": i + 1,
            "text": text_block['text'],
            "image": img_path,
            "scene_id": scene_idx,
            "shot_time": shot_time,
            "scene_start": s1,
            "scene_end": s2
        })
        
    return final_steps

import cv2

def extract_keyframe(video_path, timestamp, output_path):
    """Извлекает кадр из видео по заданной секунде."""
    cap = cv2.VideoCapture(video_path)
    # Переходим на нужную миллисекунду
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
    success, image = cap.read()
    if success:
        cv2.imwrite(output_path, image)
    cap.release()
    return output_path if success else None