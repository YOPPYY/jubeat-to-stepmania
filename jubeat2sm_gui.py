import sys
import re
import os
import math
import functools
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    TkinterDnD = None 
    print("エラー: 'tkinterdnd2' が見つかりません。")

# ==========================================
# ユーティリティ: LCM (最小公倍数)
# ==========================================
def lcm(a, b):
    return abs(a * b) // math.gcd(a, b)

def list_lcm(numbers):
    if not numbers: return 4
    return functools.reduce(lcm, numbers)

# ==========================================
# 変換ロジック (ホールド削除・始点のみ1)
# ==========================================
def jubeat_to_sm_converter(text_data):
    # 丸数字(始点/単押し) -> IDへのマップ
    circle_nums = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯"
    start_map = {c: i+1 for i, c in enumerate(circle_nums)}
    
    # 全角数字(終点) -> IDへのマップ
    # ※リズム解析のために定義は残すが、ノーツ生成には使用しない
    end_map = {c: i+1 for i, c in enumerate("１２３４５６７８９")}
    end_map['０'] = 10 

    # 小節データに分割
    measures = re.split(r'^\s*\d+\s*$', text_data, flags=re.MULTILINE)
    measures = [m for m in measures if m.strip()]

    sm_measures_data = []

    # --- 0小節目 (空小節) を先頭に追加 ---
    measure0 = "// measure 0\n0000\n0000\n0000\n0000"
    sm_measures_data.append(measure0)

    # --- 入力データの変換 ---
    for measure_idx, measure_text in enumerate(measures):
        lines = measure_text.strip().split('\n')
        grid_events = {} 
        beats_data = []

        # 解析
        for line in lines:
            if "|" in line:
                parts = line.split('|')
                grid_str = parts[0].strip()
                time_str = parts[1]
                
                # グリッド
                clean_grid = grid_str.replace('＜', '□').replace('■', '□')
                for col_idx, char in enumerate(clean_grid):
                    if col_idx > 3: break
                    if char in start_map:
                        pid = start_map[char]
                        if pid not in grid_events: grid_events[pid] = []
                        grid_events[pid].append({'col': col_idx, 'type': 'tap'}) # すべてtap扱い
                    # 終点記号(全角数字)がグリッドにあっても無視する

                # タイムライン解析
                # 文字数がリズム分解能になる
                beat_chars = [c for c in time_str]
                resolution = len(beat_chars)
                if resolution > 0:
                    beats_data.append((resolution, beat_chars))
            else:
                # グリッドのみ
                clean_grid = line.strip().replace('＜', '□').replace('■', '□')
                for col_idx, char in enumerate(clean_grid):
                    if col_idx > 3: break
                    if char in start_map:
                        pid = start_map[char]
                        if pid not in grid_events: grid_events[pid] = []
                        grid_events[pid].append({'col': col_idx, 'type': 'tap'})

        if not beats_data:
            sm_measures_data.append(f"// measure {measure_idx + 1}\n0000\n0000\n0000\n0000")
            continue

        # LCM計算
        resolutions = [b[0] for b in beats_data]
        lcm_res = list_lcm(resolutions)
        total_rows = len(beats_data) * lcm_res
        tick_events = [[] for _ in range(total_rows)]

        for beat_idx, (res, chars) in enumerate(beats_data):
            beat_start_row = beat_idx * lcm_res
            scale = lcm_res // res
            for char_idx, char in enumerate(chars):
                target_id = None
                
                # 始点(丸数字)のみをターゲットIDとして取得
                if char in start_map: 
                    target_id = start_map[char]
                
                # 終点(全角数字)は無視 (target_id = Noneのまま) -> ノーツ配置されない(0000になる)
                
                if target_id is not None:
                    row_idx = beat_start_row + (char_idx * scale)
                    tick_events[row_idx].append(target_id)

        # 文字列生成
        measure_lines = []
        for tick in range(total_rows):
            row_chars = ['0', '0', '0', '0']
            active_ids = tick_events[tick]
            for pid in active_ids:
                if pid in grid_events:
                    for event in grid_events[pid]:
                        col = event['col']
                        # 常に '1' (Tap) を出力
                        row_chars[col] = '1'
            measure_lines.append("".join(row_chars))
        
        # 配列に追加
        sm_measures_data.append(f"// measure {measure_idx + 1}\n" + "\n".join(measure_lines))

    return "\n,\n".join(sm_measures_data)

# ==========================================
# GUI アプリケーション
# ==========================================
class JubeatToSmApp(TkinterDnD.Tk if TkinterDnD else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jubeat Memo to StepMania Converter")
        self.geometry("700x750")
        
        # --- 変数定義 ---
        self.input_text_content = ""
        
        # ヘッダー用変数
        self.var_title = tk.StringVar()
        self.var_artist = tk.StringVar(value="")
        self.var_music = tk.StringVar()
        self.var_music_ext = tk.StringVar(value=".mp3")
        self.var_bpm = tk.StringVar(value="100")
        self.var_difficulty = tk.StringVar(value="Hard")
        self.var_level = tk.StringVar(value="1")  # デフォルトレベル: 1

        # 変更時にプレビュー更新
        for var in [self.var_title, self.var_artist, self.var_music, 
                    self.var_music_ext, self.var_bpm, self.var_difficulty, self.var_level]:
            var.trace_add("write", lambda *args: self.update_preview())

        # --- UI配置 ---
        top_frame = tk.Frame(self, pady=10, padx=10)
        top_frame.pack(fill=tk.X)

        # Row 1: ファイル選択
        row1 = tk.Frame(top_frame)
        row1.pack(fill=tk.X, pady=5)
        btn_select = tk.Button(row1, text="ファイルを選択 (.txt)", command=self.open_file_dialog)
        btn_select.pack(side=tk.LEFT)
        tk.Label(row1, text="※D&Dでも読み込めます", fg="gray").pack(side=tk.LEFT, padx=10)

        # Row 2: Title / Artist
        row2 = tk.Frame(top_frame)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="TITLE:", width=6, anchor='e').grid(row=0, column=0, padx=5)
        tk.Entry(row2, textvariable=self.var_title, width=30).grid(row=0, column=1, padx=5)
        tk.Label(row2, text="ARTIST:", width=6, anchor='e').grid(row=0, column=2, padx=5)
        tk.Entry(row2, textvariable=self.var_artist, width=30).grid(row=0, column=3, padx=5)

        # Row 3: Music / BPM
        row3 = tk.Frame(top_frame)
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="MUSIC:", width=6, anchor='e').grid(row=0, column=0, padx=5)
        music_frame = tk.Frame(row3)
        music_frame.grid(row=0, column=1, padx=5, sticky="w")
        tk.Entry(music_frame, textvariable=self.var_music, width=22).pack(side=tk.LEFT)
        ttk.Combobox(music_frame, textvariable=self.var_music_ext, values=[".mp3", ".ogg"], width=5, state="readonly").pack(side=tk.LEFT)
        tk.Label(row3, text="BPM:", width=6, anchor='e').grid(row=0, column=2, padx=5)
        tk.Entry(row3, textvariable=self.var_bpm, width=10).grid(row=0, column=3, padx=5, sticky="w")

        # Row 4: Difficulty / Level (Modified)
        row4 = tk.Frame(top_frame)
        row4.pack(fill=tk.X, pady=5)

        tk.Label(row4, text="Diff:", width=6, anchor='e').pack(side=tk.LEFT, padx=5)
        diff_combo = ttk.Combobox(row4, textvariable=self.var_difficulty, 
                                  values=["Beginner", "Easy", "Medium", "Hard", "Challenge", "Edit"], 
                                  state="readonly", width=10)
        diff_combo.pack(side=tk.LEFT, padx=5)

        # レベル入力欄の追加
        tk.Label(row4, text="Level:", width=6, anchor='e').pack(side=tk.LEFT, padx=(20, 5))
        tk.Entry(row4, textvariable=self.var_level, width=5).pack(side=tk.LEFT, padx=5)

        btn_save = tk.Button(row4, text="結果を保存", bg="#e0e0e0", command=self.save_file, width=15)
        btn_save.pack(side=tk.RIGHT, padx=5)

        # 説明
        if TkinterDnD:
            lbl_desc = tk.Label(self, text="↓ ここにテキストファイルをドラッグ＆ドロップ ↓", 
                                bg="#f0f0f0", relief=tk.GROOVE, pady=5)
            lbl_desc.pack(fill=tk.X, padx=10)

        # 結果表示エリア
        self.result_area = scrolledtext.ScrolledText(self, font=("Consolas", 10))
        self.result_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # D&D設定
        if TkinterDnD:
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)

    def process_content(self, text, filepath=None):
        self.input_text_content = text
        if filepath:
            basename = os.path.splitext(os.path.basename(filepath))[0]
            self.var_title.set(basename)
            self.var_music.set(basename)
            self.title(f"Jubeat2SM - {basename}")
        self.update_preview()

    def generate_sm_content(self):
        if not self.input_text_content:
            return ""

        # ノーツデータの変換 (ホールド引数なし)
        notes_data = jubeat_to_sm_converter(self.input_text_content)
        
        # ヘッダー情報の取得
        title = self.var_title.get()
        artist = self.var_artist.get()
        music = self.var_music.get() + self.var_music_ext.get()
        bpm = self.var_bpm.get()
        difficulty = self.var_difficulty.get()
        level = self.var_level.get()

        # ヘッダー構築
        header = f"#TITLE:{title};\n"
        header += f"#ARTIST:{artist};\n"
        header += f"#MUSIC:{music};\n"
        header += f"#BPMS:0.000={bpm};\n"
        header += "#OFFSET:0.000;\n"
        header += "#NOTES:\n"
        header += "     dance-single:\n"
        header += "     :\n"
        header += f"     {difficulty}:\n"
        header += f"     {level}:\n"  # ここにレベル数値が入る
        header += "     0.000,0.000,0.000,0.000:\n"
        
        full_content = header + notes_data + "\n;"
        return full_content

    def update_preview(self):
        content = self.generate_sm_content()
        self.result_area.delete('1.0', tk.END)
        self.result_area.insert(tk.END, content)

    def on_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
                self.process_content(content, file_path)
            except:
                try:
                    with open(file_path, 'r', encoding='shift_jis') as f: content = f.read()
                    self.process_content(content, file_path)
                except:
                    messagebox.showerror("エラー", "読み込み失敗")

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
            self.process_content(content, file_path)

    def save_file(self):
        result_text = self.result_area.get('1.0', tk.END).strip()
        if not result_text: return
        
        initial_name = f"{self.var_title.get()}.sm"
        file_path = filedialog.asksaveasfilename(
            initialfile=initial_name, defaultextension=".sm",
            filetypes=[("StepMania File", "*.sm"), ("Text File", "*.txt")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f: f.write(result_text)
            messagebox.showinfo("完了", "保存しました")

if __name__ == "__main__":
    app = JubeatToSmApp()
    app.mainloop()