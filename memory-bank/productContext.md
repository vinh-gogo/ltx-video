# Product Context — AI Video Studio: LTX-2.5 & MiniMax H3

> Bối cảnh sản phẩm, vấn đề cần giải quyết, đối tượng người dùng và trải nghiệm tương tác.

## 1. Vấn đề thực tế (Problem Statement)
- **Thiếu tính nhất quán giữa các cảnh quay:** Trong các công cụ tạo video AI truyền thống, việc giữ nguyên khuôn mặt, trang phục, hoặc kiểu dáng nhân vật qua từng đoạn cắt (shot) rất khó khăn. Mỗi prompt sinh ra một nhân vật hoàn toàn khác.
- **Tạo âm thanh rời rạc, lệch pha:** Hầu hết mô hình AI video chỉ sinh hình ảnh câm. Người sáng tạo phải dùng các công cụ TTS và sound effect riêng rồi ghép nối thủ công, dẫn tới khẩu hình không khớp và âm thanh môi trường thiếu tự nhiên.
- **Tiêu tốn tài nguyên và thời gian render lâu:** Các mô hình diffusion video cỡ lớn (22B+) đòi hỏi phần cứng cực mạnh và mất hàng chục phút cho vài giây video nếu không được tối ưu hóa VRAM và số bước lấy mẫu (sampling steps).
- **Phức tạp khi sử dụng ComfyUI:** Giao diện node ComfyUI tuy mạnh mẽ nhưng phức tạp, khó tiếp cận với người sáng tạo nội dung không chuyên về kỹ thuật.

## 2. Giải pháp của hệ thống (Solution)
- **Multi-Subject Reference (MSR):** Cho phép người dùng tải lên từ 1 đến 4 ảnh tham chiếu (`<Picture 1>` đến `<Picture 4>`) và gọi tên trực tiếp trong câu nhắc để khóa chặt nhận dạng nhân vật và bối cảnh.
- **Omni-Modal Audio-Visual:** Sử dụng MiniMax H3 để tạo đồng thời video 768p và âm thanh stereo (thoại + tiếng động + nhạc nền) trong cùng 1 pass inference.
- **Tối ưu hóa đa tầng:**
  - Tích hợp Turbo LoRA (4-step / 8-step) giảm thời gian sinh video xuống còn dưới 1 phút.
  - Lượng tử hóa mô hình sang `int8_convrot` và `fp4 AWQ`, giảm 46% VRAM.
  - Tiled VAE Decoding giúp tránh lỗi Out-Of-Memory (OOM).
- **Giao diện Gradio WebUI hiện đại (Gradio 6.0+):** Ẩn toàn bộ độ phức tạp của ComfyUI phía sau backend, cung cấp giao diện web trực quan với các tab điều khiển rõ ràng, slider điều chỉnh thông số và preview tức thì.
- **Tự động ghép nối Storyboard & Làm mượt:** Tự động ghép nối các cảnh liên tiếp bằng FFmpeg và nâng FPS lên 48fps/96fps bằng RIFE AI.

## 3. Đối tượng sử dụng (User Personas)
- **Content Creators / YouTubers / TikTokers:** Cần sản xuất video ngắn, phim tài liệu, hoặc video hoạt hình với nhân vật cố định.
- **Storytellers & Biên kịch:** Cần chuyển đổi kịch bản chữ (scripts) thành các đoạn phim mẫu (pre-visualization).
- **AI Researchers & Prompt Engineers:** Thử nghiệm các kỹ thuật prompting điện ảnh, MSR và tối ưu hóa diffusion pipeline.
