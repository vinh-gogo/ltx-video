# 🎬 BỘ KỊCH BẢN MẪU CHO MINIMAX H3 STUDIO (REFERENCE-TO-VIDEO)
> File điều khiển tương ứng: `minimax.py` (sử dụng model **MiniMax H3 ref2va** tích hợp Native Stereo Audio)

---

## 📌 QUY TẮC CỐT LÕI KHI VIẾT KỊCH BẢN CHO MINIMAX H3

1. **Tag ảnh tham khảo (`ref_images`):**
   - Ảnh nạp vào ô **Pic 1 (Bắt buộc)** ➔ trong prompt gọi là `<Picture 1>`
   - Ảnh nạp vào ô **Pic 2 (Tuỳ chọn)** ➔ trong prompt gọi là `<Picture 2>`
   - Ảnh nạp vào ô **Pic 3 (Tuỳ chọn)** ➔ trong prompt gọi là `<Picture 3>`
   - *Lưu ý: Luôn dùng đúng định dạng `<Picture X>` để model khóa danh tính nhân vật / bối cảnh.*

2. **Native Audio & Lời thoại (Speech + SFX + BGM):**
   - MiniMax H3 sinh cả video và audio stereo đồng bộ trong cùng một forward pass (không cần ghép audio ngoài).
   - Mô tả lời thoại trực tiếp trong ngoặc kép: `"Hello world!"`.
   - Mô tả rõ: tông giọng (confident, terrified, cheerful...), hiệu ứng âm thanh SFX (explosion, laser beam, footstep...), và nhạc nền (cinematic drums, synthwave, violin...).

3. **Cơ chế phân cảnh tự động (Multi-scene chaining & Auto-concat):**
   - Trong `minimax.py`, mỗi phân cảnh cách nhau bằng **1 dòng trống** (`Enter 2 lần`).
   - Hệ thống sẽ render từng cảnh (mỗi cảnh dài theo slider thời lượng `5s - 15s`) rồi tự động dùng `ffmpeg` ghép nối liền mạch thành 1 video dài hoàn chỉnh!

---

## 🎬 KỊCH BẢN 1: SIÊU ANH HÙNG VS MECH KAIJU (SCI-FI ACTION CINEMATIC)

- **Thể loại:** Hành động viễn tưởng, kịch tính, phong cách Comic / Cinematic Blockbuster
- **Tỉ lệ khung hình khuyến nghị:** `16:9 (1344x768)`
- **Thời lượng:** 3 phân cảnh × 6 giây = **18 giây**
- **Gán ảnh tham khảo:**
  - **🎭 Pic 1:** Siêu anh hùng thiếu niên hoặc chiến binh áo choàng đỏ
  - **🎭 Pic 2:** Quái thú robot khổng lồ (Black Mech Kaiju)
  - **🎭 Pic 3:** Toàn cảnh thành phố đêm ngập tràn ánh đèn neon và khói lửa

### 📝 Prompt dán vào ô kịch bản:
```text
Bold cinematic comic-book film style, heavy dramatic linework, high contrast volumetric lighting, red and blue-black color palette, epic Hollywood orchestral battle music. Use <Picture 1> as the young superhero on the rooftop, <Picture 2> as the colossal enemy mech kaiju towering over the skyline, and <Picture 3> as the burning night city environment.

Close-up shot of <Picture 1> standing heroically on the edge of the skyscraper rooftop, rain dripping down his face and his red cape fluttering violently in the howling wind. <Picture 1> smirks with intense confidence, looks directly into the camera lens and delivers his line with a loud, defiant voice: "Get ready to meet your maker!" The camera slowly pushes in on his face as deep thunder rumbles in the stormy sky.

Low-angle hero view looking up at <Picture 2> towering over the skyscraper rooftops. Its glowing red mechanical eyes flare blindingly bright, and blue electrical lightning arcs across its dark steel armor. <Picture 2> rears back its horned head and unleashes a terrifying, ear-shattering mechanical roar: "ROAAARRRR!" The roar creates a visible sonic shockwave through the fog, sending dust and sparks rattling against surrounding windows, heavy subwoofer bass vibrations booming.

Fast-paced cinematic action cut. <Picture 1> charges glowing plasma energy into his hands and leaps forward off the roof directly toward camera with extreme velocity. Loud rushing wind sound effect, energetic escalating taiko battle drums, ending with a massive cinematic impact explosion sound as plasma beams strike the mech in a blinding burst of white and red sparks.
```

---

## 🎬 KỊCH BẢN 2: HOẠT HÌNH 3D PIXAR / CUTE ANIMAL HEIST (HÀI HƯỚC, CÓ THOẠI)

- **Thể loại:** Hoạt hình 3D Pixar/Disney, hài hước, siêu dễ thương
- **Tỉ lệ khung hình khuyến nghị:** `9:16 (768x1344)` (Dọc TikTok/Reels) hoặc `16:9 (1344x768)`
- **Thời lượng:** 3 phân cảnh × 6 giây = **18 giây**
- **Gán ảnh tham khảo:**
  - **🎭 Pic 1:** Chú mèo mướp vàng béo đội nón đầu bếp (Chef Cat)
  - **🎭 Pic 2:** Chú chó Corgi đeo khăn đỏ hoặc chú chuột nhắt háu ăn
  - **🎭 Pic 3:** Gian bếp gia đình ấm cúng với tủ lạnh mở hé sáng rực

### 📝 Prompt dán vào ô kịch bản:
```text
Vibrant 3D Pixar animation style, warm cozy lighting, soft ambient glow, whimsical cartoon orchestral music with playful acoustic strings. Use <Picture 1> as the chubby chef cat character, <Picture 2> as the clumsy dog partner, and <Picture 3> as the warm midnight kitchen environment.

Medium shot inside <Picture 3>. <Picture 1> stands on a stool, proudly stirring a giant simmering soup pot with a wooden spoon, aromatic steam swirling up. <Picture 1> takes a deep breath, smiles with sparkling eyes, and speaks in a cute, cheerful voice: "Mmm! The secret midnight dessert is finally perfection!" Whimsical violin melody, bubbling pot sound effects, and pleasant culinary ambience.

Camera cuts low to the tile floor. <Picture 2> slides out from behind the refrigerator corner, mouth wide open and tongue lolling out in excitement. <Picture 2> accidentally slips on a banana peel, shouting comically in panic: "Look out belowwww, I can't stop!" Funny cartoon slide-whistle sound effect as <Picture 2> skids across the shiny kitchen floor toward the camera, crashing into a stack of soft pillows with a gentle thud.

Wide comedic shot. <Picture 1> freezes in absolute shock with enlarged round eyes, wooden spoon dropping to the counter with a loud clatter. Both characters turn their heads simultaneously toward the lens as the bright ceiling light clicks on with a sharp "CLICK!". <Picture 1> raises his furry paws innocently and whispers nervously: "Uh-oh... we are totally busted!" Comedic trombone wah-wah sound effect and cute cartoon laughter.
```

---

## 🎬 KỊCH BẢN 3: KIẾM HIỆP / TIÊN HIỆP HUYỀN ẢO (WUXIA / FANTASY DUEL)

- **Thể loại:** Cổ trang, kiếm hiệp, huyền ảo phương Đông, đậm chất điện ảnh
- **Tỉ lệ khung hình khuyến nghị:** `16:9 (1344x768)`
- **Thời lượng:** 3 phân cảnh × 7 giây = **21 giây**
- **Gán ảnh tham khảo:**
  - **🎭 Pic 1:** Bạch y kiếm khách (Kiếm tông áo trắng thanh thoát)
  - **🎭 Pic 2:** Hắc y ma tôn (Chiến binh áo đen quyền năng hắc ám)
  - **🎭 Pic 3:** Rừng trúc mù sương hoặc đỉnh núi tuyết mây vần

### 📝 Prompt dán vào ô kịch bản:
```text
Cinematic wuxia fantasy aesthetic, ethereal mist, floating fallen leaves, atmospheric chiaroscuro lighting, traditional Chinese guzheng and bamboo flute melody blended with heavy battle drums. Feature <Picture 1> as the graceful white-robed swordsman, <Picture 2> as the formidable dark warrior, and <Picture 3> as the misty bamboo forest setting.

Slow elegant tracking shot through <Picture 3>. <Picture 1> steps forward gently upon bamboo leaves without making a sound, white silk robes billowing gracefully in the mountain breeze. <Picture 1> slightly pulls his silver sword an inch from its scabbard, releasing a soft metallic chime, and speaks in a serene, cold voice: "Ten years in seclusion... this blade has waited long enough." Wind whistling through bamboo stems and gentle chime sound effects.

Close-up tracking shot on <Picture 2> standing surrounded by swirling dark smoke and glowing purple embers. <Picture 2> suddenly draws a massive jagged dark broadsword that slices the air with a heavy whoosh, laughing darkly: "Then let us see if your blade can pierce my shadow!" Dark ethereal bass vibrations resonate, accompanied by crackling dark lightning sound effects as tension escalates.

Explosive action shot. Both <Picture 1> and <Picture 2> leap into the air at blinding speed, clashing their blades mid-air. A blinding radiant flash of silver and purple sword qi bursts outward, scattering bamboo leaves in all directions. Sharp ringing metal clang sound, thunderous shockwave boom, and intense escalating cinematic percussion.
```

---

## 🎬 KỊCH BẢN 4: COMMERCIAL / THỜI TRANG LUXURY (CINEMATIC PRODUCT)

- **Thể loại:** Quảng cáo thương mại cao cấp, TVC thời trang / mỹ phẩm / phụ kiện
- **Tỉ lệ khung hình khuyến nghị:** `16:9 (1344x768)` hoặc `9:16 (768x1344)`
- **Thời lượng:** 3 phân cảnh × 5 giây = **15 giây**
- **Gán ảnh tham khảo:**
  - **🎭 Pic 1:** Người mẫu thời trang (High-fashion model với makeup sắc sảo)
  - **🎭 Pic 2:** Sản phẩm sang trọng (Chai nước hoa cao cấp, đồng hồ hoặc túi xách)
  - **🎭 Pic 3:** Sảnh triển lãm kiến trúc hiện đại tối giản hoặc phố đêm Paris

### 📝 Prompt dán vào ô kịch bản:
```text
High-end commercial aesthetic, shot on 35mm cinema lens, elegant shallow depth of field, silky smooth bokeh, modern downtempo electronic music with deep sub-bass and atmospheric synths. Feature <Picture 1> as the runway fashion model, <Picture 2> as the luxury signature perfume bottle, and <Picture 3> as the minimalist marble showroom.

Slow-motion medium shot of <Picture 1> walking gracefully across the polished reflective floor in <Picture 3>. Gentle breeze lifts her hair, ambient studio warm spotlights highlighting her jawline and silk dress. <Picture 1> gazes calmly into the lens, smooth electronic synth pads swelling gently in the background with subtle high-heel acoustic echo.

Extreme close-up macro beauty shot of <Picture 2> resting upon a black obsidian pedestal. A beam of golden light slowly pans across the crystal glass surface, revealing liquid amber reflections and fine engraved lettering. Crisp metallic click sound as perfume mist sprays into the air with a soft delicate hiss, shimmering light particles dancing in slow motion.

Glamour medium close-up. <Picture 1> holds <Picture 2> near her neck, breathing in the scent with a subtle, confident smile. She whispers smoothly toward the camera: "Define your own essence." Bass drops into a warm final chord, camera gently glides backwards into a soft fade out.
```

---

## ⚙️ BẢNG THÔNG SỐ KHUYẾN NGHỊ TRÊN GRADIO UI (`minimax.py`)

| Thông số | Giá trị khuyên dùng | Mục đích & Giải thích |
| :--- | :--- | :--- |
| **Aspect Ratio** | `16:9 (1344x768)` hoặc `9:16 (768x1344)` | 1344x768 là độ phân giải chuẩn 768p (0.98 MP) của MiniMax H3. Dùng `864x480` nếu máy yếu. |
| **Duration (Thời lượng)** | `5` đến `8` giây / cảnh | Đủ cho 1 câu thoại + diễn biến hành động tự nhiên. |
| **FPS** | `24` | Cố định chuẩn điện ảnh của MiniMax H3. |
| **Scheduler** | `beta` | Tối ưu tốt nhất cho tác vụ có ảnh tham khảo (`ref2va`). |
| **Turbo LoRA (4-step)** | `Bật` khi test nhanh, `Tắt` khi render chính | Bật giúp render cực nhanh (~1-2 phút/cảnh). Tắt để render nét căng với 20 steps. |
| **ref_image_size** | `match` hoặc `max` | `match` render nhanh hơn. `max` giữ chi tiết nét đến 2048px (tốt cho cận cảnh khuôn mặt). |
| **Low VRAM Mode** | `Bật ✅` | Giải phóng VRAM giữa các bước, hạn chế crash CUDA OOM trên Colab. |
