# Active Context — AI Video Studio: LTX-2.5 & MiniMax H3

> Trạng thái hiện tại của dự án, các thay đổi gần nhất, và các bước tiếp theo.

## 1. Trọng tâm hiện tại (Current Focus)
- Đã hoàn thiện cấu trúc mã nguồn phân tách rõ ràng thành các thư mục chuyên biệt:
  - `ltx/`: Các công cụ và notebook cho Lightricks LTX-2.5.
  - `minimax/`: Các công cụ và notebook cho MiniMax H3 (kèm RIFE post-processor).
  - `workflow/`: Lưu trữ các file JSON mẫu workflow ComfyUI.
  - `scripts/`: Kho kịch bản và dataset mẫu MSR cho các thể loại khác nhau (phim tài liệu động vật, tâm lý học, viễn tưởng, hài hước).
  - `memory-bank/`: Hệ thống tài liệu quản lý bộ nhớ và tri thức của dự án.
- Bổ sung tài liệu đóng góp chuẩn mực [CONTRIBUTING.md](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/CONTRIBUTING.md) với Contributor License Agreement (CLA).
- Đảm bảo tính tương thích của Gradio UI trên cả phiên bản mới (Gradio 6.0+) và môi trường Google Colab.

## 2. Các thay đổi gần đây (Recent Changes)
- **Cập nhật MiniMax H3 Workflow:** Hỗ trợ Turbo LoRA 4-step/8-step và tải model VAE `int8_convrot` tiết kiệm 46% VRAM.
- **Tích hợp RIFE Post-Processor:** Viết module `rife_postprocess.py` độc lập hoàn toàn, hỗ trợ nội suy video 24fps lên 48fps/96fps và giữ nguyên audio stereo.
- **Bổ sung kịch bản mẫu chất lượng cao trong `scripts/`:**
  - `01/`: Kịch bản phim tài liệu Bướm Vua (Monarch Butterfly) 5 phút + ảnh tham chiếu 3 góc độ 16:9.
  - `02/`: Kịch bản Ếch Thủy Tinh (Glass Frog) 3 phút + ảnh chi tiết nội tạng và kẻ săn mồi.
  - `03/`: Kịch bản Kính Tương Lai (The Genesis Scan).
  - `04/`: Meme Statue Prank 30s + video thành phẩm kiểm nghiệm.
  - `how_loneliness_hurts_your_body`: Kịch bản tâm lý học giải phẫu nỗi cô đơn.
  - `minimax_h3`: Kịch bản siêu anh hùng & hành vi học kết hợp prompt audio tự nhiên.
  - `msr_midnight_snack_heist`: Kịch bản hài động vật (Mèo đầu bếp, Corgi, Raccoon, Hamster) cùng video render thực tế.
  - `phim_HD`: Thần thú thượng cổ tiên giới.
  - `psychology`: Thao túng tâm lý công sở (Gaslighting) với 4 nhân vật thú và nhiều video thành phẩm.
- **Nâng cấp hồ sơ CV kỹ sư (`cv_tieng_viet.tex`):** Tích hợp dự án chính thức [Open Video Lab](https://github.com/vinh-gogo/open-video-lab) vào vị trí Dự án Tiêu biểu số 1, nhấn mạnh điểm mạnh sinh video đa phương thức theo yêu cầu (T2V, I2V, First/Last Frame, MSR, A2V) và tối ưu hóa Low-VRAM.

## 3. Kế hoạch tiếp theo (Immediate Next Steps)
1. **Kiểm thử trên Colab mới:** Xác thực quy trình chạy từ đầu đến cuối trên Google Colab với GPU T4 và L4 cho cả hai notebook MiniMax và LTX.
2. **Đồng bộ hóa Preset Thông số:** Thêm các preset cấu hình nhanh trong giao diện Gradio (e.g., *Fast Draft*, *Cinematic HD*, *Ultra Smooth*).
3. **Mở rộng hỗ trợ Webhook / Queue:** Cho phép xếp hàng nhiều prompt tạo video liên tiếp trong chế độ Storyboard không giám sát.
