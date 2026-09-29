"""
HEMM Sensor Fusion POC
Professional laptop dashboard — synthetic Radar + Thermal + Camera inputs.
The fusion logic and CSV data flow are unchanged; only the dashboard presentation
has been redesigned for a professional industrial / mining safety display.
"""
import csv
import tkinter as tk
from pathlib import Path
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

DATA = Path(__file__).parent / "data" / "sensor_data.csv"

# -----------------------------
# Professional dashboard palette
# -----------------------------
BG = "#071018"
PANEL = "#0D1A24"
PANEL_2 = "#10222E"
BORDER = "#1D3A4A"
TEXT = "#E8F1F5"
MUTED = "#8FA6B3"
CYAN = "#19D3E6"
BLUE = "#3488FF"
GREEN = "#31D17C"
YELLOW = "#FFC857"
RED = "#FF4D5A"
ORANGE = "#FF8A3D"
GRID = "#183342"


def load_rows():
    with open(DATA, newline="") as f:
        return list(csv.DictReader(f))


def fuse(r):
    radar = float(r["radar_confidence"])
    thermal = float(r["thermal_confidence"]) if int(r["thermal_detected"]) else 0
    camera = float(r["camera_confidence"])
    # Adaptive weights: camera is reduced as camera health degrades.
    health = r["camera_health"]
    if health == "NORMAL":
        weights = (0.45, 0.35, 0.20)
    elif health == "DEGRADED":
        weights = (0.55, 0.35, 0.10)
    else:
        weights = (0.60, 0.40, 0.00)
    fused = radar * weights[0] + thermal * weights[1] + camera * weights[2]
    dist = float(r["radar_distance_m"])
    vel = float(r["radar_velocity_kmh"])
    if dist < 15 or (dist < 25 and vel > 20):
        status = "DANGER"
    elif dist < 40:
        status = "CAUTION"
    else:
        status = "SAFE"
    return fused, status, weights


class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("HEMM SAFETY MONITOR | Sensor Fusion POC")
        self.root.geometry("1360x820")
        self.root.minsize(1180, 720)
        self.root.configure(bg=BG)

        self.rows = load_rows()
        self.i = 0
        self.running = True
        self.sim_speed_kmh = 20.0
        self.sim_time = 0.0
        self.motion_step = 0.0

        self._build_header()
        self._build_main()
        self._build_footer()
        self.update()

    # -----------------------------
    # Generic UI helpers
    # -----------------------------
    def panel(self, parent, title, subtitle=None):
        outer = tk.Frame(parent, bg=BORDER)
        inner = tk.Frame(outer, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        head = tk.Frame(inner, bg=PANEL)
        head.pack(fill="x", padx=14, pady=(11, 5))
        tk.Label(head, text=title, font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=PANEL).pack(side="left")
        if subtitle:
            tk.Label(head, text=subtitle, font=("Segoe UI", 9),
                     fg=MUTED, bg=PANEL).pack(side="right")
        return outer, inner

    def metric_card(self, parent, title, value, unit="", accent=CYAN):
        frame = tk.Frame(parent, bg=PANEL_2, highlightthickness=1,
                         highlightbackground=BORDER)
        frame.pack(side="left", fill="both", expand=True, padx=4)
        tk.Frame(frame, bg=accent, height=3).pack(fill="x")
        tk.Label(frame, text=title, font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL_2).pack(anchor="w", padx=10, pady=(8, 1))
        row = tk.Frame(frame, bg=PANEL_2)
        row.pack(anchor="w", padx=10, pady=(0, 8))
        val = tk.Label(row, text=value, font=("Segoe UI", 18, "bold"),
                       fg=TEXT, bg=PANEL_2)
        val.pack(side="left")
        if unit:
            tk.Label(row, text=unit, font=("Segoe UI", 9, "bold"),
                     fg=accent, bg=PANEL_2).pack(side="left", padx=(5, 0), pady=(7, 0))
        return val

    def status_chip(self, parent, name, state="ACTIVE"):
        box = tk.Frame(parent, bg=PANEL_2, highlightthickness=1,
                       highlightbackground=BORDER)
        box.pack(fill="x", padx=12, pady=4)
        dot = tk.Canvas(box, width=15, height=15, bg=PANEL_2, highlightthickness=0)
        dot.pack(side="left", padx=(9, 6), pady=9)
        dot.create_oval(3, 3, 12, 12, fill=GREEN, outline="")
        tk.Label(box, text=name, font=("Segoe UI", 10, "bold"),
                 fg=TEXT, bg=PANEL_2).pack(side="left", pady=8)
        value = tk.Label(box, text=state, font=("Segoe UI", 8, "bold"),
                         fg=GREEN, bg=PANEL_2)
        value.pack(side="right", padx=10)
        return value

    # -----------------------------
    # Header
    # -----------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg="#09151E", height=74)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg="#09151E")
        left.pack(side="left", padx=22, pady=10)
        tk.Label(left, text="ZENRIC TECHNOLOGIES", font=("Segoe UI", 20, "bold"),
                 fg=CYAN, bg="#09151E").pack(side="left")
        tk.Label(left, text="  FOG SAFETY MONITOR", font=("Segoe UI", 17, "bold"),
                 fg=TEXT, bg="#09151E").pack(side="left")
        tk.Label(left, text="\nSensor Fusion Proof of Concept", font=("Segoe UI", 8),
                 fg=MUTED, bg="#09151E", justify="left").pack(side="left", padx=(15, 0))

        right = tk.Frame(header, bg="#09151E")
        right.pack(side="right", padx=22, pady=14)
        self.mode_badge = tk.Label(right, text="●  POC SIMULATION", font=("Segoe UI", 9, "bold"),
                                   fg=CYAN, bg="#102631", padx=12, pady=7)
        self.mode_badge.pack(side="right", padx=(10, 0))
        self.env = tk.Label(right, text="HEAVY FOG  |  MINING ZONE  |  SIM SPEED 20 km/h", font=("Segoe UI", 9, "bold"),
                            fg=MUTED, bg="#09151E")
        self.env.pack(side="right")

        tk.Frame(self.root, bg=CYAN, height=2).pack(fill="x")

    # -----------------------------
    # Main dashboard layout
    # -----------------------------
    def _build_main(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # LEFT: data/sensor status, as in user's sketch
        left = tk.Frame(body, bg=BG, width=245)
        left.pack(side="left", fill="y", padx=(0, 9))
        left.pack_propagate(False)

        p, inside = self.panel(left, "DATA STATUS", "LIVE")
        p.pack(fill="x")
        self.sensor_status_frame = tk.Frame(inside, bg=PANEL)
        self.sensor_status_frame.pack(fill="x", pady=(3, 10))
        self.radar_chip = self.status_chip(self.sensor_status_frame, "RADAR")
        self.thermal_chip = self.status_chip(self.sensor_status_frame, "THERMAL")
        self.camera_chip = self.status_chip(self.sensor_status_frame, "CAMERA")

        # Caution distance moved into DATA STATUS for a compact safety overview.
        caution_box = tk.Frame(inside, bg=PANEL_2, highlightthickness=1,
                               highlightbackground=BORDER)
        caution_box.pack(fill="x", padx=12, pady=(6, 10))
        tk.Label(caution_box, text="CAUTION DISTANCE", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL_2).pack(anchor="w", padx=10, pady=(8, 0))
        caution_row = tk.Frame(caution_box, bg=PANEL_2)
        caution_row.pack(anchor="w", padx=10, pady=(0, 8))
        self.caution_value = tk.Label(caution_row, text="--", font=("Segoe UI", 24, "bold"),
                                      fg=YELLOW, bg=PANEL_2)
        self.caution_value.pack(side="left")
        tk.Label(caution_row, text="m", font=("Segoe UI", 9, "bold"),
                 fg=YELLOW, bg=PANEL_2).pack(side="left", padx=(5, 0), pady=(7, 0))

        p2, inside2 = self.panel(left, "FUSION ENGINE", "ADAPTIVE")
        p2.pack(fill="x", pady=10)
        self.fusion_value = tk.Label(inside2, text="-- %", font=("Segoe UI", 29, "bold"),
                                     fg=CYAN, bg=PANEL)
        self.fusion_value.pack(pady=(4, 0))
        tk.Label(inside2, text="FUSED CONFIDENCE", font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(pady=(0, 8))
        self.weight_text = tk.Label(inside2, text="", justify="left", anchor="w",
                                    font=("Consolas", 9), fg=TEXT, bg=PANEL)
        self.weight_text.pack(fill="x", padx=14, pady=(2, 12))

        p3, inside3 = self.panel(left, "SYSTEM HEALTH", "100%")
        p3.pack(fill="x")
        self.health_text = tk.Label(inside3, text="●  ALL SYSTEMS NOMINAL",
                                    font=("Segoe UI", 9, "bold"), fg=GREEN, bg=PANEL)
        self.health_text.pack(anchor="w", padx=14, pady=(6, 12))

        # CENTER: 3D-ish map / mining area visualization
        center = tk.Frame(body, bg=BG, width=515)
        center.pack(side="left", fill="both", expand=False, padx=9)
        center.pack_propagate(False)

        p4, inside4 = self.panel(center, "MINING ROAD MAP / MULTI-OBJECT TRACK VIEW", "3 OBJECTS  •  FUSED RADAR + THERMAL + CAMERA")
        p4.pack(fill="both", expand=True)
        self.map_canvas = tk.Canvas(inside4, bg="#071017", highlightthickness=0)
        self.map_canvas.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        # bottom metrics inside center panel
        metrics = tk.Frame(inside4, bg=PANEL, height=74)
        metrics.pack(fill="x", padx=10, pady=(0, 10))
        self.distance_value = self.metric_card(metrics, "OBJECT DISTANCE", "--", "m", YELLOW)
        self.velocity_value = self.metric_card(metrics, "HEMM SPEED", "20.0", "km/h", ORANGE)
        self.direction_value = self.metric_card(metrics, "ROAD DIRECTION", "NORTH-EAST", "", CYAN)
        self.confidence_value = self.metric_card(metrics, "RADAR CONFIDENCE", "--", "%", BLUE)

        # RIGHT: camera image + caution distance, as in sketch
        right = tk.Frame(body, bg=BG, width=515)
        right.pack(side="right", fill="y", padx=(9, 0))
        right.pack_propagate(False)

        p5, inside5 = self.panel(right, "CAMERA IMAGE", "NIR / VISION")
        p5.pack(fill="both", expand=True)
        self.camera_canvas = tk.Canvas(inside5, width=480, height=310, bg="#05090D", highlightthickness=0)
        self.camera_canvas.pack(fill="both", expand=True, padx=12, pady=(3, 12))
        self.camera_image = None
        camera_path = Path(__file__).parent / "data" / "mining_camera.png"
        if Image is not None and camera_path.exists():
            try:
                img = Image.open(camera_path).convert("RGB")
                img = img.resize((480, 310), Image.Resampling.LANCZOS)
                self.camera_image = ImageTk.PhotoImage(img)
            except Exception:
                self.camera_image = None

        # Caution distance has been moved to DATA STATUS on the left.

        p7, inside7 = self.panel(right, "OBJECT TRACK", "TRACK #01")
        p7.pack(fill="x")
        self.object_text = tk.Label(inside7, text="", justify="left", anchor="w",
                                    font=("Consolas", 9), fg=TEXT, bg=PANEL)
        self.object_text.pack(fill="x", padx=14, pady=(2, 12))

        p8, inside8 = self.panel(right, "SAFETY DECISION")
        p8.pack(fill="x", pady=10)
        self.status = tk.Label(inside8, text="--", font=("Segoe UI", 23, "bold"),
                               fg=TEXT, bg=PANEL, pady=10)
        self.status.pack(fill="x", padx=10, pady=8)

    # -----------------------------
    # Map drawing
    # -----------------------------
    def draw_map(self, distance, status):
        c = self.map_canvas
        c.delete("all")
        w = max(c.winfo_width(), 600)
        h = max(c.winfo_height(), 360)

        # Professional mining-road plan/perspective view. The road scrolls to
        # simulate a HEMM travelling at 20 km/h while multiple fused objects
        # are displayed around the vehicle.
        c.create_rectangle(0, 0, w, h, fill="#071017", outline="")
        horizon = int(h * 0.22)

        # Terrain / mining benches
        for i, y in enumerate([horizon + 20, horizon + 72, horizon + 125]):
            inset = 20 + i * 28
            c.create_polygon(inset, y, w-inset, y, w-inset-25, y+22, inset+25, y+22,
                             fill="#0B1A21", outline="#1C3B48")

        # Road boundaries and center line
        road_top = horizon + 5
        road_bottom = h
        left_top, right_top = int(w*.44), int(w*.56)
        left_bottom, right_bottom = int(w*.08), int(w*.92)
        c.create_polygon(left_top, road_top, right_top, road_top, right_bottom, road_bottom,
                         left_bottom, road_bottom, fill="#101E24", outline="#31505A")
        c.create_line(left_top, road_top, left_bottom, road_bottom, fill="#47636A", width=2)
        c.create_line(right_top, road_top, right_bottom, road_bottom, fill="#47636A", width=2)

        # Animated lane markings: 20 km/h simulation
        offset = int((self.sim_time * self.sim_speed_kmh / 3.6 * 2.5) % 70)
        for y in range(road_top + offset, road_bottom, 70):
            yy = min(y, road_bottom)
            c.create_line(w//2, yy, w//2, min(yy+30, road_bottom), fill="#C8D7DA", width=3)

        c.create_text(20, 16, text="MINING HAUL ROAD  •  LIVE FUSED MAP", anchor="nw",
                      fill=MUTED, font=("Segoe UI", 9, "bold"))
        c.create_text(w-20, 16, text="SIMULATION SPEED 20 km/h", anchor="ne",
                      fill=ORANGE, font=("Segoe UI", 9, "bold"))

        # Radar range rings around HEMM
        cx, cy = w // 2, h - 58
        for radius, label in [(55, "20m"), (105, "40m"), (155, "60m")]:
            c.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, outline="#1C4858")
            c.create_text(cx+radius+5, cy-3, text=label, fill="#5C7C86", font=("Segoe UI", 7))

        # HEMM vehicle
        c.create_polygon(cx-44, cy+18, cx+44, cy+18, cx+31, cy-14, cx-31, cy-14,
                         fill="#1B4252", outline=CYAN, width=2)
        c.create_rectangle(cx-20, cy-28, cx+20, cy-10, fill="#163846", outline=CYAN)
        c.create_text(cx, cy+31, text="HEMM  |  20 km/h", fill=CYAN, font=("Segoe UI", 8, "bold"))

        # Three detected objects are intentionally kept well ahead of our HEMM.
        # This gives the demo a safer, more realistic following-distance view.
        objects = [
            {"id":"01", "lane":0.00, "dist":145.0 + 1.5*((self.i)%3), "speed":10.0, "kind":"TRUCK"},
            {"id":"02", "lane":-0.30, "dist":190.0 + 1.5*((self.i+1)%3), "speed":8.0, "kind":"LOADER"},
            {"id":"03", "lane":0.28, "dist":235.0 + 2.0*((self.i+2)%3), "speed":9.0, "kind":"DUMPER"},
        ]

        def road_x(lane, y):
            # interpolate lane position across perspective road
            t = max(0.0, min(1.0, (y-road_top)/(road_bottom-road_top)))
            center = w/2
            road_half = (right_top-left_top)/2*(1-t) + (right_bottom-left_bottom)/2*t
            return center + lane*road_half

        danger_color = RED if status == "DANGER" else YELLOW if status == "CAUTION" else GREEN
        for obj in objects:
            d = obj["dist"]
            t = max(0.0, min(1.0, d/260.0))
            y = road_bottom - t*(road_bottom-road_top)
            x = road_x(obj["lane"], y)
            scale = 0.65 + (1-t)*0.55
            bw, bh = int(25*scale), int(14*scale)
            col = danger_color if obj["id"] == "01" else (ORANGE if obj["kind"] == "DUMPER" else BLUE)
            c.create_oval(x-bw-7, y-bh-7, x+bw+7, y+bh+7, outline=col, width=1)
            c.create_rectangle(x-bw, y-bh, x+bw, y+bh, fill="#20343B", outline=col, width=2)
            c.create_rectangle(x-int(bw*.45), y-int(bh*.75), x+int(bw*.45), y-int(bh*.05), fill="#13282F", outline=CYAN)
            c.create_text(x, y, text=obj["id"], fill=TEXT, font=("Segoe UI", 7, "bold"))
            label_y = y - bh - 11
            c.create_text(x+18, label_y, text=f"OBJ {obj['id']}  {d:.1f}m  {obj['speed']:.0f}km/h",
                          anchor="w", fill=TEXT if obj["id"] == "01" else MUTED,
                          font=("Segoe UI", 7, "bold"))

        # Fusion line to primary object
        p = objects[0]
        pt = max(0.0, min(1.0, p["dist"]/260.0))
        py = road_bottom - pt*(road_bottom-road_top)
        px = road_x(0.0, py)
        c.create_line(cx, cy-15, px, py, fill=CYAN, dash=(5,4), width=2)
        c.create_text(24, h-18, text="● 01-03 MULTI-OBJECT FUSED TRACKS",
                      anchor="w", fill=CYAN, font=("Segoe UI", 8, "bold"))

    def draw_camera(self, r):
        c = self.camera_canvas
        c.delete("all")
        w = max(c.winfo_width(), 480)
        h = max(c.winfo_height(), 310)

        # Realistic mining-road camera frame supplied with the POC. The image
        # shows the three detected vehicles well ahead of the HEMM.
        if self.camera_image is not None:
            c.create_image(w // 2, h // 2, image=self.camera_image, anchor="center")
            c.create_rectangle(5, 5, w-5, h-5, outline="#254552")
            c.create_text(12, 12, text="FRONT CAMERA  •  LIVE", anchor="nw",
                          fill=CYAN, font=("Segoe UI", 7, "bold"))
        else:
            c.create_rectangle(0, 0, w, h, fill="#0A161D", outline="#254552")
            c.create_text(w//2, h//2, text="MINING CAMERA FEED\n3 OBJECTS DETECTED",
                          fill=CYAN, justify="center", font=("Segoe UI", 10, "bold"))

    # -----------------------------
    # Footer
    # -----------------------------
    def _build_footer(self):
        bar = tk.Frame(self.root, bg="#09151E", height=42)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        self.footer = tk.Label(bar, text="RADAR  ●  ACTIVE     THERMAL  ●  ACTIVE     CAMERA  ●  NORMAL",
                               font=("Segoe UI", 9, "bold"), fg=MUTED, bg="#09151E")
        self.footer.pack(side="left", padx=18, pady=10)
        self.clock = tk.Label(bar, text="LIVE MOTION  •  20 km/h  •  SLOW TRACK  •  3 FPS", font=("Segoe UI", 8, "bold"),
                              fg="#607987", bg="#09151E")
        self.clock.pack(side="right", padx=18)
        self.pause_btn = tk.Button(bar, text="PAUSE", command=self.toggle,
                                   font=("Segoe UI", 8, "bold"), fg=TEXT, bg="#142732",
                                   activebackground="#1B3948", activeforeground=TEXT,
                                   relief="flat", padx=12, pady=4, cursor="hand2")
        self.pause_btn.pack(side="right", padx=(0, 8))

    # -----------------------------
    # Data refresh — fusion logic unchanged
    # -----------------------------
    def update(self):
        r = self.rows[self.i]
        fused, status, weights = fuse(r)
        distance = float(r["radar_distance_m"])
        velocity = float(r["radar_velocity_kmh"])
        display_speed = self.sim_speed_kmh
        radar_conf = float(r["radar_confidence"])
        thermal_detected = int(r["thermal_detected"])
        camera_detected = int(r["camera_detected"])
        health = r["camera_health"]

        self.draw_map(distance, status)
        self.draw_camera(r)

        self.distance_value.config(text=f"{distance:.1f}")
        self.velocity_value.config(text=f"{display_speed:.1f}")
        self.direction_value.config(text="AHEAD")
        self.confidence_value.config(text=f"{radar_conf:.0f}")
        self.caution_value.config(text=f"{distance:.1f}")
        self.fusion_value.config(text=f"{fused:.0f}%")

        self.weight_text.config(text=(
            f"RADAR      {weights[0]*100:>3.0f}%\n"
            f"THERMAL    {weights[1]*100:>3.0f}%\n"
            f"CAMERA     {weights[2]*100:>3.0f}%"
        ))

        self.object_text.config(text=(
            f"3 ACTIVE TRACKS\n"
            f"Primary    {distance:>6.1f} m\n"
            f"HEMM speed {display_speed:>5.1f} km/h\n"
            f"Objects    01 02 03\n"
            f"Primary    {fused:>6.0f}% fused"
        ))

        self.radar_chip.config(text="ACTIVE", fg=GREEN)
        self.thermal_chip.config(text="ACTIVE" if thermal_detected else "NO DETECTION",
                                 fg=GREEN if thermal_detected else YELLOW)
        self.camera_chip.config(text=health, fg=GREEN if health == "NORMAL" else YELLOW)

        if status == "DANGER":
            status_color = RED
            status_text = "DANGER"
            health_text = "●  IMMEDIATE HAZARD"
        elif status == "CAUTION":
            status_color = YELLOW
            status_text = "CAUTION"
            health_text = "●  ATTENTION REQUIRED"
        else:
            status_color = GREEN
            status_text = "SAFE"
            health_text = "●  ALL SYSTEMS NOMINAL"

        self.status.config(text=status_text, fg=status_color)
        self.health_text.config(text=health_text, fg=status_color)
        self.caution_value.config(fg=status_color if status != "SAFE" else GREEN)
        self.footer.config(
            text=f"RADAR  ●  ACTIVE     THERMAL  ●  {'ACTIVE' if thermal_detected else 'STANDBY'}"
                 f"     CAMERA  ●  {health}     |     OBJECTS 01-03  ●  TRACKING  |  HEMM 20 km/h"
        )

        if self.running:
            self.i = (self.i + 1) % len(self.rows)
            self.sim_time += 0.10
            self.root.after(350, self.update)

    def toggle(self):
        self.running = not self.running
        self.pause_btn.config(text="PAUSE" if self.running else "RESUME")
        if self.running:
            self.update()


if __name__ == "__main__":
    app = tk.Tk()
    Dashboard(app)
    app.mainloop()
