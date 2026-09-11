# 🎬 SERIES KỊCH BẢN VIDEO HÀI BỰA TÂM LÝ HỌC 9:16: "108 ANH HÀO TÂM LÝ HỌC CÔNG SỞ"
> *(Phong cách Animal Comedy ẩn dụ hành vi con người - 108 nét tính cách Thủy Hử)*

- **Thể loại:** Hài bựa châm biếm sâu cay (Dark Satirical Animal Comedy), Phim tâm lý học hành vi con người mượn hình tượng động vật siêu biểu cảm.
- **Định dạng khung hình:** **9:16 Khung dọc (Vertical Video)** — Chuẩn Reels, TikTok, YouTube Shorts đỉnh cao.
- **Quy mô Series:** **2 Tập (6 Phút tổng cộng)** = **36 Phân đoạn (Shots) × 10 giây/shot**.
  - **Tập 1 (Part 1):** *Vụ Án Trà Sữa Thiu & Đòn Tâm Lý Chiến* (18 Shots · 180s)
  - **Tập 2 (Part 2):** *Cơn Địa Chấn Tiêu Hóa & Đại Họa Sa Thải* (18 Shots · 180s)
- **Cấu hình tham chiếu:** **Đúng 5 ảnh cố định (4 Nhân vật Động vật + 1 Background)**.
- **Tương thích:** Tối ưu 100% cho `ltx2_5_msr.py` (`ltx-msr.py`) — áp dụng triệt để 3 fix: speech ở đầu prompt (`immediately says/shouts...`), bỏ timestamp, tên nhân vật khớp tuyệt đối `Figure X` & `Image X`.

---

# 🎭 CẤU HÌNH THAM CHIẾU NHÂN VẬT & BỐI CẢNH (DÙNG CHUNG CẢ PART 1 & PART 2)
> *Dán toàn bộ 5 mục bên dưới vào ô **① Mô tả nhân vật (`character_description`)** trên Gradio*

```text
Image 1: Figure 1, The Gaslighter Boss Cat (Tong Giang archetype): A chubby tuxedo British Shorthair cat with sleek dark grey fur, white chest patch, wearing a miniature executive navy blue necktie and small stylish rimless spectacles perched on its nose, cunning calculating amber eyes. Pixar-style 3D cartoon character, photorealistic render quality.

Image 2: Figure 2, The Rageholic Bulldog ID (Ly Quy archetype): A muscular fawn French Bulldog with wrinkled brow, intense fiery eyes, bulging neck veins, wearing a tiny black spiked collar, expressive comedic rage facial expressions. Pixar-style 3D cartoon character, photorealistic render quality.

Image 3: Figure 3, The Paranoid Overthinker Raccoon (Ngo Dung archetype): A skinny curious raccoon with natural black mask markings around eyes, wearing thick round wire-frame reading glasses and a tiny beige knitted cardigan, twitching paws, wide terrified paranoid eyes. Pixar-style 3D cartoon character, photorealistic render quality.

Image 4: Figure 4, The People-Pleaser and Drama Corgi (Lam Xung archetype): A fluffy tri-color Corgi with large expressive perky ears, wearing a tiny crumpled blue office collar and pink bow tie, holding a small notepad, alternating between a tortured polite smile and sharp judgmental side-eye. Pixar-style 3D cartoon character, photorealistic render quality.

Image 5: Scene, vertical 9:16 composition, a cozy modern lounge and meeting room with warm natural lighting, a low rustic wooden coffee table in the center on a soft textured woven rug, surrounded by low comfortable leather poufs, plush armchairs, and a sofa with cushions, cinematic photorealistic interior, 4k resolution.
```

---
---

# 🍿 TẬP 1 (PART 1): "VỤ ÁN TRÀ SỮA THIU & ĐÒN TÂM LÝ CHIẾN"
*(Thời lượng: 180s = 18 Shots × 10s)*

## 📌 PROMPT CHÍNH PART 1 (`prompt_main`)
> *Dán 18 phân đoạn dưới đây vào ô **② Kịch bản / Prompt chính** khi render Tập 1*

```text
Figure 3 (paranoid raccoon with round glasses and beige cardigan) immediately holds up a magnifying glass over an empty boba cup and says Đây không đơn thuần là ly trà sữa bị hút trộm! Đây là một đòn tâm lý chiến nhằm tiêu diệt niềm tin nội bộ! with wild paranoid eyes and twitching paws, adjusting its thick wire glasses frantically. Red strings on the whiteboard loom in the background. Continuous vertical locked shot, cozy meeting room, no camera cut, consistent character appearance throughout.

Figure 1 (tuxedo boss cat with navy necktie and rimless glasses) immediately leans forward with a saintly yet deeply manipulative purr and says Chúng ta là một gia đình... Kẻ trộm trà sữa không có lỗi, lỗi là cả phòng đã không đủ bao dung để chia sẻ! gesturing smoothly with calculated pseudo-empathy, tilting its head and adjusting its rimless spectacles. Stable cinematic lighting, continuous single camera take, no morphing.

Figure 2 (muscular bulldog with spiked collar) immediately slams both front paws violently onto the conference table and roars Bao dung cái con khỉ! Đứa nào uống cạn trân châu hoàng kim của tao? Bước ra đây solo 1 mất 1 còn! with wrinkly face turning red and veins popping, barking straight toward the camera in cartoonish explosive fury. Single locked continuous camera take, expressive comedic rage motion.

Figure 4 (corgi with pink bow tie and blue collar) immediately cowers in its seat hugging a tiny apology notepad with short paws and whines Em xin lỗi cả nhà... Dù em mới đi vệ sinh vào, nhưng chắc chắn là do hào quang tội lỗi của em gây ra! with perky ears drooping down, trembling mouth curled into a tortured polite smile, eyes watery with guilt. Consistent framing, no cuts, natural subtle shivers.

---

Figure 4 (corgi with pink bow tie) immediately perks its ears up and casts a razor-sharp judgmental side-eye across the room, whispering loudly Em không có ý phán xét đâu nha, nhưng ai đó mang tiếng sếp lớn ăn cá hồi mà đi tiếc ly trà sữa 30k thì hơi bần đấy ạ! with a venomous sweet smirk and mock innocence. Sharp cinematic focus, continuous single take.

Figure 1 (tuxedo boss cat) immediately puffs its chest out, swinging its tail pompously and lectures Với tư duy lãnh đạo đỉnh cao của loài mèo, tôi khẳng định đây là bài test tâm lý do ban giám đốc cài vào! raising a paw with supreme baseless confidence, arrogant feline smirk directed at Figure 3 and Figure 2. Smooth locked camera, no morphing.

Figure 3 (paranoid raccoon) immediately grabs two squeaking markers and frantically draws 50 interconnected arrows and pie charts on the whiteboard, tail twitching hysterically, spinning around to face the camera and sputtering Theo ma trận tâm lý tội phạm học: Ly trà sữa bị uống lúc 3h15 phút... trùng khớp với giờ sao Thủy nghịch hành! in sheer existential dread. Continuous tracking take, no cuts.

Figure 1 (tuxedo boss cat) immediately clutches its chest theatrically and squeezes out fake crocodile tears, wailing Các em làm tôi đau lòng quá! Nếu ngày mai công ty phá sản, chính là vì sự ích kỷ của từng người trong phòng này! pointing a claw dramatically around the room while manipulating collective guilt. Consistent character render, no morphing.

Figure 2 (muscular bulldog) immediately collapses onto the floor in absurd sobbing grief, hugging the empty boba cup to its wrinkly cheek and howling Trân châu ơi sao mày bỏ tao đi... Tao đã dặn thêm 70% đường 30% đá mà bọn ác nhân nỡ cướp mất! in hyperbolic tragedy toward the ceiling. Continuous locked camera take.

Figure 4 (corgi) immediately hides a tiny smartphone under the table with its paws, secretly live-streaming the office breakdown while whispering gleefully Alo mạng xã hội ơi! Team em đang đấu tố sinh tử vì ly trà sữa, vào xem drama nghìn mắt xem sếp mèo diễn xiếc nào! eyes glittering with dark joy, stifling mischievous laughter. Continuous single take.

Figure 4 (corgi) immediately snaps and tears the apology notepad to shreds with teeth and paws, eyes wild, screaming Đủ rồi! Tôi nhịn các người suốt 3 năm nay rồi! Tôi không nhận lỗi nữa, tôi nguyền rủa tất cả các người! in glorious psychotic liberation with an unhinged wild toothy grin. Dramatic low lighting, no cuts.

Figure 2 (muscular bulldog) immediately flips sides, clapping front paws and howling Chí lý! Tôi đồng ý với đồng chí Corgi! Khởi nghĩa đi! Lương Sơn Bạc công sở muôn năm! wagging stubby tail wildly, excited and energized by the mutiny. Continuous dynamic take.

Figure 3 (paranoid raccoon) immediately sits on the floor amidst scattered papers, holding its furry head with both paws as its brain short-circuits and stutters Nếu ai cũng là nạn nhân... thì ai là thủ phạm? Trà sữa có thật không hay chỉ là ảo ảnh của tiềm thức?! eyes swirling in dizzy spirals. Continuous single take.

Figure 1 (tuxedo boss cat) immediately freezes as a spotlight hits its face revealing a distinct brown boba syrup stain smeared across its white whiskers and pink nose, stammering nervously Vết... vết này là sốt cá hồi hữu cơ tôi ăn từ sáng... Thề có trời đất chứng giám tôi không hề... with smug look shattering into pure pale shock. Locked continuous take.

Figure 2 (muscular bulldog) immediately points a trembling paw at Figure 1 stained whiskers and shouts Mày bảo Chúng ta là một gia đình... mà mày lại lén hút hết 100% đường của tao hả con mèo kia?! jaw dropping in hyper-dramatic cartoon betrayal shock, whimper cracking between disbelief and heartbreak. Continuous locked framing.

Figure 3 (paranoid raccoon) immediately backs into a corner and dramatically points both paws toward the office refrigerator, chattering frantically Đây rõ ràng là lỗi của phong thủy chiếc tủ lạnh! Chiếc tủ lạnh có tần số năng lượng độc hại phát ra sóng thao túng! attempting absurd psychological projection. Continuous single take.

Figure 4 (corgi) immediately casually kicks a trash bin forward, dusts its paws, and looks straight into the camera with an utterly unimpressed soul-crushing smirk, dropping the bombshell Mà quên chưa nói: Ly trà sữa đó của con bé thực tập để quên từ tuần trước thiu ngắt rồi, anh mèo hút ngon miệng ghê! deadpan and unhurried. Continuous single take.

All 4 animal characters immediately freeze simultaneously as Figure 1 boss cat clutches its churning stomach with wide panicked eyes, immediately looks straight into the camera and announces Tâm lý học hành vi chứng minh rằng: 99% drama trên đời sinh ra từ việc... rảnh rỗi sinh nông nổi! while Figure 2 bulldog and Figure 3 raccoon gag and Figure 4 corgi grins smugly. All slowly turn heads in unison to stare dead-center into the camera with an awkward meme smile. Locked continuous wide shot.
```

---

## 🎙️ BẢNG CHI TIẾT 18 PHÂN ĐOẠN PART 1

| Shot | Nhân vật & Cảm xúc | Thiên kiến tâm lý | Diễn xuất & Body Language | Lời thoại [SPEECH] & SFX |
| :--- | :--- | :--- | :--- | :--- |
| **Shot 1**<br>*(10s)* | 🦝 **Figure 3 (Ngô Dụng Raccoon)** | **Paranoia / Confirmation Bias** | Cầm kính lúp soi ly trà sữa rỗng, vuốt gọng kính run rẩy, mắt trợn trừng | *(SFX: Tim đập dồn dập & Violin hồi hộp)*<br>🦝 *"Đây không đơn thuần là ly trà sữa bị hút trộm! Đây là một đòn tâm lý chiến nhằm tiêu diệt niềm tin nội bộ!"* |
| **Shot 2**<br>*(10s)* | 🐱 **Figure 1 (Tống Giang Boss Cat)** | **Gaslighting / Machiavellianism** | Ngồi ngay ngắn đầu bàn, đẩy kính không gọng, nheo mắt thấu cảm giả tạo | *(SFX: Đàn hạc du dương giả tạo)*<br>🐱 *"Chúng ta là một gia đình... Kẻ trộm trà sữa không có lỗi, lỗi là cả phòng đã không đủ bao dung để chia sẻ!"* |
| **Shot 3**<br>*(10s)* | 🐶 **Figure 2 (Lý Quỳ Bulldog)** | **Primal Aggression (Id Instinct)** | Đập rầm hai chân trước xuống bàn, mặt nhăn tít đỏ bừng, gân cổ nổi cuồn cuộn | *(SFX: RẦM! Còi báo động khẩn cấp)*<br>🐶 *"Bao dung cái con khỉ! Đứa nào uống cạn trân châu hoàng kim của tao? Bước ra đây solo 1 mất 1 còn!"* |
| **Shot 4**<br>*(10s)* | 🦊 **Figure 4 (Corgi Cam Chịu)** | **People-Pleasing / Stockholm** | Tai cụp xuống, hai chân ôm sổ xin lỗi, miệng cười gượng run rẩy, mắt ươn ướt | *(SFX: Tiếng dế kêu thảm thương)*<br>🦊 *"Em xin lỗi cả nhà... Dù em mới đi vệ sinh vào, nhưng chắc chắn là do hào quang tội lỗi của em gây ra!"* |
| **Shot 5**<br>*(10s)* | 💅 **Figure 4 (Corgi Cà Khịa)** | **Passive-Aggressive / Comparison** | Đột ngột dựng thẳng tai, liếc xéo sắc lẹm, nở nụ cười nhếch mép thảo mai | *(SFX: Mèo cào móng & Rắn rít)*<br>💅 *"Em không có ý phán xét đâu nha, nhưng ai đó mang tiếng sếp lớn ăn cá hồi mà đi tiếc ly trà sữa 30k thì hơi bần đấy ạ!"* |
| **Shot 6**<br>*(10s)* | 👑 **Figure 1 (Boss Cat Tự Cao)** | **Dunning-Kruger Effect** | Ưỡn ngực lông trắng phổng phao, giơ một móng vuốt lên chỉ trỏ trịch thượng | *(SFX: Kèn bóp hề Boing Boing)*<br>👑 *"Với tư duy lãnh đạo đỉnh cao của loài mèo, tôi khẳng định đây là bài test tâm lý do ban giám đốc cài vào!"* |
| **Shot 7**<br>*(10s)* | 📊 **Figure 3 (Raccoon Loạn Trí)** | **Analysis Paralysis / Conspiracy** | Cầm 2 bút lông quẹt loạn xạ ma trận trên bảng trắng, thở dốc quay về camera | *(SFX: Bút lông quẹt chói tai & Đèn chớp)*<br>📊 *"Theo ma trận tâm lý tội phạm học: Ly trà sữa bị uống lúc 3h15 phút... trùng khớp với giờ sao Thủy nghịch hành!"* |
| **Shot 8**<br>*(10s)* | 😿 **Figure 1 (Boss Cat Đóng Kịch)** | **Guilt-Tripping / Blackmail** | Lấy chân gạt nước mắt cá sấu, rung râu bi thương, chỉ móng vuốt vào từng đứa | *(SFX: Đàn bầu sầu thảm & Sấm chớp)*<br>😿 *"Các em làm tôi đau lòng quá! Nếu ngày mai công ty phá sản, chính là vì sự ích kỷ của từng người trong phòng này!"* |
| **Shot 9**<br>*(10s)* | 😭 **Figure 2 (Bulldog Than Khóc)** | **Loss Aversion / Grief** | Quỳ sụp xuống, ôm ly trà sữa rỗng áp vào má nhiều nếp nhăn, hú lên trần nhà | *(SFX: Mưa rơi ầm ầm & Nhạc cải lương)*<br>😭 *"Trân châu ơi sao mày bỏ tao đi... Tao đã dặn thêm 70% đường 30% đá mà bọn ác nhân nỡ cướp mất!"* |
| **Shot 10**<br>*(10s)* | 📱 **Figure 4 (Corgi Livestream)** | **Schadenfreude / Voyeurism** | Lén giấu điện thoại dưới gầm bàn livestream, lấy chân che miệng cười khúc khích | *(SFX: Ting ting livestream & Comment bão)*<br>📱 *"Alo mạng xã hội ơi! Team em đang đấu tố sinh tử vì ly trà sữa, vào xem drama nghìn mắt xem sếp mèo diễn xiếc nào!"* |
| **Shot 11**<br>*(10s)* | 😈 **Figure 4 (Corgi Bùng Nổ)** | **Catharsis / Reaction Formation** | Dùng răng xé toạc quyển sổ xin lỗi, mắt long sòng sọc, cười man dại phát điên | *(SFX: Kính vỡ XOẢNG & Rock Metal gào thét)*<br>😈 *"Đủ rồi! Tôi nhịn các người suốt 3 năm nay rồi! Tôi không nhận lỗi nữa, tôi nguyền rủa tất cả các người!"* |
| **Shot 12**<br>*(10s)* | 🚩 **Figure 2 (Bulldog Ba Phải)** | **Bandwagon Effect / Herd** | Vỗ hai chân trước bôm bốp, lắc đuôi cụt tít mù, quay xe 180 độ giơ nắm đấm | *(SFX: Còi xe quay đầu & Tiếng hò reo)*<br>🚩 *"Chí lý! Tôi đồng ý với đồng chí Corgi! Khởi nghĩa đi! Lương Sơn Bạc công sở muôn năm!"* |
| **Shot 13**<br>*(10s)* | 🌀 **Figure 3 (Raccoon Sụp Đổ)** | **Cognitive Dissonance / Overload** | Ngồi bệt giữa đống giấy tờ, hai chân ôm đầu xoay tròn, mắt hoa lên như vòng xoáy | *(SFX: Rè radio mất sóng & Tiếng ong kêu)*<br>🌀 *"Nếu ai cũng là nạn nhân... thì ai là thủ phạm? Trà sữa có thật không hay chỉ là ảo ảnh của tiềm thức?!"* |
| **Shot 14**<br>*(10s)* | 😱 **Figure 1 (Boss Cat Bẽ Bàng)** | **Narcissistic Collapse** | Ánh đèn rọi thẳng vào ria mép dính siro trà sữa nâu óng, mặt đực ra tái mét | *(SFX: Kim rơi TENG! & Spotlight rọi)*<br>😱 *"Vết... vết này là sốt cá hồi hữu cơ tôi ăn từ sáng... Thề có trời đất chứng giám tôi không hề..."* |
| **Shot 15**<br>*(10s)* | 💔 **Figure 2 (Bulldog Uất Ức)** | **Betrayal Trauma** | Run rẩy chỉ chân vào ria mép Boss Mèo, hàm trễ xuống đất, mắt mở to kinh hoàng | *(SFX: Sét đánh ÙNG OÀNG & Đàn nhị)*<br>💔 *"Mày bảo Chúng ta là một gia đình... mà mày lại lén hút hết 100% đường của tao hả con mèo kia?!"* |
| **Shot 16**<br>*(10s)* | 🚪 **Figure 3 (Raccoon Đổ Lỗi)** | **Projection / Scapegoating** | Đưa 2 chân chỉ về phía chiếc tủ lạnh góc phòng, diễn nét kinh hoàng giả tạo | *(SFX: Âm thanh ma mị u u ám ám)*<br>🚪 *"Đây rõ ràng là lỗi của phong thủy chiếc tủ lạnh! Chiếc tủ lạnh có tần số năng lượng độc hại phát ra sóng thao túng!"* |
| **Shot 17**<br>*(10s)* | 🧋 **Figure 4 (Corgi Lật Kèo)** | **The Reality Check / Twist** | Đẩy nhẹ sọt rác, phủi hai chân trước, nhìn thẳng camera nở nụ cười khinh bỉ | *(SFX: Tiếng Ủa alo? & Dạ dày sôi ục ục)*<br>🧋 *"Mà quên chưa nói: Ly trà sữa đó của con bé thực tập để quên từ tuần trước thiu ngắt rồi, anh mèo hút ngon miệng ghê!"* |
| **Shot 18**<br>*(10s)* | 🤡 **Cả 4 Nhân Vật (Đau Bụng & Meme)** | **Collective Catharsis / Folly** | Boss Mèo ôm bụng quằn quại, Bulldog & Raccoon buồn nôn, cả 4 nhìn camera cười trừ | *(SFX: Quạ kêu Quạ... & Meme Outro)*<br>🤡 *"Tâm lý học hành vi chứng minh rằng: 99% drama trên đời sinh ra từ việc... rảnh rỗi sinh nông nổi!"* |

---
---

# 🚀 TẬP 2 (PART 2): "CƠN ĐỊA CHẤN TIÊU HÓA & ĐẠI HỌA SA THẢI"
*(Thời lượng: 180s = 18 Shots × 10s · Tiếp nối ngay sau cú sốc trà sữa thiu)*

## 📖 TÓM TẮT CỐT TRUYỆN PART 2:
Sau khi trúng thực vì uống nhầm ly trà sữa thiu 7 ngày, Boss Mèo đối mặt với cơn đau bụng dữ dội nhưng bản tính ái kỷ không cho phép hắn nhận sai. Hắn lập tức khởi động chiến dịch "săn lùng phù thủy" và ban bố thiết quân luật. Corgi chớp thời cơ dùng thủ thuật tâm lý ly gián (Triangulation) khiến Bulldog và Raccoon lao vào cuộc chiến tranh giành quyền lực ghế "Quyền Giám Đốc". Cuộc đấu tố đạt đỉnh điểm khi Boss Mèo "ngộ đạo" từ nhà vệ sinh bước ra, đúng lúc Corgi công bố email sa thải tập thể từ Ban Tổng Giám Đốc do livestream làm lộ bí mật công ty lên top 1 trending TikTok.

---

## 📌 PROMPT CHÍNH PART 2 (`prompt_main`)
> *Dán 18 phân đoạn dưới đây vào ô **② Kịch bản / Prompt chính** khi render Tập 2*

```text
Figure 1 (tuxedo boss cat with navy necktie and spectacles) immediately clutches its violently rumbling stomach with trembling paws, cold sweat dripping down its fur, and groans Cơn đau bụng này không phải do trúng thực, mà là phản ứng thanh lọc độc tố của một cơ thể lãnh đạo thanh khiết! with bulging amber eyes trying to maintain arrogant dignity. Single continuous locked vertical shot, cozy meeting room, consistent character rendering.

Figure 2 (muscular bulldog with spiked collar) immediately pulls out a toy first-aid kit and barks frantically Thanh lọc cái đầu ông! Mặt ông xanh như tàu lá chuối rồi kìa! Đứa nào gọi cấp cứu đi chứ tao chỉ biết bấm cắn người thôi! with wrinkly brow trembling and eyes wide with comical panic. Continuous single camera take, no cut.

Figure 3 (paranoid raccoon with round glasses and beige cardigan) immediately rolls down a giant psychological trauma chart on the whiteboard, frantically tapping it with a pointer and sputtering Theo thuyết quy kết căn bản: Cơn tiêu chảy của sếp chính là nghiệp báo vũ trụ trừng phạt tội thao túng tâm lý nhân viên! with wild nervous twitches. Continuous vertical take, sharp focus.

Figure 4 (corgi with pink bow tie) immediately tiptoes behind Figure 1 boss cat, leans into its ear with an evil sweet whisper, saying Anh Mèo ơi, em nghe đồn con Bulldog hôm qua cố tình đổi nhãn dán ly trà thiu để đầu độc anh cướp ghế giám đốc đấy ạ! with a toxic devious smirk and glittering mischievous eyes. Continuous single take, consistent character appearance.

Figure 1 (tuxedo boss cat) immediately slams a stapler violently onto the table, hissing through gritted teeth and gasping for breath Tôi biết ngay mà! Con Bulldog mang mầm mống phản trắc! Toàn phòng này bị trừ 6 tháng tiền thưởng và đi học lại khóa học Đạo đức công sở! with fur standing on end in vindictive paranoia. Continuous locked shot, stable lighting.

Figure 2 (muscular bulldog) immediately flips the wooden coffee table upside down with immense rage, throwing cushions everywhere and roaring Trừ tiền thưởng cái lông mày! Tao cày bừa như trâu 5 năm nay mà mày dám vu oan tao đầu độc hả con mèo lươn lẹo?! with neck veins popping and cartoon steam blowing from ears. Dynamic continuous take, no morphing.

Figure 3 (paranoid raccoon) immediately jumps onto a leather pouf waving a white flag made of toilet paper, shivering in panic and squeaking Các đồng chí ơi đình chiến đi! Nếu chúng ta cùng nhau quỳ xuống xin lỗi sếp, năng lượng chữa lành tập thể sẽ làm êm dạ dày sếp! in absurd Stockholm syndrome compliance. Continuous vertical framing, no cuts.

Figure 4 (corgi) immediately turns to Figure 3 with mock sorrow, clutching its chest and wailing Sao anh Raccoon lại kích động bạo lực nội bộ? Em chỉ là đứa nhân viên thấp cổ bé họng muốn mọi người yêu thương nhau thôi mà! with crocodile tears flowing in perfect psychological DARVO defense. Continuous single take.

Figure 1 (tuxedo boss cat) immediately doubles over clutching its lower abdomen in sheer gastrointestinal agony, dragging itself toward the restroom door and wheezing Trước khi... tôi lâm vào cửa tử trong toilet... tôi sẽ lập di chúc bổ nhiệm kẻ trung thành nhất làm Quyền Giám Đốc! with dramatic dying gaze. Continuous tracking take, no camera cuts.

Figure 2 (muscular bulldog) immediately drops its angry posture, stands at rigid attention with an absurd wide eager grin, wagging its stubby tail and barking Dạ sếp! Em xin tình nguyện hy sinh gánh vác ngai vàng! Em thề sẽ cắn chết bất cứ đứa nào dám ho he chống đối sếp! with instant Pavlovian obedience. Continuous locked shot.

Figure 3 (paranoid raccoon) immediately pulls a shiny aluminium foil hat onto its head, raising a whiteboard marker like a royal sceptre and sputtering Khoan đã! Theo chỉ số IQ 300 và bản đồ sao chiêm tinh, chỉ có ta mới đủ năng lực dẫn dắt bộ tộc này qua cơn đại hồng thủy! with sudden grandiose delusions of power. Continuous single camera take.

Figure 4 (corgi) immediately adjusts its tiny pink bow tie, looks directly into the secret smartphone livestream, and whispers chillingly Nhìn hai con rối đang cắn xé nhau vì cái ghế tạm quyền kìa... Mọi chuyện đang diễn ra đúng 100% theo kịch bản thao túng hắc ám của tôi! with an unhinged Machiavellian smile. Sharp focus, continuous locked take.

Figure 2 (muscular bulldog) immediately grabs Figure 3 raccoon by its knitted cardigan, shaking it back and forth aggressively while Figure 3 tries to poke Figure 2 with marker pens, bulldog roaring Ghế quyền lực này là của tao! Khôn hồn thì lui ra con gấu mèo hôi hám! amidst hilarious slapstick office combat. Continuous locked vertical action shot.

Figure 1 (tuxedo boss cat) immediately kicks the restroom door wide open with theatrical slow-motion, toilet paper stuck to its left hind paw, glowing with delusional enlightenment and proclaiming Sau 15 phút ngộ đạo giữa lằn ranh sinh tử, tôi đã khai mở luân xa thứ 7 và nhìn thấu sự vô thường của quyền lực công sở! with supreme arrogant serenity. Continuous locked take.

Figure 4 (corgi) immediately walks up to Figure 1 holding an iPad with a huge red email notification, deadpanning Sếp ngộ đạo xong chưa ạ? Ban Giám Đốc vừa gửi trát sa thải tập thể cả phòng vì livestream đấu tố nội bộ lọt top 1 xu hướng TikTok 10 triệu view rồi kìa! with a soul-shattering smug expression. Continuous single take.

Figure 2 (muscular bulldog) immediately freezes in mid-punch, dropping the marker pen, jaw hitting the floor as eyes pop out in horror, howling 10 triệu view?! Mẹ tao ở quê vừa thả tim video tao cắn rách áo sếp rồi! Đời tao coi như tàn phế! with catastrophic panic breakdown. Continuous locked single take.

Figure 3 (paranoid raccoon) immediately collapses flat on the woven rug in a starfish pose, staring blankly at the ceiling fan with dizzy spiral eyes and murmuring Thất nghiệp thực chất là một sự giải phóng năng lượng lượng tử... Chúng ta đã hoàn toàn tự do khỏi ma trận tư bản... with total existential nihilism. Continuous single take.

All 4 animal characters immediately stand in a horizontal lineup holding packed cardboard boxes, Figure 1 boss cat wearing sunglasses with a mini suitcase, Figure 2 bulldog carrying a dog bowl, Figure 3 raccoon clutching its whiteboard, Figure 4 corgi holding a selfie stick, as Figure 1 immediately looks into the camera and says Tâm lý học hành vi đúc kết bài học cuối: Khi công ty cháy... đứa thông minh nhất là đứa biết mở livestream bán hàng online! while all 4 freeze simultaneously in a ridiculous viral meme pose, staring straight into the camera lens with deadpan expressions. Continuous locked wide vertical take.
```

---

## 🎙️ BẢNG CHI TIẾT 18 PHÂN ĐOẠN PART 2

| Shot | Nhân vật & Cảm xúc | Thiên kiến tâm lý | Diễn xuất & Body Language | Lời thoại [SPEECH] & SFX |
| :--- | :--- | :--- | :--- | :--- |
| **Shot 1**<br>*(10s)* | 🐱 **Figure 1 (Boss Cat Quằn Quại)** | **Cognitive Dissonance / Rationalization** | Ôm bụng sôi ùng ục, mồ hôi hột rơi lộp độp, cố gồng mình giữ nét quý phái | *(SFX: Dạ dày sôi sấm sét & Đàn cello rên rỉ)*<br>🐱 *"Cơn đau bụng này không phải do trúng thực, mà là phản ứng thanh lọc độc tố của một cơ thể lãnh đạo thanh khiết!"* |
| **Shot 2**<br>*(10s)* | 🐶 **Figure 2 (Bulldog Hoảng Hốt)** | **Bystander Effect / Diffusion** | Lôi hộp cứu thương đồ chơi, mặt nhăn tít, mồm sủa cuống cuồng nhìn quanh | *(SFX: Còi xe cứu thương réo ầm ĩ)*<br>🐶 *"Thanh lọc cái đầu ông! Mặt ông xanh như tàu lá chuối rồi kìa! Đứa nào gọi cấp cứu đi chứ tao chỉ biết bấm cắn người thôi!"* |
| **Shot 3**<br>*(10s)* | 🦝 **Figure 3 (Raccoon Lên Lớp)** | **Fundamental Attribution Error** | Kéo sập bảng biểu chấn thương tâm lý, gõ cây chỉ bảng côm cốp, giật giật đuôi | *(SFX: Tiếng phấn gãy rắc & Chuông chùa ngân)*<br>🦝 *"Theo thuyết quy kết căn bản: Cơn tiêu chảy của sếp chính là nghiệp báo vũ trụ trừng phạt tội thao túng tâm lý nhân viên!"* |
| **Shot 4**<br>*(10s)* | 🐍 **Figure 4 (Corgi Ly Gián)** | **Triangulation / Malicious Rumor** | Rón rén ghé sát tai Boss Mèo, liếc mắt hiểm độc thì thầm to nhỏ | *(SFX: Rắn độc thè lưỡi phì phì & Trống gõ dồn)*<br>🐍 *"Anh Mèo ơi, em nghe đồn con Bulldog hôm qua cố tình đổi nhãn dán ly trà thiu để đầu độc anh cướp ghế giám đốc đấy ạ!"* |
| **Shot 5**<br>*(10s)* | 🤬 **Figure 1 (Boss Cat Độc Tài)** | **Horn Effect / Scapegoating 2.0** | Đập dập ghim rầm xuống bàn, rít qua kẽ răng, mắt long sòng sọc nhìn Bulldog | *(SFX: Tiếng sập bẫy sắt XOẢNG & Sấm chớp)*<br>🤬 *"Tôi biết ngay mà! Con Bulldog mang mầm mống phản trắc! Toàn phòng này bị trừ 6 tháng tiền thưởng và đi học lại khóa học Đạo đức công sở!"* |
| **Shot 6**<br>*(10s)* | 🔥 **Figure 2 (Bulldog Lật Bàn)** | **Reactive Aggression / Burnout** | Lật tung chiếc bàn trà gỗ, ném gối ôm tung tóe, gầm rú khói xì ra hai tai | *(SFX: BÀN GỖ ĐỔ RẦM! & Tiếng bom nổ)*<br>🔥 *"Trừ tiền thưởng cái lông mày! Tao cày bừa như trâu 5 năm nay mà mày dám vu oan tao đầu độc hả con mèo lươn lẹo?!"* |
| **Shot 7**<br>*(10s)* | 🏳️ **Figure 3 (Raccoon Đầu Hàng)** | **Stockholm Syndrome / Submission** | Nhảy phắt lên đôn da vẫy cờ trắng bằng giấy vệ sinh, run rẩy van xin | *(SFX: Tiếng đàn Ukulele thảm thương)*<br>🏳️ *"Các đồng chí ơi đình chiến đi! Nếu chúng ta cùng nhau quỳ xuống xin lỗi sếp, năng lượng chữa lành tập thể sẽ làm êm dạ dày sếp!"* |
| **Shot 8**<br>*(10s)* | 🎭 **Figure 4 (Corgi Đóng Vai Nạn Nhân)** | **DARVO (Deny, Attack, Reverse Victim)** | Ôm ngực nức nở ăn vạ, rớt nước mắt cá sấu, đổ ngược tội lỗi cho Raccoon | *(SFX: Nhạc kịch bi tráng & Tiếng vỗ tay hề)*<br>🎭 *"Sao anh Raccoon lại kích động bạo lực nội bộ? Em chỉ là đứa nhân viên thấp cổ bé họng muốn mọi người yêu thương nhau thôi mà!"* |
| **Shot 9**<br>*(10s)* | 🚽 **Figure 1 (Boss Cat Di Chúc)** | **Illusion of Control / Scarcity** | Bò lê lết về phía cửa toilet, một tay bấu chặt mép cửa, thì thào trăn trối | *(SFX: Tiếng tim đập thoi thóp & Kèn đám ma)*<br>🚽 *"Trước khi... tôi lâm vào cửa tử trong toilet... tôi sẽ lập di chúc bổ nhiệm kẻ trung thành nhất làm Quyền Giám Đốc!"* |
| **Shot 10**<br>*(10s)* | 🐶 **Figure 2 (Bulldog Quay Xe Nịnh)** | **Pavlovian Conditioning / Greed** | Đứng nghiêm chào cờ, cười toe toét nhe răng, ngoáy đuôi tít mù nịnh bợ | *(SFX: Ting Ting tiếng tiền xu rơi)*<br>🐶 *"Dạ sếp! Em xin tình nguyện hy sinh gánh vác ngai vàng! Em thề sẽ cắn chết bất cứ đứa nào dám ho he chống đối sếp!"* |
| **Shot 11**<br>*(10s)* | 👑 **Figure 3 (Raccoon Hoang Tưởng Quyền)** | **Megalomania / Dunning-Kruger** | Đội mũ giấy bạc chống sóng não, cầm bút lông làm vương trượng vung vẩy | *(SFX: Nhạc giao hưởng đăng quang hoàng gia)*<br>👑 *"Khoan đã! Theo chỉ số IQ 300 và bản đồ sao chiêm tinh, chỉ có ta mới đủ năng lực dẫn dắt bộ tộc này qua cơn đại hồng thủy!"* |
| **Shot 12**<br>*(10s)* | 📱 **Figure 4 (Corgi Trùm Cuối)** | **Machiavellianism / Dark Triad** | Chỉnh nơ hồng, ghé sát camera điện thoại livestream thì thầm đắc thắng | *(SFX: Tiếng cười ác quỷ Hehehe & Bão tym)*<br>📱 *"Nhìn hai con rối đang cắn xé nhau vì cái ghế tạm quyền kìa... Mọi chuyện đang diễn ra đúng 100% theo kịch bản thao túng hắc ám của tôi!"* |
| **Shot 13**<br>*(10s)* | 🤼 **Figure 2 & 3 (Đại Chiến Tranh Ghế)** | **Zero-Sum Game / Escalation** | Bulldog tóm áo len Raccoon lắc điên cuồng, Raccoon lấy bút lông chọc mặt Bulldog | *(SFX: Tiếng mèo chó cắn nhau chí chóe)*<br>🤼 *"Ghế quyền lực này là của tao! Khôn hồn thì lui ra con gấu mèo hôi hám!"* |
| **Shot 14**<br>*(10s)* | ✨ **Figure 1 (Boss Cat Ngộ Đạo)** | **Spiritual Bypassing / Halo Effect** | Tung cửa toilet bước ra oai vệ, chân sau dính dải giấy vệ sinh dài thượt | *(SFX: Hào quang thánh thót Aaaa... & Tiếng nước xả)*<br>✨ *"Sau 15 phút ngộ đạo giữa lằn ranh sinh tử, tôi đã khai mở luân xa thứ 7 và nhìn thấu sự vô thường của quyền lực công sở!"* |
| **Shot 15**<br>*(10s)* | 📄 **Figure 4 (Corgi Phát Trát Sa Thải)** | **Schadenfreude / Reality Check** | Giơ iPad hiện email viền đỏ chót, mặt tỉnh queo tung đòn kết liễu | *(SFX: Tiếng sét đánh sụp trần & Tiếng Ting email)*<br>📄 *"Sếp ngộ đạo xong chưa ạ? Ban Giám Đốc vừa gửi trát sa thải tập thể cả phòng vì livestream đấu tố nội bộ lọt top 1 xu hướng TikTok 10 triệu view rồi kìa!"* |
| **Shot 16**<br>*(10s)* | 😱 **Figure 2 (Bulldog Chết Đứng)** | **Panic Breakdown / Social Stigma** | Đứng hình giữa không trung, rơi bút lông, hàm rớt xuống đất hú hét tuyệt vọng | *(SFX: Tiếng đĩa vỡ xoảng & Nhạc phim kinh dị)*<br>😱 *"10 triệu view?! Mẹ tao ở quê vừa thả tim video tao cắn rách áo sếp rồi! Đời tao coi như tàn phế!"* |
| **Shot 17**<br>*(10s)* | 🌌 **Figure 3 (Raccoon Buông Xuôi)** | **Existential Nihilism / Zen** | Nằm ngửa hình con sao biển trên thảm, mắt xoáy ốc nhìn trần nhà thở dài | *(SFX: Gió thổi hiu quạnh phù phù & Tiếng lá rơi)*<br>🌌 *"Thất nghiệp thực chất là một sự giải phóng năng lượng lượng tử... Chúng ta đã hoàn toàn tự do khỏi ma trận tư bản..."* |
| **Shot 18**<br>*(10s)* | 📦 **Cả 4 Nhân Vật (Dọn Đồ & Meme Outro)** | **The Final Satire / Monetization** | Cả 4 ôm thùng carton dọn đồ, đeo kính râm cầm gậy selfie tạo dáng TikTok | *(SFX: Nhạc TikTok Remix giật cục & Tiếng Đing)*<br>📦 *"Tâm lý học hành vi đúc kết bài học cuối: Khi công ty cháy... đứa thông minh nhất là đứa biết mở livestream bán hàng online!"* |

---
---

# 🚫 PROMPT PHỦ ĐỊNH CHUNG (`negative_prompt`)

```text
subtitles, watermark, text, signature, low quality, worst quality, blurry, deformed paws, extra paws, duplicate limbs, distorted animal faces, creepy eyes, jittery unstable frame, dark muddy colors, inconsistent fur color, sudden morphing, scene cut inside shot, multi-speaker confusion, frozen still image, horizontal landscape layout, cropped heads, ugly artifacts
```

---

# 💡 HƯỚNG DẪN GÁN ẢNH THAM KHẢO TRÊN GIAO DIỆN GRADIO

| Ô Upload trong UI | Nhân vật / Bối cảnh | File ảnh có sẵn trong thư mục `scrpits/psychology/` |
| :--- | :--- | :--- |
| **🎭 Pic 1 (Bắt buộc)** | **Figure 1: Boss Mèo Tuxedo (Tống Giang)** | `msr_pic1_gaslighter_cat_ref.jpg` |
| **🎭 Pic 2 (Tuỳ chọn)** | **Figure 2: Bulldog Giận Dữ (Lý Quỳ)** | `msr_pic2_bulldog_ref.jpg` |
| **🎭 Pic 3 (Tuỳ chọn)** | **Figure 3: Gấu Mèo Raccoon (Ngô Dụng)** | `msr_pic3_raccoon_ref.jpg` |
| **🎭 Pic 4 (Tuỳ chọn)** | **Figure 4: Chó Corgi Cam Chịu & Drama (Lâm Xung)** | `msr_pic4_corgi_ref.jpg` |
| **🌄 Background (Tuỳ chọn)** | **Scene: Phòng họp công sở hiện đại** | `msr_bg_meeting_room.jpg` |

---

# ⚙️ THÔNG SỐ KHUYẾN NGHỊ TRÊN GRADIO (TỐI ƯU 9:16)

| Thông số | Giá trị | Ghi chú |
| :--- | :--- | :--- |
| **Tỉ lệ khung hình** | `9:16 (720x1280) · HD 720p Dọc` | Hoặc `480x832` nếu GPU < 24GB |
| **Thời lượng mỗi cảnh** | `10` giây | 18 cảnh × 10s = 3 phút/tập tự nối ffmpeg |
| **FPS** | `24` | Khớp chuẩn đồng bộ khẩu hình |
| **MSR LoRA Strength** | `1.0` ⭐ | Giữ khuôn mặt 4 nhân vật cố định 100% |
| **Video CFG** | `2.5` ⭐ | Bám sát hành động và khẩu hình lời thoại tiếng Việt |
| **Reference Strength** | `0.85` ⭐ | Tránh tình trạng nhân vật bị biến dạng ở Stage 2 |
| **Reference Frames** | `33` | Chuẩn MSR chính thức |
| **Stage 2 (Upscale x2)** | `Bật ✅` | Tăng độ nét chi tiết lông và biểu cảm |
| **Low VRAM Mode** | `Bật ✅` | Tiết kiệm bộ nhớ GPU tránh tràn VRAM |
