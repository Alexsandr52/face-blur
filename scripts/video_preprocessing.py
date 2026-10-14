import cv2

import subprocess
import argparse
import json
import sys

import os

def mp4_path(path):
    if os.path.splitext(path)[1].lower() != '.mp4':
        raise argparse.ArgumentTypeError('Поддерживаются только файлы MP4')
    return path


def build_parser():
    parser = argparse.ArgumentParser(description='Предобработка видео перед детекцией')
    parser.add_argument(
        '--input_file_path',
        type=mp4_path,
        required=True,
        help='Путь к входному файлу MP4',
    )
    parser.add_argument(
        '--fps_verbose', action='store_true', help='Показать счетчик кадров'
    )
    parser.add_argument(
        '--output_path',
        type=str,
        default='../data',
        help='Путь к папке, куда сохранить результат',
    )
    return parser


def check_paths(input_path, output_dir):
    abs_input = os.path.abspath(input_path)
    abs_output = os.path.abspath(output_dir)

    # Проверка входного файла
    if not os.path.exists(abs_input):
        print(
            f'Ошибка: Входной файл не найден.\nИскал по пути: {abs_input}\nПроверьте правильность имени и пути.'
        )
        return False

    if not os.path.isfile(abs_input):
        print(
            f'Ошибка: Указанный входной путь не является файлом.\nПуть: {abs_input}\nПожалуйста, укажите конкретный файл.'
        )
        return False

    # Проверка прав на чтение входного файла
    if not os.access(abs_input, os.R_OK):
        print(
            f'Ошибка: Нет прав на чтение входного файла.\nПуть: {abs_input}\nЗапустите программу от имени администратора или измените права доступа.'
        )
        return False

    # Проверка выходной папки
    if not os.path.exists(abs_output):
        print(
            f'Ошибка: Выходная папка не существует.\nОжидаемый путь: {abs_output}\nСоздайте её перед запуском программы.'
        )
        return False

    if not os.path.isdir(abs_output):
        print(
            f'Ошибка: Выходной путь занят файлом, а должна быть папка.\nПуть: {abs_output}'
        )
        return False

    # Проверка прав на запись в выходную папку
    if not os.access(abs_output, os.W_OK):
        print(
            f'Ошибка: Запись в выходную папку запрещена системой.\nПапка: {abs_output}\nВыберите другую директорию для сохранения.'
        )
        return False

    print('Проверка путей прошла успешно')
    return True


def get_video_info(video_path):
    result = subprocess.run(
        [
            'ffprobe',
            '-v',
            'error',
            '-show_streams',
            '-show_format',
            '-of',
            'json',
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    data = json.loads(result.stdout)

    video = next(s for s in data['streams'] if s['codec_type'] == 'video')

    has_audio = any(s['codec_type'] == 'audio' for s in data['streams'])

    print('Найденный файл')
    print('Кодек:', video['codec_name'])
    print('Разрешение:', video['width'], 'x', video['height'])
    print('Средний FPS:', video['avg_frame_rate'])
    print('Длительность:', data['format'].get('duration'))
    print('Размер файла:', data['format'].get('size'), 'байт')
    print('Аудио:', has_audio)


def processe_video(input_video_path, output_video_path, fps_verbose=False):

    base_file_name = 'processed_base_' + os.path.splitext(
        os.path.basename(input_video_path)
    )[0] + '.mp4'
    output_video_path = os.path.join(output_video_path, base_file_name)

    capture = cv2.VideoCapture(input_video_path)
    if not capture.isOpened():
        raise RuntimeError('Не получилось открыть видео')

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    if not out.isOpened():
        capture.release()
        raise RuntimeError('Не удалось создать выходное видео')

    frame_number = 0

    try:
        while True:
            ret, frame = capture.read()

            if not ret:
                break

            frame_number += 1
            if fps_verbose:
                cv2.putText(
                    frame,
                    f'Frame: {frame_number}',
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

            out.write(frame)

    finally:
        capture.release()
        out.release()

    print(f'Обработано кадров: {frame_number}')


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not check_paths(args.input_file_path, args.output_path):
        sys.exit(1)

    try:
        get_video_info(args.input_file_path)
        processe_video(args.input_file_path, args.output_path, args.fps_verbose)
    except Exception as error:
        raise error


if __name__ == '__main__':
    main()
