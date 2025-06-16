# Audio2Sub - 音频/视频转字幕 Web 应用

本项目是一个基于 FastAPI 后端和 React 前端的 Web 应用，用于将音频或视频文件转换为字幕。

## 技术栈

- **后端:** FastAPI, Celery, Redis, faster-whisper, ffmpeg-python
- **前端:** React, Vite, TypeScript, Tailwind CSS
- **容器化:** Docker, Docker Compose

## 目录结构

详细的目录结构请参见项目内部文档。

## 启动项目

1.  确保已安装 Docker 和 Docker Compose。
2.  根据 `说明文档` 中的 Redis 和 MySQL 信息，如有必要，请在 `docker-compose.yml` 和后端配置中进行相应调整。
    (注意: MySQL 在此核心功能中不是必需的，但 Redis 是 Celery 的必需组件。)
3.  在项目根目录 (`audio2sub`) 下运行:
    ```bash
    docker-compose up --build
    ```
4.  前端应用将在 `http://localhost:5173` (或其他 Vite 配置的端口) 可用。
5.  后端 API 将在 `http://localhost:8000` (或其他 FastAPI 配置的端口) 可用。

