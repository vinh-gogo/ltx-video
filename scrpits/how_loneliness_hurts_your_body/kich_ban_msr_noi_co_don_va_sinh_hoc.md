# 🎬 KỊCH BẢN VIDEO KHOA HỌC GIẢI THÍCH: "BẠN CHƯA TỪNG NHẬN RA NỖI CÔ ĐƠN ĐANG PHÁ HỦY CƠ THỂ BẠN NHƯ THẾ NÀO"
> *(Phong cách Hand-drawn 2D Doodle Animation / Sinh học tiến hóa & Thần kinh học)*

- **Thể loại:** Phim tài liệu khoa học giải thích (Educational Science Explainer), Sinh học tiến hóa & Khoa học thần kinh xã hội.
- **Định dạng khung hình:** **16:9 Khung ngang (YouTube Long-form)** hoặc **9:16 (Shorts / Reels)**.
- **Thời lượng:** **11 - 13 phút** (Chia theo từng cảnh 10s hoặc chạy liên tục theo timestamps).
- **Cấu hình tham chiếu:** **Đúng 5 ảnh (4 Nhân vật Doodle + 1 Background)**.
- **Tương thích:** Tối ưu 100% cho `ltx2_5_msr.py` — áp dụng 3 fix: speech ở đầu prompt, bỏ timestamp, character desc khớp ảnh.

---

## 📌 PHẦN 1: MÔ TẢ NHÂN VẬT & BỐI CẢNH (`character_description`)
> *Dán toàn bộ 5 mục bên dưới vào ô **① Mô tả nhân vật — phải khớp với Pic 1/2/3/4 bên trên***

```text
Image 1: Figure 1, The Modern Human: A clean minimalist 2D hand-drawn doodle stick figure with a large round white head, expressive dot eyes and thick black eyebrows, wearing a simple blue t-shirt and dark pants, sitting at a desk or standing, bold black outlines, flat solid color fill, YouTube doodle explainer style.

Image 2: Figure 2, The Ancient Caveman Ancestor: A 2D hand-drawn doodle stick figure wearing a primitive brown fur tunic and holding a wooden torch or spear, round head with rugged thick eyebrows, wild hair, bold black sketchy marker outlines, flat color fill.

Image 3: Figure 3, The Personified Brain and Immune Cell: A cute expressive 2D cartoon pink brain character wearing round scientist glasses, alongside a white blood cell character wearing a red firefighter helmet, bold black outlines, flat solid colors.

Image 4: Figure 4, The Scientist Researcher: A 2D hand-drawn cartoon scientist stick figure in a white lab coat with a stethoscope and clipboard, smart confident expression, bold black outlines, flat colors.

Image 5: Scene, minimalist 2D hand-drawn room interior with a simple wooden desk, chair, window looking out to night sky, flat white background with solid color blocks, zero gradients, zero shadows, clean YouTube explainer style.
```

---

## 📌 PHẦN 2: PROMPT CHÍNH — HÀNH ĐỘNG & KỊCH BẢN 9:16 (`prompt_main`)
> *Dán toàn bộ 18 phân đoạn bên dưới vào ô **② Kịch bản / Prompt chính**. Mỗi phân cảnh cách nhau 1 dòng trống.*
>
> ✅ **Fix đã áp dụng:**
> - **Speech ở đầu câu** — lời thoại xuất hiện ngay frame đầu, KHÔNG dùng `At 00:XX.XXX`
> - **Từ "immediately"** — báo hiệu hành động xảy ra tức thì ngay khi video bắt đầu
> - **Figure rõ ràng** — chỉ đích danh `Figure 1`, `Figure 2` khớp với `Image 1`, `Image 2`

```text
Figure 1 (modern stick figure in blue shirt) immediately sits alone in a quiet room and says Ngay lúc này, khi bạn đang ngồi một mình trong căn phòng yên tĩnh, cơ thể bạn đang kích hoạt một cơ chế sinh tồn cổ xưa. with a subtle pulsating red warning aura around its chest. Hand-drawn 2D doodle cartoon animation, bold black outlines, flat white background, no gradients, no shadows, 16:9 aspect ratio.

Figure 1 (stick figure with drooping sad eyes) immediately looks at a small rain cloud above head and says Bạn nghĩ rằng sự cô đơn chỉ là một trạng thái tâm lý buồn bã thoáng qua. with a thought bubble reading JUST SAD?. Hand-drawn 2D doodle cartoon animation, flat white background, no gradients, 16:9 aspect ratio.

Figure 1 (stick figure) immediately clutches its chest in pain and says Nhưng sâu bên trong từng tế bào, cơ thể bạn đang phản ứng như thể bạn vừa bị một vết thương hở trên da thịt. while Figure 3 (white blood cell in firefighter helmet) immediately pulls a red emergency fire alarm lever labeled CODE RED. Bold red ALL CAPS text at top SAME SIGNAL, flat white background, no gradients, 16:9 aspect ratio.

Figure 2 (caveman stick figure in fur tunic) immediately looks out over an ancient prehistoric savanna and says Để hiểu được điều kỳ lạ này, bạn phải quay ngược thời gian về hai trăm nghìn năm trước trên thảo nguyên châu Phi. standing next to a giant spinning cartoon hourglass. Flat tan background with acacia tree silhouette, bold black outlines, no gradients, 16:9 aspect ratio.

Figure 2 (caveman) and two other tribe members immediately sit closely around a glowing campfire sharing food and say Sự sống còn của bạn phụ thuộc hoàn toàn vào bộ lạc. Bộ lạc là thức ăn, nguồn nhiệt và sự an toàn. with warm smiling faces. Solid orange background, bold black marker outlines, no gradients, 16:9 aspect ratio.

Figure 4 (scientist Dr. Naomi Eisenberger) immediately points to an MRI brain scan monitor and says Bộ não của bạn không hề phân biệt giữa nỗi đau thể xác và nỗi đau bị ruồng bỏ! while the central dACC brain region flashes bright red. Flat solid blue background, bold black outlines, no gradients, 16:9 aspect ratio.

Figure 3 (cartoon brain character with judge glasses) immediately holds up a balanced scale with a broken bone on one side and a lonely heart on the other and says Khi ai đó từ chối bạn, cơ thể bạn thực sự cảm nhận được nỗi đau vật lý có thật. with bold red text HEARTBROKEN at top. Flat white background, no gradients, 16:9 aspect ratio.

Figure 1 (stick figure with spinning red radar dish on head) immediately looks around nervously in the dark and says Khi bạn cô đơn, bộ não chuyển sang trạng thái cảnh giác cao độ hypervigilance, không bao giờ cho phép bạn ngủ sâu. while jagged EEG brainwave graphs flash in the background. Flat dark blue background, no gradients, 16:9 aspect ratio.

Figure 4 (scientist Dr. Steve Cole) immediately points at a microscopic DNA double-helix diagram and says Sự cô đơn kích hoạt gen CTRA, tắt kháng thể chống virus và thổi bùng ngọn lửa viêm mạn tính phá hủy mạch máu và tim mạch. with red inflammation warning indicators. Flat white background, no gradients, 16:9 aspect ratio.

Figure 4 (scientist Dr. Julianne Holt-Lunstad) immediately displays a chart comparing loneliness to smoking and says Nỗi cô đơn kinh niên làm tăng nguy cơ tử vong sớm tương đương với việc hút mười lăm điếu thuốc lá mỗi ngày! with a crossed-out pack of 15 cigarettes. Flat white background, bold black outlines, 16:9 aspect ratio.

Figure 1 (modern stick figure) immediately puts down its smartphone, turns to smile and hug a close friend, and says Cơ thể bạn chỉ cần một hoặc hai kết nối sâu sắc chân thật để giải phóng oxytocin dập tắt hoàn toàn ngọn lửa viêm nhiễm. with a bright glowing yellow heart and smiling happy faces. Flat bright white background, no gradients, 16:9 aspect ratio.

Figure 1 (stick figure) immediately looks directly into the camera with a calm enlightened smile and says Và tối nay, khi bạn lại ngồi một mình trong căn phòng yên tĩnh ấy, bạn sẽ hiểu rằng cơ thể bạn chưa từng yếu đuối, nó chỉ đang tha thiết nhắc nhở bạn tìm đường trở về với đồng loại mà thôi. Locked continuous camera, warm glowing room, flat white background, no gradients, 16:9 aspect ratio.
```

---

## 🎙️ BẢNG CHI TIẾT LỜI THOẠI [SPEECH] & SFX

| Phân đoạn | Nhân vật | Trọng tâm khoa học | Lời thoại [SPEECH] & SFX |
| :--- | :--- | :--- | :--- |
| **Hồi 1: Báo động sinh học** | 👤 **Figure 1 (Modern Human)** | Cơ chế sinh tồn cổ xưa & Báo động khẩn cấp | *(SFX: Tiếng còi báo động xa xăm & Nhịp tim dồn dập)*<br>👤 *"Ngay lúc này, cơ thể bạn đang kích hoạt cơ chế sinh tồn cổ xưa..."* |
| **Hồi 2: Thảo nguyên cổ đại** | 🏹 **Figure 2 (Caveman Ancestor)** | Tiến hóa 200,000 năm & Sự gắn kết bộ lạc | *(SFX: Tiếng lửa trại tí tách & Tiếng dã thú đêm)*<br>🏹 *"Sự sống còn của bạn phụ thuộc hoàn toàn vào bộ lạc..."* |
| **Hồi 3: Thí nghiệm Cyberball** | 🔬 **Figure 4 (Dr. Eisenberger)** | Vùng não dACC & Nỗi đau thể xác | *(SFX: Tiếng máy quét MRI vo ve & Tiếng kim rơi TENG!)*<br>🔬 *"Bộ não không phân biệt giữa nỗi đau thể xác và nỗi đau bị ruồng bỏ!"* |
| **Hồi 4: Giấc ngủ & Đa nghi** | 🧠 **Figure 3 & Figure 1** | Hypervigilance & Phá hủy giấc ngủ sâu | *(SFX: Tiếng đồng hồ tích tắc & Tiếng sóng não rè rè)*<br>🧠 *"Bộ não chuyển sang trạng thái cảnh giác cao độ vô thức..."* |
| **Hồi 5: Gen CTRA & Viêm** | 🧬 **Figure 4 (Dr. Steve Cole)** | Biểu hiện gen CTRA & Viêm mạn tính | *(SFX: Tiếng tim đập dồn dập & Báo động tế bào)*<br>🧬 *"Cơ thể bạn bị nhấn chìm trong ngọn lửa viêm mạn tính..."* |
| **Hồi 6: Tác hại 15 điếu thuốc** | 📊 **Figure 4 (Dr. Holt-Lunstad)**| Tương đương 15 điếu thuốc/ngày & Tử vong sớm | *(SFX: Tiếng còi cứu thương & Tiếng lật biểu đồ)*<br>📊 *"Tác hại của sự cô đơn tương đương hút 15 điếu thuốc lá mỗi ngày!"* |
| **Hồi 7: Liều thuốc giải độc** | ❤️ **Figure 1 (Kết nối chân thật)** | Oxytocin, Endorphin & Bản năng trở về | *(SFX: Tiếng thở phào nhẹ nhõm & Nhạc piano ấm áp)*<br>❤️ *"Cơ thể bạn chưa từng yếu đuối, nó chỉ đang nhắc nhở bạn tìm về với đồng loại."* |

---

## 🚫 PHẦN 3: PROMPT PHỦ ĐỊNH (`negative_prompt`)

```text
blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, compression artifacts, glitches, watermark, text, logo, subtitles, photorealism, 3D render, realistic faces, drop shadows, gradients, realistic textures, anime style, deformed limbs, extra fingers, messy lines, bad anatomy, character switching, sudden morphing
```

---

## 💡 HƯỚNG DẪN GÁN ẢNH THAM KHẢO VÀO CÁC Ô TRÊN GRADIO (CHUẨN 5 ẢNH)

| Ô Upload trong UI | Nhân vật tương ứng (`Image X`) | Gợi ý hình ảnh tải lên |
| :--- | :--- | :--- |
| **🎭 Pic 1 (Bắt buộc)** | `Image 1` — Con người hiện đại (Modern Human) | Stick figure nét vẽ tay marker, đầu tròn trắng, áo thun xanh, mắt chấm tròn |
| **🎭 Pic 2 (Tuỳ chọn)** | `Image 2` — Tổ tiên người tiền sử (Caveman) | Stick figure mặc áo da thú nâu, cầm ngọn đuốc hoặc giáo gỗ |
| **🎭 Pic 3 (Tuỳ chọn)** | `Image 3` — Não bộ & Bạch cầu (Brain & Cell) | Não hoạt hình màu hồng đeo kính cận + Tế bào bạch cầu đội mũ cứu hỏa |
| **🎭 Pic 4 (Tuỳ chọn)** | `Image 4` — Nhà khoa học / Bác sĩ (Scientist) | Stick figure mặc áo blouse trắng, cầm bảng kẹp tài liệu |
| **🌄 Background (Tuỳ chọn)** | `Image 5` — Bối cảnh căn phòng / Thảo nguyên | Nền trắng phẳng hoặc nền cam hoàng hôn thảo nguyên đơn sắc |

---

## ⚙️ THÔNG SỐ KHUYẾN NGHỊ TRÊN GRADIO / LTX-VIDEO (TỐI ƯU DOODLE ANIMATION)

| Thông số | Giá trị | Ghi chú |
| :--- | :--- | :--- |
| **Tỉ lệ khung hình** | `16:9 (1280x720) · HD Ngang` | Hoặc `9:16` nếu render cho Shorts/Reels/TikTok |
| **Thời lượng mỗi cảnh** | `10` giây | Render từng phân cảnh rồi ghép nối hoàn chỉnh |
| **FPS** | `24` fps | Chuyển động hoạt họa mượt mà |
| **MSR LoRA Strength** | `1.0` ⭐ | Giữ nét vẽ doodle và phong cách nhân vật nhất quán |
| **Video CFG** | `2.5` ⭐ | Bám sát kịch bản và khẩu hình lời thoại |
| **Reference Strength** | `0.85` ⭐ | Giữ chuẩn nét vẽ tay 2D không bị biến dạng sang 3D |
| **Reference Frames** | `33` | Mặc định MSR chính thức |
| **Stage 2 (Upscale x2)** | `Bật ✅` | Nâng độ nét lên chuẩn 2K/4K sắc nét từng nét vẽ |
| **Low VRAM Mode** | `Bật ✅` | Bật nếu GPU dưới 24GB |


