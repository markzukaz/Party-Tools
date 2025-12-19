import streamlit as st
import random
import time
import json
import streamlit.components.v1 as components
import re
st.set_page_config(page_title="Party Tools", page_icon="🎡", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
def shuffle_avoid_adjacent_same(items, max_tries=50):
    """
    Shuffle list so that no identical neighbors exist (best effort).
    If impossible (e.g. too many duplicates), it will try and return best attempt.
    """
    if len(items) <= 2:
        return items[:]

    best = items[:]
    best_bad = float("inf")

    for _ in range(max_tries):
        arr = items[:]
        random.shuffle(arr)
        bad = sum(1 for i in range(1, len(arr)) if arr[i] == arr[i - 1])
        if bad == 0:
            return arr
        if bad < best_bad:
            best_bad = bad
            best = arr

    # fallback: greedy fix
    arr = best[:]
    for i in range(1, len(arr)):
        if arr[i] == arr[i - 1]:
            # find a later different element and swap
            j = None
            for k in range(i + 1, len(arr)):
                if arr[k] != arr[i - 1]:
                    j = k
                    break
            if j is not None:
                arr[i], arr[j] = arr[j], arr[i]
    return arr


def expand_weighted_labels(punish_items):
    """
    Expand list by weight -> ["ดื่ม 3 วินาที", "ดื่ม 3 วินาที", ...]
    and then shuffle to avoid duplicates adjacent.
    """
    expanded = []
    for it in punish_items:
        w = max(0, int(it.get("weight", 0)))
        if w <= 0:
            continue
        expanded.extend([str(it["label"])] * w)

    # shuffle so that same label not stuck together
    expanded = shuffle_avoid_adjacent_same(expanded, max_tries=80)
    return expanded

def parse_eel_points(label: str):
    """
    ดึงเลขหลังคำว่า 'แทงปลาไหล' เช่น '... แทงปลาไหล 40' -> 40
    ถ้าไม่มี -> None
    """
    if not label:
        return None
    m = re.search(r"แทงปลาไหล\s*(\d+)", str(label))
    return int(m.group(1)) if m else None
# -----------------------------
# State init
# -----------------------------
def init_state():
    ss = st.session_state

    # Reward wheel
    ss.setdefault("reward_pool", list(range(1, 11)))
    ss.setdefault("reward_last", None)
    ss.setdefault("reward_remove_after", False)
    ss.setdefault("reward_winner_index", None)
    ss.setdefault("reward_wheel_labels", None)  # shuffled labels for display

    # Buddy list
    ss.setdefault("buddy_list", [
    "พี่ปั๊ป",
    "น้องอ่าย",
    "พี่ป้อง",
    "หมอไนท์",
    "หมอพีท",
    "หมอกานต์",
    "พี่แบงค์",
    "พี่วัจน์",
    "ป๊อป AR",
    "แอ๊น",
    "นันทิชา",
    "พิม Asst",
    "แนน Asst.",
    "สตางค์ Admin",
    "บี๋ ACC",
    "MARK",
    "อามร์",
    "แนท DEV",
    "อีฟ Pur",
    "เจน IB",
    "โจ๊ค DRN",
    "พราว RN",
    "เมย์ RN",
    "พี่แอน RN",
    "ฟ้าใส HPH",
    "พี่บี PH",
    "แอม PH",
    "เขต",
    "แจน PH",
    "หนุงหนิง",
    "ตอง",
    "เดียร์",
    "ชมพู่",
    "มะปราง",
    "เดียร์น่า",
    "หลิน",
    "โอม PMD",
    "นัท PMD",
    "ฟ้า PMD",
    "บังเจี๊ยบ DV",
    "เมย์ HK",
    "บังหมาน DV",
    "หมูแป้ง",
    "แนน PH",
    "สมา",
    "เบญ",
    "นี",
    "เอ้",
    "ตุ๊ก",
    "หลิว",
    "จิ๋ม",
    "เมย์ IB",
    "อ้อน IB",
    "ยาหยี IB",
    "น้าพง",
    "โดม",
    "อู",
    "อาคา",
    "ปาย",
])
    ss.setdefault("selected_player", None)

    # Punishment config
    ss.setdefault("punish_items", [
        {"label": "ดื่ม 0 วินาที", "seconds": 0, "weight": 1},
        {"label": "ดื่ม 1 วินาที หรือ แทงปลาไหล 20", "seconds": 1, "weight": 1},
        {"label": "ดื่ม 2 วินาที หรือ แทงปลาไหล 30", "seconds": 2, "weight": 2},
        {"label": "ดื่ม 3 วินาที หรือ แทงปลาไหล 40", "seconds": 3, "weight": 3},
        {"label": "ดื่ม 4 วินาที หรือ แทงปลาไหล 50", "seconds": 4, "weight": 2},
        {"label": "ดื่ม 5 วินาที หรือ แทงปลาไหล 60", "seconds": 5, "weight": 1},
    ])
    ss.setdefault("punish_last", None)
    ss.setdefault("punish_remove_after", False)
    ss.setdefault("punish_winner_index", None)
    ss.setdefault("punish_wheel_labels", None)  # shuffled expanded labels for display

    # Buddy–Budder
    ss.setdefault("budder_list", [
    "พี่ปั๊ป",
    "น้องอ่าย",
    "พี่ป้อง",
    "หมอไนท์",
    "หมอพีท",
    "หมอกานต์",
    "พี่แบงค์",
    "พี่วัจน์",
    "ป๊อป AR",
    "แอ๊น",
    "นันทิชา",
    "พิม Asst",
    "แนน Asst.",
    "สตางค์ Admin",
    "บี๋ ACC",
    "MARK",
    "อามร์",
    "แนท DEV",
    "อีฟ Pur",
    "เจน IB",
    "โจ๊ค DRN",
    "พราว RN",
    "เมย์ RN",
    "พี่แอน RN",
    "ฟ้าใส HPH",
    "พี่บี PH",
    "แอม PH",
    "เขต",
    "แจน PH",
    "หนุงหนิง",
    "ตอง",
    "เดียร์",
    "ชมพู่",
    "มะปราง",
    "เดียร์น่า",
    "หลิน",
])
    ss.setdefault("pairs", [])
    ss.setdefault("selected_buddy", None)
    ss.setdefault("selected_budder", None)
    ss.setdefault("confirm_step", None)

init_state()


# -----------------------------
# Canvas Wheel Component (HTML/JS)
# - draws wheel; if winner_index passed -> animates to it
# -----------------------------
def wheel_component(labels, winner_index=None, height=560, key="wheel"):
    payload = {
        "labels": labels,
        "winnerIndex": winner_index,
        "key": key,
        "ts": int(time.time() * 1000),
    }
    data = json.dumps(payload)
    canvas_id = f"wheelCanvas_{key}"

    html = f"""
    <div style="width:100%; display:flex; justify-content:center;">
      <canvas id="{canvas_id}" width="520" height="520" style="max-width:100%;"></canvas>
    </div>

    <script>
      const payload = {data};
      const labels = payload.labels || [];
      const canvas = document.getElementById("{canvas_id}");
      const ctx = canvas.getContext("2d");

      function mulberry32(a) {{
        return function() {{
          var t = a += 0x6D2B79F5;
          t = Math.imul(t ^ t >>> 15, t | 1);
          t ^= t + Math.imul(t ^ t >>> 7, t | 61);
          return ((t ^ t >>> 14) >>> 0) / 4294967296;
        }}
      }}
      const rand = mulberry32((payload.ts >>> 0));

      function colorFor(i) {{
        const hue = (i * 360 / Math.max(1, labels.length)) % 360;
        return `hsl(${{hue}}, 70%, 55%)`;
      }}

      let angle = 0;

      function draw() {{
        const n = labels.length;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const r = Math.min(cx, cy) - 10;

        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
        ctx.lineWidth = 6;
        ctx.strokeStyle = "#222";
        ctx.stroke();

        if (n === 0) return;

        const arc = (Math.PI * 2) / n;

        for (let i = 0; i < n; i++) {{
          const start = angle + i * arc;
          const end = start + arc;

          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.arc(cx, cy, r - 6, start, end);
          ctx.closePath();
          ctx.fillStyle = colorFor(i);
          ctx.fill();

          ctx.save();
          ctx.translate(cx, cy);
          ctx.rotate(start + arc/2);
          ctx.textAlign = "right";
          ctx.fillStyle = "#111";
          ctx.font = "bold 16px sans-serif";
          const text = String(labels[i]);
          ctx.fillText(text.length > 16 ? text.slice(0, 16) + "…" : text, r - 24, 6);
          ctx.restore();
        }}

        // center
        ctx.beginPath();
        ctx.arc(cx, cy, 56, 0, Math.PI * 2);
        ctx.fillStyle = "#fff";
        ctx.fill();
        ctx.lineWidth = 4;
        ctx.strokeStyle = "#111";
        ctx.stroke();

        ctx.fillStyle = "#111";
        ctx.font = "bold 16px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("SPIN", cx, cy + 6);

        // pointer
        ctx.beginPath();
        ctx.moveTo(cx, cy - r + 6);
        ctx.lineTo(cx - 14, cy - r + 34);
        ctx.lineTo(cx + 14, cy - r + 34);
        ctx.closePath();
        ctx.fillStyle = "#111";
        ctx.fill();
      }}

      function angleForIndex(idx) {{
        const n = labels.length;
        const arc = (Math.PI * 2) / n;
        const pointerAngle = (Math.PI * 3/2);
        const sectorCenter = idx * arc + arc/2;
        return (pointerAngle - sectorCenter);
      }}

      function spinTo(idx) {{
        const n = labels.length;
        if (!n) return;

        const target = angleForIndex(idx);
        const extra = (Math.PI * 2) * (4 + Math.floor(rand() * 3)); // 4-6 รอบ
        const finalAngle = target + extra;

        const start = angle;
        const delta = finalAngle - start;
        const duration = 1800 + Math.floor(rand() * 600);
        const t0 = performance.now();

        function easeOutCubic(t) {{ return 1 - Math.pow(1 - t, 3); }}

        function frame(now) {{
          const t = Math.min(1, (now - t0) / duration);
          angle = start + delta * easeOutCubic(t);
          draw();
          if (t < 1) requestAnimationFrame(frame);
        }}
        requestAnimationFrame(frame);
      }}

      draw();

      if (typeof payload.winnerIndex === "number") {{
        setTimeout(() => spinTo(payload.winnerIndex), 200);
      }}
    </script>
    """
    return components.html(html, height=height)


# -----------------------------
# UI helpers: clickable "cards"
# -----------------------------
def card_picker(title, items, selected, key_prefix):
    st.markdown(f"### {title}")
    if not items:
        st.info("ไม่มีรายการ")
        return None

    cols = st.columns(4)
    chosen = selected
    for i, name in enumerate(items):
        with cols[i % 4]:
            is_sel = (name == selected)
            label = f"✅ {name}" if is_sel else name
            if st.button(label, use_container_width=True, key=f"{key_prefix}_btn_{i}_{name}"):
                chosen = name
    return chosen


st.title("🎡 Party Tools (Graphic Wheels + Buddy Picker)")

tab1, tab2, tab3 = st.tabs(["1) วงล้อรางวัล", "2) วงล้อบทลงโทษ + เลือกผู้เล่น", "3) Buddy–Budder"])


# -----------------------------
# 1) Reward wheel (equal chance)
# -----------------------------
with tab1:
    st.subheader("1) วงล้อรางวัล (โอกาสเท่ากัน)")

    a, b = st.columns([2, 3])

    with a:
        n = st.number_input(
            "จำนวนรางวัล (1..N)",
            min_value=1, max_value=999,
            value=len(st.session_state.reward_pool) or 10,
            step=1, key="reward_n"
        )

        if st.button("สร้าง/รีเซ็ตพูลรางวัล", use_container_width=True, key="reward_reset"):
            st.session_state.reward_pool = list(range(1, int(n) + 1))
            st.session_state.reward_last = None
            st.session_state.reward_winner_index = None
            st.session_state.reward_wheel_labels = None
            st.success(f"สร้างพูลรางวัล 1..{n} แล้ว")

        st.session_state.reward_remove_after = st.toggle(
            "หมุนแล้วตัดออกจากพูล (ของจริง)",
            value=st.session_state.reward_remove_after,
            key="reward_remove_toggle"
        )

        st.caption(f"เหลือในพูล: {len(st.session_state.reward_pool)}")
        st.code(str(st.session_state.reward_pool))

    with b:
        pool = st.session_state.reward_pool[:]

        # ทำ labels แบบคละ (1..10 ไม่เรียงติดกัน)
        if st.session_state.reward_wheel_labels is None or set(st.session_state.reward_wheel_labels) != set(map(str, pool)):
            labels = [str(x) for x in pool]
            random.shuffle(labels)  # reward ไม่มี duplicate เลย shuffle ธรรมดาพอ
            st.session_state.reward_wheel_labels = labels

        labels = st.session_state.reward_wheel_labels

        if st.button("🎡 หมุนรางวัล", type="primary", key="reward_spin_btn"):
            if labels:
                st.session_state.reward_winner_index = random.randrange(len(labels))
            else:
                st.session_state.reward_winner_index = None

        winner_idx = st.session_state.reward_winner_index
        wheel_component(labels, winner_index=winner_idx, key="reward_wheel", height=560)

        if winner_idx is not None and 0 <= winner_idx < len(labels):
            result = int(labels[winner_idx])
            st.session_state.reward_last = result

            if st.session_state.reward_remove_after:
                # remove from pool by value
                st.session_state.reward_pool = [x for x in st.session_state.reward_pool if x != result]
                st.session_state.reward_winner_index = None
                st.session_state.reward_wheel_labels = None  # rebuild after remove

    if st.session_state.reward_last is not None:
        st.markdown(f"**ล่าสุดได้:** {st.session_state.reward_last}")


# -----------------------------
# 2) Punishment wheel (weighted) + must pick player + MARK = 0s (display 0)
# -----------------------------
with tab2:
    st.subheader("2) วงล้อบทลงโทษ (ตั้งค่า weight ได้) + ต้องเลือกผู้เล่นก่อนหมุน")

    left, right = st.columns([2, 3])

    with left:
        st.markdown("## 👤 เลือกผู้เล่น")
        st.session_state.selected_player = card_picker(
            title="Players",
            items=st.session_state.buddy_list,
            selected=st.session_state.selected_player,
            key_prefix="player"
        )

        st.divider()
        st.markdown("## ⚙️ ตั้งค่าบทลงโทษ (label / seconds / weight)")

        items = st.session_state.punish_items

        with st.expander("➕ เพิ่มรายการใหม่"):
            nl = st.text_input("label", value="ดื่ม 10 วินาที", key="punish_new_label")
            ns = st.number_input("seconds", min_value=0, max_value=999, value=10, step=1, key="punish_new_seconds")
            nw = st.number_input("weight", min_value=0, max_value=999, value=1, step=1, key="punish_new_weight")
            if st.button("เพิ่ม", use_container_width=True, key="punish_add_btn"):
                items.append({"label": nl, "seconds": int(ns), "weight": int(nw)})
                st.session_state.punish_items = items
                st.session_state.punish_wheel_labels = None
                st.success("เพิ่มแล้ว ✅")

        for idx, it in enumerate(items):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                it["label"] = st.text_input("label", value=it["label"], key=f"pun_label_{idx}")
            with c2:
                it["seconds"] = int(st.number_input("sec", min_value=0, max_value=999, value=int(it["seconds"]), step=1, key=f"pun_sec_{idx}"))
            with c3:
                it["weight"] = int(st.number_input("w", min_value=0, max_value=999, value=int(it["weight"]), step=1, key=f"pun_w_{idx}"))
            with c4:
                if st.button("ลบ", key=f"pun_del_{idx}"):
                    items.pop(idx)
                    st.session_state.punish_items = items
                    st.session_state.punish_wheel_labels = None
                    st.rerun()

        st.session_state.punish_items = items

        st.session_state.punish_remove_after = st.toggle(
            "หมุนแล้วตัดออกจากพูล (ถ้าต้องการ)",
            value=st.session_state.punish_remove_after,
            key="punish_remove_toggle",
            help="ตัดรายการที่ออกออกจาก config (ใน session นี้)"
        )

        st.divider()
        st.markdown("## ✍️ จัดการรายชื่อผู้เล่น")
        player_text = st.text_area("รายชื่อผู้เล่น (ขึ้นบรรทัดใหม่)", value="\n".join(st.session_state.buddy_list), height=150, key="player_list_text")
        if st.button("อัปเดตรายชื่อผู้เล่น", use_container_width=True, key="player_update_btn"):
            st.session_state.buddy_list = [x.strip() for x in player_text.splitlines() if x.strip()]
            if st.session_state.selected_player not in st.session_state.buddy_list:
                st.session_state.selected_player = None
            st.success("อัปเดตแล้ว ✅")

    with right:
        st.markdown("## 🎡 วงล้อบทลงโทษ")

        player = st.session_state.selected_player
        if not player:
            st.warning("ต้องเลือกผู้เล่นก่อน ถึงจะหมุนได้")
        else:
            is_mark = (player.strip().upper() == "MARK")
            effective_items = [x for x in st.session_state.punish_items if int(x.get("weight", 0)) > 0]

            if not effective_items:
                st.warning("ยังไม่มีรายการที่ weight > 0")
            else:
                # สร้าง wheel_labels แบบคละ (ไม่ให้ label เดิมติดกัน)
                if st.session_state.punish_wheel_labels is None:
                    st.session_state.punish_wheel_labels = expand_weighted_labels(effective_items)

                wheel_labels = st.session_state.punish_wheel_labels

                st.caption(f"ผู้เล่น: **{player}**")
                if st.button("🎯 เลือกผลบทลงโทษ (แล้วให้วงล้อหมุนไปหยุด)", type="primary", key="punish_spin_py"):
                    if wheel_labels:
                        st.session_state.punish_winner_index = random.randrange(len(wheel_labels))
                    else:
                        st.session_state.punish_winner_index = None

                winner_idx = st.session_state.punish_winner_index
                wheel_component(wheel_labels, winner_index=winner_idx, key="punish_wheel", height=560)

                if winner_idx is not None and 0 <= winner_idx < len(wheel_labels):
                    label = wheel_labels[winner_idx]
                    chosen = next((x for x in effective_items if x["label"] == label), {"label": label, "seconds": 0, "weight": 1})

                    eel_points = parse_eel_points(chosen.get("label", ""))

                    # ถ้าเป็นกติกา "MARK = 0 เสมอ" (แบบเปิดเผย) ก็ใช้บรรทัดนี้ต่อได้
                    seconds_to_show = 0 if is_mark else int(chosen.get("seconds", 0))
                    
                    st.session_state.punish_last = {
                        "player": player,
                        "label": chosen.get("label"),
                        "seconds": seconds_to_show,
                        "eel_points": eel_points,
                    }

                    msg = f"ผล: {player} → ดื่ม {seconds_to_show} วินาที"
                    if eel_points is not None:
                        msg += f" หรือ แทงปลาไหล {eel_points}"
                    st.success(msg)

                    # remove after (ไม่ให้ตัดตอน Mark)
                    if st.session_state.punish_remove_after and not is_mark:
                        st.session_state.punish_items = [x for x in st.session_state.punish_items if x["label"] != chosen["label"]]
                        st.session_state.punish_winner_index = None
                        st.session_state.punish_wheel_labels = None  # rebuild after remove
                        st.info("ตัดรายการนี้ออกจากพูลชั่วคราวแล้ว (session นี้)")

        # if st.session_state.punish_last:
        #     st.divider()
        #     st.markdown("### ล่าสุดได้")
        #     st.write(st.session_state.punish_last)


# -----------------------------
# 3) Buddy–Budder pairing (1-1; remove budder)
# -----------------------------
with tab3:
    st.subheader("3) Buddy–Budder")

    topL, topR = st.columns([1, 1])
    with topL:
        buddy_text = st.text_area("Buddy list (ขึ้นบรรทัดใหม่)", value="\n".join(st.session_state.buddy_list), height=150, key="bb_buddy_text")
        if st.button("อัปเดต Buddy", key="bb_buddy_update", use_container_width=True):
            st.session_state.buddy_list = [x.strip() for x in buddy_text.splitlines() if x.strip()]
            st.success("อัปเดตแล้ว ✅")

    with topR:
        budder_text = st.text_area("Budder list (ขึ้นบรรทัดใหม่)", value="\n".join(st.session_state.budder_list), height=150, key="bb_budder_text")
        if st.button("อัปเดต Budder", key="bb_budder_update", use_container_width=True):
            st.session_state.budder_list = [x.strip() for x in budder_text.splitlines() if x.strip()]
            st.success("อัปเดตแล้ว ✅")

    st.divider()

    left, mid, right = st.columns([2, 1, 2])

    with left:
        st.markdown("### 👈 เลือก Buddy")
        st.session_state.selected_buddy = card_picker(
            title="Buddy",
            items=st.session_state.buddy_list,
            selected=st.session_state.selected_buddy,
            key_prefix="bb_buddy"
        )

    with right:
        st.markdown("### Budder 👉")
        st.session_state.selected_budder = card_picker(
            title="Budder",
            items=st.session_state.budder_list,
            selected=st.session_state.selected_budder,
            key_prefix="bb_budder"
        )

    with mid:
        st.markdown("### ✅ Confirm")
        buddy = st.session_state.selected_buddy
        budder = st.session_state.selected_budder

        st.write("Buddy:", f"**{buddy or '-'}**")
        st.write("Budder:", f"**{budder or '-'}**")

        used_buddies = set(p["buddy"] for p in st.session_state.pairs)
        if buddy and buddy in used_buddies:
            st.warning("Buddy คนนี้ถูกจับคู่ไปแล้ว")

        if buddy and budder and buddy not in used_buddies:
            if st.button("จับคู่นี้เลย", type="primary", use_container_width=True, key="bb_pair_btn"):
                if st.session_state.confirm_step != (buddy, budder):
                    st.session_state.confirm_step = (buddy, budder)
                    st.warning("กดยืนยันอีกครั้งเพื่อ Confirm (กันพลาด)")
                    st.stop()
                else:
                    st.session_state.confirm_step = None

                st.session_state.pairs.append({
                    "buddy": buddy,
                    "budder": budder,
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.budder_list = [x for x in st.session_state.budder_list if x != budder]
                st.success(f"จับคู่แล้ว ✅ {buddy} ↔ {budder}")
                st.session_state.selected_budder = None
        else:
            st.info("เลือกทั้ง 2 ฝั่งก่อน")

        st.divider()
        if st.button("รีเซ็ตคู่ทั้งหมด (ไม่รีเซ็ต list)", key="bb_reset_pairs", use_container_width=True):
            st.session_state.pairs = []
            st.session_state.confirm_step = None
            st.success("ล้างคู่แล้ว ✅")

    st.divider()
    st.markdown("### 📌 ผลการจับคู่")
    if st.session_state.pairs:
        st.table(st.session_state.pairs)
    else:
        st.info("ยังไม่มีคู่")

    st.caption(f"Budder เหลือในพูล: {len(st.session_state.budder_list)} คน")
