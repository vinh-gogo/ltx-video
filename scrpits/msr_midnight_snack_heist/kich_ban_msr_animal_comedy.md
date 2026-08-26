# 🎬 KỊCH BẢN VIDEO HÀI HƯỚC 9:16 (TIKTOK / REELS / SHORTS): "ĐẠI NÁO TỦ LẠNH LÚC NỬA ĐÊM"

- **Thể loại:** Hài hước, siêu dễ thương (Cute & Comedy Animal Animation), chuẩn hoạt hình 3D Pixar/Disney
- **Định dạng khung hình:** **9:16 Khung dọc (Vertical Video)** — Tối ưu cho TikTok, Facebook Reels, YouTube Shorts
- **Thời lượng:** 30 giây (3 phân đoạn × 10s, tự ghép nối)
- **Tương thích:** Tối ưu chuẩn cho `ltx2_5_msr.py` — áp dụng 3 fix: speech ở đầu prompt, bỏ timestamp, character desc khớp ảnh

---

## 📌 PHẦN 1: MÔ TẢ NHÂN VẬT & BỐI CẢNH (`character_description`)
> *Dán toàn bộ đoạn tiếng Anh bên dưới vào ô **① Mô tả nhân vật — phải khớp với Pic 1/2/3/4 bên trên***
>
> ⚠️ **Quy tắc bắt buộc:** `Image 1` mô tả chính xác nhân vật trong **Pic 1**, `Image 2` mô tả **Pic 2**, v.v. Mô tả càng chi tiết (màu lông, trang phục, đặc điểm) → AI giữ nhân vật càng chính xác.

```text
Image 1: A chubby orange tabby cat with thick fluffy ginger fur, round amber eyes, white whiskers, pink nose, wearing a miniature white chef hat tilted on its head and a tiny white apron. Pixar-style 3D cartoon character, photorealistic render quality.

Image 2: A tri-color Corgi puppy with large perky ears, short stubby legs, golden and white fluffy fur, happy smiling face with tongue out, wearing a tiny red bandana tied around its neck. Pixar-style 3D cartoon character, photorealistic render quality.

Image 3: A chubby raccoon with natural black eye mask markings, grey fur with dark stripes on bushy tail, delicate dexterous paws, holding a small wooden spoon. Pixar-style 3D cartoon character, photorealistic render quality.

Image 4: A tiny fluffy golden Syrian hamster with puffed-up round cheeks, shiny black bead eyes, soft golden fur, standing on its hind legs looking alert. Pixar-style 3D cartoon character, photorealistic render quality.

Image 5: Scene, vertical 9:16 composition, cozy home kitchen at night, soft moonlight streaming through window, tall stainless steel refrigerator with door slightly ajar and warm interior light spilling out, cinematic warm lighting, 4k.
```

---

## 📌 PHẦN 2: PROMPT CHÍNH — HÀNH ĐỘNG & KỊCH BẢN 9:16 (`prompt_main`)
> *Dán toàn bộ 3 phân đoạn bên dưới vào ô **② Kịch bản / Prompt chính**. Mỗi phân cảnh cách nhau 1 dòng trống.*
>
> ✅ **Fix đã áp dụng:**
> - **Speech ở đầu câu** — lời thoại xuất hiện ngay frame đầu, KHÔNG dùng `At 00:XX.XXX`
> - **Từ "immediately"** — báo hiệu hành động xảy ra tức thì ngay khi video bắt đầu
> - **Figure rõ ràng** — chỉ đích danh `Figure 1`, `Figure 2` khớp với `Image 1`, `Image 2` trong mô tả nhân vật

```text
Figure 1 (orange tabby cat chef) immediately taps a wooden spoon on the counter and meows loudly saying 'Nghe đây! Tối nay đội mình đột kích tủ lạnh. Mục tiêu: bánh phô mai, tầng hai, góc trái. Không để lại bằng chứng. Phát!' with an animated open mouth and commanding eyes. In the lower background, Figure 2 (corgi puppy) and Figure 3 (raccoon) immediately nod and begin sneaking forward across the kitchen floor toward the refrigerator. Continuous vertical locked shot, cozy midnight kitchen, no camera cut, consistent character appearance throughout.

Figure 2 (corgi puppy with red bandana) immediately shouts 'Ôi TRỜI ƠI trơn vậy trời— AHHHH! Ai cứu tui vớiiiiii mà!!!' with mouth wide open as it slides forward on the kitchen tile floor after slipping on a butter wrapper. Figure 3 (raccoon) holds a giant cheesecake slice near the open refrigerator in the background. Figure 2 slides rapidly toward the camera and crashes into a stack of pudding cups at the bottom frame. Dynamic vertical tracking shot, continuous take, no cuts, consistent character fur and bandana throughout.

Figure 1 (orange tabby cat chef) immediately looks up into the camera with wide guilty blinking amber eyes and says 'Ơ... Sen đi ngủ chưa ạ? Tụi này đang... kiểm tra hạn sử dụng bánh thôi ạ. Vì sức khoẻ của Sen đó ạ.' while sitting next to a half-eaten cheesecake on the kitchen floor, mouth still smeared with cream. Figure 2 (corgi puppy) freezes beside Figure 1 with pudding on its nose. Overhead kitchen light suddenly blazes on bright white. Locked continuous vertical high-angle shot, consistent character appearance, no scene cuts.
```

---

## 🎙️ BẢNG CHI TIẾT LỜI THOẠI [SPEECH] TIẾNG VIỆT (DÙNG ĐỂ THU ÂM / LỒNG TIẾNG CAPCUT / TTS)
> 🎯 **Quy tắc 1 Speaker / Shot:** Mỗi shot 10s chỉ có **1 nhân vật nói duy nhất** để âm thanh, khẩu hình và hình ảnh hoàn toàn ăn khớp.
>
> ✅ **Fix SPEECH timing:** Lời thoại xuất hiện **ngay frame đầu** nhờ đặt "immediately says/shouts" ở đầu prompt — không còn bị đẩy về cuối video.

| Shot / Phân đoạn | Nhân vật phát ngôn | Giọng điệu & Hành động | Lời thoại [SPEECH] |
| :--- | :--- | :--- | :--- |
| **Shot 1**<br>*(10 giây)* | 🐱 **Figure 1 (Mèo Đầu Bếp)** | Gõ thìa chỉ huy — nghiêm như sếp tổng<br>Figure 2 & 3 gật đầu bò đi ngay | *(SFX: Cộc cộc cộc)*<br>🐱 *"Nghe đây! Tối nay đội mình đột kích tủ lạnh. Mục tiêu: bánh phô mai, tầng hai, góc trái. Không để lại bằng chứng. Phát!"*<br>*(SFX: Tiếng chân rón rén)* |
| **Shot 2**<br>*(10 giây)* | 🐶 **Figure 2 (Chó Corgi)** | Trượt ngay từ đầu — hét như bị bắt cóc<br>Lao thẳng vào camera như tàu hoả | *(SFX: Kẽo kẹt mở tủ lạnh)*<br>🐶 *"Ôi TRỜI ƠI trơn vậy trời— AHHHH! Ai cứu tui vớiiiiii mà!!!"*<br>*(SFX: Tiếng trượt dài & Xoảng xoảng BỤP!)* |
| **Shot 3**<br>*(10 giây)* | 🐱 **Figure 1 (Mèo Đầu Bếp)** | Nhìn thẳng camera — mặt dày 100%<br>Mồm vẫn dính kem, phân trần không chớp mắt | *(SFX: Chẹp chẹp nhai ngấu nghiến)*<br>*(SFX: Tách — Đèn bật trắng trưng)*<br>🐱 *"Ơ... Sen đi ngủ chưa ạ? Tụi này đang... kiểm tra hạn sử dụng bánh thôi ạ. Vì sức khoẻ của Sen đó ạ."*<br>*(SFX: Tiếng dế kêu / quạ kêu)* |

---

## 🚫 PHẦN 3: PROMPT PHỦ ĐỊNH (`negative_prompt`)
> *Dán vào ô **Negative Prompt*** (đã cập nhật theo fix character consistency)

```text
blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, compression artifacts, glitches, watermark, text, logo, subtitles, static frame, frozen image, standing still, lack of motion, deformed limbs, extra paws, duplicate limbs, distorted face, character switching, sudden character change, wrong character, inconsistent character identity, different person, different animal, character replacement, morphing face, mid-shot camera cut, sudden transition, ignored prompt
```

---

## 💡 HƯỚNG DẪN GÁN ẢNH THAM KHẢO VÀO CÁC Ô TRÊN GRADIO

| Ô Upload trong UI | Nhân vật tương ứng (`Image X`) | Gợi ý hình ảnh tải lên |
| :--- | :--- | :--- |
| **🎭 Pic 1 (Bắt buộc)** | `Image 1` — Mèo mướp vàng béo (Chef Cat) | Ảnh rõ mặt & toàn thân mèo vàng 3D đội nón đầu bếp + tạp dề |
| **🎭 Pic 2 (Tuỳ chọn)** | `Image 2` — Chó Corgi lùn (Corgi Puppy) | Ảnh Corgi 3D đeo khăn bandana đỏ, rõ tai to |
| **🎭 Pic 3 (Tuỳ chọn)** | `Image 3` — Gấu mèo Raccoon (Snack Bandit) | Ảnh Raccoon 3D cầm thìa gỗ, rõ vằn đuôi |
| **🎭 Pic 4 (Tuỳ chọn)** | `Image 4` — Chuột Hamster má phúng | Ảnh Hamster 3D má tròn xoe đứng 2 chân |
| **🌄 Background (Tuỳ chọn)** | `Image 5` — Bếp đêm | Ảnh phòng bếp có tủ lạnh phát sáng (tỉ lệ dọc 9:16) |

---

## ⚙️ THÔNG SỐ KHUYẾN NGHỊ TRÊN GRADIO (TỐI ƯU 9:16)

| Thông số | Giá trị | Ghi chú |
| :--- | :--- | :--- |
| **Tỉ lệ khung hình** | `9:16 (720x1280) · HD 720p Dọc` | Hoặc `480x832` nếu GPU < 24GB |
| **Thời lượng mỗi cảnh** | `10` giây | 3 cảnh × 10s = 30s tự ghép |
| **FPS** | `24` | |
| **MSR LoRA Strength** | `1.0` ⭐ | Tăng từ 0.85 → giữ nhân vật chặt hơn |
| **Video CFG** | `2.5` ⭐ | Tăng từ 1.5 → bám prompt & speech tốt hơn |
| **Reference Strength** | `0.85` ⭐ | Tăng từ 0.7 → ít bị đổi nhân vật ở Stage 2 |
| **Reference Frames** | `33` | Mặc định MSR chính thức |
| **Stage 2 (Upscale x2)** | `Bật ✅` | Stage 2 giờ giữ nguyên msr_strength (không giảm nữa) |
| **Low VRAM Mode** | `Bật ✅` | Bắt buộc với GPU < 24GB |

> 💡 **Nếu nhân vật vẫn bị đổi**: Tăng **Reference Strength** lên `0.9–1.0` và **LoRA Strength** lên `1.1–1.2`.
> 💡 **Nếu video bị artifact/cứng**: Giảm **Video CFG** xuống `2.0` và **Reference Strength** xuống `0.75`.


---

## 📌 PHẦN 1: MÔ TẢ NHÂN VẬT & BỐI CẢNH (`character_description`)
> *Dán toàn bộ đoạn tiếng Anh bên dưới vào ô **① Mô tả nhân vật (character_description)***

```text
Image 1: A real chubby orange tabby cat with authentic fluffy ginger fur, sharp amber eyes, white whiskers, pink nose, wearing a miniature white chef hat gently placed on its head, sitting upright on a table looking at the camera, photorealistic 8k DSLR pet photography, cinematic lighting.

Image 2: A real cute tri-color Corgi puppy with large perky ears, short stubby legs, fluffy soft fur, happy smiling face with tongue out, wearing a tiny red bandana around its neck, photorealistic high-detail pet photography.

Image 3: A real curious chubby raccoon with natural black eye mask markings, delicate dexterous paws, bushy striped tail, holding a small wooden spoon, photorealistic wildlife photography, natural fur texture.

Image 4: A real tiny fluffy golden Syrian hamster with puffed-up round cheeks, shiny black bead eyes, soft golden fur, standing on its hind legs, photorealistic macro photography.

Image 5: Scene, vertical 9:16 composition, authentic cozy home kitchen at night, soft moonlight streaming through the window onto the floor, tall stainless steel refrigerator door slightly ajar with warm interior light spilling out, cinematic realistic warm lighting, 4k resolution.
```

---

## 📌 PHẦN 2: PROMPT CHÍNH - HÀNH ĐỘNG & KỊCH BẢN 9:16 (`prompt_main`)
> *Dán toàn bộ 3 phân đoạn bên dưới vào ô **② Prompt chính (hành động / kịch bản)**. Quy tắc: **Mỗi Shot chỉ có 1 nhân vật phát ngôn chính** và **khóa góc quay liên tục (no camera cuts/no morphing)** giúp AI không bao giờ bị tự động chuyển cảnh hay lẫn lộn giọng nói giữa nhân vật A và B.*

```text
[Shot 1 - 00:00 to 00:10 | The Infiltration Plan]
Continuous vertical shot in cozy midnight kitchen, locked focus on Figure 1 (the chubby orange cat in miniature chef hat) sitting upright on the counter. Figure 1 taps a wooden spoon and meows animatedly with expressive mouth movement, giving tactical orders. In the lower background on the floor, Figure 2 (the corgi puppy) and Figure 3 (the raccoon) nod obediently and sneak forward in stealth. Consistent character identity, continuous single camera take, no morphing, no mid-shot cut.
[SPEECH - Cat]: "Mục tiêu: Bánh phô mai tầng hai! Triển khai đội hình báo thủ mau!"

[Shot 2 - 00:10 to 00:20 | The Golden Heist & The Slip]
Continuous dynamic vertical tracking shot focused on Figure 2 (the corgi puppy). Near the open glowing refrigerator, Figure 3 (the raccoon) pulls a giant cheesecake slice. Excited, Figure 2 (the corgi) rushes forward, slips on a dropped butter wrapper on the tile floor, and slides rapidly straight down toward the camera with mouth wide open shouting in comedic panic, crashing into a stack of pudding cups. Consistent character focus on Figure 2, continuous tracking, no cuts.
[SPEECH - Corgi]: "Né ra cho em... Ái trơn quá! Cứu em vớiii!"

[Shot 3 - 00:20 to 00:30 | The Sweet Victory & Caught Red-Handed]
Continuous vertical high-angle shot: On the kitchen floor, Figure 1 (the cat) and Figure 2 (the corgi) messily feast on cheesecake and pudding. Suddenly, the overhead kitchen light clicks on bright white. All animals instantly snap their heads up and freeze, with Figure 1 looking straight up into the camera with wide guilty blinking eyes, nervously talking and making excuses. Locked continuous camera framing, consistent character appearance, no scene cuts.
[SPEECH - Cat]: "Ủa Sen... tụi tao đang dọn bếp hộ mày thôi mà!"
```

---

## 🎙️ BẢNG CHI TIẾT LỜI THOẠI [SPEECH] TIẾNG VIỆT (DÙNG ĐỂ THU ÂM / LỒNG TIẾNG CAPCUT / TTS)
> 🎯 **Quy tắc 1 Speaker / Shot:** Mỗi shot 10s chỉ có **1 nhân vật nói duy nhất** để âm thanh, khẩu hình và hình ảnh hoàn toàn ăn khớp, không bị AI nhảy góc máy sang nhân vật khác.

| Shot / Phân đoạn | Thời điểm chính xác | Nhân vật phát ngôn | Giọng điệu & Hành động | Lời thoại [SPEECH] (Duy nhất 1 nhân vật nói) |
| :--- | :--- | :--- | :--- | :--- |
| **Shot 1**<br>*(10 giây)* | `00:00 - 00:02`<br>`00:02 - 00:07`<br>`00:07 - 00:10` | 🐱 **Figure 1 (Mèo Đầu Bếp)** | Gõ thìa chỉ huy trên bàn cao<br>Nghiêm nghị, hách dịch ra lệnh<br>Corgi & Raccoon gật đầu bò đi | *(SFX: Cộc cộc cộc)*<br>🐱 *"Mục tiêu: Bánh phô mai tầng hai! Triển khai đội hình báo thủ mau!"*<br>*(SFX: Tiếng chân rón rén lén lút)* |
| **Shot 2**<br>*(10 giây)* | `00:10 - 00:13`<br>`00:13 - 00:18`<br>`00:18 - 00:20` | 🐶 **Figure 2 (Chó Corgi)** | Raccoon mở tủ lấy bánh kem<br>Corgi trượt vỏ bơ hét thất thanh<br>Tông đổ pudding xoảng xoảng | *(SFX: Kẽo kẹt mở tủ lạnh)*<br>🐶 *"Né ra cho em... Ái trơn quá! Cứu em vớiii!"*<br>*(SFX: Tiếng trượt dài & Xoảng!)* |
| **Shot 3**<br>*(10 giây)* | `00:20 - 00:24`<br>`00:24 - 00:25`<br>`00:25 - 00:30` | 🐱 **Figure 1 (Mèo Đầu Bếp)** | Cả bọn cắm mặt ăn ngấu nghiến<br>*(SFX: Tách!)* Đèn sáng - Đứng hình<br>Mèo ngước lên camera phân trần | *(SFX: Chẹp chẹp, nhai nhồm nhoàm)*<br>*(SFX: Tách - Bật đèn sáng trưng)*<br>🐱 *"Ủa Sen... tụi tao đang dọn bếp hộ mày thôi mà!"*<br>*(SFX: Tiếng dế kêu / quạ kêu)* |

---

## 🚫 PHẦN 3: PROMPT PHỦ ĐỊNH (`negative_prompt`)
> *Dán vào ô **Negative Prompt***

```text
subtitles, watermark, text, worst quality, blurry, deformed limbs, extra paws, duplicate limbs, distorted face, creepy eyes, jittery movement, dark scary atmosphere, low resolution, bad anatomy, inconsistent character design, morphing, frozen static frame, horizontal black bars, pillarbox, cropped head, landscape layout, mid-shot camera cut, character switching, sudden transition
```

---

## 💡 HƯỚNG DẪN GÁN ẢNH THAM KHẢO VÀO CÁC Ô TRÊN GRADIO

| Ô Upload trong UI | Nhân vật tương ứng | Gợi ý hình ảnh tải lên |
| :--- | :--- | :--- |
| **🎭 Pic 1 (Bắt buộc)** | Mèo mướp vàng béo (Chef Cat) | 1 ảnh chụp rõ mặt & toàn thân mèo vàng 3D đội nón đầu bếp |
| **🎭 Pic 2 (Tuỳ chọn)** | Chó Corgi lùn (Corgi Puppy) | 1 ảnh Corgi 3D đeo khăn bandana đỏ |
| **🎭 Pic 3 (Tuỳ chọn)** | Gấu mèo Raccoon (Snack Bandit) | 1 ảnh Raccoon 3D cầm thìa gỗ |
| **🎭 Pic 4 (Tuỳ chọn)** | Chuột Hamster má phúng phính | 1 ảnh Hamster 3D má tròn xoe |
| **🌄 Background (Tuỳ chọn)**| Nhà bếp ấm cúng ban đêm | 1 ảnh phòng bếp có tủ lạnh phát sáng (tỉ lệ dọc) |

---

## ⚙️ THÔNG SỐ KHUYẾN NGHỊ TRÊN GRADIO (TỐI ƯU 9:16)
- **Tỉ lệ khung hình (Aspect Ratio):** `9:16 (720x1280) · HD 720p Dọc` *(hoặc `9:16 (480x832) · Nhẹ / Tiết kiệm VRAM` nếu chạy GPU thấp)*
- **Thời lượng mỗi lượt (Length):** `10` giây (Chạy 3 phân cảnh tự ghép thành 30s)
- **FPS:** `24`
- **MSR LoRA Strength:** `1.0`
- **Reference Strength:** `0.7` ⭐ *(Mức vàng: giữ đúng nhân vật mà video luôn chuyển động mượt, chống đứng hình/lặp frame)*
- **Reference Frames:** `33`
- **Stage 2 (Upscale x2):** `Bật (Checked)`
- **Low VRAM Mode:** `Bật (Checked)`
