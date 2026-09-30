# Project Brief — AI Video Studio: LTX-2.5 & MiniMax H3

> Tổng quan cốt lõi, mục tiêu và phạm vi của hệ thống AI Video Studio.

## 1. Giới thiệu dự án
Hệ thống **AI Video Studio** chuyên nghiệp tích hợp hai mô hình sinh video tiên tiến nhất hiện nay:
- **Lightricks LTX-2.5 (22B)**: Mô hình tạo video chất lượng cao với quy trình 2-stage denoising, upscaler không gian latent x2 và kiểm soát đa nhân vật qua IC-LoRA & PromptRelay.
- **MiniMax H3 (Omni-Modal Video + Native Audio)**: Mô hình video tạo đồng thời video độ phân giải cao và âm thanh stereo tự nhiên (lời thoại, hiệu ứng môi trường, nhạc nền) trong một pass duy nhất, hỗ trợ Multi-Subject Reference (MSR) với tối đa 4 ảnh tham chiếu.

## 2. Mục tiêu cốt lõi (Core Objectives)
- **Kiểm soát tính nhất quán nhân vật (Character Consistency):** Giải quyết triệt để vấn đề mất tính nhất quán khuôn mặt và trang phục giữa các phân cảnh qua kỹ thuật Multi-Subject Reference (MSR).
- **Video & Âm thanh đồng bộ tự nhiên (Native Audio-Visual Synthesis):** Tận dụng MiniMax H3 để tạo video có sẵn âm thanh khớp ngữ cảnh mà không cần ghép âm thanh hậu kỳ thủ công.
- **Tối ưu hóa tài nguyên phần cứng (VRAM & Compute Optimization):** Chạy mượt mà trên môi trường điện toán đám mây như Google Colab GPU (T4, V100, A100, L4) thông qua lượng tử hóa `int8_convrot`, `fp4 AWQ`, Turbo LoRA (4-step, 8-step), và Tiled VAE decode.
- **Hậu xử lý mượt mà (Frame Interpolation):** Nâng tốc độ khung hình từ 24fps lên 48fps (2x) hoặc 96fps (4x) bằng mô hình RIFE AI độc lập, giữ nguyên đồng bộ âm thanh.
- **Quy trình kịch bản đến video (Script-to-Video Workflow):** Cung cấp kho kịch bản chuẩn điện ảnh, tài nguyên ảnh tham chiếu và giao diện Gradio UI trực quan dễ sử dụng.

## 3. Các thành phần chính (Key Deliverables)
1. **Module MiniMax H3 (`minimax/`):**
   - `download.py`: Tải tự động và quản lý checkpoint, VAE int8, Turbo LoRA, Text Encoder Qwen3-VL 32B.
   - `minimax.py`: Server ComfyUI quản lý ngầm + WebUI Gradio (chế độ MSR `<Picture 1>`–`<Picture 4>` và I2V First-Last Frame).
   - `rife_postprocess.py`: Bộ công cụ độc lập nội suy khung hình RIFE v4.26 tăng FPS và slow-motion.
   - Notebooks Colab (`MiniMax_H3_MSR_Colab.ipynb`, `MiniMax_H3_MSR_I2V_Colab.ipynb`).
2. **Module LTX-2.5 (`ltx/`):**
   - `ltx2_5.py`: Studio đa năng hỗ trợ Text-to-Video (T2V), Image-to-Video (I2V), First-Last Frame, Storyboard đa cảnh nối tự động qua FFmpeg.
   - `ltx2_5_msr.py`: Studio MSR chuyên sâu khóa diện mạo 4 nhân vật + 1 bối cảnh.
   - Notebook Colab (`LTX_2_5_MSR_Colab.ipynb`).
3. **Mẫu Workflow ComfyUI (`workflow/`):**
   - Bộ workflow JSON trực quan cho cả LTX-2.5 và MiniMax H3.
4. **Bộ kịch bản & Dataset tham chiếu (`scripts/`):**
   - Các kịch bản phim tài liệu thiên nhiên, tâm lý học, hài hước, khoa học viễn tưởng kèm đầy đủ ảnh nhân vật chuẩn tỉ lệ 16:9.
