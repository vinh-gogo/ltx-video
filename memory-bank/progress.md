# Progress — AI Video Studio: LTX-2.5 & MiniMax H3

> Theo dõi tiến độ phát triển, các tính năng đã hoàn thiện và lộ trình tương lai.

## 1. Tính năng đã hoàn thành (Completed Milestones)

### A. Module MiniMax H3 (`minimax/`)
- [x] **Cell 1 (`download.py`):** Tải tự động ComfyUI, custom nodes cần thiết, model VAE `int8_convrot`, Turbo LoRA (8-step & 4-step), Text Encoders Qwen3-VL 32B (`int8` / `fp4 AWQ`).
- [x] **Cell 2 (`minimax.py`):** Server ComfyUI tự động kiểm tra port, giải phóng socket, khởi chạy background process an toàn, và mount Gradio Live WebUI.
- [x] **Hỗ trợ Multi-Subject Reference (MSR - `ref2va`):** Tải lên tối đa 4 ảnh tham chiếu (`<Picture 1>` đến `<Picture 4>`), khóa chặt nhận diện nhân vật và background.
- [x] **Hỗ trợ Image-to-Video (I2V - `fl2va`):** Tạo video từ First Frame hoặc nội suy First-Last Frame.
- [x] **Native Stereo Audio:** Tạo đồng thời âm thanh và video trong 1 pass, đồng bộ tự nhiên giữa hình ảnh và âm thanh.
- [x] **Cell 3 (`rife_postprocess.py`):** RIFE v4.26 Standalone Post-Processor, tăng tốc độ khung hình từ 24fps lên 48fps (2x) hoặc 96fps (4x), hỗ trợ slow-motion và remux giữ nguyên âm thanh stereo.
- [x] **Notebooks Colab:** Hoàn thành [`MiniMax_H3_MSR_Colab.ipynb`](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/minimax/MiniMax_H3_MSR_Colab.ipynb) và [`MiniMax_H3_MSR_I2V_Colab.ipynb`](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/minimax/MiniMax_H3_MSR_I2V_Colab.ipynb).

### B. Module LTX-2.5 (`ltx/`)
- [x] **Studio đa chế độ (`ltx2_5.py`):** Hỗ trợ Text-to-Video (T2V), Image-to-Video (I2V), First-Last Frame (FLF).
- [x] **Quy trình 2-Stage Denoising:** Giai đoạn 1 phác thảo ở 1/2 độ phân giải, nâng cấp qua Latent Spatial Upscaler x2, giai đoạn 2 hoàn thiện chi tiết sắc nét.
- [x] **Storyboard Chaining:** Tự động trích xuất frame cuối của cảnh trước để làm frame đầu của cảnh sau, hỗ trợ 3 chế độ bám nhân vật (Smooth, Strict, Periodic).
- [x] **Prompt Enhancer:** Tích hợp mô hình Gemma để tự động làm giàu câu nhắc thành mô tả điện ảnh.
- [x] **MSR Studio (`ltx2_5_msr.py`):** Khóa nhận dạng 4 nhân vật + 1 bối cảnh bằng IC-LoRA và PromptRelay.
- [x] **Notebook Colab:** Hoàn thành [`LTX_2_5_MSR_Colab.ipynb`](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/ltx/LTX_2_5_MSR_Colab.ipynb).

### C. Mẫu Kịch bản & Tài nguyên (`scripts/`)
- [x] Kịch bản phim tài liệu thiên nhiên (01: Bướm Vua, 02: Ếch Thủy Tinh).
- [x] Kịch bản khoa học viễn tưởng (03: Kính Tương Lai Genesis Scan).
- [x] Kịch bản hài tình huống (04: Statue Prank, Animal Midnight Snack Heist).
- [x] Kịch bản tâm lý học chuyên sâu (Nỗi cô đơn, Thao túng tâm lý nơi công sở).
- [x] Bộ ảnh mẫu tham chiếu chuẩn tỉ lệ 16:9 cho từng nhân vật và môi trường.

### D. Tài liệu & Quy chuẩn Dự án
- [x] [README.md](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/README.md) chi tiết cấu trúc repo, hướng dẫn cài đặt và tối ưu hóa VRAM.
- [x] [CONTRIBUTING.md](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/CONTRIBUTING.md) với Contributor License Agreement (CLA) và quy trình đóng góp.
- [x] [LICENSE](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/LICENSE) (MIT).
- [x] Hệ thống tài liệu [memory-bank/](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/memory-bank/).

---

## 2. Kế hoạch phát triển tiếp theo (Future Roadmap)
- [ ] **Batch Storyboard Processing:** Tự động render toàn bộ danh sách phân cảnh từ file markdown kịch bản mà không cần sao chép từng prompt thủ công.
- [ ] **Voice Cloning Integration:** Tích hợp thêm các node TTS tuỳ biến (F5-TTS, CosyVoice) cho các dự án cần giọng lồng tiếng đặc thù theo mẫu người dùng.
- [ ] **Direct Export to Cloud Drive:** Tự động sao lưu video kết quả và checkpoint sang Google Drive khi chạy trên Colab.
