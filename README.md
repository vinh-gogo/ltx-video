# 🎬 LTX-2.5 Video Studio & Multi-Subject Reference (MSR)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Integration-orange.svg)](https://github.com/comfyanonymous/ComfyUI)
[![Gradio](https://img.shields.io/badge/Gradio-UI-orange?logo=gradio)](https://gradio.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-LTX--2.5-ffcc00)](https://huggingface.co/Lightricks/LTX-2.5)

Hệ thống tạo video AI chuyên nghiệp dựa trên mô hình **Lightricks LTX-2.5 (22B)** tích hợp trực tiếp với **ComfyUI Backend** và giao diện **Gradio WebUI**. Hỗ trợ tạo video độ phân giải cao (HD 720p+), kiểm soát tính nhất quán nhân vật qua **IC-LoRA Ingredients**, tạo video dài tự động qua **Multi-Subject Reference (MSR)** và kịch bản nhiều phân cảnh.

---

## 🌟 Điểm nổi bật & Tính năng chính

### 1. ⚡ Tự động hóa cài đặt & Tải Model siêu tốc (`download.py`)
- Cài đặt môi trường cực nhanh qua `uv pip` (nhanh gấp 5-10x so với `pip` thông thường).
- Tải song song đa luồng các checkpoint nặng (~40GB) bằng `aria2c` với cơ chế tiếp tục tải khi đứt mạng (resume).
- Tự động nạp:
  - **Transformer:** `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`
  - **Text Encoder:** `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors`
  - **Text Enhancer:** `gemma4_e2b_it_bf16.safetensors`
  - **VAE:** Video VAE & Audio VAE BF16
  - **Upscaler:** `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors`
  - **LoRA:** IC-LoRA Ingredients (giữ nhân vật/props) & Licon MSR V1 LoRA.

### 2. 🎨 LTX-2.5 AI Video Studio (`ltx2_5.py`)
Giao diện trực quan tích hợp 3 luồng xử lý (Pipelines):
- **🖼️ PIPE 1: Ảnh → Video (I2V) & Text → Video (T2V):** Tạo video chuyển động tự nhiên từ ảnh tĩnh hoặc tạo từ prompt văn bản. Hỗ trợ Prompt Enhancer (Gemma 4), nạp LoRA tùy chỉnh và IC-LoRA Ingredients.
- **🎞️ PIPE 2: Nối 2 Khung Đầu/Cuối (FLF2V) & Âm thanh:** Tạo chuyển động mượt mà giữa khung hình bắt đầu và kết thúc (First-Last-Frame interpolation), tự động đồng bộ âm thanh.
- **🎯 PIPE 3: Storyboard (Phân cảnh liên hoàn):** Tạo chuỗi phân cảnh kịch bản liên tiếp với cơ chế giữ nhất quán bối cảnh/nhân vật qua từng cảnh.

### 3. 🧬 LTX-2.5 MSR Studio - Multi-Subject Reference (`ltx2_5_msr.py`)
- **Đa nhân vật (Tối đa 4 nhân vật + 1 bối cảnh):** Slot `Pic 1` đến `Pic 4` cùng `Background`.
- **Cơ chế PromptRelay:** Tự động map mô tả từng nhân vật (`Image 1: ...`, `Image 2: ...`) với ảnh tham khảo tương ứng qua attention layer.
- **Tự động hóa kịch bản & Nối video:** Nhập kịch bản gồm nhiều phân cảnh (cách nhau bởi dòng trống); hệ thống tự động render tuần tự từng cảnh và ghép nối bằng `FFmpeg` thành video hoàn chỉnh dài 30s, 60s+.

### 4. 🚀 Tối ưu quy trình tạo hình 2-Stage Denoising
- **Stage 1 (Half Res):** Khởi tạo chuyển động và bố cục nhanh chóng ở độ phân giải $1/2$.
- **Spatial Latent Upscale:** Nâng cấp x2 latent resolution.
- **Stage 2 (Refinement):** Khử nhiễu chi tiết và hoàn thiện video ở chuẩn HD sắc nét.

---

## 📁 Cấu trúc thư mục

```text
ltx-video/
├── download.py                         # [Cell 1] Tải model, cài ComfyUI & custom nodes
├── ltx2_5.py                           # [Cell 2] LTX-2.5 Video Studio (T2V, I2V, FLF2V, Storyboard)
├── ltx2_5_msr.py                       # [Cell MSR] MSR Studio (Multi-Subject Reference & Auto Stitched Script)
├── LTX2.5-MSR-sample-workflow.json     # Workflow mẫu ComfyUI cho MSR
├── kich_ban_msr_animal_comedy.md       # Kịch bản mẫu hài hước (Prompt + Lời thoại)
├── msr_pic1_chef_cat.jpg               # Ảnh mẫu: Mèo đầu bếp (Pic 1)
├── msr_pic2_corgi_puppy.jpg            # Ảnh mẫu: Cún Corgi (Pic 2)
├── msr_pic3_raccoon_bandit.jpg         # Ảnh mẫu: Gấu mèo Raccoon (Pic 3)
├── msr_pic4_hamster_agent.jpg          # Ảnh mẫu: Chuột Hamster (Pic 4)
├── msr_bg_midnight_kitchen.jpg         # Ảnh mẫu: Bối cảnh bếp nửa đêm (Background)
├── LICENSE                             # Giấy phép mã nguồn mở MIT
└── README.md                           # Tài liệu hướng dẫn sử dụng
```

---

## 💻 Yêu cầu phần cứng (Hardware Requirements)

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị (Tối ưu) |
| :--- | :--- | :--- |
| **GPU** | NVIDIA GPU 16GB VRAM (T4*) | **24GB+ VRAM** (L4, A100, RTX 3090, RTX 4090) |
| **Hệ thống** | Google Colab Pro / Linux / Windows WSL2 | Google Colab (L4/A100) / Dedicated AI Server |
| **Dung lượng đĩa** | ~60GB trống (Model weights + ComfyUI) | ~100GB SSD NVMe |
| **RAM** | 16GB System RAM | 32GB+ System RAM |

> [!WARNING]
> *Mô hình LTX-2.5 22B + Gemma 4 Text Encoder chiếm tổng cộng ~37GB trọng số. Trên GPU 16GB (như Colab T4), hệ thống sẽ bật Low VRAM mode (offload sang RAM), thời gian render sẽ lâu hơn và có nguy cơ OOM nếu render độ phân giải quá cao. Khuyến khích sử dụng **GPU 24GB VRAM trở lên (L4 hoặc A100)**.*

---

## 🚀 Hướng dẫn sử dụng trên Google Colab

### Bước 1: Chuẩn bị Hugging Face Token (Bắt buộc)
Mô hình **LTX-2.5** và **IC-LoRA Ingredients** được bảo vệ (gated repository). Bạn cần:
1. Đăng ký tài khoản tại [HuggingFace](https://huggingface.co/).
2. Truy cập [Hugging Face Token Settings](https://huggingface.co/settings/tokens) và tạo một **Access Token** (loại `Read`).
3. Truy cập và nhấn **"Agree and access repository"** tại cả 2 repo:
   - [Lightricks/LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5)
   - [Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients](https://huggingface.co/Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients)
4. (Tùy chọn) Thêm token vào **Colab Secrets** với tên `HF_TOKEN` (biểu tượng chiếc chìa khóa 🔑 ở thanh bên trái Colab).

### Bước 2: Chạy Cell 1 - Cài đặt môi trường & Tải Model (`download.py`)
Mở notebook trên Colab và chạy code từ `download.py`:
```python
# Tải và chạy script cài đặt
!python download.py
```
> Script sẽ tự động kiểm tra CUDA, cài đặt ComfyUI, clone các custom nodes cần thiết (`ComfyUI-KJNodes`, `ComfyUI-LTX2.5-MSR`, `ComfyUI-PromptRelay`, v.v.) và tải toàn bộ model qua `aria2c`.

### Bước 3: Khởi chạy Studio

#### Lựa chọn A: Chạy Studio tổng hợp (`ltx2_5.py`)
```python
# Chạy Cell 2: AI Video Studio (I2V / T2V / FLF2V / Storyboard)
!python ltx2_5.py
```
- Click vào đường link Gradio công khai (`https://xxxx.gradio.live`) hoặc link local.
- Chọn tab phù hợp:
  - **PIPE 1:** Tải ảnh lên hoặc nhập prompt mô tả để tạo video.
  - **PIPE 2:** Nạp ảnh đầu & ảnh cuối để tạo chuyển cảnh mượt.
  - **PIPE 3:** Nhập chuỗi storyboard để tạo hoạt cảnh liên hoàn.

#### Lựa chọn B: Chạy Multi-Subject Reference Studio (`ltx2_5_msr.py`)
```python
# Chạy Cell MSR: Tạo phim dài nhiều nhân vật
!python ltx2_5_msr.py
```
1. Tải ảnh nhân vật vào các ô `Pic 1`, `Pic 2`, `Pic 3`, `Pic 4` và ảnh `Background` (có thể dùng ngay bộ ảnh mẫu đi kèm repo).
2. Điền mô tả ngoại hình nhân vật vào mục **① Mô tả nhân vật (`character_description`)**.
3. Nhập kịch bản các phân cảnh vào mục **② Kịch bản / Prompt chính** (mỗi phân cảnh cách nhau 1 dòng trống).
4. Nhấn **🚀 Render toàn bộ kịch bản & Ghép phim**. Hệ thống sẽ tạo lần lượt từng cảnh và tự động ghép nối thành file `.mp4` hoàn chỉnh.

---

## 📝 Ví dụ Kịch bản MSR mẫu

Xem chi tiết trong file [`kich_ban_msr_animal_comedy.md`](kich_ban_msr_animal_comedy.md).

**Mô tả nhân vật (`character_description`):**
```text
Image 1: A real chubby orange tabby cat with authentic fluffy ginger fur, sharp amber eyes, white whiskers, pink nose, wearing a miniature white chef hat gently placed on its head, sitting upright on a table looking at the camera, photorealistic 8k DSLR pet photography, cinematic lighting.

Image 2: A real cute tri-color Corgi puppy with large perky ears, short stubby legs, fluffy soft fur, happy smiling face with tongue out, wearing a tiny red bandana around its neck, photorealistic high-detail pet photography.

Image 3: A real curious chubby raccoon with natural black eye mask markings, delicate dexterous paws, bushy striped tail, holding a small wooden spoon, photorealistic wildlife photography, natural fur texture.

Image 4: A real tiny fluffy golden Syrian hamster with puffed-up round cheeks, shiny black bead eyes, soft golden fur, standing on its hind legs, photorealistic macro photography.

Image 5: Scene, authentic cozy home kitchen at night, soft moonlight streaming through the window onto the floor, large stainless steel refrigerator door slightly ajar with warm interior light spilling out, cinematic realistic warm lighting, 4k resolution.
```

**Kịch bản phân cảnh (`prompt_main`):**
```text
[Shot 1] The chubby orange cat wearing a chef hat taps a wooden spoon on the counter while the hamster listens beside a toy walkie-talkie. The corgi and raccoon sneak near the glowing refrigerator.

[Shot 2] The refrigerator door creaks open with warm golden light. The raccoon reaches for cheesecake while the excited corgi puppy slips on the floor and slides across the room.

[Shot 3] The orange cat catches the cheesecake slice. All four animals feast messily on treats when suddenly the kitchen light turns on and they freeze, looking guilty into the camera.
```

---

## 🛠️ Hướng dẫn cài đặt Local (ComfyUI độc lập)

Nếu bạn muốn chạy trực tiếp trên PC/Workstation có GPU mạnh:

1. **Cài đặt ComfyUI** theo tài liệu chính thức của ComfyUI.
2. **Cài đặt Custom Nodes:**
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/kijai/ComfyUI-KJNodes
   git clone https://github.com/kijai/ComfyUI-PromptRelay
   git clone https://github.com/liconstudio/ComfyUI-LTX2.5-MSR
   git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
   ```
3. **Tải Models:** Đặt các checkpoint vào đúng thư mục tương ứng trong `ComfyUI/models/` (xem chi tiết đường dẫn tại `download.py`).
4. **Nạp Workflow JSON:** Mở ComfyUI Web và kéo thả file [`LTX2.5-MSR-sample-workflow.json`](LTX2.5-MSR-sample-workflow.json) vào giao diện để sử dụng ngay.

---

## ❓ Xử lý sự cố thường gặp (FAQ & Troubleshooting)

### 1. Lỗi HTTP 401 / 403 khi tải model
- **Nguyên nhân:** Chưa nhập đúng `HF_TOKEN` hoặc chưa bấm đồng ý thỏa thuận bản quyền tại repo Hugging Face của Lightricks.
- **Khắc phục:** Truy cập cả 2 đường link ở [Bước 1](#bước-1-chuẩn-bị-hugging-face-token-bắt-buộc), bấm **Agree and access repository**, sau đó chạy lại `download.py`.

### 2. Báo lỗi Out of Memory (CUDA OOM)
- **Khắc phục:** 
  - Chọn tỉ lệ độ phân giải nhẹ hơn (ví dụ: `480x832` thay vì `720x1280`).
  - Giảm thời lượng phân cảnh xuống `5s` hoặc `6s`.
  - Hệ thống tự động kích hoạt tham số `--lowvram` khi phát hiện GPU có VRAM < 24GB.

### 3. Server ComfyUI bị treo hoặc không phản hồi
- Bấm nút **🔄 Restart Server** trực tiếp trên thanh công cụ của Gradio UI để giải phóng VRAM và khởi động lại backend service.

---

## 📜 Giấy phép (License)

Dự án này được phát hành theo giấy phép mã nguồn mở **[MIT License](LICENSE)**.

Trọng số mô hình **LTX-2.5** tuân thủ theo giấy phép của **Lightricks Ltd.** Vui lòng tham khảo điều khoản sử dụng tại [Lightricks LTX-2.5 License](https://huggingface.co/Lightricks/LTX-2.5).

---

## 🙏 Lời cảm ơn & Tham khảo (Acknowledgements)

- [Lightricks](https://github.com/Lightricks) với mô hình tạo video mã nguồn mở đột phá LTX-2.5.
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) bởi Comfy Anonymous.
- [ComfyUI-LTX2.5-MSR](https://github.com/liconstudio/ComfyUI-LTX2.5-MSR) bởi LiconStudio.
- [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) & [ComfyUI-PromptRelay](https://github.com/kijai/ComfyUI-PromptRelay) bởi Kijai.
