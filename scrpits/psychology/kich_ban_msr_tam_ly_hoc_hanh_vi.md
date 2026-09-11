# 🎬 SERIES KỊCH BẢN VIDEO HÀI BỰA TÂM LÝ HỌC 9:16: "108 ANH HÀO TÂM LÝ HỌC CÔNG SỞ"
> *(Phong cách Animal Comedy ẩn dụ hành vi con người - 108 nét tính cách Thủy Hử)*

- **Thể loại:** Hài bựa châm biếm sâu cay (Dark Satirical Animal Comedy), Phim tâm lý học hành vi con người mượn hình tượng động vật siêu biểu cảm.
- **Định dạng khung hình:** **9:16 Khung dọc (Vertical Video)** — Chuẩn Reels, TikTok, YouTube Shorts đỉnh cao.
- **Quy mô Series:** **2 Tập (6 Phút tổng cộng)** = **36 Phân đoạn (Shots) × 10 giây/shot**.
  - **Tập 1 (Part 1):** *Vụ Án Trà Sữa Thiu & Đòn Tâm Lý Chiến* (18 Shots · 180s)
  - **Tập 2 (Part 2):** *Cơn Địa Chấn Tiêu Hóa & Đại Họa Sa Thải* (18 Shots · 180s)
- **Cấu hình tham chiếu:** **Đúng 5 ảnh cố định (4 Nhân vật Động vật + 1 Background)**.
- **Tương thích:** Tối ưu 100% cho `ltx2_5_msr.py` (`ltx-msr.py`) — áp dụng triệt để 3 fix: speech ở đầu prompt (`immediately says/shouts...`), bỏ timestamp, tên nhân vật khớp tuyệt đối `Figure X` & `Image X`.
- **Nguyên tắc vàng Giữ Phong Cách & Giọng Điệu (Character Consistency):** Từng nhân vật sở hữu bộ **Nhận diện ngoại hình cố định** kết hợp **Phong cách diễn xuất & Giọng điệu độc quyền**, được lặp lại đồng nhất 100% trong mọi prompt từ shot 1 đến shot 36.

---

# 🎭 CẤU HÌNH THAM CHIẾU NHÂN VẬT & BỐI CẢNH (DÙNG CHUNG CẢ PART 1 & PART 2)
> *Dán toàn bộ 5 mục bên dưới vào ô **① Mô tả nhân vật (`character_description`)** trên Gradio*

```text
Image 1: Figure 1, The Gaslighter Boss Cat (Tong Giang archetype): A chubby tuxedo British Shorthair cat with sleek dark grey fur, white chest patch, wearing a miniature executive navy blue necktie and small stylish rimless spectacles perched on its nose, cunning calculating amber eyes. Signature style and tone: smooth manipulative purr, pretentious patronizing sanctimonious tone, calculated pseudo-empathy, gesturing aristocratically with soft front paws, pretending collective love while guilt-tripping subordinates. Pixar-style 3D cartoon character, photorealistic render quality.

Image 2: Figure 2, The Rageholic Bulldog ID (Ly Quy archetype): A muscular fawn French Bulldog with wrinkled furrowed brow, intense fiery eyes, bulging neck veins, wearing a tiny black spiked collar. Signature style and tone: explosive comedic guttural roar, raw primal aggressive rage, loud barking cadence, violently slamming paws onto surfaces, rapidly alternating between hysterical temper tantrums and hyperbolic sobbing tragedy. Pixar-style 3D cartoon character, photorealistic render quality.

Image 3: Figure 3, The Paranoid Overthinker Raccoon (Ngo Dung archetype): A skinny neurotic raccoon with natural black bandit mask markings around eyes, wearing thick round wire-frame reading glasses and a tiny beige knitted cardigan, twitching tail and trembling paws. Signature style and tone: high-pitched trembling neurotic stutter, breathless panicked conspiracy theorist delivery, frantically pushing up glasses while drawing obsessive psychological charts. Pixar-style 3D cartoon character, photorealistic render quality.

Image 4: Figure 4, The People-Pleaser and Drama Corgi (Lam Xung archetype): A fluffy tri-color Corgi with large expressive perky bat ears, wearing a tiny crumpled blue office collar and pink bow tie, holding a small notepad. Signature style and tone: sweet passive-aggressive sing-song voice alternating between a trembling submissive whimper and a razor-sharp venomous smirk, side-eyeing with toxic mock innocence while covertly stirring chaos. Pixar-style 3D cartoon character, photorealistic render quality.

Image 5: Scene, vertical 9:16 composition, a cozy modern lounge and meeting room with warm natural lighting, a low rustic wooden coffee table in the center on a soft textured woven rug, surrounded by low comfortable leather poufs, plush armchairs, and a sofa with cushions, cinematic photorealistic interior, 4k resolution.
```

---

## 🎙️ BẢN ĐẶC TẢ PHONG CÁCH & GIỌNG ĐIỆU BẤT BIẾN CỦA 4 NHÂN VẬT

| Nhân vật | Nhãn nhận diện & Ngoại hình cố định | Phong cách diễn xuất (Acting Style) | Giọng điệu & Âm vực (Voice & Tone Delivery) |
| :--- | :--- | :--- | :--- |
| **Figure 1**<br>🐱 **Boss Mèo Gaslighter**<br>*(Tống Giang)* | `Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie)` | Bệ vệ, đĩnh đạc quý tộc giả tạo, vẫy đuôi khoan thai, một chân ôm ngực diễn vẻ tổn thương, ngón chân bấm kính trịch thượng. | **Smooth manipulative purr**: Giọng đầm ấm, êm như nhung, trịch thượng ban ơn, mang tính thao túng đạo đức giả ("Chúng ta là một gia đình..."). Khi bị dồn vào chân tường thì lắp bắp chống chế. |
| **Figure 2**<br>🐶 **Bulldog Sôi Máu**<br>*(Lý Quỳ)* | `Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar)` | Cục súc bản năng, hai chân trước đập bàn rầm rầm, mắt đỏ ngầu trợn trừng, khói xì mang tai, khi khóc thì quỳ sụp ăn vạ như đứa trẻ khổng lồ. | **Explosive guttural roar**: Giọng khàn đục sấm sét, âm lượng cực đại, gầm rú bộc phát, từ ngữ bỗ bã giang hồ, cảm xúc dao động cực đoan từ sôi máu sang khóc lóc bi ai rồi quay xe nịnh bợ. |
| **Figure 3**<br>🦝 **Gấu Mèo Hoang Tưởng**<br>*(Ngô Dụng)* | `Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask)` | Co ro, co giật đuôi liên tục, hai chân trước run lẩy bẩy cầm kính lúp soi mói hoặc vẽ loạn xạ lên bảng trắng, mắt đảo vòng xoáy ốc. | **High-pitched neurotic stutter**: Giọng the thé cao độ, lắp bắp lo âu tột cùng, thở dốc gấp gáp, luôn viện dẫn thuật ngữ tâm lý học vũ trụ và chiêm tinh học ma trận để thổi phồng bi kịch. |
| **Figure 4**<br>🦊 **Corgi Thảo Mai & Drama**<br>*(Lâm Xung)* | `Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie)` | Hai mặt tráo trở: Lúc thì tai cụp ôm sổ xin lỗi run rẩy cam chịu, lúc thì dựng thẳng tai liếc xéo sắc lẹm, lén bấm điện thoại livestream, mặt cười khẩy sát khí. | **Sweet passive-aggressive sing-song voice**: Giọng ngọt ngào thảo mai như rót mật nhưng chát chúa mỉa mai, luyến láy cà khịa sâu cay, đổi giọng từ rên rỉ oan ức sang cười man rợ giải thoát. |

---
---

# 🍿 TẬP 1 (PART 1): "VỤ ÁN TRÀ SỮA THIU & ĐÒN TÂM LÝ CHIẾN"
*(Thời lượng: 180s = 18 Shots × 10s)*

## 📌 PROMPT CHÍNH PART 1 (`prompt_main`)
> *Dán 18 phân đoạn dưới đây vào ô **② Kịch bản / Prompt chính** khi render Tập 1*

```text
Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately holds up a magnifying glass over an empty boba cup in its signature high-pitched neurotic trembling stutter and sputters with wild existential paranoia Đây không đơn thuần là ly trà sữa bị hút trộm! Đây là một đòn tâm lý chiến nhằm tiêu diệt niềm tin nội bộ! frantically adjusting thick wire glasses with twitching paws as red conspiracy strings on the whiteboard loom behind. Consistent character appearance, continuous vertical locked 9:16 shot, cozy modern meeting room, no morphing, stable cinematic lighting.

Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately leans forward in its signature smooth manipulative purr and lectures with calculated pseudo-empathy Chúng ta là một gia đình... Kẻ trộm trà sữa không có lỗi, lỗi là cả phòng đã không đủ bao dung để chia sẻ! gesturing smoothly with velvet paws, tilting its head pompously and pushing up rimless spectacles with patronizing arrogance. Consistent character appearance, continuous locked 9:16 take, cozy meeting room, stable lighting.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately slams both front paws violently onto the coffee table in its signature explosive guttural roar and barks with raw primal fury Bao dung cái con khỉ! Đứa nào uống cạn trân châu hoàng kim của tao? Bước ra đây solo 1 mất 1 còn! with wrinkled red face, neck veins bulging, teeth bared in cartoon comedic rage straight toward the camera. Consistent character appearance, continuous locked 9:16 take, cozy meeting room, no cuts.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately cowers in its seat hugging an apology notepad in its signature submissive trembling whimper and whines with watery guilty eyes Em xin lỗi cả nhà... Dù em mới đi vệ sinh vào, nhưng chắc chắn là do hào quang tội lỗi của em gây ra! with bat ears drooping, mouth quivering in a tortured polite people-pleaser smile. Consistent character appearance, continuous locked 9:16 take, cozy meeting room, natural shivers.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately perks its bat ears upright, casting a razor-sharp judgmental side-eye in its signature sweet passive-aggressive sing-song voice and whispers loudly with venomous mock innocence Em không có ý phán xét đâu nha, nhưng ai đó mang tiếng sếp lớn ăn cá hồi mà đi tiếc ly trà sữa 30k thì hơi bần đấy ạ! with a toxic sweet smirk. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately puffs its white chest out pompously in its signature pretentious patronizing purr and proclaims with supreme baseless arrogance Với tư duy lãnh đạo đỉnh cao của loài mèo, tôi khẳng định đây là bài test tâm lý do ban giám đốc cài vào! raising a sharp claw in condescending authority, swinging its fluffy tail smugly. Consistent character appearance, continuous locked 9:16 take, cozy meeting room, no morphing.

Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately grabs two squeaking markers, frantically sketching interconnected diagrams on the whiteboard in its signature high-pitched neurotic stutter and gasps breathlessly Theo ma trận tâm lý tội phạm học: Ly trà sữa bị uống lúc 3h15 phút... trùng khớp với giờ sao Thủy nghịch hành! spinning toward the camera with wide terrified spiraling eyes. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately clutches its chest theatrically with paws in its signature hypocritical guilt-tripping wail and laments with fake crocodile tears Các em làm tôi đau lòng quá! Nếu ngày mai công ty phá sản, chính là vì sự ích kỷ của từng người trong phòng này! shaking whiskers in tragic emotional blackmail. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately collapses onto the woven rug, hugging the empty boba cup to its wrinkly cheek in its signature hyperbolic sobbing howl and wails toward the ceiling in melodramatic despair Trân châu ơi sao mày bỏ tao đi... Tao đã dặn thêm 70% đường 30% đá mà bọn ác nhân nỡ cướp mất! weeping comic waterfall tears. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately hides a smartphone under the wooden table in its signature mischievous conspiratorial whisper and giggles gleefully into the livestream camera Alo mạng xã hội ơi! Team em đang đấu tố sinh tử vì ly trà sữa, vào xem drama nghìn mắt xem sếp mèo diễn xiếc nào! eyes glittering with dark voyeuristic delight. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately snaps, violently tearing the apology notepad to shreds with teeth and paws in its signature unhinged psychotic shriek and screams with manic liberation Đủ rồi! Tôi nhịn các người suốt 3 năm nay rồi! Tôi không nhận lỗi nữa, tôi nguyền rủa tất cả các người! eyes wide, unhinged toothy grin. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately flips sides, clapping front paws enthusiastically in its signature loud comedic barking cadence and roars with mutinous excitement Chí lý! Tôi đồng ý với đồng chí Corgi! Khởi nghĩa đi! Lương Sơn Bạc công sở muôn năm! wagging its stubby tail in wild herd mentality. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately sits amidst scattered papers, holding its furry head with trembling paws in its signature breathy neurotic stammer and groans in cognitive breakdown Nếu ai cũng là nạn nhân... thì ai là thủ phạm? Trà sữa có thật không hay chỉ là ảo ảnh của tiềm thức?! with dazed swirling pupils. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately freezes as an overhead spotlight reveals glossy brown boba syrup smeared across its white whiskers and pink nose, in its signature guilty stammering squeak and gasps in pale narcissistic shock Vết... vết này là sốt cá hồi hữu cơ tôi ăn từ sáng... Thề có trời đất chứng giám tôi không hề... ears twitching in pure humiliation. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately points a trembling front paw at Figure 1 syrup-stained face in its signature thunderous betrayed bark and shouts in cartoon heartbreak Mày bảo Chúng ta là một gia đình... mà mày lại lén hút hết 100% đường của tao hả con mèo kia?! jaw dropping to the floor in exaggerated shock. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately cowers into the corner, pointing both paws toward the office refrigerator in its signature high-pitched conspiratorial chatter and squeaks desperately Đây rõ ràng là lỗi của phong thủy chiếc tủ lạnh! Chiếc tủ lạnh có tần số năng lượng độc hại phát ra sóng thao túng! tail shivering in absurd projection. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately pushes a trash bin forward, dusting its paws in its signature cold deadpan sing-song cadence and drops the bombshell with a soul-crushing smirk Mà quên chưa nói: Ly trà sữa đó của con bé thực tập để quên từ tuần trước thiu ngắt rồi, anh mèo hút ngon miệng ghê! looking directly at camera. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

All 4 animal characters immediately freeze simultaneously as Figure 1 tuxedo boss cat clutches its rumbling stomach in sheer panic, immediately looks into the camera in its signature pompous yet agonizing purr and announces Tâm lý học hành vi chứng minh rằng: 99% drama trên đời sinh ra từ việc... rảnh rỗi sinh nông nổi! while Figure 2 bulldog and Figure 3 raccoon gag in disgust and Figure 4 corgi grins smugly, all 4 slowly turning heads deadpan toward camera. Consistent character appearance, continuous locked 9:16 wide shot, cozy meeting room.
```

---

## 🎙️ BẢNG CHI TIẾT 18 PHÂN ĐOẠN PART 1

| Shot | Nhân vật & Diễn xuất | Thiên kiến tâm lý | Phong cách & Giọng điệu cố định | Lời thoại [SPEECH] & SFX |
| :--- | :--- | :--- | :--- | :--- |
| **Shot 1**<br>*(10s)* | 🦝 **Figure 3 (Raccoon)**<br>Cầm kính lúp soi ly rỗng, chỉnh kính tròn dày | **Paranoia / Confirmation Bias** | Giọng the thé, lắp bắp lo âu tột độ, thở dốc gấp gáp | *(SFX: Tim đập & Violin rùng rợn)*<br>🦝 *"Đây không đơn thuần là ly trà sữa bị hút trộm! Đây là một đòn tâm lý chiến nhằm tiêu diệt niềm tin nội bộ!"* |
| **Shot 2**<br>*(10s)* | 🐱 **Figure 1 (Boss Cat)**<br>Vuốt cà vạt navy, đẩy kính không gọng, vẫy đuôi | **Gaslighting / Machiavellianism** | Giọng đầm ấm êm như nhung, trịch thượng ban ơn giả tạo | *(SFX: Đàn hạc du dương giả nhân giả nghĩa)*<br>🐱 *"Chúng ta là một gia đình... Kẻ trộm trà sữa không có lỗi, lỗi là cả phòng đã không đủ bao dung để chia sẻ!"* |
| **Shot 3**<br>*(10s)* | 🐶 **Figure 2 (Bulldog)**<br>Đập rầm hai chân xuống bàn, gân cổ nổi cuồn cuộn | **Primal Aggression (Id Instinct)** | Giọng khàn đục sấm sét, gầm rú bộc phát sùi bọt mép | *(SFX: RẦM! Còi báo động khẩn cấp)*<br>🐶 *"Bao dung cái con khỉ! Đứa nào uống cạn trân châu hoàng kim của tao? Bước ra đây solo 1 mất 1 còn!"* |
| **Shot 4**<br>*(10s)* | 🦊 **Figure 4 (Corgi)**<br>Cụp tai to, ôm sổ xin lỗi, miệng cười gượng run rẩy | **People-Pleasing / Stockholm** | Giọng run rẩy cam chịu, rên rỉ đóng vai tội đồ | *(SFX: Tiếng dế kêu thê lương)*<br>🦊 *"Em xin lỗi cả nhà... Dù em mới đi vệ sinh vào, nhưng chắc chắn là do hào quang tội lỗi của em gây ra!"* |
| **Shot 5**<br>*(10s)* | 💅 **Figure 4 (Corgi)**<br>Dựng tai thẳng đứng, liếc xéo sắc lẹm, cười nhếch mép | **Passive-Aggressive / Comparison** | Giọng ngọt ngào thảo mai, luyến láy cà khịa chát chúa | *(SFX: Tiếng mèo cào móng & Rắn rít)*<br>💅 *"Em không có ý phán xét đâu nha, nhưng ai đó mang tiếng sếp lớn ăn cá hồi mà đi tiếc ly trà sữa 30k thì hơi bần đấy ạ!"* |
| **Shot 6**<br>*(10s)* | 👑 **Figure 1 (Boss Cat)**<br>Ưỡn ngực lông trắng, giơ móng chỉ trỏ trịch thượng | **Dunning-Kruger Effect** | Giọng kiêu ngạo tự mãn, phong thái lãnh đạo ảo tưởng | *(SFX: Kèn bóp hề Boing Boing)*<br>👑 *"Với tư duy lãnh đạo đỉnh cao của loài mèo, tôi khẳng định đây là bài test tâm lý do ban giám đốc cài vào!"* |
| **Shot 7**<br>*(10s)* | 📊 **Figure 3 (Raccoon)**<br>Quẹt 2 bút lông vẽ ma trận bảng trắng, mắt trợn tròn | **Analysis Paralysis / Conspiracy** | Giọng the thé hụt hơi, dồn dập hoang tưởng vũ trụ | *(SFX: Bút lông quẹt xoèn xoẹt & Đèn chớp)*<br>📊 *"Theo ma trận tâm lý tội phạm học: Ly trà sữa bị uống lúc 3h15 phút... trùng khớp với giờ sao Thủy nghịch hành!"* |
| **Shot 8**<br>*(10s)* | 😿 **Figure 1 (Boss Cat)**<br>Gạt nước mắt cá sấu, rung râu bi thương diễn kịch | **Guilt-Tripping / Emotional Blackmail** | Giọng hờn dỗi tống tiền cảm xúc, thê lương bi ai giả vờ | *(SFX: Đàn bầu sầu thảm & Sấm chớp)*<br>😿 *"Các em làm tôi đau lòng quá! Nếu ngày mai công ty phá sản, chính là vì sự ích kỷ của từng người trong phòng này!"* |
| **Shot 9**<br>*(10s)* | 😭 **Figure 2 (Bulldog)**<br>Quỳ sụp ôm ly rỗng áp vào má nhăn, ngửa cổ hú trời | **Loss Aversion / Hyperbolic Grief** | Giọng gào khóc bi thảm cực đoan như hát cải lương | *(SFX: Mưa rơi tầm tã & Đàn nhị não nề)*<br>😭 *"Trân châu ơi sao mày bỏ tao đi... Tao đã dặn thêm 70% đường 30% đá mà bọn ác nhân nỡ cướp mất!"* |
| **Shot 10**<br>*(10s)* | 📱 **Figure 4 (Corgi)**<br>Giấu điện thoại gầm bàn livestream, che miệng khúc khích | **Schadenfreude / Voyeurism** | Giọng thì thầm hóng hớt, cười rúc rích khoái chí | *(SFX: Ting ting livestream & Bão tim bay)*<br>📱 *"Alo mạng xã hội ơi! Team em đang đấu tố sinh tử vì ly trà sữa, vào xem drama nghìn mắt xem sếp mèo diễn xiếc nào!"* |
| **Shot 11**<br>*(10s)* | 😈 **Figure 4 (Corgi)**<br>Nhe răng xé nát sổ xin lỗi, mắt long sòng sọc cười điên | **Catharsis / Reaction Formation** | Giọng gào thét cuồng loạn, cười man dại giải thoát | *(SFX: Kính vỡ XOẢNG & Nhạc Rock rách tai)*<br>😈 *"Đủ rồi! Tôi nhịn các người suốt 3 năm nay rồi! Tôi không nhận lỗi nữa, tôi nguyền rủa tất cả các người!"* |
| **Shot 12**<br>*(10s)* | 🚩 **Figure 2 (Bulldog)**<br>Vỗ tay bôm bốp, ngoáy đuôi cụt, giơ nắm đấm hò reo | **Bandwagon Effect / Herd Mentality** | Giọng sủa nhí nhảnh quay xe, hào sảng ba phải | *(SFX: Còi xe quay đầu & Tiếng hò reo)*<br>🚩 *"Chí lý! Tôi đồng ý với đồng chí Corgi! Khởi nghĩa đi! Lương Sơn Bạc công sở muôn năm!"* |
| **Shot 13**<br>*(10s)* | 🌀 **Figure 3 (Raccoon)**<br>Ngồi bệt ôm đầu xoay tròn, mắt hoa xoáy ốc đơ toàn tập | **Cognitive Dissonance / System Overload** | Giọng lắp bắp đứt quãng, triết lý hư vô bế tắc | *(SFX: Rè sóng radio mất đài & Ong kêu)*<br>🌀 *"Nếu ai cũng là nạn nhân... thì ai là thủ phạm? Trà sữa có thật không hay chỉ là ảo ảnh của tiềm thức?!"* |
| **Shot 14**<br>*(10s)* | 😱 **Figure 1 (Boss Cat)**<br>Đèn rọi ria mép dính siro nâu óng, mặt tái mét thụt tai | **Narcissistic Collapse / Red-Handed** | Giọng lí nhí lắp bắp, mất sạch vẻ đạo mạo bề trên | *(SFX: Kim rơi TENG! & Spotlight rọi)*<br>😱 *"Vết... vết này là sốt cá hồi hữu cơ tôi ăn từ sáng... Thề có trời đất chứng giám tôi không hề..."* |
| **Shot 15**<br>*(10s)* | 💔 **Figure 2 (Bulldog)**<br>Chỉ chân run rẩy vào ria Boss Mèo, hàm rớt chạm đất | **Betrayal Trauma / Disillusionment** | Giọng sấm sét nứt vỡ giữa phẫn nộ và tan nát con tim | *(SFX: Sét đánh ÙNG OÀNG & Đàn cò ai oán)*<br>💔 *"Mày bảo Chúng ta là một gia đình... mà mày lại lén hút hết 100% đường của tao hả con mèo kia?!"* |
| **Shot 16**<br>*(10s)* | 🚪 **Figure 3 (Raccoon)**<br>Núp sau góc phòng, chỉ 2 chân về chiếc tủ lạnh xua đuổi | **Psychological Projection / Scapegoat** | Giọng rít hoảng loạn, dựng chuyện mê tín dị đoan | *(SFX: Tiếng gió ma mị hú u ám)*<br>🚪 *"Đây rõ ràng là lỗi của phong thủy chiếc tủ lạnh! Chiếc tủ lạnh có tần số năng lượng độc hại phát ra sóng thao túng!"* |
| **Shot 17**<br>*(10s)* | 🧋 **Figure 4 (Corgi)**<br>Đẩy sọt rác, phủi chân trước, cười nhếch mép khinh bỉ | **The Reality Check / Anti-Climax** | Giọng lạnh lùng tỉnh rụi (deadpan), cà khịa đòn chí mạng | *(SFX: Tiếng Ủa alo? cực vang & Dạ dày sôi)*<br>🧋 *"Mà quên chưa nói: Ly trà sữa đó của con bé thực tập để quên từ tuần trước thiu ngắt rồi, anh mèo hút ngon miệng ghê!"* |
| **Shot 18**<br>*(10s)* | 🤡 **Cả 4 Nhân Vật**<br>Mèo ôm bụng quằn quại, Chó & Raccoon nôn ọe, nhìn camera | **Collective Catharsis / Shared Folly** | Boss Mèo rên rỉ ngạo mạn, cả 4 nhìn camera cười trừ | *(SFX: Quạ kêu Quạ... & Meme Outro)*<br>🤡 *"Tâm lý học hành vi chứng minh rằng: 99% drama trên đời sinh ra từ việc... rảnh rỗi sinh nông nổi!"* |

---
---

# 🚀 TẬP 2 (PART 2): "CƠN ĐỊA CHẤN TIÊU HÓA & ĐẠI HỌA SA THẢI"
*(Thời lượng: 180s = 18 Shots × 10s · Tiếp nối ngay sau cú sốc trà sữa thiu)*

## 📖 TÓM TẮT CỐT TRUYỆN PART 2:
Sau khi trúng độc vì hút trọn ly trà thiu 7 ngày, Boss Mèo vật vã ôm bụng nhưng cái tôi ái kỷ không cho phép hắn thừa nhận. Hắn khởi xướng chiến dịch "săn lùng nội gián". Corgi khéo léo dùng thủ thuật ly gián (Triangulation) đẩy Bulldog và Raccoon vào cuộc ẩu đả tranh giành ngôi vị "Quyền Giám Đốc" trước khi Sếp bò vào toilet lâm chung. Đến khi Boss Mèo bước ra với tâm thế "ngộ đạo luân xa", Corgi giáng đòn chí mạng bằng email sa thải tập thể từ Ban Giám Đốc do livestream lọt Top 1 Trending TikTok. Cả phòng ngậm ngùi ôm thùng carton mở livestream bán hàng online.

---

## 📌 PROMPT CHÍNH PART 2 (`prompt_main`)
> *Dán 18 phân đoạn dưới đây vào ô **② Kịch bản / Prompt chính** khi render Tập 2*

```text
Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately clutches its violently rumbling stomach with trembling paws, cold sweat dripping down grey fur, in its signature pretentious yet agonizing purr and groans in stubborn cognitive dissonance Cơn đau bụng này không phải do trúng thực, mà là phản ứng thanh lọc độc tố của một cơ thể lãnh đạo thanh khiết! amber eyes bulging while striving to uphold arrogant dignity. Consistent character appearance, continuous locked 9:16 vertical take, cozy meeting room, no cuts.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately pulls out a toy medical kit in its signature explosive panicked bark and shouts with frantic comic urgency Thanh lọc cái đầu ông! Mặt ông xanh như tàu lá chuối rồi kìa! Đứa nào gọi cấp cứu đi chứ tao chỉ biết bấm cắn người thôi! wrinkled brow trembling in comical bystander diffusion. Consistent character appearance, continuous locked 9:16 take, cozy meeting room, no morphing.

Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately rolls down a trauma chart on the whiteboard in its signature high-pitched breathless neurotic stutter and lectures in fundamental attribution error Theo thuyết quy kết căn bản: Cơn tiêu chảy của sếp chính là nghiệp báo vũ trụ trừng phạt tội thao túng tâm lý nhân viên! tail twitching frantically while tapping chart with a pointer. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately tiptoes behind Figure 1 boss cat in its signature sweet venomous whisper and stirs malicious triangulation Anh Mèo ơi, em nghe đồn con Bulldog hôm qua cố tình đổi nhãn dán ly trà thiu để đầu độc anh cướp ghế giám đốc đấy ạ! with a toxic devious smirk and glittering mischievous eyes. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately slams an office stapler violently onto the table in its signature vindictive tyrannical hiss and spits through clenched teeth Tôi biết ngay mà! Con Bulldog mang mầm mống phản trắc! Toàn phòng này bị trừ 6 tháng tiền thưởng và đi học lại khóa học Đạo đức công sở! fur standing on end in retaliatory paranoia. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately flips the wooden coffee table upside down in its signature thunderous guttural roar and bellows with catastrophic reactive aggression Trừ tiền thưởng cái lông mày! Tao cày bừa như trâu 5 năm nay mà mày dám vu oan tao đầu độc hả con mèo lươn lẹo?! throwing cushions as cartoon steam shoots from ears. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately jumps onto a leather pouf, waving a white toilet paper flag in its signature high-pitched trembling squeak and pleads in toxic Stockholm syndrome Các đồng chí ơi đình chiến đi! Nếu chúng ta cùng nhau quỳ xuống xin lỗi sếp, năng lượng chữa lành tập thể sẽ làm êm dạ dày sếp! shivering in panic. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately turns to Figure 3 in its signature sweet passive-aggressive wail and plays the victim with dramatic crocodile tears Sao anh Raccoon lại kích động bạo lực nội bộ? Em chỉ là đứa nhân viên thấp cổ bé họng muốn mọi người yêu thương nhau thôi mà! clutching paws to chest in perfect DARVO reversal. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately doubles over in gastrointestinal torment, crawling toward the restroom door in its signature dying wheeze and gasps with fading illusion of control Trước khi... tôi lâm vào cửa tử trong toilet... tôi sẽ lập di chúc bổ nhiệm kẻ trung thành nhất làm Quyền Giám Đốc! dragging belly with theatrical despair. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately drops all anger, standing rigid at attention in its signature eager comedic bark and barks with instant Pavlovian sycophancy Dạ sếp! Em xin tình nguyện hy sinh gánh vác ngai vàng! Em thề sẽ cắn chết bất cứ đứa nào dám ho he chống đối sếp! wagging stubby tail with an absurd greedy grin. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately dons a shiny foil hat, waving a whiteboard marker like a sceptre in its signature shrill megalomaniacal shriek and proclaims with grandiose delusion Khoan đã! Theo chỉ số IQ 300 và bản đồ sao chiêm tinh, chỉ có ta mới đủ năng lực dẫn dắt bộ tộc này qua cơn đại hồng thủy! pupils swirling in hubris. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately adjusts its pink bow tie, leaning close to the hidden phone in its signature chilling Machiavellian whisper and chuckles darkly to the livestream Nhìn hai con rối đang cắn xé nhau vì cái ghế tạm quyền kìa... Mọi chuyện đang diễn ra đúng 100% theo kịch bản thao túng hắc ám của tôi! ears perked in toxic triumph. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately grabs Figure 3 raccoon by its beige cardigan, shaking it violently in its signature explosive guttural roar and barks in zero-sum fury Ghế quyền lực này là của tao! Khôn hồn thì lui ra con gấu mèo hôi hám! while Figure 3 pokes Figure 2 face with markers in slapstick combat. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 1 (tuxedo boss cat with sleek dark grey fur, white chest patch, rimless glasses, and navy necktie) immediately kicks open the restroom door in slow-motion, trailing toilet paper from its hind paw, in its signature pompous pseudo-spiritual purr and announces with radiant halo delusion Sau 15 phút ngộ đạo giữa lằn ranh sinh tử, tôi đã khai mở luân xa thứ 7 và nhìn thấu sự vô thường của quyền lực công sở! with hands clasped in fake zen. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 4 (fluffy tri-color corgi with perky bat ears, blue office collar, and pink bow tie) immediately strides forward holding an iPad displaying a flashing red notice in its signature sweet deadpan voice and delivers the coup de grâce with an icy smirk Sếp ngộ đạo xong chưa ạ? Ban Giám Đốc vừa gửi trát sa thải tập thể cả phòng vì livestream đấu tố nội bộ lọt top 1 xu hướng TikTok 10 triệu view rồi kìa! eyes gleaming with schadenfreude. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 2 (muscular fawn bulldog with wrinkled brow, fiery eyes, neck veins, and black spiked collar) immediately freezes in mid-punch, dropping its marker, in its signature catastrophic panicked howl and screams with jaw dropping to the floor 10 triệu view?! Mẹ tao ở quê vừa thả tim video tao cắn rách áo sếp rồi! Đời tao coi như tàn phế! popping eyes in complete social ruin. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

Figure 3 (skinny neurotic raccoon with round wire glasses, beige knitted cardigan, and black eye mask) immediately flops flat onto the rug in a starfish pose, staring at the ceiling in its signature hollow nihilistic sigh and murmurs in total existential surrender Thất nghiệp thực chất là một sự giải phóng năng lượng lượng tử... Chúng ta đã hoàn toàn tự do khỏi ma trận tư bản... with deadpan spiral eyes. Consistent character appearance, continuous locked 9:16 take, cozy meeting room.

All 4 animal characters immediately stand in a lineup holding packed cardboard boxes, Figure 1 boss cat wearing sunglasses with a mini briefcase, Figure 2 bulldog clutching a dog bowl, Figure 3 raccoon holding its whiteboard, Figure 4 corgi holding a selfie stick, as Figure 1 immediately looks straight into camera in its signature resilient pompous purr and concludes Tâm lý học hành vi đúc kết bài học cuối: Khi công ty cháy... đứa thông minh nhất là đứa biết mở livestream bán hàng online! all 4 freezing simultaneously in an absurd viral TikTok creator meme pose. Consistent character appearance, continuous locked 9:16 wide shot, cozy meeting room.
```

---

## 🎙️ BẢNG CHI TIẾT 18 PHÂN ĐOẠN PART 2

| Shot | Nhân vật & Diễn xuất | Thiên kiến tâm lý | Phong cách & Giọng điệu cố định | Lời thoại [SPEECH] & SFX |
| :--- | :--- | :--- | :--- | :--- |
| **Shot 1**<br>*(10s)* | 🐱 **Figure 1 (Boss Cat)**<br>Ôm bụng sôi ùng ục, mồ hôi hột rơi, cố gồng nét quý phái | **Cognitive Dissonance / Rationalization** | Giọng đầm ấm rên rỉ nghẹn ngào, cố giữ vẻ bề trên ngạo mạn | *(SFX: Dạ dày sôi sấm sét & Cello rên rỉ)*<br>🐱 *"Cơn đau bụng này không phải do trúng thực, mà là phản ứng thanh lọc độc tố của một cơ thể lãnh đạo thanh khiết!"* |
| **Shot 2**<br>*(10s)* | 🐶 **Figure 2 (Bulldog)**<br>Lôi vali đồ chơi cứu thương, mặt nhăn cuống cuồng | **Bystander Effect / Diffusion** | Giọng khàn gắt hoảng loạn, sủa dồn dập đùn đẩy trách nhiệm | *(SFX: Còi xe cứu thương réo inh ỏi)*<br>🐶 *"Thanh lọc cái đầu ông! Mặt ông xanh như tàu lá chuối rồi kìa! Đứa nào gọi cấp cứu đi chứ tao chỉ biết bấm cắn người thôi!"* |
| **Shot 3**<br>*(10s)* | 🦝 **Figure 3 (Raccoon)**<br>Kéo biểu đồ chấn thương, gõ côm cốp, đuôi giật tít | **Fundamental Attribution Error** | Giọng the thé hụt hơi, lên lớp đạo lý quy kết nghiệp báo | *(SFX: Tiếng gõ thước côm cốp & Chuông chùa)*<br>🦝 *"Theo thuyết quy kết căn bản: Cơn tiêu chảy của sếp chính là nghiệp báo vũ trụ trừng phạt tội thao túng tâm lý nhân viên!"* |
| **Shot 4**<br>*(10s)* | 🐍 **Figure 4 (Corgi)**<br>Rón rén ghé tai Boss Mèo, liếc mắt hiểm hóc thì thầm | **Triangulation / Malicious Rumor** | Giọng ngọt như mía lùi thảo mai, thì thầm đâm bị thóc chọc bị gạo | *(SFX: Rắn thè lưỡi phì phì & Trống dồn dập)*<br>🐍 *"Anh Mèo ơi, em nghe đồn con Bulldog hôm qua cố tình đổi nhãn dán ly trà thiu để đầu độc anh cướp ghế giám đốc đấy ạ!"* |
| **Shot 5**<br>*(10s)* | 🤬 **Figure 1 (Boss Cat)**<br>Đập dập ghim rầm rầm, mắt long sòng sọc, dựng lông | **Horn Effect / Scapegoating 2.0** | Giọng rít qua kẽ răng cay nghiệt, kết án độc tài trừng phạt | *(SFX: Tiếng sập bẫy sắt XOẢNG & Sấm sét)*<br>🤬 *"Tôi biết ngay mà! Con Bulldog mang mầm mống phản trắc! Toàn phòng này bị trừ 6 tháng tiền thưởng và đi học lại khóa học Đạo đức công sở!"* |
| **Shot 6**<br>*(10s)* | 🔥 **Figure 2 (Bulldog)**<br>Lật tung bàn trà gỗ, ném gối ôm, khói xì hai mang tai | **Reactive Aggression / Burnout Rage** | Giọng gầm sấm sét bùng nổ, gào thét uất ức tột đỉnh | *(SFX: BÀN GỖ ĐỔ RẦM! & Tiếng bom nổ)*<br>🔥 *"Trừ tiền thưởng cái lông mày! Tao cày bừa như trâu 5 năm nay mà mày dám vu oan tao đầu độc hả con mèo lươn lẹo?!"* |
| **Shot 7**<br>*(10s)* | 🏳️ **Figure 3 (Raccoon)**<br>Nhảy lên đôn da vẫy cờ giấy vệ sinh, run lẩy bẩy | **Stockholm Syndrome / Submission** | Giọng the thé van xin cam chịu, hèn nhát cầu hòa | *(SFX: Tiếng đàn Ukulele thê lương)*<br>🏳️ *"Các đồng chí ơi đình chiến đi! Nếu chúng ta cùng nhau quỳ xuống xin lỗi sếp, năng lượng chữa lành tập thể sẽ làm êm dạ dày sếp!"* |
| **Shot 8**<br>*(10s)* | 🎭 **Figure 4 (Corgi)**<br>Ôm ngực khóc nức nở, rớt nước mắt cá sấu đóng kịch | **DARVO (Deny, Attack, Reverse Victim)** | Giọng nức nở ăn vạ, đổi trắng thay đen đổ tội ngược | *(SFX: Nhạc kịch bi tráng & Tiếng vỗ tay hề)*<br>🎭 *"Sao anh Raccoon lại kích động bạo lực nội bộ? Em chỉ là đứa nhân viên thấp cổ bé họng muốn mọi người yêu thương nhau thôi mà!"* |
| **Shot 9**<br>*(10s)* | 🚽 **Figure 1 (Boss Cat)**<br>Bò lê lết bấu cửa toilet, quằn quại trăn trối di chúc | **Illusion of Control / Scarcity** | Giọng thều thào hấp hối, ảo tưởng quyền lực phút chót | *(SFX: Tiếng tim đập yếu ớt & Kèn đám ma)*<br>🚽 *"Trước khi... tôi lâm vào cửa tử trong toilet... tôi sẽ lập di chúc bổ nhiệm kẻ trung thành nhất làm Quyền Giám Đốc!"* |
| **Shot 10**<br>*(10s)* | 🐶 **Figure 2 (Bulldog)**<br>Đứng nghiêm chào cờ, cười nhe răng toe toét, lắc đuôi | **Pavlovian Conditioning / Greed** | Giọng sủa hớn hở nịnh bợ, phản xạ trước mồi nhử chức quyền | *(SFX: Ting Ting tiếng tiền vàng rơi)*<br>🐶 *"Dạ sếp! Em xin tình nguyện hy sinh gánh vác ngai vàng! Em thề sẽ cắn chết bất cứ đứa nào dám ho he chống đối sếp!"* |
| **Shot 11**<br>*(10s)* | 👑 **Figure 3 (Raccoon)**<br>Đội mũ giấy bạc, vung bút lông làm quyền trượng | **Megalomania / Dunning-Kruger** | Giọng the thé ảo tưởng vĩ cuồng, phong vương tự xưng | *(SFX: Nhạc giao hưởng đăng quang hoàng gia)*<br>👑 *"Khoan đã! Theo chỉ số IQ 300 và bản đồ sao chiêm tinh, chỉ có ta mới đủ năng lực dẫn dắt bộ tộc này qua cơn đại hồng thủy!"* |
| **Shot 12**<br>*(10s)* | 📱 **Figure 4 (Corgi)**<br>Chỉnh nơ hồng, ghé sát điện thoại thì thầm đắc thắng | **Machiavellianism / Dark Triad** | Giọng thì thầm hiểm ác giật dây, cười khẩy lạnh người | *(SFX: Tiếng cười ác ma Hehehe & Bão tim)*<br>📱 *"Nhìn hai con rối đang cắn xé nhau vì cái ghế tạm quyền kìa... Mọi chuyện đang diễn ra đúng 100% theo kịch bản thao túng hắc ám của tôi!"* |
| **Shot 13**<br>*(10s)* | 🤼 **Figure 2 & 3**<br>Bulldog túm áo len Raccoon, Raccoon chọc bút lông | **Zero-Sum Game / Escalation** | Bulldog gầm gừ độc chiếm, tranh đấu mất nhân tính | *(SFX: Tiếng mèo chó ẩu đả náo loạn)*<br>🤼 *"Ghế quyền lực này là của tao! Khôn hồn thì lui ra con gấu mèo hôi hám!"* |
| **Shot 14**<br>*(10s)* | ✨ **Figure 1 (Boss Cat)**<br>Tung cửa toilet, chân dính giấy vệ sinh, chắp tay zen | **Spiritual Bypassing / Halo Effect** | Giọng đầm ấm thanh cao giả tạo, thuyết giảng ngộ đạo | *(SFX: Hào quang thánh ca Aaaa & Xả nước)*<br>✨ *"Sau 15 phút ngộ đạo giữa lằn ranh sinh tử, tôi đã khai mở luân xa thứ 7 và nhìn thấu sự vô thường của quyền lực công sở!"* |
| **Shot 15**<br>*(10s)* | 📄 **Figure 4 (Corgi)**<br>Giơ iPad hiện trát sa thải viền đỏ, cười khẩy kết liễu | **Schadenfreude / Reality Check** | Giọng ngọt ngào tỉnh queo (deadpan), tung cú tát thực tế | *(SFX: Sét đánh sụp trần & Chuông báo email)*<br>📄 *"Sếp ngộ đạo xong chưa ạ? Ban Giám Đốc vừa gửi trát sa thải tập thể cả phòng vì livestream đấu tố nội bộ lọt top 1 xu hướng TikTok 10 triệu view rồi kìa!"* |
| **Shot 16**<br>*(10s)* | 😱 **Figure 2 (Bulldog)**<br>Đứng hình rơi bút, hàm chạm đất, mắt lồi kinh hoàng | **Panic Breakdown / Social Ruin** | Giọng gào thét tuyệt vọng, khủng hoảng thanh danh gia đình | *(SFX: Đĩa vỡ XOẢNG & Nhạc phim kinh dị)*<br>😱 *"10 triệu view?! Mẹ tao ở quê vừa thả tim video tao cắn rách áo sếp rồi! Đời tao coi như tàn phế!"* |
| **Shot 17**<br>*(10s)* | 🌌 **Figure 3 (Raccoon)**<br>Nằm ngửa sao biển trên thảm, mắt xoáy ốc thở dài | **Existential Nihilism / Surrender** | Giọng thều thào buông xuôi, chấp nhận hư vô giải thoát | *(SFX: Gió thổi hiu hắt phù phù & Lá rụng)*<br>🌌 *"Thất nghiệp thực chất là một sự giải phóng năng lượng lượng tử... Chúng ta đã hoàn toàn tự do khỏi ma trận tư bản..."* |
| **Shot 18**<br>*(10s)* | 📦 **Cả 4 Nhân Vật**<br>Ôm thùng carton, đeo kính râm cầm gậy selfie tạo dáng | **The Final Satire / Monetization** | Boss Mèo chốt hạ đanh thép, cả 4 nhìn camera meme | *(SFX: Nhạc TikTok Remix giật cục & Đing)*<br>📦 *"Tâm lý học hành vi đúc kết bài học cuối: Khi công ty cháy... đứa thông minh nhất là đứa biết mở livestream bán hàng online!"* |

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
