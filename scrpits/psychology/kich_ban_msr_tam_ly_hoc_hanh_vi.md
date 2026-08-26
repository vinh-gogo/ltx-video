# 🎬 KỊCH BẢN VIDEO HÀI BỰA TÂM LÝ HỌC 9:16 (3 PHÚT): "108 ANH HÀO TÂM LÝ HỌC: ĐẠI CHIẾN BÀN TRÒN CÔNG SỞ"
> *(Phong cách Animal Comedy ẩn dụ hành vi con người - 108 nét tính cách Thủy Hử)*

- **Thể loại:** Hài bựa châm biếm sâu cay (Dark Satirical Animal Comedy), Phim tâm lý học hành vi con người mượn hình tượng động vật siêu biểu cảm.
- **Định dạng khung hình:** **9:16 Khung dọc (Vertical Video)** — Chuẩn Reels, TikTok, YouTube Shorts đỉnh cao.
- **Thời lượng:** **3 phút (180 giây)** = **18 Phân đoạn (Shots) × 10 giây/shot**.
- **Cấu hình tham chiếu:** **Đúng 5 ảnh (4 Nhân vật Động vật + 1 Background)**.
- **Tương thích:** Tối ưu 100% cho `ltx2_5_msr.py` — áp dụng 3 fix: speech ở đầu prompt, bỏ timestamp, character desc khớp ảnh.

---

## 📌 PHẦN 1: MÔ TẢ NHÂN VẬT & BỐI CẢNH (`character_description`)
> *Dán toàn bộ 5 mục bên dưới vào ô **① Mô tả nhân vật — phải khớp với Pic 1/2/3/4 bên trên***
>
> ⚠️ **Quy tắc bắt buộc:** `Image 1` mô tả chính xác nhân vật trong **Pic 1**, `Image 2` mô tả **Pic 2**, v.v. Mô tả càng chi tiết (màu lông, trang phục, đặc điểm) → AI giữ nhân vật càng chính xác.

```text
Image 1: Figure 1, The Gaslighter Boss Cat (Tong Giang archetype): A chubby tuxedo British Shorthair cat with sleek dark grey fur, white chest patch, wearing a miniature executive navy blue necktie and small stylish rimless spectacles perched on its nose, cunning calculating amber eyes. Pixar-style 3D cartoon character, photorealistic render quality.

Image 2: Figure 2, The Rageholic Bulldog ID (Ly Quy archetype): A muscular fawn French Bulldog with wrinkled brow, intense fiery eyes, bulging neck veins, wearing a tiny black spiked collar, expressive comedic rage facial expressions. Pixar-style 3D cartoon character, photorealistic render quality.

Image 3: Figure 3, The Paranoid Overthinker Raccoon (Ngo Dung archetype): A skinny curious raccoon with natural black mask markings around eyes, wearing thick round wire-frame reading glasses and a tiny beige knitted cardigan, twitching paws, wide terrified paranoid eyes. Pixar-style 3D cartoon character, photorealistic render quality.

Image 4: Figure 4, The People-Pleaser and Drama Corgi (Lam Xung archetype): A fluffy tri-color Corgi with large expressive perky ears, wearing a tiny crumpled blue office collar and pink bow tie, holding a small notepad, alternating between a tortured polite smile and sharp judgmental side-eye. Pixar-style 3D cartoon character, photorealistic render quality.

Image 5: Scene, vertical 9:16 composition, a cozy modern lounge and meeting room with warm natural lighting, a low rustic wooden coffee table in the center on a soft textured woven rug, surrounded by low comfortable leather poufs, plush armchairs, and a sofa with cushions, cinematic photorealistic interior, 4k resolution.
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
Figure 3 (paranoid raccoon with round glasses and beige cardigan) immediately holds up a magnifying glass over an empty boba cup and says Đây không đơn thuần là ly trà sữa bị hút trộm! Đây là một đòn tâm lý chiến nhằm tiêu diệt niềm tin nội bộ! with wild paranoid eyes and twitching paws, adjusting its thick wire glasses frantically. Red strings on the whiteboard loom in the background. Continuous vertical locked shot, cozy meeting room, no camera cut, consistent character appearance throughout.

Figure 1 (tuxedo boss cat with navy necktie and rimless glasses) immediately leans forward with a saintly yet deeply manipulative purr and says Chúng ta là một gia đình... Kẻ trộm trà sữa không có lỗi, lỗi là cả phòng đã không đủ bao dung để chia sẻ! gesturing smoothly with calculated pseudo-empathy, tilting its head and adjusting its rimless spectacles. Stable cinematic lighting, continuous single camera take, no morphing.

Figure 2 (muscular bulldog with spiked collar) immediately slams both front paws violently onto the conference table and roars Bao dung cái con khỉ! Đứa nào uống cạn trân châu hoàng kim của tao? Bước ra đây solo 1 mất 1 còn! with wrinkly face turning red and veins popping, barking straight toward the camera in cartoonish explosive fury. Single locked continuous camera take, expressive comedic rage motion.

Figure 4 (corgi with pink bow tie and blue collar) immediately cowers in its seat hugging a tiny apology notepad with short paws and whines Em xin lỗi cả nhà... Dù em mới đi vệ sinh vào, nhưng chắc chắn là do hào quang tội lỗi của em gây ra! with perky ears drooping down, trembling mouth curled into a tortured polite smile, eyes watery with guilt. Consistent framing, no cuts, natural subtle shivers.

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

## 🎙️ BẢNG CHI TIẾT 18 PHÂN ĐOẠN — CUNG BẬC CẢM XÚC & LỜI THOẠI [SPEECH] TIẾNG VIỆT
> 🎯 **Quy tắc 1 Speaker / Shot:** Mỗi shot 10s chỉ có duy nhất **1 nhân vật phát ngôn**, phân định rõ **Thiên kiến tâm lý**, **Cung bậc cảm xúc**, **Hành động & Diễn xuất** cùng **SFX**.
>
> ✅ **Fix SPEECH timing:** Lời thoại xuất hiện **ngay frame đầu** nhờ đặt "immediately says/shouts" ở đầu prompt — không còn bị đẩy về cuối video.

| Shot | Nhân vật & Cảm xúc | Thiên kiến tâm lý | Diễn xuất & Body Language | Lời thoại [SPEECH] & SFX |
| :--- | :--- | :--- | :--- | :--- |
| **Shot 1**<br>*(10s)* | 🦝 **Figure 3 (Ngô Dụng Raccoon)**<br>*(Hoang tưởng, Nghi ngờ tột độ)* | **Paranoia / Confirmation Bias** | Cầm kính lúp soi ly trà sữa rỗng, vuốt gọng kính run rẩy, mắt trợn trừng, đuôi ngoe nguẩy lo âu | *(SFX: Tiếng tim đập dồn dập & Violin hồi hộp)*<br>🦝 *"Đây không đơn thuần là ly trà sữa bị hút trộm! Đây là một đòn tâm lý chiến nhằm tiêu diệt niềm tin nội bộ!"* |
| **Shot 2**<br>*(10s)* | 🐱 **Figure 1 (Tống Giang Boss Cat)**<br>*(Đạo đức giả, Thao túng)* | **Gaslighting / Machiavellianism** | Ngồi ngay ngắn đầu bàn, đẩy kính không gọng, nheo mắt thấu cảm giả tạo, vẫy đuôi nhẹ nhàng | *(SFX: Tiếng đàn hạc du dương giả tạo)*<br>🐱 *"Chúng ta là một gia đình... Kẻ trộm trà sữa không có lỗi, lỗi là cả phòng đã không đủ bao dung để chia sẻ!"* |
| **Shot 3**<br>*(10s)* | 🐶 **Figure 2 (Lý Quỳ Bulldog)**<br>*(Phẫn nộ, Điên cuồng bản năng)* | **Primal Aggression (Id Instinct)** | Đập rầm hai chân trước xuống bàn, mặt nhăn tít đỏ bừng, gân cổ nổi cuồn cuộn, sùi bọt mép | *(SFX: RẦM! Tiếng còi báo động khẩn cấp)*<br>🐶 *"Bao dung cái con khỉ! Đứa nào uống cạn trân châu hoàng kim của tao? Bước ra đây solo 1 mất 1 còn!"* |
| **Shot 4**<br>*(10s)* | 🦊 **Figure 4 (Lâm Xung Corgi Cam Chịu)**<br>*(Tội lỗi oan ức, Sợ hãi)* | **People-Pleasing / Stockholm Syndrome** | Tai cụp xuống, hai chân ôm sổ xin lỗi, miệng cười gượng run rẩy, mắt ươn ướt | *(SFX: Tiếng dế kêu thảm thương)*<br>🦊 *"Em xin lỗi cả nhà... Dù em mới đi vệ sinh vào, nhưng chắc chắn là do hào quang tội lỗi của em gây ra!"* |
| **Shot 5**<br>*(10s)* | 💅 **Figure 4 (Corgi Drama Cà Khịa)**<br>*(Cà khịa, Khinh bỉ, Hả hê)* | **Passive-Aggressive / Social Comparison** | Đột ngột dựng thẳng tai, liếc xéo sắc lẹm, nở nụ cười nhếch mép thảo mai | *(SFX: Tiếng mèo cào móng & Tiếng rắn rít)*<br>💅 *"Em không có ý phán xét đâu nha, nhưng ai đó mang tiếng sếp lớn ăn cá hồi mà đi tiếc ly trà sữa 30k thì hơi bần đấy ạ!"* |
| **Shot 6**<br>*(10s)* | 👑 **Figure 1 (Tống Giang Boss Cat)**<br>*(Tự cao tự đại, Hợm hĩnh)* | **Dunning-Kruger Effect** | Ưỡn ngực lông trắng phổng phao, giơ một móng vuốt lên chỉ trỏ trịch thượng | *(SFX: Tiếng kèn bóp hề kêu Boing Boing)*<br>👑 *"Với tư duy lãnh đạo đỉnh cao của loài mèo, tôi khẳng định đây là bài test tâm lý do ban giám đốc cài vào!"* |
| **Shot 7**<br>*(10s)* | 📊 **Figure 3 (Ngô Dụng Raccoon)**<br>*(Khủng hoảng, Rối loạn phân tích)* | **Analysis Paralysis / Conspiracy** | Cầm 2 bút lông quẹt loạn xạ ma trận trên bảng trắng, đuôi ngoáy tít mù, quay ngoắt về camera thở dốc | *(SFX: Tiếng bút lông quẹt chói tai & Đèn chớp)*<br>📊 *"Theo ma trận tâm lý tội phạm học: Ly trà sữa bị uống lúc 3h15 phút... trùng khớp với giờ sao Thủy nghịch hành!"* |
| **Shot 8**<br>*(10s)* | 😿 **Figure 1 (Tống Giang Boss Cat)**<br>*(Nước mắt cá sấu, Tống tiền cảm xúc)* | **Guilt-Tripping / Emotional Blackmail** | Lấy chân gạt nước mắt cá sấu, rung râu bi thương, chỉ móng vuốt vào từng đứa | *(SFX: Tiếng đàn bầu sầu thảm & Sấm chớp)*<br>😿 *"Các em làm tôi đau lòng quá! Nếu ngày mai công ty phá sản, chính là vì sự ích kỷ của từng người trong phòng này!"* |
| **Shot 9**<br>*(10s)* | 😭 **Figure 2 (Lý Quỳ Bulldog)**<br>*(Đau khổ tột cùng, Cảm giác mất mát)* | **Loss Aversion / Hyperbolic Grief** | Quỳ sụp xuống, ôm ly trà sữa rỗng áp vào má nhiều nếp nhăn, ngửa mõm hú lên trần nhà | *(SFX: Tiếng mưa rơi ầm ầm & Nhạc cải lương)*<br>😭 *"Trân châu ơi sao mày bỏ tao đi... Tao đã dặn thêm 70% đường 30% đá mà bọn ác nhân nỡ cướp mất!"* |
| **Shot 10**<br>*(10s)* | 📱 **Figure 4 (Corgi Livestream)**<br>*(Đắc ý độc hại, Háo hức hóng hớt)* | **Schadenfreude / Voyeurism** | Lén giấu điện thoại dưới gầm bàn livestream, lấy chân che miệng cười khúc khích | *(SFX: Ting ting thông báo live stream & Comment bão táp)*<br>📱 *"Alo mạng xã hội ơi! Team em đang đấu tố sinh tử vì ly trà sữa, vào xem drama nghìn mắt xem sếp mèo diễn xiếc nào!"* |
| **Shot 11**<br>*(10s)* | 😈 **Figure 4 (Corgi Bùng Nổ)**<br>*(Cuồng loạn, Giải tỏa uất ức đỉnh điểm)* | **Catharsis / Reaction Formation** | Dùng răng xé toạc quyển sổ xin lỗi, mắt long sòng sọc, cười man dại phát điên | *(SFX: Tiếng kính vỡ XOẢNG & Nhạc Rock Metal gào thét)*<br>😈 *"Đủ rồi! Tôi nhịn các người suốt 3 năm nay rồi! Tôi không nhận lỗi nữa, tôi nguyền rủa tất cả các người!"* |
| **Shot 12**<br>*(10s)* | 🚩 **Figure 2 (Bulldog Hưởng Ứng)**<br>*(Hoảng hốt, Trở cờ ba phải)* | **Bandwagon Effect / Herd Mentality** | Vỗ hai chân trước bôm bốp, lắc đuôi cụt tít mù, quay xe 180 độ giơ nắm đấm hò reo | *(SFX: Tiếng còi xe quay đầu & Tiếng reo hò)*<br>🚩 *"Chí lý! Tôi đồng ý với đồng chí Corgi! Khởi nghĩa đi! Lương Sơn Bạc công sở muôn năm!"* |
| **Shot 13**<br>*(10s)* | 🌀 **Figure 3 (Ngô Dụng Raccoon)**<br>*(Bế tắc tâm thần, Sụp đổ nhận thức)* | **Cognitive Dissonance / System Overload** | Ngồi bệt giữa đống giấy tờ, hai chân ôm đầu xoay tròn, mắt hoa lên như vòng xoáy | *(SFX: Tiếng rè radio mất sóng & Tiếng ong kêu trong tai)*<br>🌀 *"Nếu ai cũng là nạn nhân... thì ai là thủ phạm? Trà sữa có thật không hay chỉ là ảo ảnh của tiềm thức?!"* |
| **Shot 14**<br>*(10s)* | 😱 **Figure 1 (Tống Giang Boss Cat)**<br>*(Bẽ bàng, Xấu hổ, Sụp đổ)* | **Narcissistic Collapse / Caught Red-Handed** | Ánh đèn rọi thẳng vào ria mép lộ rõ vệt siro trà sữa nâu óng, mặt đực ra tái mét, tai giật giật | *(SFX: Tiếng kim rơi TENG! & Đèn rọi Spotlight)*<br>😱 *"Vết... vết này là sốt cá hồi hữu cơ tôi ăn từ sáng... Thề có trời đất chứng giám tôi không hề..."* |
| **Shot 15**<br>*(10s)* | 💔 **Figure 2 (Bulldog Sôi Máu)**<br>*(Sốc phản bội, Tan nát con tim)* | **Betrayal Trauma / Disillusionment** | Run rẩy chỉ chân vào ria mép Boss Mèo, hàm trễ xuống đất, mắt mở to kinh hoàng | *(SFX: Tiếng sét đánh ÙNG OÀNG & Đàn nhị ai oán)*<br>💔 *"Mày bảo Chúng ta là một gia đình... mà mày lại lén hút hết 100% đường của tao hả con mèo kia?!"* |
| **Shot 16**<br>*(10s)* | 🚪 **Figure 3 (Ngô Dụng Raccoon)**<br>*(Chối bay, Đổ lỗi hoang đường)* | **Psychological Projection / Scapegoating** | Đưa 2 chân chỉ về phía chiếc tủ lạnh góc phòng, diễn nét kinh hoàng giả tạo | *(SFX: Tiếng hiệu ứng ma mị u u ám ám)*<br>🚪 *"Đây rõ ràng là lỗi của phong thủy chiếc tủ lạnh! Chiếc tủ lạnh có tần số năng lượng độc hại phát ra sóng thao túng!"* |
| **Shot 17**<br>*(10s)* | 🧋 **Figure 4 (Corgi Lật Kèo)**<br>*(Tỉnh bơ, Tung đòn chí mạng)* | **The Reality Check / Anti-Climax** | Đẩy nhẹ sọt rác, phủi hai chân trước, nhìn thẳng vào camera nở nụ cười khinh bỉ | *(SFX: Tiếng Ủa alo? cực to & Tiếng dạ dày sôi ùng ục)*<br>🧋 *"Mà quên chưa nói: Ly trà sữa đó của con bé thực tập để quên từ tuần trước thiu ngắt rồi, anh mèo hút ngon miệng ghê!"* |
| **Shot 18**<br>*(10s)* | 🤡 **Cả 4 Nhân Vật (Đứng Hình & Đau Bụng)**<br>*(Kinh hoàng, Đau bụng, Cười trừ Meme)* | **Collective Catharsis / Shared Folly** | Boss Mèo ôm bụng quằn quại, Bulldog & Raccoon buồn nôn, cả 4 nhìn camera cười trừ meme | *(SFX: Tiếng quạ kêu Quạ... Quạ... & Nhạc Meme Outro)*<br>🤡 *"Tâm lý học hành vi chứng minh rằng: 99% drama trên đời sinh ra từ việc... rảnh rỗi sinh nông nổi!"* |

---

## 🚫 PHẦN 3: PROMPT PHỦ ĐỊNH (`negative_prompt`)

```text
subtitles, watermark, text, signature, low quality, worst quality, blurry, deformed paws, extra paws, duplicate limbs, distorted animal faces, creepy eyes, jittery unstable frame, dark muddy colors, inconsistent fur color, sudden morphing, scene cut inside shot, multi-speaker confusion, frozen still image, horizontal landscape layout, cropped heads, ugly artifacts
```

---

## 💡 HƯỚNG DẪN GÁN ẢNH THAM KHẢO VÀO CÁC Ô TRÊN GRADIO (CHUẨN 5 ẢNH)

| Ô Upload trong UI | Nhân vật / Bối cảnh | Gợi ý hình ảnh tham chiếu (3-panel turnaround) |
| :--- | :--- | :--- |
| **🎭 Pic 1 (Bắt buộc)** | **Figure 1: Boss Mèo Gaslighter (Tống Giang)** | Mèo Tuxedo xám tro béo đeo kính không gọng & cà vạt navy |
| **🎭 Pic 2 (Tuỳ chọn)** | **Figure 2: Bulldog Sôi Máu (Lý Quỳ)** | Chó Bull Pháp cơ bắp đeo vòng cổ xích gai nhọn, mặt giận dữ |
| **🎭 Pic 3 (Tuỳ chọn)** | **Figure 3: Raccoon Overthink (Ngô Dụng)** | Gấu mèo Raccoon đeo kính cận tròn dày, áo len gile be |
| **🎭 Pic 4 (Tuỳ chọn)** | **Figure 4: Corgi Cam Chịu & Drama (Lâm Xung)** | Chó Corgi tai to đeo nơ hồng, ôm sổ xin lỗi |
| **🌄 Background (Tuỳ chọn)** | **Scene: Phòng họp công sở hoàng hôn** | Phòng họp kính hiện đại với bảng trắng chằng chịt dây đỏ, ly trà sữa cô độc (tỉ lệ dọc 9:16) |

---

## ⚙️ THÔNG SỐ KHUYẾN NGHỊ TRÊN GRADIO (TỐI ƯU 9:16 — 3 PHÚT)

| Thông số | Giá trị | Ghi chú |
| :--- | :--- | :--- |
| **Tỉ lệ khung hình** | `9:16 (720x1280) · HD 720p Dọc` | Hoặc `480x832` nếu GPU < 24GB |
| **Thời lượng mỗi cảnh** | `10` giây | 18 cảnh × 10s = 3 phút tự ghép |
| **FPS** | `24` | |
| **MSR LoRA Strength** | `1.0` ⭐ | Tăng từ 0.85 → giữ nhân vật chặt hơn |
| **Video CFG** | `2.5` ⭐ | Tăng từ 1.5 → bám prompt & speech tốt hơn |
| **Reference Strength** | `0.85` ⭐ | Tăng từ 0.7 → ít bị đổi nhân vật ở Stage 2 |
| **Reference Frames** | `33` | Mặc định MSR chính thức |
| **Stage 2 (Upscale x2)** | `Bật ✅` | Stage 2 giờ giữ nguyên msr_strength (không giảm nữa) |
| **Low VRAM Mode** | `Bật ✅` | Bắt buộc với GPU < 24GB |

> 💡 **Nếu nhân vật vẫn bị đổi**: Tăng **Reference Strength** lên `0.9–1.0` và **LoRA Strength** lên `1.1–1.2`.
> 💡 **Nếu video bị artifact/cứng**: Giảm **Video CFG** xuống `2.0` và **Reference Strength** xuống `0.75`.
> 💡 **Render 18 cảnh liên tiếp ~5-6 tiếng** trên L4/A100. Nên dùng **Seed cố định** để nhân vật nhất quán xuyên suốt.

