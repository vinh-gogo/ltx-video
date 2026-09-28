# 🤝 Hướng Dẫn & Thỏa Thuận Cấp Phép Người Đóng Góp (Contributing Guide & CLA)

Cảm ơn bạn đã quan tâm và muốn đóng góp cho dự án! Tài liệu này quy định **Thỏa thuận cấp phép người đóng góp (Contributor License Agreement - CLA)**, **Chứng nhận nguồn gốc nhà phát triển (DCO)** và quy trình đóng góp nhằm bảo đảm tính pháp lý, minh bạch và an toàn cho cộng đồng nguồn mở.

---

## 📜 1. Thỏa Thuận Cấp Phép Đóng Góp (Contributor License Agreement - CLA)

Khi gửi bất kỳ đóng góp nào (mã nguồn, tệp kịch bản, ảnh tham chiếu, workflow JSON, tài liệu) qua Pull Request hoặc Issue vào kho lưu trữ này, bạn đồng ý với các điều khoản sau:

### 1.1. Cấp phép theo giấy phép MIT (Grant of License)
- Mọi đóng góp của bạn vào dự án sẽ tự động được cấp phép theo giấy phép mã nguồn mở **[MIT License](LICENSE)** của dự án.
- Bạn cấp cho dự án và người dùng toàn cầu quyền vĩnh viễn, miễn phí bản quyền, không hủy ngang để sử dụng, sao chép, sửa đổi, phân phối, tích hợp và xuất bản nội dung đóng góp của bạn.

### 1.2. Chứng nhận nguồn gốc nhà phát triển (Developer Certificate of Origin - DCO 1.1)
Bằng việc tạo commit hoặc gửi Pull Request, bạn cam kết rằng:
1. Đóng góp hoàn toàn do chính bạn tự tay tạo ra (toàn bộ hoặc một phần); HOẶC
2. Bạn có quyền hợp pháp từ tác giả gốc để cấp phép nội dung đó theo điều khoản MIT; HOẶC
3. Nội dung dựa trên các tài liệu công cộng, mã nguồn mở có giấy phép tương thích hoàn toàn với MIT License.

### 1.3. Tuân thủ bản quyền mô hình AI (Model Compliance)
- Đóng góp liên quan đến **LTX-2.5** phải tuân thủ điều khoản sử dụng của **[Lightricks Ltd.](https://huggingface.co/Lightricks/LTX-2.5)**.
- Đóng góp liên quan đến **MiniMax H3** phải tuân thủ điều khoản của **[MiniMax / Comfy-Org](https://huggingface.co/Comfy-Org/MiniMax-H3)**.
- Không đóng góp dữ liệu huấn luyện hoặc ảnh tham chiếu xâm phạm quyền hình ảnh cá nhân (Deepfake) hoặc nội dung nhạy cảm, vi phạm pháp luật.

---

## 🛠️ 2. Các Lĩnh Vực Có Thể Đóng Góp

Chúng tôi hoan nghênh mọi đóng góp thuộc các mảng sau:

| Khu vực | Thư mục | Nội dung đóng góp |
| :--- | :--- | :--- |
| **Mã nguồn MiniMax H3** | `minimax/` | Tối ưu bộ giải mã VAE, node ComfyUI mới, cải tiến script RIFE hoặc giao diện Gradio. |
| **Mã nguồn LTX-2.5** | `ltx/` | Cải tiến Prompt Enhancer, IC-LoRA Ingredients, cơ chế ghép nối nhiều phân cảnh. |
| **Workflow ComfyUI** | `workflow/` | Các tệp JSON workflow tối ưu cho render nhanh, upscale 4K hoặc tạo audio. |
| **Kịch bản & MSR Data** | `scripts/` | Kịch bản phim ngắn hoàn chỉnh kèm bộ ảnh tham chiếu chuẩn MSR `<Picture 1>` – `<Picture 4>`. |
| **Tài liệu & Bản dịch** | `README.md` | Sửa lỗi chính tả, dịch thuật đa ngôn ngữ, bổ sung hướng dẫn chạy trên phần cứng khác. |

---

## 🚀 3. Quy Trình Gửi Đóng Góp (Contribution Workflow)

1. **Fork kho lưu trữ:** Nhấn nút **Fork** ở góc phải trên cùng của trang GitHub.
2. **Tạo nhánh tính năng (Feature Branch):**
   ```bash
   git checkout -b feature/ten-tinh-nang-moi
   ```
3. **Thực hiện thay đổi & Kiểm tra kỹ:**
   - Đảm bảo code chạy không lỗi cú pháp: `python -m py_compile <file.py>`
   - Đặt tên file và thư mục theo tiếng Anh chuẩn, không dấu, dùng dấu gạch dưới `_` hoặc gạch ngang `-`.
4. **Cam kết thay đổi (Commit):**
   Tuân theo quy ước **Conventional Commits**:
   - `feat:` Thêm tính năng, kịch bản hoặc workflow mới.
   - `fix:` Sửa lỗi mã nguồn hoặc lỗi liên kết.
   - `docs:` Cập nhật tài liệu, README.
   - `refactor:` Tái cấu trúc thư mục hoặc dọn dẹp mã nguồn.
5. **Đẩy lên GitHub & Tạo Pull Request:**
   ```bash
   git push origin feature/ten-tinh-nang-moi
   ```
   Mở trang GitHub và nhấn **Compare & pull request**, mô tả chi tiết những gì bạn đã thay đổi.

---

## 🤝 4. Quy Tắc Ứng Xử (Code of Conduct)

- Tôn trọng, hòa nhã và mang tính xây dựng khi thảo luận tại Issues và Pull Requests.
- Sẵn sàng hỗ trợ và giải thích khi các thành viên khác đặt câu hỏi hoặc yêu cầu phản hồi code review.
- Kiên quyết bài trừ các hành vi quấy rối, ngôn từ thù địch hoặc xúc phạm danh dự của bất kỳ ai.

---

*Nếu bạn có bất kỳ thắc mắc nào về thỏa thuận này, vui lòng mở một Issue trên GitHub để được giải đáp.*
