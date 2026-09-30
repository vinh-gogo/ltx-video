# 🎬 KỊCH BẢN VIDEO MEME (30 GIÂY): TƯỢNG PHẬT "NÉM ĐÁ GIẤU TAY" [LTX-2.5 MSR EDITION]

> **Hệ thống mục tiêu:** LTX-2.5 MSR (`ltx/ltx2_5_msr.py` / ComfyUI LTX-2.5 MSR Studio)  
> **Định dạng khung hình:** **9:16 Dọc (Vertical Video 720x1280)** — Tối ưu cho TikTok / Facebook Reels / YouTube Shorts  
> **Thời lượng:** 30 Giây (Ghép nối liền mạch tự động bằng ffmpeg)  
> **Ảnh tham khảo đầu vào:** [vinh.jpg](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/scripts/04/vinh.jpg), [pic1_young_man.jpg](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/scripts/04/pic1_young_man.jpg), [pic2_stone_buddha.jpg](file:///C:/Users/lea26/OneDrive/Desktop/CLAUDE/code/scripts/04/pic2_stone_buddha.jpg)

---

## 📸 HƯỚNG DẪN GÁN ẢNH THAM KHẢO VÀO GIAO DIỆN MSR LTX

Trong giao diện Gradio (`python ltx/ltx2_5_msr.py`), tại khu vực **📸 Ảnh tham khảo nhân vật / bối cảnh**:

| Ô Upload trong UI | Tương ứng trong Prompt | File ảnh sử dụng | Vai trò nhận diện |
| :--- | :--- | :--- | :--- |
| **🎭 Pic 1 - Nhân vật 1 (bắt buộc)** | `Image 1` / `Figure 1` | `scripts/04/pic1_young_man.jpg` | Nam thanh niên áo thun trắng chữ Uncover, quần cargo túi hộp, đứng khấn trên mỏm đá |
| **🎭 Pic 2 - Nhân vật 2 (tuỳ chọn)** | `Image 2` / `Figure 2` | `scripts/04/pic2_stone_buddha.jpg` | Tượng Phật đá khổng lồ khắc trên vách núi granite, tóc ốc xoắn, nét mặt trang nghiêm |
| **🎭 Pic 3 - Nhân vật 3** | *(Để trống)* | — | Không sử dụng |
| **🎭 Pic 4 - Nhân vật 4** | *(Để trống)* | — | Không sử dụng |
| **🌄 Background - Bối cảnh (tuỳ chọn)**| `Image 5` / Scene | `scripts/04/vinh.jpg` | Khung cảnh toàn cảnh vách núi đá hiểm trở, mỏm đá tiền cảnh và hẻm núi |

> 💡 **Tại sao cần cắt thành Pic 1 và Pic 2 từ `vinh.jpg`?**  
> LTX-2.5 MSR gán learned embedding riêng cho từng slot nhân vật (`Pic 1` = Người, `Pic 2` = Tượng). Việc tách riêng giúp AI không bị nhầm lẫn giữa cơ thể người thật và chất liệu đá của tượng Phật, tránh hoàn toàn lỗi mặt người hóa đá hoặc tượng bị biến dạng thành người!

---

## 📌 PHẦN 1: MÔ TẢ NHÂN VẬT & BỐI CẢNH (`msr_relay_desc`)
> *Copy toàn bộ đoạn bên dưới dán vào ô: **① Mô tả nhân vật — phải khớp với Pic 1/2/3/4 bên trên***

```text
Image 1: A young Asian man in his early 20s with short black hair, viewed from behind and side. He is wearing an oversized white streetwear short-sleeved t-shirt with colorful typographic 'UNCOVER' prints across the back in red, orange, and blue letters, paired with loose olive-brown khaki cargo pants with large utility side pockets. He stands on a rocky mountain ledge with hands clasped together in sincere prayer, bowing his head slightly, natural skin tone, athletic realistic build.

Image 2: A colossal ancient Buddha statue carved directly into a steep vertical granite mountain cliff face. The stone statue features traditional snail-shell curly hair nodules, a calm serene stone-chiseled face with closed or half-closed eyelids, elongated sculpted earlobes, and ancient weathered grey-brown stone robes engraved into the cliff with natural rainwater streaks and cracks across the stone texture.

Image 5: Scene, vertical 9:16 composition, a rugged quarry cliffside mountain on an overcast misty day. In the foreground, an elevated rugged rock ledge overlooking a deep rocky chasm and sparse green bushes clinging to the cliffs. In the background, a massive towering vertical stone cliff face under a soft overcast sky, natural cinematic daylight, sharp photorealistic mountain texture.
```

---

## 🚫 PHẦN 2: PROMPT PHỦ ĐỊNH (`negative_prompt`)
> *Copy toàn bộ đoạn bên dưới dán vào ô: **🚫 Negative Prompt***

```text
blurry, oversaturated, pixelated, low resolution, grainy, distorted, noise, compression artifacts, glitches, watermark, text, logo, subtitles, static frame, frozen image, standing still, lack of motion, deformed limbs, extra paws, duplicate limbs, distorted face, character switching, sudden character change, wrong character, inconsistent character identity, different person, character replacement, morphing face, mid-shot camera cut, sudden transition, ignored prompt, temporal inconsistency, jittery motion, flickering texture, strobing, bad anatomy, clipping, floating limbs, melting body, moving camera, panning, zoom, shaky cam
```

---

## 📌 PHẦN 3: PROMPT KỊCH BẢN CHÍNH (`msr_prompt`)
> *Dán vào ô **② Kịch bản / Prompt chính (mỗi phân cảnh cách nhau 1 dòng trống)***

### 🎯 Tùy Chọn A (Khuyến nghị cho nhịp Meme): 6 Cảnh × 5 Giây = 30 Giây
*(Cài đặt slider: **Thời lượng MỖI cảnh = 5 giây**)*

```text
Figure 1 (young man in white t-shirt and cargo pants) stands on the foreground rocky ledge bowing deeply with hands clasped in sincere prayer with eyes closed. Taking advantage of Figure 1 lowered head, Figure 2 (colossal carved stone Buddha on the cliff) subtly comes to life: its stone eyes flick sideways toward Figure 1, and one giant stone hand stealthily picks up a small pebble from the cliff edge and conceals it in its stone palm. Locked-off continuous vertical 9:16 shot, fixed camera, natural daylight, no cuts.

Figure 2 (colossal carved stone Buddha on the cliff) immediately flicks the stone pebble through the air toward Figure 1, and the microsecond the pebble leaves its fingers, Figure 2 instantly snaps back into a completely motionless, inanimate ancient stone carving with a flat serene face. The pebble hits the back of Figure 1 head. Figure 1 immediately jolts up, clutching the back of his neck in surprise and spins to stare at the cliff, seeing only a 100% frozen sacred stone statue. Locked-off continuous vertical 9:16 shot, zero camera movement.

Figure 1 (young man in white t-shirt and cargo pants) immediately turns his back 180 degrees away from the cliff to search the lower rocky slope and bushes below, scratching his head in confusion. The instant Figure 1 looks away, Figure 2 (colossal carved stone Buddha on the cliff) immediately comes alive again, smirking mischievously at the camera, tilting its massive stone head to peek at Figure 1 back, and slyly plucks a second pebble from the rock face. Locked-off continuous vertical 9:16 shot, no camera motion.

Figure 2 (colossal carved stone Buddha on the cliff) immediately tosses the second pebble in an arc, hitting Figure 1 square on the back. A split-second before Figure 1 whips around, Figure 2 instantly withdraws its stone arm behind the rock ledge and freezes into eternal stone immobility, innocently gazing straight ahead with neutral stone lips. Figure 1 turns around furiously glaring at the cliff wall, finding only an ancient monolithic rock carving. Fixed locked-off vertical 9:16 shot, no camera cuts.

Figure 1 (young man in white t-shirt and cargo pants) immediately steps forward toward the cliff, squinting and intensely scrutinizing Figure 2 face looking for any movement. Figure 2 (colossal stone Buddha) maintains a flawless, totally rigid stone poker face without flinching. Defeated, Figure 1 sighs and turns his gaze away to the left. The exact fraction of a second Figure 1 looks away, Figure 2 rapidly winks directly at the camera lens with a cheeky stone grin, then instantly freezes solid again. Locked-off vertical 9:16 shot, stationary camera.

Figure 1 (young man in white t-shirt and cargo pants) immediately throws both hands up in the air in complete comedic defeat and exasperation, shaking his head and sighing. While Figure 1 looks down at the ground, Figure 2 (colossal stone Buddha) subtly flashes a triumphant, smug grin toward the camera before settling back into eternal peaceful stone meditation. Locked-off vertical 9:16 shot, comedic meme freeze-frame ending, zero camera movement.
```

---

### 🎯 Tùy Chọn B (Chuẩn Mặc Định LTX): 3 Phân Đoạn × 10 Giây = 30 Giây
*(Cài đặt slider: **Thời lượng MỖI cảnh = 10 giây**)*

```text
Figure 1 (young man in white t-shirt and cargo pants) stands on the foreground rocky ledge with hands clasped bowing in sincere prayer with eyes closed. Taking advantage of the blind spot, Figure 2 (colossal carved stone Buddha on the cliff) immediately comes to life, flicks its stone eyes sideways, grabs a small pebble and flicks it toward Figure 1. The microsecond the pebble leaves its fingers, Figure 2 instantly freezes back into a motionless ancient rock carving. The pebble bonks the back of Figure 1 head; Figure 1 jolts up clutching his neck, staring at the cliff in utter confusion, seeing only a totally frozen sacred statue. Locked-off continuous vertical 9:16 shot, fixed camera, no cuts.

Figure 1 (young man in white t-shirt and cargo pants) immediately turns around 180 degrees away from the cliff searching the lower rocky slope. The moment Figure 1 back is turned, Figure 2 (colossal stone Buddha) immediately comes alive again, smirking mischievously at the camera, plucks a second pebble and tosses it, hitting Figure 1 square on the back. A split-second before Figure 1 furiously whips back around, Figure 2 has already frozen into solid granite stone posture, innocently gazing forward with a blank sacred face as Figure 1 inspects the cliff in paranoia. Locked-off continuous vertical 9:16 shot, no camera motion.

Figure 1 (young man in white t-shirt and cargo pants) immediately steps forward, squinting intensely at Figure 2 face to catch it moving. Figure 2 maintains an unyielding stone poker face. Baffled and giving up, Figure 1 sighs and looks away; the precise millisecond Figure 1 looks away, Figure 2 winks boldly at the camera with a playful smirk, then instantly freezes before Figure 1 glances back. Figure 1 throws both arms up in total comedic exasperation as Figure 2 flashes a smug victorious grin at the camera. Locked-off continuous vertical 9:16 shot, hilarious meme freeze-frame ending, no camera movement.
```

---

## 🎶 GỢI Ý ÂM NHẠC & SFX MEME (KHI HẬU KỲ CAPCUT)

| Cảnh | Âm nhạc (Music) | Hiệu ứng âm thanh (SFX) |
| :--- | :--- | :--- |
| **Cảnh 1** | Nhạc rón rén hoạt hình ("Monkeys Spinning Monkeys") | Tiếng gió núi hiu hiu, tiếng đá trượt xào xạc |
| **Cảnh 2** | Nhạc ngắt đột ngột khi bị trúng đá | Tiếng "BONK!" cốc vào đầu + tiếng vịt cao su "squeak" |
| **Cảnh 3** | Nhạc rón rén vui nhộn tiếp tục, tiếng còi trượt slide whistle | Tiếng sỏi lạo xạo dưới giày + tiếng cười khúc khích lén |
| **Cảnh 4** | Tiếng sáo rơi vút xuống nhanh | Tiếng ném "PLINK!" trúng lưng + hiệu ứng kịch tính "Vine Boom" |
| **Cảnh 5** | Tiếng dế kêu ngượng ngùng lúc soi xét | Tiếng "Huh?!" hoang mang + tiếng lấp lánh "Bling!" khi tượng nháy mắt |
| **Cảnh 6** | Kèn trombone thất bại hài hước ("Sad Trombone: Wah-wah-wah-waaaah") | Tiếng bass "Bruh" sâu lắng lúc freeze frame |

---

## ⚙️ THÔNG SỐ CÀI ĐẶT KHUYẾN NGHỊ TRÊN GRADIO MSR LTX

| Thông số | Giá trị khuyến nghị | Mục đích |
| :--- | :--- | :--- |
| **Tỉ lệ khung hình (Ratio)** | `9:16 (720x1280) · HD 720p Dọc` | Chuẩn video ngắn dọc TikTok/Reels |
| **Thời lượng MỖI cảnh** | `5` giây (Tùy chọn A) hoặc `10` giây (Tùy chọn B) | Tự động ghép thành video 30s |
| **FPS** | `24` | Chuẩn điện ảnh mượt mà |
| **Seed** | `-1` (ngẫu nhiên) hoặc chọn số yêu thích | Giữ `fixed_seed_msr = False` |
| **MSR LoRA Strength** | `1.0` ⭐ | Khuyến nghị để giữ tượng đá và trang phục cố định |
| **Video CFG** | `2.5` ⭐ | Bám sát hành động và nhịp độ prompt |
| **Reference Strength** | `0.85` ⭐ | Giữ chặt nhân vật, hạn chế đổi mặt |
| **Reference Frames** | `33` | Mặc định MSR chính thức |
| **Stage 2 (Upscale x2)** | `Bật ✅` | Đạt độ sắc nét 720p chi tiết vách đá |
| **Low VRAM Mode** | `Bật ✅` (nếu GPU < 24GB) | Tiết kiệm bộ nhớ chống OOM |
