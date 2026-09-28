# 🎬 AI Video Studio: LTX-2.5 & MiniMax H3

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Integration-orange.svg)](https://github.com/comfyanonymous/ComfyUI)
[![Gradio](https://img.shields.io/badge/Gradio-UI%206.0-orange?logo=gradio)](https://gradio.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HuggingFace LTX-2.5](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-LTX--2.5-ffcc00)](https://huggingface.co/Lightricks/LTX-2.5)
[![HuggingFace MiniMax-H3](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-MiniMax--H3-blue)](https://huggingface.co/Comfy-Org/MiniMax-H3)

Hệ thống AI Video Studio chuyên nghiệp tích hợp 2 mô hình tạo video tiên tiến nhất hiện nay: **Lightricks LTX-2.5 (22B)** và **MiniMax H3 (Omni-Modal Video + Native Stereo Audio)**. Hệ thống hoạt động trên nền tảng **ComfyUI Backend** kết hợp giao diện **Gradio WebUI (tương thích Gradio 6.0+)**, hỗ trợ tạo video điện ảnh độ phân giải cao, kiểm soát nhất quán nhân vật qua **Multi-Subject Reference (MSR)** và hậu xử lý làm mượt khung hình qua **RIFE Interpolation**.

---

## 🌟 Điểm nổi bật & Tính năng chính

### 1. 🎬 MiniMax H3 Studio (`minimax/`)
- **Video & Âm thanh đồng bộ tự nhiên (Native Stereo Audio):** MiniMax H3 tạo video cùng giọng nói, âm thanh môi trường và nhạc nền trong cùng 1 pass duy nhất (không phải ghép audio sau).
- **Multi-Subject Reference (MSR - `ref2va`):** Hỗ trợ tối đa 4 ảnh tham chiếu (`<Picture 1>` đến `<Picture 4>`), khóa chặt diện mạo nhân vật và bối cảnh xuyên suốt các phân cảnh.
- **Image-to-Video (I2V - `fl2va`):** Tạo video từ 1 ảnh đầu (First Frame) hoặc nội suy mượt mà giữa ảnh đầu và ảnh cuối (First-Last Frame).
- **⚡ Turbo LoRA tăng tốc:** Tích hợp bộ LoRA Turbo mới nhất (8-step v1.0 và 4-step v1.2 từ lightx2v), cho phép tạo video HD 768p cực nhanh chỉ trong vài chục giây.
- **Tối ưu hóa VRAM & Tốc độ:**
  - Video VAE `int8_convrot` (nhanh hơn 1.4-2.7x, tiết kiệm 46% VRAM so với fp16).
  - Text Encoder Qwen3-VL 32B chuẩn hóa sang `int8` (27GB) và `fp4 AWQ` (16GB), tương thích tốt trên Colab GPU.
  - Tiled VAE Decode & Fast Mode (`--fast`).
- **🎞️ RIFE Frame Interpolation (`rife_postprocess.py`):**
  - Chạy 100% độc lập, nâng FPS từ 24fps gốc lên **48fps (2×)** hoặc **96fps (4×)** siêu mượt mà không làm lệch đồng bộ âm thanh.
  - Chế độ **Slow-motion** chuẩn điện ảnh.

### 2. ⚡ Lightricks LTX-2.5 Studio (`ltx/`)
- **Quy trình 2-Stage Denoising:** Tạo bố cục nhanh ở $1/2$ độ phân giải, nâng cấp qua Latent Spatial Upscaler x2, sau đó hoàn thiện chi tiết ở chuẩn HD sắc nét.
- **Kiểm soát nhân vật qua IC-LoRA Ingredients & PromptRelay:** Khóa diện mạo tối đa 4 nhân vật + 1 bối cảnh.
- **Prompt Enhancer thông minh:** Tích hợp mô hình VLM Gemma (`gemma4_e2b_it_bf16`) tự động mở rộng câu nhắc thành mô tả điện ảnh.
- **Studio đa năng:** Hỗ trợ T2V, I2V, First-Last-Frame và Storyboard nhiều phân cảnh nối tự động bằng FFmpeg.

---

## 📁 Cấu trúc thư mục (Repository Structure)

```text
├── ltx/                                     # Module LTX-2.5 Studio
│   ├── ltx2_5.py                            # Studio đa năng (T2V / I2V / FLF2V / Storyboard)
│   ├── ltx2_5_msr.py                        # Multi-Subject Reference Studio (Gradio UI)
│   └── LTX_2_5_MSR_Colab.ipynb              # Notebook Colab chạy LTX-2.5 MSR
│
├── minimax/                                 # Module MiniMax H3 Studio
│   ├── download.py                          # Cell 1: Tải model (VAE int8, LoRA 8-step, Text Encoders)
│   ├── minimax.py                           # Cell 2: Server ComfyUI & Gradio Live UI (MSR & I2V)
│   ├── rife_postprocess.py                  # Cell 3: RIFE AI Frame Interpolation (24fps -> 48/96fps)
│   ├── MiniMax_H3_MSR_Colab.ipynb           # Notebook Colab cho MSR (Multi-Subject Reference)
│   └── MiniMax_H3_MSR_I2V_Colab.ipynb       # Notebook Colab cho I2V (Image-to-Video)
│
├── workflow/                                # Các mẫu ComfyUI JSON Workflows
│   ├── ltx/                                 # 3 workflow mẫu cho LTX-2.5
│   └── minimax/                             # Workflow chính thức cho MiniMax H3 (ref2va)
│
├── scripts/                                 # Bộ kịch bản mẫu & tài nguyên ảnh tham chiếu
│   ├── 01/                                  # Bướm vua di cư (Monarch butterfly migration)
│   ├── 02/                                  # Phim tài liệu Ếch Thủy Tinh (Glass Frog 3 mins)
│   ├── 03/                                  # The Genesis Scan (Mô phỏng kính tương lai 5 mins)
│   ├── how_loneliness_hurts_your_body/      # Kịch bản khoa học tâm lý
│   ├── minimax_h3/                          # Kịch bản siêu anh hùng & anime
│   ├── msr_midnight_snack_heist/            # Kịch bản hài động vật "Đại náo tủ lạnh"
│   ├── phim_HD/                             # Kịch bản sinh vật cổ đại
│   └── psychology/                          # Kịch bản tâm lý học hành vi
│
├── README.md                                # Tài liệu hướng dẫn sử dụng
└── LICENSE                                  # Giấy phép mã nguồn mở MIT
```

---

## 🚀 Hướng dẫn khởi chạy trên Google Colab

### 🅰️ Khởi chạy MiniMax H3 (Khuyên dùng ⭐)

Mở Colab (GPU A100 hoặc L4 khuyến nghị) và chạy lần lượt 3 Cells:

1. **Cell 1: Cài đặt ComfyUI & Tải Model**
   ```python
   %run minimax/download.py
   ```
2. **Cell 2: Khởi chạy MiniMax H3 WebUI**
   ```python
   %run minimax/minimax.py
   ```
   *Mở liên kết `https://xxxx.gradio.live` được tạo ra để sử dụng giao diện MSR / I2V.*
3. **Cell 3 (Tùy chọn): Làm mượt video với RIFE Post-Processor**
   ```python
   %run minimax/rife_postprocess.py
   ```
   *Mở giao diện RIFE tại port 7861 để nâng video 24fps lên 48fps hoặc 96fps.*

---

### 🅱️ Khởi chạy LTX-2.5 Studio

Mô hình LTX-2.5 yêu cầu [Hugging Face Access Token](https://huggingface.co/settings/tokens) (loại `Read`) và cần được cấp quyền tại [Lightricks/LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5).

1. **Chạy qua Notebook:** Mở trực tiếp [LTX_2_5_MSR_Colab.ipynb](ltx/LTX_2_5_MSR_Colab.ipynb).
2. **Hoặc chạy từng lệnh:**
   ```bash
   python ltx/ltx2_5_msr.py
   ```

---

## 💻 Yêu cầu phần cứng (Hardware Requirements)

| Cấu hình | MiniMax H3 (Int8/FP4) | LTX-2.5 (Int8 Distilled) |
| :--- | :--- | :--- |
| **GPU tối thiểu** | NVIDIA T4 16GB *(chế độ fp4 AWQ)* | NVIDIA T4 16GB *(bật Low VRAM)* |
| **GPU khuyến nghị** | **L4 24GB** hoặc **A100 40GB/80GB** | **L4 24GB** hoặc **A100 40GB/80GB** |
| **Dung lượng ổ đĩa** | ~50GB trống | ~60GB trống |
| **Hệ thống** | Google Colab / Linux / Windows WSL2 | Google Colab / Linux / Windows WSL2 |

---

## 📜 Giấy phép (License)

Dự án này được phát hành theo giấy phép mã nguồn mở **[MIT License](LICENSE)**.

- Trọng số mô hình **LTX-2.5** tuân thủ theo giấy phép của **Lightricks Ltd.** ([Lightricks LTX-2.5 License](https://huggingface.co/Lightricks/LTX-2.5)).
- Trọng số mô hình **MiniMax H3** tuân thủ theo điều khoản của **MiniMax / Comfy-Org** ([MiniMax Terms](https://huggingface.co/Comfy-Org/MiniMax-H3)).

---

## 🙏 Lời cảm ơn & Tham khảo (Acknowledgements)

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) bởi Comfy Anonymous.
- [MiniMax H3](https://huggingface.co/Comfy-Org/MiniMax-H3) bởi MiniMax & Comfy-Org.
- [lightx2v](https://huggingface.co/lightx2v/Minimax-h3-Turbo) cho các checkpoint Turbo LoRA chất lượng cao.
- [Practical-RIFE](https://github.com/hzwer/Practical-RIFE) cho thuật toán nội suy khung hình thời gian thực.
- [Lightricks LTX-2.5](https://github.com/Lightricks/LTX-Video) cho mô hình video nền tảng 22B.
